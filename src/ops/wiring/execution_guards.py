from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.ops.gates.armed_gate import ArmedGate, ArmedState
from src.ops.gates.risk_gate import RiskLimits, RiskContext, RiskDecision, evaluate_risk


@dataclass(frozen=True)
class GuardConfig:
    enabled: bool = False  # global toggle: default OFF
    armed_required: bool = True  # if enabled, require armed
    risk_enabled: bool = True  # if enabled, evaluate_risk
    token_ttl_seconds: int = 120


@dataclass(frozen=True)
class GuardInputs:
    armed_state: ArmedState
    armed_token: Optional[str]
    limits: RiskLimits
    ctx: RiskContext


@dataclass(frozen=True)
class GuardResult:
    allow: bool
    risk: Optional[RiskDecision]


def apply_execution_guards(
    cfg: GuardConfig,
    *,
    gate: ArmedGate,
    inputs: GuardInputs,
) -> GuardResult:
    # Default: no-op, allow
    if not cfg.enabled:
        return GuardResult(allow=True, risk=None)

    if cfg.armed_required:
        if inputs.armed_token is not None:
            s = gate.arm(
                inputs.armed_state,
                inputs.armed_token,
                inputs.ctx.now_epoch,
            )
        else:
            s = inputs.armed_state
        ArmedGate.require_armed(s)

    risk_dec = None
    if cfg.risk_enabled:
        risk_dec = evaluate_risk(inputs.limits, inputs.ctx)
        if not risk_dec.allow:
            raise RuntimeError(
                f"Execution blocked: risk_gate deny reason={risk_dec.reason} "
                f"details={risk_dec.details}"
            )

    return GuardResult(allow=True, risk=risk_dec)
