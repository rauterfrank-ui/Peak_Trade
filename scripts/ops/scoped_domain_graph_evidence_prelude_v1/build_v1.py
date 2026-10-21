"""Build a pin-bound candidate manifest from evidenced source lines.

The prelude does not call the causal integrator and does not mark nodes
CURRENT_VERIFIED. A reference whose line does not contain its symbol is rejected.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import edge_semantics_flags
from scripts.ops.scoped_domain_graph_evidence_prelude_v1.constants_v1 import (
    AUTHORITY,
    CURRENT_VERIFIED,
    EVIDENCE_PLANE,
    REACHABILITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_AUTHORITY_EDGE_TYPES = frozenset({"AUTHORIZES", "EXTERNAL_EFFECT"})


def build_code_reference_prelude_v1(
    *,
    declared_commit_sha: str,
    declared_tree_sha: str,
    nodes: list[Mapping[str, str]],
    references: list[Mapping[str, Any]],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return a candidate manifest, or reasons when a reference is not in the tree."""
    root = _REPO_ROOT if repo_root is None else repo_root
    reasons: list[str] = []
    candidate_nodes: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()
    for node in nodes:
        native_id = str(node.get("object_id") or "")
        if native_id == "" or native_id in seen_nodes:
            reasons.append(f"node_invalid:{native_id}")
            continue
        seen_nodes.add(native_id)
        candidate_nodes.append(
            {
                "object_id": native_id,
                "evidence_plane": EVIDENCE_PLANE,
                "reachability": REACHABILITY,
                "scope_class": str(node.get("scope_class") or ""),
            }
        )

    candidate_edges: list[dict[str, Any]] = []
    seen_edges: set[str] = set()
    for reference in references:
        edge_id = str(reference.get("edge_id") or "")
        if edge_id == "" or edge_id in seen_edges:
            reasons.append(f"edge_invalid:{edge_id}")
            continue
        source = str(reference.get("source_native_id") or "")
        target = str(reference.get("target_native_id") or "")
        if source not in seen_nodes or target not in seen_nodes:
            reasons.append(f"edge_endpoint_missing:{edge_id}")
            continue
        evidence_reason = _evidence_reason(root, reference)
        if evidence_reason is not None:
            reasons.append(evidence_reason)
            continue
        edge_type = str(reference.get("edge_type") or "")
        if edge_type in _AUTHORITY_EDGE_TYPES:
            reasons.append(f"authority_implied:{edge_id}")
            continue
        try:
            flags = edge_semantics_flags(edge_type)
        except ValueError:
            reasons.append(f"unknown_edge_type:{edge_id}")
            continue
        if flags.get("trading_authority_implied"):
            reasons.append(f"authority_implied:{edge_id}")
            continue
        seen_edges.add(edge_id)
        candidate_edges.append(
            {
                "edge_id": edge_id,
                "source_native_id": source,
                "target_native_id": target,
                "evidence_plane": EVIDENCE_PLANE,
                "reachability": REACHABILITY,
                "causal_traversal_eligible": bool(flags["causal_propagation_allowed"]),
                "typed_edge": {
                    "edge_type": edge_type,
                    "structural_only": flags["structural_only"],
                    "causal_propagation_allowed": flags["causal_propagation_allowed"],
                    "trading_authority_implied": False,
                },
                "evidence": {
                    "path": str(reference["path"]),
                    "line": int(reference["line"]),
                    "symbol": str(reference["symbol"]),
                },
            }
        )

    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "declared_commit_sha": declared_commit_sha,
        "declared_tree_sha": declared_tree_sha,
        "current_verified": CURRENT_VERIFIED,
        "reachability": REACHABILITY,
        "candidate_nodes": candidate_nodes,
        "candidate_edges": candidate_edges,
        "reasons": reasons,
        "ok": not reasons,
    }


def _evidence_reason(repo_root: Path, reference: Mapping[str, Any]) -> str | None:
    edge_id = str(reference.get("edge_id") or "")
    raw_path = reference.get("path")
    line_number = reference.get("line")
    symbol = reference.get("symbol")
    if not isinstance(raw_path, str) or raw_path.startswith("/") or ".." in Path(raw_path).parts:
        return f"evidence_path_rejected:{edge_id}"
    if not isinstance(line_number, int) or line_number < 1:
        return f"evidence_line_rejected:{edge_id}"
    if not isinstance(symbol, str) or symbol.strip() == "":
        return f"evidence_symbol_rejected:{edge_id}"
    path = repo_root / raw_path
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return f"evidence_unreadable:{edge_id}"
    if line_number > len(lines):
        return f"evidence_line_past_eof:{edge_id}"
    if symbol not in lines[line_number - 1]:
        return f"evidence_symbol_absent:{edge_id}"
    return None
