"""Deterministic report assembly. Status cannot ratify a universe boundary."""

from __future__ import annotations

import json
from typing import Any

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    ALLOWED_BOUNDARY_STATUSES,
    AUTHORITY,
    FORBIDDEN_BOUNDARY_STATUSES,
    GRAPH_PROJECTION_AUTHORITY,
    PROJECTOR_ID,
    RUNTIME_AUTHORIZATION_EFFECT,
    TARGET_IDENTITY,
    TRADING_AUTHORITY,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
)


def decide_boundary_status_v1(
    *,
    causal_graph_verified: bool,
    proven_count: int,
    resolved_count: int,
) -> str:
    if not causal_graph_verified:
        return "BLOCKED_BY_EVIDENCE"
    if proven_count == 0 and resolved_count == 0:
        return "NOT_PROVEN"
    return "PARTIAL"


def coerce_boundary_status_v1(status: str) -> str:
    if status in FORBIDDEN_BOUNDARY_STATUSES:
        raise ProjectorFailClosedV1("FORBIDDEN_STATUS", status)
    if status not in ALLOWED_BOUNDARY_STATUSES:
        raise ProjectorFailClosedV1("UNKNOWN_STATUS", status)
    return status


def canonical_json_v1(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def assemble_report_v1(parts: dict[str, Any]) -> dict[str, Any]:
    status = coerce_boundary_status_v1(str(parts["boundary_status"]))
    report = {
        "PROJECTOR_ID": PROJECTOR_ID,
        "AUTHORITY": AUTHORITY,
        "TRADING_AUTHORITY": TRADING_AUTHORITY,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "GRAPH_PROJECTION_AUTHORITY": GRAPH_PROJECTION_AUTHORITY,
        "UNIVERSE_RATIFICATION": False,
        "CURRENT_BASELINE": {
            "commit": parts["commit"],
            "tree": parts["tree"],
        },
        "TARGET_UNIVERSE": TARGET_IDENTITY,
        "SCOPE_MANIFEST": parts["scope_manifest"],
        "PROVEN_MEMBERS": parts["proven_members"],
        "UNCLASSIFIED_CANDIDATES": parts["unclassified_candidates"],
        "EXTERNAL_BOUNDARY_PARTNERS": parts["external_boundary_partners"],
        "INBOUND_BOUNDARY_EDGES": parts["inbound_boundary_edges"],
        "OUTBOUND_BOUNDARY_EDGES": parts["outbound_boundary_edges"],
        "UNRESOLVED_EDGES": parts["unresolved_edges"],
        "UNRESOLVED_COMPONENTS": parts["unresolved_components"],
        "SOURCE_PROVENANCE": parts["source_provenance"],
        "COVERAGE": parts["coverage"],
        "UNCERTAINTIES": parts["uncertainties"],
        "COUNTERCHECK_RESULTS": parts["countercheck_results"],
        "BOUNDARY_VERIFICATION_STATUS": status,
        "RESOLVER_ID": parts["resolver_id"],
        "INPUT_SCOPE": parts["input_scope"],
        "RESOLVED_SYMBOL_ENDPOINTS": parts["resolved_symbol_endpoints"],
        "PROVEN_SYMBOL_RELATIONS": parts["proven_symbol_relations"],
        "UNRESOLVED_SYMBOL_ENDPOINTS": parts["unresolved_symbol_endpoints"],
        "ORIGINAL_FLOW_PRESERVATION": parts["original_flow_preservation"],
    }
    _reject_forbidden_values(report)
    return report


def _reject_forbidden_values(value: object) -> None:
    if isinstance(value, str):
        if value in FORBIDDEN_BOUNDARY_STATUSES:
            raise ProjectorFailClosedV1("FORBIDDEN_STATUS", value)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_forbidden_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_forbidden_values(item)
