"""Source validation counterexamples; constructed inputs, no market proof."""

from __future__ import annotations

import copy
from datetime import datetime, timezone

import pytest

from src.research.offline_recorded_mark_horizon_source_v1 import (
    ENDPOINT,
    aggregate_recorded_mark_minutes,
    read_bound_json,
)


@pytest.fixture
def source_args():
    start = int(datetime(2026, 10, 9, 11, tzinfo=timezone.utc).timestamp())
    rows = [[str((start + i * 60) * 1000), "100", "102", "99", "101", "1"] for i in range(180)]
    return {
        "pages": [
            {
                "raw_sha256": "a" * 64,
                "payload": {"code": "0", "data": rows},
                "request_record": {
                    "raw_response_sha256": "a" * 64,
                    "endpoint": ENDPOINT,
                    "query_params": {"instId": "ETH-USDT-SWAP", "bar": "1m"},
                    "http_status": 200,
                    "okx_code": "0",
                    "request_time_utc": "2026-10-09T20:03:10Z",
                    "response_time_utc": "2026-10-09T20:03:11Z",
                },
            }
        ],
        "instrument_binding": {
            "canonical_instrument_id": "inst-eth-usdt-perp",
            "native_instrument_id": "ETH-USDT-SWAP",
            "venue": "OKX",
            "instrument_metadata": {
                "instId": "ETH-USDT-SWAP",
                "instType": "SWAP",
                "settleCcy": "USDT",
                "uly": "ETH-USDT",
            },
        },
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "native_instrument_id": "ETH-USDT-SWAP",
        "horizon_start_utc": "2026-10-09T11:00:00Z",
        "n_bars": 2,
        "repository_sha": "a" * 40,
    }


@pytest.mark.parametrize("n", [1, 2, 3])
def test_bar_count_is_explicit_request_not_fixed_system_horizon(source_args, n):
    source_args["n_bars"] = n
    result = aggregate_recorded_mark_minutes(**source_args)
    assert len(result["bar_receipts"]) == n
    assert len(result["original_minute_rows"]) == n * 60
    assert result["bar_receipts"][-1]["available_at_utc"] == "2026-10-09T20:03:11Z"
    assert result["horizon_policy"] == "EXPLICIT_OFFLINE_REQUEST_ONLY_NOT_SYSTEM_DEFAULT"


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("missing", "INCOMPLETE_ORIGINAL_MINUTE_COVERAGE"),
        ("duplicate", "DUPLICATE_OR_CONFLICTING_SOURCE_MINUTE"),
        ("partial", "UNFINALIZED_SOURCE_MINUTE"),
        ("trade_price", "ORIGINAL_REQUEST_CONTRACT_MISMATCH"),
        ("wrong_instrument", "ORIGINAL_REQUEST_CONTRACT_MISMATCH"),
        ("wrong_interval", "ORIGINAL_REQUEST_CONTRACT_MISMATCH"),
        ("wrong_hash", "RAW_REQUEST_HASH_MISMATCH"),
        ("premature_receipt", "SOURCE_RECEIVED_BEFORE_MINUTE_CLOSE"),
        ("bad_price", "INVALID_ORIGINAL_PRICE"),
    ],
)
def test_false_completeness_and_source_substitution_rejected(source_args, mutation, reason):
    page = source_args["pages"][0]
    rows, record = page["payload"]["data"], page["request_record"]
    if mutation == "missing":
        rows.pop(10)
    elif mutation == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif mutation == "partial":
        rows[10][5] = "0"
    elif mutation == "trade_price":
        record["endpoint"] = "/api/v5/market/history-candles"
    elif mutation == "wrong_instrument":
        record["query_params"]["instId"] = "RSR-USDT-SWAP"
    elif mutation == "wrong_interval":
        record["query_params"]["bar"] = "1H"
    elif mutation == "wrong_hash":
        page["raw_sha256"] = "b" * 64
    elif mutation == "premature_receipt":
        record["request_time_utc"] = "2026-10-09T10:59:00Z"
        record["response_time_utc"] = "2026-10-09T11:00:01Z"
    elif mutation == "bad_price":
        rows[10][4] = "NaN"
    with pytest.raises(ValueError, match=reason):
        aggregate_recorded_mark_minutes(**source_args)


def test_raw_file_hash_is_checked_before_parsing(tmp_path):
    path = tmp_path / "raw.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
        read_bound_json(path, "a" * 64)
