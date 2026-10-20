"""Read-only Execution GHV binding verifier. AUTHORITY=NONE. No repository writes."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_guardian_binding_verifier_v1.common_v1 import (
    assert_no_forbidden_keys_v1,
    authority_block_v1,
    bind_baseline_v1,
    contract_assessment_v1,
    direction_class_v1,
    lock_assignment_result_v1,
    registry_status_v1,
    reject_claims_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    TRAVERSABLE_CLASSES,
    WORKFLOW_EQUALS_GUARDIAN,
    WORKFLOW_PACKAGE_ID,
    frozen_edges_v1,
    frozen_open_tasks_v1,
)

SCHEMA_ID = "EXECUTION_GHV_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "EXECUTION_GHV"


def verify_execution_ghv_v1(
    *,
    current_sha: str,
    current_tree: str,
    registry: Mapping[str, Any] | None,
    boundary_contract_text: str | None = None,
    domain_source_text: str | None = None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    reject_claims_v1(claim_map, reasons)
    bind_baseline_v1(current_sha, current_tree, reasons)
    status = registry_status_v1(registry, reasons)
    contract_findings = contract_assessment_v1(boundary_contract_text, reasons)
    lock_source = lock_assignment_result_v1(domain_source_text)
    if lock_source == "MISSING_REQUIRED_EVIDENCE":
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    if lock_source == "CONTRACT_MISMATCH":
        reasons.append("CONTRACT_MISMATCH")
    edges = frozen_edges_v1() if status == "MATCH" else []
    forward = [
        _view(row)
        for row in edges
        if row["EDGE_CLASS"] in TRAVERSABLE_CLASSES
        and direction_class_v1(row["DIRECTION"]) == "FORWARD"
    ]
    reverse = [
        _view(row)
        for row in edges
        if row["EDGE_CLASS"] in TRAVERSABLE_CLASSES
        and direction_class_v1(row["DIRECTION"]) == "REVERSE"
    ]
    findings = [
        *contract_findings,
        {"CHECK": "PYTHON_LOCK_ENFORCEMENT", "RESULT": lock_source},
        {"CHECK": "REGISTRY_IS_SOURCE_PROOF", "RESULT": "FALSE"},
        {
            "CHECK": "OPEN_TASKS",
            "RESULT": "OPEN",
        },
        {"CHECK": "WORKFLOW_EQUALS_GUARDIAN", "RESULT": "FALSE"},
    ]
    report = {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "DOMAIN": "EXECUTION",
        **authority_block_v1(),
        "GHV_READY": False,
        "CURRENT_SHA": EXPECTED_BASELINE_SHA,
        "CURRENT_TREE": EXPECTED_BASELINE_TREE,
        "OBSERVED_SHA": current_sha,
        "OBSERVED_TREE": current_tree,
        "REGISTRY_STATUS": status,
        "REGISTRY_IS_SOURCE_PROOF": False,
        "VERIFICATION_STATUS": "REJECTED" if reasons else "REPORTED",
        "REJECTION_REASONS": list(dict.fromkeys(reasons)),
        "FINDINGS": findings,
        "FORWARD_EDGES": forward,
        "REVERSE_EDGES": reverse,
        "FORWARD_REVERSE_EVIDENCE_CLASS": "REGISTRY_CLASSIFICATION",
        "OPEN_TASKS": frozen_open_tasks_v1(),
        "WORKFLOW_PACKAGE_ID_NOT_USED_AS_GUARDIAN": WORKFLOW_PACKAGE_ID,
        "WORKFLOW_EQUALS_GUARDIAN": WORKFLOW_EQUALS_GUARDIAN,
        "TRAVERSAL_BEYOND_SUPPLIED_REGISTRY": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
    }
    assert_no_forbidden_keys_v1(report)
    return report


def _view(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "EDGE_ID": row["EDGE_ID"],
        "SOURCE": row["SOURCE"],
        "TARGET": row["TARGET"],
        "DIRECTION": row["DIRECTION"],
        "DIRECTION_CLASS": direction_class_v1(row["DIRECTION"]),
        "EDGE_CLASS": row["EDGE_CLASS"],
        "DOMAIN_OWNER": row["DOMAIN_OWNER"],
        "EVIDENCE_CLASS": "REGISTRY_CLASSIFICATION",
    }
