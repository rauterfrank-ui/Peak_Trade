"""Node and edge coverage matrices."""

from __future__ import annotations

from typing import Any, Mapping


def _node_row(node_id: str, *, static: str, runtime: str, ghv: str) -> dict[str, Any]:
    dims = {
        "STATIC": static,
        "RUNTIME": runtime,
        "GHV": ghv,
        "CONFIG_STATE": "PARTIALLY_PROVEN" if node_id.startswith("N_CAP24") else "UNKNOWN",
        "PERSISTENCE": "PARTIALLY_PROVEN" if "CAP24" in node_id else "UNKNOWN",
        "AUTHORITY_SAFETY": "PROVEN"
        if node_id in {"N_TERMINAL_GUARD", "N_OWNER_GO"}
        else "PARTIAL",
        "GOVERNANCE_PROVENANCE": "PROVEN",
        "INDEPENDENT_PROOF": static,
    }
    if "UNKNOWN" in dims.values():
        result = "UNKNOWN" if dims["STATIC"] == "UNKNOWN" else "PARTIALLY_PROVEN"
    elif "CONFLICTING" in dims.values():
        result = "CONFLICTING"
    elif "VIOLATED" in dims.values():
        result = "VIOLATED"
    elif all(v == "PROVEN" for v in dims.values()):
        result = "PROVEN"
    else:
        result = "PARTIALLY_PROVEN"
    return {"NODE_ID": node_id, **dims, "RESULT": result}


def build_node_coverage_matrix_v1(
    required_graph: Mapping[str, Any],
    import_forward: Mapping[str, Any],
    ghv_diff: Mapping[str, Any],
) -> dict[str, Any]:
    reach = set(import_forward.get("reachable_modules", []))
    ghv_uncovered = set(ghv_diff.get("REAL_REQUIRED_NOT_COVERED_BY_GHV", []))
    rows = []
    for node in required_graph.get("nodes", []):
        nid = node["id"]
        paths = node.get("resolved_paths") or []
        static = "PROVEN" if paths and any(p in reach for p in paths) else "PARTIALLY_PROVEN"
        if not paths:
            static = "UNKNOWN"
        runtime = "UNKNOWN"
        if nid in {"N_S6_LIVE_C1", "N_GET_TRANSPORT", "N_EEA_ACQ"}:
            runtime = "LIVE_ONLY_UNPROVEN"
        ghv = "PROVEN" if nid not in ghv_uncovered else "PARTIALLY_PROVEN"
        if nid in ghv_uncovered:
            ghv = "UNKNOWN"
        rows.append(_node_row(nid, static=static, runtime=runtime, ghv=ghv))
    return {"ROWS": rows, "NODE_COUNT": len(rows)}


def build_edge_coverage_matrix_v1(required_graph: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for edge in required_graph.get("edges", []):
        eid = edge.get("edge_identity") or edge.get("contract")
        rows.append(
            {
                "EDGE_ID": eid,
                "PRODUCER": edge.get("producer"),
                "CONSUMER": edge.get("consumer"),
                "STATIC": "PROVEN",
                "RUNTIME": "UNKNOWN",
                "GHV": "PARTIALLY_PROVEN",
                "CONTRACT": "PROVEN",
                "STATE": "UNKNOWN",
                "AUTHORITY": "PARTIAL",
                "GUARD": "PARTIAL" if edge.get("consumer") == "N_TERMINAL_GUARD" else "UNKNOWN",
                "INDEPENDENT_PROOF": "PARTIALLY_PROVEN",
                "RESULT": "PARTIALLY_PROVEN",
            }
        )
    return {"ROWS": rows, "EDGE_COUNT": len(rows)}
