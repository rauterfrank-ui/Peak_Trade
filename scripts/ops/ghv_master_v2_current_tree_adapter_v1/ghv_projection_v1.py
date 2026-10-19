"""Project adapter CALLS records into the existing GHV traversal schema.

Graph neighborhood is not productive runtime reachability.
This module does not create a graph engine and does not write graph artifacts.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import edge_semantics_flags
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.traversal_v1 import (
    traverse_forensic_graph_v1,
)
from scripts.ops.ghv_master_v2_current_tree_adapter_v1.tree_reader_v1 import PinRejected

_REQUIRED_EDGE_FIELDS = (
    "source_native_id",
    "target_native_id",
    "edge_id",
    "typed_edge",
    "causal_traversal_eligible",
)


class ProjectionRejected(PinRejected):
    pass


def ghv_native_id(*, path: str, symbol: str) -> str:
    if not isinstance(path, str) or not path or not isinstance(symbol, str) or not symbol:
        raise ProjectionRejected("NATIVE_ID_ABSENT")
    if "\n" in path or "\n" in symbol:
        raise ProjectionRejected("NATIVE_ID_ABSENT")
    return f"{path}::{symbol}"


def _require_record_value(record: dict[str, Any], field: str) -> Any:
    if field not in record or record[field] in (None, ""):
        raise ProjectionRejected(f"PROJECTION_FIELD_ABSENT:{field}")
    return record[field]


def _edge_id(
    *,
    source_native_id: str,
    target_native_id: str,
    edge_type: str,
    call_lines: list[int],
    current_tree: str,
) -> str:
    payload = json.dumps(
        {
            "v": 1,
            "source_native_id": source_native_id,
            "target_native_id": target_native_id,
            "edge_type": edge_type,
            "call_lines": call_lines,
            "current_tree": current_tree,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "calls:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _flags_for_record(record: dict[str, Any]) -> dict[str, Any]:
    edge_type = str(_require_record_value(record, "edge_type"))
    try:
        flags = dict(edge_semantics_flags(edge_type))
    except ValueError as exc:
        raise ProjectionRejected("UNKNOWN_EDGE_TYPE") from exc
    supplied = record.get("ghv_edge_flags")
    if not isinstance(supplied, dict):
        raise ProjectionRejected("PROJECTION_FIELD_ABSENT:ghv_edge_flags")
    if supplied.get("edge_type") != edge_type:
        raise ProjectionRejected("EDGE_TYPE_PROVENANCE_MISMATCH")
    if supplied.get("trading_authority_implied") is not False:
        raise ProjectionRejected("AUTHORITY_ESCALATION_REJECTED")
    if flags.get("trading_authority_implied") is not False:
        raise ProjectionRejected("AUTHORITY_ESCALATION_REJECTED")
    if record.get("trading_authority_implied") is not False:
        raise ProjectionRejected("AUTHORITY_ESCALATION_REJECTED")
    if "causal_propagation_allowed" not in supplied:
        raise ProjectionRejected("PROJECTION_FIELD_ABSENT:causal_propagation_allowed")
    if supplied["causal_propagation_allowed"] is not flags["causal_propagation_allowed"]:
        raise ProjectionRejected("CAUSAL_FLAG_MISMATCH")
    return flags


def _reject_status_upgrade(record: dict[str, Any]) -> None:
    if "activity" not in record or "authorization" not in record:
        raise ProjectionRejected("PROJECTION_FIELD_ABSENT:status")
    if record["activity"] == "ACTIVE" or record["authorization"] == "AUTHORIZED":
        raise ProjectionRejected("STATUS_UPGRADE_REJECTED")


def project_adapter_edges_v1(
    records: list[dict[str, Any]],
    *,
    target_overlays: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Project records. Incomplete targets are explicit rejections, never silent drops."""
    overlays = target_overlays or {}
    nodes: dict[str, dict[str, Any]] = {}
    projected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    def remember_node(native_id: str, *, path: str, symbol: str, record: dict[str, Any]) -> None:
        current = nodes.get(native_id)
        provenance = {
            "source_native_id": native_id,
            "file": path,
            "symbol": symbol,
            "current_sha": record["current_sha"],
            "current_tree": record["current_tree"],
        }
        if current is None:
            nodes[native_id] = provenance
            return
        if (
            current["current_sha"] != provenance["current_sha"]
            or current["current_tree"] != provenance["current_tree"]
        ):
            raise ProjectionRejected("PROVENANCE_CONFLICT")

    for record in records:
        if record.get("record_kind") != "EDGE":
            raise ProjectionRejected("EDGE_RECORD_REQUIRED")
        _reject_status_upgrade(record)
        flags = _flags_for_record(record)
        source_path = str(_require_record_value(record, "file"))
        source_symbol = str(_require_record_value(record, "symbol"))
        target_symbol = str(_require_record_value(record, "target_symbol"))
        current_sha = str(_require_record_value(record, "current_sha"))
        current_tree = str(_require_record_value(record, "current_tree"))
        evidence_ref = str(_require_record_value(record, "evidence_ref"))
        call_lines_raw = record.get("call_lines")
        if not isinstance(call_lines_raw, list) or not call_lines_raw:
            raise ProjectionRejected("PROJECTION_FIELD_ABSENT:call_lines")
        call_lines = sorted(int(line) for line in call_lines_raw)
        target_file = record.get("target_file")
        overlay_applied = False
        if not target_file:
            overlay = overlays.get((source_path, source_symbol, target_symbol))
            if overlay is None or not overlay.get("target_file"):
                rejected.append(
                    {
                        "file": source_path,
                        "symbol": source_symbol,
                        "target_symbol": target_symbol,
                        "call_lines": call_lines,
                        "reason": "TARGET_NATIVE_ID_ABSENT",
                    }
                )
                continue
            target_file = str(overlay["target_file"])
            overlay_applied = True
        source_native_id = ghv_native_id(path=source_path, symbol=source_symbol)
        target_native_id = ghv_native_id(path=str(target_file), symbol=target_symbol)
        edge_type = str(flags["edge_type"])
        projected_edge = {
            "source_native_id": source_native_id,
            "target_native_id": target_native_id,
            "edge_id": _edge_id(
                source_native_id=source_native_id,
                target_native_id=target_native_id,
                edge_type=edge_type,
                call_lines=call_lines,
                current_tree=current_tree,
            ),
            "typed_edge": {"edge_type": edge_type},
            "causal_traversal_eligible": flags["causal_propagation_allowed"] is True,
            "current_sha": current_sha,
            "current_tree": current_tree,
            "evidence_ref": evidence_ref,
            "source_blob_sha": record.get("source_blob_sha"),
            "call_lines": call_lines,
            "file": source_path,
            "symbol": source_symbol,
            "target_file": target_file,
            "target_symbol": target_symbol,
            "activity": record["activity"],
            "authorization": record["authorization"],
            "reachability": "NOT_PROVEN",
            "trading_authority_implied": False,
            "runtime_reachability": "NOT_PROVEN",
            "graph_neighborhood_is_runtime_reachability": False,
            "target_overlay_applied": overlay_applied,
        }
        for field in _REQUIRED_EDGE_FIELDS:
            if field not in projected_edge or projected_edge[field] in (None, ""):
                raise ProjectionRejected(f"GHV_SCHEMA_FIELD_ABSENT:{field}")
        if not isinstance(projected_edge["typed_edge"].get("edge_type"), str):
            raise ProjectionRejected("GHV_SCHEMA_FIELD_ABSENT:typed_edge.edge_type")
        if projected_edge["trading_authority_implied"] is not False:
            raise ProjectionRejected("AUTHORITY_ESCALATION_REJECTED")
        remember_node(source_native_id, path=source_path, symbol=source_symbol, record=record)
        remember_node(
            target_native_id,
            path=str(target_file),
            symbol=target_symbol,
            record=record,
        )
        projected.append(projected_edge)

    if len(projected) + len(rejected) != len(records):
        raise ProjectionRejected("SILENT_DROP_REJECTED")
    node_list = [nodes[key] for key in sorted(nodes)]
    edge_list = sorted(
        projected,
        key=lambda edge: (edge["source_native_id"], edge["target_native_id"], edge["edge_id"]),
    )
    rejected.sort(key=lambda item: (item["file"], item["symbol"], item["target_symbol"]))
    status = "PROJECTED" if not rejected else "PROJECTED_WITH_EXPLICIT_REJECTIONS"
    return {
        "schema": "GHV_TRAVERSAL_V1",
        "status": status,
        "max_depth_enforced": 1,
        "graph_neighborhood_is_runtime_reachability": False,
        "trading_authority_implied": False,
        "nodes": node_list,
        "edges": edge_list,
        "rejected": rejected,
        "node_count": len(node_list),
        "edge_count": len(edge_list),
        "rejected_count": len(rejected),
    }


def assert_ghv_traversal_schema_v1(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    node_ids = {str(node.get("source_native_id")) for node in nodes if node.get("source_native_id")}
    if len(node_ids) != len(nodes):
        raise ProjectionRejected("GHV_SCHEMA_FIELD_ABSENT:source_native_id")
    for edge in edges:
        for field in _REQUIRED_EDGE_FIELDS:
            if field not in edge or edge[field] in (None, ""):
                raise ProjectionRejected(f"GHV_SCHEMA_FIELD_ABSENT:{field}")
        typed = edge["typed_edge"]
        if not isinstance(typed, dict) or not typed.get("edge_type"):
            raise ProjectionRejected("GHV_SCHEMA_FIELD_ABSENT:typed_edge.edge_type")
        if not isinstance(edge["causal_traversal_eligible"], bool):
            raise ProjectionRejected("GHV_SCHEMA_FIELD_ABSENT:causal_traversal_eligible")
        if edge.get("trading_authority_implied") is not False:
            raise ProjectionRejected("AUTHORITY_ESCALATION_REJECTED")
        if edge["source_native_id"] not in node_ids or edge["target_native_id"] not in node_ids:
            raise ProjectionRejected("GHV_ENDPOINT_ABSENT")


def traverse_projected_graph_v1(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    origin_native_id: str,
    direction: str,
    max_depth: int,
) -> Any:
    if max_depth != 1:
        raise ProjectionRejected("DEPTH_LIMIT_REJECTED")
    if direction not in {"FORWARD", "REVERSE"}:
        raise ProjectionRejected("DIRECTION_REJECTED")
    assert_ghv_traversal_schema_v1(nodes=nodes, edges=edges)
    return traverse_forensic_graph_v1(
        nodes=nodes,
        edges=edges,
        origin_native_id=origin_native_id,
        direction=direction,
        causal_only=True,
        max_depth=1,
    )
