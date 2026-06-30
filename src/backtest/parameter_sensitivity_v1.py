"""
Deterministic offline parameter sensitivity v1 (RUNBOOK STEP 29M).

Fail-closed bounded grid contract, full-grid persistence, and train/validation/OOS
evaluation binding for EconomicViabilityEvidenceV1. Pipeline pass does not imply
parameter-robustness policy pass or economic validity.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.cost_config_v0 import FUNDING_MODEL_VERSION
from src.backtest.economic_validity_policy_v1 import (
    POLICY_THRESHOLD_STATUS_BLOCKED,
    POLICY_THRESHOLD_STATUS_PASS,
    EconomicValidityPolicyV1,
    resolve_economic_validity_policy_v1,
)
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
)

PARAMETER_SENSITIVITY_VERSION = "backtest_parameter_sensitivity_v1"
PARAMETER_SENSITIVITY_OWNER = "backtest.parameter_sensitivity_v1"
DEFAULT_GRID_ID = "step29m_bounded_cost_sensitivity_v1"
DEFAULT_GRID_VERSION = "v1"
MIN_BARS_PER_SPLIT = 4
TRAIN_FRACTION = 0.50
VALIDATION_FRACTION = 0.25

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})
_CFG_PARAM_PATHS: dict[str, tuple[str, ...]] = {
    "fee_bps": ("backtest", "fee_bps"),
    "slippage_bps": ("backtest", "slippage_bps"),
    "risk_per_trade": ("risk", "risk_per_trade"),
}


class ParameterSensitivityError(ValueError):
    """Fail-closed parameter sensitivity error."""


class PipelineStatus(str, Enum):
    PIPELINE_PASS = "PIPELINE_PASS"
    PIPELINE_BLOCKED = "PIPELINE_BLOCKED"
    PIPELINE_FAILED = "PIPELINE_FAILED"


class EvaluationStatus(str, Enum):
    EVALUATED = "EVALUATED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class MetricValueStatus(str, Enum):
    COMPUTED = "COMPUTED"
    UNKNOWN = "UNKNOWN"
    NOT_COMPUTED = "NOT_COMPUTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ParameterSensitivityGridV1:
    grid_id: str
    grid_version: str
    strategy_id: str
    strategy_version: str
    canonical_trading_logic_version: str
    parameter_names: tuple[str, ...]
    parameter_values: tuple[tuple[float, ...], ...]
    combination_count: int
    search_space_bounds: Mapping[str, Mapping[str, float]]
    seed: int
    train_period: str
    validation_period: str
    out_of_sample_period: str
    config_digest: str
    implementation_digest: str
    data_digest_or_explicit_missing: str
    grid_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "grid_id": self.grid_id,
            "grid_version": self.grid_version,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "canonical_trading_logic_version": self.canonical_trading_logic_version,
            "parameter_names": list(self.parameter_names),
            "parameter_values": [list(values) for values in self.parameter_values],
            "combination_count": self.combination_count,
            "search_space_bounds": {
                key: dict(bounds) for key, bounds in self.search_space_bounds.items()
            },
            "seed": self.seed,
            "train_period": self.train_period,
            "validation_period": self.validation_period,
            "out_of_sample_period": self.out_of_sample_period,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "data_digest_or_explicit_missing": self.data_digest_or_explicit_missing,
            "grid_digest": self.grid_digest,
        }


@dataclass(frozen=True)
class ParameterSensitivityPointV1:
    parameter_set_id: str
    parameter_values: Mapping[str, float]
    evaluation_status: EvaluationStatus
    reason_codes: tuple[str, ...]
    train_result_ref: str
    validation_result_ref: str
    out_of_sample_result_ref: str
    net_return: MetricValueStatus
    net_return_value: Optional[float]
    net_expectancy: MetricValueStatus
    net_expectancy_value: Optional[float]
    profit_factor: MetricValueStatus
    profit_factor_value: Optional[float]
    max_drawdown: MetricValueStatus
    max_drawdown_value: Optional[float]
    trade_count: MetricValueStatus
    trade_count_value: Optional[float]
    walk_forward_status: str
    monte_carlo_status: str
    stress_status: str
    cost_model_ref: str
    funding_model_ref: str
    config_digest: str
    implementation_digest: str
    data_digest: str
    result_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter_set_id": self.parameter_set_id,
            "parameter_values": dict(self.parameter_values),
            "evaluation_status": self.evaluation_status.value,
            "reason_codes": list(self.reason_codes),
            "train_result_ref": self.train_result_ref,
            "validation_result_ref": self.validation_result_ref,
            "out_of_sample_result_ref": self.out_of_sample_result_ref,
            "net_return": _metric_payload(self.net_return, self.net_return_value),
            "net_expectancy": _metric_payload(self.net_expectancy, self.net_expectancy_value),
            "profit_factor": _metric_payload(self.profit_factor, self.profit_factor_value),
            "max_drawdown": _metric_payload(self.max_drawdown, self.max_drawdown_value),
            "trade_count": _metric_payload(self.trade_count, self.trade_count_value),
            "walk_forward_status": self.walk_forward_status,
            "monte_carlo_status": self.monte_carlo_status,
            "stress_status": self.stress_status,
            "cost_model_ref": self.cost_model_ref,
            "funding_model_ref": self.funding_model_ref,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "data_digest": self.data_digest,
            "result_digest": self.result_digest,
        }


@dataclass(frozen=True)
class ParameterSensitivityResultV1:
    contract_version: str
    owner: str
    pipeline_status: PipelineStatus
    parameter_robustness_policy_pass: bool
    parameter_robustness_policy_status: str
    grid: ParameterSensitivityGridV1
    grid_digest: str
    result_digest: str
    combination_count: int
    points: tuple[ParameterSensitivityPointV1, ...]
    failed_point_count: int
    blocked_point_count: int
    seed: int
    reason_codes: tuple[str, ...]
    oos_tuning_forbidden: bool = True
    full_grid_persisted: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "owner": self.owner,
            "pipeline_status": self.pipeline_status.value,
            "parameter_robustness_policy_pass": self.parameter_robustness_policy_pass,
            "parameter_robustness_policy_status": self.parameter_robustness_policy_status,
            "grid": self.grid.to_dict(),
            "grid_digest": self.grid_digest,
            "result_digest": self.result_digest,
            "combination_count": self.combination_count,
            "points": [point.to_dict() for point in self.points],
            "failed_point_count": self.failed_point_count,
            "blocked_point_count": self.blocked_point_count,
            "seed": self.seed,
            "reason_codes": list(self.reason_codes),
            "oos_tuning_forbidden": self.oos_tuning_forbidden,
            "full_grid_persisted": self.full_grid_persisted,
        }

    def evidence_digest(self) -> str:
        payload = self.to_dict()
        payload.pop("points", None)
        return _stable_digest(payload)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _metric_payload(status: MetricValueStatus, value: Optional[float]) -> dict[str, Any]:
    payload: dict[str, Any] = {"semantic": status.value}
    if value is not None:
        payload["value"] = value
    return payload


def _reject_forbidden_instrument(instrument_id: str) -> None:
    lowered = instrument_id.lower()
    for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS:
        if token in lowered:
            raise ParameterSensitivityError(f"instrument_kind_forbidden:{instrument_id}")


def parameter_sensitivity_binding_requested(cfg: Mapping[str, Any]) -> bool:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        return False
    section = backtest.get("parameter_sensitivity")
    if not isinstance(section, Mapping):
        return False
    if section.get("bind") is True:
        return True
    return str(section.get("grid_version", "")) == DEFAULT_GRID_VERSION


def _deep_copy_cfg(cfg: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(cfg))


def _apply_cfg_param(cfg: dict[str, Any], param_name: str, value: float) -> None:
    if param_name not in _CFG_PARAM_PATHS:
        raise ParameterSensitivityError(f"parameter_not_cfg_bound:{param_name}")
    path = _CFG_PARAM_PATHS[param_name]
    node: dict[str, Any] = cfg
    for key in path[:-1]:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    node[path[-1]] = float(value)


def _canonicalize_values(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        raise ParameterSensitivityError("empty_parameter_values")
    canonical: list[float] = []
    seen: set[float] = set()
    for raw in values:
        numeric = float(raw)
        if not math.isfinite(numeric):
            raise ParameterSensitivityError(f"parameter_value_non_finite:{raw!r}")
        if numeric in seen:
            raise ParameterSensitivityError(f"duplicate_parameter_value:{numeric}")
        seen.add(numeric)
        canonical.append(numeric)
    return tuple(sorted(canonical))


def _validate_bounds(
    parameter_names: Sequence[str],
    parameter_values: Sequence[Sequence[float]],
    search_space_bounds: Mapping[str, Mapping[str, float]],
) -> None:
    if not parameter_names:
        raise ParameterSensitivityError("empty_parameter_list")
    if len(parameter_names) != len(parameter_values):
        raise ParameterSensitivityError("parameter_names_values_length_mismatch")
    for name in parameter_names:
        if name not in _CFG_PARAM_PATHS:
            raise ParameterSensitivityError(f"parameter_not_allowed:{name}")
        bounds = search_space_bounds.get(name)
        if bounds is None:
            raise ParameterSensitivityError(f"search_space_bounds_missing:{name}")
        lower = float(bounds.get("min", float("-inf")))
        upper = float(bounds.get("max", float("inf")))
        if not math.isfinite(lower) or not math.isfinite(upper):
            raise ParameterSensitivityError(f"search_space_bounds_non_finite:{name}")
        if lower >= upper:
            raise ParameterSensitivityError(f"search_space_bounds_invalid:{name}")
        for value in parameter_values[list(parameter_names).index(name)]:
            if value < lower or value > upper:
                raise ParameterSensitivityError(f"parameter_value_out_of_bounds:{name}:{value}")


def _iter_grid_combinations(
    parameter_names: Sequence[str],
    parameter_values: Sequence[Sequence[float]],
) -> list[dict[str, float]]:
    canonical_values = [_canonicalize_values(values) for values in parameter_values]
    expected_count = math.prod(len(values) for values in canonical_values)
    combos: list[dict[str, float]] = []
    for combo in itertools.product(*canonical_values):
        combos.append(
            {name: float(value) for name, value in zip(parameter_names, combo, strict=True)}
        )
    if len(combos) != expected_count:
        raise ParameterSensitivityError("combination_count_mismatch")
    return combos


def _period_label(bars: pd.DataFrame) -> str:
    if bars.empty:
        return "empty"
    return f"{bars.index[0]}..{bars.index[-1]}"


def split_bars_train_validation_oos_v1(
    bars: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if bars.empty:
        raise ParameterSensitivityError("bars_empty")
    total = len(bars)
    train_end = max(MIN_BARS_PER_SPLIT, int(total * TRAIN_FRACTION))
    val_end = train_end + max(MIN_BARS_PER_SPLIT, int(total * VALIDATION_FRACTION))
    if val_end + MIN_BARS_PER_SPLIT > total:
        raise ParameterSensitivityError("insufficient_bars_for_train_validation_oos")
    train = bars.iloc[:train_end]
    validation = bars.iloc[train_end:val_end]
    oos = bars.iloc[val_end:]
    return train, validation, oos


def build_parameter_grid_v1(
    *,
    strategy_id: str,
    strategy_version: str,
    cfg: Mapping[str, Any],
    bars: pd.DataFrame,
    data_digest: str,
    instrument_id: str,
    grid_spec: Mapping[str, Any] | None = None,
) -> ParameterSensitivityGridV1:
    _reject_forbidden_instrument(instrument_id)
    spec = dict(grid_spec or {})
    grid_id = str(spec.get("grid_id", DEFAULT_GRID_ID))
    grid_version = str(spec.get("grid_version", DEFAULT_GRID_VERSION))
    parameter_names = tuple(
        str(name) for name in spec.get("parameter_names", ("fee_bps", "slippage_bps"))
    )
    raw_values = spec.get(
        "parameter_values",
        ([8.0, 10.0, 12.0], [3.0, 5.0, 7.0]),
    )
    parameter_values = tuple(_canonicalize_values(values) for values in raw_values)
    search_space_bounds = dict(
        spec.get(
            "search_space_bounds",
            {
                "fee_bps": {"min": 8.0, "max": 12.0},
                "slippage_bps": {"min": 3.0, "max": 7.0},
            },
        )
    )
    seed = int(spec.get("seed", 42))
    _validate_bounds(parameter_names, parameter_values, search_space_bounds)
    combinations = _iter_grid_combinations(parameter_names, parameter_values)
    train, validation, oos = split_bars_train_validation_oos_v1(bars)
    config_digest = _stable_digest({"cfg": dict(cfg), "owner": PARAMETER_SENSITIVITY_OWNER})
    implementation_digest = _stable_digest(
        {
            "owner": PARAMETER_SENSITIVITY_OWNER,
            "version": PARAMETER_SENSITIVITY_VERSION,
            "canonical_trading_logic_version": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        }
    )
    grid_payload = {
        "grid_id": grid_id,
        "grid_version": grid_version,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "parameter_names": list(parameter_names),
        "parameter_values": [list(values) for values in parameter_values],
        "search_space_bounds": search_space_bounds,
        "seed": seed,
    }
    grid_digest = _stable_digest(grid_payload)
    return ParameterSensitivityGridV1(
        grid_id=grid_id,
        grid_version=grid_version,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        canonical_trading_logic_version=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        parameter_names=parameter_names,
        parameter_values=parameter_values,
        combination_count=len(combinations),
        search_space_bounds=search_space_bounds,
        seed=seed,
        train_period=_period_label(train),
        validation_period=_period_label(validation),
        out_of_sample_period=_period_label(oos),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        data_digest_or_explicit_missing=data_digest or "MISSING",
        grid_digest=grid_digest,
    )


def load_parameter_grid_v1(
    cfg: Mapping[str, Any],
    *,
    strategy_id: str,
    strategy_version: str,
    bars: pd.DataFrame,
    data_digest: str,
    instrument_id: str,
) -> ParameterSensitivityGridV1:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise ParameterSensitivityError("missing_parameter_grid")
    section = backtest.get("parameter_sensitivity")
    if not isinstance(section, Mapping):
        raise ParameterSensitivityError("missing_parameter_grid")
    grid_spec = section.get("grid")
    if grid_spec is not None and not isinstance(grid_spec, Mapping):
        raise ParameterSensitivityError("parameter_grid_not_mapping")
    return build_parameter_grid_v1(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        cfg=cfg,
        bars=bars,
        data_digest=data_digest,
        instrument_id=instrument_id,
        grid_spec=grid_spec if isinstance(grid_spec, Mapping) else None,
    )


def _metric_from_stats(
    key: str, stats: Mapping[str, float]
) -> tuple[MetricValueStatus, Optional[float]]:
    if key not in stats:
        return MetricValueStatus.UNKNOWN, None
    value = float(stats[key])
    if not math.isfinite(value):
        return MetricValueStatus.NOT_COMPUTED, None
    return MetricValueStatus.COMPUTED, value


def _evaluate_split(
    *,
    bars: pd.DataFrame,
    strategy_id: str,
    cfg: Mapping[str, Any],
    instrument_id: str,
    split_name: str,
    parameter_set_id: str,
    explicit_zero_cost_non_economic: bool,
) -> tuple[str, Mapping[str, float], str, str]:
    ref = f"{parameter_set_id}:{split_name}"
    if bars.empty or len(bars) < MIN_BARS_PER_SPLIT:
        return ref, {}, "NOT_BOUND", FUNDING_MODEL_VERSION
    wiring = mv2_wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=strategy_id,
        cfg=cfg,
        instrument_id=instrument_id,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
    )
    stats = mv2_wiring.compute_mv2_backtest_metrics_v1(wiring.backtest_result)
    cost_ref = wiring.effective_cost_config.cost_model_version
    funding_ref = wiring.effective_cost_config.funding_model_version
    return ref, stats, cost_ref, funding_ref


def _evaluate_parameter_point_v1(
    *,
    grid: ParameterSensitivityGridV1,
    parameter_values: Mapping[str, float],
    bars: pd.DataFrame,
    base_cfg: Mapping[str, Any],
    strategy_id: str,
    instrument_id: str,
    data_digest: str,
    explicit_zero_cost_non_economic: bool,
) -> ParameterSensitivityPointV1:
    parameter_set_id = _stable_digest(
        {"grid_digest": grid.grid_digest, "parameter_values": dict(parameter_values)}
    )
    cfg = _deep_copy_cfg(base_cfg)
    reason_codes: list[str] = []
    try:
        for name, value in sorted(parameter_values.items()):
            _apply_cfg_param(cfg, name, value)
        train, validation, oos = split_bars_train_validation_oos_v1(bars)
        train_ref, train_stats, cost_ref, funding_ref = _evaluate_split(
            bars=train,
            strategy_id=strategy_id,
            cfg=cfg,
            instrument_id=instrument_id,
            split_name="train",
            parameter_set_id=parameter_set_id,
            explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        )
        val_ref, val_stats, _, _ = _evaluate_split(
            bars=validation,
            strategy_id=strategy_id,
            cfg=cfg,
            instrument_id=instrument_id,
            split_name="validation",
            parameter_set_id=parameter_set_id,
            explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        )
        oos_ref, oos_stats, _, _ = _evaluate_split(
            bars=oos,
            strategy_id=strategy_id,
            cfg=cfg,
            instrument_id=instrument_id,
            split_name="out_of_sample",
            parameter_set_id=parameter_set_id,
            explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        )
        evaluation_status = EvaluationStatus.EVALUATED
        metric_stats = oos_stats
    except Exception as exc:  # noqa: BLE001 - persist failed points
        evaluation_status = EvaluationStatus.FAILED
        reason_codes.append(f"evaluation_failed:{exc}")
        train_ref = f"{parameter_set_id}:train"
        val_ref = f"{parameter_set_id}:validation"
        oos_ref = f"{parameter_set_id}:out_of_sample"
        metric_stats = {}
        cost_ref = "NOT_BOUND"
        funding_ref = FUNDING_MODEL_VERSION

    net_return_status, net_return_value = _metric_from_stats("total_return", metric_stats)
    net_expectancy_status, net_expectancy_value = _metric_from_stats("expectancy", metric_stats)
    profit_factor_status, profit_factor_value = _metric_from_stats("profit_factor", metric_stats)
    max_drawdown_status, max_drawdown_value = _metric_from_stats("max_drawdown", metric_stats)
    trade_count_status, trade_count_value = _metric_from_stats("total_trades", metric_stats)

    point_payload = {
        "parameter_set_id": parameter_set_id,
        "parameter_values": dict(parameter_values),
        "evaluation_status": evaluation_status.value,
        "train_result_ref": train_ref,
        "validation_result_ref": val_ref,
        "out_of_sample_result_ref": oos_ref,
    }
    result_digest = _stable_digest(point_payload)
    return ParameterSensitivityPointV1(
        parameter_set_id=parameter_set_id,
        parameter_values=dict(parameter_values),
        evaluation_status=evaluation_status,
        reason_codes=tuple(reason_codes),
        train_result_ref=train_ref,
        validation_result_ref=val_ref,
        out_of_sample_result_ref=oos_ref,
        net_return=net_return_status,
        net_return_value=net_return_value,
        net_expectancy=net_expectancy_status,
        net_expectancy_value=net_expectancy_value,
        profit_factor=profit_factor_status,
        profit_factor_value=profit_factor_value,
        max_drawdown=max_drawdown_status,
        max_drawdown_value=max_drawdown_value,
        trade_count=trade_count_status,
        trade_count_value=trade_count_value,
        walk_forward_status="NOT_COMPUTED",
        monte_carlo_status="NOT_COMPUTED",
        stress_status="NOT_COMPUTED",
        cost_model_ref=cost_ref,
        funding_model_ref=funding_ref,
        config_digest=grid.config_digest,
        implementation_digest=grid.implementation_digest,
        data_digest=data_digest,
        result_digest=result_digest,
    )


def resolve_parameter_robustness_policy_status_v1(policy: EconomicValidityPolicyV1) -> str:
    if policy.thresholds_configured():
        return POLICY_THRESHOLD_STATUS_PASS
    return POLICY_THRESHOLD_STATUS_BLOCKED


def run_parameter_sensitivity_v1(
    *,
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
    strategy_id: str,
    strategy_version: str,
    data_digest: str,
    instrument_id: str = mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
    explicit_zero_cost_non_economic: bool = False,
    policy: EconomicValidityPolicyV1 | None = None,
) -> ParameterSensitivityResultV1:
    _reject_forbidden_instrument(instrument_id)
    if bars.empty:
        raise ParameterSensitivityError("bars_empty")
    if not data_digest:
        raise ParameterSensitivityError("missing_data_digest")

    loaded_policy = policy or resolve_economic_validity_policy_v1(cfg)
    policy_status = resolve_parameter_robustness_policy_status_v1(loaded_policy)
    parameter_robustness_policy_pass = loaded_policy.thresholds_configured()

    try:
        grid = load_parameter_grid_v1(
            cfg,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            bars=bars,
            data_digest=data_digest,
            instrument_id=instrument_id,
        )
    except ParameterSensitivityError as exc:
        raise ParameterSensitivityError(f"missing_or_invalid_grid:{exc}") from exc

    combinations = _iter_grid_combinations(grid.parameter_names, grid.parameter_values)
    if grid.combination_count != len(combinations):
        raise ParameterSensitivityError("grid_combination_count_mismatch")

    points: list[ParameterSensitivityPointV1] = []
    failed_count = 0
    blocked_count = 0
    for combo in combinations:
        point = _evaluate_parameter_point_v1(
            grid=grid,
            parameter_values=combo,
            bars=bars,
            base_cfg=cfg,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            data_digest=data_digest,
            explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        )
        points.append(point)
        if point.evaluation_status is EvaluationStatus.FAILED:
            failed_count += 1
        if point.evaluation_status is EvaluationStatus.BLOCKED:
            blocked_count += 1

    reason_codes = ["parameter_sensitivity_pipeline_executed"]
    if not parameter_robustness_policy_pass:
        reason_codes.append("parameter_robustness_policy_blocked_missing_thresholds")
    if failed_count:
        reason_codes.append("parameter_points_failed")
    pipeline_status = PipelineStatus.PIPELINE_PASS
    if failed_count == len(points) and points:
        pipeline_status = PipelineStatus.PIPELINE_FAILED

    result_payload = {
        "grid_digest": grid.grid_digest,
        "combination_count": len(points),
        "seed": grid.seed,
        "pipeline_status": pipeline_status.value,
    }
    result_digest = _stable_digest(
        {**result_payload, "points": [point.to_dict() for point in points]}
    )
    return ParameterSensitivityResultV1(
        contract_version=PARAMETER_SENSITIVITY_VERSION,
        owner=PARAMETER_SENSITIVITY_OWNER,
        pipeline_status=pipeline_status,
        parameter_robustness_policy_pass=parameter_robustness_policy_pass,
        parameter_robustness_policy_status=policy_status,
        grid=grid,
        grid_digest=grid.grid_digest,
        result_digest=result_digest,
        combination_count=len(points),
        points=tuple(points),
        failed_point_count=failed_count,
        blocked_point_count=blocked_count,
        seed=grid.seed,
        reason_codes=tuple(sorted(set(reason_codes))),
    )


def serialize_parameter_sensitivity_results_v1(
    result: ParameterSensitivityResultV1,
) -> dict[str, Any]:
    return result.to_dict()


def parameter_sensitivity_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "parameter_sensitivity_v1",
        "contract_version": PARAMETER_SENSITIVITY_VERSION,
        "owner": PARAMETER_SENSITIVITY_OWNER,
        "allowed_pipeline_statuses": [status.value for status in PipelineStatus],
        "allowed_evaluation_statuses": [status.value for status in EvaluationStatus],
        "oos_tuning_forbidden": True,
        "full_grid_persistence_required": True,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
    }
