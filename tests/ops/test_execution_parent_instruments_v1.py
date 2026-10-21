"""Pin-bound execution instrument enablement. Not productive runtime evidence."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from scripts.ops.execution_parent_instruments_v1.ghosv_v1 import run_execution_ghosv_disclosure_v1
from scripts.ops.execution_parent_instruments_v1.graph_v1 import run_execution_graph_memory_v1
from scripts.ops.execution_parent_instruments_v1.ghv_v1 import run_execution_ghv_disclosure_v1
from scripts.ops.execution_parent_instruments_v1.inventory_v1 import (
    FORWARD_ORIGIN,
    UNKNOWN_EDGES,
)
from scripts.ops.execution_parent_instruments_v1.readiness_v1 import derive_execution_readiness_v1
from scripts.ops.execution_parent_instruments_v1.run_v1 import run_execution_parent_toolchain_v1
from scripts.ops.execution_parent_instruments_v1 import verify_v1

_CURRENT_COMMIT = "4f41e55c911b663097b092be4fce2dfc630671f3"
_CURRENT_TREE = "0f999ff806d64232432bbe1613dc2977a56df830"
_OTHER_COMMIT = "37e51e3c7988026d2caa8c9a83ff46a056e416a8"
_OTHER_TREE = "4619907408f709ba6781377b853d7efb682bc49d"
_REPLAY = "execution.boundary.trading_replay"
_SUBMISSION_UNKNOWN = "execution.decision.runtime_cycle.edge.submission.unknown"
_PACKAGES = (
    Path("scripts/ops/execution_parent_instruments_v1"),
    Path("scripts/ops/execution_parent_disclosure_v1"),
)
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
_SHA40 = re.compile(r"\b[0-9a-f]{40}\b")


def _run(**overrides: str) -> dict[str, object]:
    payload = {
        "current_commit_sha": _CURRENT_COMMIT,
        "current_tree_sha": _CURRENT_TREE,
        "baseline_currency": "CURRENT",
    }
    payload.update(overrides)
    return run_execution_parent_toolchain_v1(**payload)


def test_toolchain_resolves_current_subjects_and_stays_read_only() -> None:
    result = _run()

    assert result["status"] == "ACCEPTED"
    assert result["productive_runtime_evidence"] is False
    admission = result["admission"]
    assert admission["status"] == "ADMITTED"
    assert admission["baseline_commit"] == _CURRENT_COMMIT
    assert admission["baseline_tree"] == _CURRENT_TREE
    assert admission["membership_binding_status"] == "SCOPE_EMPTY"
    assert admission["domain_functional_members"] == []
    assert admission["current_validated"] is False
    assert "census" in admission["historical_sources"]
    observed = {item["subject_id"] for item in admission["observed_subjects"]}
    assert FORWARD_ORIGIN in observed
    assert _REPLAY in observed
    ghv = result["ghv"]
    assert ghv["instrument_id"] == "PARENT_EXECUTION_GHV"
    assert ghv["forward"]["reachable"] == [_REPLAY]
    assert ghv["reverse"]["reachable"] == [FORWARD_ORIGIN]
    assert ghv["transitive"]["reachable"] == [_REPLAY]
    assert ghv["coverage_status"] == "PARTIAL"
    assert ghv["causal_closure_proven"] is False
    assert ghv["files_written"] is False
    assert any(edge["edge_id"] == _SUBMISSION_UNKNOWN for edge in ghv["unknown_edges"])
    graph = result["graph"]
    assert graph["instrument_id"] == "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH"
    assert graph["coverage_status"] == "PARTIAL"
    assert graph["current_verified"] is False
    assert graph["writer_invoked"] is False
    assert graph["global_causal_closure_proven"] is False
    assert graph["forward"]["reachable"] == [_REPLAY]
    assert all(_CURRENT_COMMIT in item for item in graph["node_ids"])
    again = _run()
    assert again["graph"]["node_ids"] == graph["node_ids"]
    assert again["graph"]["edge_ids"] == graph["edge_ids"]
    ghosv = result["ghosv"]
    assert ghosv["instrument_id"] == "PARENT_EXECUTION_GHOSV"
    assert ghosv["findings_evaluated"] is True
    assert ghosv["safety_escalation_enabled"] is False
    assert ghosv["counts_as_proof"] is False
    readiness = result["readiness"]
    assert readiness["ADMISSION_READY"] is True
    assert readiness["GHV_READ_ONLY_READY"] is True
    assert readiness["GRAPH_READ_ONLY_READY"] is True
    assert readiness["GHOSV_READ_ONLY_READY"] is True
    assert readiness["TOOLCHAIN_READ_ONLY_READY"] is True
    assert readiness["coverage_status"] == "PARTIAL"
    assert readiness["CURRENT_VALIDATED"] is False
    assert readiness["CAUSAL_CLOSURE_PROVEN"] is False
    assert readiness["GUARDIAN_ACTIVE"] is False
    assert readiness["fixture_only"] is False
    assert readiness["productive_runtime_evidence"] is False


def test_new_mainline_pin_rebinds_without_code_change() -> None:
    result = _run(current_commit_sha=_OTHER_COMMIT, current_tree_sha=_OTHER_TREE)

    assert result["status"] == "ACCEPTED"
    assert result["admission"]["baseline_commit"] == _OTHER_COMMIT
    assert all(_OTHER_COMMIT in item for item in result["graph"]["node_ids"])


def test_commit_tree_mismatch_is_fail_closed() -> None:
    result = _run(current_tree_sha=_OTHER_TREE)

    assert result["status"] == "NOT_READY"
    assert result["admission"]["status"] == "FAIL_CLOSED"
    assert result["admission"]["reasons"] == ["commit_tree_mismatch"]
    assert result["ghv"]["composition_invoked"] is False
    assert result["graph"]["projected"] is False


def test_historical_currency_is_fail_closed() -> None:
    result = _run(baseline_currency="HISTORICAL")

    assert result["status"] == "FAIL_CLOSED"
    assert result["reasons"] == ["historical_baseline_rejected"]


def test_stale_subject_hash_is_rejected(monkeypatch: object) -> None:
    stale = []
    for record in verify_v1.OBSERVED_SUBJECTS:
        copied = dict(record)
        if copied["subject_id"] == FORWARD_ORIGIN:
            copied["source_sha256"] = "0" * 64
        stale.append(copied)
    monkeypatch.setattr(verify_v1, "OBSERVED_SUBJECTS", tuple(stale))

    result = _run()

    assert result["status"] == "REJECTED"
    assert result["reasons"] == [f"subject_hash_mismatch:{FORWARD_ORIGIN}"]


def test_unknown_submission_edge_is_not_evaluated() -> None:
    result = _run()
    unknown_ids = {edge["edge_id"] for edge in UNKNOWN_EDGES}

    assert _SUBMISSION_UNKNOWN in unknown_ids
    assert unknown_ids.isdisjoint(set(result["ghv"]["evaluated_edges"]))
    assert unknown_ids.isdisjoint(set(result["graph"]["edge_ids"]))


def test_three_instruments_run_independently() -> None:
    result = _run()
    ghv = run_execution_ghv_disclosure_v1(
        admission=result["admission"],
        call_edges=list(result["inventory"]["call_edges"]),
        unknown_edges=list(result["inventory"]["unknown_edges"]),
    )
    graph = run_execution_graph_memory_v1(ghv=ghv)
    ghosv = run_execution_ghosv_disclosure_v1(
        admission=result["admission"],
        findings=[],
        evidence_refs=[],
    )

    assert ghv["instrument_id"] == "PARENT_EXECUTION_GHV"
    assert graph["instrument_id"] == "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH"
    assert ghosv["instrument_id"] == "PARENT_EXECUTION_GHOSV"
    assert {ghv["instrument_id"], graph["instrument_id"], ghosv["instrument_id"]} == {
        "PARENT_EXECUTION_GHV",
        "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH",
        "PARENT_EXECUTION_GHOSV",
    }
    assert ghv["files_written"] is False
    assert graph["writer_invoked"] is False
    assert ghosv["counts_as_proof"] is False


def test_ghosv_missing_evidence_is_rejected() -> None:
    result = _run()
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


def test_package_does_not_import_writers_or_trading_or_store_a_baseline() -> None:
    for package in _PACKAGES:
        for path in sorted(package.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            text = path.read_text(encoding="utf-8")
            for banned in _WRITERS:
                assert banned not in text
            assert _SHA40.search(text) is None
            imported: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
                elif isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
            for name in imported:
                assert all(prefix not in name for prefix in _FORBIDDEN)
