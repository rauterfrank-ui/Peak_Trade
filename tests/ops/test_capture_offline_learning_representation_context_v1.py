"""Exercise the public representation archive through the original context owner."""

from datetime import datetime, timedelta, timezone
from functools import partial
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ops import capture_offline_learning_mark_window_v1 as mark
from scripts.ops import capture_offline_learning_representation_context_v1 as representation
from scripts.ops import route_offline_paired_market_representation_meta_v1 as meta_route
from scripts.ops import run_offline_learning_mark_measurement_v1 as measurement
from scripts.ops import run_offline_learning_representation_sequence_v1 as cohort
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    replay_admitted_market_context_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    read_frozen_market_forecast_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    seal_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_recorded_market_replay_v1 import (
    recorded_market_target_from_frozen_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import (
    market_request,
    seed_frozen_forecast,
    utc,
)


@pytest.fixture
def public_capture(tmp_path, monkeypatch):
    opened = datetime(2026, 11, 12, 6, tzinfo=timezone.utc)
    clock = [opened + timedelta(hours=1, seconds=1)]
    monkeypatch.setattr(mark, "_utc_now", lambda: utc(clock[0]))
    monkeypatch.setattr(representation, "_utc_now", lambda: utc(clock[0]))
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "venue": "OKX",
                "canonical_instrument_id": "inst-eth-usdt-perp",
                "native_instrument_id": mark.NATIVE_INSTRUMENT,
                "instrument_metadata": {
                    "instId": mark.NATIVE_INSTRUMENT,
                    "instType": "SWAP",
                    "settleCcy": "USDT",
                    "uly": "ETH-USDT",
                    "ctVal": "0.1",
                    "ctValCcy": "ETH",
                },
            }
        )
    )

    def mark_response(query):
        rows = [
            [str(int(query["after"]) - 60_000 * i), "100", "101", "99", "100", "1"]
            for i in range(1, int(query["limit"]) + 1)
        ]
        return 200, json.dumps({"code": "0", "data": rows}).encode()

    mark_root = tmp_path / "mark"
    mark.capture_public_mark_window_v1(
        output=mark_root,
        start_utc=utc(opened),
        hours=1,
        binding_path=binding,
        binding_sha256=hashlib.sha256(binding.read_bytes()).hexdigest(),
        repository_sha="a" * 40,
        fetch_page=mark_response,
    )
    end = opened + timedelta(hours=1, minutes=20)
    clock[0] = end + timedelta(seconds=5)
    inputs = {
        "output": tmp_path / "representation",
        "mark_archive": mark_root,
        "ohlcv_end_utc": utc(end),
        "trade_count": 2,
        "max_age_seconds_by_role": {"price_o4": 3600, "flow": 60, "microstructure": 300},
    }
    end_ms = int(end.timestamp() * 1000)
    responses = {
        representation.INSTRUMENTS_PATH: [
            {
                "instId": mark.NATIVE_INSTRUMENT,
                "instType": "SWAP",
                "uly": "ETH-USDT",
                "instFamily": "ETH-USDT",
                "ctType": "linear",
                "ctVal": "0.1",
                "ctValCcy": "ETH",
                "ctMult": "1",
                "settleCcy": "USDT",
                "state": "live",
            }
        ],
        representation.CANDLES_PATH: [
            [
                str(end_ms - 60_000 * i),
                str(103 - i / 10),
                "110",
                "90",
                str(104 - i / 10),
                "1000",
                "4",
                "400",
                "1",
            ]
            for i in range(1, representation.REQUIRED_WARMUP_ROWS + 1)
        ],
        representation.TRADES_REST_PATH: [
            {
                "instId": mark.NATIVE_INSTRUMENT,
                "tradeId": "2",
                "side": "sell",
                "px": "100",
                "sz": "1",
                "ts": str(end_ms + 2000),
            },
            {
                "instId": mark.NATIVE_INSTRUMENT,
                "tradeId": "1",
                "side": "buy",
                "px": "100",
                "sz": "2",
                "ts": str(end_ms + 1000),
            },
        ],
    }
    requests = []

    def fetch(path, query):
        requests.append((path, query))
        clock[0] += timedelta(seconds=1)
        return 200, json.dumps({"code": "0", "data": responses[path]}).encode()

    return {**inputs, "fetch": fetch}, clock, responses, requests


def test_archive_admits_actual_trade_units_and_final_bar_grid(public_capture):
    inputs, clock, _, requests = public_capture
    context = representation.capture_representation_context_v1(**inputs)
    assert [path for path, _ in requests] == [
        representation.INSTRUMENTS_PATH,
        representation.CANDLES_PATH,
        representation.TRADES_REST_PATH,
    ]
    assert requests[1][1]["after"] == str(
        int(representation.instant_v1(inputs["ohlcv_end_utc"]).timestamp()) * 1000
    )
    assert context["context_status"] == "VALID"
    assert context == replay_admitted_market_context_v1(context)
    assert context["as_of"] == utc(clock[0])
    bindings = context["source_bindings"]
    trade_sizes = {
        row["payload"]["trade_id"]: row["payload"]["size"]
        for row in bindings
        if row["role"] == "flow"
    }
    assert trade_sizes == {"1": "0.2", "2": "0.1"}
    bars = [row for row in bindings if row["role"] == "microstructure"]
    assert len(bars) == 21
    assert all(row["payload"]["volume"] == "4" and row["units"]["volume"] == "BASE" for row in bars)
    flow = context["market_context"]["flow_state_ref"]["state_ref"]
    assert float(context["derivations"][flow]["signed_net_notional"]) == pytest.approx(10.0)

    output = Path(inputs["output"])
    with pytest.raises(ValueError, match="^REPRESENTATION_CAPTURE_NOT_YET_AVAILABLE$"):
        representation.read_recorded_representation_context_v1(
            output, cutoff_utc=utc(clock[0] - timedelta(microseconds=1))
        )
    clock[0] += timedelta(hours=1)
    assert representation.capture_representation_context_v1(**inputs) == context
    assert len(requests) == 3
    path = output / "trades.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="^SOURCE_SHA256_MISMATCH$"):
        representation.read_recorded_representation_context_v1(output, cutoff_utc=utc(clock[0]))


@pytest.mark.parametrize(
    ("corruption", "reason"),
    [
        ("trade_size_unit", "OKX_CONTRACT_VALUE_MISMATCH"),
        ("missing_candle", "OKX_OHLCV_WINDOW_INCOMPLETE"),
        ("unfinalized_candle", "OKX_FINAL_OHLCV_ROW_REQUIRED"),
        ("future_trade", "OKX_TRADE_OUTSIDE_KNOWLEDGE_WINDOW"),
    ],
)
def test_invalid_originals_do_not_publish(public_capture, corruption, reason):
    inputs, clock, responses, _ = public_capture
    if corruption == "trade_size_unit":
        responses[representation.INSTRUMENTS_PATH][0]["ctVal"] = "0.01"
    elif corruption == "missing_candle":
        responses[representation.CANDLES_PATH].pop()
    elif corruption == "unfinalized_candle":
        responses[representation.CANDLES_PATH][0][-1] = "0"
    else:
        responses[representation.TRADES_REST_PATH][0]["ts"] = str(
            int((clock[0] + timedelta(minutes=1)).timestamp() * 1000)
        )
    with pytest.raises(ValueError, match=f"^{reason}$"):
        representation.capture_representation_context_v1(**inputs)
    assert not Path(inputs["output"]).exists()


def test_declared_cohort_builds_eight_original_jobs_and_persists_the_comparison(
    public_capture, tmp_path, monkeypatch
):
    inputs, clock, responses, _ = public_capture
    seed_context = representation.capture_representation_context_v1(**inputs)
    store = tmp_path / "store"
    first_start = clock[0].replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    request = {**market_request(first_start), "market_identity": seed_context["identity"]}
    seed = seed_frozen_forecast(store, seed_context, request)
    archive = mark.read_captured_mark_archive_v1(inputs["mark_archive"])
    monkeypatch.setattr(measurement, "_utc_now", lambda: utc(clock[0]))
    measurement.schedule_recorded_market_measurement_v1(
        store_root=store,
        job_key=seed["job_key"],
        binding_path=archive.binding_path,
        binding_sha256=archive.binding_sha256,
        repository_sha=archive.repository_sha,
        capture_delay_seconds=60,
    )
    advance = measurement.advance_recorded_market_measurement_v1
    captures = []
    contexts = []

    def complete_fixture(**locator):
        if "capture_window" in locator:
            return advance(**locator)
        folder = store / ".intelligence-integration-v1" / digest_v1(locator["job_key"])
        if (folder / "calibration_ack.json").is_file():
            return advance(**locator)
        frozen = read_frozen_market_forecast_v1(**locator)
        target = recorded_market_target_from_frozen_v1(frozen)
        horizon = measurement.instant_v1(target["horizon_start_time_utc"])
        end = horizon + timedelta(hours=2)
        clock[0] = end + timedelta(minutes=1)
        index = len(captures)
        captures.append(horizon)

        def fetch(query):
            clock[0] += timedelta(seconds=1)
            rows = []
            for offset in range(1, int(query["limit"]) + 1):
                opened = int(query["after"]) - 60_000 * offset
                close = (
                    100
                    + index
                    + (
                        (index * index) % 7 + 1
                        if opened >= (end - timedelta(hours=1)).timestamp() * 1000
                        else 0
                    )
                )
                rows.append([str(opened), str(close), str(close), str(close), str(close), "1"])
            return 200, json.dumps({"code": "0", "data": rows}).encode()

        return advance(
            **locator,
            capture_window=lambda **kwargs: mark.capture_public_mark_window_v1(
                **kwargs, fetch_page=fetch
            ),
        )

    def capture_context(path, query):
        index = len(captures)
        contexts.append((index, path))
        if path == representation.INSTRUMENTS_PATH:
            rows = responses[path]
        elif path == representation.CANDLES_PATH:
            rows = [
                [
                    str(int(query["after"]) - 60_000 * offset),
                    "100",
                    "112",
                    "99",
                    str(110 - offset / 10),
                    "500",
                    str(1 + (index * index) % 13),
                    "100",
                    "1",
                ]
                for offset in range(1, int(query["limit"]) + 1)
            ]
        else:
            event_ms = int(clock[0].timestamp() * 1000) - 1000
            rows = [
                {
                    "instId": mark.NATIVE_INSTRUMENT,
                    "tradeId": str(2 * index + offset),
                    "side": "buy" if index % 2 else "sell",
                    "px": "100",
                    "sz": str(index + offset),
                    "ts": str(event_ms + offset),
                }
                for offset in (1, 2)
            ]
        clock[0] += timedelta(seconds=1)
        return 200, json.dumps({"code": "0", "data": rows}).encode()

    monkeypatch.setattr(measurement, "advance_recorded_market_measurement_v1", complete_fixture)
    monkeypatch.setattr(
        cohort,
        "prepare_recorded_representation_successor_v1",
        partial(cohort.prepare_recorded_representation_successor_v1, fetch=capture_context),
    )
    args = {
        "store_root": store,
        "seed_job_key": seed["job_key"],
        "seed_context_root": inputs["output"],
        "next_starts_utc": [utc(first_start + timedelta(hours=3 * index)) for index in range(1, 8)],
        "fit_window_count": 6,
        "validation_fraction": 0.25,
        "repository_sha": archive.repository_sha,
        "forecast_context_max_age_seconds": 300,
        "wait": False,
    }
    assert cohort.run_representation_cohort_v1(**args) == 0
    (comparison_path,) = store.glob(
        ".intelligence-integration-v1/*/paired_representation_comparison.json"
    )
    original_bytes = comparison_path.read_bytes()
    comparison = json.loads(original_bytes)
    assert comparison["status"] == "MEASURED_CHRONOLOGICAL_HOLDOUT"
    assert comparison["paired_case_count"] == 8
    assert comparison["stage_comparison"]["walk_forward_summary"]["holdout_rows"] == 2
    assert [case["split"] for case in comparison["cases"]] == ["FIT"] * 6 + ["HOLDOUT"] * 2
    assert len(captures) == 8 and len(contexts) == 7 * 3
    assert cohort.run_representation_cohort_v1(**args) == 0
    assert comparison_path.read_bytes() == original_bytes
    assert len(captures) == 8 and len(contexts) == 7 * 3
    with pytest.raises(ValueError, match="^IMMUTABLE_ATTACHMENT_CONFLICT$"):
        cohort.run_representation_cohort_v1(**{**args, "validation_fraction": 0.3})

    locator = {"store_root": store, "seed_job_key": seed["job_key"]}
    receipt = meta_route.route_recorded_representation_cohort_v1(**locator)
    assert receipt["status"] == "LEARNING_RESEARCH_PLAN_READY"
    assert receipt["comparison_digest"] == comparison["exact_content_digest"]
    handoff = receipt["handoff"]
    evidence = handoff["evidence"]
    assert (
        evidence["representation_lineage"]["additional_feature"] == "signed_return_volume_pressure"
    )
    assert (
        evidence["measurement"]["delta_b0_minus_b1"]
        == comparison["stage_comparison"]["challenger_delta"]
    )
    assert handoff["research_plan"]["research_purpose"] == "INVESTIGATE_FEATURE_USEFULNESS"
    assert (
        handoff["research_plan"]["learning_representation_lineage_ref"]
        == evidence["representation_lineage_ref"]
    )
    routing_cycle = handoff["routing_cycle"]
    route = routing_cycle["routing_result"]
    assert (
        route["learning_consumer_invoked"] is True
        and route["optimization_consumer_invoked"] is False
    )
    nested = routing_cycle["meta_evidence"]["meta_learning_evidence"]
    assert nested["source_experiment_ids"] == []
    assert nested["source_optimization_experiment_evidence_digest"] is None
    encoded = nested["predictive_evidence_features"]
    assert json.loads(encoded["utf8"]) == evidence["measurement"]
    assert encoded["sha256"] == digest_v1(evidence["measurement"])
    output = comparison_path.with_name("paired_representation_meta.json")
    assert output.read_bytes() == bytes_v1(receipt)
    assert meta_route.route_recorded_representation_cohort_v1(**locator) == receipt
    assert len(captures) == 8 and len(contexts) == 7 * 3

    forged = {name: value for name, value in comparison.items() if name != "exact_content_digest"}
    forged["stage_comparison"] = {**forged["stage_comparison"], "challenger_delta": 99.0}
    comparison_path.write_bytes(bytes_v1(seal_v1(forged)))
    with pytest.raises(ValueError, match="^PAIRED_META_ORIGINAL_COMPARISON_MISMATCH$"):
        meta_route.route_recorded_representation_cohort_v1(**locator)
    assert output.read_bytes() == bytes_v1(receipt)
