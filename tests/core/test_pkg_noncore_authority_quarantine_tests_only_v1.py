"""PKG-NONCORE-AUTHORITY-QUARANTINE-TESTS-ONLY package contract.

Protects OWNER_GO=PEAK_TRADE_POST_REGIME_COMBINED_TESTS_ONLY_PACKAGES_1_2_IMPLEMENTATION_V1

    PACKAGE_D_CLASS=TESTS_ONLY
    MEMBER_NODES=WN-SRC-AUTONOMOUS,WN-LIVE-GATES,WN-LIVE-TESTNET-ORCH,
                 WN-SRC-GOVERNANCE-PROMOTION

Already-adjudicated disposition (not re-proven here):

    preserve research-workflow automation / eligibility predicates /
    testnet lifecycle orchestration / promotion governance;
    do not self-promote those surfaces into trading, live, or execution
    authority.

This module is tests-only quarantine. It does not mutate src/. It does
not implement a Testnet Owner-GO token. It does not re-run the WP-A4
ConfigPatch -> Manifest -> PromotionCandidate flow. It does not expand
portfolio eligibility. Scheduler is out of scope.
"""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

from src.autonomous.decision_engine import DecisionAction, WorkflowDecision
from src.live.live_gates import LiveGateResult
from src.trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE,
    LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING,
    MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED,
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTONOMOUS_ROOT_REL = "src/autonomous"
LIVE_GATES_REL = "src/live/live_gates.py"
TESTNET_ORCH_REL = "src/live/testnet_orchestrator.py"
PROMOTION_LOOP_ROOT_REL = "src/governance/promotion_loop"

# WP-A4 already closed the narrow ConfigPatch path. This package scans the
# remaining promotion_loop files for the broader promotion != LIVE_ENABLED
# residual and does not re-implement that ConfigPatch flow.
WP_A4_PROVEN_PROMOTION_RELS: frozenset[str] = frozenset(
    {
        "src/governance/promotion_loop/engine.py",
        "src/governance/promotion_loop/models.py",
        "src/governance/promotion_loop/proposal_input_refs_v1.py",
        "src/governance/promotion_loop/safety.py",
        "src/governance/promotion_loop/__init__.py",
    }
)

_FORBIDDEN_ACTIVATION_NAMES: frozenset[str] = frozenset(
    {
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
        "enable_live_trading",
        "live_mode_armed",
        "live_authorized",
        "testnet_authorized",
        "canary_authorized",
    }
)
_FORBIDDEN_ORDER_SUBMIT_NAMES: frozenset[str] = frozenset(
    {
        "submit_order",
        "place_order",
        "create_order",
    }
)
_FORBIDDEN_AUTHORITY_TYPE_NAMES: frozenset[str] = frozenset(
    {
        "Permit",
        "ExecutionPermit",
    }
)
_AUTONOMOUS_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.live",
        "src.risk",
        "src.risk_layer",
        "src.ops.double_play",
        "trading.master_v2",
        "src.trading.master_v2",
        "src.webui",
        "src.exchange",
    }
)
_PROMOTION_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.exchange",
        "src.live",
    }
)
_ORCH_FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "src.execution",
        "src.execution_simple",
        "src.orders",
        "src.exchange",
        "trading.master_v2",
        "src.trading.master_v2",
        "src.ops.double_play",
    }
)

# Required non-claims. Do not invert these in this surface.
NON_CORE_CONTROL_SURFACES_CANNOT_SELF_PROMOTE_TO_TRADING_AUTHORITY = True
AUTONOMY_IS_TRADING_AUTHORITY = False
AUTONOMY_IS_SELECTION_AUTHORITY = False
AUTONOMY_IS_RISK_AUTHORITY = False
AUTONOMY_IS_PLANNING_AUTHORITY = False
AUTONOMY_IS_EXECUTION_AUTHORITY = False
AUTONOMY_REPLACES_MASTER_V2 = False
AUTONOMY_REPLACES_DOUBLE_PLAY = False
DECISION_ACTION_EXECUTE_IS_ORDER_PERMIT = False
ELIGIBILITY_IS_PERMIT = False
PROMOTION_IS_LIVE_ENABLED = False
TESTNET_ORCHESTRATOR_MAY_START_LIVE = False
TESTNET_OWNER_GO_TOKEN_IMPLEMENTED_BY_THIS_PACKAGE = False
PORTFOLIO_ELIGIBILITY_EXPANDED_BY_THIS_PACKAGE = False
WP_A4_CONFIGPATCH_FLOW_REIMPLEMENTED = False
SCHEDULER_INCLUDED_IN_THIS_PACKAGE = False
PRODUCTIVE_MUTATION_PERFORMED_BY_THIS_PACKAGE = False


def _repo_path(rel: str) -> Path:
    return REPO_ROOT / rel


def _iter_python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _package_scan_paths() -> tuple[Path, ...]:
    autonomous = _iter_python_files(_repo_path(AUTONOMOUS_ROOT_REL))
    promotion = _iter_python_files(_repo_path(PROMOTION_LOOP_ROOT_REL))
    return autonomous + (_repo_path(LIVE_GATES_REL), _repo_path(TESTNET_ORCH_REL)) + promotion


def _parse_path(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _const_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _forbidden_activation_writes(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not _const_true(node.value):
                continue
            for target in node.targets:
                name = _target_name(target)
                if name in _FORBIDDEN_ACTIVATION_NAMES:
                    hits.append(name)
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    key = target.slice.value
                    if isinstance(key, str) and key in _FORBIDDEN_ACTIVATION_NAMES:
                        hits.append(key)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if not _const_true(node.value):
                continue
            name = _target_name(node.target)
            if name in _FORBIDDEN_ACTIVATION_NAMES:
                hits.append(name)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg in _FORBIDDEN_ACTIVATION_NAMES and _const_true(keyword.value):
                    hits.append(keyword.arg)
    return hits


def _forbidden_submit_calls(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name in _FORBIDDEN_ORDER_SUBMIT_NAMES:
            hits.append(name)
    return hits


def _class_names(tree: ast.AST) -> tuple[str, ...]:
    return tuple(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _imported_modules(path: Path, tree: ast.AST) -> list[str]:
    current_parts = path.relative_to(REPO_ROOT).with_suffix("").parts
    if current_parts[-1] == "__init__":
        package_parts = current_parts[:-1]
    else:
        package_parts = current_parts[:-1]
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                hits.append(node.module or "")
                continue
            base = list(package_parts)
            for _ in range(node.level - 1):
                if base:
                    base = base[:-1]
            if node.module:
                base.extend(node.module.split("."))
            hits.append(".".join(base))
    return hits


def _forbidden_import_hits(imported: list[str], roots: frozenset[str]) -> list[str]:
    hits: list[str] = []
    for name in imported:
        for forbidden in roots:
            if name == forbidden or name.startswith(f"{forbidden}."):
                hits.append(name)
    return hits


def _name_assign_linenos(fn: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> tuple[int, ...]:
    lines: list[int] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    lines.append(node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                lines.append(node.lineno)
    return tuple(lines)


def _call_linenos(fn: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> tuple[int, ...]:
    return tuple(
        node.lineno
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and _call_name(node) == name
    )


def test_package_contract_does_not_normalize_authority_claims() -> None:
    assert NON_CORE_CONTROL_SURFACES_CANNOT_SELF_PROMOTE_TO_TRADING_AUTHORITY is True
    assert AUTONOMY_IS_TRADING_AUTHORITY is False
    assert AUTONOMY_IS_SELECTION_AUTHORITY is False
    assert AUTONOMY_IS_RISK_AUTHORITY is False
    assert AUTONOMY_IS_PLANNING_AUTHORITY is False
    assert AUTONOMY_IS_EXECUTION_AUTHORITY is False
    assert AUTONOMY_REPLACES_MASTER_V2 is False
    assert AUTONOMY_REPLACES_DOUBLE_PLAY is False
    assert DECISION_ACTION_EXECUTE_IS_ORDER_PERMIT is False
    assert ELIGIBILITY_IS_PERMIT is False
    assert PROMOTION_IS_LIVE_ENABLED is False
    assert TESTNET_ORCHESTRATOR_MAY_START_LIVE is False
    assert TESTNET_OWNER_GO_TOKEN_IMPLEMENTED_BY_THIS_PACKAGE is False
    assert PORTFOLIO_ELIGIBILITY_EXPANDED_BY_THIS_PACKAGE is False
    assert WP_A4_CONFIGPATCH_FLOW_REIMPLEMENTED is False
    assert SCHEDULER_INCLUDED_IN_THIS_PACKAGE is False
    assert PRODUCTIVE_MUTATION_PERFORMED_BY_THIS_PACKAGE is False


def test_package_surfaces_do_not_flip_activation_or_submit_orders() -> None:
    activation_hits: list[tuple[str, str]] = []
    submit_hits: list[tuple[str, str]] = []
    permit_hits: list[tuple[str, str]] = []
    for path in _package_scan_paths():
        rel = str(path.relative_to(REPO_ROOT))
        tree = _parse_path(path)
        for name in _forbidden_activation_writes(tree):
            activation_hits.append((rel, name))
        for name in _forbidden_submit_calls(tree):
            submit_hits.append((rel, name))
        class_names = set(_class_names(tree))
        for name in sorted(class_names & _FORBIDDEN_AUTHORITY_TYPE_NAMES):
            permit_hits.append((rel, name))
    assert activation_hits == []
    assert submit_hits == []
    assert permit_hits == []


def test_autonomy_has_no_core_execution_or_live_authority_imports() -> None:
    import_hits: list[tuple[str, str]] = []
    for path in _iter_python_files(_repo_path(AUTONOMOUS_ROOT_REL)):
        rel = str(path.relative_to(REPO_ROOT))
        imported = _imported_modules(path, _parse_path(path))
        for name in _forbidden_import_hits(imported, _AUTONOMOUS_FORBIDDEN_IMPORT_ROOTS):
            import_hits.append((rel, name))
    assert import_hits == []


def test_decision_action_execute_is_workflow_enum_not_order_permit() -> None:
    assert DecisionAction.EXECUTE.value == "execute"
    assert set(DecisionAction) == {
        DecisionAction.EXECUTE,
        DecisionAction.SKIP,
        DecisionAction.ALERT,
        DecisionAction.WAIT,
    }
    decision = WorkflowDecision(
        action=DecisionAction.EXECUTE,
        confidence=1.0,
        reasoning="workflow-only execute enum is not an order permit",
    )
    assert decision.should_execute is True
    assert "submit_order" not in decision.reasoning
    assert not hasattr(decision, "permit")
    tree = _parse_path(_repo_path("src/autonomous/decision_engine.py"))
    action_cls = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "DecisionAction"
    )
    assert _forbidden_submit_calls(action_cls) == []
    assert "Permit" not in {base.id for base in action_cls.bases if isinstance(base, ast.Name)}


def test_autonomy_workflow_script_map_is_not_submit_or_live_activation() -> None:
    fn = _function_def(
        _parse_path(_repo_path("src/autonomous/workflow_engine.py")), "_execute_workflow_internal"
    )
    assert fn is not None
    script_map: dict[str, str] = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id != "workflow_scripts":
            continue
        assert isinstance(node.value, ast.Dict)
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            assert isinstance(key, ast.Constant) and isinstance(key.value, str)
            assert isinstance(value, ast.Constant) and isinstance(value.value, str)
            script_map[key.value] = value.value
    assert script_map
    for script in script_map.values():
        assert script.startswith("scripts/")
        assert not script.startswith("src/execution")
        assert "submit_order" not in script
        assert "place_order" not in script
        assert "create_order" not in script
        stem = Path(script).stem
        assert stem not in _FORBIDDEN_ACTIVATION_NAMES
        assert stem not in _FORBIDDEN_ORDER_SUBMIT_NAMES


def test_live_gate_result_eligibility_is_not_a_permit() -> None:
    field_names = tuple(item.name for item in dataclasses.fields(LiveGateResult))
    assert "is_eligible" in field_names
    assert "permit" not in field_names
    assert "Permit" not in field_names
    assert "LIVE_ENABLED" not in field_names
    assert "LIVE_AUTHORIZED" not in field_names
    assert ELIGIBILITY_IS_PERMIT is False


def test_live_gates_finalize_eligibility_before_double_play_annotation() -> None:
    tree = _parse_path(_repo_path(LIVE_GATES_REL))
    for fn_name in ("check_strategy_live_eligibility", "check_portfolio_live_eligibility"):
        fn = _function_def(tree, fn_name)
        assert fn is not None, fn_name
        eligible_lines = _name_assign_linenos(fn, "is_eligible")
        dp_lines = _call_linenos(fn, "evaluate_double_play")
        annotation_lines = _call_linenos(fn, "build_legacy_double_play_live_gates_annotation")
        assert eligible_lines, fn_name
        assert dp_lines, fn_name
        assert annotation_lines, fn_name
        assert max(eligible_lines) < min(dp_lines), fn_name
        assert max(dp_lines) <= max(annotation_lines), fn_name
        returns = sorted(
            (node for node in ast.walk(fn) if isinstance(node, ast.Return)),
            key=lambda node: node.lineno,
        )
        assert returns, fn_name
        final_return = returns[-1]
        assert isinstance(final_return.value, ast.Call), fn_name
        assert _call_name(final_return.value) == "LiveGateResult"
        eligible_kw = next(kw for kw in final_return.value.keywords if kw.arg == "is_eligible")
        assert isinstance(eligible_kw.value, ast.Name)
        assert eligible_kw.value.id == "is_eligible"
        details_kw = next(kw for kw in final_return.value.keywords if kw.arg == "details")
        assert isinstance(details_kw.value, ast.Name)
        assert details_kw.value.id == "details"
        assert final_return.lineno > max(annotation_lines), fn_name


def test_live_gates_double_play_remains_non_authoritative_annotation() -> None:
    assert LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE == "PROJECTION_DIAGNOSTIC_ONLY"
    assert LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING == "false"
    assert MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED == "false"
    assert OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY == "LEGACY_NON_AUTHORITATIVE"
    source = _repo_path(LIVE_GATES_REL).read_text(encoding="utf-8")
    assert "``is_eligible`` is finalized above; evaluate_double_play must not affect it." in source
    assert "build_legacy_double_play_live_gates_annotation" in source
    assert 'details["double_play"]' in source


def test_portfolio_eligibility_is_not_expanded_by_this_package() -> None:
    tree = _parse_path(_repo_path(LIVE_GATES_REL))
    portfolio_defs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "check_portfolio_live_eligibility"
    ]
    assert portfolio_defs == ["check_portfolio_live_eligibility"]
    assert PORTFOLIO_ELIGIBILITY_EXPANDED_BY_THIS_PACKAGE is False


def test_testnet_orchestrator_blocks_live_and_does_not_set_authorization() -> None:
    tree = _parse_path(_repo_path(TESTNET_ORCH_REL))
    readiness = _function_def(tree, "_ensure_readiness")
    assert readiness is not None
    readiness_src = ast.get_source_segment(
        _repo_path(TESTNET_ORCH_REL).read_text(encoding="utf-8"), readiness
    )
    assert readiness_src is not None
    assert "env_config.is_live" in readiness_src
    assert "ReadinessCheckFailedError" in readiness_src
    assert "Live-Mode ist nicht erlaubt" in readiness_src
    for start_name in ("start_shadow_run", "start_testnet_run"):
        start_fn = _function_def(tree, start_name)
        assert start_fn is not None, start_name
        assert _call_linenos(start_fn, "_ensure_readiness"), start_name
        assert _forbidden_submit_calls(start_fn) == []
    imported = _imported_modules(_repo_path(TESTNET_ORCH_REL), tree)
    assert _forbidden_import_hits(imported, _ORCH_FORBIDDEN_IMPORT_ROOTS) == []
    assert TESTNET_OWNER_GO_TOKEN_IMPLEMENTED_BY_THIS_PACKAGE is False


def test_promotion_loop_residual_is_not_live_enablement() -> None:
    residual_paths = [
        path
        for path in _iter_python_files(_repo_path(PROMOTION_LOOP_ROOT_REL))
        if str(path.relative_to(REPO_ROOT)) not in WP_A4_PROVEN_PROMOTION_RELS
    ]
    assert residual_paths
    import_hits: list[tuple[str, str]] = []
    for path in residual_paths:
        rel = str(path.relative_to(REPO_ROOT))
        tree = _parse_path(path)
        imported = _imported_modules(path, tree)
        for name in _forbidden_import_hits(imported, _PROMOTION_FORBIDDEN_IMPORT_ROOTS):
            import_hits.append((rel, name))
    assert import_hits == []
    assert PROMOTION_IS_LIVE_ENABLED is False
    assert WP_A4_CONFIGPATCH_FLOW_REIMPLEMENTED is False
    engine_src = _repo_path("src/governance/promotion_loop/engine.py").read_text(encoding="utf-8")
    assert "def apply_proposals_to_live_overrides" in engine_src
    assert "return None" in engine_src
