"""Traceability matrix: every ladder field and mandatory metric once."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_RUNBOOK_PATH,
    CANONICAL_SECTION_HEADING,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    LADDER_FIELDS,
    MANDATORY_LIVE_METRICS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

PACKAGE = "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1"
TESTS = "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_v1.py"
PERSIST_TESTS = "tests/ops/test_section_11_14_live_order_and_economic_evidence_ladder_persist_v1.py"
SPEC = "docs/ops/specs/SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1.md"


def _row(
    *,
    requirement: str,
    location: str,
    implementation: str,
    test_path: str,
    evidence: str,
    current_value: Any,
    epistemic_class: str,
    adjudication: str,
    unresolved: str,
) -> dict[str, Any]:
    return {
        "CANONICAL_REQUIREMENT": requirement,
        "CANONICAL_LOCATION": location,
        "IMPLEMENTATION_PATH": implementation,
        "TEST_PATH": test_path,
        "EVIDENCE_SCHEMA_OR_PATH": evidence,
        "CURRENT_VALUE": current_value,
        "EPISTEMIC_CLASS": epistemic_class,
        "ADJUDICATION": adjudication,
        "UNRESOLVED_DEPENDENCY": unresolved,
    }


def build_traceability_matrix_v1(
    *,
    ladder_values: Mapping[str, bool],
    metrics_schema: Mapping[str, Any],
) -> dict[str, Any]:
    location = f"{CANONICAL_RUNBOOK_PATH} {CANONICAL_SECTION_HEADING}"
    rows: list[dict[str, Any]] = []
    for field_name in LADDER_FIELDS:
        if field_name not in ladder_values:
            raise Section1114OfflineSurfaceError(f"TRACE_MISSING_LADDER_FIELD:{field_name}")
        unresolved = (
            EARLIEST_UNRESOLVED_DEPENDENCY
            if field_name == EARLIEST_UNRESOLVED_DEPENDENCY
            else f"BLOCKED_BY_{EARLIEST_UNRESOLVED_DEPENDENCY}"
        )
        rows.append(
            _row(
                requirement=field_name,
                location=location,
                implementation=f"{PACKAGE}/constants_v1.py",
                test_path=TESTS,
                evidence=f"{PACKAGE}/evidence_schema_v1.py",
                current_value=bool(ladder_values[field_name]),
                epistemic_class="3_ALREADY_ADJUDICATED_CONCLUSION",
                adjudication="FALSE_FAIL_CLOSED_OFFLINE_SURFACE",
                unresolved=unresolved,
            )
        )
    metric_names = list(metrics_schema.get("names") or [])
    if metric_names != list(MANDATORY_LIVE_METRICS):
        raise Section1114OfflineSurfaceError("TRACE_METRIC_NAME_MISMATCH")
    for metric_name in MANDATORY_LIVE_METRICS:
        rows.append(
            _row(
                requirement=metric_name,
                location=f"{location} mandatory Live metrics include",
                implementation=f"{PACKAGE}/metrics_schema_v1.py",
                test_path=TESTS,
                evidence=f"{PACKAGE}/metrics_schema_v1.py",
                current_value=None,
                epistemic_class="3_ALREADY_ADJUDICATED_CONCLUSION",
                adjudication="SCHEMA_BOUND_NOT_COLLECTED",
                unresolved="SEPARATE_OWNER_GO_FOR_LIVE_METRIC_COLLECTION",
            )
        )
    primary = [row["CANONICAL_REQUIREMENT"] for row in rows]
    expected = list(LADDER_FIELDS) + list(MANDATORY_LIVE_METRICS)
    if primary != expected:
        raise Section1114OfflineSurfaceError("TRACE_PRIMARY_ROW_ORDER_MISMATCH")
    if len(primary) != len(set(primary)):
        raise Section1114OfflineSurfaceError("TRACE_PRIMARY_ROW_DUPLICATE")
    return {
        "schema_version": "section_11_14_traceability.v1",
        "primary_row_count": len(rows),
        "ladder_field_count": len(LADDER_FIELDS),
        "mandatory_metric_count": len(MANDATORY_LIVE_METRICS),
        "persist_test_path": PERSIST_TESTS,
        "spec_path": SPEC,
        "rows": rows,
    }
