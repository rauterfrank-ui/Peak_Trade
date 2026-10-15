"""Typed edge normalization."""

from __future__ import annotations

from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    CAUSAL_EDGE_TYPES,
    STRUCTURAL_EDGE_TYPES,
)

ALL_TYPED_EDGE_TYPES = CAUSAL_EDGE_TYPES | STRUCTURAL_EDGE_TYPES


def census_flow_to_typed_edge(edge: dict[str, Any]) -> tuple[str | None, str]:
    flow = str(edge.get("flow_type") or "")
    contract = edge.get("contract_or_payload")
    if flow == "DECISION_FLOW":
        if contract and str(contract).strip():
            return "HANDOFF", "CONTRACT_EVIDENCE"
        return None, "UNRESOLVED_DECISION_FLOW_WITHOUT_CONTRACT"
    if flow in {"DATA_FLOW", "OBSERVATION_FLOW"}:
        return "PRODUCES", "CONTRACT_EVIDENCE"
    if flow == "EVIDENCE_FLOW":
        return "OBSERVES", "CONTRACT_EVIDENCE"
    return None, f"UNRESOLVED_FLOW_TYPE:{flow}"


def atlas_relation_to_typed_edge(rel: dict[str, Any]) -> tuple[str, bool]:
    rel_type = str(rel.get("type") or "UNKNOWN")
    mapping = {
        "CONTAINS": "CONFIGURES",
        "HAS_FUNCTIONAL_CORE": "CONFIGURES",
        "NAVIGATES_TO": "OBSERVES",
        "SUPERSEDES": "CONFIGURES",
        "DEPENDS_ON": "IMPORTS",
    }
    edge_type = mapping.get(rel_type, "CONFIGURES")
    causal = edge_type in CAUSAL_EDGE_TYPES
    return edge_type, causal


def assert_known_edge_type(edge_type: str) -> None:
    if edge_type not in ALL_TYPED_EDGE_TYPES:
        raise ValueError(f"unknown_edge_type:{edge_type}")


def edge_semantics_flags(edge_type: str) -> dict[str, Any]:
    assert_known_edge_type(edge_type)
    return {
        "edge_type": edge_type,
        "structural_only": edge_type in STRUCTURAL_EDGE_TYPES,
        "causal_propagation_allowed": edge_type in CAUSAL_EDGE_TYPES,
        "trading_authority_implied": False,
    }
