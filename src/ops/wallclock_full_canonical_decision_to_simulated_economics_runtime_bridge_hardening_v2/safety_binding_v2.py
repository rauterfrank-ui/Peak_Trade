"""Real safety evaluation binding for hardened bridge cycles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from trading.master_v2.double_play_entry_exit_policy_v0 import (
    PolicySignalV0,
    SafetyMode,
    TradingGate,
)


@dataclass(frozen=True)
class SafetyEvaluationV2:
    safety_mode: str
    trading_gate: str
    safety_exit_signal: dict[str, Any]
    hard_risk_reduction_signal: dict[str, Any]
    veto_reason: str
    safety_inputs: dict[str, Any]
    safety_result: str
    evaluation_bound: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def safety_mode_enum(self) -> SafetyMode:
        return SafetyMode(self.safety_mode)

    @property
    def trading_gate_enum(self) -> TradingGate:
        return TradingGate(self.trading_gate)

    @property
    def safety_exit_signal_obj(self) -> PolicySignalV0:
        return PolicySignalV0(
            triggered=bool(self.safety_exit_signal.get("triggered")),
            reason_code=str(self.safety_exit_signal.get("reason_code") or ""),
        )

    @property
    def hard_risk_signal_obj(self) -> PolicySignalV0:
        return PolicySignalV0(
            triggered=bool(self.hard_risk_reduction_signal.get("triggered")),
            reason_code=str(self.hard_risk_reduction_signal.get("reason_code") or ""),
        )


def evaluate_bridge_safety_v2(
    *,
    killstate_active: bool,
    killstate_trigger: str = "",
    warmup_complete: bool,
    regime_ok: bool,
    price_basis_ok: bool,
    max_drawdown: float = 0.0,
    drawdown_kill_threshold: float = 0.25,
    bridge_enabled: bool = True,
) -> SafetyEvaluationV2:
    """Canonical safety evaluation for the analytical wallclock bridge.

    Not a pauschal PolicySignalV0(triggered=False) stub: inputs are evaluated
    and mapped onto SafetyMode / TradingGate / PolicySignalV0.
    """
    inputs = {
        "killstate_active": killstate_active,
        "killstate_trigger": killstate_trigger,
        "warmup_complete": warmup_complete,
        "regime_ok": regime_ok,
        "price_basis_ok": price_basis_ok,
        "max_drawdown": max_drawdown,
        "drawdown_kill_threshold": drawdown_kill_threshold,
        "bridge_enabled": bridge_enabled,
        "evaluation_owner": (
            "ops.wallclock_full_canonical_decision_to_simulated_economics_"
            "runtime_bridge_hardening_v2.safety_binding_v2"
        ),
    }
    if not bridge_enabled:
        return SafetyEvaluationV2(
            safety_mode=SafetyMode.BLOCKED.value,
            trading_gate=TradingGate.BLOCKED.value,
            safety_exit_signal={"triggered": True, "reason_code": "BRIDGE_DISABLED"},
            hard_risk_reduction_signal={"triggered": False, "reason_code": ""},
            veto_reason="BRIDGE_DISABLED",
            safety_inputs=inputs,
            safety_result="BLOCKED",
            evaluation_bound=True,
        )
    if killstate_active:
        return SafetyEvaluationV2(
            safety_mode=SafetyMode.BLOCKED.value,
            trading_gate=TradingGate.BLOCKED.value,
            safety_exit_signal={
                "triggered": True,
                "reason_code": killstate_trigger or "KILLSTATE_ACTIVE",
            },
            hard_risk_reduction_signal={"triggered": True, "reason_code": "KILLSTATE"},
            veto_reason=killstate_trigger or "KILLSTATE_ACTIVE",
            safety_inputs=inputs,
            safety_result="BLOCKED",
            evaluation_bound=True,
        )
    if not price_basis_ok:
        return SafetyEvaluationV2(
            safety_mode=SafetyMode.BLOCKED.value,
            trading_gate=TradingGate.BLOCKED.value,
            safety_exit_signal={"triggered": True, "reason_code": "PRICE_BASIS_INVALID"},
            hard_risk_reduction_signal={"triggered": False, "reason_code": ""},
            veto_reason="PRICE_BASIS_INVALID",
            safety_inputs=inputs,
            safety_result="BLOCKED",
            evaluation_bound=True,
        )
    if not warmup_complete or not regime_ok:
        return SafetyEvaluationV2(
            safety_mode=SafetyMode.EXIT_ONLY.value,
            trading_gate=TradingGate.EXIT_ONLY.value,
            safety_exit_signal={"triggered": False, "reason_code": ""},
            hard_risk_reduction_signal={"triggered": False, "reason_code": ""},
            veto_reason="WARMUP_OR_REGIME_INCOMPLETE",
            safety_inputs=inputs,
            safety_result="EXIT_ONLY",
            evaluation_bound=True,
        )
    if max_drawdown >= drawdown_kill_threshold:
        return SafetyEvaluationV2(
            safety_mode=SafetyMode.BLOCKED.value,
            trading_gate=TradingGate.BLOCKED.value,
            safety_exit_signal={"triggered": True, "reason_code": "DRAWDOWN_KILL"},
            hard_risk_reduction_signal={"triggered": True, "reason_code": "DRAWDOWN_KILL"},
            veto_reason="DRAWDOWN_KILL",
            safety_inputs=inputs,
            safety_result="BLOCKED",
            evaluation_bound=True,
        )
    return SafetyEvaluationV2(
        safety_mode=SafetyMode.NORMAL.value,
        trading_gate=TradingGate.ENTRY_ALLOWED.value,
        safety_exit_signal={"triggered": False, "reason_code": ""},
        hard_risk_reduction_signal={"triggered": False, "reason_code": ""},
        veto_reason="",
        safety_inputs=inputs,
        safety_result="PASS",
        evaluation_bound=True,
    )
