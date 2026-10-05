"""Exclusion ledger for discovered-but-not-required components."""

from __future__ import annotations

from typing import Any, Mapping, Set


def build_exclusion_ledger_v1(
    discovered_modules: list[str],
    required_paths: Set[str],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for mod in discovered_modules:
        if mod in required_paths:
            continue
        entries.append(
            {
                "COMPONENT_OR_EDGE": mod,
                "DISCOVERED_BY": "import_bfs_forward_from_launcher",
                "CLASSIFICATION": "UNKNOWN_RELEVANCE",
                "EXCLUSION_REASON": "not_in_operation_semantic_required_graph",
                "EVIDENCE": "import_reachability_only",
                "WHY_IT_CANNOT_AFFECT_OPERATION": "not_adjudicated_in_this_pass",
            }
        )
    excluded_with_proof = [e for e in entries if e["CLASSIFICATION"] == "NOT_REQUIRED_WITH_PROOF"]
    unknown = [e for e in entries if e["CLASSIFICATION"] == "UNKNOWN_RELEVANCE"]
    return {
        "ENTRIES": entries[:500],
        "ENTRIES_TRUNCATED": len(entries) > 500,
        "TOTAL_EXCLUDED_CANDIDATES": len(entries),
        "EXCLUDED_WITH_PROOF_COUNT": len(excluded_with_proof),
        "UNKNOWN_RELEVANCE_COUNT": len(unknown),
    }
