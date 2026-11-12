"""Public mark capture fixtures with independent response receipt clocks."""

from dataclasses import replace
import hashlib
import json
import math

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

START = "2026-10-09T11:00:00Z"
RECEIVED = "2026-10-09T13:00:05.000003+00:00"


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
    raw = json.dumps(binding).encode()
    path = tmp_path / "binding.json"
    path.write_bytes(raw)
    return {
        "output": tmp_path / "archive",
        "start_utc": START,
        "hours": 2,
        "binding_path": path,
        "binding_sha256": hashlib.sha256(raw).hexdigest(),
        "repository_sha": "a" * 40,
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


def test_captured_pages_feed_existing_measurement_with_their_own_clocks(capture_args):
    queries = []

    def fetch(query):
        queries.append(query)
        return mark_page(query)

    manifest = capture.capture_public_mark_window_v1(**capture_args, fetch_page=fetch)
    assert manifest["available_at_utc"] == RECEIVED
    assert [q["limit"] for q in queries] == ["100", "20"]
    assert int(queries[0]["after"]) - int(queries[1]["after"]) == 100 * 60_000
    archive = capture.read_captured_mark_archive_v1(capture_args["output"])
    request = {
        "schema_version": REQUEST_SCHEMA,
        "market_identity": {
            "dataset_generation": "archive.fixture",
            "venue": "OKX",
            "instrument_ref": "inst-eth-usdt-perp",
            "native_instrument_ref": "ETH-USDT-SWAP",
        },
        "horizon_start_time_utc": START,
        "n_bars": 2,
        "o4_interval_id": "PT1H",
        "price_unit": "USDT per ETH",
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


def test_incomplete_window_is_not_published(capture_args):
    with pytest.raises(ValueError, match="^INCOMPLETE_ORIGINAL_MINUTE_COVERAGE$"):
        capture.capture_public_mark_window_v1(
            **capture_args, fetch_page=lambda query: mark_page(query, omit_last=True)
        )
    assert not capture_args["output"].exists()
    capture.capture_public_mark_window_v1(**capture_args, fetch_page=mark_page)
    assert (capture_args["output"] / "capture.json").is_file()
