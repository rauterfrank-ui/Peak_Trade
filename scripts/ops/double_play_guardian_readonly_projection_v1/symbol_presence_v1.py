"""Frozen-graph symbol presence. AUTHORITY=NONE. No traversal and no new graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.double_play_guardian_readonly_projection_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    FORBIDDEN_OUTPUT_KEYS,
)
from scripts.ops.double_play_guardian_readonly_projection_v1.extract_v1 import (
    read_json_object_v1,
)

SCHEMA_ID = "DOUBLE_PLAY_FROZEN_GRAPH_SYMBOL_PRESENCE_V1"
SCHEMA_VERSION = 1
FROZEN_SNAPSHOT_ID = "58f855c9c9818a78849859613c33148e"
FUNCTION_SYMBOLS = (
    "double_play_state",
    "evaluate_double_play_entry_exit_policy_v0",
)
INTERNAL_EDGE_ENDPOINTS = frozenset({"double_play_state", "transition_state"})
CENSUS_NATIVE_ID = "SO-OPS-PKG:double_play"
_PRESENCE_VALUES = frozenset({"PRESENT", "UNKNOWN"})


def load_frozen_graph_v1(path: Path) -> dict[str, Any] | None:
    try:
        return read_json_object_v1(path)
    except json.JSONDecodeError:
        return None


def project_frozen_graph_symbol_presence_v1(
    *,
    composed_graph: Mapping[str, Any] | None,
    integrated_graph: Mapping[str, Any] | None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    if claim_map.get("treat_ops_census_node_as_trading_symbol") is True:
        reasons.append("OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL")
    if claim_map.get("treat_missing_graph_symbol_as_isolation") is True:
        reasons.append("MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF")

    composed = _as_graph(composed_graph)
    integrated = _as_graph(integrated_graph)
    if composed is None or integrated is None:
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return _report(reasons, None, None, False)

    for graph in (composed, integrated):
        reasons.extend(_binding_reasons(graph))

    composed_view = _graph_view(composed)
    integrated_view = _graph_view(integrated)
    if composed_view != integrated_view:
        reasons.append("GRAPH_PRESENCE_CONFLICT")
        return _report(reasons, None, None, composed_view["census"])

    unique = tuple(dict.fromkeys(reasons))
    return _report(list(unique), composed_view, integrated_view, composed_view["census"])


def _as_graph(payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if not isinstance(payload.get("nodes"), list) or not isinstance(payload.get("edges"), list):
        return None
    return dict(payload)


def _binding_reasons(graph: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if graph.get("snapshot_id") != FROZEN_SNAPSHOT_ID:
        reasons.append("SNAPSHOT_ID_MISMATCH")
    code_snapshot = graph.get("code_snapshot")
    head = code_snapshot.get("git_head") if isinstance(code_snapshot, dict) else None
    if head != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if graph.get("authority") != "NONE":
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    return reasons


def _graph_view(graph: Mapping[str, Any]) -> dict[str, Any]:
    native_ids = _native_ids(graph)
    symbols = {symbol: _presence(symbol in native_ids) for symbol in FUNCTION_SYMBOLS}
    return {
        "symbols": symbols,
        "internal_edge": _internal_edge(graph, native_ids),
        "census": CENSUS_NATIVE_ID in native_ids,
    }


def _native_ids(graph: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    for node in graph["nodes"]:
        if not isinstance(node, dict):
            continue
        native = node.get("source_native_id")
        if isinstance(native, str):
            found.add(native)
        provenance = node.get("provenance")
        if isinstance(provenance, dict) and isinstance(provenance.get("NATIVE_ID"), str):
            found.add(provenance["NATIVE_ID"])
    return found


def _presence(found: bool) -> str:
    return "PRESENT" if found else "UNKNOWN"


def _internal_edge(graph: Mapping[str, Any], native_ids: set[str]) -> str:
    if not INTERNAL_EDGE_ENDPOINTS.issubset(native_ids):
        return "UNKNOWN"
    for edge in graph["edges"]:
        if not isinstance(edge, dict):
            continue
        pair = {edge.get("source_native_id"), edge.get("target_native_id")}
        if pair == INTERNAL_EDGE_ENDPOINTS:
            return "PRESENT"
    return "UNKNOWN"


def _report(
    reasons: list[str],
    composed_view: dict[str, Any] | None,
    integrated_view: dict[str, Any] | None,
    census_observed: bool,
) -> dict[str, Any]:
    unique = tuple(dict.fromkeys(reasons))
    view = composed_view if composed_view is not None and composed_view == integrated_view else None
    if view is None:
        symbols = [{"SYMBOL": symbol, "PRESENCE": "UNKNOWN"} for symbol in FUNCTION_SYMBOLS]
        internal_edge = "UNKNOWN"
    else:
        symbols = [
            {"SYMBOL": symbol, "PRESENCE": view["symbols"][symbol]} for symbol in FUNCTION_SYMBOLS
        ]
        internal_edge = view["internal_edge"]
    for row in symbols:
        if row["PRESENCE"] not in _PRESENCE_VALUES:
            raise RuntimeError("PRESENCE_CONTRACT")
    if internal_edge not in _PRESENCE_VALUES:
        raise RuntimeError("PRESENCE_CONTRACT")
    report: dict[str, Any] = {
        "SCHEMA_ID": SCHEMA_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "AUTHORITY": "NONE",
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "SNAPSHOT_ID": FROZEN_SNAPSHOT_ID,
        "PROJECTION_STATUS": "REJECTED" if unique else "REPORTED",
        "REJECTION_REASONS": list(unique),
        "SYMBOLS": symbols,
        "INTERNAL_DYNAMIC_SCOPE_EDGE": internal_edge,
        "CENSUS_NODE_OBSERVED": census_observed,
        "CENSUS_NODE_IS_TRADING_SYMBOL": False,
        "ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF": False,
        "TRAVERSAL_EXECUTED": False,
        "GRAPH_REBUILT": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "DOMAIN_COVERAGE_STATUS": "NOT_PROVEN",
    }
    _assert_no_forbidden_keys(report)
    return report


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
