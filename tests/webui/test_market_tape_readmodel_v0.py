from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.webui.market_tape_readmodel_v0 import (
    AUTHORITY_BOUNDARY,
    MarketTapeReadmodelError,
    build_market_tape_readmodel_v0,
    enabled_explicitly_on,
    resolve_market_tape_readmodel_payload_v0,
    to_json_dict,
)
from src.webui.market_tape_readmodel_v0.gate import ENV_BUNDLE_ROOT, ENV_ENABLED

FIXTURE_ROOT = Path("tests/fixtures/market_tape_readmodel_v0")


def test_market_tape_readmodel_builds_json_native_offline_bundle() -> None:
    readmodel = build_market_tape_readmodel_v0(
        bundle_root=FIXTURE_ROOT / "complete_minimal",
        generated_at_iso="2026-05-02T16:00:00Z",
    )

    payload = to_json_dict(readmodel)

    assert payload["readmodel_id"] == "market_tape_readmodel.v0"
    assert payload["symbol"] == "BTC/EUR"
    assert payload["source"] == "fixture:complete_minimal"
    assert payload["limit"] == 3
    assert payload["generated_at_iso"] == "2026-05-02T16:00:00Z"
    assert payload["runtime_source_status"] == "offline_bundle"
    assert payload["stale"] is True
    assert payload["stale_reason"] == "offline_bundle_scan"
    assert payload["non_authorizing"] is True
    assert payload["provider_truth_blocked"] is True
    assert payload["order_fill_position_truth_blocked"] is True
    assert payload["slippage_liquidity_depth_truth_blocked"] is True

    assert payload["tape"]["trade_limit"] == 3
    assert payload["tape"]["trades_returned"] == 3
    assert [trade["sequence"] for trade in payload["tape"]["trades"]] == [101, 100, 99]
    assert payload["tape"]["trades"][0]["price"] == "63020"
    assert json.loads(json.dumps(payload)) == payload


def test_market_tape_readmodel_explicit_limit_truncates_sorted_trades() -> None:
    payload = to_json_dict(
        build_market_tape_readmodel_v0(
            bundle_root=FIXTURE_ROOT / "complete_minimal",
            limit=1,
            generated_at_iso="2026-05-02T16:00:00Z",
        )
    )

    assert payload["limit"] == 1
    assert payload["tape"]["trades_returned"] == 1
    assert payload["tape"]["trades"][0]["sequence"] == 101


def test_market_tape_readmodel_rejects_missing_bundle_root() -> None:
    with pytest.raises(MarketTapeReadmodelError, match="bundle_root does not exist"):
        build_market_tape_readmodel_v0(bundle_root=FIXTURE_ROOT / "does_not_exist")


def test_market_tape_readmodel_rejects_malformed_trades() -> None:
    with pytest.raises(MarketTapeReadmodelError, match=r"trades\[0\]\.price must be positive"):
        build_market_tape_readmodel_v0(bundle_root=FIXTURE_ROOT / "malformed_trades")


def test_market_tape_readmodel_module_has_no_runtime_provider_imports() -> None:
    builder_source = Path("src/webui/market_tape_readmodel_v0/builder.py").read_text(
        encoding="utf-8"
    )

    forbidden_tokens = [
        "ccxt",
        "kraken",
        "requests",
        "httpx",
        "aiohttp",
        "subprocess",
        "os.environ",
    ]

    for token in forbidden_tokens:
        assert token not in builder_source


_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "readmodel_id",
        "symbol",
        "source",
        "limit",
        "generated_at_iso",
        "runtime_source_status",
        "stale",
        "stale_reason",
        "non_authorizing",
        "provider_truth_blocked",
        "dashboard_truth_blocked",
        "trading_readiness_blocked",
        "selected_future_truth_blocked",
        "order_fill_position_truth_blocked",
        "slippage_liquidity_depth_truth_blocked",
        "signal_strategy_readiness_blocked",
        "tape",
    }
)

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "live_authorization",
        "live_ready",
        "testnet_ready",
        "trading_ready",
        "execute",
        "execution",
        "order",
        "orders",
        "approve",
        "approved",
        "promote",
        "sign_off",
        "enable_live",
        "confirm_token",
        "fills",
        "fills_count",
        "position",
        "pnl",
        "slippage",
        "liquidity",
        "depth",
    }
)


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                out.add(key)
            _collect_object_keys(value, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


def test_market_tape_readmodel_rejects_missing_tape_json(tmp_path: Path) -> None:
    empty_root = tmp_path / "bundle"
    empty_root.mkdir()
    with pytest.raises(MarketTapeReadmodelError, match="missing tape fixture"):
        build_market_tape_readmodel_v0(bundle_root=empty_root)


def test_market_tape_readmodel_rejects_invalid_tape_json(tmp_path: Path) -> None:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "tape.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(MarketTapeReadmodelError, match="malformed tape fixture JSON"):
        build_market_tape_readmodel_v0(bundle_root=root)


def test_market_tape_readmodel_stable_top_level_keys_and_no_authority_keys() -> None:
    payload = to_json_dict(
        build_market_tape_readmodel_v0(
            bundle_root=FIXTURE_ROOT / "complete_minimal",
            generated_at_iso="2026-05-02T16:00:00Z",
        )
    )
    assert set(payload.keys()) == _EXPECTED_TOP_LEVEL_KEYS
    tape_keys = set(payload["tape"].keys())
    assert tape_keys == frozenset({"trades", "trades_returned", "trade_limit"})
    collected: set[str] = set()
    _collect_object_keys(payload, collected)
    assert collected.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_market_tape_readmodel_authority_boundary_matches_module_constant() -> None:
    payload = to_json_dict(
        build_market_tape_readmodel_v0(
            bundle_root=FIXTURE_ROOT / "complete_minimal",
            generated_at_iso="2026-05-02T16:00:00Z",
        )
    )
    for key, expected in AUTHORITY_BOUNDARY.items():
        assert payload[key] is expected


@pytest.mark.parametrize(
    "field",
    [
        "order_id",
        "client_order_id",
        "fill_id",
        "fills",
        "fills_count",
        "position",
        "pnl",
        "slippage",
        "liquidity",
        "depth",
    ],
)
def test_market_tape_readmodel_rejects_forbidden_trade_fields_v0(
    tmp_path: Path,
    field: str,
) -> None:
    fixture = {
        "symbol": "BTC/EUR",
        "source": "fixture:forbidden",
        "limit": 5,
        "trades": [
            {
                "sequence": 1,
                "price": "63000",
                "size": "0.1",
                "side": "buy",
                "timestamp_iso": "2026-05-02T15:59:58Z",
                field: "forbidden",
            }
        ],
    }
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "tape.json").write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(MarketTapeReadmodelError, match="forbidden fields"):
        build_market_tape_readmodel_v0(bundle_root=root)


def test_market_tape_gate_defaults_disabled_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)

    assert enabled_explicitly_on() is False
    status_code, payload = resolve_market_tape_readmodel_payload_v0()
    assert status_code == 503
    assert payload["runtime_source_status"] == "disabled"
    assert payload["stale_reason"] == "source_disabled"
    assert payload["non_authorizing"] is True
    assert "tape" not in payload


def test_market_tape_gate_unconfigured_when_enabled_without_bundle_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_BUNDLE_ROOT, raising=False)

    status_code, payload = resolve_market_tape_readmodel_payload_v0()
    assert status_code == 503
    assert payload["runtime_source_status"] == "unconfigured"
    assert payload["stale_reason"] == "bundle_root_unconfigured"
    assert "tape" not in payload


def test_market_tape_gate_builds_when_enabled_with_bundle_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = FIXTURE_ROOT / "complete_minimal"
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_BUNDLE_ROOT, str(bundle.resolve()))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-05-02T16:00:00Z")

    status_code, payload = resolve_market_tape_readmodel_payload_v0()
    assert status_code == 200
    assert payload["readmodel_id"] == "market_tape_readmodel.v0"
    assert payload["tape"]["trades_returned"] == 3
