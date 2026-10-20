"""AST verifier for six Double Play call edges. AUTHORITY=NONE. No traversal."""

from __future__ import annotations

import ast
from typing import Any, Mapping

SCHEMA_ID = "DOUBLE_PLAY_GRAPH_BINDING_VERIFIER_V1"
TOOL_IDENTITY = "DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH"
EXPECTED_BASELINE_SHA = "97c8c954204c15f9af5a48995b889ce3fb223c64"
EXPECTED_BASELINE_TREE = "898ede79de7e527db3632b8a3b32daf8b9b098b8"
FROZEN_SNAPSHOT_ID = "58f855c9c9818a78849859613c33148e"
CENSUS_NATIVE_ID = "SO-OPS-PKG:double_play"
FUNCTION_SYMBOLS = (
    "run_current_productive_master_v2_runtime_cycle_v1",
    "run_integrated_offline_trading_logic_replay_v1",
    "transition_state",
    "update_dynamic_boundaries",
    "RuntimeScopeState",
    "evaluate_double_play_entry_exit_policy_v0",
    "commit_host_dynamic_scope_after_replay_v1",
    "persist_dynamic_scope_state_atomic_v1",
)
REQUIRED_EDGES = (
    (
        "run_current_productive_master_v2_runtime_cycle_v1",
        "run_integrated_offline_trading_logic_replay_v1",
    ),
    (
        "run_integrated_offline_trading_logic_replay_v1",
        "update_dynamic_boundaries",
    ),
    (
        "run_integrated_offline_trading_logic_replay_v1",
        "transition_state",
    ),
    (
        "run_integrated_offline_trading_logic_replay_v1",
        "evaluate_double_play_entry_exit_policy_v0",
    ),
    (
        "commit_host_dynamic_scope_after_replay_v1",
        "persist_dynamic_scope_state_atomic_v1",
    ),
    (
        "run_bridge_cycle_v1",
        "commit_host_dynamic_scope_after_replay_v1",
    ),
)
SOURCE_FILES = {
    "cycle": (
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_master_v2_runtime_cycle_v1.py"
    ),
    "replay": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "double_play_state": "src/trading/master_v2/double_play_state.py",
    "entry_exit_policy": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "host_binding": "src/ops/dynamic_scope_persistence_binding_v1/host_binding_v1.py",
    "persistence": "src/ops/dynamic_scope_persistence_binding_v1/persistence_v1.py",
    "bridge": (
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
        "decision_economics_cycle_bridge_v1.py"
    ),
}
FORBIDDEN_OUTPUT_KEYS = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)


def verify_double_play_graph_v1(
    *,
    current_sha: str,
    current_tree: str,
    sources: Mapping[str, str | None],
    composed_graph: Mapping[str, Any] | None,
    integrated_graph: Mapping[str, Any] | None,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    claim_map = dict(claims or {})
    if any(
        claim_map.get(name) not in (None, "NONE") for name in ("authority", "trading_authority")
    ):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    if claim_map.get("dynamic_scope_separate_universe") is True:
        reasons.append("UNAUTHORIZED_UNIVERSE_CLAIM")
    if claim_map.get("treat_ops_census_node_as_trading_symbol") is True:
        reasons.append("OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL")
    if claim_map.get("treat_missing_graph_symbol_as_isolation") is True:
        reasons.append("MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF")
    if claim_map.get("persists_edge_requested") is True:
        reasons.append("UNSUPPORTED_PERSISTS_CLAIM")
    if _contains_forbidden_key(claim_map):
        reasons.append("OVERALL_PASS_FORBIDDEN")
    if current_sha != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if current_tree != EXPECTED_BASELINE_TREE:
        reasons.append("BASELINE_TREE_MISMATCH")

    parsed, malformed = _parse_sources(sources, reasons)
    symbols = _defined_symbols(parsed)
    missing_symbols = [name for name in FUNCTION_SYMBOLS if name not in symbols]
    if missing_symbols and not malformed:
        reasons.append("MISSING_SYMBOL")
    edges = [] if malformed else _match_edges(parsed)
    found_pairs = {(row["SOURCE"], row["TARGET"]) for row in edges}
    missing_edges = [
        {"SOURCE": source, "TARGET": target, "VERIFICATION_STATUS": "MISSING"}
        for source, target in REQUIRED_EDGES
        if (source, target) not in found_pairs
    ]
    if missing_edges and not malformed:
        reasons.append("MISSING_CALL")
    membership, census = _membership(composed_graph, integrated_graph, reasons)

    unique = tuple(dict.fromkeys(reasons))
    report: dict[str, Any] = {
        "SCHEMA_ID": SCHEMA_ID,
        "TOOL_IDENTITY": TOOL_IDENTITY,
        "AUTHORITY": "NONE",
        "TRADING_AUTHORITY": "NONE",
        "SAFETY_AUTHORITY": "NONE",
        "EXECUTION_AUTHORITY": "NONE",
        "GRAPH_READY": False,
        "VERIFICATION_STATUS": "REJECTED" if unique else "REPORTED",
        "REJECTION_REASONS": list(unique),
        "CONFIRMED_SYMBOLS": [name for name in FUNCTION_SYMBOLS if name in symbols],
        "MISSING_SYMBOLS": missing_symbols,
        "LOGICAL_EDGE_COUNT": len(found_pairs),
        "VERIFIED_EDGES": edges,
        "MISSING_EDGES": missing_edges,
        "FROZEN_GRAPH_SYMBOLS": membership,
        "CENSUS_NODE_OBSERVED": census,
        "CENSUS_NODE_IS_TRADING_SYMBOL": False,
        "ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF": False,
        "TRAVERSAL_EXECUTED": False,
        "GRAPH_REBUILT": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
    }
    _assert_no_forbidden_keys(report)
    return report


def _parse_sources(
    sources: Mapping[str, str | None],
    reasons: list[str],
) -> tuple[dict[str, ast.AST], bool]:
    parsed: dict[str, ast.AST] = {}
    malformed = False
    for role in SOURCE_FILES:
        text = sources.get(role)
        if not isinstance(text, str) or not text:
            reasons.append("MISSING_REQUIRED_EVIDENCE")
            continue
        try:
            parsed[role] = ast.parse(text)
        except SyntaxError:
            malformed = True
            reasons.append("MALFORMED_AST")
    return parsed, malformed


def _defined_symbols(parsed: Mapping[str, ast.AST]) -> set[str]:
    found: set[str] = set()
    for tree in parsed.values():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in FUNCTION_SYMBOLS:
                    found.add(node.name)
    return found


def _match_edges(parsed: Mapping[str, ast.AST]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    required = set(REQUIRED_EDGES)
    for role, tree in parsed.items():
        parents = _parents(tree)
        for call in _calls(tree):
            target = _callee_name(call)
            function = _enclosing_function(call, parents)
            if target is None or function is None:
                continue
            pair = (function.name, target)
            if pair not in required:
                continue
            rows.append(_edge_row(role, function, call, parents))
    rows.sort(key=lambda row: (row["SOURCE"], row["TARGET"], row["LINE"], row["COLUMN"]))
    return rows


def _edge_row(
    role: str,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
    parents: dict[ast.AST, ast.AST],
) -> dict[str, Any]:
    target = _callee_name(call) or ""
    condition = _condition(call, parents)
    reachability = (
        "NOT_ASSESSED" if _return_precedes(function, call.lineno) else "NO_EARLIER_RETURN_OBSERVED"
    )
    productive = "NOT_APPLICABLE"
    if target == "commit_host_dynamic_scope_after_replay_v1":
        productive = "CONDITIONAL"
    if target == "persist_dynamic_scope_state_atomic_v1":
        productive = "CONDITIONAL"
    return {
        "SOURCE": function.name,
        "TARGET": target,
        "EDGE_TYPE": "CALLS",
        "SOURCE_FILE": SOURCE_FILES[role],
        "SOURCE_FUNCTION": function.name,
        "LINE": call.lineno,
        "COLUMN": _column(call),
        "CONDITION": condition,
        "REACHABILITY": reachability,
        "PRODUCTIVE_PERSISTENCE": productive,
        "EVIDENCE_CLASS": "CURRENT_CODE",
        "VERIFICATION_STATUS": "VERIFIED",
    }


def _calls(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def _callee_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _column(call: ast.Call) -> int:
    return call.func.col_offset + 1


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _enclosing_function(
    node: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current: ast.AST | None = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def _condition(call: ast.Call, parents: Mapping[ast.AST, ast.AST]) -> str:
    parts: list[str] = []
    current: ast.AST | None = call
    seen: set[int] = set()
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.If) and id(parent) not in seen:
            branch = _branch(parent, call, parents)
            if branch == "body":
                parts.append(ast.unparse(parent.test))
            elif branch == "orelse":
                parts.append(_negate(parent.test))
            seen.add(id(parent))
        current = parent
    parts.reverse()
    return " and ".join(parts) if parts else "DIRECT"


def _branch(
    if_node: ast.If,
    target: ast.AST,
    parents: Mapping[ast.AST, ast.AST],
) -> str | None:
    current: ast.AST | None = target
    while current is not None and current is not if_node:
        if current in if_node.body:
            return "body"
        if current in if_node.orelse:
            return "orelse"
        current = parents.get(current)
    return None


def _negate(test: ast.expr) -> str:
    if (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    ):
        left = ast.unparse(test.left)
        if isinstance(test.ops[0], ast.IsNot):
            return f"{left} is None"
        if isinstance(test.ops[0], ast.Is):
            return f"{left} is not None"
    return f"not ({ast.unparse(test)})"


def _return_precedes(function: ast.FunctionDef | ast.AsyncFunctionDef, line: int) -> bool:
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Return) and getattr(node, "lineno", line) < line:
            return True
        stack.extend(ast.iter_child_nodes(node))
    return False


def _membership(
    composed: Mapping[str, Any] | None,
    integrated: Mapping[str, Any] | None,
    reasons: list[str],
) -> tuple[list[dict[str, str]], bool]:
    unknown = [{"SYMBOL": name, "PRESENCE": "UNKNOWN"} for name in FUNCTION_SYMBOLS]
    if not isinstance(composed, Mapping) or not isinstance(integrated, Mapping):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
        return unknown, False
    left_reasons = _graph_binding(composed)
    right_reasons = _graph_binding(integrated)
    reasons.extend(left_reasons)
    reasons.extend(right_reasons)
    if left_reasons or right_reasons:
        return unknown, False
    left = _native_ids(composed)
    right = _native_ids(integrated)
    left_symbols = tuple(name in left for name in FUNCTION_SYMBOLS)
    right_symbols = tuple(name in right for name in FUNCTION_SYMBOLS)
    if left_symbols != right_symbols:
        reasons.append("GRAPH_PRESENCE_CONFLICT")
        return unknown, CENSUS_NATIVE_ID in left or CENSUS_NATIVE_ID in right
    rows = [
        {"SYMBOL": name, "PRESENCE": "PRESENT" if name in left else "UNKNOWN"}
        for name in FUNCTION_SYMBOLS
    ]
    return rows, CENSUS_NATIVE_ID in left and CENSUS_NATIVE_ID in right


def _graph_binding(graph: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if graph.get("snapshot_id") != FROZEN_SNAPSHOT_ID:
        reasons.append("SNAPSHOT_ID_MISMATCH")
    code_snapshot = graph.get("code_snapshot")
    head = code_snapshot.get("git_head") if isinstance(code_snapshot, dict) else None
    if head != EXPECTED_BASELINE_SHA:
        reasons.append("BASELINE_SHA_MISMATCH")
    if graph.get("authority") not in (None, "NONE"):
        reasons.append("UNAUTHORIZED_AUTHORITY_CLAIM")
    if not isinstance(graph.get("nodes"), list):
        reasons.append("MISSING_REQUIRED_EVIDENCE")
    return reasons


def _native_ids(graph: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return found
    for node in nodes:
        if not isinstance(node, dict):
            continue
        native = node.get("source_native_id")
        if isinstance(native, str):
            found.add(native)
        provenance = node.get("provenance")
        if isinstance(provenance, dict) and isinstance(provenance.get("NATIVE_ID"), str):
            found.add(provenance["NATIVE_ID"])
    return found


def _contains_forbidden_key(payload: object) -> bool:
    if isinstance(payload, dict):
        return any(
            key in FORBIDDEN_OUTPUT_KEYS or _contains_forbidden_key(value)
            for key, value in payload.items()
        )
    if isinstance(payload, list):
        return any(_contains_forbidden_key(item) for item in payload)
    return False


def _assert_no_forbidden_keys(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in FORBIDDEN_OUTPUT_KEYS:
                raise RuntimeError("FORBIDDEN_OUTPUT_KEY")
            _assert_no_forbidden_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_forbidden_keys(item)
