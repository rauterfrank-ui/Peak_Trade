"""Run admission, GHV, graph, GHOSV, and readiness. No writers and no activation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.execution_parent_disclosure_v1.bind_v1 import bind_execution_disclosure_v1
from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
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


def run_execution_parent_toolchain_v1(repo_root: Path | None = None) -> dict[str, Any]:
    """One bounded pin observation. Historical sources stay historical."""
    root = _REPO_ROOT if repo_root is None else repo_root
    inventory, reason = load_verified_inventory_v1(root)
    if inventory is None:
        return {"status": "REJECTED", "reasons": [reason or "inventory_failed"]}
    provenance = execution_provenance_v1(root)
    admission = bind_execution_disclosure_v1(
        authoritative_commit_sha=EXPECTED_BASELINE_SHA,
        authoritative_tree_sha=EXPECTED_BASELINE_TREE,
        declared_commit_sha=EXPECTED_BASELINE_SHA,
        declared_tree_sha=EXPECTED_BASELINE_TREE,
        provenance=provenance,
        disclosure_subjects=list(inventory["disclosure_subjects"]),
        repo_root=root,
    )
    ghv = run_execution_ghv_disclosure_v1(
        admission=admission,
        call_edges=list(inventory["call_edges"]),
        unknown_edge=inventory["unknown_edge"],
    )
    graph = run_execution_graph_memory_v1(ghv=ghv)
    findings, refs = findings_for_inventory_v1(inventory)
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
