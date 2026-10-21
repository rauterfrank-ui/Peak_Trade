"""Run admission, GHV, graph, GHOSV, and readiness. No writers and no activation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.execution_parent_disclosure_v1.bind_v1 import bind_execution_disclosure_v1
from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    BASELINE_CURRENCY_CURRENT,
    STATUS_FAIL_CLOSED,
)
from scripts.ops.execution_parent_instruments_v1.ghosv_v1 import (
    findings_for_inventory_v1,
    run_execution_ghosv_disclosure_v1,
)
from scripts.ops.execution_parent_instruments_v1.ghv_v1 import run_execution_ghv_disclosure_v1
from scripts.ops.execution_parent_instruments_v1.graph_v1 import run_execution_graph_memory_v1
from scripts.ops.execution_parent_instruments_v1.readiness_v1 import derive_execution_readiness_v1
from scripts.ops.execution_parent_instruments_v1.verify_v1 import (
    execution_provenance_v1,
    load_verified_inventory_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def run_execution_parent_toolchain_v1(
    *,
    current_commit_sha: str,
    current_tree_sha: str,
    baseline_currency: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """One explicit current-pin observation. No historical fallback."""
    if baseline_currency != BASELINE_CURRENCY_CURRENT:
        return {"status": STATUS_FAIL_CLOSED, "reasons": ["historical_baseline_rejected"]}
    root = _REPO_ROOT if repo_root is None else repo_root
    inventory, reason = load_verified_inventory_v1(
        root,
        commit_sha=current_commit_sha,
        tree_sha=current_tree_sha,
    )
    if inventory is None:
        return {"status": "REJECTED", "reasons": [reason or "inventory_failed"]}
    provenance = execution_provenance_v1(
        commit_sha=current_commit_sha,
        tree_sha=current_tree_sha,
        repo_root=root,
    )
    admission = bind_execution_disclosure_v1(
        authoritative_commit_sha=current_commit_sha,
        authoritative_tree_sha=current_tree_sha,
        declared_commit_sha=current_commit_sha,
        declared_tree_sha=current_tree_sha,
        provenance=provenance,
        disclosure_subjects=list(inventory["disclosure_subjects"]),
        baseline_currency=baseline_currency,
        repo_root=root,
    )
    ghv = run_execution_ghv_disclosure_v1(
        admission=admission,
        call_edges=list(inventory["call_edges"]),
        unknown_edges=list(inventory["unknown_edges"]),
        policy_guards=list(inventory.get("policy_guards") or []),
    )
    graph = run_execution_graph_memory_v1(ghv=ghv)
    findings, refs = findings_for_inventory_v1(inventory, commit_sha=current_commit_sha)
    ghosv = run_execution_ghosv_disclosure_v1(
        admission=admission,
        findings=findings,
        evidence_refs=refs,
    )
    readiness = derive_execution_readiness_v1(
        admission=admission,
        ghv=ghv,
        graph=graph,
        ghosv=ghosv,
    )
    return {
        "status": "ACCEPTED" if readiness["TOOLCHAIN_READ_ONLY_READY"] else "NOT_READY",
        "inventory": inventory,
        "admission": admission,
        "ghv": ghv,
        "graph": graph,
        "ghosv": ghosv,
        "readiness": readiness,
        "historical_sources": list(admission.get("historical_sources") or []),
        "productive_runtime_evidence": False,
    }
