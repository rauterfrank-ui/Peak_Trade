"""Autonomy closure standard field contracts (§11.17) — bound, never proven-overclaimed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (
    AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS,
    AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS,
    AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_ACTIVATED,
    AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_BOUND,
    AUTONOMY_CLOSURE_STANDARD_FIELD_OWNER,
    AUTONOMY_CLOSURE_STANDARD_FIELDS,
    CANONICAL_STATEFUL_CORE_PROVEN,
    CONTRACT_VERSION,
    CORE_LOGIC_PARITY_ACROSS_MODES,
    LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN,
    LIVE_AUTONOMOUS_DEGRADATION_PROVEN,
    LIVE_AUTONOMOUS_RECOVERY_PROVEN,
    LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN,
    LIVE_EVIDENCE_VERIFIED,
    LIVE_KILL_SWITCH_PROVEN,
    LIVE_ORDER_LIFECYCLE_PROVEN,
    LIVE_PARTIAL_FILL_RECOVERY_PROVEN,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_RECONCILIATION_PROVEN,
    LIVE_RESTART_PROVEN,
    LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    OWNER,
    OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION,
    OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE,
    SIMULATED_LIFECYCLE_PROVEN,
    TESTNET_LIFECYCLE_PROVEN,
)
from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.binding_v1 import (
    bind_canonical_stateful_core_proven_from_cap72_v1,
)

# Bound from Cap 7.2 via §11.17 package; remaining evidence residuals stay unset.
_SECTION_11_17_BOUND_TRUE_FIELDS: frozenset[str] = frozenset({"CANONICAL_STATEFUL_CORE_PROVEN"})
_SECTION_11_17_POLICY_TRUE_FIELDS: frozenset[str] = frozenset(
    {
        "OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE",
        "CORE_LOGIC_PARITY_ACROSS_MODES",
    }
)
_CANONICAL_CORE_SOURCE = "EXISTING_EVIDENCE_BINDING_CAP72_SECTION_11_17"


class AutonomyClosureStandardFieldError(RuntimeError):
    """Fail-closed autonomy closure standard field violation."""


@dataclass(frozen=True)
class AutonomyClosureStandardFieldRecordV1:
    field_name: str
    contract_bound: bool
    proven_claimed: bool
    expected_for_ready: bool
    current_value: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = AUTONOMY_CLOSURE_STANDARD_FIELD_OWNER


_CURRENT_FIELD_VALUES: dict[str, bool] = {
    "CANONICAL_STATEFUL_CORE_PROVEN": CANONICAL_STATEFUL_CORE_PROVEN,
    "SIMULATED_LIFECYCLE_PROVEN": SIMULATED_LIFECYCLE_PROVEN,
    "TESTNET_LIFECYCLE_PROVEN": TESTNET_LIFECYCLE_PROVEN,
    "LIVE_PRIVATE_READ_ONLY_PROVEN": LIVE_PRIVATE_READ_ONLY_PROVEN,
    "LIVE_ORDER_LIFECYCLE_PROVEN": LIVE_ORDER_LIFECYCLE_PROVEN,
    "LIVE_RECONCILIATION_PROVEN": LIVE_RECONCILIATION_PROVEN,
    "LIVE_RESTART_PROVEN": LIVE_RESTART_PROVEN,
    "LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN": LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
    "LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN": LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN,
    "LIVE_PARTIAL_FILL_RECOVERY_PROVEN": LIVE_PARTIAL_FILL_RECOVERY_PROVEN,
    "LIVE_KILL_SWITCH_PROVEN": LIVE_KILL_SWITCH_PROVEN,
    "LIVE_AUTONOMOUS_DEGRADATION_PROVEN": LIVE_AUTONOMOUS_DEGRADATION_PROVEN,
    "LIVE_AUTONOMOUS_RECOVERY_PROVEN": LIVE_AUTONOMOUS_RECOVERY_PROVEN,
    "LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN": LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN,
    "LIVE_EVIDENCE_VERIFIED": LIVE_EVIDENCE_VERIFIED,
    "OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE": (
        OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE
    ),
    "CORE_LOGIC_PARITY_ACROSS_MODES": CORE_LOGIC_PARITY_ACROSS_MODES,
    "OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION": (
        OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION
    ),
    "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
}


def _expected_for_ready(field_name: str) -> bool:
    if field_name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS:
        return True
    if field_name in AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS:
        return False
    if field_name == "FULLY_AUTONOMOUS_LIVE_TRADING_READY":
        return True
    raise AutonomyClosureStandardFieldError(f"UNKNOWN_AUTONOMY_CLOSURE_FIELD:{field_name}")


def build_autonomy_closure_standard_field_record_v1(
    *, field_name: str
) -> AutonomyClosureStandardFieldRecordV1:
    if field_name not in AUTONOMY_CLOSURE_STANDARD_FIELDS:
        raise AutonomyClosureStandardFieldError(f"UNKNOWN_AUTONOMY_CLOSURE_FIELD:{field_name}")
    source = (
        _CANONICAL_CORE_SOURCE if field_name in _SECTION_11_17_BOUND_TRUE_FIELDS else "FIXTURE_ONLY"
    )
    return AutonomyClosureStandardFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        proven_claimed=False,
        expected_for_ready=_expected_for_ready(field_name),
        current_value=bool(_CURRENT_FIELD_VALUES[field_name]),
        source=source,
    )


def refuse_autonomy_closure_proven_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in AUTONOMY_CLOSURE_STANDARD_FIELDS:
        raise AutonomyClosureStandardFieldError(f"UNKNOWN_AUTONOMY_CLOSURE_FIELD:{field_name}")
    raise AutonomyClosureStandardFieldError(
        f"AUTONOMY_CLOSURE_PROVEN_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_12:{field_name}"
    )


def refuse_autonomy_closure_field_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise AutonomyClosureStandardFieldError(
        f"AUTONOMY_CLOSURE_STANDARD_FIELD_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_12:{claimed_action}"
    )


def prove_autonomy_closure_standard_field_contract_v1() -> dict[str, Any]:
    records: dict[str, AutonomyClosureStandardFieldRecordV1] = {}
    for field_name in AUTONOMY_CLOSURE_STANDARD_FIELDS:
        records[field_name] = build_autonomy_closure_standard_field_record_v1(field_name=field_name)

    unknown_blocked = False
    try:
        build_autonomy_closure_standard_field_record_v1(
            field_name="LIVE_END_TO_END_EVIDENCE_PROVEN"
        )
    except AutonomyClosureStandardFieldError as exc:
        unknown_blocked = "UNKNOWN_AUTONOMY_CLOSURE_FIELD" in str(exc)

    proven_overclaim_blocked = False
    try:
        refuse_autonomy_closure_proven_overclaim_v1(field_name="LIVE_ORDER_LIFECYCLE_PROVEN")
    except AutonomyClosureStandardFieldError as exc:
        proven_overclaim_blocked = "PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_autonomy_closure_field_activation_v1(claimed_action="mark_proven")
    except AutonomyClosureStandardFieldError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    all_unclaimed = all(
        r.contract_bound is True and r.proven_claimed is False for r in records.values()
    )
    # Cap 11.12 consumes only CANONICAL_STATEFUL_CORE_PROVEN from §11.17/Cap-7.2 binding.
    # Remaining evidence-proven residuals stay false; policy fields do not unlock READY.
    evidence_residuals_unset = all(
        records[name].current_value is False
        for name in AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS
        if name not in (_SECTION_11_17_BOUND_TRUE_FIELDS | _SECTION_11_17_POLICY_TRUE_FIELDS)
    )
    canonical_core_bound = (
        records["CANONICAL_STATEFUL_CORE_PROVEN"].current_value is True
        and records["CANONICAL_STATEFUL_CORE_PROVEN"].source == _CANONICAL_CORE_SOURCE
        and CANONICAL_STATEFUL_CORE_PROVEN is True
    )
    core_binding = bind_canonical_stateful_core_proven_from_cap72_v1()
    core_binding_ok = (
        core_binding.get("ok") is True
        and core_binding.get("CANONICAL_STATEFUL_CORE_PROVEN") is True
        and core_binding.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is False
        and core_binding.get("FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE") is False
        and core_binding.get("SIMULATED_LIFECYCLE_PROVEN") is False
        and core_binding.get("FIXTURE_ONLY") is False
    )
    prerequisite_not_met = all(
        [
            evidence_residuals_unset,
            canonical_core_bound,
            core_binding_ok,
            records["OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION"].current_value is True,
            records["OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE"].current_value is True,
            records["CORE_LOGIC_PARITY_ACROSS_MODES"].current_value is True,
            records["FULLY_AUTONOMOUS_LIVE_TRADING_READY"].current_value is False,
        ]
    )

    ok = all(
        [
            all_unclaimed,
            unknown_blocked,
            proven_overclaim_blocked,
            activation_blocked,
            prerequisite_not_met,
            AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_BOUND is True,
            AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_ACTIVATED is False,
            CANONICAL_STATEFUL_CORE_PROVEN is True,
            SIMULATED_LIFECYCLE_PROVEN is False,
            TESTNET_LIFECYCLE_PROVEN is False,
            LIVE_PRIVATE_READ_ONLY_PROVEN is False,
            LIVE_ORDER_LIFECYCLE_PROVEN is False,
            LIVE_RECONCILIATION_PROVEN is False,
            LIVE_RESTART_PROVEN is False,
            LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN is False,
            LIVE_PARTIAL_FILL_RECOVERY_PROVEN is False,
            LIVE_KILL_SWITCH_PROVEN is False,
            LIVE_AUTONOMOUS_DEGRADATION_PROVEN is False,
            LIVE_AUTONOMOUS_RECOVERY_PROVEN is False,
            LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN is False,
            LIVE_EVIDENCE_VERIFIED is False,
            OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION is True,
            OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE is True,
            CORE_LOGIC_PARITY_ACROSS_MODES is True,
            records["FULLY_AUTONOMOUS_LIVE_TRADING_READY"].current_value is False,
        ]
    )
    return {
        "ok": ok,
        "AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_BOUND": True,
        "AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_ACTIVATED": False,
        "CANONICAL_STATEFUL_CORE_PROVEN": True,
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
        "OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION": True,
        "OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE": True,
        "CORE_LOGIC_PARITY_ACROSS_MODES": True,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "fields": list(AUTONOMY_CLOSURE_STANDARD_FIELDS),
        "required_true_fields": list(AUTONOMY_CLOSURE_REQUIRED_TRUE_FIELDS),
        "required_false_fields": list(AUTONOMY_CLOSURE_REQUIRED_FALSE_FIELDS),
        "unknown_field_blocked": unknown_blocked,
        "proven_overclaim_blocked": proven_overclaim_blocked,
        "activation_blocked": activation_blocked,
        "prerequisites_not_met_for_ready": prerequisite_not_met,
        "SECTION_11_17_CANONICAL_STATEFUL_CORE_CONSUMED": True,
        "OWNER": OWNER,
    }
