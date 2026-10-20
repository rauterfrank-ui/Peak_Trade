"""Read-only Execution guardian GHOSV. AUTHORITY=NONE.

This identity is separate from GHOSV_BOUNDED_CONTEXT_V1.
"""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_guardian_binding_verifier_v1.common_v1 import (
    assert_no_forbidden_keys_v1,
    authority_block_v1,
    bind_baseline_v1,
    constant_assignments_v1,
    contract_assessment_v1,
    lock_assignment_result_v1,
    registry_status_v1,
    reject_claims_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    GUARDIAN_GHOSV_IDENTITY,
    REQUIREMENT_IDS,
    WORKFLOW_EQUALS_GUARDIAN,
    WORKFLOW_PACKAGE_ID,
    frozen_open_tasks_v1,
)

SCHEMA_ID = "EXECUTION_GHOSV_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "EXECUTION_GHOSV"
_WORKFLOW_NAMES = {"ADAPTER_MODE", "GHOSV_AUTHORITY", "PACKAGE_ID"}


def verify_execution_ghosv_v1(
    *,
    current_sha: str,
    current_tree: str,
    registry: Mapping[str, Any] | None,
    workflow_constants_source: str | None,
    boundary_contract_text: str | None = None,
    domain_source_text: str | None = None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    reject_claims_v1(claim_map, reasons)
    bind_baseline_v1(current_sha, current_tree, reasons)
    registry_state = registry_status_v1(registry, reasons)
    contract_findings = contract_assessment_v1(boundary_contract_text, reasons)
    lock_source = lock_assignment_result_v1(domain_source_text)
    if lock_source == "CONTRACT_MISMATCH":
        reasons.append("CONTRACT_MISMATCH")
    observed = constant_assignments_v1(workflow_constants_source, _WORKFLOW_NAMES)
    if observed is None:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        package_id = None
        workflow_authority = None
        adapter_mode = None
    else:
        package_id = observed.get("PACKAGE_ID")
        workflow_authority = observed.get("GHOSV_AUTHORITY")
        adapter_mode = observed.get("ADAPTER_MODE")
        if package_id != WORKFLOW_PACKAGE_ID:
            reasons.append("WORKFLOW_IDENTITY_MISMATCH")
        if package_id == GUARDIAN_GHOSV_IDENTITY:
            reasons.append("WORKFLOW_IDENTITY_COLLISION")
        if workflow_authority != "NONE":
            reasons.append("WORKFLOW_AUTHORITY_DRIFT")
    findings = [
        {
            "CHECK": "WORKFLOW_PACKAGE",
            "RESULT": "TOKEN_MATCH" if package_id == WORKFLOW_PACKAGE_ID else "UNKNOWN",
            "OBSERVED": package_id,
        },
        {
            "CHECK": "WORKFLOW_AUTHORITY",
            "RESULT": "TOKEN_MATCH" if workflow_authority == "NONE" else "UNKNOWN",
            "OBSERVED": workflow_authority,
        },
        {
            "CHECK": "ADAPTER_MODE",
            "RESULT": "TOKEN_MATCH" if adapter_mode == "DISABLED" else "OBSERVED",
            "OBSERVED": adapter_mode,
        },
        {"CHECK": "WORKFLOW_EQUALS_GUARDIAN", "RESULT": "FALSE"},
        {"CHECK": "AMPEL_IS_RELEASE", "RESULT": "FALSE"},
        {
            "CHECK": "OPEN_TASKS",
            "RESULT": "OPEN",
        },
        {"CHECK": "EXISTING_CHECKER_EXECUTED", "RESULT": "FALSE"},
    ]
    report = {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "DOMAIN": "EXECUTION",
        **authority_block_v1(),
        "GHOSV_READY": False,
        "GUARDIAN_AUTHORITY": "NONE",
        "EXISTING_CHECKER_EXECUTED": False,
        "GUARDIAN_IDENTITY": GUARDIAN_GHOSV_IDENTITY,
        "WORKFLOW_PACKAGE_ID": WORKFLOW_PACKAGE_ID,
        "WORKFLOW_EQUALS_GUARDIAN": WORKFLOW_EQUALS_GUARDIAN,
        "CURRENT_SHA": EXPECTED_BASELINE_SHA,
        "CURRENT_TREE": EXPECTED_BASELINE_TREE,
        "OBSERVED_SHA": current_sha,
        "OBSERVED_TREE": current_tree,
        "REGISTRY_STATUS": registry_state,
        "VERIFICATION_STATUS": "REJECTED" if reasons else "REPORTED",
        "REJECTION_REASONS": list(dict.fromkeys(reasons)),
        "FINDINGS": findings,
        "REQUIREMENTS": _requirements(contract_findings, lock_source),
        "OPEN_TASKS": frozen_open_tasks_v1(),
        "READ_ONLY": True,
        "FILE_WRITE_PERFORMED": False,
        "AUTOMATIC_RELEASE": False,
    }
    assert_no_forbidden_keys_v1(report)
    return report


def _requirements(
    contract_findings: list[dict[str, str]],
    lock_source: str,
) -> list[dict[str, str]]:
    by_check = {row["CHECK"]: row["RESULT"] for row in contract_findings}
    mapping = {
        "EX-COV": "COVERAGE",
        "EX-MEM": "UNIVERSE_MEMBERSHIP",
        "EX-LOCK": "OWNER_LOCK",
        "EX-POST": "POST_ALLOWED",
        "EX-EXT": "EXTERNAL_EFFECT",
    }
    rows: list[dict[str, str]] = []
    for requirement_id in REQUIREMENT_IDS:
        result = by_check.get(mapping[requirement_id], "NOT_ASSESSED")
        if requirement_id == "EX-LOCK" and lock_source == "CONTRACT_MISMATCH":
            result = "CONTRACT_MISMATCH"
        rows.append(
            {
                "REQUIREMENT_ID": requirement_id,
                "OBSERVATION_STATUS": result,
                "EVIDENCE_STATUS": "PARTIAL" if result == "MATCH" else "NOT_PROVEN",
                "EXISTING_CHECKER_STATUS": "NOT_TESTED",
                "AUTHORITY": "NONE",
            }
        )
    return rows
