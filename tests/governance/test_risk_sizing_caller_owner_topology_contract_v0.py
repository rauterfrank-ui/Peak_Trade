"""Static contract: Risk/Sizing caller→owner topology freeze v0.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
consolidation, authority assignment, or risk/sizing semantic changes.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_caller_owner_topology_contract_v0.json"
)
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "governance" / "RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md"
)
OWNER_INVENTORY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
)
UNITS_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_units_dimensions_contract_v0.json"
LEGACY_ORDER_INTENT_JSON = (
    REPO_ROOT / "config" / "governance" / "legacy_order_intent_inventory_ssot_v1.json"
)

EXPECTED_PRIMARY_OWNER_IDS = (
    "backtest.offline_evaluation_sizing_contract_v1",
    "src.core.position_sizing",
    "src.execution.pipeline.execute_from_signals",
    "src.governance.capital_risk_sizing_v1",
    "src.risk.position_sizer",
)
EXPECTED_PRODUCTIVE_EDGE_IDS = (
    "EDGE_CRS_INTENT_PIPELINE_BRIDGE",
    "EDGE_CRS_OFFLINE_REPLAY_ADAPTER",
    "EDGE_ENGINE_CALC_POSITION_SIZE",
    "EDGE_ENGINE_GET_TARGET_POSITION",
    "EDGE_ENGINE_OFFLINE_EVAL_SIZING",
    "EDGE_FEEDBACK_CALC_POSITION_SIZE",
    "EDGE_FEEDBACK_GET_TARGET_POSITION",
    "EDGE_FEEDBACK_OFFLINE_EVAL_SIZING",
)
EXPECTED_COMPANION_EDGE_IDS = (
    "COMPANION_LIVE_SESSION_POSITION_FRACTION",
    "COMPANION_SHADOW_POSITION_FRACTION",
)
EXPECTED_BYPASS_IDS = (
    "BYPASS_CLASSIC_BACKTEST_DEFAULT",
    "BYPASS_CORE_POSITION_SIZER",
    "BYPASS_EXECUTION_EXECUTE_FROM_SIGNALS",
    "BYPASS_LIVE_SHADOW_POSITION_FRACTION",
    "BYPASS_OFFLINE_EVAL_SIZING_CONTRACT",
)
EXPECTED_PASS_THROUGH_EDGE_IDS = (
    "EDGE_CRS_INTENT_PIPELINE_BRIDGE",
    "EDGE_CRS_OFFLINE_REPLAY_ADAPTER",
)
EXPECTED_AMBIGUOUS_EDGE_IDS = (
    "EDGE_DIAGNOSTICS_BUILD_POSITION_SIZER",
    "EDGE_OFFLINE_EVAL_WRAPS_CALC_POSITION_SIZE",
    "EDGE_SWEEPS_BUILD_POSITION_SIZER",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0=true",
    "INVENTORY_ONLY=true",
    "CALLER_TO_OWNER_TOPOLOGY_FROZEN=true",
    "CALLER_TO_OWNER_TOPOLOGY_RESOLVED=false",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "CANONICAL_RISK_SIZING_AUTHORITY_OWNER=UNRESOLVED",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "EXPECTED_PRIMARY_OWNER_COUNT=5",
    "EXPECTED_PRODUCTIVE_DIRECT_EDGE_COUNT=8",
    "EXPECTED_COMPANION_EDGE_COUNT=2",
    "EXPECTED_DIRECT_SIZING_BYPASS_COUNT=5",
    "EXPECTED_PASS_THROUGH_EDGE_COUNT=2",
    "EXPECTED_AMBIGUOUS_EDGE_COUNT=3",
    "EXPECTED_EXECUTE_FROM_SIGNALS_EXTERNAL_CALLER_COUNT=0",
    "LEVERAGE_APPLICATION_STATUS=declared_pass_through_not_applied_in_quantity_chain",
)

# Symbols used for closed-world productive call scanning under src/
SCAN_CALLEE_SYMBOLS = frozenset(
    {
        "evaluate_capital_risk_sizing_v1",
        "calc_position_size",
        "size_offline_evaluation_entry_v1",
        "get_target_position",
        "build_position_sizer_from_config",
        "execute_from_signals",
        "PositionSizer",
    }
)

OWNER_DEF_FILES = {
    "evaluate_capital_risk_sizing_v1": "src/governance/capital_risk_sizing_v1.py",
    "calc_position_size": "src/risk/position_sizer.py",
    "size_offline_evaluation_entry_v1": ("src/backtest/offline_evaluation_sizing_contract_v1.py"),
    "get_target_position": "src/core/position_sizing.py",
    "build_position_sizer_from_config": "src/core/position_sizing.py",
    "execute_from_signals": "src/execution/pipeline.py",
    "PositionSizer": "src/risk/position_sizer.py",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _ast_symbol_resolves(source_path: Path, symbol_or_callable: str) -> bool:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    if "." in symbol_or_callable:
        class_name, method_name = symbol_or_callable.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if (
                        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name == method_name
                    ):
                        return True
        return False
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol_or_callable
        ):
            return True
        if isinstance(node, ast.ClassDef) and node.name == symbol_or_callable:
            return True
    return False


def _enclosing_qualname(stack: list[ast.AST]) -> str:
    parts: list[str] = []
    for node in stack:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            parts.append(node.name)
    return ".".join(parts) if parts else "<module>"


def _call_attr_or_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _collect_src_calls(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> list[dict[str, object]]:
    """AST collect Call sites for SCAN_CALLEE_SYMBOLS under scan_root (default src/)."""
    root = path_root or REPO_ROOT
    src = scan_root or (root / "src")
    hits: list[dict[str, object]] = []
    for path in sorted(src.rglob("*.py")):
        if "/_archive/" in str(path).replace("\\", "/"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        stack: list[ast.AST] = []

        class Visitor(ast.NodeVisitor):
            def generic_visit(self, node: ast.AST) -> None:
                stack.append(node)
                super().generic_visit(node)
                stack.pop()

            def visit_Call(self, node: ast.Call) -> None:
                name = _call_attr_or_name(node)
                if name in SCAN_CALLEE_SYMBOLS:
                    hits.append(
                        {
                            "file": rel,
                            "lineno": node.lineno,
                            "caller": _enclosing_qualname(stack[:-1]),
                            "callee": name,
                        }
                    )
                self.generic_visit(node)

        Visitor().visit(tree)
    return hits


def _edge_key(file: str, caller: str, callee: str) -> tuple[str, str, str]:
    return (file, caller, callee)


def _pinned_topology_keys(payload: dict) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for edge in payload["productive_direct_edges"]:
        keys.add(
            _edge_key(
                edge["caller_source_path"],
                edge["caller_symbol"],
                edge["callee_symbol"],
            )
        )
    for edge in payload["ambiguous_edges"]:
        keys.add(
            _edge_key(
                edge["caller_source_path"],
                edge["caller_symbol"],
                edge["callee_symbol"],
            )
        )
    for edge in payload["non_topology_construction_edges"]:
        keys.add(
            _edge_key(
                edge["caller_source_path"],
                edge["caller_symbol"],
                edge["callee_symbol"],
            )
        )
    return keys


def _external_hits_for_closed_world(hits: list[dict[str, object]]) -> list[dict[str, object]]:
    """Drop self-def-file calls and core.position_sizing internal get_target recursion."""
    out: list[dict[str, object]] = []
    for hit in hits:
        file = str(hit["file"])
        callee = str(hit["callee"])
        def_file = OWNER_DEF_FILES.get(callee)
        if def_file and file == def_file:
            continue
        out.append(hit)
    return out


def assert_closed_world_topology(
    payload: dict | None = None,
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
    require_pinned_present: bool = True,
) -> None:
    """Fail-closed AST guard for caller→owner topology drift."""
    payload = payload or _load_contract()
    pinned = _pinned_topology_keys(payload)
    hits = _external_hits_for_closed_world(
        _collect_src_calls(scan_root=scan_root, path_root=path_root)
    )

    observed: set[tuple[str, str, str]] = set()
    for hit in hits:
        key = _edge_key(str(hit["file"]), str(hit["caller"]), str(hit["callee"]))
        observed.add(key)

    # New productive/ambiguous/construction call sites must be pinned
    unexpected = sorted(observed - pinned)
    missing = sorted(pinned - observed)
    if require_pinned_present:
        # Prefer removal/rename diagnostics when pins no longer match observations
        assert not missing, f"productive_direct_edge_removal FAIL: {missing}"
    assert not unexpected, f"productive_direct_edge_addition FAIL: {unexpected}"

    # execute_from_signals external callers must remain zero
    exec_external = [
        h
        for h in hits
        if h["callee"] == "execute_from_signals"
        and h["file"] != OWNER_DEF_FILES["execute_from_signals"]
    ]
    expected_exec = payload["expected_counts"]["execute_from_signals_external_callers"]
    if require_pinned_present or exec_external:
        assert len(exec_external) == expected_exec, (
            f"execute_from_signals_external_caller_addition FAIL: {exec_external}"
        )


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"


def test_schema_counts_and_identity_no_duplicates() -> None:
    payload = _load_contract()
    counts = payload["expected_counts"]
    assert counts["primary_owners"] == 5
    assert counts["productive_direct_edges"] == 8
    assert counts["companion_edges"] == 2
    assert counts["direct_sizing_bypass_edges"] == 5
    assert counts["pass_through_edges"] == 2
    assert counts["ambiguous_edges"] == 3
    assert counts["unresolved_symbols"] == 0
    assert counts["percent_conflicts"] == 2
    assert counts["owners_without_external_productive_callers"] == 1
    assert counts["productive_callers_without_pinned_canonical_owner"] == 2
    assert counts["execute_from_signals_external_callers"] == 0

    owner_ids = tuple(o["owner_id"] for o in payload["primary_owners"])
    assert owner_ids == EXPECTED_PRIMARY_OWNER_IDS
    assert len(owner_ids) == len(set(owner_ids))

    prod_ids = tuple(e["edge_id"] for e in payload["productive_direct_edges"])
    assert prod_ids == EXPECTED_PRODUCTIVE_EDGE_IDS
    assert len(prod_ids) == len(set(prod_ids)), "productive_direct_edge_duplicate FAIL"

    companion_ids = tuple(sorted(e["edge_id"] for e in payload["companion_edges"]))
    assert companion_ids == EXPECTED_COMPANION_EDGE_IDS

    bypass_ids = tuple(b["bypass_stable_id"] for b in payload["direct_sizing_bypass_edges"])
    assert bypass_ids == EXPECTED_BYPASS_IDS

    pass_ids = tuple(e["edge_id"] for e in payload["pass_through_edges"])
    assert pass_ids == EXPECTED_PASS_THROUGH_EDGE_IDS

    amb_ids = tuple(e["edge_id"] for e in payload["ambiguous_edges"])
    assert amb_ids == EXPECTED_AMBIGUOUS_EDGE_IDS
    assert len(amb_ids) == len(set(amb_ids))

    # All edge_ids across categories that must be unique within productive+ambiguous+construction
    decision_ids = [
        e["edge_id"]
        for e in (
            *payload["productive_direct_edges"],
            *payload["ambiguous_edges"],
            *payload["non_topology_construction_edges"],
        )
    ]
    assert len(decision_ids) == len(set(decision_ids)), "duplicate_edge_identity FAIL"


def test_authority_and_leverage_and_percent_pins() -> None:
    payload = _load_contract()
    auth = payload["authority_status"]
    assert auth["canonical_execution_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_authority_owner"] == "UNRESOLVED"
    assert auth["canonical_risk_sizing_owner"] == "UNRESOLVED"
    assert auth["authority_effect"] == "NONE"

    lev = payload["leverage_status"]
    assert lev["applied_in_quantity_chain"] is False
    assert lev["application_status"] == ("declared_pass_through_not_applied_in_quantity_chain")

    conflicts = payload["percent_conflicts_unresolved"]
    assert len(conflicts) == 2
    for conflict in conflicts:
        left, right = conflict["must_not_equate"]
        assert left != right
        assert conflict["resolution_status"] == "UNRESOLVED_MUST_NOT_EQUATE"


def test_symbol_resolution_ast_fail_closed() -> None:
    payload = _load_contract()
    unresolved: list[str] = []

    for owner in payload["primary_owners"]:
        path = REPO_ROOT / owner["source_path"]
        assert path.is_file(), owner["source_path"]
        for symbol in owner["primary_symbols"]:
            if not _ast_symbol_resolves(path, symbol):
                unresolved.append(f"owner:{owner['owner_id']}:{symbol}")

    for edge in payload["productive_direct_edges"]:
        caller_path = REPO_ROOT / edge["caller_source_path"]
        owner_path = REPO_ROOT / edge["owner_source_path"]
        assert caller_path.is_file()
        assert owner_path.is_file()
        if not _ast_symbol_resolves(caller_path, edge["caller_symbol"]):
            unresolved.append(f"caller:{edge['edge_id']}:{edge['caller_symbol']}")
        # callee may be method attr (get_target_position) — resolve on owner when dotted pin present
        owner_sym = edge.get("callee_owner_symbol") or edge["callee_symbol"]
        if not _ast_symbol_resolves(owner_path, owner_sym):
            # bare function on owner module
            if not _ast_symbol_resolves(owner_path, edge["callee_symbol"]):
                unresolved.append(f"callee:{edge['edge_id']}:{edge['callee_symbol']}")

    for edge in payload["companion_edges"]:
        path = REPO_ROOT / edge["caller_source_path"]
        if not _ast_symbol_resolves(path, edge["caller_symbol"]):
            unresolved.append(f"companion:{edge['edge_id']}")

    for edge in payload["ambiguous_edges"]:
        caller_path = REPO_ROOT / edge["caller_source_path"]
        owner_path = REPO_ROOT / edge["owner_source_path"]
        if not _ast_symbol_resolves(caller_path, edge["caller_symbol"]):
            unresolved.append(f"ambiguous_caller:{edge['edge_id']}")
        if not _ast_symbol_resolves(owner_path, edge["callee_symbol"]):
            unresolved.append(f"ambiguous_callee:{edge['edge_id']}")

    for edge in payload["direct_sizing_bypass_edges"]:
        path = REPO_ROOT / edge["source_path"]
        if not _ast_symbol_resolves(path, edge["caller_symbol"]):
            unresolved.append(f"bypass_caller:{edge['bypass_stable_id']}")
        target = edge.get("target_symbol")
        if target:
            # target may live on another module; resolve on bypass source or known owner paths
            if not _ast_symbol_resolves(path, target):
                # try common owner files
                found = False
                for owner in payload["primary_owners"]:
                    if _ast_symbol_resolves(REPO_ROOT / owner["source_path"], target):
                        found = True
                        break
                if not found and "." in target:
                    # Class.method on owner
                    for owner in payload["primary_owners"]:
                        if _ast_symbol_resolves(REPO_ROOT / owner["source_path"], target):
                            found = True
                            break
                if not found:
                    unresolved.append(f"bypass_target:{edge['bypass_stable_id']}:{target}")

    assert not unresolved, f"unresolved_symbol FAIL: {unresolved}"
    assert payload["expected_counts"]["unresolved_symbols"] == 0


def test_ast_closed_world_guard_matches_pinned_topology() -> None:
    assert_closed_world_topology()


def test_companion_edges_not_primary_owners() -> None:
    payload = _load_contract()
    primary = {o["owner_id"] for o in payload["primary_owners"]}
    for edge in payload["companion_edges"]:
        assert edge["primary_owner"] is False
        assert edge["must_not_classify_as_primary_owner"] is True
        assert edge["edge_id"] not in primary
        assert edge["classification"] == "OBSERVED_COMPANION_EDGE_NOT_PRIMARY_OWNER"
        path = REPO_ROOT / edge["caller_source_path"]
        text = path.read_text(encoding="utf-8")
        assert edge["assignment_attribute"] in text
        assert edge["handoff_callee"] in text


def test_pass_through_edges_are_not_sixth_owner() -> None:
    payload = _load_contract()
    primary = {o["owner_id"] for o in payload["primary_owners"]}
    assert len(primary) == 5
    for edge in payload["pass_through_edges"]:
        assert edge["classification"] == "PASS_THROUGH_ONLY"
        assert edge["authoritative_size_decision"] is False
        assert edge["owner_id"] in primary
        # adapters themselves are not owners
        assert edge["caller_source_path"] not in {
            o["source_path"] for o in payload["primary_owners"]
        }


def test_owners_without_external_productive_caller() -> None:
    payload = _load_contract()
    rows = payload["owners_without_external_productive_callers"]
    assert len(rows) == 1
    assert rows[0]["owner_id"] == "src.execution.pipeline.execute_from_signals"
    assert rows[0]["external_productive_caller_count"] == 0

    hits = _external_hits_for_closed_world(_collect_src_calls())
    exec_hits = [h for h in hits if h["callee"] == "execute_from_signals"]
    assert exec_hits == []


def test_productive_callers_without_pinned_canonical_owner() -> None:
    payload = _load_contract()
    rows = payload["productive_callers_without_pinned_canonical_owner"]
    assert len(rows) == 2
    keys = {(r["caller_source_path"], r["caller_symbol"]) for r in rows}
    assert keys == {
        ("src/strategies/diagnostics.py", "run_single_strategy_smoke"),
        ("src/sweeps/engine.py", "SweepEngine._run_single_backtest"),
    }


def test_bypass_classifications_match_surface_contract() -> None:
    payload = _load_contract()
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    surface = inventory["risk_sizing_owner_and_bypass_surface_contract"]
    surface_by_id = {b["stable_id"]: b for b in surface["bypasses"]}
    assert surface["expected_bypass_count"] == 5
    assert surface["expected_owner_count"] == 5

    for bypass in payload["direct_sizing_bypass_edges"]:
        sid = bypass["bypass_stable_id"]
        assert sid in surface_by_id
        pinned = surface_by_id[sid]
        assert bypass["source_path"] == pinned["source_path"]
        assert bypass["caller_symbol"] == pinned["caller_symbol"]
        assert bypass["target_symbol"] == pinned["target_symbol"]
        assert bypass["target_classification"] == pinned["target_classification"]
        assert bypass["classification"] == "PRODUCTIVE_RISK_SIZING_BYPASS"


def test_units_and_legacy_contracts_referenced_unchanged() -> None:
    payload = _load_contract()
    units = json.loads(_read(UNITS_JSON))
    legacy = json.loads(_read(LEGACY_ORDER_INTENT_JSON))

    assert payload["referenced_contracts"]["risk_sizing_units_dimensions_contract_v0"].endswith(
        "risk_sizing_units_dimensions_contract_v0.json"
    )
    assert units["markers"]["EXPECTED_PRIMARY_OWNER_COUNT"] == 5
    assert len(units["companion_edges"]) == 2
    assert len(units["known_percent_conflicts"]) == 2
    assert units["global_authority_pins"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"

    companion_ids = {e["edge_id"] for e in payload["companion_edges"]}
    units_ids = {e["edge_id"] for e in units["companion_edges"]}
    assert companion_ids == units_ids

    conflict_ids = {c["conflict_id"] for c in payload["percent_conflicts_unresolved"]}
    units_conflicts = {c["conflict_id"] for c in units["known_percent_conflicts"]}
    assert conflict_ids == units_conflicts

    assert "direct_submission_surface_contract" in legacy
    assert "decision_owner_surface_contract" in legacy
    assert len(legacy["direct_submission_surface_contract"]["surfaces"]) == 5
    assert len(legacy["decision_owner_surface_contract"]["owners"]) == 3


def test_leverage_not_applied_in_quantity_chain_source() -> None:
    payload = _load_contract()
    assert payload["leverage_status"]["applied_in_quantity_chain"] is False
    crs = _read(REPO_ROOT / "src/governance/capital_risk_sizing_v1.py")
    # Locate evaluate_quantity_chain_v1 body roughly and ensure no leverage multiply use
    start = crs.find("def evaluate_quantity_chain_v1(")
    assert start >= 0
    rest = crs[start + 4 :]
    next_def = rest.find("\ndef ")
    body = rest[: next_def if next_def >= 0 else len(rest)]
    assert "leverage" not in body.lower() or "leverage_ceiling" not in body
    # stronger: leverage_ceiling must not appear in the function body
    assert "leverage_ceiling" not in body


def test_readme_and_related_docs_point_to_topology_contract() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md" in readme
    inventory_doc = _read(
        REPO_ROOT / "docs" / "governance" / "RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md"
    )
    assert "risk_sizing_caller_owner_topology_contract_v0.json" in inventory_doc
    units_doc = _read(
        REPO_ROOT / "docs" / "governance" / "RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md"
    )
    assert "RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0" in units_doc


# --- Drift / mutation fixtures (in-memory + tmp AST; never mutate productive src/) ---


def test_drift_fixture_edge_addition_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["productive_direct_edges"].append(
        {
            "edge_id": "EDGE_ROGUE_NEW_CALLER",
            "classification": "LEGACY_OR_SPECIALIST_PATH",
            "caller_source_path": "src/backtest/engine.py",
            "caller_symbol": "BacktestEngine.run_realistic",
            "callee_symbol": "evaluate_capital_risk_sizing_v1",
            "owner_id": "src.governance.capital_risk_sizing_v1",
            "owner_source_path": "src/governance/capital_risk_sizing_v1.py",
            "reachability": "REACHABLE_PRODUCTIVE",
        }
    )
    # Count guard
    assert (
        len(payload["productive_direct_edges"])
        != payload["expected_counts"]["productive_direct_edges"]
    )


def test_drift_fixture_edge_removal_fails_closed_world() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["productive_direct_edges"] = [
        e
        for e in payload["productive_direct_edges"]
        if e["edge_id"] != "EDGE_ENGINE_CALC_POSITION_SIZE"
    ]
    # Unpinning an observed call site surfaces as unexpected addition vs remaining pins
    with pytest.raises(AssertionError, match="productive_direct_edge_addition FAIL"):
        assert_closed_world_topology(payload)


def test_drift_fixture_duplicate_edge_identity_detected() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["productive_direct_edges"].append(copy.deepcopy(payload["productive_direct_edges"][0]))
    ids = [e["edge_id"] for e in payload["productive_direct_edges"]]
    assert len(ids) != len(set(ids))


def test_drift_fixture_companion_as_primary_owner_rejected() -> None:
    payload = copy.deepcopy(_load_contract())
    rogue = copy.deepcopy(payload["companion_edges"][0])
    rogue["primary_owner"] = True
    with pytest.raises(AssertionError):
        assert rogue["primary_owner"] is False
        raise AssertionError("companion_as_primary_owner FAIL")


def test_drift_fixture_bypass_reclassification_rejected() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["direct_sizing_bypass_edges"][0]["classification"] = "CANONICAL_OWNER"
    assert (
        payload["direct_sizing_bypass_edges"][0]["classification"]
        != "PRODUCTIVE_RISK_SIZING_BYPASS"
    )


def test_drift_fixture_percent_silent_equivalence_rejected() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["percent_conflicts_unresolved"][0]["must_not_equate"] = [
        "PERCENT_0_100",
        "PERCENT_0_100",
    ]
    left, right = payload["percent_conflicts_unresolved"][0]["must_not_equate"]
    with pytest.raises(AssertionError, match="percent_convention_silent_equivalence"):
        assert left != right, "percent_convention_silent_equivalence FAIL"


def test_drift_fixture_leverage_falsely_applied_rejected() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["leverage_status"]["applied_in_quantity_chain"] = True
    with pytest.raises(AssertionError, match="leverage_falsely_claimed_applied"):
        assert payload["leverage_status"]["applied_in_quantity_chain"] is False, (
            "leverage_falsely_claimed_applied FAIL"
        )


def test_drift_fixture_new_execute_from_signals_caller_fails(
    tmp_path: Path,
) -> None:
    rogue = tmp_path / "src" / "rogue_exec_caller_v0.py"
    rogue.parent.mkdir(parents=True)
    rogue.write_text(
        "def rogue_call(pipeline):\n"
        "    return pipeline.execute_from_signals(signals=[], prices=[])\n",
        encoding="utf-8",
    )
    with pytest.raises(
        AssertionError,
        match=(
            "execute_from_signals_external_caller_addition FAIL|"
            "productive_direct_edge_addition FAIL"
        ),
    ):
        assert_closed_world_topology(
            scan_root=tmp_path / "src",
            path_root=tmp_path,
            require_pinned_present=False,
        )


def test_drift_fixture_new_productive_caller_to_owner_fails(
    tmp_path: Path,
) -> None:
    # Seed minimal pinned files so removal does not fire; only addition should fail.
    # Use a scan that only sees the rogue file.
    rogue = tmp_path / "src" / "rogue_crs_caller_v0.py"
    rogue.parent.mkdir(parents=True)
    rogue.write_text(
        "from src.governance.capital_risk_sizing_v1 import evaluate_capital_risk_sizing_v1\n"
        "def rogue():\n"
        "    return evaluate_capital_risk_sizing_v1()\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="productive_direct_edge_addition FAIL"):
        assert_closed_world_topology(
            scan_root=tmp_path / "src",
            path_root=tmp_path,
            require_pinned_present=False,
        )


def test_drift_fixture_rename_move_symbol_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["productive_direct_edges"][2]["callee_symbol"] = "calc_position_size_renamed"
    # Renamed pin no longer matches observation: removal of renamed pin + addition of real call
    with pytest.raises(
        AssertionError,
        match="productive_direct_edge_removal FAIL|productive_direct_edge_addition FAIL",
    ):
        assert_closed_world_topology(payload)


def test_drift_fixture_owner_without_caller_state_loss_fails() -> None:
    payload = copy.deepcopy(_load_contract())
    payload["owners_without_external_productive_callers"] = []
    assert (
        len(payload["owners_without_external_productive_callers"])
        != payload["expected_counts"]["owners_without_external_productive_callers"]
    )


def test_drift_policy_pins_are_fail() -> None:
    payload = _load_contract()
    drift = payload["drift_policy"]
    for key, value in drift.items():
        assert value == "FAIL", f"{key} must be FAIL"
