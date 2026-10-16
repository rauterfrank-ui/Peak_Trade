"""Bidirectional deterministic traversal over composed forensic graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Direction = Literal["FORWARD", "REVERSE"]


@dataclass(frozen=True)
class TraversalStepV1:
    edge_id: str
    from_native_id: str
    to_native_id: str
    edge_type: str
    causal_traversal_eligible: bool


@dataclass
class TraversalResultV1:
    direction: Direction
    origin_native_id: str
    reachable_native_ids: list[str] = field(default_factory=list)
    paths: list[list[TraversalStepV1]] = field(default_factory=list)
    unknown_endpoints: list[str] = field(default_factory=list)
    blocked_non_causal: list[str] = field(default_factory=list)


def _edge_records(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for edge in edges:
        src = edge.get("source_native_id")
        tgt = edge.get("target_native_id")
        if not src or not tgt:
            continue
        typed = edge.get("typed_edge") or {}
        out.append(
            {
                "edge_id": str(edge.get("edge_id") or ""),
                "source_native_id": str(src),
                "target_native_id": str(tgt),
                "edge_type": str(typed.get("edge_type") or "UNKNOWN"),
                "causal_traversal_eligible": bool(edge.get("causal_traversal_eligible")),
            }
        )
    return out


def traverse_forensic_graph_v1(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    origin_native_id: str,
    direction: Direction,
    causal_only: bool = True,
    max_depth: int = 32,
) -> TraversalResultV1:
    node_ids = {str(n.get("source_native_id")) for n in nodes if n.get("source_native_id")}
    result = TraversalResultV1(direction=direction, origin_native_id=origin_native_id)
    if origin_native_id not in node_ids:
        result.unknown_endpoints.append(origin_native_id)
        return result

    adjacency: dict[str, list[dict[str, Any]]] = {nid: [] for nid in node_ids}
    for rec in _edge_records(edges):
        if rec["source_native_id"] not in node_ids or rec["target_native_id"] not in node_ids:
            missing = [
                sid
                for sid in (rec["source_native_id"], rec["target_native_id"])
                if sid not in node_ids
            ]
            result.unknown_endpoints.extend(missing)
            continue
        if causal_only and not rec["causal_traversal_eligible"]:
            result.blocked_non_causal.append(rec["edge_id"])
            continue
        if direction == "FORWARD":
            adjacency[rec["source_native_id"]].append(rec)
        else:
            adjacency[rec["target_native_id"]].append(
                {
                    **rec,
                    "source_native_id": rec["target_native_id"],
                    "target_native_id": rec["source_native_id"],
                }
            )

    # Deterministic BFS: sort neighbors by (target, edge_id).
    visited: set[str] = {origin_native_id}
    queue: list[tuple[str, list[TraversalStepV1]]] = [(origin_native_id, [])]
    reachable: list[str] = []

    while queue:
        current, path = queue.pop(0)
        if current != origin_native_id:
            reachable.append(current)
        if len(path) >= max_depth:
            continue
        neighbors = sorted(
            adjacency.get(current, []),
            key=lambda r: (r["target_native_id"], r["edge_id"]),
        )
        for rec in neighbors:
            nxt = rec["target_native_id"]
            step = TraversalStepV1(
                edge_id=rec["edge_id"],
                from_native_id=rec["source_native_id"],
                to_native_id=rec["target_native_id"],
                edge_type=rec["edge_type"],
                causal_traversal_eligible=rec["causal_traversal_eligible"],
            )
            new_path = [*path, step]
            if nxt in visited:
                result.paths.append(new_path)
                continue
            visited.add(nxt)
            result.paths.append(new_path)
            queue.append((nxt, new_path))

    result.reachable_native_ids = sorted(set(reachable))
    result.unknown_endpoints = sorted(set(result.unknown_endpoints))
    result.blocked_non_causal = sorted(set(result.blocked_non_causal))
    return result
