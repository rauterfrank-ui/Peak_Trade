"""Autonomous recovery / degradation contracts (§11.8) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED,
    AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND,
    AUTONOMOUS_RECOVERY_DEGRADATION_OWNER,
    CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED,
    CONTRACT_VERSION,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED,
    OPERATING_STATES,
    OWNER,
    RECOVERY_FORBIDDEN_CONDITIONS,
    TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
)


class AutonomousRecoveryDegradationError(RuntimeError):
    """Fail-closed autonomous recovery / degradation violation."""

    __test__ = False


@dataclass(frozen=True)
class OperatingStateTransitionRecordV1:
    __test__ = False

    from_state: str
    to_state: str
    reason_code: str
    authority_source: str
    persisted_timestamp: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = AUTONOMOUS_RECOVERY_DEGRADATION_OWNER


def build_operating_state_transition_record_v1(
    *,
    from_state: str,
    to_state: str,
    reason_code: str,
    authority_source: str,
    persisted_timestamp: str,
) -> OperatingStateTransitionRecordV1:
    if from_state not in OPERATING_STATES:
        raise AutonomousRecoveryDegradationError(f"UNKNOWN_OPERATING_STATE:{from_state}")
    if to_state not in OPERATING_STATES:
        raise AutonomousRecoveryDegradationError(f"UNKNOWN_OPERATING_STATE:{to_state}")
    if not reason_code or not authority_source or not persisted_timestamp:
        raise AutonomousRecoveryDegradationError("OPERATING_TRANSITION_FIELDS_INCOMPLETE")
    return OperatingStateTransitionRecordV1(
        from_state=from_state,
        to_state=to_state,
        reason_code=reason_code,
        authority_source=authority_source,
        persisted_timestamp=persisted_timestamp,
    )


def refuse_autonomous_recovery_for_forbidden_condition_v1(*, condition: str) -> dict[str, Any]:
    if condition not in RECOVERY_FORBIDDEN_CONDITIONS:
        raise AutonomousRecoveryDegradationError(
            f"UNKNOWN_RECOVERY_FORBIDDEN_CONDITION:{condition}"
        )
    raise AutonomousRecoveryDegradationError(
        f"AUTONOMOUS_RECOVERY_FORBIDDEN_REQUIRES_OWNER_LOCKED_OR_HALTED:{condition}"
    )


def refuse_cap_11_6_long_running_autonomous_testnet_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise AutonomousRecoveryDegradationError(
        f"CAPABILITY_11_6_SURFACE_FORBIDDEN_IN_CAPABILITY_11_5:{claimed_surface}"
    )


def prove_autonomous_recovery_degradation_contract_v1() -> dict[str, Any]:
    transition = build_operating_state_transition_record_v1(
        from_state="ACTIVE",
        to_state="DEGRADED_NO_NEW_ENTRY",
        reason_code="RECONCILIATION_DIVERGENCE",
        authority_source="canonical_safety_policy",
        persisted_timestamp="2026-08-07T00:00:00Z",
    )

    unknown_state_blocked = False
    try:
        build_operating_state_transition_record_v1(
            from_state="ACTIVE",
            to_state="UNBOUNDED_AUTONOMY",
            reason_code="x",
            authority_source="y",
            persisted_timestamp="2026-08-07T00:00:00Z",
        )
    except AutonomousRecoveryDegradationError as exc:
        unknown_state_blocked = "UNKNOWN_OPERATING_STATE" in str(exc)

    incomplete_blocked = False
    try:
        build_operating_state_transition_record_v1(
            from_state="ACTIVE",
            to_state="HALTED",
            reason_code="",
            authority_source="canonical_safety_policy",
            persisted_timestamp="2026-08-07T00:00:00Z",
        )
    except AutonomousRecoveryDegradationError as exc:
        incomplete_blocked = "OPERATING_TRANSITION_FIELDS_INCOMPLETE" in str(exc)

    forbidden_blocked: dict[str, bool] = {}
    for condition in RECOVERY_FORBIDDEN_CONDITIONS:
        blocked = False
        try:
            refuse_autonomous_recovery_for_forbidden_condition_v1(condition=condition)
        except AutonomousRecoveryDegradationError as exc:
            blocked = "AUTONOMOUS_RECOVERY_FORBIDDEN_REQUIRES_OWNER_LOCKED_OR_HALTED" in str(exc)
        forbidden_blocked[condition] = blocked

    unknown_forbidden_condition_blocked = False
    try:
        refuse_autonomous_recovery_for_forbidden_condition_v1(condition="invented_condition")
    except AutonomousRecoveryDegradationError as exc:
        unknown_forbidden_condition_blocked = "UNKNOWN_RECOVERY_FORBIDDEN_CONDITION" in str(exc)

    cap_11_6_blocked = False
    try:
        refuse_cap_11_6_long_running_autonomous_testnet_v1(
            claimed_surface="long_running_autonomous_testnet_campaign"
        )
    except AutonomousRecoveryDegradationError as exc:
        cap_11_6_blocked = "CAPABILITY_11_6_SURFACE_FORBIDDEN" in str(exc)

    all_forbidden_blocked = all(forbidden_blocked.values())
    ok = all(
        [
            transition.source == "FIXTURE_ONLY",
            unknown_state_blocked,
            incomplete_blocked,
            all_forbidden_blocked,
            unknown_forbidden_condition_blocked,
            cap_11_6_blocked,
            AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND is True,
            AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED is False,
            TESTNET_AUTONOMOUS_RECOVERY_PROVEN is False,
            CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED is False,
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED is False,
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
        ]
    )
    return {
        "ok": ok,
        "AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND": True,
        "AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED": False,
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": False,
        "CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED": False,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED": False,
        "operating_states": list(OPERATING_STATES),
        "recovery_forbidden_conditions": list(RECOVERY_FORBIDDEN_CONDITIONS),
        "forbidden_condition_blocked": forbidden_blocked,
        "unknown_state_blocked": unknown_state_blocked,
        "incomplete_transition_blocked": incomplete_blocked,
        "unknown_forbidden_condition_blocked": unknown_forbidden_condition_blocked,
        "cap_11_6_surface_blocked": cap_11_6_blocked,
        "sample_transition": {
            "from_state": transition.from_state,
            "to_state": transition.to_state,
            "reason_code": transition.reason_code,
        },
        "OWNER": OWNER,
    }
