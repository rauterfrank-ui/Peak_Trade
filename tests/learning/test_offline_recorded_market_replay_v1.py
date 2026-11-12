"""Exact clock and source bindings at the learning-side archive ingress."""

from datetime import datetime, timezone
import hashlib
import json
import math

import pytest

from src.learning.deterministic_decision_outcome_v0.independent_market_horizon_v1 import (
    REQUEST_SCHEMA,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    ContextAdmissionPolicyV1,
    replay_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    MarketIdentityV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    RecordedMarkArchiveV1,
    compose_recorded_market_context_v1,
    measure_recorded_market_horizon_v1,
)
from src.research.offline_recorded_mark_horizon_source_v1 import ENDPOINT


def test_archived_consumers_bind_files_and_reject_early_reads(tmp_path):
    def write(name, value):
        data = json.dumps(value).encode("utf-8")
        path = tmp_path / name
        path.write_bytes(data)
        return path, hashlib.sha256(data).hexdigest()

    identity = MarketIdentityV1("archive.test", "OKX", "inst-eth-usdt-perp", "ETH-USDT-SWAP")
    received = "2026-10-09T13:03:11.123456Z"
    opened = datetime(2026, 10, 9, 11, tzinfo=timezone.utc)
    hour = opened.isoformat().replace("+00:00", "Z")
    rows = [
        [str(int(opened.timestamp() + minute * 60) * 1000), "100", "102", "99", "101", "1"]
        for minute in range(120)
    ]
    rows[-1][4] = "102"
    raw = write("raw.json", {"code": "0", "data": rows})
    log = write(
        "request_log.json",
        [
            {
                "raw_response_sha256": raw[1],
                "endpoint": ENDPOINT,
                "query_params": {"instId": identity.native_instrument_ref, "bar": "1m"},
                "http_status": 200,
                "okx_code": "0",
                "request_time_utc": "2026-10-09T13:03:10Z",
                "response_time_utc": received,
            }
        ],
    )
    binding = write(
        "binding.json",
        {
            "canonical_instrument_id": identity.instrument_ref,
            "native_instrument_id": identity.native_instrument_ref,
            "venue": identity.venue,
            "instrument_metadata": {
                "instId": identity.native_instrument_ref,
                "instType": "SWAP",
                "settleCcy": "USDT",
                "uly": "ETH-USDT",
            },
        },
    )
    archive = RecordedMarkArchiveV1(*raw, *log, *binding, "a" * 40)
    context_args = {
        "archive": archive,
        "identity": identity,
        "bar_open_utc": hour,
        "policy": ContextAdmissionPolicyV1(
            "explicit.test", {"price_o4": 7200}, ("price_state_ref",)
        ),
    }
    context = compose_recorded_market_context_v1(**context_args, observed_at=received)
    assert replay_admitted_market_context_v1(context) == context
    assert context["source_bindings"][0]["captured_at"] == "2026-10-09T13:03:11.123456+00:00"
    request = {
        "schema_version": REQUEST_SCHEMA,
        "market_identity": identity.payload(),
        "horizon_start_time_utc": hour,
        "n_bars": 2,
        "o4_interval_id": "PT1H",
        "price_unit": "USDT per ETH",
        "price_family": "MARK_PRICE",
        "source_kind": "RECORDED_PUBLIC_MD",
        "max_end_age_seconds": 300,
        "expected_price_basis_kind": "O4_BAR_CLOSE_FINALIZED",
    }
    observation = measure_recorded_market_horizon_v1(
        archive=archive, request=request, evaluated_at_utc=received
    )
    assert observation["measurement"]["log_return"] == pytest.approx(math.log(102 / 101))
    assert observation["evaluated_at_utc"] == received

    archive.raw_path.unlink()
    earlier = "2026-10-09T13:03:11.123455999Z"
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        compose_recorded_market_context_v1(**context_args, observed_at=earlier)
    with pytest.raises(ValueError, match="^ARCHIVE_RESPONSE_NOT_YET_AVAILABLE$"):
        measure_recorded_market_horizon_v1(
            archive=archive, request=request, evaluated_at_utc=earlier
        )
