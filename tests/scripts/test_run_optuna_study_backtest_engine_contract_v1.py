"""
run_optuna_study.py: stale BacktestEngine API contract-first tests (offline, fail-closed).

Locks legacy BacktestEngine(strategy=..., config=...) construction and bare
run_realistic() calls. EQUIVALENCE_NOT_PROVEN vs load_strategy() migration.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_optuna_study as run_optuna_script

TARGET_SCRIPT = project_root / "scripts" / "run_optuna_study.py"
EQUIVALENCE_NOT_PROVEN = "EQUIVALENCE_NOT_PROVEN"
MODERNIZATION_REQUIRED_ARGS = frozenset({"df", "strategy_signal_fn", "strategy_params"})
LEGACY_ENGINE_KWARGS = frozenset({"strategy", "config"})


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    tree = ast.parse(_read_source())
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(_read_source(), fn) or ""


def _backtest_engine_call_keywords() -> set[str]:
    tree = ast.parse(_read_source())
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_backtest_trial"
    )
    keywords: set[str] = set()
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "BacktestEngine"
        ):
            keywords = {kw.arg for kw in node.keywords if kw.arg}
    return keywords


def _run_realistic_call_arg_count() -> int:
    tree = ast.parse(_read_source())
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_backtest_trial"
    )
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run_realistic"
        ):
            return len(node.args) + len(node.keywords)
    raise AssertionError("run_realistic call not found in run_backtest_trial")


# ---------------------------------------------------------------------------
# AST / static guards — production fix not applied in this slice
# ---------------------------------------------------------------------------


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(run_optuna_script, "main") as main_mock:
        importlib.reload(run_optuna_script)
    main_mock.assert_not_called()


def test_source_has_no_load_strategy_migration() -> None:
    assert "load_strategy" not in _read_source()


def test_equivalence_not_proven_marker_present_in_test_owner() -> None:
    owner_source = Path(__file__).read_text(encoding="utf-8")
    assert EQUIVALENCE_NOT_PROVEN in owner_source


def test_source_still_imports_backtest_engine() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "src.backtest.engine"
        for alias in node.names
    }
    assert "BacktestEngine" in imported


def test_source_still_uses_get_strategy_spec_cls_binding() -> None:
    source = _read_source()
    assert "get_strategy_spec" in source
    assert ".cls" in source


def test_source_still_instantiates_strategy_cls_with_trial_params() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert "strategy_cls(**trial_params)" in fn_source


# ---------------------------------------------------------------------------
# Stale Constructor Contract
# ---------------------------------------------------------------------------


def test_stale_constructor_passes_legacy_strategy_and_config_keywords() -> None:
    keywords = _backtest_engine_call_keywords()
    assert LEGACY_ENGINE_KWARGS <= keywords


def test_canonical_backtest_engine_constructor_rejects_legacy_keywords() -> None:
    sig = inspect.signature(run_optuna_script.BacktestEngine.__init__)
    param_names = set(sig.parameters) - {"self"}
    assert LEGACY_ENGINE_KWARGS.isdisjoint(param_names)


def test_stale_constructor_shape_differs_from_canonical_contract() -> None:
    stale = _backtest_engine_call_keywords()
    canonical = set(inspect.signature(run_optuna_script.BacktestEngine.__init__).parameters) - {
        "self"
    }
    assert stale != canonical
    assert "tracker" in stale
    assert "tracker" in canonical


# ---------------------------------------------------------------------------
# Stale run_realistic Contract
# ---------------------------------------------------------------------------


def test_stale_run_realistic_called_without_required_arguments() -> None:
    assert _run_realistic_call_arg_count() == 0


def test_canonical_run_realistic_requires_df_signal_fn_and_params() -> None:
    sig = inspect.signature(run_optuna_script.BacktestEngine.run_realistic)
    for required in MODERNIZATION_REQUIRED_ARGS:
        param = sig.parameters[required]
        assert param.default is inspect.Parameter.empty


# ---------------------------------------------------------------------------
# Fail-loud boundary — deterministic contract break, no real backtest
# ---------------------------------------------------------------------------


class _MinimalTrialStrategy:
    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs


def test_run_backtest_trial_fails_loud_on_legacy_engine_construction() -> None:
    with (
        patch.object(run_optuna_script, "build_tracker_from_config", return_value=MagicMock()),
        pytest.raises(TypeError, match="unexpected keyword argument 'strategy'"),
    ):
        run_optuna_script.run_backtest_trial(
            cfg=MagicMock(),
            strategy_cls=_MinimalTrialStrategy,
            trial_params={"fast_window": 10, "slow_window": 50},
            trial=None,
        )


def test_bare_run_realistic_on_canonical_engine_requires_arguments() -> None:
    engine = run_optuna_script.BacktestEngine()
    with pytest.raises(TypeError):
        engine.run_realistic()


# ---------------------------------------------------------------------------
# OOP Trial Binding — legacy class path, not load_strategy() equivalence
# ---------------------------------------------------------------------------


def test_run_study_resolves_strategy_via_get_strategy_spec_cls() -> None:
    fn_source = _function_source("run_study")
    assert "get_strategy_spec(study_cfg.strategy_name).cls" in fn_source


def test_trial_params_passed_via_strategy_cls_constructor() -> None:
    trial_params = {"fast_window": 7, "slow_window": 35}
    constructed: dict[str, Any] = {}

    class RecordingStrategy:
        def __init__(self, **kwargs: Any) -> None:
            constructed.update(kwargs)

    with (
        patch.object(run_optuna_script, "build_tracker_from_config", return_value=MagicMock()),
        pytest.raises(TypeError, match="unexpected keyword argument 'strategy'"),
    ):
        run_optuna_script.run_backtest_trial(
            cfg=MagicMock(),
            strategy_cls=RecordingStrategy,
            trial_params=trial_params,
            trial=None,
        )

    assert constructed == trial_params


def test_load_strategy_equivalence_not_claimed() -> None:
    assert EQUIVALENCE_NOT_PROVEN == "EQUIVALENCE_NOT_PROVEN"
    assert "load_strategy" not in _read_source()


# ---------------------------------------------------------------------------
# Functional Target Boundary — future modernization contract (test-local)
# ---------------------------------------------------------------------------


def test_modernization_boundary_requires_functional_signal_contract() -> None:
    owner_source = Path(__file__).read_text(encoding="utf-8")
    for arg in MODERNIZATION_REQUIRED_ARGS:
        assert arg in owner_source
    fn_source = _function_source("run_backtest_trial")
    for arg in MODERNIZATION_REQUIRED_ARGS:
        assert arg not in fn_source


# ---------------------------------------------------------------------------
# Data Contract Gap
# ---------------------------------------------------------------------------


def test_run_backtest_trial_has_no_dataframe_binding() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert "DataFrame" not in fn_source
    assert "load_data" not in fn_source
    assert "read_csv" not in fn_source
    assert "df" not in fn_source


def test_run_study_has_no_ohlcv_loader_before_trial_path() -> None:
    fn_source = _function_source("run_study")
    assert "DataFrame" not in fn_source
    assert "load_data" not in fn_source


# ---------------------------------------------------------------------------
# Objective Preservation — static contract freeze
# ---------------------------------------------------------------------------


def test_objective_single_preserves_metric_extraction_and_drawdown_negation() -> None:
    fn_source = _function_source("objective_single")
    assert "metrics.get(objective_name, 0.0)" in fn_source
    assert 'objective_name == "max_drawdown"' in fn_source
    assert "objective_value = -objective_value" in fn_source


def test_objective_single_preserves_directional_failure_fallback() -> None:
    fn_source = _function_source("objective_single")
    assert 'study_cfg.direction == "maximize"' in fn_source
    assert 'return float("-inf")' in fn_source
    assert 'return float("inf")' in fn_source


def test_objective_multi_preserves_pareto_objective_negation() -> None:
    fn_source = _function_source("objective_multi")
    assert 'obj_name == "max_drawdown"' in fn_source
    assert "value = -value" in fn_source
    assert 'return tuple([float("-inf")]' in fn_source


def test_run_study_single_objective_direction_defaults_to_maximize() -> None:
    fn_source = _function_source("run_study")
    assert 'direction = study_cfg.direction or "maximize"' in fn_source


# ---------------------------------------------------------------------------
# Pruning and Exceptions — static + isolated fakes, no study execution
# ---------------------------------------------------------------------------


def test_run_backtest_trial_preserves_pruning_report_and_should_prune() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert "trial.report" in fn_source
    assert "trial.should_prune" in fn_source
    assert "optuna.TrialPruned" in fn_source


class _PruningTrial:
    def report(self, value: float, step: int) -> None:
        self.reported = (value, step)

    def should_prune(self) -> bool:
        return True


def test_run_backtest_trial_raises_trial_pruned_when_should_prune_true() -> None:
    trial = _PruningTrial()
    captured: dict[str, Any] = {}

    class TrialPruned(Exception):
        pass

    class FakeEngine:
        def __init__(self, **kwargs: Any) -> None:
            captured["engine_kwargs"] = kwargs

        def run_realistic(self) -> dict[str, Any]:
            return {"stats": {"sharpe": 1.5, "max_drawdown": -0.1}}

    fake_optuna = MagicMock()
    fake_optuna.TrialPruned = TrialPruned

    with (
        patch.object(run_optuna_script, "BacktestEngine", FakeEngine),
        patch.object(run_optuna_script, "build_tracker_from_config", return_value=MagicMock()),
        patch.object(run_optuna_script, "optuna", fake_optuna),
        pytest.raises(TrialPruned),
    ):
        run_optuna_script.run_backtest_trial(
            cfg=MagicMock(),
            strategy_cls=_MinimalTrialStrategy,
            trial_params={},
            trial=trial,
        )

    assert captured["engine_kwargs"]["strategy"] is not None


def test_objective_single_exception_path_returns_directional_worst_value() -> None:
    study_cfg = run_optuna_script.StudyConfig(
        strategy_name="ma_crossover",
        config_path=Path("config.toml"),
        n_trials=1,
        study_name=None,
        objectives=["sharpe"],
        storage=None,
        pruner_type="none",
        sampler_type="tpe",
        timeout=None,
        n_jobs=1,
        direction="maximize",
    )
    trial = MagicMock()
    trial.number = 0

    with (
        patch.object(run_optuna_script, "suggest_params_from_schema", return_value={}),
        patch.object(
            run_optuna_script,
            "run_backtest_trial",
            side_effect=RuntimeError("synthetic trial failure"),
        ),
    ):
        result = run_optuna_script.objective_single(
            trial=trial,
            study_cfg=study_cfg,
            cfg=MagicMock(),
            strategy_cls=_MinimalTrialStrategy,
            objective_name="sharpe",
        )

    assert result == float("-inf")


# ---------------------------------------------------------------------------
# No-Run Guard — import/help only
# ---------------------------------------------------------------------------


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_optuna_study"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_smoke() -> None:
    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "run_study_optuna_placeholder.py" in result.stdout
    assert "--strategy" in result.stdout
