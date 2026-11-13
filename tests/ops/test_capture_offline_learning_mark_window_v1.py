"""Public mark capture fixtures with independent response receipt clocks."""

from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

import pytest

from scripts.ops import capture_offline_learning_mark_window_v1 as capture
from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    REQUEST_SCHEMA,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    MarketIdentityV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    compose_recorded_market_context_v1,
    measure_recorded_market_horizon_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    resolve_okx_venue_instrument_mapping_v1,
)

START = "2026-10-09T11:00:00Z"
RECEIVED = "2026-10-09T13:00:05.000003+00:00"
XPERP_INVENTORY = (
    Path(__file__).parents[1]
    / "fixtures/ops/okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1"
    / "instruments_futures_live.json"
)


@pytest.fixture
def capture_args(tmp_path, monkeypatch):
    times = iter(
        [
            "2026-10-09T13:00:01.000001+00:00",
            "2026-10-09T13:00:02.000001+00:00",
            "2026-10-09T13:00:03.000002+00:00",
            "2026-10-09T13:00:04.000002+00:00",
            RECEIVED,
        ]
    )
    monkeypatch.setattr(capture, "_utc_now", lambda: next(times, RECEIVED))
    binding = {
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "native_instrument_id": "ETH-USDT-SWAP",
        "venue": "OKX",
        "instrument_metadata": {
            "instId": "ETH-USDT-SWAP",
            "instType": "SWAP",
            "settleCcy": "USDT",
            "uly": "ETH-USDT",
        },
    }
    return with_binding(
        {
            "output": tmp_path / "archive",
            "start_utc": START,
            "hours": 2,
            "binding_path": tmp_path / "binding.json",
            "repository_sha": "a" * 40,
        },
        binding,
    )


def with_binding(args, binding):
    raw = json.dumps(binding).encode()
    args["binding_path"].write_bytes(raw)
    return {**args, "binding_sha256": hashlib.sha256(raw).hexdigest()}


@pytest.fixture
def xperp_binding():
    inventory = json.loads(XPERP_INVENTORY.read_bytes())["data"]
    instrument = inventory[0]["instId"]
    mapping = resolve_okx_venue_instrument_mapping_v1(
        canonical_instrument_id=instrument, instruments_inventory=inventory
    )
    return {
        "canonical_instrument_id": instrument,
        "native_instrument_id": mapping.venue_instrument_id,
        "venue": mapping.venue,
        "mapping_digest": mapping.mapping_digest,
        "instrument_metadata": inventory[0],
    }


def mark_page(query, *, omit_last=False):
    cursor = int(query["after"])
    limit = int(query["limit"]) - omit_last
    first_hour_end = (int(capture.utc_seconds(START)) + 3600) * 1000
    rows = []
    for index in range(limit):
        opened = cursor - (index + 1) * 60_000
        price = "100" if opened < first_hour_end else "102"
        rows.append([str(opened), price, price, price, price, "1"])
    return 200, json.dumps({"code": "0", "data": rows}).encode()


@pytest.mark.parametrize("is_xperp", [False, True], ids=["legacy-swap", "current-i17-xperp"])
def test_captured_pages_feed_existing_measurement_with_their_own_clocks(
    capture_args, xperp_binding, is_xperp
):
    if is_xperp:
        capture_args = with_binding(capture_args, xperp_binding)
    binding = json.loads(capture_args["binding_path"].read_bytes())
    native = binding["native_instrument_id"]
    price_unit = "USD per ETH" if is_xperp else "USDT per ETH"
    queries = []

    def fetch(query):
        queries.append(query)
        return mark_page(query)

    manifest = capture.capture_public_mark_window_v1(**capture_args, fetch_page=fetch)
    assert manifest["available_at_utc"] == RECEIVED
    assert [q["instId"] for q in queries] == [native, native]
    assert [q["limit"] for q in queries] == ["100", "20"]
    assert int(queries[0]["after"]) - int(queries[1]["after"]) == 100 * 60_000
    archive = capture.read_captured_mark_archive_v1(capture_args["output"])
    request = {
        "schema_version": REQUEST_SCHEMA,
        "market_identity": {
            "dataset_generation": "archive.fixture",
            "venue": "OKX",
            "instrument_ref": binding["canonical_instrument_id"],
            "native_instrument_ref": native,
        },
        "horizon_start_time_utc": START,
        "n_bars": 2,
        "o4_interval_id": "PT1H",
        "price_unit": price_unit,
        "price_family": "MARK_PRICE",
        "source_kind": "RECORDED_PUBLIC_MD",
        "max_end_age_seconds": 300,
        "expected_price_basis_kind": "O4_BAR_CLOSE_FINALIZED",
    }
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        measure_recorded_market_horizon_v1(
            archive=replace(archive, raw_path=archive.raw_path.parent / "unavailable.json"),
            request=request,
            evaluated_at_utc="2026-10-09T13:00:05.000002+00:00",
        )
    measured = measure_recorded_market_horizon_v1(
        archive=archive, request=request, evaluated_at_utc=RECEIVED
    )
    assert measured["measurement"]["log_return"] == pytest.approx(math.log(102 / 100))
    assert [row["available_at_utc"] for row in measured["source_receipts"]] == [
        "2026-10-09T13:00:05.000003Z",
        "2026-10-09T13:00:03.000002Z",
    ]
    assert all(row["price_unit"] == price_unit for row in measured["source_receipts"])
    context = compose_recorded_market_context_v1(
        archive=archive,
        identity=MarketIdentityV1(**request["market_identity"]),
        bar_open_utc="2026-10-09T12:00:00+00:00",
        observed_at=RECEIVED,
        policy=ContextAdmissionPolicyV1(
            "explicit.fixture", {"price_o4": 300}, ("price_state_ref",)
        ),
    )
    assert context["as_of"] == "2026-10-09T13:00:05.000003Z"
    assert capture.capture_public_mark_window_v1(**capture_args, fetch_page=fetch) == manifest
    assert len(queries) == 2
    if is_xperp:
        with pytest.raises(ValueError, match="^MARKET_SOURCE_PRICE_UNIT_OR_FAMILY_MISMATCH$"):
            measure_recorded_market_horizon_v1(
                archive=archive,
                request={**request, "price_unit": "USDT per ETH"},
                evaluated_at_utc=RECEIVED,
            )
        log = json.loads(archive.request_log_path.read_bytes())
        log[0]["request_host"] = "www.okx.com"
        raw = json.dumps(log).encode()
        wrong_host_log = archive.request_log_path.with_name("wrong-host.json")
        wrong_host_log.write_bytes(raw)
        with pytest.raises(ValueError, match="^ORIGINAL_REQUEST_CONTRACT_MISMATCH$"):
            measure_recorded_market_horizon_v1(
                archive=replace(
                    archive,
                    request_log_path=wrong_host_log,
                    request_log_sha256=hashlib.sha256(raw).hexdigest(),
                ),
                request=request,
                evaluated_at_utc=RECEIVED,
            )


@pytest.mark.parametrize(
    "binding_patch,metadata_patch",
    [
        ({"canonical_instrument_id": "inst-eth-usdt-perp"}, {}),
        ({"mapping_digest": "0" * 64}, {}),
        ({}, {"instType": "SWAP"}),
        ({}, {"ctType": "inverse"}),
        ({}, {"settleCcy": "USDT"}),
        ({}, {"uly": "ETH-USDT"}),
        ({}, {"state": "suspend"}),
        (
            {
                "canonical_instrument_id": "ETH-USD_UM_XPERP-310328",
                "native_instrument_id": "ETH-USD_UM_XPERP-310328",
            },
            {"instId": "ETH-USD_UM_XPERP-310328"},
        ),
    ],
)
def test_wrong_xperp_binding_is_rejected_before_fetch_or_publish(
    capture_args, xperp_binding, binding_patch, metadata_patch
):
    args = with_binding(
        capture_args,
        {
            **xperp_binding,
            **binding_patch,
            "instrument_metadata": {**xperp_binding["instrument_metadata"], **metadata_patch},
        },
    )

    def must_not_fetch(_query):
        pytest.fail("must reject the binding before the first request")

    with pytest.raises(ValueError, match="^PILOT_INSTRUMENT_BINDING_MISMATCH$"):
        capture.capture_public_mark_window_v1(**args, fetch_page=must_not_fetch)
    assert not args["output"].exists()


def test_incomplete_window_is_not_published(capture_args):
    with pytest.raises(ValueError, match="^INCOMPLETE_ORIGINAL_MINUTE_COVERAGE$"):
        capture.capture_public_mark_window_v1(
            **capture_args, fetch_page=lambda query: mark_page(query, omit_last=True)
        )
    assert not capture_args["output"].exists()
    capture.capture_public_mark_window_v1(**capture_args, fetch_page=mark_page)
    assert (capture_args["output"] / "capture.json").is_file()
