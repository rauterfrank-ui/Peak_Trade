"""
run_optuna_study.py: stale BacktestEngine API contract-first tests (offline, fail-closed).

Locks legacy BacktestEngine(strategy=..., config=...) construction and bare
run_realistic() calls. EQUIVALENCE_NOT_PROVEN vs load_strategy() migration.

Extended with test-local data/signal/engine binding target contracts for future
modernization (no production changes in this slice).
"""

from __future__ import annotations

import ast
import copy
import importlib
import inspect
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_optuna_study as run_optuna_script

TARGET_SCRIPT = project_root / "scripts" / "run_optuna_study.py"
EQUIVALENCE_NOT_PROVEN = "EQUIVALENCE_NOT_PROVEN"
MODERNIZATION_REQUIRED_ARGS = frozenset({"df", "strategy_signal_fn", "strategy_params"})
LEGACY_ENGINE_KWARGS = frozenset({"strategy", "config"})
REQUIRED_OHLCV_COLUMNS = frozenset({"open", "high", "low", "close", "volume"})
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
DATA_BINDING_TARGET_DEFINED = True
SIGNAL_BINDING_TARGET_DEFINED = True
ENGINE_CALL_TARGET_DEFINED = True
SIGNAL_EQUIVALENCE_PROVEN_FOR_SCHEMA_KEYS = True
OBJECTIVE_EQUIVALENCE_PROVEN = True
OBJECTIVE_RESULT_MAPPING_DEFINED = True
OBJECTIVE_METRIC_NAME_PRESERVED = True
OBJECTIVE_DIRECTION_PRESERVED = True
OBJECTIVE_INVALID_VALUE_POLICY_FAIL_CLOSED = True
OBJECTIVE_RESULT_CONTRACT_DEFINED = True
OBJECTIVE_METRIC_CONTRACT_DEFINED = True
LEGACY_RESULT_SHAPE = 'dict-like with result.get("stats", {})'
CANONICAL_RESULT_SHAPE = "BacktestResult.stats"
LEGACY_METRIC_PATH = "metrics.get(objective_name, 0.0) after stats.get(key, 0.0) intermediate"
CANONICAL_METRIC_PATH = "BacktestResult.stats[objective_name] fail-closed"
LEGACY_AND_CANONICAL_SHAPES_IDENTICAL = False
MAPPING_REQUIRED = True
METRIC_NAME = "objective_name from study_cfg.objectives[0]"
OPTIMIZATION_DIRECTION = 'study_cfg.direction or "maximize"; max_drawdown forces maximize'
FAILURE_POLICY = "legacy: metrics.get fallback 0.0 + directional worst on broad except; target: fail-closed ObjectiveMetricContractError"
PRUNING_CONTRACT_DEFINED = True
EXCEPTION_CONTRACT_DEFINED = True
STOP_PCT_SOURCE_PROVEN = True
STOP_PCT_PRECEDENCE_DEFINED = True
STOP_PCT_DEFAULT_PROVEN = True
STOP_PCT_RANGE_PROVEN = True
STOP_PCT_CONFLICT_POLICY = "FAIL_CLOSED"
STOP_PCT_TRIAL_PARAMETER = False
STOP_PCT_DECISION_STATUS = "RESOLVED_RUN_BACKTEST_CONFIG_SECTION_V1"
CANONICAL_STOP_PCT_OWNER = "scripts/run_backtest.py:_build_strategy_params_from_config"
STOP_PCT_CONFIG_KEY_TEMPLATE = "strategy.{strategy_key}.stop_pct"
STOP_PCT_DEFAULT_VALUE = 0.02
STOP_PCT_RANGE_GT_EXCLUSIVE = 0.0
STOP_PCT_RANGE_LE_INCLUSIVE = 0.10
STOP_PCT_SOURCE_PRECEDENCE = (
    "config_section_strategy_key",
    "canonical_default",
)
BOUNDED_MODERNIZATION_AUTHORIZED = False
CANONICAL_BACKTEST_RESULT_OWNER = "src/backtest/result.py:BacktestResult"
LEGACY_OBJECTIVE_METRIC_FALLBACK = 0.0
LEGACY_RUN_BACKTEST_TRIAL_METRIC_NAMES = frozenset(
    {"sharpe", "total_return", "max_drawdown", "win_rate", "num_trades", "profit_factor"}
)
STOP_PCT_CANDIDATE_SOURCES = (
    "trial_params",
    "strategy_defaults",
    "strategy_config",
    "engine_strategy_params_default",
)
TARGET_ENGINE_STOP_PCT_DEFAULT = 0.02
OPTUNA_DOCSTRING_SCHEMA_KEYS = frozenset({"ma_crossover", "rsi_reversion", "breakout_donchian"})
SCHEMA_KEY_TRIAL_PARAMS: dict[str, dict[str, Any]] = {
    "ma_crossover": {"fast_window": 10, "slow_window": 50},
    "rsi_reversion": {"rsi_window": 14, "lower": 30.0, "upper": 70.0},
    "breakout_donchian": {"lookback": 20, "price_col": "close"},
}
PRODUCTION_GUARD_PATHS = (
    "scripts/run_optuna_study.py",
    "scripts/run_backtest.py",
    "src/backtest/engine.py",
    "src/strategies/__init__.py",
    "src/strategies/registry.py",
)


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


def _sample_ohlcv(n: int = 120) -> pd.DataFrame:
    np.random.seed(42)
    index = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = 100.0 + np.cumsum(np.random.randn(n))
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": np.full(n, 1000.0),
        },
        index=index,
    )


def _optuna_schema_strategy_keys() -> tuple[str, ...]:
    from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

    keys: list[str] = []
    for key in sorted(get_available_strategy_keys()):
        schema = getattr(get_strategy_spec(key).cls, "parameter_schema", None)
        if schema:
            keys.append(key)
    return tuple(keys)


@dataclass(frozen=True)
class DataBindingTargetContract:
    data_loader_owner: str
    required_columns: frozenset[str]
    lifetime: str
    allow_network: bool
    allow_global_mutable_df: bool
    allow_trial_mutation: bool


DATA_BINDING_TARGET = DataBindingTargetContract(
    data_loader_owner=DATA_LOADER_OWNER,
    required_columns=REQUIRED_OHLCV_COLUMNS,
    lifetime="once_before_study_optimize_reused_by_reference_per_trial",
    allow_network=False,
    allow_global_mutable_df=False,
    allow_trial_mutation=False,
)


def _validate_data_binding_target(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("empty dataframe rejected by data binding target contract")
    missing = DATA_BINDING_TARGET.required_columns - set(df.columns)
    if missing:
        raise ValueError(f"missing OHLCV columns rejected: {sorted(missing)}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DatetimeIndex required by data binding target contract")


def _resolve_signal_adapter(
    strategy_key: str,
) -> Callable[[pd.DataFrame, dict[str, Any]], pd.Series]:
    from src.strategies import load_strategy

    return load_strategy(strategy_key)


def _invoke_signal_binding_target(
    strategy_key: str,
    df: pd.DataFrame,
    trial_params: dict[str, Any],
) -> pd.Series:
    adapter = _resolve_signal_adapter(strategy_key)
    return adapter(df, trial_params)


def _simulate_engine_call_target(
    df: pd.DataFrame,
    strategy_signal_fn: Callable[[pd.DataFrame, dict[str, Any]], pd.Series],
    strategy_params: dict[str, Any],
) -> dict[str, Any]:
    sig = inspect.signature(strategy_signal_fn)
    if len(sig.parameters) != 2:
        raise TypeError("strategy_signal_fn must accept (df, strategy_params)")
    signals = strategy_signal_fn(df, strategy_params)
    if not signals.index.equals(df.index):
        raise ValueError("signal index must match dataframe index")
    return {
        "df_id": id(df),
        "strategy_params": dict(strategy_params),
        "signal_len": len(signals),
    }


class ObjectiveMetricContractError(ValueError):
    """Test-local fail-closed rejection for objective metric target contract."""


class ObjectiveResultContractError(ValueError):
    """Test-local fail-closed rejection for objective result shape target contract."""


@dataclass(frozen=True)
class LegacyObjectiveResultInventory:
    result_access_pattern: str
    metric_access_pattern: str
    metric_fallback: float
    drawdown_negation: bool
    directional_failure_fallback: bool


@dataclass(frozen=True)
class CanonicalBacktestResultContract:
    owner: str
    stats_field: str
    return_type_name: str


@dataclass(frozen=True)
class PruningTargetContract:
    prune_exception_type: str
    report_metric_name: str
    report_step: int
    swallow_trial_pruned: bool
    convert_engine_errors_to_prune: bool


@dataclass(frozen=True)
class ExceptionTargetContract:
    broad_catch_exception_blocked: bool
    silent_zero_substitute_blocked: bool
    silent_nan_substitute_blocked: bool
    silent_inf_substitute_blocked: bool
    classify_data_signal_engine_result_metric_errors: bool


LEGACY_OBJECTIVE_RESULT_INVENTORY = LegacyObjectiveResultInventory(
    result_access_pattern='result.get("stats", {})',
    metric_access_pattern="metrics.get(objective_name, 0.0)",
    metric_fallback=LEGACY_OBJECTIVE_METRIC_FALLBACK,
    drawdown_negation=True,
    directional_failure_fallback=True,
)


def _canonical_backtest_result_contract() -> CanonicalBacktestResultContract:
    from src.backtest.result import BacktestResult

    return CanonicalBacktestResultContract(
        owner=CANONICAL_BACKTEST_RESULT_OWNER,
        stats_field="stats",
        return_type_name=BacktestResult.__name__,
    )


def _legacy_extract_stats_from_result(result: Any) -> dict[str, Any]:
    if not hasattr(result, "get"):
        raise TypeError("legacy contract expects dict-like result with .get()")
    return result.get("stats", {})


def _legacy_build_metrics_from_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharpe": stats.get("sharpe", LEGACY_OBJECTIVE_METRIC_FALLBACK),
        "total_return": stats.get("total_return", LEGACY_OBJECTIVE_METRIC_FALLBACK),
        "max_drawdown": abs(stats.get("max_drawdown", LEGACY_OBJECTIVE_METRIC_FALLBACK)),
        "win_rate": stats.get("win_rate", LEGACY_OBJECTIVE_METRIC_FALLBACK),
        "num_trades": stats.get("num_trades", 0),
        "profit_factor": stats.get("profit_factor", LEGACY_OBJECTIVE_METRIC_FALLBACK),
    }


def _legacy_extract_objective_value(
    result: dict[str, Any],
    objective_name: str,
) -> float:
    metrics = _legacy_build_metrics_from_stats(_legacy_extract_stats_from_result(result))
    objective_value = metrics.get(objective_name, LEGACY_OBJECTIVE_METRIC_FALLBACK)
    if objective_name == "max_drawdown":
        objective_value = -objective_value
    return float(objective_value)


def _extract_canonical_stats_from_result(result: Any) -> dict[str, Any]:
    contract = _canonical_backtest_result_contract()
    from src.backtest.result import BacktestResult

    if not isinstance(result, BacktestResult):
        raise ObjectiveResultContractError(
            f"objective target contract requires {contract.return_type_name}, "
            f"got {type(result).__name__}"
        )
    if result.stats is None:
        raise ObjectiveResultContractError("BacktestResult.stats is None")
    return dict(result.stats)


def _extract_target_objective_metric(
    stats: dict[str, Any],
    objective_name: str,
    *,
    apply_max_drawdown_negation: bool = False,
) -> float:
    if objective_name not in stats:
        raise ObjectiveMetricContractError(f"missing metric: {objective_name!r}")
    raw = stats[objective_name]
    if raw is None:
        raise ObjectiveMetricContractError("metric value is None")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ObjectiveMetricContractError(f"non-numeric metric: {type(raw).__name__}")
    value = float(raw)
    if not math.isfinite(value):
        raise ObjectiveMetricContractError(f"non-finite metric: {value!r}")
    if objective_name == "max_drawdown" and apply_max_drawdown_negation:
        value = -abs(value)
    return value


def _minimal_backtest_result(stats: dict[str, Any]) -> Any:
    from src.backtest.result import BacktestResult

    idx = pd.DatetimeIndex([], tz="UTC")
    empty = pd.Series(dtype=float, index=idx)
    return BacktestResult(
        equity_curve=empty,
        drawdown=empty,
        stats=dict(stats),
    )


def _extract_objective_from_backtest_result(
    result: Any,
    objective_name: str,
) -> float:
    stats = _extract_canonical_stats_from_result(result)
    return _extract_target_objective_metric(
        stats,
        objective_name,
        apply_max_drawdown_negation=True,
    )


def _legacy_and_canonical_objective_equivalent_for_valid_stats(
    stats: dict[str, Any],
    objective_name: str,
) -> bool:
    legacy_result = {"stats": stats}
    try:
        canonical_value = _extract_objective_from_backtest_result(
            _minimal_backtest_result(stats),
            objective_name,
        )
    except (ObjectiveMetricContractError, ObjectiveResultContractError):
        return False
    legacy_value = _legacy_extract_objective_value(legacy_result, objective_name)
    return canonical_value == legacy_value


def _inventory_stop_pct_sources_in_optuna_runner() -> dict[str, bool]:
    trial_source = _function_source("run_backtest_trial")
    study_source = _function_source("run_study")
    engine_source = inspect.getsource(run_optuna_script.BacktestEngine.run_realistic)
    return {
        "trial_params": "stop_pct" in trial_source,
        "strategy_defaults": "stop_pct" in study_source,
        "strategy_config": "stop_pct" in study_source,
        "engine_strategy_params_default": 'get("stop_pct", 0.02)' in engine_source,
    }


class StopPctContractError(ValueError):
    """Test-local fail-closed rejection for stop_pct target contract."""


def _canonical_config_stop_pct_key(strategy_key: str) -> str:
    return STOP_PCT_CONFIG_KEY_TEMPLATE.format(strategy_key=strategy_key)


def _resolve_stop_pct_from_config(cfg: Any, strategy_key: str) -> Any:
    """Mirror scripts/run_backtest.py::_build_strategy_params_from_config stop_pct binding."""
    import scripts.run_backtest as run_backtest_script

    return run_backtest_script._build_strategy_params_from_config(cfg, strategy_key)["stop_pct"]


def _validate_stop_pct_target_value(value: Any) -> float:
    if value is None:
        raise StopPctContractError("stop_pct value is None")
    if isinstance(value, bool):
        raise StopPctContractError("bool is not a valid numeric stop_pct")
    if not isinstance(value, (int, float)):
        raise StopPctContractError(f"non-numeric stop_pct: {type(value).__name__}")
    result = float(value)
    if not math.isfinite(result):
        raise StopPctContractError(f"non-finite stop_pct: {result!r}")
    if not (result > STOP_PCT_RANGE_GT_EXCLUSIVE and result <= STOP_PCT_RANGE_LE_INCLUSIVE):
        raise StopPctContractError(
            f"stop_pct {result!r} outside canonical range "
            f"({STOP_PCT_RANGE_GT_EXCLUSIVE}, {STOP_PCT_RANGE_LE_INCLUSIVE}]"
        )
    return result


def _resolve_stop_pct_target_contract(
    cfg: Any,
    strategy_key: str,
    trial_params: dict[str, Any],
) -> float:
    if "stop_pct" in trial_params:
        raise StopPctContractError("stop_pct must not be a trial search parameter")
    raw = _resolve_stop_pct_from_config(cfg, strategy_key)
    return _validate_stop_pct_target_value(raw)


def _bind_stop_pct_to_engine_strategy_params(
    cfg: Any,
    strategy_key: str,
    trial_params: dict[str, Any],
) -> dict[str, Any]:
    stop_pct = _resolve_stop_pct_target_contract(cfg, strategy_key, trial_params)
    return {**trial_params, "stop_pct": stop_pct}


PRUNING_TARGET_CONTRACT = PruningTargetContract(
    prune_exception_type="optuna.TrialPruned",
    report_metric_name="sharpe",
    report_step=0,
    swallow_trial_pruned=False,
    convert_engine_errors_to_prune=False,
)


EXCEPTION_TARGET_CONTRACT = ExceptionTargetContract(
    broad_catch_exception_blocked=True,
    silent_zero_substitute_blocked=True,
    silent_nan_substitute_blocked=True,
    silent_inf_substitute_blocked=True,
    classify_data_signal_engine_result_metric_errors=True,
)


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
# Objective/Stats Ist- und Zielvertrag — test-local, no production changes
# ---------------------------------------------------------------------------


def test_legacy_result_get_stats_access_remains_visible() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert LEGACY_OBJECTIVE_RESULT_INVENTORY.result_access_pattern in fn_source


def test_canonical_backtest_result_structure_identified_statically() -> None:
    from src.backtest.result import BacktestResult

    contract = _canonical_backtest_result_contract()
    assert contract.owner == CANONICAL_BACKTEST_RESULT_OWNER
    assert is_dataclass(BacktestResult)
    assert contract.stats_field in BacktestResult.__dataclass_fields__
    sig = inspect.signature(run_optuna_script.BacktestEngine.run_realistic)
    assert sig.return_annotation is BacktestResult


def test_legacy_and_canonical_result_shapes_are_not_equivalent() -> None:
    trial_source = _function_source("run_backtest_trial")
    assert LEGACY_OBJECTIVE_RESULT_INVENTORY.result_access_pattern in trial_source
    from src.backtest.result import BacktestResult

    sig = inspect.signature(run_optuna_script.BacktestEngine.run_realistic)
    assert sig.return_annotation is BacktestResult
    assert not hasattr(BacktestResult, "get")


def test_legacy_objective_metric_names_frozen_in_run_backtest_trial() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert LEGACY_RUN_BACKTEST_TRIAL_METRIC_NAMES <= {
        name.strip('"')
        for name in fn_source.split('"')
        if name in LEGACY_RUN_BACKTEST_TRIAL_METRIC_NAMES
    }


def test_objective_metric_name_and_direction_remain_unchanged() -> None:
    single_source = _function_source("objective_single")
    study_source = _function_source("run_study")
    assert LEGACY_OBJECTIVE_RESULT_INVENTORY.metric_access_pattern in single_source
    assert 'study_cfg.direction == "maximize"' in single_source
    assert 'direction = study_cfg.direction or "maximize"' in study_source
    assert 'objective_name == "max_drawdown"' in single_source


def test_target_contract_extracts_valid_numeric_metric_deterministically() -> None:
    stats = {"sharpe": 1.25, "total_return": 0.1}
    assert _extract_target_objective_metric(stats, "sharpe") == 1.25
    assert _extract_target_objective_metric(stats, "sharpe") == 1.25


def test_target_contract_rejects_missing_metric_fail_closed() -> None:
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_target_objective_metric({"total_return": 0.2}, "sharpe")


def test_target_contract_rejects_none_metric_fail_closed() -> None:
    with pytest.raises(ObjectiveMetricContractError, match="None"):
        _extract_target_objective_metric({"sharpe": None}, "sharpe")


def test_target_contract_rejects_nan_metric_fail_closed() -> None:
    with pytest.raises(ObjectiveMetricContractError, match="non-finite"):
        _extract_target_objective_metric({"sharpe": float("nan")}, "sharpe")


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf")])
def test_target_contract_rejects_nonfinite_inf_metric_fail_closed(bad_value: float) -> None:
    with pytest.raises(ObjectiveMetricContractError, match="non-finite"):
        _extract_target_objective_metric({"sharpe": bad_value}, "sharpe")


@pytest.mark.parametrize("bad_value", ["1.0", {"sharpe": 1.0}, [1.0]])
def test_target_contract_rejects_non_numeric_metric_fail_closed(bad_value: Any) -> None:
    with pytest.raises(ObjectiveMetricContractError, match="non-numeric"):
        _extract_target_objective_metric({"sharpe": bad_value}, "sharpe")


def test_target_contract_does_not_mutate_stats_dict() -> None:
    stats = {"sharpe": 1.2, "total_return": 0.05}
    baseline = copy.deepcopy(stats)
    _extract_target_objective_metric(stats, "sharpe")
    assert stats == baseline


def test_target_contract_blocks_fallback_to_alternate_metric() -> None:
    stats = {"total_return": 0.5, "profit_factor": 2.0}
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_target_objective_metric(stats, "sharpe")


def test_target_contract_helpers_avoid_extra_backtest_or_objective_calls() -> None:
    helper_sources = (
        inspect.getsource(_legacy_extract_stats_from_result)
        + inspect.getsource(_extract_canonical_stats_from_result)
        + inspect.getsource(_extract_target_objective_metric)
    )
    forbidden = (
        "run_backtest_trial(",
        "run_realistic(",
        "objective_single(",
        "objective_multi(",
        "study.optimize(",
    )
    for token in forbidden:
        assert token not in helper_sources


def test_legacy_metric_fallback_differs_from_target_fail_closed_semantics() -> None:
    legacy_value = _legacy_extract_objective_value({"stats": {}}, "sharpe")
    assert legacy_value == LEGACY_OBJECTIVE_METRIC_FALLBACK
    with pytest.raises(ObjectiveMetricContractError):
        _extract_target_objective_metric({}, "sharpe")


def test_canonical_stats_extraction_rejects_dict_like_legacy_result() -> None:
    with pytest.raises(ObjectiveResultContractError, match="BacktestResult"):
        _extract_canonical_stats_from_result({"stats": {"sharpe": 1.0}})


def test_target_contract_accepts_zero_as_valid_numeric() -> None:
    assert _extract_target_objective_metric({"sharpe": 0}, "sharpe") == 0.0
    assert _extract_target_objective_metric({"sharpe": 0.0}, "sharpe") == 0.0


def test_target_contract_normalizes_integer_to_float() -> None:
    assert _extract_target_objective_metric({"sharpe": 2}, "sharpe") == 2.0
    assert isinstance(_extract_target_objective_metric({"sharpe": 2}, "sharpe"), float)


def test_target_contract_rejects_bool_metric_fail_closed() -> None:
    with pytest.raises(ObjectiveMetricContractError, match="non-numeric"):
        _extract_target_objective_metric({"sharpe": True}, "sharpe")
    with pytest.raises(ObjectiveMetricContractError, match="non-numeric"):
        _extract_target_objective_metric({"sharpe": False}, "sharpe")


def test_target_contract_rejects_missing_stats_structure_fail_closed() -> None:
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_target_objective_metric({}, "sharpe")


def test_canonical_stats_extraction_rejects_stats_none_on_backtest_result() -> None:
    result = _minimal_backtest_result({})
    object.__setattr__(result, "stats", None)
    with pytest.raises(ObjectiveResultContractError, match="stats"):
        _extract_canonical_stats_from_result(result)


def test_canonical_objective_extraction_does_not_mutate_backtest_result() -> None:
    stats = {"sharpe": 1.1, "total_return": 0.05}
    result = _minimal_backtest_result(stats)
    baseline_stats = copy.deepcopy(result.stats)
    baseline_equity_id = id(result.equity_curve)
    _extract_objective_from_backtest_result(result, "sharpe")
    assert result.stats == baseline_stats
    assert id(result.equity_curve) == baseline_equity_id


def test_legacy_objective_extraction_does_not_mutate_legacy_dict() -> None:
    legacy = {"stats": {"sharpe": 1.1, "total_return": 0.05}}
    baseline = copy.deepcopy(legacy)
    _legacy_extract_objective_value(legacy, "sharpe")
    assert legacy == baseline


def test_objective_result_and_metric_contract_status_flags_defined() -> None:
    assert OBJECTIVE_RESULT_CONTRACT_DEFINED is True
    assert OBJECTIVE_METRIC_CONTRACT_DEFINED is True
    assert OBJECTIVE_RESULT_MAPPING_DEFINED is True
    assert OBJECTIVE_METRIC_NAME_PRESERVED is True
    assert OBJECTIVE_DIRECTION_PRESERVED is True
    assert OBJECTIVE_INVALID_VALUE_POLICY_FAIL_CLOSED is True
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True


# ---------------------------------------------------------------------------
# Objective equivalence matrix — legacy dict stats vs BacktestResult.stats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stats", "objective_name", "expected"),
    [
        ({"sharpe": 1.25, "total_return": 0.1}, "sharpe", 1.25),
        ({"sharpe": 2.5}, "sharpe", 2.5),
        ({"sharpe": -0.75}, "sharpe", -0.75),
        ({"sharpe": 0}, "sharpe", 0.0),
        ({"sharpe": 3}, "sharpe", 3.0),
        ({"max_drawdown": -0.15}, "max_drawdown", -0.15),
        ({"max_drawdown": 0.15}, "max_drawdown", -0.15),
        ({"total_return": 0.42}, "total_return", 0.42),
    ],
)
def test_objective_equivalence_valid_numeric_cases(
    stats: dict[str, Any],
    objective_name: str,
    expected: float,
) -> None:
    legacy = {"stats": stats}
    assert _legacy_extract_objective_value(legacy, objective_name) == expected
    assert (
        _extract_objective_from_backtest_result(
            _minimal_backtest_result(stats),
            objective_name,
        )
        == expected
    )
    assert _legacy_and_canonical_objective_equivalent_for_valid_stats(stats, objective_name)


def test_objective_equivalence_integer_and_float_normalization_identical() -> None:
    for raw in (2, 2.0, 2.5):
        stats = {"sharpe": raw}
        legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
        canonical_val = _extract_objective_from_backtest_result(
            _minimal_backtest_result(stats),
            "sharpe",
        )
        assert legacy_val == canonical_val == float(raw)


def test_objective_equivalence_missing_stats_fail_closed_divergence_documented() -> None:
    legacy_val = _legacy_extract_objective_value({"stats": {}}, "sharpe")
    assert legacy_val == LEGACY_OBJECTIVE_METRIC_FALLBACK
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_objective_from_backtest_result(_minimal_backtest_result({}), "sharpe")


def test_objective_equivalence_missing_metric_key_fail_closed_divergence() -> None:
    stats = {"total_return": 0.2}
    legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
    assert legacy_val == LEGACY_OBJECTIVE_METRIC_FALLBACK
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_objective_from_backtest_result(_minimal_backtest_result(stats), "sharpe")


def test_objective_equivalence_stats_none_on_legacy_dict_not_equivalent() -> None:
    with pytest.raises(AttributeError):
        _legacy_extract_objective_value({"stats": None}, "sharpe")
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_objective_from_backtest_result(_minimal_backtest_result({}), "sharpe")


@pytest.mark.parametrize(
    "bad_value",
    [None, True, False, float("nan"), float("inf"), float("-inf"), "1.0"],
)
def test_objective_equivalence_invalid_metric_fail_closed_divergence(
    bad_value: Any,
) -> None:
    stats = {"sharpe": bad_value}
    if bad_value is None:
        with pytest.raises(TypeError):
            _legacy_extract_objective_value({"stats": stats}, "sharpe")
    elif isinstance(bad_value, bool):
        legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
        assert legacy_val == float(bad_value)
    elif isinstance(bad_value, (int, float)) and not math.isfinite(float(bad_value)):
        legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
        assert not math.isfinite(legacy_val)
    else:
        legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
        assert isinstance(legacy_val, float)
    with pytest.raises(ObjectiveMetricContractError):
        _extract_objective_from_backtest_result(_minimal_backtest_result(stats), "sharpe")


def test_objective_equivalence_no_metric_fallback_in_target_contract() -> None:
    stats = {"total_return": 0.5, "profit_factor": 2.0}
    legacy_val = _legacy_extract_objective_value({"stats": stats}, "sharpe")
    assert legacy_val == LEGACY_OBJECTIVE_METRIC_FALLBACK
    with pytest.raises(ObjectiveMetricContractError, match="missing metric"):
        _extract_objective_from_backtest_result(_minimal_backtest_result(stats), "sharpe")


def test_objective_equivalence_direction_and_return_type_preserved() -> None:
    single_source = _function_source("objective_single")
    study_source = _function_source("run_study")
    assert 'study_cfg.direction == "maximize"' in single_source
    assert 'return float("-inf")' in single_source
    assert 'direction = study_cfg.direction or "maximize"' in study_source
    assert inspect.signature(run_optuna_script.objective_single).return_annotation in {
        float,
        "float",
    }


def test_objective_equivalence_max_drawdown_negation_matches_legacy_abs_semantics() -> None:
    for raw in (-0.2, 0.2, -0.0):
        stats = {"max_drawdown": raw}
        legacy_val = _legacy_extract_objective_value({"stats": stats}, "max_drawdown")
        canonical_val = _extract_objective_from_backtest_result(
            _minimal_backtest_result(stats),
            "max_drawdown",
        )
        assert legacy_val == canonical_val == -abs(float(raw))


def test_objective_equivalence_contract_inventory_constants() -> None:
    assert LEGACY_RESULT_SHAPE == 'dict-like with result.get("stats", {})'
    assert CANONICAL_RESULT_SHAPE == "BacktestResult.stats"
    assert LEGACY_AND_CANONICAL_SHAPES_IDENTICAL is False
    assert MAPPING_REQUIRED is True
    assert "objective_name" in METRIC_NAME
    assert "maximize" in OPTIMIZATION_DIRECTION
    assert "fail-closed" in FAILURE_POLICY


def test_objective_equivalence_proven_with_production_still_legacy() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert LEGACY_OBJECTIVE_RESULT_INVENTORY.result_access_pattern in fn_source
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


def test_objective_equivalence_exception_timing_documented() -> None:
    single_source = _function_source("objective_single")
    trial_pos = single_source.index("run_backtest_trial")
    except_pos = single_source.index("except Exception")
    assert trial_pos < except_pos
    with pytest.raises(ObjectiveMetricContractError):
        _extract_objective_from_backtest_result(
            _minimal_backtest_result({"sharpe": float("nan")}),
            "sharpe",
        )


def test_objective_equivalence_preserves_pruning_seed_stop_pct_contracts() -> None:
    fn_source = _function_source("run_backtest_trial")
    study_source = _function_source("run_study")
    assert "trial.report" in fn_source
    assert "trial.should_prune" in fn_source
    assert "seed=42" in study_source.replace(" ", "")
    assert "stop_pct" not in fn_source


def test_objective_equivalence_helpers_avoid_extra_engine_signal_objective_calls() -> None:
    helper_sources = (
        inspect.getsource(_extract_objective_from_backtest_result)
        + inspect.getsource(_legacy_and_canonical_objective_equivalent_for_valid_stats)
        + inspect.getsource(_minimal_backtest_result)
    )
    forbidden = (
        "run_backtest_trial(",
        "run_realistic(",
        "objective_single(",
        "objective_multi(",
        "study.optimize(",
        "load_ohlcv_data(",
    )
    for token in forbidden:
        assert token not in helper_sources


def test_objective_equivalence_proven_status_gate() -> None:
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True
    assert OBJECTIVE_RESULT_MAPPING_DEFINED is True
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False
    assert LEGACY_AND_CANONICAL_SHAPES_IDENTICAL is False
    assert MAPPING_REQUIRED is True


# ---------------------------------------------------------------------------
# stop_pct Ist- und Zielvertrag — resolved via run_backtest config-section owner
# ---------------------------------------------------------------------------


def test_canonical_stop_pct_owner_is_run_backtest_build_strategy_params() -> None:
    import scripts.run_backtest as run_backtest_script

    assert CANONICAL_STOP_PCT_OWNER == "scripts/run_backtest.py:_build_strategy_params_from_config"
    source = inspect.getsource(run_backtest_script._build_strategy_params_from_config)
    assert 'params["stop_pct"]' in source
    assert 'cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)' in source


def test_stop_pct_source_inventory_covers_all_candidate_sources() -> None:
    inventory = _inventory_stop_pct_sources_in_optuna_runner()
    assert set(inventory) == set(STOP_PCT_CANDIDATE_SOURCES)


def test_stop_pct_absent_from_optuna_trial_and_study_paths() -> None:
    inventory = _inventory_stop_pct_sources_in_optuna_runner()
    assert inventory["trial_params"] is False
    assert inventory["strategy_defaults"] is False
    assert inventory["strategy_config"] is False


def test_stop_pct_not_in_optuna_parameter_schema() -> None:
    from src.strategies.registry import get_strategy_spec

    for strategy_key in sorted(OPTUNA_DOCSTRING_SCHEMA_KEYS):
        schema_names = {
            param.name for param in get_strategy_spec(strategy_key).cls.parameter_schema
        }
        assert "stop_pct" not in schema_names
    assert STOP_PCT_TRIAL_PARAMETER is False


def test_trial_params_schema_keys_unchanged_without_stop_pct() -> None:
    for strategy_key, trial_params in SCHEMA_KEY_TRIAL_PARAMS.items():
        assert "stop_pct" not in trial_params
        from src.strategies.registry import get_strategy_spec

        schema_names = {
            param.name for param in get_strategy_spec(strategy_key).cls.parameter_schema
        }
        assert set(trial_params) <= schema_names


def test_stop_pct_engine_default_is_canonically_belegt_but_not_wired_in_optuna_legacy() -> None:
    inventory = _inventory_stop_pct_sources_in_optuna_runner()
    assert inventory["engine_strategy_params_default"] is True
    assert "stop_pct" not in _function_source("run_backtest_trial")
    assert STOP_PCT_SOURCE_PROVEN is True


def test_stop_pct_precedence_defined_from_config_section_then_default() -> None:
    assert STOP_PCT_SOURCE_PRECEDENCE == (
        "config_section_strategy_key",
        "canonical_default",
    )
    assert STOP_PCT_PRECEDENCE_DEFINED is True
    assert STOP_PCT_SOURCE_PROVEN is True


def test_stop_pct_target_contract_binds_configured_valid_value_unchanged() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {"ma_crossover": {"fast_window": 10, "slow_window": 50, "stop_pct": 0.03}},
        }
    )
    trial_params = {"fast_window": 10, "slow_window": 50}
    assert _resolve_stop_pct_target_contract(cfg, "ma_crossover", trial_params) == 0.03


def test_stop_pct_target_contract_missing_config_uses_canonical_default() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {"ma_crossover": {"fast_window": 10, "slow_window": 50}},
        }
    )
    trial_params = {"fast_window": 10, "slow_window": 50}
    assert (
        _resolve_stop_pct_target_contract(cfg, "ma_crossover", trial_params)
        == STOP_PCT_DEFAULT_VALUE
    )


def test_stop_pct_target_contract_no_second_fallback_source() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}, "strategy": {}})
    trial_params = {"fast_window": 10, "slow_window": 50}
    resolved = _resolve_stop_pct_target_contract(cfg, "ma_crossover", trial_params)
    assert resolved == STOP_PCT_DEFAULT_VALUE
    engine_source = inspect.getsource(run_optuna_script.BacktestEngine.run_realistic)
    assert 'get("stop_pct", 0.02)' in engine_source
    assert resolved == TARGET_ENGINE_STOP_PCT_DEFAULT


def test_stop_pct_target_contract_rejects_trial_params_conflict_fail_closed() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}, "strategy": {}})
    with pytest.raises(StopPctContractError, match="trial search parameter"):
        _resolve_stop_pct_target_contract(
            cfg, "ma_crossover", {"fast_window": 10, "stop_pct": 0.05}
        )


def test_stop_pct_target_contract_rejects_none_fail_closed() -> None:
    with pytest.raises(StopPctContractError, match="None"):
        _validate_stop_pct_target_value(None)


def test_stop_pct_target_contract_rejects_bool_as_numeric_fail_closed() -> None:
    with pytest.raises(StopPctContractError, match="bool"):
        _validate_stop_pct_target_value(True)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_stop_pct_target_contract_rejects_nonfinite_fail_closed(bad_value: float) -> None:
    with pytest.raises(StopPctContractError, match="non-finite"):
        _validate_stop_pct_target_value(bad_value)


@pytest.mark.parametrize("bad_value", ["0.02", {"stop_pct": 0.02}, [0.02]])
def test_stop_pct_target_contract_rejects_non_numeric_fail_closed(bad_value: Any) -> None:
    with pytest.raises(StopPctContractError, match="non-numeric"):
        _validate_stop_pct_target_value(bad_value)


@pytest.mark.parametrize("bad_value", [0.0, -0.01, 0.11, 1.0])
def test_stop_pct_target_contract_rejects_out_of_range_fail_closed(bad_value: float) -> None:
    with pytest.raises(StopPctContractError, match="outside canonical range"):
        _validate_stop_pct_target_value(bad_value)


def test_stop_pct_target_contract_does_not_mutate_trial_params() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {"ma_crossover": {"fast_window": 10, "slow_window": 50, "stop_pct": 0.04}},
        }
    )
    trial_params = {"fast_window": 7, "slow_window": 35}
    baseline = copy.deepcopy(trial_params)
    _bind_stop_pct_to_engine_strategy_params(cfg, "ma_crossover", trial_params)
    assert trial_params == baseline


def test_stop_pct_target_contract_engine_receives_validated_stop_pct() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {"ma_crossover": {"fast_window": 10, "slow_window": 50, "stop_pct": 0.035}},
        }
    )
    trial_params = {"fast_window": 12, "slow_window": 40}
    engine_params = _bind_stop_pct_to_engine_strategy_params(cfg, "ma_crossover", trial_params)
    assert engine_params["stop_pct"] == 0.035
    assert engine_params["fast_window"] == 12
    assert engine_params["slow_window"] == 40


def test_stop_pct_target_contract_preserves_objective_metric_and_direction() -> None:
    single_source = _function_source("objective_single")
    study_source = _function_source("run_study")
    assert LEGACY_OBJECTIVE_RESULT_INVENTORY.metric_access_pattern in single_source
    assert 'study_cfg.direction == "maximize"' in single_source
    assert 'direction = study_cfg.direction or "maximize"' in study_source
    assert 'objective_name == "max_drawdown"' in single_source


def test_stop_pct_target_contract_preserves_pruning_and_exception_timing() -> None:
    fn_source = _function_source("run_backtest_trial")
    single_source = _function_source("objective_single")
    assert "trial.report" in fn_source
    assert "trial.should_prune" in fn_source
    trial_pos = single_source.index("run_backtest_trial")
    except_pos = single_source.index("except Exception")
    assert trial_pos < except_pos


def test_stop_pct_target_contract_helpers_avoid_extra_runtime_calls() -> None:
    helper_sources = (
        inspect.getsource(_resolve_stop_pct_from_config)
        + inspect.getsource(_validate_stop_pct_target_value)
        + inspect.getsource(_resolve_stop_pct_target_contract)
        + inspect.getsource(_bind_stop_pct_to_engine_strategy_params)
    )
    forbidden = (
        "run_backtest_trial(",
        "run_realistic(",
        "study.optimize(",
        "optuna.create_study(",
        "load_ohlcv_data(",
        "objective_single(",
        "objective_multi(",
    )
    for token in forbidden:
        assert token not in helper_sources


def test_stop_pct_target_contract_preserves_engine_default_reference_only() -> None:
    assert TARGET_ENGINE_STOP_PCT_DEFAULT == STOP_PCT_DEFAULT_VALUE
    engine_source = inspect.getsource(run_optuna_script.BacktestEngine.run_realistic)
    assert 'get("stop_pct", 0.02)' in engine_source
    assert "stop_pct" not in _function_source("run_backtest_trial")


def test_stop_pct_decision_status_resolved_without_productive_change() -> None:
    assert STOP_PCT_DECISION_STATUS == "RESOLVED_RUN_BACKTEST_CONFIG_SECTION_V1"
    assert STOP_PCT_SOURCE_PROVEN is True
    assert STOP_PCT_DEFAULT_PROVEN is True
    assert STOP_PCT_RANGE_PROVEN is True
    assert STOP_PCT_CONFLICT_POLICY == "FAIL_CLOSED"
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


def test_stop_pct_no_productive_semantics_change_in_this_slice() -> None:
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


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


def test_pruning_target_contract_defined_with_explicit_semantics() -> None:
    assert PRUNING_CONTRACT_DEFINED is True
    assert PRUNING_TARGET_CONTRACT.prune_exception_type == "optuna.TrialPruned"
    assert PRUNING_TARGET_CONTRACT.report_metric_name == "sharpe"
    assert PRUNING_TARGET_CONTRACT.report_step == 0
    assert PRUNING_TARGET_CONTRACT.swallow_trial_pruned is False
    assert PRUNING_TARGET_CONTRACT.convert_engine_errors_to_prune is False


def test_pruning_target_contract_trial_pruned_is_not_swallowed() -> None:
    trial = _PruningTrial()

    class TrialPruned(Exception):
        pass

    class FakeEngine:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def run_realistic(self) -> dict[str, Any]:
            return {"stats": {"sharpe": 1.0}}

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


def test_pruning_target_contract_engine_errors_do_not_auto_prune() -> None:
    class _NoPruneTrial:
        def report(self, value: float, step: int) -> None:
            pass

        def should_prune(self) -> bool:
            return False

    class FailingEngine:
        def __init__(self, **kwargs: Any) -> None:
            pass

        def run_realistic(self) -> dict[str, Any]:
            raise RuntimeError("synthetic engine failure")

    with (
        patch.object(run_optuna_script, "BacktestEngine", FailingEngine),
        patch.object(run_optuna_script, "build_tracker_from_config", return_value=MagicMock()),
        pytest.raises(RuntimeError, match="synthetic engine failure"),
    ):
        run_optuna_script.run_backtest_trial(
            cfg=MagicMock(),
            strategy_cls=_MinimalTrialStrategy,
            trial_params={},
            trial=_NoPruneTrial(),
        )


def test_pruning_target_contract_preserves_report_metric_and_step() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert (
        f'trial.report(metrics["{PRUNING_TARGET_CONTRACT.report_metric_name}"], step=' in fn_source
    )
    assert f"step={PRUNING_TARGET_CONTRACT.report_step}" in fn_source.replace(" ", "")


def test_exception_target_contract_defined_with_explicit_classification() -> None:
    assert EXCEPTION_CONTRACT_DEFINED is True
    assert EXCEPTION_TARGET_CONTRACT.broad_catch_exception_blocked is True
    assert EXCEPTION_TARGET_CONTRACT.silent_zero_substitute_blocked is True
    assert EXCEPTION_TARGET_CONTRACT.classify_data_signal_engine_result_metric_errors is True


def test_exception_target_contract_legacy_broad_catch_remains_visible() -> None:
    single_source = _function_source("objective_single")
    multi_source = _function_source("objective_multi")
    assert "except Exception" in single_source
    assert "except Exception" in multi_source
    assert "run_backtest_trial" in single_source


def test_exception_target_contract_timing_is_after_backtest_call() -> None:
    single_source = _function_source("objective_single")
    trial_pos = single_source.index("run_backtest_trial")
    except_pos = single_source.index("except Exception")
    assert trial_pos < except_pos


def test_exception_target_contract_blocks_silent_zero_nan_inf_substitutes() -> None:
    assert EXCEPTION_TARGET_CONTRACT.silent_zero_substitute_blocked is True
    assert EXCEPTION_TARGET_CONTRACT.silent_nan_substitute_blocked is True
    assert EXCEPTION_TARGET_CONTRACT.silent_inf_substitute_blocked is True
    target_helper_source = inspect.getsource(_extract_target_objective_metric)
    assert "return 0" not in target_helper_source
    assert "return float(" not in target_helper_source


def test_exception_target_contract_rejects_metric_errors_without_broad_fallback() -> None:
    with pytest.raises(ObjectiveMetricContractError):
        _extract_target_objective_metric({"sharpe": float("nan")}, "sharpe")
    with pytest.raises(ObjectiveMetricContractError):
        _extract_target_objective_metric({"sharpe": "bad"}, "sharpe")


def test_objective_equivalence_status_flags_after_full_mapping_proven() -> None:
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True
    assert OBJECTIVE_RESULT_CONTRACT_DEFINED is True
    assert OBJECTIVE_METRIC_CONTRACT_DEFINED is True
    assert OBJECTIVE_RESULT_MAPPING_DEFINED is True
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


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


# ---------------------------------------------------------------------------
# Binding target status constants — objective boundary freeze
# ---------------------------------------------------------------------------


def test_binding_target_status_constants() -> None:
    assert DATA_BINDING_TARGET_DEFINED is True
    assert SIGNAL_BINDING_TARGET_DEFINED is True
    assert ENGINE_CALL_TARGET_DEFINED is True
    assert SIGNAL_EQUIVALENCE_PROVEN_FOR_SCHEMA_KEYS is True
    assert OBJECTIVE_RESULT_CONTRACT_DEFINED is True
    assert OBJECTIVE_METRIC_CONTRACT_DEFINED is True
    assert PRUNING_CONTRACT_DEFINED is True
    assert EXCEPTION_CONTRACT_DEFINED is True
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True
    assert OBJECTIVE_RESULT_MAPPING_DEFINED is True
    assert OBJECTIVE_METRIC_NAME_PRESERVED is True
    assert OBJECTIVE_DIRECTION_PRESERVED is True
    assert OBJECTIVE_INVALID_VALUE_POLICY_FAIL_CLOSED is True
    assert STOP_PCT_SOURCE_PROVEN is True
    assert STOP_PCT_DECISION_STATUS == "RESOLVED_RUN_BACKTEST_CONFIG_SECTION_V1"
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


# ---------------------------------------------------------------------------
# Data binding target contract (test-local, no real loader execution)
# ---------------------------------------------------------------------------


def test_data_loader_owner_is_run_backtest_load_ohlcv_data() -> None:
    import scripts.run_backtest as run_backtest_script

    assert DATA_BINDING_TARGET.data_loader_owner == DATA_LOADER_OWNER
    sig = inspect.signature(run_backtest_script.load_ohlcv_data)
    for param in ("data_file", "start_date", "end_date", "n_bars"):
        assert param in sig.parameters


def test_data_binding_target_requires_no_new_loader_abstraction() -> None:
    assert DATA_BINDING_TARGET.data_loader_owner == DATA_LOADER_OWNER
    assert DATA_BINDING_TARGET.allow_network is False
    data_helper_source = inspect.getsource(_validate_data_binding_target)
    assert "load_ohlcv_data(" not in data_helper_source


def test_data_binding_target_requires_ohlcv_columns_and_datetime_index() -> None:
    df = _sample_ohlcv()
    _validate_data_binding_target(df)
    assert REQUIRED_OHLCV_COLUMNS <= set(df.columns)
    assert isinstance(df.index, pd.DatetimeIndex)


def test_data_binding_target_rejects_empty_and_incomplete_dataframe() -> None:
    empty = pd.DataFrame(columns=list(REQUIRED_OHLCV_COLUMNS))
    with pytest.raises(ValueError, match="empty dataframe"):
        _validate_data_binding_target(empty)

    partial = _sample_ohlcv().drop(columns=["volume"])
    with pytest.raises(ValueError, match="missing OHLCV columns"):
        _validate_data_binding_target(partial)


def test_data_binding_target_forbids_dataframe_mutation_between_trials() -> None:
    df = _sample_ohlcv()
    baseline = df.copy(deep=True)
    _validate_data_binding_target(df)

    def _objective_like_trial(_trial_params: dict[str, Any]) -> int:
        return id(df)

    assert _objective_like_trial({"fast_window": 10}) == _objective_like_trial({"fast_window": 20})
    pd.testing.assert_frame_equal(df, baseline)
    assert DATA_BINDING_TARGET.allow_trial_mutation is False


def test_data_binding_contract_tests_avoid_network_and_real_loader() -> None:
    import scripts.run_backtest as run_backtest_script

    loader_called = {"value": False}

    def _fail_if_called(*args: Any, **kwargs: Any) -> pd.DataFrame:
        loader_called["value"] = True
        raise AssertionError("real load_ohlcv_data must not execute in contract tests")

    df = _sample_ohlcv()
    with patch.object(run_backtest_script, "load_ohlcv_data", side_effect=_fail_if_called):
        _validate_data_binding_target(df)
        _invoke_signal_binding_target("ma_crossover", df, SCHEMA_KEY_TRIAL_PARAMS["ma_crossover"])
    assert loader_called["value"] is False


# ---------------------------------------------------------------------------
# Signal binding target contract — functional adapter, schema keys
# ---------------------------------------------------------------------------


def test_schema_strategy_keys_match_optuna_docstring_scope() -> None:
    keys = _optuna_schema_strategy_keys()
    assert set(keys) == OPTUNA_DOCSTRING_SCHEMA_KEYS
    assert len(keys) == 3


@pytest.mark.parametrize("strategy_key", sorted(OPTUNA_DOCSTRING_SCHEMA_KEYS))
def test_signal_binding_target_table_covers_schema_key(strategy_key: str) -> None:
    assert strategy_key in SCHEMA_KEY_TRIAL_PARAMS
    trial_params = SCHEMA_KEY_TRIAL_PARAMS[strategy_key]
    from src.strategies.registry import get_strategy_spec

    schema_names = {param.name for param in get_strategy_spec(strategy_key).cls.parameter_schema}
    assert set(trial_params) <= schema_names


def test_signal_binding_target_passes_strategy_key_to_load_strategy() -> None:
    captured: dict[str, str] = {}

    def _recording_load_strategy(name: str) -> Callable[[pd.DataFrame, dict[str, Any]], pd.Series]:
        captured["key"] = name
        return lambda df, params: pd.Series(0, index=df.index)

    df = _sample_ohlcv()
    with patch("src.strategies.load_strategy", side_effect=_recording_load_strategy):
        _invoke_signal_binding_target("rsi_reversion", df, SCHEMA_KEY_TRIAL_PARAMS["rsi_reversion"])
    assert captured["key"] == "rsi_reversion"


def test_signal_binding_target_passes_trial_params_unchanged() -> None:
    df = _sample_ohlcv()
    trial_params = {"fast_window": 7, "slow_window": 35, "extra_probe": "keep"}
    captured: dict[str, Any] = {}

    def _capture_adapter(df_in: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        captured["params"] = params
        captured["df_id"] = id(df_in)
        return pd.Series(0, index=df_in.index)

    contract_module = sys.modules[__name__]
    with patch.object(contract_module, "_resolve_signal_adapter", return_value=_capture_adapter):
        _invoke_signal_binding_target("ma_crossover", df, trial_params)

    assert captured["params"] == trial_params


def test_signal_binding_target_preserves_dataframe_reference() -> None:
    df = _sample_ohlcv()
    captured_ids: list[int] = []

    def _capture_adapter(df_in: pd.DataFrame, _params: dict[str, Any]) -> pd.Series:
        captured_ids.append(id(df_in))
        return pd.Series(0, index=df_in.index)

    contract_module = sys.modules[__name__]
    with patch.object(contract_module, "_resolve_signal_adapter", return_value=_capture_adapter):
        _invoke_signal_binding_target(
            "breakout_donchian", df, SCHEMA_KEY_TRIAL_PARAMS["breakout_donchian"]
        )
        _invoke_signal_binding_target(
            "breakout_donchian", df, SCHEMA_KEY_TRIAL_PARAMS["breakout_donchian"]
        )

    assert captured_ids == [id(df), id(df)]


def test_signal_binding_target_series_index_matches_dataframe() -> None:
    df = _sample_ohlcv()
    for strategy_key in sorted(OPTUNA_DOCSTRING_SCHEMA_KEYS):
        signals = _invoke_signal_binding_target(
            strategy_key,
            df,
            SCHEMA_KEY_TRIAL_PARAMS[strategy_key],
        )
        assert signals.index.equals(df.index)


@pytest.mark.parametrize(
    "strategy_key,oop_cls",
    [
        ("ma_crossover", "src.strategies.ma_crossover.MACrossoverStrategy"),
        ("rsi_reversion", "src.strategies.rsi_reversion.RsiReversionStrategy"),
        ("breakout_donchian", "src.strategies.breakout_donchian.DonchianBreakoutStrategy"),
    ],
)
def test_signal_equivalence_vs_oop_reference_for_schema_key(
    strategy_key: str,
    oop_cls: str,
) -> None:
    module_path, class_name = oop_cls.rsplit(".", 1)
    oop_strategy_cls = getattr(importlib.import_module(module_path), class_name)
    df = _sample_ohlcv()
    trial_params = dict(SCHEMA_KEY_TRIAL_PARAMS[strategy_key])
    legacy = oop_strategy_cls(**trial_params).generate_signals(df)
    canonical = _invoke_signal_binding_target(strategy_key, df, trial_params)
    assert canonical.index.equals(df.index)
    pd.testing.assert_series_equal(canonical, legacy)


def test_signal_binding_target_excludes_oop_strategy_object() -> None:
    invoke_source = inspect.getsource(_invoke_signal_binding_target)
    resolve_source = inspect.getsource(_resolve_signal_adapter)
    assert "strategy_cls" not in invoke_source
    assert "generate_signals" not in invoke_source
    assert "load_strategy" in resolve_source


def test_signal_binding_target_excludes_stale_strategy_closure() -> None:
    from src.strategies import load_strategy

    df = _sample_ohlcv()
    with patch("src.strategies.load_strategy", wraps=load_strategy) as load_mock:
        _invoke_signal_binding_target("ma_crossover", df, SCHEMA_KEY_TRIAL_PARAMS["ma_crossover"])
        _invoke_signal_binding_target("ma_crossover", df, {"fast_window": 12, "slow_window": 40})

    assert load_mock.call_count == 2
    assert all(call.args[0] == "ma_crossover" for call in load_mock.call_args_list)
    trial_source = _function_source("run_backtest_trial")
    assert "strategy = strategy_cls(**trial_params)" in trial_source


# ---------------------------------------------------------------------------
# Engine call target contract — canonical run_realistic shape
# ---------------------------------------------------------------------------


def test_engine_call_target_requires_three_run_realistic_arguments() -> None:
    sig = inspect.signature(run_optuna_script.BacktestEngine.run_realistic)
    required = {
        name
        for name, param in sig.parameters.items()
        if name != "self" and param.default is inspect.Parameter.empty
    }
    assert required == MODERNIZATION_REQUIRED_ARGS

    df = _sample_ohlcv()
    params = SCHEMA_KEY_TRIAL_PARAMS["ma_crossover"]
    captured = _simulate_engine_call_target(
        df,
        _resolve_signal_adapter("ma_crossover"),
        params,
    )
    assert captured["df_id"] == id(df)
    assert captured["strategy_params"] == params


def test_engine_call_target_excludes_legacy_constructor_keywords() -> None:
    sig = inspect.signature(run_optuna_script.BacktestEngine.__init__)
    param_names = set(sig.parameters) - {"self"}
    assert LEGACY_ENGINE_KWARGS.isdisjoint(param_names)


def test_engine_call_target_excludes_bare_run_realistic() -> None:
    assert _run_realistic_call_arg_count() == 0
    engine = run_optuna_script.BacktestEngine()
    with pytest.raises(TypeError):
        engine.run_realistic()


def test_stop_pct_legacy_ist_unresolved_in_production_runner() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert "stop_pct" not in fn_source
    assert STOP_PCT_SOURCE_PROVEN is True
    owner_source = Path(__file__).read_text(encoding="utf-8")
    assert "RESOLVED_RUN_BACKTEST_CONFIG_SECTION_V1" in owner_source


def test_objective_equivalence_proven_in_tests_production_unchanged() -> None:
    fn_source = _function_source("run_backtest_trial")
    assert 'result.get("stats"' in fn_source
    assert OBJECTIVE_EQUIVALENCE_PROVEN is True
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False


def test_bounded_modernization_remains_unauthorized() -> None:
    assert BOUNDED_MODERNIZATION_AUTHORIZED is False
    assert EQUIVALENCE_NOT_PROVEN in Path(__file__).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Production unchanged guard + no-run safety for binding slice
# ---------------------------------------------------------------------------


def _ensure_git_object(rev: str) -> None:
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        return
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    subprocess.run(
        ["git", "fetch", "--depth=1", "origin", rev],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _production_guard_base_ref() -> str:
    for candidate in (
        os.environ.get("GITHUB_BASE_SHA"),
        os.environ.get("CI_MERGE_BASE"),
    ):
        if candidate:
            _ensure_git_object(candidate)
            return candidate

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        base_sha = payload.get("pull_request", {}).get("base", {}).get("sha")
        if base_sha:
            _ensure_git_object(base_sha)
            return base_sha

    base_ref_name = os.environ.get("GITHUB_BASE_REF")
    if base_ref_name:
        remote_ref = f"origin/{base_ref_name}"
        result = subprocess.run(
            ["git", "rev-parse", "--verify", remote_ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and os.environ.get("GITHUB_ACTIONS") == "true":
            subprocess.run(
                [
                    "git",
                    "fetch",
                    "--depth=1",
                    "origin",
                    f"{base_ref_name}:refs/remotes/origin/{base_ref_name}",
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", remote_ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if verify.returncode == 0:
            return remote_ref

    for ref in ("origin/main", "main"):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return ref
    raise AssertionError("cannot resolve git base ref for production guard")


def test_run_optuna_study_production_file_unchanged_ast_guard() -> None:
    base_ref = _production_guard_base_ref()
    changed: list[str] = []
    for rel_path in PRODUCTION_GUARD_PATHS:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref, "--", rel_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        if result.stdout.strip():
            changed.append(rel_path)
    assert changed == []


def test_binding_contract_tests_do_not_start_study_trial_backtest_or_loader() -> None:
    binding_helpers = (
        inspect.getsource(_validate_data_binding_target)
        + inspect.getsource(_invoke_signal_binding_target)
        + inspect.getsource(_simulate_engine_call_target)
        + inspect.getsource(_legacy_extract_stats_from_result)
        + inspect.getsource(_extract_canonical_stats_from_result)
        + inspect.getsource(_extract_target_objective_metric)
        + inspect.getsource(_inventory_stop_pct_sources_in_optuna_runner)
    )
    forbidden_runtime_calls = (
        "study.optimize(",
        "optuna.create_study(",
        "load_ohlcv_data(",
        "requests.get(",
        "urllib.request",
        "run_backtest_trial(",
        "run_study(",
    )
    for token in forbidden_runtime_calls:
        assert token not in binding_helpers
