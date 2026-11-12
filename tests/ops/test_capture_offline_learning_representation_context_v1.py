"""Exercise the public representation archive through the original context owner."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from scripts.ops import capture_offline_learning_mark_window_v1 as mark
from scripts.ops import capture_offline_learning_representation_context_v1 as representation
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.context_admission_v1 import (
    replay_admitted_market_context_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import utc


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
