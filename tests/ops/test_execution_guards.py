from __future__ import annotations

import pytest
from src.ops.wiring.execution_guards import (
    GuardConfig,
    GuardInputs,
    apply_execution_guards,
)
from src.ops.gates.armed_gate import ArmedGate, ArmedState
from src.ops.gates.risk_gate import RiskLimits, RiskContext


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


def test_noop_when_disabled():
    gate = ArmedGate(secret=b"s", token_ttl_seconds=10)
    cfg = GuardConfig(enabled=False)
    inputs = GuardInputs(
        armed_state=ArmedState(
            enabled=False, armed=False, armed_since_epoch=None, token_issued_epoch=None
        ),
        armed_token=None,
        limits=RiskLimits(),
        ctx=base_ctx(),
    )
    r = apply_execution_guards(cfg, gate=gate, inputs=inputs)
    assert r.allow is True
    assert r.risk is None


def test_enabled_requires_armed():
    gate = ArmedGate(secret=b"s", token_ttl_seconds=10)
    cfg = GuardConfig(enabled=True, armed_required=True, risk_enabled=False)
    inputs = GuardInputs(
        armed_state=ArmedState(
            enabled=True, armed=False, armed_since_epoch=None, token_issued_epoch=None
        ),
        armed_token=None,
        limits=RiskLimits(),
        ctx=base_ctx(),
    )
    with pytest.raises(RuntimeError):
        apply_execution_guards(cfg, gate=gate, inputs=inputs)


def test_enabled_can_arm_with_valid_token():
    gate = ArmedGate(secret=b"s", token_ttl_seconds=10)
    cfg = GuardConfig(enabled=True, armed_required=True, risk_enabled=False)
    now = 1_700_000_000
    tok = gate.issue_token(now)
    inputs = GuardInputs(
        armed_state=ArmedState(
            enabled=True, armed=False, armed_since_epoch=None, token_issued_epoch=None
        ),
        armed_token=tok,
        limits=RiskLimits(),
        ctx=base_ctx(now_epoch=now),
    )
    r = apply_execution_guards(cfg, gate=gate, inputs=inputs)
    assert r.allow is True


def test_risk_gate_denies_when_enabled():
    gate = ArmedGate(secret=b"s", token_ttl_seconds=10)
    cfg = GuardConfig(enabled=True, armed_required=False, risk_enabled=True)
    limits = RiskLimits(max_notional_usd=50, enabled=True)
    inputs = GuardInputs(
        armed_state=ArmedState(
            enabled=False, armed=False, armed_since_epoch=None, token_issued_epoch=None
        ),
        armed_token=None,
        limits=limits,
        ctx=base_ctx(order_notional_usd=60),
    )
    with pytest.raises(RuntimeError):
        apply_execution_guards(cfg, gate=gate, inputs=inputs)
