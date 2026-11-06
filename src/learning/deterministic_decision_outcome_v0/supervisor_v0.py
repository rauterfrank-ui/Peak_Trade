"""Deterministic autonomy supervisor offline state machine v0.

TRANSITION(current_state, event, health_snapshot, authority_snapshot,
persisted_cycle_state) -> (actions, next_state, reason_codes, evidence_refs).

No LLM. No hidden mutable authority. No runtime reachability. SUBMITTING is
unreachable as a new action. Crash into SUBMITTING reconciles without resend.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY,
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    SUPERVISOR_EVENT_V0,
    SUPERVISOR_STATE_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.supervisor_records_v0 import (
    build_autonomy_cycle_record_v0,
    validate_health_snapshot_v0,
)

SUPERVISOR_HIDDEN_MUTABLE_STATE_ALLOWED: Final[bool] = False
SINGLE_WRITER_REQUIRED: Final[bool] = True
BLIND_RESEND_ALLOWED: Final[bool] = False
EPHEMERAL_PERMISSION_SURVIVES_RESTART: Final[bool] = False

# Intersection of section 21 allowed-next and section 46 implementable guards.
# EVALUATING + NO_ACTION uses WAITING (section 21 does not list READY).
# PERMISSION_CHECK never advances to SUBMITTING in this offline package.
_OFFLINE_TRANSITIONS: Final[dict[tuple[str, str], tuple[str, str, tuple[str, ...]]]] = {
    ("STOPPED", "authorized_start"): (
        "INITIALIZING",
        "CONTINUE",
        ("create_cycle_epoch", "load_exact_versions"),
    ),
    ("INITIALIZING", "invariants_valid"): (
        "SYNCING",
        "CONTINUE",
        ("persist_initialization_proof",),
    ),
    ("INITIALIZING", "critical_invariant_fails"): (
        "HALTED",
        "HALT",
        ("persist_failure", "fail_closed"),
    ),
    ("SYNCING", "fresh_state_proven"): ("READY", "CONTINUE", ("persist_sync_proof",)),
    ("SYNCING", "recoverable_dependency_issue"): (
        "DEGRADED",
        "DEGRADE",
        ("record_degraded_reason",),
    ),
    ("READY", "cycle_due"): ("EVALUATING", "CONTINUE", ("allocate_unique_cycle_id",)),
    ("READY", "unrecoverable_invariant"): ("HALTED", "HALT", ("fail_closed",)),
    ("EVALUATING", "canonical_no_action"): (
        "WAITING",
        "WAIT",
        ("persist_decision_event",),
    ),
    ("EVALUATING", "canonical_plan_candidate_produced"): (
        "PLANNED",
        "CONTINUE",
        ("persist_decision_lineage",),
    ),
    ("EVALUATING", "recoverable_dependency_issue"): (
        "DEGRADED",
        "DEGRADE",
        ("record_degraded_reason",),
    ),
    ("PLANNED", "plan_still_admissible"): (
        "PERMISSION_CHECK",
        "CONTINUE",
        ("freeze_plan_identity",),
    ),
    ("PLANNED", "hard_predicate_false"): (
        "WAITING",
        "WAIT",
        ("persist_deny_no_wire", "no_wire"),
    ),
    ("PERMISSION_CHECK", "hard_predicate_false"): (
        "WAITING",
        "WAIT",
        ("persist_deny_no_wire", "no_wire"),
    ),
    ("PERMISSION_CHECK", "ephemeral_predicates_true"): (
        "WAITING",
        "WAIT",
        ("persist_deny_no_wire", "no_wire"),
    ),
    ("SUBMITTING", "transport_outcome_known"): (
        "RECONCILING",
        "CONTINUE",
        ("persist_exact_response", "no_wire"),
    ),
    ("SUBMITTING", "transport_outcome_ambiguous"): (
        "RECONCILING",
        "WAIT",
        ("forbid_resend_mark_ambiguity", "no_wire"),
    ),
    ("RECONCILING", "venue_truth_proven"): (
        "OBSERVING",
        "CONTINUE",
        ("persist_reconciliation_proof", "no_wire"),
    ),
    ("RECONCILING", "truth_not_provable_recoverable"): (
        "RECOVERING",
        "RECOVER",
        ("no_risk_increase", "no_wire"),
    ),
    ("OBSERVING", "evidence_persisted_coherent"): (
        "WAITING",
        "CONTINUE",
        ("close_cycle",),
    ),
    ("WAITING", "fresh_state_proven"): ("READY", "CONTINUE", ("persist_sync_proof",)),
    ("WAITING", "recoverable_dependency_issue"): (
        "DEGRADED",
        "DEGRADE",
        ("record_degraded_reason",),
    ),
    ("DEGRADED", "recovery_policy_admits_attempt"): (
        "RECOVERING",
        "RECOVER",
        ("bounded_recovery_action",),
    ),
    ("DEGRADED", "unrecoverable_invariant"): ("HALTED", "HALT", ("fail_closed",)),
    ("RECOVERING", "reproof_succeeds"): ("SYNCING", "CONTINUE", ("persist_sync_proof",)),
    ("RECOVERING", "unrecoverable_invariant"): ("HALTED", "HALT", ("fail_closed",)),
    ("HALTED", "authorized_start"): (
        "INITIALIZING",
        "CONTINUE",
        ("create_cycle_epoch", "load_exact_versions"),
    ),
}

_ANY_UNRECOVERABLE: Final[frozenset[str]] = frozenset(SUPERVISOR_STATE_V0) - frozenset({"HALTED"})


@dataclass(frozen=True)
class SupervisorTransitionV0:
    from_state: str
    to_state: str
    event: str
    outcome: str
    actions: tuple[str, ...]
    rejected: bool
    reason_codes: tuple[str, ...]
    cycle_id: str
    record: MappingProxyType[str, Any]


class DeterministicAutonomySupervisorV0:
    """Offline no-order supervisor. Execution remains unreachable."""

    def __init__(self, *, fencing_token: str, initial_state: str = "STOPPED") -> None:
        if not fencing_token:
            raise DdoValidationError("FENCING_TOKEN_REQUIRED")
        if initial_state not in SUPERVISOR_STATE_V0:
            raise DdoValidationError(f"UNKNOWN_ENUM_VALUE:initial_state:{initial_state!r}")
        if AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY or AUTONOMY_SUPERVISOR_EXECUTION_AUTHORITY:
            raise DdoValidationError("AUTONOMY_SUPERVISOR_MUST_REMAIN_UNREACHABLE")
        self._fencing_token = fencing_token
        self._writer_held = True
        self._state = initial_state
        self._cycle_id: str | None = None
        self._seen_cycle_ids: set[str] = set()
        self._transitions: list[SupervisorTransitionV0] = []

    @property
    def state(self) -> str:
        return self._state

    @property
    def cycle_id(self) -> str | None:
        return self._cycle_id

    def reconstruct(self, records: tuple[Mapping[str, Any], ...]) -> None:
        if not records:
            self._state = "STOPPED"
            self._cycle_id = None
            return
        last = records[-1]
        self._state = str(last["to_state"])
        self._cycle_id = str(last["cycle_id"])
        self._seen_cycle_ids = {str(item["cycle_id"]) for item in records if item.get("cycle_id")}
        if self._state == "SUBMITTING":
            # Crash reconstruction: in-flight mutation is ambiguous. No resend.
            return

    def transition(
        self,
        *,
        event: str,
        health_snapshot: Mapping[str, Any],
        authority_snapshot: Mapping[str, Any],
        record_id: str,
        event_time_utc: str,
        correlation_id: str,
        cycle_id: str,
        producer_id: str,
        code_sha: str = "UNKNOWN",
        config_hash: str = "UNKNOWN",
        evidence_hash: str = "UNKNOWN",
        evidence_source_refs: list[str] | None = None,
        causal_parent_ids: list[str] | None = None,
        authority_owner: str = "UNKNOWN",
    ) -> SupervisorTransitionV0:
        if not self._writer_held:
            raise DdoValidationError("SINGLE_WRITER_FENCING_LOST")
        if event not in SUPERVISOR_EVENT_V0:
            raise DdoValidationError(f"UNKNOWN_ENUM_VALUE:event:{event!r}")
        health = validate_health_snapshot_v0(health_snapshot)
        if authority_snapshot.get("execution_authority") not in (None, False, "NONE"):
            raise DdoValidationError("SUPERVISOR_CANNOT_RECEIVE_EXECUTION_AUTHORITY")
        if event == "duplicate_cycle_invocation" or (
            event == "cycle_due" and cycle_id in self._seen_cycle_ids
        ):
            return self._record(
                from_state=self._state,
                to_state=self._state,
                event="duplicate_cycle_invocation",
                outcome="WAIT",
                actions=("collapse_duplicate_cycle", "no_wire"),
                rejected=True,
                reason="DUPLICATE_CYCLE_COLLAPSED",
                record_id=record_id,
                event_time_utc=event_time_utc,
                correlation_id=correlation_id,
                cycle_id=cycle_id,
                producer_id=producer_id,
                health=health,
                code_sha=code_sha,
                config_hash=config_hash,
                evidence_hash=evidence_hash,
                evidence_source_refs=evidence_source_refs,
                causal_parent_ids=causal_parent_ids,
                authority_owner=authority_owner,
            )
        if event == "unrecoverable_invariant" and self._state in _ANY_UNRECOVERABLE:
            next_state, outcome, actions = ("HALTED", "HALT", ("fail_closed",))
            rejected = False
            reason = "UNRECOVERABLE_INVARIANT"
        else:
            mapped = _OFFLINE_TRANSITIONS.get((self._state, event))
            if mapped is None:
                return self._record(
                    from_state=self._state,
                    to_state=self._state,
                    event=event,
                    outcome="WAIT",
                    actions=("no_wire",),
                    rejected=True,
                    reason="TRANSITION_REJECTED",
                    record_id=record_id,
                    event_time_utc=event_time_utc,
                    correlation_id=correlation_id,
                    cycle_id=cycle_id,
                    producer_id=producer_id,
                    health=health,
                    code_sha=code_sha,
                    config_hash=config_hash,
                    evidence_hash=evidence_hash,
                    evidence_source_refs=evidence_source_refs,
                    causal_parent_ids=causal_parent_ids,
                    authority_owner=authority_owner,
                )
            next_state, outcome, actions = mapped
            rejected = False
            reason = "TRANSITION_ACCEPTED"
            if next_state == "SUBMITTING":
                raise DdoValidationError("SUBMITTING_UNREACHABLE_OFFLINE")
            if "no_wire" not in actions and next_state in {"PERMISSION_CHECK", "WAITING"}:
                if event == "ephemeral_predicates_true":
                    reason = "EXECUTION_AUTHORITY_NONE"
        if next_state == "EVALUATING":
            self._cycle_id = cycle_id
            self._seen_cycle_ids.add(cycle_id)
        result = self._record(
            from_state=self._state,
            to_state=next_state,
            event=event,
            outcome=outcome,
            actions=actions,
            rejected=rejected,
            reason=reason,
            record_id=record_id,
            event_time_utc=event_time_utc,
            correlation_id=correlation_id,
            cycle_id=cycle_id if self._cycle_id is None else (self._cycle_id or cycle_id),
            producer_id=producer_id,
            health=health,
            code_sha=code_sha,
            config_hash=config_hash,
            evidence_hash=evidence_hash,
            evidence_source_refs=evidence_source_refs,
            causal_parent_ids=causal_parent_ids,
            authority_owner=authority_owner,
        )
        if not rejected:
            self._state = next_state
        return result

    def _record(
        self,
        *,
        from_state: str,
        to_state: str,
        event: str,
        outcome: str,
        actions: tuple[str, ...],
        rejected: bool,
        reason: str,
        record_id: str,
        event_time_utc: str,
        correlation_id: str,
        cycle_id: str,
        producer_id: str,
        health: Mapping[str, Any],
        code_sha: str,
        config_hash: str,
        evidence_hash: str,
        evidence_source_refs: list[str] | None,
        causal_parent_ids: list[str] | None,
        authority_owner: str,
    ) -> SupervisorTransitionV0:
        record = build_autonomy_cycle_record_v0(
            {
                "schema_name": "autonomy_cycle_record",
                "schema_version": "autonomy_cycle_record_v0",
                "record_id": record_id,
                "event_time_utc": event_time_utc,
                "correlation_id": correlation_id,
                "cycle_id": cycle_id,
                "causal_parent_ids": causal_parent_ids or [],
                "producer_id": producer_id,
                "authority_owner": authority_owner,
                "code_sha": code_sha,
                "config_hash": config_hash,
                "evidence_hash": evidence_hash,
                "evidence_source_refs": evidence_source_refs or [str(health["record_id"])],
                "from_state": from_state,
                "to_state": to_state,
                "event": event,
                "outcome": outcome,
                "actions": list(actions),
                "reason_codes": [
                    {
                        "taxonomy_id": "blueprint.ddo.reason_v0",
                        "code": UNKNOWN,
                        "source_taxonomy_ref": None,
                    }
                ],
                "health_snapshot_ref": health["record_id"],
                "rejected_transition": rejected,
                "execution_reachable": False,
            }
        )
        result = SupervisorTransitionV0(
            from_state=from_state,
            to_state=to_state,
            event=event,
            outcome=outcome,
            actions=actions,
            rejected=rejected,
            reason_codes=(reason,),
            cycle_id=cycle_id,
            record=record,
        )
        self._transitions.append(result)
        return result

    def persisted_transitions(self) -> tuple[SupervisorTransitionV0, ...]:
        return tuple(self._transitions)
