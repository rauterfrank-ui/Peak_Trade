"""Depth-1 outer cut. GHV types are recorded beside the original flow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from scripts.ops.mv2_outer_boundary_projector_v1.classification_v1 import (
    derive_owner_relation_class_v1,
)

FlowMapper = Callable[[dict[str, Any]], tuple[str | None, str]]
TraverseFn = Callable[..., Any]


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def normalize_observed_edge_v1(raw: dict[str, Any]) -> dict[str, Any]:
    flow = raw.get("original_flow_type")
    flow_text = _text(flow).strip()
    if flow_text == "":
        flow_text = "UNKNOWN"
    resolution = _text(raw.get("endpoint_resolution") or "UNRESOLVED")
    return {
        "edge_id": _text(raw.get("edge_id")),
        "source_id": _text(raw.get("source_id")),
        "target_id": _text(raw.get("target_id")),
        "original_flow_type": flow_text,
        "endpoint_resolution": resolution,
        "source_kind": _text(raw.get("source_kind") or "UNSPECIFIED"),
        "baseline": _text(raw.get("baseline")),
        "artifact": _text(raw.get("artifact")),
        "authority": _text(raw.get("authority") or "NONE"),
        "corroboration": raw.get("corroboration"),
        "observed_direction": _text(raw.get("observed_direction") or "UNKNOWN"),
        "contract_or_payload": raw.get("contract_or_payload"),
        "current_proof": bool(raw.get("current_proof", True)),
    }


def ghv_type_for_flow_v1(
    edge: dict[str, Any],
    flow_mapper: FlowMapper | None,
) -> str | None:
    original_flow_type = str(edge.get("original_flow_type") or "")
    if flow_mapper is None or original_flow_type in {"", "UNKNOWN"}:
        return None
    mapped, _note = flow_mapper(
        {
            "flow_type": original_flow_type,
            "contract_or_payload": edge.get("contract_or_payload"),
        }
    )
    if mapped is None or mapped == "":
        return None
    return str(mapped)


def _edge_record(
    edge: dict[str, Any],
    *,
    classification: str,
    owner_class: str,
    ghv_edge_type: str | None,
    uncertainty: str,
) -> dict[str, Any]:
    return {
        "edge_id": edge["edge_id"],
        "classification": classification,
        "original_flow_type": edge["original_flow_type"],
        "owner_relation_class": owner_class,
        "ghv_edge_type": ghv_edge_type,
        "ghv_edge_type_replaces_flow": False,
        "direction": edge["observed_direction"],
        "source_id": edge["source_id"],
        "target_id": edge["target_id"],
        "source_evidence": {
            "kind": edge["source_kind"],
            "artifact": edge["artifact"],
            "baseline": edge["baseline"],
            "authority": edge["authority"],
        },
        "provenance": {
            "source_kind": edge["source_kind"],
            "baseline": edge["baseline"],
            "current_proof": edge["current_proof"],
            "unverified_contract_or_payload": edge["contract_or_payload"],
        },
        "proof_status": "NOT_PROVEN"
        if classification == "UNRESOLVED_EDGE"
        else "DIRECT_EDGE_EVIDENCED",
        "uncertainty": uncertainty,
        "synthetic": False,
        "identity_join": False,
    }


def cut_outer_edges_v1(
    raw_edges: list[dict[str, Any]],
    *,
    proven_member_ids: set[str],
    proven_external_ids: set[str],
    flow_mapper: FlowMapper | None,
) -> dict[str, list[dict[str, Any]]]:
    inbound: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for raw in raw_edges:
        edge = normalize_observed_edge_v1(raw)
        ghv_edge_type = ghv_type_for_flow_v1(edge, flow_mapper)
        owner_class = derive_owner_relation_class_v1(
            None if edge["original_flow_type"] == "UNKNOWN" else edge["original_flow_type"],
            None if edge["corroboration"] is None else str(edge["corroboration"]),
        )
        missing_endpoint = edge["source_id"] == "" or edge["target_id"] == ""
        if not edge["current_proof"]:
            reason = "SOURCE_BASELINE_IS_NOT_CURRENT_PROOF"
            if edge["source_id"] == "" or edge["target_id"] == "":
                reason = f"{reason};UNRESOLVED_ENDPOINT"
            elif edge["endpoint_resolution"] != "COMPONENT":
                reason = f"{reason};UNRESOLVED_COMPONENT_IDENTITY"
            if owner_class == "UNKNOWN":
                reason = f"{reason};OWNER_RELATION_CLASS_UNKNOWN"
            unresolved.append(
                _edge_record(
                    edge,
                    classification="UNRESOLVED_EDGE",
                    owner_class="UNKNOWN",
                    ghv_edge_type=ghv_edge_type,
                    uncertainty=reason,
                )
            )
            continue
        if missing_endpoint or edge["endpoint_resolution"] != "COMPONENT":
            reason = "UNRESOLVED_ENDPOINT" if missing_endpoint else "UNRESOLVED_COMPONENT_IDENTITY"
            if owner_class == "UNKNOWN":
                reason = f"{reason};OWNER_RELATION_CLASS_UNKNOWN"
            unresolved.append(
                _edge_record(
                    edge,
                    classification="UNRESOLVED_EDGE",
                    owner_class=owner_class if not missing_endpoint else "UNKNOWN",
                    ghv_edge_type=ghv_edge_type,
                    uncertainty=reason,
                )
            )
            continue
        if owner_class == "UNKNOWN":
            unresolved.append(
                _edge_record(
                    edge,
                    classification="UNRESOLVED_EDGE",
                    owner_class="UNKNOWN",
                    ghv_edge_type=ghv_edge_type,
                    uncertainty="OWNER_RELATION_CLASS_UNKNOWN",
                )
            )
            continue
        source_member = edge["source_id"] in proven_member_ids
        target_member = edge["target_id"] in proven_member_ids
        source_external = edge["source_id"] in proven_external_ids
        target_external = edge["target_id"] in proven_external_ids
        record = _edge_record(
            edge,
            classification="RESOLVED_CROSS_BOUNDARY_EDGE",
            owner_class=owner_class,
            ghv_edge_type=ghv_edge_type,
            uncertainty="DIRECT_EDGE_ONLY_BOUNDARY_NOT_RATIFIED",
        )
        if target_member and source_external and not source_member:
            record["direction"] = "INBOUND"
            inbound.append(record)
        elif source_member and target_external and not target_member:
            record["direction"] = "OUTBOUND"
            outbound.append(record)
        else:
            record["classification"] = "UNRESOLVED_EDGE"
            record["proof_status"] = "NOT_PROVEN"
            record["uncertainty"] = "ENDS_ARE_NOT_A_MEMBER_AND_PROVEN_EXTERNAL_PARTNER"
            unresolved.append(record)
    inbound.sort(key=lambda item: str(item["edge_id"]))
    outbound.sort(key=lambda item: str(item["edge_id"]))
    unresolved.sort(key=lambda item: str(item["edge_id"]))
    return {
        "inbound": inbound,
        "outbound": outbound,
        "unresolved": unresolved,
    }


def traversal_crosscheck_v1(
    unresolved_edges: list[dict[str, Any]],
    traverse_fn: TraverseFn | None,
) -> dict[str, Any]:
    """Depth-1 GHV walk is a countercheck. It does not add edges or members."""

    if traverse_fn is None:
        return {
            "status": "NOT_RUN",
            "used_as_membership_proof": False,
            "used_as_relation_class_replacement": False,
            "max_depth": 1,
        }
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in unresolved_edges:
        ghv_type = record.get("ghv_edge_type")
        if not ghv_type:
            continue
        for endpoint in (record["source_id"], record["target_id"]):
            if endpoint and endpoint not in seen:
                seen.add(endpoint)
                nodes.append({"source_native_id": endpoint})
        edges.append(
            {
                "edge_id": record["edge_id"],
                "source_native_id": record["source_id"],
                "target_native_id": record["target_id"],
                "typed_edge": {"edge_type": ghv_type},
                "causal_traversal_eligible": ghv_type not in {"IMPORTS", "CONFIGURES", "OBSERVES"},
            }
        )
    if not nodes:
        return {
            "status": "NO_TYPED_EDGES",
            "used_as_membership_proof": False,
            "used_as_relation_class_replacement": False,
            "max_depth": 1,
            "causal_only_blocked_edge_ids": [],
        }
    origin = sorted(seen)[0]
    causal = traverse_fn(
        nodes=nodes,
        edges=edges,
        origin_native_id=origin,
        direction="FORWARD",
        causal_only=True,
        max_depth=1,
    )
    return {
        "status": "CROSSCHECK_ONLY",
        "used_as_membership_proof": False,
        "used_as_relation_class_replacement": False,
        "max_depth": 1,
        "origin_native_id": origin,
        "causal_only_blocked_edge_ids": list(causal.blocked_non_causal),
        "reachable_native_ids": list(causal.reachable_native_ids),
    }
