"""Execution guardian gap projection. AUTHORITY=NONE. Readiness stays NOT_READY."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_guardian_binding_verifier_v1.common_v1 import (
    assert_no_forbidden_keys_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    COVERAGE,
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    TOOL_IDENTITIES,
    UNIVERSE_MEMBERSHIP,
)
from scripts.ops.execution_guardian_binding_verifier_v1.ghosv_track_v1 import (
    verify_execution_ghosv_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.ghv_track_v1 import (
    verify_execution_ghv_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.graph_track_v1 import (
    verify_execution_graph_v1,
)

SCHEMA_ID = "EXECUTION_GUARDIAN_GAP_PROJECTION_V1"


def project_execution_guardian_gap_v1(
    *,
    current_sha: str,
    current_tree: str,
    registry: Mapping[str, Any] | None,
    boundary_contract_text: str | None,
    workflow_constants_source: str | None,
    sources: Mapping[str, str] | None = None,
    anchors: list[Mapping[str, str]] | None = None,
    graph_artifact: Mapping[str, Any] | None = None,
    domain_source_text: str | None = None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ghv = verify_execution_ghv_v1(
        current_sha=current_sha,
        current_tree=current_tree,
        registry=registry,
        boundary_contract_text=boundary_contract_text,
        domain_source_text=domain_source_text,
        claims=claims,
    )
    graph = verify_execution_graph_v1(
        current_sha=current_sha,
        current_tree=current_tree,
        registry=registry,
        sources=sources,
        anchors=anchors,
        graph_artifact=graph_artifact,
        claims=claims,
    )
    ghosv = verify_execution_ghosv_v1(
        current_sha=current_sha,
        current_tree=current_tree,
        registry=registry,
        workflow_constants_source=workflow_constants_source,
        boundary_contract_text=boundary_contract_text,
        domain_source_text=domain_source_text,
        claims=claims,
    )
    binding = (
        "BOUND"
        if current_sha == EXPECTED_BASELINE_SHA and current_tree == EXPECTED_BASELINE_TREE
        else "MISMATCH"
    )
    source_results = [
        row["RESULT"]
        for row in ghv["FINDINGS"]
        if row["CHECK"]
        in {"COVERAGE", "UNIVERSE_MEMBERSHIP", "OWNER_LOCK", "POST_ALLOWED", "EXTERNAL_EFFECT"}
    ]
    if not source_results:
        source_status = "NOT_ASSESSED"
    elif any(result == "MISSING_REQUIRED_EVIDENCE" for result in source_results):
        source_status = "MISSING_REQUIRED_EVIDENCE"
    elif any(result == "CONTRACT_MISMATCH" for result in source_results):
        source_status = "CONTRACT_MISMATCH"
    elif all(result == "MATCH" for result in source_results):
        source_status = "MATCH"
    else:
        source_status = "NOT_ASSESSED"
    report = {
        "SCHEMA_ID": SCHEMA_ID,
        "AUTHORITY": "NONE",
        "GUARDIAN_AUTHORITY": "NONE",
        "TOOL_IMPLEMENTED": list(TOOL_IDENTITIES),
        "CURRENT_DOMAIN_BINDING": binding,
        "SOURCE_VERIFICATION": source_status,
        "GRAPH_ARTIFACT_BINDING": graph["GRAPH_ARTIFACT_BINDING"]["STATUS"],
        "DOMAIN_COVERAGE": COVERAGE,
        "UNIVERSE_MEMBERSHIP": UNIVERSE_MEMBERSHIP,
        "READINESS": "NOT_READY",
        "EXECUTION_GHV_READY": False,
        "EXECUTION_CURRENT_CAUSAL_GRAPH_READY": False,
        "EXECUTION_GHOSV_READY": False,
        "GHV_STATUS": ghv["VERIFICATION_STATUS"],
        "GRAPH_STATUS": graph["VERIFICATION_STATUS"],
        "GHOSV_STATUS": ghosv["VERIFICATION_STATUS"],
        "EXISTING_CHECKER_EXECUTED": False,
        "GRAPH_REBUILT": False,
        "PROJECTION_STATUS": (
            "REJECTED"
            if "REJECTED"
            in {
                ghv["VERIFICATION_STATUS"],
                graph["VERIFICATION_STATUS"],
                ghosv["VERIFICATION_STATUS"],
            }
            else "GAP_REPORTED"
        ),
    }
    assert_no_forbidden_keys_v1(report)
    return report
