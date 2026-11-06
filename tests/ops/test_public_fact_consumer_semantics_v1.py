"""Canonical public facts retain instrument, clock and quote meaning at consumers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.consumer_adapters_v1 import (
    finalized_facts_to_raw_mark_candles_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    DurableStoreError,
    append_fact_v1,
    default_store_paths_v1,
    load_all_facts_v1,
)


def _fact(kind: str, *, native: str = "ETH-USDT-SWAP", event: int = 1793836800000) -> dict:
    return {
        "fact_kind": kind,
        "instrument": {"venue_native_id": native},
        "provenance": {"transport": "injected_test", "endpoint_or_channel": "test-only-source"},
        "timestamps": {
            "venue_event_time_ms": event,
            "captured_at": "2026-11-05T00:00:01Z",
            "effective_at": None,
            "source_clock_class": "VENUE_EVENT_TIME",
        },
        "interval_start_ms": event,
        "confirm": "1",
        "mark_px": "100.125",
        "bid_px": "100.1",
        "ask_px": "100.2",
    }


def test_canonical_scalar_quote_and_nested_capture_reach_economic_input(tmp_path: Path) -> None:
    paths = default_store_paths_v1(tmp_path)
    mark = _fact("FinalizedPt1mMarkFactV1")
    quote = _fact("BestBidAskFactV1")
    append_fact_v1(paths, mark)
    append_fact_v1(paths, quote)
    result = PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
        venue_native_id="ETH-USDT-SWAP"
    )
    assert result.marks[0].receive_or_capture_timestamp == mark["timestamps"]["captured_at"]
    assert result.ticker is not None
    assert (result.ticker.bid_px, result.ticker.ask_px) == ("100.1", "100.2")
    assert result.ticker.source_class == "BestBidAskFactV1"
    assert result.ticker.source_endpoint == "test-only-source"
    assert result.ticker.ticker_event_timestamp == str(quote["timestamps"]["venue_event_time_ms"])
    assert result.ticker.capture_or_receive_timestamp == quote["timestamps"]["captured_at"]


def test_latest_quote_is_chronological_and_not_append_order(tmp_path: Path) -> None:
    paths = default_store_paths_v1(tmp_path)
    newest = _fact("BestBidAskFactV1", event=1793836802000)
    older = _fact("BestBidAskFactV1")
    older["bid_px"] = "90"
    newest["bid_px"] = "105"
    for fact in (older, newest, older):
        append_fact_v1(paths, fact)
    result = PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
        venue_native_id="ETH-USDT-SWAP"
    )
    assert result.ticker is not None
    assert result.ticker.bid_px == "105"


def test_mark_conversion_does_not_relabel_another_instrument() -> None:
    own = _fact("FinalizedPt1mMarkFactV1")
    foreign = _fact("FinalizedPt1mMarkFactV1", native="BTC-USDT-SWAP")
    result = finalized_facts_to_raw_mark_candles_v1(
        [own, foreign], venue_native_id="ETH-USDT-SWAP", captured_at="2026-11-05T00:05:00Z"
    )
    assert len(result) == 1
    assert result[0].receive_or_capture_timestamp == own["timestamps"]["captured_at"]


def test_missing_capture_does_not_become_a_historical_literal(tmp_path: Path) -> None:
    mark = _fact("FinalizedPt1mMarkFactV1")
    del mark["timestamps"]["captured_at"]
    append_fact_v1(default_store_paths_v1(tmp_path), mark)
    with pytest.raises(ValueError, match="captur"):
        PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
            venue_native_id="ETH-USDT-SWAP"
        )


@pytest.mark.parametrize("damage", ["payload", "schema", "torn", "raw_legacy"])
def test_historical_readback_rejects_damage_preserving_original(
    tmp_path: Path, damage: str
) -> None:
    paths = default_store_paths_v1(tmp_path)
    append_fact_v1(paths, _fact("FinalizedPt1mMarkFactV1"))
    row = json.loads(paths.finalized_facts.read_text())
    if damage == "payload":
        row["payload"]["mark_px"] = "999"
    elif damage == "schema":
        row["schema_version"] = "unknown"
    elif damage == "raw_legacy":
        row = row["payload"]
    original = json.dumps(row) + ("" if damage == "torn" else "\n")
    paths.finalized_facts.write_text(original)
    with pytest.raises(DurableStoreError):
        load_all_facts_v1(paths)
    assert paths.finalized_facts.read_text() == original


def test_actual_rest_and_ws_normalizers_survive_store_to_economic_consumer(tmp_path: Path) -> None:
    from src.ops.peak_trade_public_market_data_runtime_v1.rest_recovery_v1 import (
        parse_finalized_pt1m_mark_rows_v1,
    )
    from src.ops.peak_trade_public_market_data_runtime_v1.ws_channel_normalizers_v1 import (
        normalize_ws_payload_to_canonical_facts_v1,
    )

    instrument = {
        "canonical_instrument_id": "inst-eth-usdt-perp",
        "venue_native_id": "ETH-USDT-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "test-only-mapping",
    }
    captured = "2026-11-05T00:01:00Z"
    # Injected public payloads, processed by the real producers; no source-authenticity claim.
    marks = parse_finalized_pt1m_mark_rows_v1(
        {"data": [["1793836800000", "100", "101", "99", "100.5", "1"]]},
        instrument_ref_dict=instrument,
        captured_at=captured,
        transport="injected_test",
    )
    quotes = normalize_ws_payload_to_canonical_facts_v1(
        {
            "arg": {"channel": "books5", "instId": "ETH-USDT-SWAP"},
            "data": [{"ts": "1793836800000", "bids": [["100.1", "2"]], "asks": [["100.2", "3"]]}],
        },
        instrument_ref=instrument,
        captured_at=captured,
        session_id="test-only",
    )
    paths = default_store_paths_v1(tmp_path)
    for fact in [marks[0].to_dict(), *quotes]:
        append_fact_v1(paths, fact)
    result = PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
        venue_native_id="ETH-USDT-SWAP"
    )
    assert result.marks[0].mark_px == "100.5"
    assert result.marks[0].receive_or_capture_timestamp == captured
    assert result.ticker is not None
    assert (result.ticker.bid_px, result.ticker.ask_px) == ("100.1", "100.2")
    assert result.ticker.source_class == "BestBidAskFactV1"
    assert result.ticker.source_endpoint == "books5"


def test_quote_capture_order_preserves_nanoseconds(tmp_path: Path) -> None:
    paths = default_store_paths_v1(tmp_path)
    for fraction, bid in [("000000002", "101"), ("000000001", "100")]:
        fact = _fact("BestBidAskFactV1")
        fact["timestamps"]["captured_at"] = f"2026-11-05T00:00:01.{fraction}Z"
        fact["bid_px"] = bid
        append_fact_v1(paths, fact)
    result = PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
        venue_native_id="ETH-USDT-SWAP"
    )
    assert result.ticker is not None
    assert result.ticker.bid_px == "101"


def test_conflicting_same_time_quotes_are_not_selected_by_file_order(tmp_path: Path) -> None:
    paths = default_store_paths_v1(tmp_path)
    fact = _fact("BestBidAskFactV1")
    append_fact_v1(paths, fact)
    fact["bid_px"] = "100.15"
    append_fact_v1(paths, fact)
    with pytest.raises(ValueError, match="conflicting public quotes"):
        PublicRuntimeEconomicMdPublicSourceV1(tmp_path).collect_instrument_raw_input_v1(
            venue_native_id="ETH-USDT-SWAP"
        )
