"""Graph authority modes for forensic crosswalk (semantic separation)."""

from __future__ import annotations

from enum import Enum
from typing import Any


class GraphMode(str, Enum):
    STRICT_CURRENT = "STRICT_CURRENT"
    NAVIGATION_ONLY = "NAVIGATION_ONLY"


def parse_graph_mode(*, navigation_only: bool) -> GraphMode:
    if navigation_only:
        return GraphMode.NAVIGATION_ONLY
    return GraphMode.STRICT_CURRENT


def build_graph_authority_coverage(
    *,
    graph_mode: GraphMode,
    source_validation_pass: bool,
    snapshot_binding_verified: bool,
    current_only_filter_applied: bool,
    current_graph_verified: bool,
    causal_closure_proven: bool = False,
    global_non_interference_proven: bool = False,
) -> dict[str, Any]:
    if graph_mode == GraphMode.NAVIGATION_ONLY:
        return {
            "GRAPH_MODE": GraphMode.NAVIGATION_ONLY.value,
            "GRAPH_AUTHORITY": "NAVIGATION_ONLY",
            "SNAPSHOT_BINDING_VERIFIED": False,
            "CURRENT_ONLY_FILTER_APPLIED": current_only_filter_applied,
            "CURRENT_GRAPH_VERIFIED": False,
            "CURRENT_ONLY_GRAPH": False,
            "SOURCE_VALIDATION_PASS": source_validation_pass,
            "CAUSAL_CLOSURE_PROVEN": False,
            "GLOBAL_NON_INTERFERENCE_PROVEN": False,
        }
    return {
        "GRAPH_MODE": GraphMode.STRICT_CURRENT.value,
        "GRAPH_AUTHORITY": "STRICT_CURRENT",
        "SNAPSHOT_BINDING_VERIFIED": snapshot_binding_verified,
        "CURRENT_ONLY_FILTER_APPLIED": current_only_filter_applied,
        "CURRENT_GRAPH_VERIFIED": current_graph_verified,
        "CURRENT_ONLY_GRAPH": current_graph_verified,
        "SOURCE_VALIDATION_PASS": source_validation_pass,
        "CAUSAL_CLOSURE_PROVEN": causal_closure_proven,
        "GLOBAL_NON_INTERFERENCE_PROVEN": global_non_interference_proven,
    }
