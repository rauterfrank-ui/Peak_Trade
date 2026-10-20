"""Offline check-depth tests for the three Execution guardian tracks."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    STALE_FOREIGN_SNAPSHOT_ID,
    TOOL_IDENTITIES,
    frozen_registry_document_v1,
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
from scripts.ops.execution_guardian_binding_verifier_v1.projection_v1 import (
    project_execution_guardian_gap_v1,
)

PACKAGE = ROOT / "scripts/ops/execution_guardian_binding_verifier_v1"
SHA = EXPECTED_BASELINE_SHA
TREE = EXPECTED_BASELINE_TREE
WORKFLOW = (ROOT / "src/ops/ghosv_bounded_context_v1/constants_v1.py").read_text()
FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.risk",
    "src.governance",
    "src.ops.ghosv_bounded_context_v1",
    "trading",
)


def _registry() -> dict:
    return frozen_registry_document_v1()


def _contract(
    *,
    coverage: str = "PARTIAL",
    membership: str = "NOT_RATIFIED",
    post: str = "false",
    external: str = "false",
    sha: str = SHA,
    tree: str = TREE,
) -> str:
    return "\n".join(
        [
            f"EXECUTION_OUTER_BOUNDARY_COVERAGE={coverage}",
            f"EXECUTION_UNIVERSE_MEMBERSHIP={membership}",
            "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3",
            f"POST_ALLOWED={post}",
            f"EXTERNAL_EFFECT_AUTHORIZED={external}",
            f"CURRENT_CODE_PIN={sha}",
            f"CURRENT_TREE_PIN={tree}",
        ]
    )


def _artifact(
    snapshot: str = "supplied-observation",
    sha: str = SHA,
    tree: str = TREE,
) -> dict:
    return {
        "snapshot_id": snapshot,
        "authority": "NONE",
        "code_snapshot": {"git_head": sha, "tree": tree},
    }


def _sources() -> dict[str, str]:
    return {"halt.py": "def halt_before_wire():\n    return None\n"}


def _anchors() -> list[dict[str, str]]:
    return [{"EDGE_ID": "EX-11", "SOURCE_FILE": "halt.py", "SYMBOL": "halt_before_wire"}]


def _result(report: dict, check: str) -> str:
    return next(row["RESULT"] for row in report["FINDINGS"] if row["CHECK"] == check)


def test_valid_current_evidence_keeps_ready_false() -> None:
    registry = _registry()
    ghv = verify_execution_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=registry,
        boundary_contract_text=_contract(),
    )
    graph = verify_execution_graph_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=registry,
        sources=_sources(),
        anchors=_anchors(),
        graph_artifact=_artifact(),
    )
    ghosv = verify_execution_ghosv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=registry,
        workflow_constants_source=WORKFLOW,
        boundary_contract_text=_contract(),
    )
    assert (ghv["TOOL_IDENTITY"], graph["TOOL_IDENTITY"], ghosv["TOOL_IDENTITY"]) == TOOL_IDENTITIES
    assert ghv["VERIFICATION_STATUS"] == "REPORTED"
    assert graph["VERIFICATION_STATUS"] == "REPORTED"
    assert ghosv["VERIFICATION_STATUS"] == "REPORTED"
    assert ghv["GHV_READY"] is False
    assert graph["GRAPH_READY"] is False
    assert ghosv["GHOSV_READY"] is False
    assert ghv["REGISTRY_IS_SOURCE_PROOF"] is False
    assert _result(ghv, "COVERAGE") == "MATCH"
    assert _result(ghv, "UNIVERSE_MEMBERSHIP") == "MATCH"
    assert _result(ghv, "OWNER_LOCK") == "MATCH"
    assert _result(ghv, "POST_ALLOWED") == "MATCH"
    assert _result(ghv, "EXTERNAL_EFFECT") == "MATCH"
    assert _result(ghv, "PIN") == "MATCH"
    assert _result(ghv, "PYTHON_LOCK_ENFORCEMENT") == "NOT_ASSESSED"
    anchored = next(row for row in graph["EDGES"] if row["EDGE_ID"] == "EX-11")
    assert anchored["SOURCE_ANCHOR"] == "MATCH"
    assert anchored["LINE"] == 1
    assert anchored["PROVENANCE"]["SOURCE_FILE"] == "halt.py"
    assert graph["GRAPH_ARTIFACT_BINDING"]["SNAPSHOT_IS_CURRENT_MATERIALIZATION"] is False
    assert graph["GRAPH_REBUILT"] is False
    assert graph["TRAVERSAL_EXECUTED"] is False
    assert ghosv["EXISTING_CHECKER_EXECUTED"] is False
    assert ghosv["GUARDIAN_AUTHORITY"] == "NONE"
    assert ghosv["WORKFLOW_EQUALS_GUARDIAN"] is False
    assert {row["STATUS"] for row in ghosv["OPEN_TASKS"]} == {"OPEN"}
    assert len(ghosv["REQUIREMENTS"]) == 5
    projection = project_execution_guardian_gap_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=registry,
        boundary_contract_text=_contract(),
        workflow_constants_source=WORKFLOW,
        sources=_sources(),
        anchors=_anchors(),
        graph_artifact=_artifact(),
    )
    assert projection["TOOL_IMPLEMENTED"] == list(TOOL_IDENTITIES)
    assert projection["CURRENT_DOMAIN_BINDING"] == "BOUND"
    assert projection["SOURCE_VERIFICATION"] == "MATCH"
    assert projection["GRAPH_ARTIFACT_BINDING"] == "RECORDED_NOT_MATERIALIZED"
    assert projection["DOMAIN_COVERAGE"] == "PARTIAL"
    assert projection["READINESS"] == "NOT_READY"


def test_missing_evidence_rejects() -> None:
    ghv = verify_execution_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=None,
        boundary_contract_text=None,
    )
    assert ghv["VERIFICATION_STATUS"] == "REJECTED"
    assert "MISSING_REQUIRED_EVIDENCE" in ghv["REJECTION_REASONS"]
    assert _result(ghv, "COVERAGE") == "MISSING_REQUIRED_EVIDENCE"
    assert ghv["GHV_READY"] is False
    graph = verify_execution_graph_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        graph_artifact=None,
    )
    assert graph["GRAPH_ARTIFACT_BINDING"]["STATUS"] == "MISSING_REQUIRED_EVIDENCE"


def test_wrong_sha_rejects() -> None:
    report = verify_execution_ghv_v1(
        current_sha="0" * 40,
        current_tree=TREE,
        registry=_registry(),
        boundary_contract_text=_contract(),
    )
    assert "BASELINE_SHA_MISMATCH" in report["REJECTION_REASONS"]
    assert report["GHV_READY"] is False


def test_wrong_tree_rejects() -> None:
    report = verify_execution_graph_v1(
        current_sha=SHA,
        current_tree="0" * 40,
        registry=_registry(),
        graph_artifact=_artifact(),
    )
    assert "BASELINE_TREE_MISMATCH" in report["REJECTION_REASONS"]
    assert report["GRAPH_READY"] is False


def test_contract_mismatch_and_pin_drift() -> None:
    mismatched = verify_execution_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        boundary_contract_text=_contract(coverage="COMPLETE"),
    )
    assert "CONTRACT_MISMATCH" in mismatched["REJECTION_REASONS"]
    assert _result(mismatched, "COVERAGE") == "CONTRACT_MISMATCH"
    drifted = verify_execution_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        boundary_contract_text=_contract(sha="1" * 40),
    )
    assert "PIN_DRIFT" in drifted["REJECTION_REASONS"]
    assert _result(drifted, "PIN") == "PIN_DRIFT"
    assert drifted["REGISTRY_IS_SOURCE_PROOF"] is False


def test_missing_source_anchor_is_not_assessed() -> None:
    graph = verify_execution_graph_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        sources=None,
        anchors=None,
        graph_artifact=_artifact(),
    )
    assert graph["VERIFICATION_STATUS"] == "REPORTED"
    assert {row["SOURCE_ANCHOR"] for row in graph["EDGES"]} == {"NOT_ASSESSED"}
    assert graph["GLOBAL_CAUSAL_CLOSURE_PROVEN"] is False


def test_foreign_snapshot_rejects() -> None:
    graph = verify_execution_graph_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        graph_artifact=_artifact(snapshot=STALE_FOREIGN_SNAPSHOT_ID),
    )
    assert "SNAPSHOT_ID_MISMATCH" in graph["REJECTION_REASONS"]
    assert graph["GRAPH_ARTIFACT_BINDING"]["SNAPSHOT_IS_CURRENT_MATERIALIZATION"] is False
    assert graph["GRAPH_READY"] is False
    assert graph["GRAPH_REBUILT"] is False


def test_registry_drift_is_not_source_proof() -> None:
    drifted = _registry()
    drifted["UNIVERSE_MEMBERSHIP"] = "RATIFIED"
    ghv = verify_execution_ghv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=drifted,
        boundary_contract_text=_contract(),
    )
    assert "REGISTRY_DRIFT" in ghv["REJECTION_REASONS"]
    assert ghv["REGISTRY_IS_SOURCE_PROOF"] is False
    assert ghv["UNIVERSE_RATIFIED"] is False
    assert _result(ghv, "UNIVERSE_MEMBERSHIP") == "MATCH"


def test_workflow_guardian_collision_rejects() -> None:
    collided = WORKFLOW.replace(
        'PACKAGE_ID = "GHOSV_BOUNDED_CONTEXT_V1"',
        'PACKAGE_ID = "EXECUTION_GHOSV"',
    )
    report = verify_execution_ghosv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        workflow_constants_source=collided,
        boundary_contract_text=_contract(),
    )
    assert "WORKFLOW_IDENTITY_COLLISION" in report["REJECTION_REASONS"]
    assert report["WORKFLOW_EQUALS_GUARDIAN"] is False
    assert report["GHOSV_READY"] is False
    separated = verify_execution_ghosv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        workflow_constants_source=WORKFLOW,
        boundary_contract_text=_contract(),
    )
    assert separated["WORKFLOW_PACKAGE_ID"] == "GHOSV_BOUNDED_CONTEXT_V1"
    assert separated["TOOL_IDENTITY"] == "EXECUTION_GHOSV"


def test_unauthorized_authority_claim_rejects() -> None:
    report = verify_execution_ghosv_v1(
        current_sha=SHA,
        current_tree=TREE,
        registry=_registry(),
        workflow_constants_source=WORKFLOW,
        boundary_contract_text=_contract(),
        claims={"authority": "OWNER", "overall_pass": True, "post_allowed": True},
    )
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "UNAUTHORIZED_AUTHORITY_CLAIM" in report["REJECTION_REASONS"]
    assert "OVERALL_PASS_FORBIDDEN" in report["REJECTION_REASONS"]
    assert "EXTERNAL_EFFECT_CLAIM" in report["REJECTION_REASONS"]
    assert report["TRADING_AUTHORITY"] == "NONE"
    assert report["POST_ALLOWED"] is False
    assert report["EXTERNAL_EFFECT_PERFORMED"] is False
    assert "overall_pass" not in report


def test_reports_are_reproducible_and_do_not_import_protected_code() -> None:
    kwargs = {
        "current_sha": SHA,
        "current_tree": TREE,
        "registry": _registry(),
        "boundary_contract_text": _contract(),
    }
    assert verify_execution_ghv_v1(**kwargs) == verify_execution_ghv_v1(**kwargs)
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(FORBIDDEN_IMPORT_PREFIXES)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES)
