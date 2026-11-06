"""Safety preflight: RiskGate, KillSwitch, Emergency — before network session."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from src.ops.gates.risk_gate import RiskContext, RiskLimits, evaluate_risk
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_EMERGENCY_COMMANDS,
    CANONICAL_POSITION_COUNT_LIMIT,
)
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.state import KillSwitchState


class ActualStartSafetyError(RuntimeError):
    """Fail-closed safety preflight violation."""


@dataclass(frozen=True)
class SafetyPreflightV1:
    risk_gate_allows: bool
    kill_switch_operational: bool
    emergency_control_operational: bool
    kill_switch_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_gate_allows": self.risk_gate_allows,
            "kill_switch_operational": self.kill_switch_operational,
            "emergency_control_operational": self.emergency_control_operational,
            "kill_switch_state": self.kill_switch_state,
        }


def evaluate_safety_preflight_v1(
    *,
    kill_switch: KillSwitch | None = None,
    force_killed: bool = False,
    max_position: float = float(CANONICAL_POSITION_COUNT_LIMIT),
    market_data_age_seconds: float = 1.0,
    current_position: float = 0.0,
    order_size: float = 1.0,
    order_notional_usd: float = 10.0,
    session_pnl_usd: float = 0.0,
    now_epoch: float | None = None,
) -> SafetyPreflightV1:
    if kill_switch is None:
        quiet = logging.getLogger("actual_start.kill_switch.fixture")
        quiet.disabled = True
        ks = KillSwitch({"recovery_cooldown_seconds": 1, "enabled": True}, logger=quiet)
    else:
        ks = kill_switch
    if force_killed and ks.state == KillSwitchState.ACTIVE:
        ks.trigger("ACTUAL_START_PREFLIGHT_KILL")
    blocked = bool(ks.check_and_block())
    operational = ks.enabled is True and not blocked
    emergency_ok = set(CANONICAL_EMERGENCY_COMMANDS).issuperset(
        {
            "BLOCK_NEW_ENTRY",
            "EXIT_ONLY",
            "REDUCE_ONLY",
            "CANCEL_ALL",
            "HALT_AFTER_CANCEL",
            "PERSISTENT_KILL",
        }
    )
    if not operational:
        raise ActualStartSafetyError("KILL_SWITCH_NOT_OPERATIONAL")
    if not emergency_ok:
        raise ActualStartSafetyError("EMERGENCY_CONTROL_NOT_OPERATIONAL")

    limits = RiskLimits(
        enabled=True,
        kill_switch=blocked,
        max_notional_usd=100.0,
        max_order_size=10.0,
        max_position=max_position,
        max_session_loss_usd=50.0,
        max_data_age_seconds=30,
    )
    ctx = RiskContext(
        now_epoch=float(now_epoch if now_epoch is not None else 1),
        market_data_age_seconds=float(market_data_age_seconds),
        session_pnl_usd=float(session_pnl_usd),
        current_position=float(current_position),
        order_size=float(order_size),
        order_notional_usd=float(order_notional_usd),
    )
    decision = evaluate_risk(limits, ctx)
    if not decision.allow:
        raise ActualStartSafetyError(f"RISK_GATE_BLOCKS:{decision.reason}")
    return SafetyPreflightV1(
        risk_gate_allows=True,
        kill_switch_operational=True,
        emergency_control_operational=True,
        kill_switch_state=ks.state.name,
    )


def evaluate_cycle_safety_v1(
    *,
    kill_switch: KillSwitch | None = None,
    force_killed: bool = False,
    market_data_age_seconds: float = 1.0,
    current_position: float = 0.0,
    order_size: float = 1.0,
    order_notional_usd: float = 10.0,
    session_pnl_usd: float = 0.0,
) -> SafetyPreflightV1:
    """Per-cycle risk / kill-switch / emergency re-evaluation before side effects."""
    return evaluate_safety_preflight_v1(
        kill_switch=kill_switch,
        force_killed=force_killed,
        market_data_age_seconds=market_data_age_seconds,
        current_position=current_position,
        order_size=order_size,
        order_notional_usd=order_notional_usd,
        session_pnl_usd=session_pnl_usd,
        now_epoch=time.time(),
    )
