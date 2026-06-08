from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SHAPE = _REPO_ROOT / "scripts/ops/u2c_packet_shape_v1.py"


def _load_shape_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_u2c_shape", _SHAPE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def shape() -> Any:
    return _load_shape_mod()


def test_normalize_market_type_maps_future_labels(shape: Any) -> None:
    assert shape.normalize_market_type("future") == "futures"
    assert shape.normalize_market_type("flexible_futures") == "perpetual"
    assert shape.normalize_market_type("perpetual") == "perpetual"


def test_flat_row_produces_nested_futures_producer_packet_shape(shape: Any) -> None:
    row = {
        "symbol": "PF_ETHUSD",
        "instrument_id": "PF_ETHUSD",
        "market_type": "perpetual",
        "exchange": "kraken_futures",
        "base_currency": "ETH",
        "quote_currency": "USD",
        "tick_size": 0.05,
        "contract_size": 1,
        "min_qty": 0.001,
        "min_notional": 1.0,
        "margin_asset": "USD",
        "settlement_asset": "USD",
        "max_leverage": 50,
        "fetched_at": "2026-06-08T18:00:00Z",
        "last_price": 3500.0,
        "mark_price": 3500.0,
        "index_price": 3500.0,
        "vol24h": 1000.0,
        "bid": 3499.0,
        "ask": 3501.0,
        "spread": 2.0,
        "funding_rate": 0.0001,
        "open_interest": 1000.0,
        "active": True,
        "missing_fields": [],
        "missing_provider_metadata": [],
    }
    packet = shape.flat_row_to_nested_packet(
        row,
        candidate_id="c-PF_ETHUSD",
        source_universe_size=3,
        rank=1,
    )
    assert "candidate" in packet
    assert "ranking" in packet
    assert "instrument" in packet
    assert "provenance" in packet
    assert packet["candidate"]["symbol"] == "PF_ETHUSD"
    assert packet["candidate"]["live_authorization"] is False
    assert packet["ranking"]["rank"] == 1
    assert packet["ranking"]["score"] is None
    assert packet["instrument"]["complete"] is True
    assert packet["instrument"]["candidate_validation_complete"] is True
    assert packet["provenance"]["freshness_state"] == "fresh"
    assert "strategy_score" not in str(packet)


def test_kraken_like_row_maps_provider_fields_without_dummy_fills(shape: Any) -> None:
    inst = {
        "symbol": "PF_ETHUSD",
        "quote": "USD",
        "impactMidSize": 5.1,
        "retailMarginLevels": [
            {"numNonContractUnits": 0.0, "initialMargin": 0.01, "maintenanceMargin": 0.005}
        ],
    }
    provider = shape.extract_kraken_provider_instrument_fields(inst)
    assert provider["min_qty"] == 5.1
    assert provider["margin_asset"] == "USD"
    assert provider["settlement_asset"] == "USD"
    assert provider["max_leverage"] == 100.0
    assert provider["missing_provider_metadata"] == ["min_notional"]


def test_kraken_like_row_candidate_validation_complete_without_min_notional(shape: Any) -> None:
    row = {
        "symbol": "PF_ETHUSD",
        "instrument_id": "PF_ETHUSD",
        "market_type": "perpetual",
        "exchange": "kraken_futures",
        "base_currency": "ETH",
        "quote_currency": "USD",
        "tick_size": 0.05,
        "contract_size": 1,
        "min_qty": 5.1,
        "margin_asset": "USD",
        "settlement_asset": "USD",
        "max_leverage": 100.0,
        "missing_provider_metadata": ["min_notional"],
        "fetched_at": "2026-06-08T18:00:00Z",
        "last_price": 3500.0,
        "mark_price": 3500.0,
        "missing_fields": ["funding_rate"],
        "market_data_missing_fields": ["funding_rate"],
        "active": True,
    }
    packet = shape.flat_row_to_nested_packet(
        row,
        candidate_id="c-PF_ETHUSD",
        source_universe_size=1,
    )
    assert packet["instrument"]["complete"] is False
    assert packet["instrument"]["candidate_validation_complete"] is True
    assert packet["instrument"]["missing_fields"] == []
    assert packet["instrument"]["missing_provider_metadata"] == ["min_notional"]
    assert "funding_rate" not in packet["instrument"]["missing_fields"]
    assert "funding_rate" in packet["provenance"]["market_data_missing_fields"]


def test_incomplete_flat_row_keeps_instrument_incomplete(shape: Any) -> None:
    row = {
        "symbol": "PF_ADAUSD",
        "instrument_id": "PF_ADAUSD",
        "market_type": "perpetual",
        "exchange": "kraken_futures",
        "base_currency": "ADA",
        "quote_currency": "USD",
        "tick_size": 0.0001,
        "contract_size": 1,
        "fetched_at": "2026-06-08T18:00:00Z",
        "last_price": 1.0,
        "missing_fields": ["vol24h"],
        "active": True,
    }
    packet = shape.flat_row_to_nested_packet(
        row,
        candidate_id="c-PF_ADAUSD",
        source_universe_size=1,
    )
    assert packet["instrument"]["complete"] is False
    assert packet["instrument"]["candidate_validation_complete"] is False
    assert packet["instrument"]["missing_fields"] == []
    assert "min_qty" in packet["instrument"]["completeness_reason"]
