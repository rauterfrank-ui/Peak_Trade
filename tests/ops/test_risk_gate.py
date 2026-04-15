from __future__ import annotations

import json

import pytest

from src.ops.gates.risk_gate import (
    RiskLimits,
    RiskContext,
    evaluate_risk,
    RiskDenyReason,
    kill_switch_should_block_trading,
    kill_switch_state_path_from_env,
    resolve_kill_switch_limit_from_state_file,
)


def base_ctx(**kw):
    d = dict(
        now_epoch=1_700_000_000,
        market_data_age_seconds=1,
        session_pnl_usd=0.0,
        current_position=0.0,
        order_size=1.0,
        order_notional_usd=100.0,
    )
    d.update(kw)
    return RiskContext(**d)


def test_disabled_denies():
    dec = evaluate_risk(RiskLimits(enabled=False), base_ctx())
    assert dec.allow is False
    assert dec.reason == RiskDenyReason.DISABLED


def test_kill_switch_denies():
    dec = evaluate_risk(RiskLimits(kill_switch=True), base_ctx())
    assert dec.allow is False
    assert dec.reason == RiskDenyReason.KILL_SWITCH


def test_stale_data_denies():
    lim = RiskLimits(max_data_age_seconds=10)
    dec = evaluate_risk(lim, base_ctx(market_data_age_seconds=11))
    assert dec.allow is False
    assert dec.reason == RiskDenyReason.STALE_DATA


def test_notional_denies():
    lim = RiskLimits(max_notional_usd=50)
    dec = evaluate_risk(lim, base_ctx(order_notional_usd=51))
    assert dec.allow is False
    assert dec.reason == RiskDenyReason.MAX_NOTIONAL


def test_allow_happy_path():
    lim = RiskLimits(
        max_notional_usd=1000,
        max_order_size=10,
        max_position=10,
        max_data_age_seconds=60,
    )
    dec = evaluate_risk(lim, base_ctx())
    assert dec.allow is True
    assert dec.reason is None


def test_resolve_kill_switch_missing_file(tmp_path):
    p = tmp_path / "missing.json"
    assert resolve_kill_switch_limit_from_state_file(str(p)) is None


@pytest.mark.parametrize(
    "state, expected",
    [
        ("KILLED", True),
        ("RECOVERING", True),
        ("ACTIVE", False),
        ("DISABLED", False),
    ],
)
def test_resolve_kill_switch_from_file(tmp_path, state, expected):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"state": state}), encoding="utf-8")
    assert resolve_kill_switch_limit_from_state_file(str(path)) is expected


def test_resolve_kill_switch_invalid_json(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json", encoding="utf-8")
    assert resolve_kill_switch_limit_from_state_file(str(path)) is None


def test_kill_switch_state_path_from_env_prefers_canonical(monkeypatch):
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", "/a/state.json")
    monkeypatch.setenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", "/b/state.json")
    assert kill_switch_state_path_from_env() == "/a/state.json"


def test_kill_switch_state_path_from_env_legacy_when_canonical_unset(monkeypatch):
    monkeypatch.delenv("PEAK_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.setenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", "/legacy/state.json")
    assert kill_switch_state_path_from_env() == "/legacy/state.json"


def test_kill_switch_should_block_trading_explicit():
    assert kill_switch_should_block_trading(explicit_active=True) is True


def test_kill_switch_should_block_trading_file_killed(tmp_path, monkeypatch):
    path = tmp_path / "ks.json"
    path.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    assert kill_switch_should_block_trading(explicit_active=False) is True


def test_kill_switch_should_block_trading_file_active_no_block(tmp_path, monkeypatch):
    path = tmp_path / "ks.json"
    path.write_text(json.dumps({"state": "ACTIVE"}), encoding="utf-8")
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    assert kill_switch_should_block_trading(explicit_active=False) is False


@pytest.mark.parametrize(
    ("peak_kill_switch", "expect_block"),
    [
        (None, False),
        ("0", False),
        ("1", True),
        ("true", False),
        ("01", False),
        ("1 ", False),
    ],
)
def test_kill_switch_should_block_trading_env_fallback_strict_literal_one(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    peak_kill_switch: str | None,
    expect_block: bool,
) -> None:
    """When state file is missing, only PEAK_KILL_SWITCH exactly ``1`` blocks (current contract)."""
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(tmp_path / "nope.json"))
    if peak_kill_switch is None:
        monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    else:
        monkeypatch.setenv("PEAK_KILL_SWITCH", peak_kill_switch)
    assert kill_switch_should_block_trading(explicit_active=False) is expect_block
