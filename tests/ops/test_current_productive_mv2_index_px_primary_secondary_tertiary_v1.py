"""Focused contracts for MV2 INDEX_PX primary/secondary/tertiary join helpers.

No venue network. No POST. No markPx→INDEX_PX substitution.
"""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
    extract_index_px_from_index_tickers_payload_v1,
    extract_mark_and_index_from_payload_v1,
    extract_ticker_fields_v1,
    resolve_index_px_primary_secondary_tertiary_v1,
    resolve_index_ticker_inst_id_v1,
)


def test_resolve_index_ticker_inst_id_strips_swap_suffix() -> None:
    assert resolve_index_ticker_inst_id_v1("0G-USDT-SWAP") == "0G-USDT"
    assert resolve_index_ticker_inst_id_v1("BTC-USDT-SWAP") == "BTC-USDT"
    assert resolve_index_ticker_inst_id_v1("0G-USDT") == "0G-USDT"
    assert resolve_index_ticker_inst_id_v1("  ETH-USDT-SWAP  ") == "ETH-USDT"


def test_endpoint_constant_is_canonical_index_tickers_path() -> None:
    assert ENDPOINT_MARKET_INDEX_TICKERS == "/api/v5/market/index-tickers"


def test_primary_mark_idx_px_wins_over_secondary_and_tertiary() -> None:
    resolved = resolve_index_px_primary_secondary_tertiary_v1(
        index_from_mark=1.11,
        index_from_ticker=2.22,
        index_from_index_tickers=3.33,
    )
    assert resolved == 1.11


def test_secondary_ticker_idx_px_when_primary_absent() -> None:
    resolved = resolve_index_px_primary_secondary_tertiary_v1(
        index_from_mark=None,
        index_from_ticker=2.22,
        index_from_index_tickers=3.33,
    )
    assert resolved == 2.22


def test_tertiary_index_tickers_when_primary_and_secondary_absent() -> None:
    resolved = resolve_index_px_primary_secondary_tertiary_v1(
        index_from_mark=None,
        index_from_ticker=None,
        index_from_index_tickers=3.33,
    )
    assert resolved == 3.33


def test_all_absent_fails_closed_none() -> None:
    assert (
        resolve_index_px_primary_secondary_tertiary_v1(
            index_from_mark=None,
            index_from_ticker=None,
            index_from_index_tickers=None,
        )
        is None
    )


def test_extract_index_tickers_accepts_matching_inst_id() -> None:
    payload = {"code": "0", "data": [{"instId": "0G-USDT", "idxPx": "0.2589"}]}
    assert extract_index_px_from_index_tickers_payload_v1(payload, wanted="0G-USDT") == 0.2589


def test_extract_index_tickers_rejects_cross_instrument() -> None:
    payload = {"code": "0", "data": [{"instId": "BTC-USDT", "idxPx": "100.0"}]}
    assert extract_index_px_from_index_tickers_payload_v1(payload, wanted="0G-USDT") is None


def test_extract_index_tickers_rejects_malformed_nonpositive_nonfinite() -> None:
    for bad in ("", "0", "-1", "nan", "inf", None):
        payload = {"code": "0", "data": [{"instId": "0G-USDT", "idxPx": bad}]}
        assert extract_index_px_from_index_tickers_payload_v1(payload, wanted="0G-USDT") is None


def test_extract_index_tickers_missing_payload_fails_closed() -> None:
    assert extract_index_px_from_index_tickers_payload_v1(None, wanted="0G-USDT") is None
    assert (
        extract_index_px_from_index_tickers_payload_v1({"code": "0", "data": []}, wanted="0G-USDT")
        is None
    )


def test_mark_px_is_not_used_as_index_px() -> None:
    mark_payload = {
        "code": "0",
        "data": [{"instId": "0G-USDT-SWAP", "markPx": "0.2582"}],
    }
    mark_px, index_from_mark = extract_mark_and_index_from_payload_v1(
        mark_payload, native_id="0G-USDT-SWAP"
    )
    assert mark_px == 0.2582
    assert index_from_mark is None
    ticker_payload = {
        "code": "0",
        "data": [
            {
                "instId": "0G-USDT-SWAP",
                "bidPx": "0.258",
                "askPx": "0.259",
                "vol24h": "10",
            }
        ],
    }
    _bid, _ask, _vol, index_from_ticker = extract_ticker_fields_v1(
        ticker_payload, native_id="0G-USDT-SWAP"
    )
    assert index_from_ticker is None
    # markPx must not leak into INDEX_PX precedence
    assert (
        resolve_index_px_primary_secondary_tertiary_v1(
            index_from_mark=index_from_mark,
            index_from_ticker=index_from_ticker,
            index_from_index_tickers=None,
        )
        is None
    )
