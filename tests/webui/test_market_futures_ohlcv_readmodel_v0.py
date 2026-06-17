"""Tests for the read-only Market Futures OHLCV readmodel v0."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.market_futures_ohlcv_readmodel_v0 import (
    READMODEL_ID,
    MarketFuturesOhlcvReadmodelError,
    build_market_futures_ohlcv_readmodel,
)
from src.webui.market_futures_ohlcv_readmodel_v0.builder import FORBIDDEN_BAR_FIELDS
from src.webui.market_instrument_eligibility_v0 import is_eligible_market_dashboard_instrument

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0" / "complete_minimal"
)

_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "readmodel_id",
        "generated_at_iso",
        "source",
        "stale",
        "stale_reason",
        "non_authorizing",
        "series",
    }
)

_EXPECTED_BAR_KEYS = frozenset({"ts", "open", "high", "low", "close", "volume"})

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "order",
        "orders",
        "order_id",
        "create_order",
        "submit_order",
        "execute",
        "execution",
        "execution_authorized",
        "live_authorized",
        "ready_for_operator_arming",
        "armed",
        "enabled",
        "credentials",
        "credential",
        "api_key",
        "api_secret",
        "private_key",
        "authority_lift",
        "promotion",
        "approve",
        "approved",
        "side_recommendation",
        "trade_recommendation",
    }
)

_BITCOIN_TOKENS = ("BTC", "XBT", "BITCOIN")


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                out.add(key)
            _collect_object_keys(value, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


def test_market_futures_ohlcv_readmodel_builds_complete_minimal_fixture_v0() -> None:
    model = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)

    assert set(model.keys()) == _EXPECTED_TOP_LEVEL_KEYS
    assert model["readmodel_id"] == READMODEL_ID
    assert model["readmodel_id"] == "market_futures_ohlcv_readmodel.v0"
    assert model["generated_at_iso"] == "2026-05-27T00:00:00Z"
    assert model["source"] == "fixture:complete_minimal"
    assert model["stale"] is False
    assert model["stale_reason"] is None
    assert model["non_authorizing"] is True
    assert list(model["series"].keys()) == sorted(model["series"].keys())


def test_market_futures_ohlcv_readmodel_futures_only_no_bitcoin_symbols_v0() -> None:
    model = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)
    symbols = list(model["series"].keys())

    assert symbols
    for symbol in symbols:
        assert "/" not in symbol
        assert is_eligible_market_dashboard_instrument(symbol)
        upper = symbol.upper()
        for token in _BITCOIN_TOKENS:
            assert token not in upper


def test_market_futures_ohlcv_readmodel_ohlcv_bar_structure_and_order_v0() -> None:
    model = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)
    fixture = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))

    eth_series = model["series"]["ETHUSDT"]
    assert eth_series["timeframe"] == "1d"
    assert eth_series["bars"][0] == {
        "ts": "2026-04-13T00:00:00+00:00",
        "open": 3400.0,
        "high": 3413.6,
        "low": 3325.4448,
        "close": 3338.8,
        "volume": 1870.0,
    }

    fixture_bars = fixture["series"]["ETHUSDT"]["bars"]
    model_bars = eth_series["bars"]
    assert len(model_bars) == len(fixture_bars)
    assert [bar["ts"] for bar in model_bars] == [bar["ts"] for bar in fixture_bars]
    assert model_bars[-1]["volume"] == fixture_bars[-1]["volume"]

    for series in model["series"].values():
        for bar in series["bars"]:
            assert set(bar.keys()) == _EXPECTED_BAR_KEYS


def test_market_futures_ohlcv_readmodel_deterministic_output_v0() -> None:
    first = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)
    second = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)

    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_market_futures_ohlcv_readmodel_non_authorizing_contract_v0() -> None:
    model = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)
    assert model["non_authorizing"] is True


def test_market_futures_ohlcv_readmodel_no_forbidden_execution_authority_keys_v0() -> None:
    model = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)
    collected: set[str] = set()
    _collect_object_keys(model, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_market_futures_ohlcv_readmodel_does_not_mutate_input_fixture_v0() -> None:
    payload_path = FIXTURE_ROOT / "futures_ohlcv.json"
    before = payload_path.read_text(encoding="utf-8")
    before_payload = json.loads(before)

    build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)

    after = payload_path.read_text(encoding="utf-8")
    after_payload = json.loads(after)
    assert after == before
    assert after_payload == before_payload


def test_market_futures_ohlcv_readmodel_rejects_missing_payload_v0(tmp_path: Path) -> None:
    with pytest.raises(MarketFuturesOhlcvReadmodelError, match="missing futures OHLCV payload"):
        build_market_futures_ohlcv_readmodel(tmp_path)


def test_market_futures_ohlcv_readmodel_rejects_wrong_readmodel_id_v0(tmp_path: Path) -> None:
    payload = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    payload["readmodel_id"] = "wrong.v0"
    (tmp_path / "futures_ohlcv.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketFuturesOhlcvReadmodelError, match="readmodel_id"):
        build_market_futures_ohlcv_readmodel(tmp_path)


def test_market_futures_ohlcv_readmodel_rejects_authorizing_payload_v0(
    tmp_path: Path,
) -> None:
    payload = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    payload["non_authorizing"] = False
    (tmp_path / "futures_ohlcv.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketFuturesOhlcvReadmodelError, match="non_authorizing"):
        build_market_futures_ohlcv_readmodel(tmp_path)


@pytest.mark.parametrize("field", sorted(FORBIDDEN_BAR_FIELDS))
def test_market_futures_ohlcv_readmodel_rejects_forbidden_bar_fields_v0(
    tmp_path: Path,
    field: str,
) -> None:
    payload = deepcopy(
        json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    )
    payload["series"]["ETHUSDT"]["bars"][0][field] = "forbidden"
    (tmp_path / "futures_ohlcv.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(MarketFuturesOhlcvReadmodelError, match="forbidden fields"):
        build_market_futures_ohlcv_readmodel(tmp_path)
