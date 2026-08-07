"""Live autonomous degradation contracts (§11.19 Cap 11.11 / §11.8).

Fixture-only. No Live activation, network, or order submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.constants_v1 import (
    AUTOMATIC_HALT_ALLOWED,
    AUTOMATIC_STAGE_DEMOTION_ALLOWED,
    BOUNDED_RECOVERY_ROLLBACK_CONTRACT_REQUIRED,
    CONTRACT_VERSION,
    LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED,
    LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_ACTIVATED,
    LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_BOUND,
    LIVE_AUTONOMOUS_DEGRADATION_OWNER,
    LIVE_AUTONOMOUS_DEGRADATION_PROVEN,
    LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED,
    LIVE_BOUNDED_MULTI_SESSION_ACTIVATED,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    NO_AUTOMATIC_STAGE_PROMOTION,
    OPERATING_STATES,
    OWNER,
    OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION,
    POSITION_COUNT_LIMIT,
    SINGLE_FUTURE_ONLY,
)


class LiveAutonomousDegradationError(RuntimeError):
    """Fail-closed Live autonomous degradation violation."""


@dataclass(frozen=True)
class LiveOperatingStateTransitionRecordV1:
    """Fixture-only Live operating-state transition bound record."""

    stage: str
    from_state: str
    to_state: str
    reason_code: str
    triggering_evidence_id: str
    authority_source: str
    persisted_timestamp: str
    degradation_session_id: str
    rollback_contract_id: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    activated: bool = False
    proven: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_AUTONOMOUS_DEGRADATION_OWNER


def build_live_operating_state_transition_record_v1(
    *,
    stage: str = "LIVE_AUTONOMOUS_SINGLE_FUTURE",
    from_state: str = "ACTIVE",
    to_state: str = "DEGRADED_NO_NEW_ENTRY",
    reason_code: str = "RECONCILIATION_DIVERGENCE",
    triggering_evidence_id: str = "live-degradation-fixture-evidence-v1",
    authority_source: str = "canonical_safety_policy",
    persisted_timestamp: str = "2026-08-07T00:00:00Z",
    degradation_session_id: str = "live-degradation-fixture-v1",
    rollback_contract_id: str = "live-degradation-rollback-fixture-v1",
    source: str = "FIXTURE_ONLY",
) -> LiveOperatingStateTransitionRecordV1:
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveAutonomousDegradationError(f"UNKNOWN_OR_FORBIDDEN_LIVE_AUTONOMOUS_STAGE:{stage}")
    if from_state not in OPERATING_STATES:
        raise LiveAutonomousDegradationError(f"UNKNOWN_OPERATING_STATE:{from_state}")
    if to_state not in OPERATING_STATES:
        raise LiveAutonomousDegradationError(f"UNKNOWN_OPERATING_STATE:{to_state}")
    if source != "FIXTURE_ONLY":
        raise LiveAutonomousDegradationError(
            f"NON_FIXTURE_LIVE_AUTONOMOUS_SOURCE_FORBIDDEN_IN_CAPABILITY_11_11:{source}"
        )
    if not reason_code or not authority_source or not persisted_timestamp:
        raise LiveAutonomousDegradationError("OPERATING_TRANSITION_FIELDS_INCOMPLETE")
    if not triggering_evidence_id or not degradation_session_id or not rollback_contract_id:
        raise LiveAutonomousDegradationError("OPERATING_TRANSITION_IDENTITY_FIELDS_INCOMPLETE")

    return LiveOperatingStateTransitionRecordV1(
        stage=stage,
        from_state=from_state,
        to_state=to_state,
        reason_code=reason_code,
        triggering_evidence_id=triggering_evidence_id,
        authority_source=authority_source,
        persisted_timestamp=persisted_timestamp,
        degradation_session_id=degradation_session_id,
        rollback_contract_id=rollback_contract_id,
        source=source,
        network_effect="NONE",
        activated=False,
        proven=False,
    )


def refuse_live_autonomous_degradation_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveAutonomousDegradationError(
        f"LIVE_AUTONOMOUS_DEGRADATION_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_action}"
    )


def refuse_live_autonomous_degradation_proven_overclaim_v1(*, claimed_field: str) -> dict[str, Any]:
    raise LiveAutonomousDegradationError(
        f"LIVE_AUTONOMOUS_DEGRADATION_PROVEN_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_field}"
    )


def refuse_cap_11_12_live_readiness_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LiveAutonomousDegradationError(
        f"CAPABILITY_11_12_SURFACE_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_surface}"
    )


def prove_live_autonomous_degradation_contract_v1() -> dict[str, Any]:
    record = build_live_operating_state_transition_record_v1()

    non_fixture_blocked = False
    try:
        build_live_operating_state_transition_record_v1(source="LIVE_NETWORK")
    except LiveAutonomousDegradationError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    unknown_state_blocked = False
    try:
        build_live_operating_state_transition_record_v1(to_state="UNBOUNDED_AUTONOMY")
    except LiveAutonomousDegradationError as exc:
        unknown_state_blocked = "UNKNOWN_OPERATING_STATE" in str(exc)

    unknown_stage_blocked = False
    try:
        build_live_operating_state_transition_record_v1(stage="LIVE_BOUNDED_SINGLE_FUTURE")
    except LiveAutonomousDegradationError as exc:
        unknown_stage_blocked = "UNKNOWN_OR_FORBIDDEN_LIVE_AUTONOMOUS_STAGE" in str(exc)

    incomplete_blocked = False
    try:
        build_live_operating_state_transition_record_v1(reason_code="")
    except LiveAutonomousDegradationError as exc:
        incomplete_blocked = "OPERATING_TRANSITION_FIELDS_INCOMPLETE" in str(exc)

    activation_blocked = False
    try:
        refuse_live_autonomous_degradation_activation_v1(claimed_action="activate_degradation")
    except LiveAutonomousDegradationError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    proven_overclaim_blocked = False
    try:
        refuse_live_autonomous_degradation_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_DEGRADATION_PROVEN"
        )
    except LiveAutonomousDegradationError as exc:
        proven_overclaim_blocked = "PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    cap_11_12_blocked = False
    try:
        refuse_cap_11_12_live_readiness_v1(claimed_surface="FULLY_AUTONOMOUS_LIVE_TRADING_READY")
    except LiveAutonomousDegradationError as exc:
        cap_11_12_blocked = "CAPABILITY_11_12_SURFACE_FORBIDDEN" in str(exc)

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.activated is False,
            record.proven is False,
            record.network_effect == "NONE",
            record.to_state == "DEGRADED_NO_NEW_ENTRY",
            non_fixture_blocked,
            unknown_state_blocked,
            unknown_stage_blocked,
            incomplete_blocked,
            activation_blocked,
            proven_overclaim_blocked,
            cap_11_12_blocked,
            LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_BOUND is True,
            LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_ACTIVATED is False,
            LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED is False,
            LIVE_AUTONOMOUS_DEGRADATION_PROVEN is False,
            LIVE_BOUNDED_MULTI_SESSION_ACTIVATED is False,
            LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED is False,
            MINIMUM_RATIFIED_NOTIONAL_ONLY is True,
            SINGLE_FUTURE_ONLY is True,
            POSITION_COUNT_LIMIT == 1,
            NO_AUTOMATIC_STAGE_PROMOTION is True,
            OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION is True,
            AUTOMATIC_STAGE_DEMOTION_ALLOWED is True,
            AUTOMATIC_HALT_ALLOWED is True,
            BOUNDED_RECOVERY_ROLLBACK_CONTRACT_REQUIRED is True,
            set(OPERATING_STATES)
            == {
                "OFF",
                "PREFLIGHT",
                "RECONCILING",
                "READY",
                "ACTIVE",
                "DEGRADED_NO_NEW_ENTRY",
                "EXIT_ONLY",
                "REDUCE_ONLY",
                "CANCEL_ALL",
                "RECOVERING",
                "HALTED",
                "OWNER_LOCKED",
            },
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_BOUND": True,
        "LIVE_AUTONOMOUS_DEGRADATION_CONTRACT_ACTIVATED": False,
        "LIVE_AUTONOMOUS_DEGRADATION_ACTIVATED": False,
        "LIVE_AUTONOMOUS_DEGRADATION_PROVEN": False,
        "LIVE_BOUNDED_MULTI_SESSION_ACTIVATED": False,
        "LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED": False,
        "MINIMUM_RATIFIED_NOTIONAL_ONLY": True,
        "SINGLE_FUTURE_ONLY": True,
        "POSITION_COUNT_LIMIT": POSITION_COUNT_LIMIT,
        "NO_AUTOMATIC_STAGE_PROMOTION": True,
        "OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION": True,
        "AUTOMATIC_STAGE_DEMOTION_ALLOWED": True,
        "AUTOMATIC_HALT_ALLOWED": True,
        "BOUNDED_RECOVERY_ROLLBACK_CONTRACT_REQUIRED": True,
        "operating_states": list(OPERATING_STATES),
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "non_fixture_blocked": non_fixture_blocked,
        "unknown_state_blocked": unknown_state_blocked,
        "unknown_stage_blocked": unknown_stage_blocked,
        "incomplete_transition_blocked": incomplete_blocked,
        "activation_blocked": activation_blocked,
        "proven_overclaim_blocked": proven_overclaim_blocked,
        "cap_11_12_surface_blocked": cap_11_12_blocked,
        "sample_from_state": record.from_state,
        "sample_to_state": record.to_state,
        "sample_reason_code": record.reason_code,
        "sample_degradation_session_id": record.degradation_session_id,
        "OWNER": LIVE_AUTONOMOUS_DEGRADATION_OWNER,
    }
