"""
Economic Viability Evidence v1 (RUNBOOK STEP 29M).

Fail-closed offline evidence contract bound to the canonical MV2 research chain
from STEP 29L. Non-authorizing: does not claim profitability or economic validity
unless all versioned policy gates pass.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.cost_config_v0 import FUNDING_MODEL_VERSION
from src.backtest.funding_model_v1 import (
    FundingModelError,
    compute_funding_drag_v1,
    load_funding_model_config_v1,
)
from src.backtest.admissible_versioned_futures_dataset_v1 import (
    AdmissibleVersionedFuturesDatasetError,
    dataset_admissibility_binding_requested,
    load_dataset_admissibility_from_cfg,
    serialize_dataset_admissibility_binding_v1,
    evaluate_admissible_versioned_futures_dataset_v1,
)
from src.backtest.parameter_sensitivity_v1 import (
    ParameterSensitivityError,
    parameter_sensitivity_binding_requested,
    run_parameter_sensitivity_v1,
    serialize_parameter_sensitivity_results_v1,
)
from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_VERSION,
    evaluate_economic_validity_gates_v1,
    load_economic_validity_policy_v1,
    validate_economic_validity_policy_v1,
)
from src.experiments.monte_carlo import MonteCarloConfig, MonteCarloSummaryResult
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
)

ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION = "v1"
ECONOMIC_VIABILITY_EVIDENCE_OWNER = "backtest.economic_viability_evidence_v1"
ARTIFACT_FILENAME = "economic_viability_evidence_v1.json"
SCHEMA_FILENAME = "economic_viability_evidence_schema_v1.json"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

_STEP29M_ALLOWED_STATUSES = frozenset(
    {
        "RESEARCH_ONLY",
        "PROMISING",
        "ROBUSTNESS_FAILED",
        "ECONOMICALLY_VIABLE_OFFLINE",
    }
)

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class EconomicViabilityStatus(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PROMISING = "PROMISING"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"


class DataSourceKind(str, Enum):
    VERSIONED_CANONICAL_FUTURES = "versioned_canonical_futures"
    SYNTHETIC_CONTRACT_FIXTURE = "synthetic_contract_fixture"
    INADMISSIBLE = "inadmissible"


class MetricSemantic(str, Enum):
    COMPUTED = "COMPUTED"
    UNKNOWN = "UNKNOWN"
    NOT_COMPUTED = "NOT_COMPUTED"


@dataclass(frozen=True)
class DataAdmissibilityV1:
    source_kind: DataSourceKind
    instrument_id: str
    data_digest: str
    data_ref: str
    versioned_dataset_id: Optional[str] = None

    def is_admissible_for_economic_claim(self) -> bool:
        return self.source_kind is DataSourceKind.VERSIONED_CANONICAL_FUTURES


@dataclass(frozen=True)
class MetricFieldV1:
    semantic: MetricSemantic
    value: Optional[float] = None
    reason_code: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"semantic": self.semantic.value}
        if self.value is not None:
            payload["value"] = self.value
        if self.reason_code is not None:
            payload["reason_code"] = self.reason_code
        return payload


@dataclass(frozen=True)
class EconomicViabilityEvidenceV1:
    contract_version: str
    owner: str
    strategy_id: str
    strategy_version: str
    instrument_id_or_universe: str
    canonical_trading_logic_version: str
    data_period: str
    training_period: str
    validation_period: str
    out_of_sample_period: str
    fee_model_version: str
    slippage_model_version: str
    funding_model_version: str
    execution_model_version: str
    config_digest: str
    implementation_digest: str
    data_digest: str
    gross_return: MetricFieldV1
    net_return: MetricFieldV1
    net_expectancy: MetricFieldV1
    profit_factor: MetricFieldV1
    sharpe: MetricFieldV1
    sortino: MetricFieldV1
    max_drawdown: MetricFieldV1
    calmar: MetricFieldV1
    trade_count: MetricFieldV1
    turnover: MetricFieldV1
    fee_drag: MetricFieldV1
    funding_drag: MetricFieldV1
    slippage_impact: MetricFieldV1
    tail_loss: MetricFieldV1
    time_in_market: MetricFieldV1
    long_contribution: MetricFieldV1
    short_contribution: MetricFieldV1
    regime_breakdown: Mapping[str, Any]
    portfolio_contribution: Mapping[str, Any]
    walk_forward_results: Mapping[str, Any]
    monte_carlo_results: Mapping[str, Any]
    stress_results: Mapping[str, Any]
    parameter_sensitivity_results: Mapping[str, Any]
    status: EconomicViabilityStatus
    reason_codes: tuple[str, ...]
    manifest_digest: str
    wiring_chain_digest: str
    randomness_seed: int
    data_admissibility: Mapping[str, Any]
    cost_binding: Mapping[str, Any]
    policy_version: str = ECONOMIC_VALIDITY_POLICY_VERSION
    policy_digest: str = ""
    policy_threshold_status: str = ""
    economic_validity_proven: bool = False
    profitability_claim_allowed: bool = False
    authority_effect: str = "NONE"
    runtime_effect: bool = False
    order_effect: bool = False
    futures_only: bool = True
    bitcoin_direction_allowed: bool = False

    def to_semantic_dict(self) -> dict[str, Any]:
        payload = {
            "contract_version": self.contract_version,
            "owner": self.owner,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "instrument_id_or_universe": self.instrument_id_or_universe,
            "canonical_trading_logic_version": self.canonical_trading_logic_version,
            "data_period": self.data_period,
            "training_period": self.training_period,
            "validation_period": self.validation_period,
            "out_of_sample_period": self.out_of_sample_period,
            "fee_model_version": self.fee_model_version,
            "slippage_model_version": self.slippage_model_version,
            "funding_model_version": self.funding_model_version,
            "execution_model_version": self.execution_model_version,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "data_digest": self.data_digest,
            "gross_return": self.gross_return.to_dict(),
            "net_return": self.net_return.to_dict(),
            "net_expectancy": self.net_expectancy.to_dict(),
            "profit_factor": self.profit_factor.to_dict(),
            "sharpe": self.sharpe.to_dict(),
            "sortino": self.sortino.to_dict(),
            "max_drawdown": self.max_drawdown.to_dict(),
            "calmar": self.calmar.to_dict(),
            "trade_count": self.trade_count.to_dict(),
            "turnover": self.turnover.to_dict(),
            "fee_drag": self.fee_drag.to_dict(),
            "funding_drag": self.funding_drag.to_dict(),
            "slippage_impact": self.slippage_impact.to_dict(),
            "tail_loss": self.tail_loss.to_dict(),
            "time_in_market": self.time_in_market.to_dict(),
            "long_contribution": self.long_contribution.to_dict(),
            "short_contribution": self.short_contribution.to_dict(),
            "regime_breakdown": dict(self.regime_breakdown),
            "portfolio_contribution": dict(self.portfolio_contribution),
            "walk_forward_results": dict(self.walk_forward_results),
            "monte_carlo_results": dict(self.monte_carlo_results),
            "stress_results": dict(self.stress_results),
            "parameter_sensitivity_results": dict(self.parameter_sensitivity_results),
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "manifest_digest": self.manifest_digest,
            "wiring_chain_digest": self.wiring_chain_digest,
            "randomness_seed": self.randomness_seed,
            "data_admissibility": dict(self.data_admissibility),
            "cost_binding": dict(self.cost_binding),
            "policy_version": self.policy_version,
            "policy_digest": self.policy_digest,
            "policy_threshold_status": self.policy_threshold_status,
            "economic_validity_proven": self.economic_validity_proven,
            "profitability_claim_allowed": self.profitability_claim_allowed,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "order_effect": self.order_effect,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
        }
        return payload

    def to_dict(self) -> dict[str, Any]:
        payload = self.to_semantic_dict()
        payload["created_at"] = OFFLINE_DETERMINISTIC_CREATED_AT
        return payload


class EconomicViabilityEvidenceError(ValueError):
    """Fail-closed economic viability evidence error."""


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fail_closed(condition: bool, reason: str) -> None:
    if condition:
        raise EconomicViabilityEvidenceError(reason)


def _reject_forbidden_instrument(instrument_id: str) -> None:
    lowered = instrument_id.lower()
    for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS:
        if token in lowered:
            raise EconomicViabilityEvidenceError(f"instrument_kind_forbidden:{instrument_id}")


def compute_bars_data_digest(bars: pd.DataFrame) -> str:
    if bars.empty:
        return _stable_digest({"empty": True})
    frame = bars.sort_index()
    payload = {
        "columns": list(frame.columns),
        "index_start": str(frame.index[0]),
        "index_end": str(frame.index[-1]),
        "row_count": len(frame),
        "close_digest": _stable_digest(frame["close"].astype(float).tolist()),
    }
    return _stable_digest(payload)


def _period_label(bars: pd.DataFrame) -> str:
    if bars.empty:
        return "empty"
    return f"{bars.index[0]}..{bars.index[-1]}"


def _metric_from_stats(key: str, stats: Mapping[str, float]) -> MetricFieldV1:
    if key not in stats:
        return MetricFieldV1(semantic=MetricSemantic.UNKNOWN, reason_code=f"metric_missing:{key}")
    value = float(stats[key])
    if not math.isfinite(value):
        return MetricFieldV1(
            semantic=MetricSemantic.NOT_COMPUTED,
            reason_code=f"metric_non_finite:{key}",
        )
    return MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=value)


def _not_computed_metric(reason_code: str) -> MetricFieldV1:
    return MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED, reason_code=reason_code)


def _serialize_monte_carlo(summary: MonteCarloSummaryResult) -> dict[str, Any]:
    return {
        "num_runs": summary.num_runs,
        "seed": summary.config.seed,
        "method": summary.config.method,
        "metric_quantiles": {
            metric: dict(quantiles) for metric, quantiles in summary.metric_quantiles.items()
        },
    }


def _serialize_walk_forward(
    wf: mv2_wiring.MV2WalkForwardWiringResultV1,
) -> dict[str, Any]:
    windows = []
    for window in wf.windows:
        metrics = mv2_wiring.compute_mv2_backtest_metrics_v1(
            window.oos_wiring_result.backtest_result
        )
        windows.append(
            {
                "window_index": window.window_index,
                "train_period_digest": window.train_period_digest,
                "test_period_digest": window.test_period_digest,
                "config_digest": window.config_digest,
                "oos_total_return": metrics.get("total_return"),
                "oos_trade_count": metrics.get("total_trades"),
            }
        )
    return {
        "split_contract_digest": wf.split_contract_digest,
        "window_count": len(windows),
        "windows": windows,
    }


def _serialize_stress(outcome: mv2_wiring.StressClassBindingOutcomeV1) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "class_statuses": {k: v.value for k, v in outcome.statuses.items()},
    }
    if outcome.suite_result is None:
        payload["suite"] = None
        return payload
    payload["suite"] = {
        "scenario_count": len(outcome.suite_result.scenario_results),
        "scenarios": [
            {
                "scenario_type": result.scenario.scenario_type,
                "stressed_total_return": result.stressed_metrics.get("total_return"),
                "stressed_max_drawdown": result.stressed_metrics.get("max_drawdown"),
            }
            for result in outcome.suite_result.scenario_results
        ],
    }
    return payload


def _evaluate_robustness_failures(
    *,
    wf: Optional[mv2_wiring.MV2WalkForwardWiringResultV1],
    mc: Optional[MonteCarloSummaryResult],
    stress: Optional[mv2_wiring.StressClassBindingOutcomeV1],
) -> list[str]:
    failures: list[str] = []
    if wf is not None:
        negative_windows = 0
        for window in wf.windows:
            metrics = mv2_wiring.compute_mv2_backtest_metrics_v1(
                window.oos_wiring_result.backtest_result
            )
            if metrics.get("total_return", 0.0) < 0.0:
                negative_windows += 1
        if negative_windows == len(wf.windows) and len(wf.windows) > 0:
            failures.append("walk_forward_all_oos_negative")
    if mc is not None:
        total_return_q = mc.metric_quantiles.get("total_return", {})
        p50 = total_return_q.get("p50")
        if p50 is not None and p50 < 0.0:
            failures.append("monte_carlo_median_return_negative")
    if stress is not None and stress.suite_result is not None:
        for result in stress.suite_result.scenario_results:
            stressed_return = result.stressed_metrics.get("total_return")
            if stressed_return is not None and stressed_return < -0.5:
                failures.append(f"stress_severe_loss:{result.scenario.scenario_type}")
    return failures


def _resolve_status(
    *,
    reason_codes: Sequence[str],
    robustness_failures: Sequence[str],
    data_admissible: bool,
    policy_version_bound: bool,
    funding_bound: bool,
    parameter_sensitivity_bound: bool,
    gates_pass: bool,
) -> EconomicViabilityStatus:
    if robustness_failures:
        return EconomicViabilityStatus.ROBUSTNESS_FAILED
    if (
        gates_pass
        and data_admissible
        and policy_version_bound
        and funding_bound
        and parameter_sensitivity_bound
    ):
        return EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE
    if not data_admissible or not policy_version_bound or not funding_bound:
        return EconomicViabilityStatus.RESEARCH_ONLY
    return EconomicViabilityStatus.PROMISING


def build_economic_viability_evidence_v1(
    *,
    bars: pd.DataFrame,
    data_admissibility: DataAdmissibilityV1,
    strategy_id: str,
    cfg: Mapping[str, Any],
    instrument_id: str = mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
    walk_forward_train_bars: int = 8,
    walk_forward_test_bars: int = 4,
    walk_forward_step_bars: int = 4,
    monte_carlo_runs: int = 16,
    monte_carlo_seed: int = 42,
    explicit_zero_cost_non_economic: bool = False,
) -> EconomicViabilityEvidenceV1:
    _reject_forbidden_instrument(instrument_id)
    _fail_closed(bars.empty, "bars_empty")
    if data_admissibility.instrument_id != instrument_id:
        raise EconomicViabilityEvidenceError("data_admissibility_instrument_mismatch")
    computed_data_digest = compute_bars_data_digest(bars)
    if data_admissibility.data_digest != computed_data_digest:
        raise EconomicViabilityEvidenceError("data_digest_mismatch")

    wiring_result = mv2_wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=strategy_id,
        cfg=cfg,
        instrument_id=instrument_id,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
    )
    stats = mv2_wiring.compute_mv2_backtest_metrics_v1(wiring_result.backtest_result)
    cost = wiring_result.effective_cost_config

    strategy_version = "unknown"
    for entry in wiring_result.registry_snapshot.entries:
        if entry.strategy_id == strategy_id:
            strategy_version = entry.strategy_version
            break

    wf_result: Optional[mv2_wiring.MV2WalkForwardWiringResultV1] = None
    mc_result: Optional[MonteCarloSummaryResult] = None
    stress_result: Optional[mv2_wiring.StressClassBindingOutcomeV1] = None
    reason_codes: list[str] = []

    if len(bars) >= walk_forward_train_bars + walk_forward_test_bars:
        wf_result = mv2_wiring.run_mv2_walk_forward_wiring_v1(
            bars,
            strategy_id=strategy_id,
            cfg=cfg,
            train_bars=walk_forward_train_bars,
            test_bars=walk_forward_test_bars,
            step_bars=walk_forward_step_bars,
            instrument_id=instrument_id,
            explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        )
    else:
        reason_codes.append("walk_forward_insufficient_bars")

    if monte_carlo_runs > 0:
        mc_result = mv2_wiring.bind_monte_carlo_analysis_v1(
            wiring_result.backtest_result,
            MonteCarloConfig(num_runs=monte_carlo_runs, seed=monte_carlo_seed),
        )
    else:
        reason_codes.append("monte_carlo_not_run")

    returns = wiring_result.backtest_result.equity_curve.pct_change().dropna()
    if not returns.empty:
        stress_result = mv2_wiring.bind_stress_class_suite_v1(returns)
    else:
        reason_codes.append("stress_returns_empty")

    dataset_binding_requested = dataset_admissibility_binding_requested(cfg)
    dataset_admissible = data_admissibility.is_admissible_for_economic_claim()
    dataset_admissibility_payload: dict[str, Any] = {
        "source_kind": data_admissibility.source_kind.value,
        "instrument_id": data_admissibility.instrument_id,
        "data_digest": data_admissibility.data_digest,
        "data_ref": data_admissibility.data_ref,
        "versioned_dataset_id": data_admissibility.versioned_dataset_id,
    }
    if dataset_binding_requested:
        try:
            descriptor, provenance = load_dataset_admissibility_from_cfg(cfg)
            binding_result = evaluate_admissible_versioned_futures_dataset_v1(
                bars=bars,
                descriptor=descriptor,
                provenance=provenance,
                instrument_id=instrument_id,
            )
            dataset_admissibility_payload = serialize_dataset_admissibility_binding_v1(
                binding_result
            )
            dataset_admissible = binding_result.is_admissible()
            if dataset_admissible:
                reason_codes.append("admissible_versioned_futures_dataset_bound")
            else:
                reason_codes.append(
                    f"dataset_admissibility_{binding_result.admissibility_status.value.lower()}"
                )
        except AdmissibleVersionedFuturesDatasetError as exc:
            dataset_admissible = False
            reason_codes.append(f"dataset_admissibility_failed:{exc}")
            dataset_admissibility_payload = {
                **dataset_admissibility_payload,
                "binding_status": "FAILED",
                "reason_code": str(exc),
            }
    else:
        if not dataset_admissible:
            reason_codes.append("admissible_versioned_futures_dataset_missing")
    if data_admissibility.source_kind is DataSourceKind.INADMISSIBLE:
        reason_codes.append("data_source_inadmissible")
        dataset_admissible = False
    policy = load_economic_validity_policy_v1(cfg)
    validate_economic_validity_policy_v1(policy)
    if not policy.is_version_bound():
        reason_codes.append("economic_viability_policy_not_versioned")
    if not policy.thresholds_configured():
        reason_codes.append("economic_validity_policy_thresholds_not_configured")
        for field_name in policy.unconfigured_fields():
            reason_codes.append(f"policy_threshold_required_not_configured:{field_name}")
    if cost.funding_model_version == "NOT_BOUND":
        reason_codes.append("funding_model_not_bound")
    if cost.zero_cost_explicitly_requested:
        reason_codes.append("explicit_zero_cost_non_economic_mode")
    sensitivity_requested = parameter_sensitivity_binding_requested(cfg)
    if not sensitivity_requested:
        reason_codes.append("parameter_sensitivity_not_bound_in_step29m_scope")

    robustness_failures = _evaluate_robustness_failures(
        wf=wf_result, mc=mc_result, stress=stress_result
    )
    reason_codes.extend(robustness_failures)

    trade_count_value = int(stats.get("total_trades", 0))
    gate_eval = evaluate_economic_validity_gates_v1(
        policy=policy,
        net_expectancy=stats.get("expectancy"),
        profit_factor=stats.get("profit_factor"),
        max_drawdown=stats.get("max_drawdown"),
        trade_count=trade_count_value,
    )
    gates_pass = gate_eval.gates_pass
    reason_codes.extend(gate_eval.reason_codes)

    policy_version_bound = policy.is_version_bound()
    funding_bound = cost.funding_model_version != "NOT_BOUND"
    parameter_sensitivity_bound = False
    parameter_sensitivity_payload: dict[str, Any] = {
        "semantic": MetricSemantic.NOT_COMPUTED.value,
        "reason_code": "parameter_sensitivity_not_bound_in_step29m_scope",
    }

    funding_drag_result = None
    funding_drag_metric = _not_computed_metric("funding_drag_not_bound")
    if funding_bound:
        try:
            initial_equity = float(cfg.get("backtest", {}).get("initial_cash", 10_000.0))
            funding_drag_result = compute_funding_drag_v1(
                bars=bars,
                position_series=wiring_result.signals,
                initial_equity=initial_equity,
                config=load_funding_model_config_v1(cfg),
                data_digest=computed_data_digest,
            )
            funding_drag_metric = MetricFieldV1(
                semantic=MetricSemantic.COMPUTED,
                value=float(funding_drag_result.funding_drag),
            )
        except FundingModelError as exc:
            reason_codes.append(f"funding_drag_compute_failed:{exc}")
            funding_bound = False
            reason_codes.append("funding_model_not_bound")

    if sensitivity_requested:
        try:
            sensitivity_result = run_parameter_sensitivity_v1(
                bars=bars,
                cfg=cfg,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                data_digest=computed_data_digest,
                instrument_id=instrument_id,
                explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
                policy=policy,
            )
            parameter_sensitivity_payload = serialize_parameter_sensitivity_results_v1(
                sensitivity_result
            )
            parameter_sensitivity_bound = True
            reason_codes = [
                code
                for code in reason_codes
                if code != "parameter_sensitivity_not_bound_in_step29m_scope"
            ]
            reason_codes.append("parameter_sensitivity_pipeline_bound")
            if not sensitivity_result.parameter_robustness_policy_pass:
                reason_codes.append("parameter_robustness_policy_blocked_missing_thresholds")
        except ParameterSensitivityError as exc:
            reason_codes.append(f"parameter_sensitivity_failed:{exc}")
            parameter_sensitivity_payload = {
                "semantic": MetricSemantic.NOT_COMPUTED.value,
                "reason_code": f"parameter_sensitivity_failed:{exc}",
            }

    status = _resolve_status(
        reason_codes=reason_codes,
        robustness_failures=robustness_failures,
        data_admissible=dataset_admissible,
        policy_version_bound=policy_version_bound,
        funding_bound=funding_bound,
        parameter_sensitivity_bound=parameter_sensitivity_bound,
        gates_pass=gates_pass,
    )
    _fail_closed(status.value not in _STEP29M_ALLOWED_STATUSES, "status_not_allowed_for_step29m")

    first_outcome = wiring_result.bar_outcomes[0]
    chain = mv2_wiring.compute_mv2_evidence_chain_digests_v1(
        context=first_outcome.context,
        evidence=first_outcome.evidence,
        registry_snapshot=wiring_result.registry_snapshot,
        cost_config=cost,
        strategy_id=strategy_id,
        data_period=_period_label(bars),
        fee_model_version=cost.fee_model_version,
        slippage_model_version=cost.slippage_model_version,
        funding_model_version_or_status=cost.funding_model_version,
        execution_model_version=cost.execution_model_version,
        config_digest=_stable_digest(
            {"cfg": dict(cfg), "owner": ECONOMIC_VIABILITY_EVIDENCE_OWNER}
        ),
        data_digest=computed_data_digest,
        walk_forward_result_digest_or_status=(
            wf_result.split_contract_digest if wf_result is not None else "not_run"
        ),
        monte_carlo_result_digest_or_status=(
            _stable_digest(_serialize_monte_carlo(mc_result))
            if mc_result is not None
            else "not_run"
        ),
        stress_result_digest_or_status=(
            _stable_digest(_serialize_stress(stress_result))
            if stress_result is not None
            else "not_run"
        ),
        metrics_digest=_stable_digest({k: float(v) for k, v in stats.items()}),
    )

    semantic_payload = {
        "strategy_id": strategy_id,
        "status": status.value,
        "wiring_chain_digest": chain["wiring_chain_digest"],
        "reason_codes": sorted(set(reason_codes)),
    }
    manifest_digest = _stable_digest(semantic_payload)

    economic_validity_proven = status is EconomicViabilityStatus.ECONOMICALLY_VIABLE_OFFLINE

    return EconomicViabilityEvidenceV1(
        contract_version=ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
        owner=ECONOMIC_VIABILITY_EVIDENCE_OWNER,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        instrument_id_or_universe=instrument_id,
        canonical_trading_logic_version=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        data_period=_period_label(bars),
        training_period=(
            _period_label(bars.iloc[wf_result.windows[0].train_slice])
            if wf_result is not None and wf_result.windows
            else "not_run"
        ),
        validation_period="not_applicable_offline_slice",
        out_of_sample_period=(
            _period_label(bars.iloc[wf_result.windows[0].test_slice])
            if wf_result is not None and wf_result.windows
            else "not_run"
        ),
        fee_model_version=cost.fee_model_version,
        slippage_model_version=cost.slippage_model_version,
        funding_model_version=cost.funding_model_version,
        execution_model_version=cost.execution_model_version,
        config_digest=_stable_digest(
            {"cfg": dict(cfg), "owner": ECONOMIC_VIABILITY_EVIDENCE_OWNER}
        ),
        implementation_digest=chain["implementation_digest"],
        data_digest=computed_data_digest,
        gross_return=_metric_from_stats("total_return", stats),
        net_return=_metric_from_stats("total_return", stats),
        net_expectancy=_metric_from_stats("expectancy", stats),
        profit_factor=_metric_from_stats("profit_factor", stats),
        sharpe=_metric_from_stats("sharpe", stats),
        sortino=_metric_from_stats("sortino", stats),
        max_drawdown=_metric_from_stats("max_drawdown", stats),
        calmar=_metric_from_stats("calmar", stats),
        trade_count=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=float(trade_count_value)),
        turnover=_not_computed_metric("turnover_not_bound_in_step29m_scope"),
        fee_drag=_not_computed_metric("fee_drag_decomposition_not_bound"),
        funding_drag=funding_drag_metric,
        slippage_impact=_not_computed_metric("slippage_impact_decomposition_not_bound"),
        tail_loss=_not_computed_metric("tail_loss_metric_not_bound"),
        time_in_market=_not_computed_metric("time_in_market_not_bound"),
        long_contribution=_not_computed_metric("long_short_attribution_not_bound"),
        short_contribution=_not_computed_metric("long_short_attribution_not_bound"),
        regime_breakdown={
            "semantic": MetricSemantic.NOT_COMPUTED.value,
            "reason_code": "regime_breakdown_not_bound",
        },
        portfolio_contribution={
            "semantic": MetricSemantic.NOT_COMPUTED.value,
            "reason_code": "single_strategy_slice",
        },
        walk_forward_results=(
            _serialize_walk_forward(wf_result)
            if wf_result is not None
            else {
                "semantic": MetricSemantic.NOT_COMPUTED.value,
                "reason_code": "walk_forward_not_run",
            }
        ),
        monte_carlo_results=(
            _serialize_monte_carlo(mc_result)
            if mc_result is not None
            else {
                "semantic": MetricSemantic.NOT_COMPUTED.value,
                "reason_code": "monte_carlo_not_run",
            }
        ),
        stress_results=(
            _serialize_stress(stress_result)
            if stress_result is not None
            else {"semantic": MetricSemantic.NOT_COMPUTED.value, "reason_code": "stress_not_run"}
        ),
        parameter_sensitivity_results=parameter_sensitivity_payload,
        status=status,
        reason_codes=tuple(sorted(set(reason_codes))),
        manifest_digest=manifest_digest,
        wiring_chain_digest=chain["wiring_chain_digest"],
        randomness_seed=monte_carlo_seed,
        data_admissibility=dataset_admissibility_payload,
        cost_binding={
            "cost_model_version": cost.cost_model_version,
            "economic_interpretation_allowed": cost.economic_interpretation_allowed,
            "zero_cost_explicitly_requested": cost.zero_cost_explicitly_requested,
            "reason_codes": list(cost.reason_codes),
            "latency_assumption": cost.latency_assumption,
            "partial_fill_assumption": cost.partial_fill_assumption,
            "spread_application_policy": cost.spread_application_policy,
            "funding_model_version": cost.funding_model_version,
            "funding_rate_source": cost.funding_rate_source,
            "funding_application_policy": cost.funding_application_policy,
            "funding_binding_status": (
                "BOUND" if funding_bound and funding_drag_result is not None else "NOT_BOUND"
            ),
            "funding_evidence_digest": (
                funding_drag_result.evidence_digest() if funding_drag_result is not None else ""
            ),
        },
        policy_version=policy.policy_version,
        policy_digest=policy.config_digest(),
        policy_threshold_status=policy.policy_threshold_status(),
        economic_validity_proven=economic_validity_proven,
        profitability_claim_allowed=False,
    )


def economic_viability_evidence_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "economic_viability_evidence_v1",
        "contract_version": ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
        "owner": ECONOMIC_VIABILITY_EVIDENCE_OWNER,
        "allowed_statuses_step29m": sorted(_STEP29M_ALLOWED_STATUSES),
        "required_fields": [
            "strategy_id",
            "strategy_version",
            "instrument_id_or_universe",
            "canonical_trading_logic_version",
            "data_period",
            "training_period",
            "validation_period",
            "out_of_sample_period",
            "fee_model_version",
            "slippage_model_version",
            "funding_model_version",
            "execution_model_version",
            "config_digest",
            "implementation_digest",
            "data_digest",
            "gross_return",
            "net_return",
            "net_expectancy",
            "profit_factor",
            "sharpe",
            "sortino",
            "max_drawdown",
            "calmar",
            "trade_count",
            "turnover",
            "fee_drag",
            "funding_drag",
            "slippage_impact",
            "tail_loss",
            "time_in_market",
            "long_contribution",
            "short_contribution",
            "regime_breakdown",
            "portfolio_contribution",
            "walk_forward_results",
            "monte_carlo_results",
            "stress_results",
            "parameter_sensitivity_results",
            "status",
            "reason_codes",
            "manifest_digest",
        ],
        "metric_semantics": [semantic.value for semantic in MetricSemantic],
        "data_source_kinds": [kind.value for kind in DataSourceKind],
        "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
    }


@dataclass(frozen=True)
class PersistedEconomicViabilityEvidenceBundleV1:
    output_dir: Path
    evidence_path: Path
    schema_path: Path
    manifest_path: Path
    manifest_verify_rc: int


@dataclass(frozen=True)
class LoadedEconomicViabilityEvidenceBundleV1:
    output_dir: Path
    evidence: EconomicViabilityEvidenceV1
    config_snapshot: dict[str, Any]
    metrics: dict[str, Any]
    input_provenance: dict[str, Any]
    manifest_verify_rc: int


@dataclass(frozen=True)
class ReproducibilityVerificationResultV1:
    reproducible: bool
    manifest_digest_match: bool
    semantic_dict_match: bool
    original_manifest_digest: str
    rebuilt_manifest_digest: str
    reason_codes: tuple[str, ...]


def _metric_field_from_dict(payload: Mapping[str, Any], *, field_name: str) -> MetricFieldV1:
    if not isinstance(payload, Mapping):
        raise EconomicViabilityEvidenceError(f"metric_field_not_mapping:{field_name}")
    semantic_raw = payload.get("semantic")
    if semantic_raw is None:
        raise EconomicViabilityEvidenceError(f"metric_semantic_missing:{field_name}")
    try:
        semantic = MetricSemantic(str(semantic_raw))
    except ValueError as exc:
        raise EconomicViabilityEvidenceError(f"metric_semantic_invalid:{field_name}") from exc
    value_raw = payload.get("value")
    value = None if value_raw is None else float(value_raw)
    reason_code = payload.get("reason_code")
    if reason_code is not None:
        reason_code = str(reason_code)
    if semantic is MetricSemantic.COMPUTED and value is None:
        raise EconomicViabilityEvidenceError(f"computed_metric_missing_value:{field_name}")
    if semantic is not MetricSemantic.COMPUTED and value is not None:
        raise EconomicViabilityEvidenceError(f"non_computed_metric_has_value:{field_name}")
    return MetricFieldV1(semantic=semantic, value=value, reason_code=reason_code)


def _mapping_from_dict(payload: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise EconomicViabilityEvidenceError(f"mapping_field_not_mapping:{field_name}")
    return dict(payload)


def economic_viability_evidence_from_dict_v1(
    payload: Mapping[str, Any],
) -> EconomicViabilityEvidenceV1:
    schema = economic_viability_evidence_schema_v1()
    for key in schema["required_fields"]:
        if key not in payload:
            raise EconomicViabilityEvidenceError(f"required_field_missing:{key}")
    status_raw = payload.get("status")
    try:
        status = EconomicViabilityStatus(str(status_raw))
    except ValueError as exc:
        raise EconomicViabilityEvidenceError(f"status_invalid:{status_raw}") from exc
    _fail_closed(status.value not in _STEP29M_ALLOWED_STATUSES, "status_not_allowed_for_step29m")
    reason_codes_raw = payload.get("reason_codes")
    if not isinstance(reason_codes_raw, list):
        raise EconomicViabilityEvidenceError("reason_codes_not_list")
    return EconomicViabilityEvidenceV1(
        contract_version=str(payload["contract_version"]),
        owner=str(payload["owner"]),
        strategy_id=str(payload["strategy_id"]),
        strategy_version=str(payload["strategy_version"]),
        instrument_id_or_universe=str(payload["instrument_id_or_universe"]),
        canonical_trading_logic_version=str(payload["canonical_trading_logic_version"]),
        data_period=str(payload["data_period"]),
        training_period=str(payload["training_period"]),
        validation_period=str(payload["validation_period"]),
        out_of_sample_period=str(payload["out_of_sample_period"]),
        fee_model_version=str(payload["fee_model_version"]),
        slippage_model_version=str(payload["slippage_model_version"]),
        funding_model_version=str(payload["funding_model_version"]),
        execution_model_version=str(payload["execution_model_version"]),
        config_digest=str(payload["config_digest"]),
        implementation_digest=str(payload["implementation_digest"]),
        data_digest=str(payload["data_digest"]),
        gross_return=_metric_field_from_dict(payload["gross_return"], field_name="gross_return"),
        net_return=_metric_field_from_dict(payload["net_return"], field_name="net_return"),
        net_expectancy=_metric_field_from_dict(
            payload["net_expectancy"], field_name="net_expectancy"
        ),
        profit_factor=_metric_field_from_dict(payload["profit_factor"], field_name="profit_factor"),
        sharpe=_metric_field_from_dict(payload["sharpe"], field_name="sharpe"),
        sortino=_metric_field_from_dict(payload["sortino"], field_name="sortino"),
        max_drawdown=_metric_field_from_dict(payload["max_drawdown"], field_name="max_drawdown"),
        calmar=_metric_field_from_dict(payload["calmar"], field_name="calmar"),
        trade_count=_metric_field_from_dict(payload["trade_count"], field_name="trade_count"),
        turnover=_metric_field_from_dict(payload["turnover"], field_name="turnover"),
        fee_drag=_metric_field_from_dict(payload["fee_drag"], field_name="fee_drag"),
        funding_drag=_metric_field_from_dict(payload["funding_drag"], field_name="funding_drag"),
        slippage_impact=_metric_field_from_dict(
            payload["slippage_impact"], field_name="slippage_impact"
        ),
        tail_loss=_metric_field_from_dict(payload["tail_loss"], field_name="tail_loss"),
        time_in_market=_metric_field_from_dict(
            payload["time_in_market"], field_name="time_in_market"
        ),
        long_contribution=_metric_field_from_dict(
            payload["long_contribution"], field_name="long_contribution"
        ),
        short_contribution=_metric_field_from_dict(
            payload["short_contribution"], field_name="short_contribution"
        ),
        regime_breakdown=_mapping_from_dict(
            payload["regime_breakdown"], field_name="regime_breakdown"
        ),
        portfolio_contribution=_mapping_from_dict(
            payload["portfolio_contribution"], field_name="portfolio_contribution"
        ),
        walk_forward_results=_mapping_from_dict(
            payload["walk_forward_results"], field_name="walk_forward_results"
        ),
        monte_carlo_results=_mapping_from_dict(
            payload["monte_carlo_results"], field_name="monte_carlo_results"
        ),
        stress_results=_mapping_from_dict(payload["stress_results"], field_name="stress_results"),
        parameter_sensitivity_results=_mapping_from_dict(
            payload["parameter_sensitivity_results"],
            field_name="parameter_sensitivity_results",
        ),
        status=status,
        reason_codes=tuple(str(code) for code in reason_codes_raw),
        manifest_digest=str(payload["manifest_digest"]),
        wiring_chain_digest=str(payload.get("wiring_chain_digest", "")),
        randomness_seed=int(payload.get("randomness_seed", 0)),
        data_admissibility=_mapping_from_dict(
            payload.get("data_admissibility", {}), field_name="data_admissibility"
        ),
        cost_binding=_mapping_from_dict(payload.get("cost_binding", {}), field_name="cost_binding"),
        policy_version=str(payload.get("policy_version", ECONOMIC_VALIDITY_POLICY_VERSION)),
        policy_digest=str(payload.get("policy_digest", "")),
        policy_threshold_status=str(payload.get("policy_threshold_status", "")),
        economic_validity_proven=bool(payload.get("economic_validity_proven", False)),
        profitability_claim_allowed=bool(payload.get("profitability_claim_allowed", False)),
    )


def load_economic_viability_evidence_bundle_v1(
    output_dir: Path,
    *,
    verify_manifest: bool = True,
) -> LoadedEconomicViabilityEvidenceBundleV1:
    if not output_dir.is_dir():
        raise EconomicViabilityEvidenceError(f"bundle_dir_missing:{output_dir}")
    manifest_verify_rc = 0
    if verify_manifest:
        ok, message = verify_manifest_sha256(output_dir)
        manifest_verify_rc = 0 if ok else 1
        if not ok:
            raise EconomicViabilityEvidenceError(f"manifest_verify_failed:{message}")
    evidence_path = output_dir / ARTIFACT_FILENAME
    if not evidence_path.is_file():
        raise EconomicViabilityEvidenceError(f"evidence_artifact_missing:{evidence_path}")
    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence = economic_viability_evidence_from_dict_v1(evidence_payload)
    config_snapshot = json.loads((output_dir / "CONFIG_SNAPSHOT.json").read_text(encoding="utf-8"))
    metrics = json.loads((output_dir / "METRICS.json").read_text(encoding="utf-8"))
    input_provenance = json.loads(
        (output_dir / "INPUT_PROVENANCE.json").read_text(encoding="utf-8")
    )
    return LoadedEconomicViabilityEvidenceBundleV1(
        output_dir=output_dir,
        evidence=evidence,
        config_snapshot=config_snapshot,
        metrics=metrics,
        input_provenance=input_provenance,
        manifest_verify_rc=manifest_verify_rc,
    )


def verify_economic_viability_evidence_reproducibility_v1(
    *,
    persisted: EconomicViabilityEvidenceV1,
    rebuilt: EconomicViabilityEvidenceV1,
) -> ReproducibilityVerificationResultV1:
    semantic_dict_match = persisted.to_semantic_dict() == rebuilt.to_semantic_dict()
    manifest_digest_match = persisted.manifest_digest == rebuilt.manifest_digest
    reason_codes: list[str] = []
    if not semantic_dict_match:
        reason_codes.append("semantic_dict_mismatch")
    if not manifest_digest_match:
        reason_codes.append("manifest_digest_mismatch")
    return ReproducibilityVerificationResultV1(
        reproducible=semantic_dict_match and manifest_digest_match,
        manifest_digest_match=manifest_digest_match,
        semantic_dict_match=semantic_dict_match,
        original_manifest_digest=persisted.manifest_digest,
        rebuilt_manifest_digest=rebuilt.manifest_digest,
        reason_codes=tuple(reason_codes),
    )


def build_and_persist_economic_viability_evidence_bundle_v1(
    output_dir: Path,
    *,
    bars: pd.DataFrame,
    data_admissibility: DataAdmissibilityV1,
    strategy_id: str,
    cfg: Mapping[str, Any],
    input_provenance: Mapping[str, Any],
    instrument_id: str = mv2_wiring.MV2_REQUIRED_INSTRUMENT_ID,
    walk_forward_train_bars: int = 8,
    walk_forward_test_bars: int = 4,
    walk_forward_step_bars: int = 4,
    monte_carlo_runs: int = 16,
    monte_carlo_seed: int = 42,
    explicit_zero_cost_non_economic: bool = False,
    verify_reproducibility: bool = True,
) -> tuple[PersistedEconomicViabilityEvidenceBundleV1, ReproducibilityVerificationResultV1]:
    evidence = build_economic_viability_evidence_v1(
        bars=bars,
        data_admissibility=data_admissibility,
        strategy_id=strategy_id,
        cfg=cfg,
        instrument_id=instrument_id,
        walk_forward_train_bars=walk_forward_train_bars,
        walk_forward_test_bars=walk_forward_test_bars,
        walk_forward_step_bars=walk_forward_step_bars,
        monte_carlo_runs=monte_carlo_runs,
        monte_carlo_seed=monte_carlo_seed,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
    )
    metrics = {
        key: field.to_dict()
        for key, field in (
            ("gross_return", evidence.gross_return),
            ("net_return", evidence.net_return),
            ("net_expectancy", evidence.net_expectancy),
            ("profit_factor", evidence.profit_factor),
            ("sharpe", evidence.sharpe),
            ("sortino", evidence.sortino),
            ("max_drawdown", evidence.max_drawdown),
            ("calmar", evidence.calmar),
            ("trade_count", evidence.trade_count),
        )
    }
    bundle = persist_economic_viability_evidence_bundle_v1(
        output_dir,
        evidence,
        config_snapshot={"cfg": dict(cfg), "strategy_id": strategy_id},
        metrics=metrics,
        input_provenance=dict(input_provenance),
    )
    rebuilt = build_economic_viability_evidence_v1(
        bars=bars,
        data_admissibility=data_admissibility,
        strategy_id=strategy_id,
        cfg=cfg,
        instrument_id=instrument_id,
        walk_forward_train_bars=walk_forward_train_bars,
        walk_forward_test_bars=walk_forward_test_bars,
        walk_forward_step_bars=walk_forward_step_bars,
        monte_carlo_runs=monte_carlo_runs,
        monte_carlo_seed=monte_carlo_seed,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
    )
    repro = verify_economic_viability_evidence_reproducibility_v1(
        persisted=evidence,
        rebuilt=rebuilt,
    )
    if verify_reproducibility and not repro.reproducible:
        raise EconomicViabilityEvidenceError(
            f"reproducibility_verification_failed:{','.join(repro.reason_codes)}"
        )
    repro_payload = {
        "reproducible": repro.reproducible,
        "manifest_digest_match": repro.manifest_digest_match,
        "semantic_dict_match": repro.semantic_dict_match,
        "original_manifest_digest": repro.original_manifest_digest,
        "rebuilt_manifest_digest": repro.rebuilt_manifest_digest,
        "reason_codes": list(repro.reason_codes),
    }
    (output_dir / "REPRODUCIBILITY_RESULT.txt").write_text(
        json.dumps(repro_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    ok, message = verify_manifest_sha256(output_dir)
    if not ok:
        raise EconomicViabilityEvidenceError(f"manifest_verify_failed_after_repro:{message}")
    return bundle, repro


def persist_economic_viability_evidence_bundle_v1(
    output_dir: Path,
    evidence: EconomicViabilityEvidenceV1,
    *,
    config_snapshot: Mapping[str, Any],
    metrics: Mapping[str, Any],
    input_provenance: Mapping[str, Any],
) -> PersistedEconomicViabilityEvidenceBundleV1:
    if output_dir.exists():
        raise EconomicViabilityEvidenceError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=False)

    evidence_path = output_dir / ARTIFACT_FILENAME
    schema_path = output_dir / SCHEMA_FILENAME
    evidence_path.write_text(
        json.dumps(evidence.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    schema_path.write_text(
        json.dumps(economic_viability_evidence_schema_v1(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "CONFIG_SNAPSHOT.json").write_text(
        json.dumps(dict(config_snapshot), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "METRICS.json").write_text(
        json.dumps(dict(metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "INPUT_PROVENANCE.json").write_text(
        json.dumps(dict(input_provenance), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "WALK_FORWARD_RESULTS.json").write_text(
        json.dumps(evidence.walk_forward_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "MONTE_CARLO_RESULTS.json").write_text(
        json.dumps(evidence.monte_carlo_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "STRESS_RESULTS.json").write_text(
        json.dumps(evidence.stress_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "PARAMETER_SENSITIVITY_RESULTS.json").write_text(
        json.dumps(evidence.parameter_sensitivity_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    grid_payload = evidence.parameter_sensitivity_results.get("grid")
    if isinstance(grid_payload, Mapping):
        (output_dir / "PARAMETER_GRID.json").write_text(
            json.dumps(dict(grid_payload), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    write_manifest_sha256(output_dir)
    ok, message = verify_manifest_sha256(output_dir)
    manifest_verify_rc = 0 if ok else 1
    if not ok:
        raise EconomicViabilityEvidenceError(f"manifest_verify_failed:{message}")

    return PersistedEconomicViabilityEvidenceBundleV1(
        output_dir=output_dir,
        evidence_path=evidence_path,
        schema_path=schema_path,
        manifest_path=output_dir / MANIFEST_FILENAME,
        manifest_verify_rc=manifest_verify_rc,
    )
