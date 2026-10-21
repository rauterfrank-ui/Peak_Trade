"""Pin-bound execution instrument enablement. Not productive runtime evidence."""

from __future__ import annotations

import ast
from pathlib import Path

from scripts.ops.execution_parent_instruments_v1.ghosv_v1 import run_execution_ghosv_disclosure_v1
from scripts.ops.execution_parent_instruments_v1.inventory_v1 import (
    FORWARD_ORIGIN,
    REVERSE_ORIGIN,
)
from scripts.ops.execution_parent_instruments_v1.readiness_v1 import derive_execution_readiness_v1
from scripts.ops.execution_parent_instruments_v1.run_v1 import run_execution_parent_toolchain_v1

_PACKAGE = Path("scripts/ops/execution_parent_instruments_v1")
_CHECK = "execution.telemetry_health.check_disk_usage"
_SIZE = "execution.telemetry_health.get_directory_size_mb"
_WRITERS = (
    "_write_wp1",
    "run_causal_integration_v1",
    "_write_provenance_manifest",
    "run_offline_graph_inspection_v1",
)
_FORBIDDEN = (
    "src.trading",
    "src.execution",
    "src.risk",
    "double_play",
    "execution_guardian_binding_verifier_v1",
    "ghosv_bounded_context_v1",
)


def test_toolchain_resolves_current_subjects_and_stays_read_only() -> None:
    result = run_execution_parent_toolchain_v1()

    assert result["status"] == "ACCEPTED"
    assert result["productive_runtime_evidence"] is False
    admission = result["admission"]
    assert admission["status"] == "ADMITTED"
    assert admission["membership_binding_status"] == "SCOPE_EMPTY"
    assert admission["domain_functional_members"] == []
    assert admission["current_validated"] is False
    assert "census" in admission["historical_sources"]
    observed = {item["subject_id"] for item in admission["observed_subjects"]}
    assert FORWARD_ORIGIN in observed
    assert _CHECK in observed
    assert _SIZE in observed
    ghv = result["ghv"]
    assert ghv["forward"]["reachable"] == [_CHECK]
    assert ghv["reverse"]["reachable"] == [_CHECK]
    assert ghv["transitive"]["reachable"] == [_CHECK, _SIZE]
    assert ghv["causal_closure_proven"] is False
    assert ghv["files_written"] is False
    assert any(edge["classification"] == "UNKNOWN" for edge in ghv["unknown_edges"])
    graph = result["graph"]
    assert graph["current_verified"] is False
    assert graph["writer_invoked"] is False
    assert graph["global_causal_closure_proven"] is False
    assert graph["forward"]["reachable"] == [_CHECK]
    assert graph["reverse"]["reachable"] == [_CHECK]
    assert graph["transitive"]["reachable"] == [_CHECK, _SIZE]
    assert all("37e51e3c7988026d2caa8c9a83ff46a056e416a8" in item for item in graph["node_ids"])
    again = run_execution_parent_toolchain_v1()
    assert again["graph"]["node_ids"] == graph["node_ids"]
    assert again["graph"]["edge_ids"] == graph["edge_ids"]
    ghosv = result["ghosv"]
    assert ghosv["findings_evaluated"] is True
    assert ghosv["safety_escalation_enabled"] is False
    assert ghosv["counts_as_proof"] is False
    readiness = result["readiness"]
    assert readiness["ADMISSION_READY"] is True
    assert readiness["GHV_READ_ONLY_READY"] is True
    assert readiness["GRAPH_READ_ONLY_READY"] is True
    assert readiness["GHOSV_READ_ONLY_READY"] is True
    assert readiness["TOOLCHAIN_READ_ONLY_READY"] is True
    assert readiness["CURRENT_VALIDATED"] is False
    assert readiness["CAUSAL_CLOSURE_PROVEN"] is False
    assert readiness["GUARDIAN_ACTIVE"] is False
    assert readiness["fixture_only"] is False
    assert readiness["productive_runtime_evidence"] is False


def test_ghosv_missing_evidence_is_rejected() -> None:
    result = run_execution_parent_toolchain_v1()
    rejected = run_execution_ghosv_disclosure_v1(
        admission=result["admission"],
        findings=[
            {
                "finding_id": "missing-ref",
                "category": "PRESENCE",
                "observed_state": "SYMBOL_PRESENT_IN_PINNED_TREE",
                "evidence_ref": "missing-ref",
                "affected_scope": FORWARD_ORIGIN,
                "status": "OBSERVED",
            }
        ],
        evidence_refs=["some-other-ref"],
    )

    assert rejected["status"] == "MISSING_EVIDENCE"
    assert rejected["findings_evaluated"] is False
    readiness = derive_execution_readiness_v1(
        admission=result["admission"],
        ghv=result["ghv"],
        graph=result["graph"],
        ghosv=rejected,
    )
    assert readiness["GHOSV_READ_ONLY_READY"] is False
    assert readiness["TOOLCHAIN_READ_ONLY_READY"] is False
    assert readiness["GUARDIAN_ACTIVE"] is False


def test_package_does_not_import_writers_or_trading() -> None:
    for path in sorted(_PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        for banned in _WRITERS:
            assert banned not in text
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        for name in imported:
            assert all(prefix not in name for prefix in _FORBIDDEN)
