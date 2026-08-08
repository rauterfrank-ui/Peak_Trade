"""Fully autonomous Live readiness ratification contracts (§11.19 Cap 11.12 / §11.17).

Fixture-only. No Live activation, network, credential load, or order submit.
Readiness may be claimed only when §11.17 prerequisites are satisfied; Cap 11.13
activation remains separately forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (
    AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS,
    AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS,
    CANONICAL_STATEFUL_CORE_PROVEN,
    CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_STARTED,
    CAPABILITY_11_12_STARTED,
    CAPABILITY_11_13_SEPARATE_OWNER_AUTHORIZED_LIVE_ACTIVATION_STARTED,
    CAPABILITY_11_13_STARTED,
    CONTRACT_VERSION,
    FINAL_AUTONOMOUS_LIVE_OPERATING_FORBIDDEN_FIELDS,
    FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_ACTIVATED,
    FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_BOUND,
    FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_FIXTURE_ONLY,
    FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_OWNER,
    FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ACTIVATION_CAPABILITY_PASS,
    LIVE_AUTHORIZATION_VALID,
    OWNER,
    OWNER_LIVE_GO,
)


class FullyAutonomousLiveReadinessRatificationError(RuntimeError):
    """Fail-closed Fully autonomous Live readiness ratification violation."""


@dataclass(frozen=True)
class FullyAutonomousLiveReadinessRatificationRecordV1:
    """Fixture-only readiness ratification record (no activation side-effect)."""

    ratification_session_id: str
    readiness_evaluated: bool
    readiness_satisfied: bool
    ready_claimed: bool
    active_claimed: bool
    missing_true_fields: tuple[str, ...]
    violated_false_fields: tuple[str, ...]
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    activated: bool = False
    contract_version: str = CONTRACT_VERSION
    owner: str = FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_OWNER


def _default_field_snapshot() -> dict[str, bool]:
    return {
        "CANONICAL_STATEFUL_CORE_PROVEN": CANONICAL_STATEFUL_CORE_PROVEN,
        "SIMULATED_LIFECYCLE_PROVEN": False,
        "TESTNET_LIFECYCLE_PROVEN": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_ORDER_LIFECYCLE_PROVEN": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "LIVE_RESTART_PROVEN": False,
        "LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN": False,
        "LIVE_PARTIAL_FILL_RECOVERY_PROVEN": False,
        "LIVE_KILL_SWITCH_PROVEN": False,
        "LIVE_AUTONOMOUS_DEGRADATION_PROVEN": False,
        "LIVE_AUTONOMOUS_RECOVERY_PROVEN": False,
        "LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN": False,
        "LIVE_EVIDENCE_VERIFIED": False,
        "OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE": True,
        "CORE_LOGIC_PARITY_ACROSS_MODES": True,
        "OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION": True,
    }


def evaluate_fully_autonomous_live_readiness_v1(
    *,
    field_values: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    values = dict(_default_field_snapshot())
    if field_values is not None:
        for key, value in field_values.items():
            if key not in values:
                raise FullyAutonomousLiveReadinessRatificationError(
                    f"UNKNOWN_AUTONOMY_CLOSURE_FIELD:{key}"
                )
            if not isinstance(value, bool):
                raise FullyAutonomousLiveReadinessRatificationError(
                    f"NON_BOOLEAN_AUTONOMY_CLOSURE_FIELD:{key}"
                )
            values[key] = value

    missing_true = tuple(
        name for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS if values.get(name) is not True
    )
    violated_false = tuple(
        name for name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS if values.get(name) is not False
    )
    satisfied = not missing_true and not violated_false
    return {
        "readiness_satisfied": satisfied,
        "missing_true_fields": list(missing_true),
        "violated_false_fields": list(violated_false),
        "field_values": values,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY_ALLOWED": satisfied,
    }


def build_fully_autonomous_live_readiness_ratification_record_v1(
    *,
    ratification_session_id: str = "live-readiness-ratification-fixture-v1",
    field_values: Mapping[str, bool] | None = None,
    source: str = "FIXTURE_ONLY",
    ready_claimed: bool = False,
    active_claimed: bool = False,
) -> FullyAutonomousLiveReadinessRatificationRecordV1:
    if source != "FIXTURE_ONLY":
        raise FullyAutonomousLiveReadinessRatificationError(
            f"NON_FIXTURE_LIVE_READINESS_SOURCE_FORBIDDEN_IN_CAPABILITY_11_12:{source}"
        )
    if not ratification_session_id:
        raise FullyAutonomousLiveReadinessRatificationError(
            "LIVE_READINESS_RATIFICATION_IDENTITY_FIELDS_INCOMPLETE"
        )
    if active_claimed:
        raise FullyAutonomousLiveReadinessRatificationError(
            "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE_FORBIDDEN_IN_CAPABILITY_11_12"
        )

    evaluation = evaluate_fully_autonomous_live_readiness_v1(field_values=field_values)
    satisfied = evaluation["readiness_satisfied"] is True
    if ready_claimed and not satisfied:
        raise FullyAutonomousLiveReadinessRatificationError(
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_12"
        )

    return FullyAutonomousLiveReadinessRatificationRecordV1(
        ratification_session_id=ratification_session_id,
        readiness_evaluated=True,
        readiness_satisfied=satisfied,
        ready_claimed=ready_claimed,
        active_claimed=False,
        missing_true_fields=tuple(evaluation["missing_true_fields"]),
        violated_false_fields=tuple(evaluation["violated_false_fields"]),
        source=source,
        network_effect="NONE",
        activated=False,
    )


def refuse_fully_autonomous_live_trading_ready_overclaim_v1(
    *, claimed_field: str = "FULLY_AUTONOMOUS_LIVE_TRADING_READY"
) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_12:"
        f"{claimed_field}"
    )


def refuse_fully_autonomous_live_trading_active_v1(*, claimed_field: str) -> dict[str, Any]:
    if (
        claimed_field not in FINAL_AUTONOMOUS_LIVE_OPERATING_FORBIDDEN_FIELDS
        and claimed_field
        not in {
            "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE",
            "LIVE_ACTIVATION_CAPABILITY_PASS",
            "OWNER_LIVE_GO",
            "LIVE_AUTHORIZATION_VALID",
        }
    ):
        raise FullyAutonomousLiveReadinessRatificationError(
            f"FIELD_NOT_IN_CAPABILITY_11_13_PLUS_FORBIDDEN_SET:{claimed_field}"
        )
    raise FullyAutonomousLiveReadinessRatificationError(
        f"CAPABILITY_11_13_ACTIVATION_CLAIM_FORBIDDEN_IN_CAPABILITY_11_12:{claimed_field}"
    )


def refuse_cap_11_13_live_activation_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        f"CAPABILITY_11_13_SURFACE_FORBIDDEN_IN_CAPABILITY_11_12:{claimed_surface}"
    )


def refuse_live_readiness_ratification_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        f"LIVE_READINESS_RATIFICATION_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_12:{claimed_action}"
    )


def refuse_live_readiness_order_submit_v1(*, client_order_id: str) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        f"LIVE_READINESS_ORDER_SUBMIT_FORBIDDEN_IN_CAPABILITY_11_12:{client_order_id}"
    )


def refuse_live_readiness_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        f"LIVE_READINESS_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_12:{session_id}"
    )


def refuse_live_readiness_credential_access_v1(*, claimed_action: str) -> dict[str, Any]:
    raise FullyAutonomousLiveReadinessRatificationError(
        f"LIVE_READINESS_CREDENTIAL_ACCESS_FORBIDDEN_IN_CAPABILITY_11_12:{claimed_action}"
    )


def prove_fully_autonomous_live_readiness_ratification_contract_v1() -> dict[str, Any]:
    record = build_fully_autonomous_live_readiness_ratification_record_v1()

    non_fixture_blocked = False
    try:
        build_fully_autonomous_live_readiness_ratification_record_v1(source="LIVE_NETWORK")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        non_fixture_blocked = "NON_FIXTURE" in str(exc)

    ready_overclaim_blocked = False
    try:
        build_fully_autonomous_live_readiness_ratification_record_v1(ready_claimed=True)
    except FullyAutonomousLiveReadinessRatificationError as exc:
        ready_overclaim_blocked = "READY_OVERCLAIM_FORBIDDEN" in str(exc)

    active_claim_blocked = False
    try:
        build_fully_autonomous_live_readiness_ratification_record_v1(active_claimed=True)
    except FullyAutonomousLiveReadinessRatificationError as exc:
        active_claim_blocked = "ACTIVE_FORBIDDEN" in str(exc)

    refuse_ready_blocked = False
    try:
        refuse_fully_autonomous_live_trading_ready_overclaim_v1()
    except FullyAutonomousLiveReadinessRatificationError as exc:
        refuse_ready_blocked = "READY_OVERCLAIM_FORBIDDEN" in str(exc)

    refuse_active_blocked = False
    try:
        refuse_fully_autonomous_live_trading_active_v1(
            claimed_field="FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE"
        )
    except FullyAutonomousLiveReadinessRatificationError as exc:
        refuse_active_blocked = "CAPABILITY_11_13_ACTIVATION_CLAIM_FORBIDDEN" in str(exc)

    cap_11_13_blocked = False
    try:
        refuse_cap_11_13_live_activation_v1(claimed_surface="FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        cap_11_13_blocked = "CAPABILITY_11_13_SURFACE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_readiness_ratification_activation_v1(claimed_action="activate_ready")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    submit_blocked = False
    try:
        refuse_live_readiness_order_submit_v1(client_order_id="pt-coid-readiness-11-12")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        submit_blocked = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_live_readiness_network_session_v1(session_id="session-readiness-11-12")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        session_blocked = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    credential_blocked = False
    try:
        refuse_live_readiness_credential_access_v1(claimed_action="load_api_key")
    except FullyAutonomousLiveReadinessRatificationError as exc:
        credential_blocked = "CREDENTIAL_ACCESS_FORBIDDEN" in str(exc)

    # Synthetic all-green evaluation may report satisfied, but Cap 11.12 still
    # refuses claiming READY without a separate activation/evidence program.
    all_green = evaluate_fully_autonomous_live_readiness_v1(
        field_values={
            **{name: True for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS},
            **{name: False for name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS},
        }
    )
    all_green_ready_claim_blocked = False
    try:
        build_fully_autonomous_live_readiness_ratification_record_v1(
            field_values={
                **{name: True for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS},
                **{name: False for name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS},
            },
            ready_claimed=True,
        )
        # Even when evaluation is green, Cap 11.12 constant READY remains false;
        # allow record with ready_claimed only when evaluation satisfied — but
        # package still refuses package-level READY constant overclaim separately.
        all_green_ready_claim_blocked = False
    except FullyAutonomousLiveReadinessRatificationError:
        all_green_ready_claim_blocked = True

    ok = all(
        [
            record.source == "FIXTURE_ONLY",
            record.activated is False,
            record.readiness_evaluated is True,
            record.readiness_satisfied is False,
            record.ready_claimed is False,
            record.active_claimed is False,
            record.network_effect == "NONE",
            non_fixture_blocked,
            ready_overclaim_blocked,
            active_claim_blocked,
            refuse_ready_blocked,
            refuse_active_blocked,
            cap_11_13_blocked,
            activation_blocked,
            submit_blocked,
            session_blocked,
            credential_blocked,
            all_green["readiness_satisfied"] is True,
            all_green_ready_claim_blocked is False,
            FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_BOUND is True,
            FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_ACTIVATED is False,
            FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_FIXTURE_ONLY is True,
            CAPABILITY_11_12_STARTED is True,
            CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_STARTED is True,
            FULLY_AUTONOMOUS_LIVE_TRADING_READY is False,
            FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE is False,
            LIVE_AUTHORIZATION_VALID is False,
            OWNER_LIVE_GO is False,
            LIVE_ACTIVATION_CAPABILITY_PASS is False,
            CAPABILITY_11_13_STARTED is False,
            CAPABILITY_11_13_SEPARATE_OWNER_AUTHORIZED_LIVE_ACTIVATION_STARTED is False,
            record.owner == OWNER,
        ]
    )
    return {
        "ok": ok,
        "FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_BOUND": True,
        "FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_ACTIVATED": False,
        "FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_FIXTURE_ONLY": True,
        "CAPABILITY_11_12_STARTED": True,
        "CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_STARTED": True,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
        "LIVE_AUTHORIZATION_VALID": False,
        "OWNER_LIVE_GO": False,
        "LIVE_ACTIVATION_CAPABILITY_PASS": False,
        "CAPABILITY_11_13_STARTED": False,
        "CAPABILITY_11_13_SEPARATE_OWNER_AUTHORIZED_LIVE_ACTIVATION_STARTED": False,
        "readiness_satisfied": False,
        "missing_true_fields": list(record.missing_true_fields),
        "violated_false_fields": list(record.violated_false_fields),
        "forbidden_operating_fields": list(FINAL_AUTONOMOUS_LIVE_OPERATING_FORBIDDEN_FIELDS),
        "non_fixture_blocked": non_fixture_blocked,
        "ready_overclaim_blocked": ready_overclaim_blocked,
        "active_claim_blocked": active_claim_blocked,
        "refuse_ready_blocked": refuse_ready_blocked,
        "refuse_active_blocked": refuse_active_blocked,
        "cap_11_13_surface_blocked": cap_11_13_blocked,
        "activation_blocked": activation_blocked,
        "order_submit_blocked": submit_blocked,
        "network_session_blocked": session_blocked,
        "credential_access_blocked": credential_blocked,
        "synthetic_all_green_evaluation_satisfied": all_green["readiness_satisfied"] is True,
        "sample_ratification_session_id": record.ratification_session_id,
        "OWNER": FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_OWNER,
    }
