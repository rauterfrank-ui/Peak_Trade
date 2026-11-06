"""Host binding: append-only telemetry session attached to the productive bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SINGLE_WRITER_IDENTITY,
    TELEMETRY_DECISION_AUTHORITY,
    TELEMETRY_FAILURE_CHANGES_DECISION,
    TELEMETRY_MUTATES_DECISION,
    TELEMETRY_MUTATES_RUNTIME_STATE,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.counters_v1 import (
    histogram_from_terminals_v1,
    increment_counters_for_cycle_v1,
    new_gate_counters_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.distance_v1 import (
    aggregate_distance_stats_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.funnel_v1 import (
    new_entry_funnel_v1,
    new_exit_funnel_v1,
    update_entry_funnel_v1,
    update_exit_funnel_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.models_v1 import (
    CycleTerminalRecordV1,
    ProductiveDecisionStageObservationV1,
    canonical_digest_v1,
)
from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.observer_v1 import (
    observe_productive_decision_cycle_v1,
)


@dataclass
class ActionabilityTelemetryBindingV1:
    """Non-authoritative append-only telemetry cursor (never mutates decisions)."""

    enabled: bool = True
    initialized: bool = False
    writer_identity: str = SINGLE_WRITER_IDENTITY
    schema_version: str = SCHEMA_VERSION
    producer_version: str = PRODUCER_VERSION
    owner: str = OWNER
    package_marker: str = PACKAGE_MARKER
    stage_events: list[dict[str, Any]] = field(default_factory=list)
    cycle_terminals: list[dict[str, Any]] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=new_gate_counters_v1)
    entry_funnel: dict[str, int] = field(default_factory=new_entry_funnel_v1)
    exit_funnel: dict[str, int] = field(default_factory=new_exit_funnel_v1)
    applied_event_digests: set[str] = field(default_factory=set)
    last_error: str | None = None
    telemetry_decision_authority: bool = TELEMETRY_DECISION_AUTHORITY
    telemetry_mutates_runtime_state: bool = TELEMETRY_MUTATES_RUNTIME_STATE
    telemetry_mutates_decision: bool = TELEMETRY_MUTATES_DECISION
    telemetry_failure_changes_decision: bool = TELEMETRY_FAILURE_CHANGES_DECISION

    def reset_ephemeral_v1(self) -> None:
        """Restart-safe: clear ephemeral counters/events without touching decision state."""
        self.stage_events.clear()
        self.cycle_terminals.clear()
        self.counters = new_gate_counters_v1()
        self.entry_funnel = new_entry_funnel_v1()
        self.exit_funnel = new_exit_funnel_v1()
        self.applied_event_digests.clear()
        self.last_error = None
        self.initialized = True


def ensure_actionability_telemetry_binding_v1(
    binding: ActionabilityTelemetryBindingV1,
) -> ActionabilityTelemetryBindingV1:
    if not binding.initialized:
        binding.initialized = True
        if not binding.counters:
            binding.counters = new_gate_counters_v1()
        if not binding.entry_funnel:
            binding.entry_funnel = new_entry_funnel_v1()
        if not binding.exit_funnel:
            binding.exit_funnel = new_exit_funnel_v1()
    return binding


def record_productive_cycle_telemetry_v1(
    binding: ActionabilityTelemetryBindingV1,
    *,
    repository_sha: str,
    config_digest: str,
    runtime_session_id: str,
    decision_cycle_id: str,
    instrument_id: str,
    market_event_time: float | None,
    observation_acceptance_result: Any,
    observation_cycle_kind: str,
    confirmation_binding: Any,
    features: Any,
    replay: Any,
    intended: Any,
    fill: Mapping[str, Any] | None,
    exit_signals: Mapping[str, Any] | None,
    has_open_position: bool,
    position_state: str,
    scope_state: str,
    safety_result: str,
    risk_sizing_result: str,
    decision_cfg: Any = None,
    fail_closed: bool = False,
) -> dict[str, Any]:
    """Observe + append. Never raises into the decision path when failure_changes=false."""
    ensure_actionability_telemetry_binding_v1(binding)
    if not binding.enabled:
        return {"ok": True, "skipped": True, "reason": "TELEMETRY_DISABLED"}
    try:
        stages, terminal = observe_productive_decision_cycle_v1(
            repository_sha=repository_sha,
            config_digest=config_digest,
            runtime_session_id=runtime_session_id,
            decision_cycle_id=decision_cycle_id,
            instrument_id=instrument_id,
            market_event_time=market_event_time,
            observation_acceptance_result=observation_acceptance_result,
            observation_cycle_kind=observation_cycle_kind,
            confirmation_binding=confirmation_binding,
            features=features,
            replay=replay,
            intended=intended,
            fill=fill,
            exit_signals=exit_signals,
            has_open_position=has_open_position,
            position_state=position_state,
            scope_state=scope_state,
            safety_result=safety_result,
            risk_sizing_result=risk_sizing_result,
            decision_cfg=decision_cfg,
            fail_closed=fail_closed,
        )
        if terminal.event_digest in binding.applied_event_digests:
            return {
                "ok": True,
                "duplicate_suppressed": True,
                "event_digest": terminal.event_digest,
            }
        for stage in stages:
            binding.stage_events.append(stage.to_dict())
        binding.cycle_terminals.append(terminal.to_dict())
        binding.applied_event_digests.add(terminal.event_digest)
        increment_counters_for_cycle_v1(
            binding.counters,
            stages=stages,
            terminal=terminal,
            observation_kind=observation_cycle_kind,
        )
        update_entry_funnel_v1(binding.entry_funnel, stages=stages, terminal=terminal)
        update_exit_funnel_v1(
            binding.exit_funnel,
            stages=stages,
            terminal=terminal,
            has_open_position=has_open_position,
        )
        binding.last_error = None
        return {
            "ok": True,
            "event_digest": terminal.event_digest,
            "terminal_outcome": terminal.terminal_outcome,
            "primary_reason": terminal.primary_reason,
            "stage_event_count": len(stages),
        }
    except Exception as exc:  # noqa: BLE001
        # TELEMETRY_FAILURE_CHANGES_DECISION=false
        binding.last_error = f"{type(exc).__name__}:{exc}"
        if TELEMETRY_FAILURE_CHANGES_DECISION:
            raise
        return {"ok": False, "error": binding.last_error, "decision_unchanged": True}


def telemetry_snapshot_v1(binding: ActionabilityTelemetryBindingV1) -> dict[str, Any]:
    hist = histogram_from_terminals_v1(
        [
            CycleTerminalRecordV1(
                schema_version=str(t.get("schema_version") or SCHEMA_VERSION),
                repository_sha=str(t.get("repository_sha") or ""),
                config_digest=str(t.get("config_digest") or ""),
                runtime_session_id=str(t.get("runtime_session_id") or ""),
                decision_cycle_id=str(t.get("decision_cycle_id") or ""),
                instrument_id=str(t.get("instrument_id") or ""),
                market_event_time=t.get("market_event_time"),
                terminal_outcome=str(t.get("terminal_outcome") or ""),
                primary_reason=t.get("primary_reason"),
                secondary_reasons=tuple(t.get("secondary_reasons") or ()),
            )
            for t in binding.cycle_terminals
        ]
    )
    distances = [dict(t.get("distance_to_actionability") or {}) for t in binding.cycle_terminals]
    return {
        "owner": binding.owner,
        "schema_version": binding.schema_version,
        "producer_version": binding.producer_version,
        "package_marker": binding.package_marker,
        "counters": dict(binding.counters),
        "entry_funnel": dict(binding.entry_funnel),
        "exit_funnel": dict(binding.exit_funnel),
        "histograms": hist,
        "distance_stats": aggregate_distance_stats_v1(distances),
        "stage_event_count": len(binding.stage_events),
        "cycle_terminal_count": len(binding.cycle_terminals),
        "applied_event_digest_count": len(binding.applied_event_digests),
        "last_error": binding.last_error,
        "snapshot_digest": canonical_digest_v1(
            {
                "counters": binding.counters,
                "entry_funnel": binding.entry_funnel,
                "exit_funnel": binding.exit_funnel,
                "terminals": binding.cycle_terminals,
            }
        ),
    }
