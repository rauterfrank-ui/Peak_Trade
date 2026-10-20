"""Read-only Execution causal-graph binding verifier. AUTHORITY=NONE. No graph rebuild."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_guardian_binding_verifier_v1.common_v1 import (
    assert_no_forbidden_keys_v1,
    authority_block_v1,
    bind_baseline_v1,
    bind_graph_artifact_v1,
    direction_class_v1,
    registry_status_v1,
    reject_claims_v1,
    symbol_line_v1,
)
from scripts.ops.execution_guardian_binding_verifier_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    INTERNAL_PROSE_ALIAS,
    INTERNAL_REGISTRY_LABELS,
    PROSE_ONLY_INTERNAL_LABEL,
    REGISTRY_ID,
    frozen_edges_v1,
    frozen_open_tasks_v1,
)

SCHEMA_ID = "EXECUTION_CURRENT_CAUSAL_GRAPH_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "EXECUTION_CURRENT_CAUSAL_GRAPH"


def verify_execution_graph_v1(
    *,
    current_sha: str,
    current_tree: str,
    registry: Mapping[str, Any] | None,
    sources: Mapping[str, str] | None = None,
    anchors: list[Mapping[str, str]] | None = None,
    graph_artifact: Mapping[str, Any] | None = None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    reject_claims_v1(claim_map, reasons)
    bind_baseline_v1(current_sha, current_tree, reasons)
    status = registry_status_v1(registry, reasons)
    binding = bind_graph_artifact_v1(graph_artifact, reasons)
    frozen = frozen_edges_v1()
    assessed = _assess_anchors(frozen, sources, anchors, reasons)
    edges = frozen if status == "MATCH" else []
    nodes = _nodes(edges) if status == "MATCH" else []
    typed = [_edge(row, assessed.get(row["EDGE_ID"])) for row in edges]
    open_edges = [row for row in typed if row["EDGE_CLASS"] == "UNRESOLVED"]
    report = {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "DOMAIN": "EXECUTION",
        **authority_block_v1(),
        "GRAPH_READY": False,
        "GRAPH_PROJECTION_AUTHORITY": "NONE",
        "CURRENT_SHA": EXPECTED_BASELINE_SHA,
        "CURRENT_TREE": EXPECTED_BASELINE_TREE,
        "OBSERVED_SHA": current_sha,
        "OBSERVED_TREE": current_tree,
        "REGISTRY_ID": REGISTRY_ID,
        "REGISTRY_STATUS": status,
        "REGISTRY_IS_SOURCE_PROOF": False,
        "GRAPH_ARTIFACT_BINDING": binding,
        "VERIFICATION_STATUS": "REJECTED" if reasons else "REPORTED",
        "REJECTION_REASONS": list(dict.fromkeys(reasons)),
        "NODES": nodes,
        "INTERNAL_NODES": [row for row in nodes if row["BOUNDARY"] == "INTERNAL"],
        "EXTERNAL_NODES": [row for row in nodes if row["BOUNDARY"] == "EXTERNAL"],
        "EDGES": typed,
        "OPEN_EDGES": open_edges,
        "OPEN_TASKS": frozen_open_tasks_v1(),
        "GRAPH_REBUILT": False,
        "TRAVERSAL_EXECUTED": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "WHOLE_SYSTEM_GRAPH_USED": False,
    }
    assert_no_forbidden_keys_v1(report)
    return report


def _assess_anchors(
    edges: list[dict[str, str]],
    sources: Mapping[str, str] | None,
    anchors: list[Mapping[str, str]] | None,
    reasons: list[str],
) -> dict[str, dict[str, Any]]:
    if not anchors:
        return {}
    if not isinstance(sources, Mapping):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return {}
    known = {row["EDGE_ID"] for row in edges}
    assessed: dict[str, dict[str, Any]] = {}
    for anchor in anchors:
        edge_id = anchor.get("EDGE_ID")
        source_file = anchor.get("SOURCE_FILE")
        symbol = anchor.get("SYMBOL")
        if not isinstance(edge_id, str) or edge_id not in known:
            reasons.append("CONTRACT_MISMATCH")
            continue
        if not isinstance(source_file, str) or not isinstance(symbol, str):
            reasons.append("MISSING_REQUIRED_EVIDENCE")
            assessed[edge_id] = {"RESULT": "MISSING_REQUIRED_EVIDENCE", "LINE": None}
            continue
        source = sources.get(source_file)
        if not isinstance(source, str) or not source:
            reasons.append("MISSING_REQUIRED_EVIDENCE")
            assessed[edge_id] = {
                "RESULT": "MISSING_REQUIRED_EVIDENCE",
                "SOURCE_FILE": source_file,
                "SYMBOL": symbol,
                "LINE": None,
            }
            continue
        line = symbol_line_v1(source, symbol)
        if line is None:
            reasons.append("CONTRACT_MISMATCH")
            result = "CONTRACT_MISMATCH"
        else:
            result = "MATCH"
        assessed[edge_id] = {
            "RESULT": result,
            "SOURCE_FILE": source_file,
            "SYMBOL": symbol,
            "LINE": line,
        }
    return assessed


def _nodes(edges: list[dict[str, str]]) -> list[dict[str, Any]]:
    labels: list[str] = [PROSE_ONLY_INTERNAL_LABEL]
    for row in edges:
        for label in (row["SOURCE"], row["TARGET"]):
            if label not in labels:
                labels.append(label)
    rows: list[dict[str, Any]] = []
    for label in labels:
        boundary = "INTERNAL" if _internal(label) else "EXTERNAL"
        rows.append(
            {
                "NODE_ID": label,
                "LABEL": label,
                "BOUNDARY": boundary,
                "PROSE_ALIAS": INTERNAL_PROSE_ALIAS.get(label),
                "PROVENANCE": _provenance("NODE", label),
            }
        )
    return rows


def _internal(label: str) -> bool:
    return label in INTERNAL_REGISTRY_LABELS or label == PROSE_ONLY_INTERNAL_LABEL


def _edge(row: Mapping[str, str], anchor: Mapping[str, Any] | None) -> dict[str, Any]:
    assessed = anchor is not None
    provenance = _provenance("EDGE", row["EDGE_ID"])
    if assessed and anchor.get("RESULT") == "MATCH":
        provenance = {
            **provenance,
            "EVIDENCE_CLASS": "CURRENT_CODE",
            "SOURCE_FILE": str(anchor.get("SOURCE_FILE")),
            "SYMBOL": str(anchor.get("SYMBOL")),
            "LINE": str(anchor.get("LINE")),
        }
    return {
        "EDGE_ID": row["EDGE_ID"],
        "SOURCE": row["SOURCE"],
        "TARGET": row["TARGET"],
        "DIRECTION": row["DIRECTION"],
        "DIRECTION_CLASS": direction_class_v1(row["DIRECTION"]),
        "EDGE_CLASS": row["EDGE_CLASS"],
        "CONTRACT": row["CONTRACT"],
        "DOMAIN_OWNER": row["DOMAIN_OWNER"],
        "UNCERTAINTY": row["UNCERTAINTY"],
        "SOURCE_BOUNDARY": "INTERNAL" if _internal(row["SOURCE"]) else "EXTERNAL",
        "TARGET_BOUNDARY": "INTERNAL" if _internal(row["TARGET"]) else "EXTERNAL",
        "SOURCE_ANCHOR": anchor.get("RESULT") if assessed else "NOT_ASSESSED",
        "SOURCE_FILE": anchor.get("SOURCE_FILE") if assessed else None,
        "SYMBOL": anchor.get("SYMBOL") if assessed else None,
        "LINE": anchor.get("LINE") if assessed else None,
        "PROVENANCE": provenance,
    }


def _provenance(kind: str, subject: str) -> dict[str, str]:
    return {
        "KIND": kind,
        "SUBJECT": subject,
        "REGISTRY_ID": REGISTRY_ID,
        "CURRENT_SHA": EXPECTED_BASELINE_SHA,
        "CURRENT_TREE": EXPECTED_BASELINE_TREE,
        "EVIDENCE_CLASS": "EXECUTION_M15_BOUNDARY_HANDOFF",
    }
