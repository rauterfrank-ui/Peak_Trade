"""AST/static contracts for Slice-3 classic caller canonicalization."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.backtest.strategy_signal_binding_v1 import (
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    LEGACY_NON_AUTHORITATIVE,
    RUN_BACKTEST_PATH_CLASSIFICATION,
    StrategySignalBindingError,
    assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1,
    declare_legacy_raw_signal_research_path_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
MASTER_V2_ROOT = SRC_ROOT / "trading" / "master_v2"
ENGINE_PATH = SRC_ROOT / "backtest" / "engine.py"
WIRING_PATH = SRC_ROOT / "backtest" / "mv2_research_wiring_v1.py"
REGISTRY_ENGINE_PATH = SRC_ROOT / "backtest" / "registry_engine.py"
BINDING_PATH = SRC_ROOT / "backtest" / "strategy_signal_binding_v1.py"
RUN_BACKTEST_SCRIPT = REPO_ROOT / "scripts" / "run_backtest.py"

_GUARD_NAMES = frozenset(
    {
        "declare_legacy_raw_signal_research_path_v1",
        "assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1",
    }
)

_CLASSIC_SRC_CALLERS = (
    SRC_ROOT / "backtest" / "engine.py",
    SRC_ROOT / "backtest" / "walkforward.py",
    SRC_ROOT / "sweeps" / "engine.py",
    SRC_ROOT / "portfolio" / "manager.py",
    SRC_ROOT / "strategies" / "diagnostics.py",
    SRC_ROOT / "experiments" / "base.py",
)

_FORBIDDEN_DECISION_OWNER_IMPORTS = frozenset(
    {
        "run_integrated_offline_trading_logic_replay_v1",
        "evaluate_suitability_binding_v1",
        "apply_strategy_suitability_agreement_material_v1",
        "double_play_composition_matrix_v1",
    }
)


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _call_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[-1])
    return names


def _functions_calling_attr(
    tree: ast.AST, attr: str
) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    hits: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == attr
            ):
                hits.append(node)
                break
    return hits


def _function_calls_any(fn: ast.AST, names: frozenset[str]) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in names:
            return True
        if isinstance(func, ast.Attribute) and func.attr in names:
            return True
    return False


def _src_py_files() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if p.is_file())


def test_classic_productive_callers_mark_raw_signal_research_or_guard() -> None:
    for path in _CLASSIC_SRC_CALLERS:
        tree = _parse(path)
        callers = _functions_calling_attr(tree, "run_realistic")
        text = path.read_text(encoding="utf-8")
        assert RUN_BACKTEST_PATH_CLASSIFICATION in text or "RAW_SIGNAL_RESEARCH" in text, path
        assert (
            "LEGACY_NON_AUTHORITATIVE" in text
            or "declare_legacy_raw_signal_research_path_v1" in text
        ), path
        # Engine module also hosts BacktestEngine.run_realistic itself — skip the method body.
        for fn in callers:
            if path == ENGINE_PATH and fn.name in {
                "run_realistic",
                "run_with_order_layer",
                "_run_with_execution_pipeline",
            }:
                # Fill/execution simulator methods — not classic decision-authority callers.
                continue
            assert _function_calls_any(fn, _GUARD_NAMES), (
                f"{path}:{fn.name} must call legacy system-evidence guard"
            )


def test_no_system_economic_evidence_from_raw_strategy_engine_paths() -> None:
    with pytest.raises(
        StrategySignalBindingError,
        match="legacy_raw_signal_path_system_economic_evidence_blocked",
    ):
        assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1(
            path_classification=RUN_BACKTEST_PATH_CLASSIFICATION,
            system_economic_evidence_requested=True,
        )
    with pytest.raises(
        StrategySignalBindingError,
        match="legacy_raw_signal_path_system_economic_evidence_blocked",
    ):
        assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1(
            path_classification="",
            system_economic_evidence_requested=True,
        )
    with pytest.raises(
        StrategySignalBindingError,
        match="legacy_raw_signal_path_system_economic_evidence_blocked",
    ):
        assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1(
            path_classification="CANONICAL_SYSTEM_REPLAY",
            system_economic_evidence_requested=False,
        )


def test_allowed_legacy_paths_are_non_authoritative_and_blocked_for_system_evidence() -> None:
    marker = declare_legacy_raw_signal_research_path_v1(
        system_economic_evidence_requested=False,
        path_classification=RUN_BACKTEST_PATH_CLASSIFICATION,
    )
    assert marker == LEGACY_NON_AUTHORITATIVE
    script = RUN_BACKTEST_SCRIPT.read_text(encoding="utf-8")
    assert "RAW_SIGNAL_RESEARCH" in script
    assert "SYSTEM_ECONOMIC_EVIDENCE_BLOCKED" in script
    assert "declare_legacy_raw_signal_research_path_v1" in script
    with pytest.raises(
        StrategySignalBindingError,
        match="legacy_raw_signal_path_system_economic_evidence_blocked",
    ):
        declare_legacy_raw_signal_research_path_v1(
            system_economic_evidence_requested=True,
            path_classification=RUN_BACKTEST_PATH_CLASSIFICATION,
        )


def test_mv2_configured_strategy_cannot_override_replay_as_system_engine_source() -> None:
    wiring = WIRING_PATH.read_text(encoding="utf-8")
    assert "allow_legacy_raw_signal_research_engine_source" in wiring
    assert "assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1" in wiring
    assert ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY in wiring
    assert CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    tree = _parse(WIRING_PATH)
    assert "assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1" in _call_names(tree)


def test_backtest_engine_remains_fill_simulator_not_decision_owner() -> None:
    tree = _parse(ENGINE_PATH)
    imported = _imported_names(tree)
    leaked = imported & _FORBIDDEN_DECISION_OWNER_IMPORTS
    assert not leaked, f"BacktestEngine module imported decision owners: {sorted(leaked)}"
    run_realistic = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BacktestEngine":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "run_realistic":
                    run_realistic = item
                    break
    assert run_realistic is not None
    called = _call_names(run_realistic)
    assert not (called & _FORBIDDEN_DECISION_OWNER_IMPORTS)


def test_registry_engine_dead_path_removed_or_unimported() -> None:
    text = REGISTRY_ENGINE_PATH.read_text(encoding="utf-8")
    assert "def run_portfolio_from_registry" not in text
    assert "def run_single_strategy_from_registry" not in text
    for path in _src_py_files():
        if path == REGISTRY_ENGINE_PATH:
            continue
        tree = _parse(path)
        imported = _imported_names(tree)
        assert "run_portfolio_from_registry" not in imported
        assert not (
            "registry_engine" in imported
            and (
                "run_portfolio_from_registry" in path.read_text(encoding="utf-8")
                or "run_single_strategy_from_registry" in path.read_text(encoding="utf-8")
            )
        )


def test_productive_src_run_realistic_callers_are_classified() -> None:
    """Every productive src caller of run_realistic is MV2-replay wiring or guarded legacy."""
    for path in _src_py_files():
        if path == ENGINE_PATH:
            # method owner + convenience entrypoints checked above
            continue
        if "reporting" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if ".run_realistic(" not in text:
            continue
        tree = _parse(path)
        for fn in _functions_calling_attr(tree, "run_realistic"):
            if path == WIRING_PATH:
                assert "ENGINE_SIGNAL_SOURCE_MV2_REPLAY" in text
                assert "allow_legacy_raw_signal_research_engine_source" in text
                continue
            assert _function_calls_any(fn, _GUARD_NAMES), (
                f"{path.relative_to(REPO_ROOT)}::{fn.name} must guard legacy raw-signal path"
            )


def test_master_v2_still_does_not_import_backtest_signal_types() -> None:
    forbidden = {"StrategySignalBindingResultV1", "StrategySignalProvenanceV1"}
    for path in MASTER_V2_ROOT.rglob("*.py"):
        tree = _parse(path)
        leaked = _imported_names(tree) & forbidden
        assert not leaked, f"{path.relative_to(REPO_ROOT)} imports {sorted(leaked)}"


def test_central_guard_symbol_exists() -> None:
    tree = _parse(BINDING_PATH)
    names = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1" in names
    assert "declare_legacy_raw_signal_research_path_v1" in names
