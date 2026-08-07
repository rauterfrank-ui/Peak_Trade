"""Live autonomous recovery contracts (§11.19 Cap 11.11 / §11.8).

Fixture-only. No Live activation, network, credential load, or order submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_AUTONOMOUS_RECOVERY_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_CONTRACT_BOUND,
    LIVE_AUTONOMOUS_RECOVERY_OWNER,
    LIVE_AUTONOMOUS_RECOVERY_PROVEN,
    LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED,
    LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11,
    LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    OWNER,
    RECOVERY_FORBIDDEN_CONDITIONS,
    RECOVERY_PERMITTED_GATES,
)


class LiveAutonomousRecoveryError(RuntimeError):
    """Fail-closed Live autonomous recovery violation."""


@dataclass(frozen=True)
class LiveAutonomousRecoveryRecordV1:
    """Fixture-only Live autonomous recovery bound record (no real recovery side-effect)."""

    stage: str
    recovery_session_id: str
    from_state: str
    to_state: str
    root_cause_classified: bool
    recovery_policy_pre_ratified: bool
    retry_budget_available: bool
    authorization_still_valid: bool
    no_unresolved_economic_ambiguity: bool
    post_recovery_reconciliation_pass: bool
    rollback_contract_id: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    activated: bool = False
    proven: bool = False
    submitted: bool = False
    execution_performed: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_AUTONOMOUS_RECOVERY_OWNER


def build_live_autonomous_recovery_record_v1(
    *,
    stage: str = "LIVE_AUTONOMOUS_SINGLE_FUTURE",
    recovery_session_id: str = "live-recovery-fixture-v1",
    from_state: str = "RECOVERING",
    to_state: str = "READY",
    root_cause_classified: bool = True,
    recovery_policy_pre_ratified: bool = True,
    retry_budget_available: bool = True,
    authorization_still_valid: bool = True,
    no_unresolved_economic_ambiguity: bool = True,
    post_recovery_reconciliation_pass: bool = True,
    rollback_contract_id: str = "live-recovery-rollback-fixture-v1",
    source: str = "FIXTURE_ONLY",
) -> LiveAutonomousRecoveryRecordV1:
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveAutonomousRecoveryError(f"UNKNOWN_OR_FORBIDDEN_LIVE_AUTONOMOUS_STAGE:{stage}")
    if source != "FIXTURE_ONLY":
        raise LiveAutonomousRecoveryError(
            f"NON_FIXTURE_LIVE_AUTONOMOUS_SOURCE_FORBIDDEN_IN_CAPABILITY_11_11:{source}"
        )
    if not recovery_session_id or not rollback_contract_id:
        raise LiveAutonomousRecoveryError("LIVE_AUTONOMOUS_RECOVERY_IDENTITY_FIELDS_INCOMPLETE")

    gates = {
        "ROOT_CAUSE_CLASSIFIED": root_cause_classified,
        "RECOVERY_POLICY_PRE_RATIFIED": recovery_policy_pre_ratified,
        "RETRY_BUDGET_AVAILABLE": retry_budget_available,
        "AUTHORIZATION_STILL_VALID": authorization_still_valid,
        "NO_UNRESOLVED_ECONOMIC_AMBIGUITY": no_unresolved_economic_ambiguity,
        "POST_RECOVERY_RECONCILIATION_PASS": post_recovery_reconciliation_pass,
    }
    for gate_name in RECOVERY_PERMITTED_GATES:
        if gates.get(gate_name) is not True:
            raise LiveAutonomousRecoveryError(
                f"LIVE_AUTONOMOUS_RECOVERY_GATE_NOT_SATISFIED:{gate_name}"
            )

    return LiveAutonomousRecoveryRecordV1(
        stage=stage,
        recovery_session_id=recovery_session_id,
        from_state=from_state,
        to_state=to_state,
        root_cause_classified=root_cause_classified,
        recovery_policy_pre_ratified=recovery_policy_pre_ratified,
        retry_budget_available=retry_budget_available,
        authorization_still_valid=authorization_still_valid,
        no_unresolved_economic_ambiguity=no_unresolved_economic_ambiguity,
        post_recovery_reconciliation_pass=post_recovery_reconciliation_pass,
        rollback_contract_id=rollback_contract_id,
        source=source,
        network_effect="NONE",
        activated=False,
        proven=False,
        submitted=False,
        execution_performed=False,
    )


def refuse_autonomous_recovery_for_forbidden_condition_v1(*, condition: str) -> dict[str, Any]:
    if condition not in RECOVERY_FORBIDDEN_CONDITIONS:
        raise LiveAutonomousRecoveryError(f"UNKNOWN_RECOVERY_FORBIDDEN_CONDITION:{condition}")
    raise LiveAutonomousRecoveryError(
        f"AUTONOMOUS_RECOVERY_FORBIDDEN_REQUIRES_OWNER_LOCKED_OR_HALTED:{condition}"
    )


def refuse_live_autonomous_recovery_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveAutonomousRecoveryError(
        f"LIVE_AUTONOMOUS_RECOVERY_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_action}"
    )


def refuse_live_autonomous_recovery_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    raise LiveAutonomousRecoveryError(
        f"LIVE_AUTONOMOUS_RECOVERY_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_11:{client_order_id}"
    )


def refuse_live_autonomous_recovery_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LiveAutonomousRecoveryError(
        f"LIVE_AUTONOMOUS_RECOVERY_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_11:{session_id}"
    )


def refuse_live_autonomous_recovery_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveAutonomousRecoveryError(
        f"LIVE_AUTONOMOUS_RECOVERY_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_action}"
    )


def refuse_live_autonomous_recovery_proven_overclaim_v1(*, claimed_field: str) -> dict[str, Any]:
    raise LiveAutonomousRecoveryError(
        f"LIVE_AUTONOMOUS_RECOVERY_PROVEN_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_11:{claimed_field}"
    )


def prove_live_autonomous_recovery_contract_v1() -> dict[str, Any]:
    record = build_live_autonomous_recovery_record_v1()

    non_fixture_blocked = False
    try:
        build_live_autonomous_recovery_record_v1(source="LIVE_NETWORK")
    except LiveAutonomousRecoveryError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    gate_blocked = False
    try:
        build_live_autonomous_recovery_record_v1(root_cause_classified=False)
    except LiveAutonomousRecoveryError as exc:
        gate_blocked = "LIVE_AUTONOMOUS_RECOVERY_GATE_NOT_SATISFIED" in str(exc)

    forbidden_blocked: dict[str, bool] = {}
    for condition in RECOVERY_FORBIDDEN_CONDITIONS:
        blocked = False
        try:
            refuse_autonomous_recovery_for_forbidden_condition_v1(condition=condition)
        except LiveAutonomousRecoveryError as exc:
            blocked = "AUTONOMOUS_RECOVERY_FORBIDDEN_REQUIRES_OWNER_LOCKED_OR_HALTED" in str(exc)
        forbidden_blocked[condition] = blocked

    unknown_forbidden_condition_blocked = False
    try:
        refuse_autonomous_recovery_for_forbidden_condition_v1(condition="invented_condition")
    except LiveAutonomousRecoveryError as exc:
        unknown_forbidden_condition_blocked = "UNKNOWN_RECOVERY_FORBIDDEN_CONDITION" in str(exc)

    activation_blocked = False
    try:
        refuse_live_autonomous_recovery_activation_v1(claimed_action="activate_recovery")
    except LiveAutonomousRecoveryError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_live_autonomous_recovery_order_submit_v1(client_order_id="pt-coid-recovery")
    except LiveAutonomousRecoveryError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_autonomous_recovery_network_session_v1(session_id="live-recovery-session")
    except LiveAutonomousRecoveryError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_autonomous_recovery_credential_access_v1(claimed_action="load_api_key")
    except LiveAutonomousRecoveryError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    proven_overclaim_blocked = False
    try:
        refuse_live_autonomous_recovery_proven_overclaim_v1(
            claimed_field="LIVE_AUTONOMOUS_RECOVERY_PROVEN"
        )
    except LiveAutonomousRecoveryError as exc:
        proven_overclaim_blocked = "PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    all_forbidden_blocked = all(forbidden_blocked.values())
    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.activated is False,
            record.proven is False,
            record.submitted is False,
            record.execution_performed is False,
            record.network_effect == "NONE",
            record.root_cause_classified is True,
            non_fixture_blocked,
            gate_blocked,
            all_forbidden_blocked,
            unknown_forbidden_condition_blocked,
            activation_blocked,
            submit_blocked,
            session_blocked,
            credential_blocked,
            proven_overclaim_blocked,
            LIVE_AUTONOMOUS_RECOVERY_CONTRACT_BOUND is True,
            LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED is False,
            LIVE_AUTONOMOUS_RECOVERY_ACTIVATED is False,
            LIVE_AUTONOMOUS_RECOVERY_PROVEN is False,
            LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED is False,
            LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11 is False,
            LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11 is False,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "LIVE_AUTONOMOUS_RECOVERY_CONTRACT_BOUND": True,
        "LIVE_AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED": False,
        "LIVE_AUTONOMOUS_RECOVERY_ACTIVATED": False,
        "LIVE_AUTONOMOUS_RECOVERY_PROVEN": False,
        "LIVE_AUTONOMOUS_SINGLE_FUTURE_ACTIVATED": False,
        "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_11": False,
        "LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_11": False,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "recovery_permitted_gates": list(RECOVERY_PERMITTED_GATES),
        "recovery_forbidden_conditions": list(RECOVERY_FORBIDDEN_CONDITIONS),
        "forbidden_condition_blocked": forbidden_blocked,
        "non_fixture_blocked": non_fixture_blocked,
        "gate_not_satisfied_blocked": gate_blocked,
        "unknown_forbidden_condition_blocked": unknown_forbidden_condition_blocked,
        "activation_blocked": activation_blocked,
        "submit_blocked": submit_blocked,
        "network_session_blocked": session_blocked,
        "credential_access_blocked": credential_blocked,
        "proven_overclaim_blocked": proven_overclaim_blocked,
        "sample_recovery_session_id": record.recovery_session_id,
        "sample_from_state": record.from_state,
        "sample_to_state": record.to_state,
        "OWNER": LIVE_AUTONOMOUS_RECOVERY_OWNER,
    }
