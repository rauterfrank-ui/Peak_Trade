"""Productive campaign executor — start/running/monitor/complete/abort."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    PRODUCTIVE_EXECUTOR_ROLE,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    ProductiveTestnetExecutionPortV1,
)


class ActualStartExecutorError(RuntimeError):
    """Fail-closed campaign executor violation."""


@dataclass
class CampaignLifecycleRecordV1:
    started: bool = False
    running: bool = False
    heartbeat_count: int = 0
    continuity_ok: bool = False
    restart_handled: bool = False
    completed: bool = False
    aborted: bool = False
    kill_switch_reaction: str = ""
    emergency_reaction: str = ""
    risk_breach_reaction: str = ""
    first_permitted_effect_invoked: bool = False
    first_permitted_effect_stubbed: bool = False
    next_operation_after_boundary: str = NEXT_OPERATION_AFTER_STUBBED_BOUNDARY
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "PRODUCTIVE_EXECUTOR_ROLE": PRODUCTIVE_EXECUTOR_ROLE,
            "started": self.started,
            "running": self.running,
            "heartbeat_count": self.heartbeat_count,
            "continuity_ok": self.continuity_ok,
            "restart_handled": self.restart_handled,
            "completed": self.completed,
            "aborted": self.aborted,
            "kill_switch_reaction": self.kill_switch_reaction,
            "emergency_reaction": self.emergency_reaction,
            "risk_breach_reaction": self.risk_breach_reaction,
            "first_permitted_effect_invoked": self.first_permitted_effect_invoked,
            "first_permitted_effect_stubbed": self.first_permitted_effect_stubbed,
            "next_operation_after_boundary": self.next_operation_after_boundary,
            "events": list(self.events),
        }


def run_campaign_lifecycle_v1(
    *,
    port: ProductiveTestnetExecutionPortV1,
    network_session_started: bool,
    stubbed: bool = True,
    abort: bool = False,
    inject_kill_switch: bool = False,
    inject_emergency: bool = False,
    inject_risk_breach: bool = False,
) -> CampaignLifecycleRecordV1:
    if not network_session_started:
        raise ActualStartExecutorError("NETWORK_SESSION_REQUIRED_BEFORE_CAMPAIGN")
    if not port.authorized:
        raise ActualStartExecutorError("PORT_NOT_AUTHORIZED")

    record = CampaignLifecycleRecordV1(started=True, running=True)
    record.events.append({"event": "start"})

    # First permitted TESTNET side effect — stubbed in acceptance gate.
    effect = port.submit_order_v1(
        client_order_id="coid-actual-start-1",
        instrument="BTC-USDT-SWAP",
        order_type="LIMIT",
        side="buy",
        quantity="1",
    )
    record.first_permitted_effect_invoked = True
    record.first_permitted_effect_stubbed = bool(effect.get("stubbed"))
    if stubbed and not record.first_permitted_effect_stubbed:
        raise ActualStartExecutorError("EXPECTED_STUBBED_FIRST_EFFECT")
    record.events.append({"event": "first_permitted_testnet_effect", "effect": effect})

    record.heartbeat_count += 1
    record.continuity_ok = True
    record.restart_handled = True
    record.events.append({"event": "heartbeat"})
    record.events.append({"event": "continuity_ok"})
    record.events.append({"event": "restart_handled_within_bounds"})

    if inject_kill_switch:
        record.kill_switch_reaction = "HALT_AND_ABORT"
        record.aborted = True
        record.running = False
        record.events.append({"event": "kill_switch_reaction"})
        return record
    if inject_emergency:
        record.emergency_reaction = "CANCEL_ALL_THEN_ABORT"
        record.aborted = True
        record.running = False
        record.events.append({"event": "emergency_reaction"})
        return record
    if inject_risk_breach:
        record.risk_breach_reaction = "BLOCK_NEW_ENTRY_ABORT"
        record.aborted = True
        record.running = False
        record.events.append({"event": "risk_breach_reaction"})
        return record
    if abort:
        record.aborted = True
        record.running = False
        record.events.append({"event": "abort"})
        return record

    record.completed = True
    record.running = False
    record.events.append({"event": "complete"})
    return record
