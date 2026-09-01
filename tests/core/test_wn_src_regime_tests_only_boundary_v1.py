"""WN-SRC-REGIME tests-only boundary for StrategySwitchingPolicy.

Protects OWNER_DECISION_POST_WP_A6_NEXT_SLICE_V1:

    SOURCE_NODE=WN-SRC-REGIME
    D_CLASS=TESTS_ONLY

Already-adjudicated disposition (not re-proven here):

    preserve regime detection for research/shadow;
    do not preserve StrategySwitchingPolicy as competing DP authority.

This module is tests-only quarantine. It does not revive historical
regime engines. It does not create a second trading authority. It does
not mutate src/. It does not import src.regime.__init__ (detectors /
switching) as a side effect of the Protocol surface check.
"""

from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
import types
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parents[2]

REGIME_BASE_REL = "src/regime/base.py"
CORE_REGIME_REL = "src/core/regime.py"
LLM_REGIME_STUB_REL = "src/ai/regimes/regime_switch_v1.py"

_ALLOWED_STRATEGY_SWITCHING_POLICY_PATHS = frozenset(
    {
        "src/regime/base.py",
        "src/regime/__init__.py",
        "src/regime/switching.py",
    }
)

_FORBIDDEN_IMPORT_ROOTS = frozenset(
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

_FORBIDDEN_ACTIVATION_NAMES = frozenset(
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

_FORBIDDEN_ORDER_SUBMIT_NAMES = frozenset(
    {
        "submit_order",
        "place_order",
        "create_order",
    }
)

_FORBIDDEN_AUTHORITY_TYPE_NAMES = frozenset(
    {
        "Permit",
        "ExecutionPermit",
    }
)

# Required non-claims. Do not invert these in this surface.
STRATEGY_SWITCHING_POLICY_IS_TRADING_AUTHORITY = False
STRATEGY_SWITCHING_POLICY_IS_SELECTION_AUTHORITY = False
STRATEGY_SWITCHING_POLICY_IS_RISK_AUTHORITY = False
STRATEGY_SWITCHING_POLICY_IS_EXECUTION_AUTHORITY = False
STRATEGY_SWITCHING_POLICY_REPLACES_MASTER_V2 = False
STRATEGY_SWITCHING_POLICY_REPLACES_DOUBLE_PLAY = False
STRATEGY_SWITCHING_POLICY_SAME_AS_CORE_REGIME = False
STRATEGY_SWITCHING_POLICY_SAME_AS_LLM_REGIME_STUB = False
NEW_REGIME_ENGINE_CREATED_BY_THIS_SLICE = False
HIST_REGIME_SEQUENCER_RESTORED = False
SEMANTIC_PARITY_PROVEN = False


def _repo_path(rel: str) -> Path:
    return REPO_ROOT / rel


def _parse(rel: str) -> ast.AST:
    return ast.parse(_repo_path(rel).read_text(encoding="utf-8"))


def _iter_src_python_files() -> tuple[Path, ...]:
    src_root = REPO_ROOT / "src"
    return tuple(sorted(path for path in src_root.rglob("*.py") if "__pycache__" not in path.parts))


def _class_names(tree: ast.AST) -> tuple[str, ...]:
    return tuple(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def _class_def(tree: ast.AST, name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            hits.append(node.module)
    return tuple(hits)


def _decorator_names(class_def: ast.ClassDef) -> tuple[str, ...]:
    names: list[str] = []
    for decorator in class_def.decorator_list:
        if isinstance(decorator, ast.Name):
            names.append(decorator.id)
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            names.append(decorator.func.id)
    return tuple(names)


def _base_names(class_def: ast.ClassDef) -> tuple[str, ...]:
    names: list[str] = []
    for base in class_def.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
    return tuple(names)


def _forbidden_name_hits(tree: ast.AST, names: frozenset[str]) -> tuple[str, ...]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in names:
            hits.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in names:
            hits.append(node.attr)
        elif isinstance(node, ast.keyword) and node.arg in names:
            hits.append(node.arg)
    return tuple(hits)


def _load_regime_base_isolated() -> types.ModuleType:
    module_name = "wn_src_regime_base_isolated_v1"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = _repo_path(REGIME_BASE_REL)
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_wn_src_regime_does_not_normalize_authority_claims() -> None:
    assert STRATEGY_SWITCHING_POLICY_IS_TRADING_AUTHORITY is False
    assert STRATEGY_SWITCHING_POLICY_IS_SELECTION_AUTHORITY is False
    assert STRATEGY_SWITCHING_POLICY_IS_RISK_AUTHORITY is False
    assert STRATEGY_SWITCHING_POLICY_IS_EXECUTION_AUTHORITY is False
    assert STRATEGY_SWITCHING_POLICY_REPLACES_MASTER_V2 is False
    assert STRATEGY_SWITCHING_POLICY_REPLACES_DOUBLE_PLAY is False
    assert STRATEGY_SWITCHING_POLICY_SAME_AS_CORE_REGIME is False
    assert STRATEGY_SWITCHING_POLICY_SAME_AS_LLM_REGIME_STUB is False
    assert NEW_REGIME_ENGINE_CREATED_BY_THIS_SLICE is False
    assert HIST_REGIME_SEQUENCER_RESTORED is False
    assert SEMANTIC_PARITY_PROVEN is False


def test_strategy_switching_policy_is_protocol_on_regime_base() -> None:
    tree = _parse(REGIME_BASE_REL)
    policy = _class_def(tree, "StrategySwitchingPolicy")
    assert policy is not None
    assert _base_names(policy) == ("Protocol",)
    assert "runtime_checkable" in _decorator_names(policy)
    methods = tuple(node.name for node in policy.body if isinstance(node, ast.FunctionDef))
    assert methods == ("decide",)
    decide = next(node for node in policy.body if isinstance(node, ast.FunctionDef))
    param_names = tuple(arg.arg for arg in decide.args.args)
    assert param_names == ("self", "regime", "available_strategies")
    non_doc_stmts = tuple(
        node
        for node in decide.body
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    )
    assert len(non_doc_stmts) == 1
    assert isinstance(non_doc_stmts[0], ast.Expr)
    assert isinstance(non_doc_stmts[0].value, ast.Constant)
    assert non_doc_stmts[0].value.value is Ellipsis


def test_isolated_import_exposes_protocol_contract_without_package_init() -> None:
    module = _load_regime_base_isolated()
    policy = module.StrategySwitchingPolicy
    assert issubclass(policy, Protocol)
    signature = inspect.signature(policy.decide)
    assert tuple(signature.parameters) == ("self", "regime", "available_strategies")
    assert "RegimeLabel" in module.__dict__
    assert "StrategySwitchDecision" in module.__dict__
    assert "SimpleRegimeMappingPolicy" not in module.__dict__
    runtime_modules = tuple(
        value.__name__ for value in vars(module).values() if isinstance(value, types.ModuleType)
    )
    for name in runtime_modules:
        for forbidden in _FORBIDDEN_IMPORT_ROOTS:
            assert name != forbidden
            assert not name.startswith(f"{forbidden}.")
        assert not name.startswith("src.regime.switching")
        assert not name.startswith("src.regime.detectors")


def test_regime_base_has_no_forbidden_authority_imports() -> None:
    imported = _imported_modules(_parse(REGIME_BASE_REL))
    for name in imported:
        for forbidden in _FORBIDDEN_IMPORT_ROOTS:
            assert name != forbidden, f"forbidden import {name}"
            assert not name.startswith(f"{forbidden}."), f"forbidden import {name}"
        assert "sequencer" not in name
        assert not name.startswith("archive")


def test_regime_base_has_no_order_live_or_permit_authority_surface() -> None:
    tree = _parse(REGIME_BASE_REL)
    assert _forbidden_name_hits(tree, _FORBIDDEN_ORDER_SUBMIT_NAMES) == ()
    assert _forbidden_name_hits(tree, _FORBIDDEN_ACTIVATION_NAMES) == ()
    class_names = set(_class_names(tree))
    assert class_names.isdisjoint(_FORBIDDEN_AUTHORITY_TYPE_NAMES)
    assert "StrategySwitchingPolicy" in class_names
    assert "RegimeDetector" in class_names
    assert "StrategySwitchDecision" in class_names


def test_strategy_switching_policy_definition_is_not_duplicated() -> None:
    definition_paths: list[str] = []
    import_paths: list[str] = []
    for path in _iter_src_python_files():
        rel = str(path.relative_to(REPO_ROOT))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if "StrategySwitchingPolicy" in _class_names(tree):
            definition_paths.append(rel)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if any(alias.name == "StrategySwitchingPolicy" for alias in node.names):
                import_paths.append(rel)
                break
    assert definition_paths == ["src/regime/base.py"]
    for rel in import_paths:
        assert rel in _ALLOWED_STRATEGY_SWITCHING_POLICY_PATHS, rel


def test_distinct_regime_surfaces_are_not_strategy_switching_policy() -> None:
    assert "StrategySwitchingPolicy" not in _class_names(_parse(CORE_REGIME_REL))
    assert "StrategySwitchingPolicy" not in _class_names(_parse(LLM_REGIME_STUB_REL))


def test_this_slice_does_not_define_a_parallel_regime_policy_class() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    defined = tuple(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and node.name.endswith("Policy")
        and node.name != "Protocol"
    )
    assert defined == ()
    assert NEW_REGIME_ENGINE_CREATED_BY_THIS_SLICE is False
