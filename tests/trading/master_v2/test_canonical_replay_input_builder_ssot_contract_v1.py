"""Static SSOT contract: single productive IntegratedOfflineReplayInputV1 builder."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

_OWNER_MODULE = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
_PRODUCTIVE_SOURCE_ADAPTERS = (
    REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py",
    REPO_ROOT / "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
    REPO_ROOT
    / "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
)
_PUBLIC_BUILDER_NAME = "build_integrated_offline_replay_input_v1"
_INPUT_TYPE_NAME = "IntegratedOfflineReplayInputV1"
_TEST_ONLY_HELPER = (
    REPO_ROOT / "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py"
)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _function_defs_by_name(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = node
    return found


def _direct_input_constructions(tree: ast.AST) -> list[ast.Call]:
    hits: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == _INPUT_TYPE_NAME:
            hits.append(node)
    return hits


def _builder_calls(tree: ast.AST) -> list[ast.Call]:
    hits: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == _PUBLIC_BUILDER_NAME:
            hits.append(node)
    return hits


def test_public_builder_is_only_productive_direct_construction_authority_v1() -> None:
    tree = ast.parse(_OWNER_MODULE.read_text(encoding="utf-8"))
    defs = _function_defs_by_name(tree)
    assert _PUBLIC_BUILDER_NAME in defs

    builder_node = defs[_PUBLIC_BUILDER_NAME]
    constructions_in_builder = _direct_input_constructions(builder_node)
    assert len(constructions_in_builder) == 1

    all_constructions = _direct_input_constructions(tree)
    assert len(all_constructions) == 1
    assert all_constructions[0] is constructions_in_builder[0]


def test_productive_source_adapters_do_not_construct_replay_input_directly_v1() -> None:
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        direct = _direct_input_constructions(tree)
        assert direct == [], f"{path.relative_to(REPO_ROOT)} still constructs {_INPUT_TYPE_NAME}"


def test_productive_source_adapters_delegate_to_public_builder_v1() -> None:
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = _builder_calls(tree)
        assert calls, f"{path.relative_to(REPO_ROOT)} missing call to {_PUBLIC_BUILDER_NAME}"


def test_test_only_helper_is_not_classified_as_productive_authority_v1() -> None:
    """Test helpers may construct fixtures; they are outside productive authority count."""
    tree = ast.parse(_TEST_ONLY_HELPER.read_text(encoding="utf-8"))
    # Presence of a test helper construction must not affect productive authority SSOT.
    assert _TEST_ONLY_HELPER.as_posix().endswith(
        "tests/trading/master_v2/test_integrated_offline_trading_logic_replay_v1.py"
    )
    # Productive authority remains exactly the public builder in owner module.
    owner_tree = ast.parse(_OWNER_MODULE.read_text(encoding="utf-8"))
    assert len(_direct_input_constructions(owner_tree)) == 1
    # Test helper is optional: if present, ignored for productive authority.
    _ = _direct_input_constructions(tree)


def test_productive_direct_construction_authority_count_is_one_v1() -> None:
    productive_authority_files = {_OWNER_MODULE.resolve()}
    for path in _PRODUCTIVE_SOURCE_ADAPTERS:
        assert path.resolve() not in productive_authority_files
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert _direct_input_constructions(tree) == []
        assert _builder_calls(tree)

    owner_tree = ast.parse(_OWNER_MODULE.read_text(encoding="utf-8"))
    assert len(_direct_input_constructions(owner_tree)) == 1
    assert len(productive_authority_files) == 1
