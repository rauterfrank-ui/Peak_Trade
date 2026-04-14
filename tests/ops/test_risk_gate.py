from __future__ import annotations

from src.ops.gates.risk_gate import (
    RiskLimits,
    RiskContext,
    evaluate_risk,
    RiskDenyReason,
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
