"""Dedicated contract tests for canonical market futures OHLCV runtime v0."""

from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.webui.market_futures_ohlcv_readmodel_v0 import (
    READMODEL_ID,
    build_market_futures_ohlcv_readmodel,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    build_market_futures_ohlcv_display_context,
    enabled_explicitly_on,
    resolve_futures_ohlcv_series_for_symbol,
    resolved_bundle_root_or_none,
)
from src.webui.market_instrument_eligibility_v0 import is_eligible_market_dashboard_instrument

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    PROJECT_ROOT / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0" / "complete_minimal"
)
CANONICAL_SYMBOL = "ETHUSDT"
CANONICAL_TIMEFRAME = "1d"

_EXPECTED_DISPLAY_CONTEXT_KEYS = frozenset(
    {
        "gate_enabled",
        "display_status",
        "readmodel_id",
        "non_authorizing",
        "stale",
        "stale_reason",
        "source",
        "generated_at_iso",
        "series",
    }
)

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


def _ready_context_from_fixture(monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    return build_market_futures_ohlcv_display_context()


def test_public_runtime_entrypoints_are_canonical() -> None:
    assert ENV_ENABLED == "PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED"
    assert ENV_BUNDLE_ROOT == "PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT"
    for fn in (
        enabled_explicitly_on,
        resolved_bundle_root_or_none,
        build_market_futures_ohlcv_display_context,
        resolve_futures_ohlcv_series_for_symbol,
    ):
        assert inspect.isfunction(fn)


def test_enabled_explicitly_on_fail_closed_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "0")
    assert enabled_explicitly_on() is False
    monkeypatch.setenv(ENV_ENABLED, "1")
    assert enabled_explicitly_on() is True


def test_resolved_bundle_root_or_none_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, "")
    assert resolved_bundle_root_or_none() is None
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(FIXTURE_ROOT))
    assert resolved_bundle_root_or_none() == FIXTURE_ROOT.resolve()


def test_display_context_disabled_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_market_futures_ohlcv_display_context()
    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is False
    assert ctx["display_status"] == "disabled"
    assert ctx["stale_reason"] == "source_disabled"
    assert ctx["series"] == {}
    assert ctx["non_authorizing"] is True


def test_display_context_unconfigured_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)
    ctx = build_market_futures_ohlcv_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "unconfigured"
    assert ctx["stale_reason"] == "bundle_root_unconfigured"
    assert ctx["series"] == {}


def test_display_context_builder_error_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    payload["readmodel_id"] = "wrong.v0"
    (tmp_path / "futures_ohlcv.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(tmp_path))
    ctx = build_market_futures_ohlcv_display_context()
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "builder_error"
    assert ctx["stale_reason"] == "bundle_build_failed"
    assert ctx["series"] == {}


def test_display_context_ready_from_canonical_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    readmodel = build_market_futures_ohlcv_readmodel(FIXTURE_ROOT)

    assert set(ctx.keys()) == _EXPECTED_DISPLAY_CONTEXT_KEYS
    assert ctx["gate_enabled"] is True
    assert ctx["display_status"] == "ready"
    assert ctx["readmodel_id"] == READMODEL_ID
    assert ctx["non_authorizing"] is True
    assert ctx["stale"] is False
    assert ctx["source"] == readmodel["source"]
    assert ctx["generated_at_iso"] == readmodel["generated_at_iso"]
    assert ctx["series"] == readmodel["series"]


def test_display_context_is_deterministic_for_identical_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _ready_context_from_fixture(monkeypatch)
    second = build_market_futures_ohlcv_display_context()
    assert first == second
    assert json.loads(json.dumps(first)) == first


def test_resolve_symbol_series_success_preserves_bar_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    fixture = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    fixture_bars = fixture["series"][CANONICAL_SYMBOL]["bars"]

    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=len(fixture_bars),
    )

    assert unavailable is False
    assert reason == ""
    assert [bar["ts"] for bar in bars] == [bar["ts"] for bar in fixture_bars]
    assert bars[0]["open"] == fixture_bars[0]["open"]
    assert bars[-1]["close"] == fixture_bars[-1]["close"]


def test_resolve_symbol_series_limit_returns_tail_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    fixture = json.loads((FIXTURE_ROOT / "futures_ohlcv.json").read_text(encoding="utf-8"))
    fixture_bars = fixture["series"][CANONICAL_SYMBOL]["bars"]
    limit = 3

    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=limit,
    )

    assert unavailable is False
    assert reason == ""
    assert len(bars) == limit
    assert [bar["ts"] for bar in bars] == [bar["ts"] for bar in fixture_bars[-limit:]]


def test_resolve_unknown_symbol_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol="UNKNOWNFUT",
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_symbol_missing"
    assert unavailable is True


def test_resolve_gate_disabled_fail_closed() -> None:
    ctx = {
        "gate_enabled": False,
        "display_status": "disabled",
        "series": {},
        "stale": True,
    }
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_unavailable"
    assert unavailable is True


def test_resolve_unconfigured_fail_closed() -> None:
    ctx = {
        "gate_enabled": True,
        "display_status": "unconfigured",
        "series": {},
        "stale": True,
    }
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_unconfigured"
    assert unavailable is True


def test_resolve_builder_error_fail_closed() -> None:
    ctx = {
        "gate_enabled": True,
        "display_status": "builder_error",
        "series": {},
        "stale": True,
    }
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_malformed"
    assert unavailable is True


def test_resolve_missing_series_map_fail_closed() -> None:
    ctx = {
        "gate_enabled": True,
        "display_status": "ready",
        "series": "not-a-dict",
        "stale": False,
    }
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_unavailable"
    assert unavailable is True


def test_resolve_empty_bars_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    ctx = deepcopy(ctx)
    ctx["series"][CANONICAL_SYMBOL]["bars"] = []
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_empty"
    assert unavailable is True


def test_resolve_malformed_bars_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    ctx = deepcopy(ctx)
    ctx["series"][CANONICAL_SYMBOL]["bars"] = "not-a-list"
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_empty"
    assert unavailable is True


def test_resolve_stale_context_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    ctx = deepcopy(ctx)
    ctx["stale"] = True
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_stale"
    assert unavailable is True


def test_resolve_timeframe_mismatch_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    bars, reason, unavailable = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe="4h",
        limit=10,
    )
    assert bars == []
    assert reason == "futures_ohlcv_timeframe_mismatch"
    assert unavailable is True


def test_resolve_does_not_mutate_input_context(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    before = deepcopy(ctx)
    resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=3,
    )
    assert ctx == before


def test_futures_only_non_bitcoin_symbols_in_ready_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    symbols = list(ctx["series"].keys())
    assert symbols
    for symbol in symbols:
        assert "/" not in symbol
        assert is_eligible_market_dashboard_instrument(symbol)
        upper = symbol.upper()
        for token in _BITCOIN_TOKENS:
            assert token not in upper


def test_display_context_non_authorizing_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    assert ctx["non_authorizing"] is True


def test_runtime_outputs_have_no_forbidden_execution_authority_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ready_context_from_fixture(monkeypatch)
    collected: set[str] = set()
    _collect_object_keys(ctx, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)

    bars, _, _ = resolve_futures_ohlcv_series_for_symbol(
        futures_ohlcv=ctx,
        symbol=CANONICAL_SYMBOL,
        timeframe=CANONICAL_TIMEFRAME,
        limit=2,
    )
    bar_keys: set[str] = set()
    _collect_object_keys(bars, bar_keys)
    assert bar_keys.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_runtime_module_source_has_no_network_or_exchange_tokens() -> None:
    source = (PROJECT_ROOT / "src" / "webui" / "market_futures_ohlcv_runtime_v0.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = ("ccxt", "kraken", "requests", "httpx", "aiohttp", "urllib")
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered
