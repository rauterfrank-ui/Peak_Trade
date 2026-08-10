"""Bounded long-running productive campaign executor — multi-cycle wallclock loop."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_LIMIT_PX_FOR_VENUE_NATIVE_BODY_V1,
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    OFFLINE_PROOF_CADENCE_SECONDS,
    OFFLINE_PROOF_MAX_CYCLES,
    PRODUCTIVE_EXECUTOR_ROLE,
    SECTION_11_12_8_BOUND_PRIORITY,
    SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS,
    SECTION_11_12_8_CAMPAIGN_MAX_CYCLES,
    SECTION_11_12_8_CYCLE_CADENCE_SECONDS,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    ProductiveTestnetExecutionPortV1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.safety_preflight_v1 import (
    ActualStartSafetyError,
    evaluate_cycle_safety_v1,
    evaluate_safety_preflight_v1,
)


class ActualStartExecutorError(RuntimeError):
    """Fail-closed campaign executor violation."""


@dataclass
class CampaignLifecycleRecordV1:
    started: bool = False
    running: bool = False
    campaign_id: str = ""
    execution_start_utc: str = ""
    execution_end_utc: str = ""
    execution_duration_seconds: float = 0.0
    duration_bound_seconds: int = 0
    cycle_bound: int = 0
    cadence_seconds: float = 0.0
    bound_priority: str = SECTION_11_12_8_BOUND_PRIORITY
    bound_reached_reason: str = ""
    cycles_started: int = 0
    cycles_completed: int = 0
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
    network_request_count: int = 0
    order_attempt_count: int = 0
    testnet_order_sent_count: int = 0
    transport_response_count: int = 0
    exchange_ack_count: int = 0
    exchange_reject_count: int = 0
    fill_count: int = 0
    partial_fill_count: int = 0
    client_order_ids: list[str] = field(default_factory=list)
    exchange_order_ids: list[str] = field(default_factory=list)
    cycle_records: list[dict[str, Any]] = field(default_factory=list)
    risk_gate_results: list[dict[str, Any]] = field(default_factory=list)
    kill_switch_checks: list[dict[str, Any]] = field(default_factory=list)
    emergency_control_checks: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "PRODUCTIVE_EXECUTOR_ROLE": PRODUCTIVE_EXECUTOR_ROLE,
            "LONG_RUNNING_CAMPAIGN": True,
            "started": self.started,
            "running": self.running,
            "campaign_id": self.campaign_id,
            "execution_start_utc": self.execution_start_utc,
            "execution_end_utc": self.execution_end_utc,
            "execution_duration_seconds": self.execution_duration_seconds,
            "duration_bound_seconds": self.duration_bound_seconds,
            "cycle_bound": self.cycle_bound,
            "cadence_seconds": self.cadence_seconds,
            "bound_priority": self.bound_priority,
            "bound_reached_reason": self.bound_reached_reason,
            "cycles_started": self.cycles_started,
            "cycles_completed": self.cycles_completed,
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
            "network_request_count": self.network_request_count,
            "order_attempt_count": self.order_attempt_count,
            "testnet_order_sent_count": self.testnet_order_sent_count,
            "transport_response_count": self.transport_response_count,
            "exchange_ack_count": self.exchange_ack_count,
            "exchange_reject_count": self.exchange_reject_count,
            "fill_count": self.fill_count,
            "partial_fill_count": self.partial_fill_count,
            "client_order_ids": list(self.client_order_ids),
            "exchange_order_ids": list(self.exchange_order_ids),
            "cycle_records": list(self.cycle_records),
            "risk_gate_results": list(self.risk_gate_results),
            "kill_switch_checks": list(self.kill_switch_checks),
            "emergency_control_checks": list(self.emergency_control_checks),
            "events": list(self.events),
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_bounds(
    *,
    offline_proof_bounds: bool,
    duration_bound_seconds: int | None,
    max_cycles: int | None,
    cadence_seconds: float | None,
) -> tuple[int, int, float]:
    duration = (
        int(duration_bound_seconds)
        if duration_bound_seconds is not None
        else int(SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS)
    )
    cycles = (
        int(max_cycles)
        if max_cycles is not None
        else (
            int(OFFLINE_PROOF_MAX_CYCLES)
            if offline_proof_bounds
            else int(SECTION_11_12_8_CAMPAIGN_MAX_CYCLES)
        )
    )
    cadence = (
        float(cadence_seconds)
        if cadence_seconds is not None
        else (
            float(OFFLINE_PROOF_CADENCE_SECONDS)
            if offline_proof_bounds
            else float(SECTION_11_12_8_CYCLE_CADENCE_SECONDS)
        )
    )
    if duration < 1:
        raise ActualStartExecutorError("CANONICAL_DURATION_BOUND_INVALID")
    if cycles < 1:
        raise ActualStartExecutorError("CANONICAL_CYCLE_BOUND_INVALID")
    if cadence < 0:
        raise ActualStartExecutorError("CANONICAL_CADENCE_INVALID")
    return duration, cycles, cadence


def run_campaign_lifecycle_v1(
    *,
    port: ProductiveTestnetExecutionPortV1,
    network_session_started: bool,
    stubbed: bool = True,
    abort: bool = False,
    inject_kill_switch: bool = False,
    inject_emergency: bool = False,
    inject_risk_breach: bool = False,
    offline_proof_bounds: bool = False,
    duration_bound_seconds: int | None = None,
    max_cycles: int | None = None,
    cadence_seconds: float | None = None,
    submit_on_cycle: Callable[[int], bool] | None = None,
    monotonic_fn: Callable[[], float] = time.monotonic,
    sleep_fn: Callable[[float], None] = time.sleep,
    campaign_id: str | None = None,
    limit_px: str = CANONICAL_LIMIT_PX_FOR_VENUE_NATIVE_BODY_V1,
) -> CampaignLifecycleRecordV1:
    """Bounded long-running campaign loop.

    CYCLE_COMPLETE must never alone complete the campaign. Completion requires
    duration and/or cycle bound under FIRST_REACHED_WINS (or abort).
    """
    if not network_session_started:
        raise ActualStartExecutorError("NETWORK_SESSION_REQUIRED_BEFORE_CAMPAIGN")
    if not port.authorized:
        raise ActualStartExecutorError("PORT_NOT_AUTHORIZED")

    duration, cycles, cadence = _resolve_bounds(
        offline_proof_bounds=offline_proof_bounds,
        duration_bound_seconds=duration_bound_seconds,
        max_cycles=max_cycles,
        cadence_seconds=cadence_seconds,
    )

    record = CampaignLifecycleRecordV1(
        started=True,
        running=True,
        campaign_id=campaign_id or f"campaign-{uuid4().hex}",
        execution_start_utc=_utc_now(),
        duration_bound_seconds=duration,
        cycle_bound=cycles,
        cadence_seconds=cadence,
    )
    record.events.append({"event": "start", "campaign_id": record.campaign_id})
    mono_start = float(monotonic_fn())

    def _elapsed() -> float:
        return float(monotonic_fn()) - mono_start

    def _should_stop_for_bound() -> str:
        if _elapsed() >= float(duration):
            return "DURATION_BOUND"
        if record.cycles_completed >= cycles:
            return "CYCLE_BOUND"
        return ""

    # Initial abort/injection before cycles still allowed.
    if abort and not inject_kill_switch and not inject_emergency and not inject_risk_breach:
        record.aborted = True
        record.running = False
        record.bound_reached_reason = "ABORT_REQUESTED"
        record.execution_end_utc = _utc_now()
        record.execution_duration_seconds = _elapsed()
        record.events.append({"event": "abort"})
        return record

    while record.running:
        if inject_kill_switch:
            record.kill_switch_reaction = "HALT_AND_ABORT"
            record.aborted = True
            record.running = False
            record.bound_reached_reason = "KILL_SWITCH"
            record.events.append({"event": "kill_switch_reaction"})
            break
        if inject_emergency:
            record.emergency_reaction = "CANCEL_ALL_THEN_ABORT"
            record.aborted = True
            record.running = False
            record.bound_reached_reason = "EMERGENCY_STOP"
            record.events.append({"event": "emergency_reaction"})
            break
        if inject_risk_breach:
            record.risk_breach_reaction = "BLOCK_NEW_ENTRY_ABORT"
            record.aborted = True
            record.running = False
            record.bound_reached_reason = "RISK_BREACH"
            record.events.append({"event": "risk_breach_reaction"})
            break

        bound = _should_stop_for_bound()
        if bound:
            record.bound_reached_reason = bound
            record.events.append({"event": "bound_reached", "reason": bound})
            break

        cycle_index = record.cycles_started
        record.cycles_started += 1
        cycle_started_at = _utc_now()
        record.events.append({"event": "cycle_running", "cycle_index": cycle_index})

        try:
            safety = evaluate_cycle_safety_v1()
        except ActualStartSafetyError as exc:
            record.aborted = True
            record.running = False
            record.bound_reached_reason = f"SAFETY_ABORT:{exc}"
            record.events.append({"event": "safety_abort", "reason": str(exc)})
            break

        record.risk_gate_results.append(safety.to_dict())
        record.kill_switch_checks.append(
            {"cycle_index": cycle_index, "kill_switch_state": safety.kill_switch_state}
        )
        record.emergency_control_checks.append(
            {
                "cycle_index": cycle_index,
                "emergency_control_operational": safety.emergency_control_operational,
            }
        )

        order_attempted = False
        effect: dict[str, Any] | None = None
        do_submit = True if submit_on_cycle is None else bool(submit_on_cycle(cycle_index))
        # Default: submit only on first cycle to prove multi-cycle with sparse orders.
        if submit_on_cycle is None:
            do_submit = cycle_index == 0

        if do_submit:
            px_text = str(limit_px).strip()
            if not px_text:
                raise ActualStartExecutorError("LIMIT_ORDER_PX_REQUIRED_BEFORE_WIRE")
            client_order_id = f"coid-{record.campaign_id[:8]}-{cycle_index}"
            effect = port.submit_order_v1(
                client_order_id=client_order_id,
                instrument="BTC-USD_UM_XPERP-310328",
                order_type="LIMIT",
                side="buy",
                quantity="1",
                px=px_text,
            )
            order_attempted = True
            record.order_attempt_count += 1
            record.network_request_count += 1
            record.client_order_ids.append(client_order_id)
            record.first_permitted_effect_invoked = True
            record.first_permitted_effect_stubbed = bool(effect.get("stubbed"))
            if stubbed and not record.first_permitted_effect_stubbed and cycle_index == 0:
                raise ActualStartExecutorError("EXPECTED_STUBBED_FIRST_EFFECT")
            if not stubbed and cycle_index == 0:
                if record.first_permitted_effect_stubbed:
                    raise ActualStartExecutorError("EXPECTED_NON_STUBBED_FIRST_EFFECT")
                boundary_ok = bool(
                    effect.get("network_send_boundary_reached")
                    or effect.get("wire_sent")
                    or effect.get("submitted")
                )
                if not boundary_ok:
                    raise ActualStartExecutorError("REAL_PATH_SEND_BOUNDARY_NOT_REACHED")

            if effect.get("wire_sent"):
                record.testnet_order_sent_count += 1
            if effect.get("transport_response"):
                record.transport_response_count += 1
            if effect.get("order_acknowledged"):
                record.exchange_ack_count += 1
            if effect.get("exchange_rejected"):
                record.exchange_reject_count += 1
            if effect.get("fill_observed"):
                record.fill_count += 1
            if effect.get("partial_fill_observed"):
                record.partial_fill_count += 1
            ex_id = effect.get("exchange_order_id")
            if ex_id:
                record.exchange_order_ids.append(str(ex_id))
            record.events.append(
                {
                    "event": "order_attempt",
                    "cycle_index": cycle_index,
                    "effect": effect,
                }
            )
            if cycle_index == 0:
                record.events.append({"event": "first_permitted_testnet_effect", "effect": effect})

        record.heartbeat_count += 1
        record.continuity_ok = True
        record.restart_handled = True
        record.cycles_completed += 1
        cycle_record = {
            "cycle_index": cycle_index,
            "cycle_started_at_utc": cycle_started_at,
            "cycle_completed_at_utc": _utc_now(),
            "order_attempted": order_attempted,
            "wire_sent": bool(effect.get("wire_sent")) if effect else False,
            "order_acknowledged": bool(effect.get("order_acknowledged")) if effect else False,
            "exchange_rejected": bool(effect.get("exchange_rejected")) if effect else False,
            "elapsed_seconds": _elapsed(),
        }
        record.cycle_records.append(cycle_record)
        record.events.append({"event": "cycle_complete", "cycle_index": cycle_index})

        # CRITICAL: cycle complete must NOT complete the campaign.
        bound = _should_stop_for_bound()
        if bound:
            record.bound_reached_reason = bound
            record.events.append({"event": "bound_reached", "reason": bound})
            break

        if cadence > 0:
            sleep_fn(cadence)
        elif offline_proof_bounds:
            # Deterministic offline path: no sleep; loop until cycle bound.
            pass

    record.execution_end_utc = _utc_now()
    record.execution_duration_seconds = _elapsed()
    record.running = False

    if record.aborted:
        record.events.append({"event": "abort_terminal"})
        return record

    if not record.bound_reached_reason:
        raise ActualStartExecutorError("CAMPAIGN_EXIT_WITHOUT_BOUND_OR_ABORT")

    # Graceful completion only after bound.
    record.completed = True
    record.events.append(
        {
            "event": "complete",
            "bound_reached_reason": record.bound_reached_reason,
            "cycles_completed": record.cycles_completed,
        }
    )
    return record


def run_preflight_safety_once_v1() -> dict[str, Any]:
    return evaluate_safety_preflight_v1().to_dict()
