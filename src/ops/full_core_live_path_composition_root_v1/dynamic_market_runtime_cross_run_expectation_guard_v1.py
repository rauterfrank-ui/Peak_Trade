"""Guardrails: runtime-dependent values must not become cross-run Golden expectations.

AUTHORITY=NONE — evidence-contract surface only; no trading semantics.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

OWNER = (
    "full_core_live_path_composition_root_v1.dynamic_market_runtime_cross_run_expectation_guard_v1"
)

# Fields whose concrete absolute values are runtime-discovered (non-exhaustive SSOT for guard).
RUNTIME_DEPENDENT_FIELD_NAMES_V1: frozenset[str] = frozenset(
    {
        "selected_instrument",
        "bound_instrument",
        "instrument_id",
        "venue_native_id",
        "reference_price",
        "mark_price",
        "bid",
        "ask",
        "available_capital",
        "remaining_capital",
        "total_capital_limit",
        "candidate_quantity_upper_bound",
        "final_quantity",
        "requested_quantity",
        "min_quantity",
        "min_notional",
        "minSz",
        "tick_size",
        "lot_size",
        "contract_value",
        "protective_stop_price",
        "policy_outcome",
        "outcome",
        "sizing_reason_code",
        "PRE_EXTERNAL_REACHED",
    }
)

TRANSITIVE_TAINT_ROOT_FIELDS_V1: frozenset[str] = frozenset(
    {
        "selected_instrument",
        "reference_price",
        "mark_price",
        "available_capital",
        "contract_spec",
        "account_state",
    }
)

TRANSITIVE_TAINT_DERIVED_FIELDS_V1: frozenset[str] = frozenset(
    {
        "candidate_quantity_upper_bound",
        "final_quantity",
        "protective_stop_context",
        "policy_outcome",
        "outcome",
        "venue_plan_values",
    }
)

FORBIDDEN_CROSS_RUN_EXPECTATION_KEYS_V1: frozenset[str] = frozenset(
    {
        "expected_cross_run_value",
        "golden_expected_value",
        "cross_run_expected_value",
        "universal_expected_value",
        "expected_value",
        "EXPECTED_VALUE",
        "ACTUAL_VALUE",
    }
)

STABLE_EVIDENCE_CRITERIA_V1: tuple[str, ...] = (
    "SINGLE_SELECTION_IDENTITY_RULE",
    "SELECTION_OWNS_SELECTION_BINDING_CONSUMES",
    "BINDING_DOES_NOT_INDEPENDENTLY_SELECT",
    "DOWNSTREAM_CONTEXT_MATCHES_BOUND_INSTRUMENT",
    "DECISION_SIDE_PROPAGATES_WITHIN_RUN",
    "SIZING_CONSUMES_CURRENT_BOUND_CONTEXT",
    "POLICY_REJECTION_ATTRIBUTABLE_WHEN_EVIDENCE_PRESENT",
    "UNKNOWN_REMAINS_UNKNOWN",
    "PRE_EXTERNAL_TERMINAL_BOUNDARY",
    "POST_AUTHORITY_CLOSED_UNLESS_INDEPENDENTLY_AUTHORIZED",
    "MAX_POSITIONS_WHERE_CANONICALLY_APPLICABLE",
)

FORBIDDEN_STABLE_CRITERIA_PATTERNS_V1: tuple[str, ...] = (
    "instrument==",
    "mark==",
    "minQty==",
    "capital==",
    "quantity==",
    "stop==",
    "same policy outcome as prior run",
)


class CrossRunGoldenExpectationGuardError(ValueError):
    """Raised when evidence contract encodes forbidden cross-run absolute expectations."""


def context_identity_for_observation_v1(
    *,
    selected_instrument: str,
    observed_instrument_id: str,
    run_id: str,
) -> str:
    inst = str(observed_instrument_id or selected_instrument or "").strip()
    rid = str(run_id or "").strip()
    if inst and rid:
        return f"{inst}@{rid}"
    return inst or rid or "UNKNOWN_CURRENT"


def assert_no_cross_run_golden_expectation_keys_v1(payload: Mapping[str, Any]) -> None:
    """Fail closed if forbidden cross-run expectation keys appear anywhere in a contract tree."""

    def _walk(obj: Any, path: str) -> None:
        if isinstance(obj, Mapping):
            for key, val in obj.items():
                key_s = str(key)
                if key_s in FORBIDDEN_CROSS_RUN_EXPECTATION_KEYS_V1:
                    raise CrossRunGoldenExpectationGuardError(
                        f"forbidden cross-run expectation key at {path}.{key_s}"
                    )
                if key_s == "cross_run_expectation" and val is True:
                    raise CrossRunGoldenExpectationGuardError(
                        f"cross_run_expectation=true at {path}.{key_s}"
                    )
                _walk(val, f"{path}.{key_s}")
        elif isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            for idx, item in enumerate(obj):
                _walk(item, f"{path}[{idx}]")

    _walk(payload, "root")


def validate_runtime_discovered_observation_row_v1(row: Mapping[str, Any]) -> None:
    if row.get("cross_run_expectation") is True:
        raise CrossRunGoldenExpectationGuardError(
            "runtime observation has cross_run_expectation=true"
        )
    field = str(row.get("field_name") or "")
    if field in RUNTIME_DEPENDENT_FIELD_NAMES_V1 and row.get("cross_run_expectation") is not False:
        if row.get("cross_run_expectation") not in (False, None):
            raise CrossRunGoldenExpectationGuardError(
                f"runtime field {field} missing cross_run_expectation=false"
            )


def validate_dynamic_market_evidence_contract_v1(contract: Mapping[str, Any]) -> None:
    assert_no_cross_run_golden_expectation_keys_v1(contract)
    sem = contract.get("runtime_evidence_semantics")
    if isinstance(sem, Mapping):
        if sem.get("CROSS_RUN_ABSOLUTE_VALUE_COMPARISON_AUTHORIZED") is True:
            raise CrossRunGoldenExpectationGuardError(
                "CROSS_RUN_ABSOLUTE_VALUE_COMPARISON_AUTHORIZED must not be true"
            )
    for row in contract.get("dynamic_value_observations") or ():
        if isinstance(row, Mapping):
            validate_runtime_discovered_observation_row_v1(row)


def transitive_dynamic_taint_metadata_v1() -> dict[str, Any]:
    return {
        "rule": (
            "IF value depends on RUNTIME_DISCOVERED_VALUE, concrete absolute is runtime-dependent "
            "unless proven otherwise by canonical invariant"
        ),
        "root_fields": sorted(TRANSITIVE_TAINT_ROOT_FIELDS_V1),
        "derived_fields": sorted(TRANSITIVE_TAINT_DERIVED_FIELDS_V1),
        "algorithm_may_be_stable_concrete_result_may_be_dynamic": True,
    }


def runtime_evidence_semantics_block_v1() -> dict[str, Any]:
    return {
        "RUNTIME_VALUE_NOT_CROSS_RUN_EXPECTATION": True,
        "CROSS_RUN_ABSOLUTE_VALUE_COMPARISON_AUTHORIZED": False,
        "DYNAMIC_VALUE_CHANGE_IS_SYSTEM_DRIFT": False,
        "POLICY_ALGORITHM_CAN_BE_STABLE": True,
        "POLICY_OUTCOME_CAN_BE_DYNAMIC": True,
        "PRE_EXTERNAL_FALSE_NOT_RELATIONAL_FAILURE": True,
        "DETERMINISTIC_OFFLINE_FIXTURE_EXPECTATION": (
            "Absolute values permitted only in offline deterministic fixtures/tests; "
            "not imported as Product cross-run expectations"
        ),
        "PRODUCT_RUNTIME_RELATIONAL_EXPECTATION": (
            "Product GHV proves same-run relations and stable criteria; not historical absolute values"
        ),
        "stable_evidence_criteria_v1": list(STABLE_EVIDENCE_CRITERIA_V1),
        "forbidden_stable_criteria_patterns_v1": list(FORBIDDEN_STABLE_CRITERIA_PATTERNS_V1),
        "transitive_runtime_taint_v1": transitive_dynamic_taint_metadata_v1(),
    }


__all__ = [
    "CrossRunGoldenExpectationGuardError",
    "FORBIDDEN_CROSS_RUN_EXPECTATION_KEYS_V1",
    "OWNER",
    "RUNTIME_DEPENDENT_FIELD_NAMES_V1",
    "STABLE_EVIDENCE_CRITERIA_V1",
    "assert_no_cross_run_golden_expectation_keys_v1",
    "context_identity_for_observation_v1",
    "runtime_evidence_semantics_block_v1",
    "transitive_dynamic_taint_metadata_v1",
    "validate_dynamic_market_evidence_contract_v1",
    "validate_runtime_discovered_observation_row_v1",
]
