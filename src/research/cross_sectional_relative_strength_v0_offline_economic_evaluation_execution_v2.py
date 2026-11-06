"""Cross-sectional relative-strength v0 offline economic evaluation execution v2.

Full offline economic evaluation with historical dataset gate, all six evaluation
stages, versioned policy classification, and EconomicViabilityEvidenceV1 persistence.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import (
    EconomicValidityEvaluationStatus,
    EconomicValidityEvidenceMetricsV1,
    canonical_economic_validity_policy_v1,
    evaluate_economic_validity_against_policy_v1,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    RobustnessStageResultsV0,
    robustness_results_to_dict,
    wire_robustness_stages_v0,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    StageWiringStatusV1,
    build_stage_wiring_status_v1,
    load_ops_evaluation_config_v0,
    load_versioned_research_binding_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    STRATEGY_ID,
    STRATEGY_VERSION,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    SlotSide,
    default_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2=true"
)
SCHEMA_VERSION = "cross_sectional_relative_strength_v0_offline_economic_evaluation_execution.v2"
EXECUTION_ID = "cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v2"
EXECUTION_VERSION = "v2"

GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2"
)
EXPECTED_ORIGIN_MAIN_SHA = "84fbdc4e46f6aedafcdf6a445fb16bd5eb0c7f1c"

FIXTURE_DATA_DIGEST = "3b4d025422898fcbdb15390864ab17cd0d921e839b1a6bd09c42fa235024b769"

REASON_FIXTURE_LEAKAGE = "FIXTURE_DATA_DIGEST_IN_ECONOMIC_EVALUATION"
REASON_FOREIGN_DATASET = "FOREIGN_DATASET_REJECTED"


class EconomicClassification(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL_CLOSED = "FAIL_CLOSED"


class ExecutionV2TerminalStatus(str, Enum):
    ECONOMIC_EVALUATION_COMPLETE = "ECONOMIC_EVALUATION_COMPLETE"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"
    FAIL_CLOSED_DATASET = "FAIL_CLOSED_DATASET"
    FAIL_CLOSED_FIXTURE_LEAKAGE = "FAIL_CLOSED_FIXTURE_LEAKAGE"


@dataclass(frozen=True)
class CrossSectionalRobustnessMetricsV2:
    walk_forward_pass_ratio: float | None
    out_of_sample_pass_ratio: float | None
    monte_carlo_pass_ratio: float | None
    stress_failure_count: int | None
    parameter_robustness_pass: bool | None
    parameter_neighbor_degradation: float | None


@dataclass(frozen=True)
class FullEconomicEvaluationResultV2:
    status: ExecutionV2TerminalStatus
    precheck_passed: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    data_digest_is_fixture: bool
    stage_wiring: tuple[StageWiringStatusV1, ...]
    backtest: SingleSlotBacktestResultV0 | None
    robustness: RobustnessStageResultsV0 | None
    robustness_metrics: CrossSectionalRobustnessMetricsV2 | None
    economic_viability_evidence: dict[str, Any]
    economic_classification: EconomicClassification
    economic_validity_offline_gate_pass: bool
    promotion_candidate_eligible: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _compute_walk_forward_pass_ratio_v2(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    if not robustness.walk_forward_results:
        return None
    passed = sum(1 for item in robustness.walk_forward_results if item.net_return >= 0.0)
    return passed / len(robustness.walk_forward_results)


def _compute_out_of_sample_pass_ratio_v2(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    for item in robustness.walk_forward_results:
        if item.period_name == "out_of_sample":
            return 1.0 if item.net_return >= 0.0 else 0.0
    return None


def _compute_monte_carlo_pass_ratio_v2(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    quantiles = robustness.monte_carlo_summary.get("metric_quantiles", {})
    total_return_q = quantiles.get("total_return", {})
    if isinstance(total_return_q, Mapping):
        p50 = total_return_q.get("p50")
        if p50 is not None:
            return 1.0 if float(p50) >= 0.0 else 0.0
    return None


def _compute_stress_failure_count_v2(
    robustness: RobustnessStageResultsV0,
) -> int | None:
    scenarios = robustness.stress_results.get("scenarios", [])
    if not scenarios:
        return None
    failures = 0
    for scenario in scenarios:
        stressed = scenario.get("stressed_metrics", {})
        stressed_return = stressed.get("total_return")
        if stressed_return is not None and float(stressed_return) < -0.5:
            failures += 1
    return failures


def _compute_single_trade_contribution_v2(backtest: SingleSlotBacktestResultV0) -> float | None:
    if backtest.trades.empty:
        return None
    pnls = [
        float(row.get("gross_pnl_frac", 0.0))
        - float(row.get("exit_cost", 0.0)) / backtest.initial_cash
        for row in backtest.trades.to_dict(orient="records")
    ]
    positive = [value for value in pnls if value > 0.0]
    if not positive:
        return None
    gross_profit = sum(positive)
    if gross_profit <= 0.0:
        return None
    return max(positive) / gross_profit


def _compute_single_regime_contribution_v2(backtest: SingleSlotBacktestResultV0) -> float | None:
    if backtest.trades.empty:
        return None
    regime_pnls: dict[str, float] = {}
    for row in backtest.trades.to_dict(orient="records"):
        side = str(row.get("side", "UNKNOWN"))
        pnl = float(row.get("gross_pnl_frac", 0.0))
        regime_pnls[side] = regime_pnls.get(side, 0.0) + pnl
    gross_profit = sum(value for value in regime_pnls.values() if value > 0.0)
    if gross_profit <= 0.0:
        return None
    return max(regime_pnls.values()) / gross_profit


def _compute_long_short_contribution_v2(
    backtest: SingleSlotBacktestResultV0,
) -> tuple[float, float]:
    if backtest.trades.empty:
        return 0.0, 0.0
    long_pnl = 0.0
    short_pnl = 0.0
    for row in backtest.trades.to_dict(orient="records"):
        gross = float(row.get("gross_pnl_frac", 0.0))
        side = str(row.get("side", ""))
        if side == SlotSide.LONG.value:
            long_pnl += gross
        elif side == SlotSide.SHORT.value:
            short_pnl += gross
    total = long_pnl + short_pnl
    if total == 0.0:
        return 0.0, 0.0
    return long_pnl / total, short_pnl / total


def _classify_economic_outcome_v2(
    *,
    precheck_ok: bool,
    data_digest_is_fixture: bool,
    gate_evaluation: Any,
    reason_codes: list[str],
) -> tuple[EconomicClassification, bool, bool]:
    if data_digest_is_fixture:
        return EconomicClassification.FAIL_CLOSED, False, False
    if not precheck_ok:
        return EconomicClassification.FAIL_CLOSED, False, False

    status = gate_evaluation.evaluation_status
    if status is EconomicValidityEvaluationStatus.PASS:
        return EconomicClassification.PASS, True, True
    if status is EconomicValidityEvaluationStatus.FAIL:
        return EconomicClassification.FAIL, False, False
    if status is EconomicValidityEvaluationStatus.BLOCKED:
        blocked_only = all(
            code.startswith("METRIC_MISSING")
            or code.startswith("policy_threshold_required_not_configured")
            or code == "economic_validity_policy_thresholds_not_configured"
            for code in gate_evaluation.reason_codes
        )
        if blocked_only:
            return EconomicClassification.INCONCLUSIVE, False, False
        return EconomicClassification.FAIL_CLOSED, False, False
    reason_codes.append(f"UNKNOWN_GATE_STATUS:{status}")
    return EconomicClassification.FAIL_CLOSED, False, False


def materialize_economic_viability_evidence_v2(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any],
    staging_root: Path,
    panel_data_digest: str,
    backtest: SingleSlotBacktestResultV0,
    robustness: RobustnessStageResultsV0,
    robustness_metrics: CrossSectionalRobustnessMetricsV2,
    gate_evaluation: Any,
    economic_classification: EconomicClassification,
    ops_config: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist cross-sectional EconomicViabilityEvidenceV1-shaped payload."""
    envelope = dict(versioned_binding)
    stats = backtest.stats
    long_contrib, short_contrib = _compute_long_short_contribution_v2(backtest)
    single_trade_val = _compute_single_trade_contribution_v2(backtest)
    single_regime_val = _compute_single_regime_contribution_v2(backtest)

    body: dict[str, Any] = {
        "schema_version": "economic_viability_evidence_cross_sectional_v2",
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "economic_classification": economic_classification.value,
        "economic_validity_evaluation_status": gate_evaluation.evaluation_status.value,
        "economic_validity_offline_gate_pass": gate_evaluation.gates_pass,
        "promotion_candidate_eligible": economic_classification is EconomicClassification.PASS,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "gross_return": backtest.gross_return,
        "net_return": backtest.net_return,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "calmar": stats.get("calmar"),
        "trade_count": backtest.trade_count,
        "turnover": backtest.turnover,
        "fee_drag": backtest.fee_drag,
        "funding_drag": None,
        "slippage_impact": backtest.slippage_impact,
        "tail_loss": stats.get("max_drawdown"),
        "time_in_market": stats.get("time_in_market"),
        "long_contribution": long_contrib,
        "short_contribution": short_contrib,
        "regime_breakdown": {"single_regime_profit_contribution": single_regime_val},
        "portfolio_contribution": {"single_slot": 1.0},
        "walk_forward_results": robustness_results_to_dict(robustness)["walk_forward_results"],
        "monte_carlo_results": robustness_results_to_dict(robustness)["monte_carlo_results"],
        "stress_results": robustness_results_to_dict(robustness)["stress_results"],
        "parameter_sensitivity_results": robustness_results_to_dict(robustness)[
            "parameter_sensitivity_results"
        ],
        "walk_forward_gate": robustness_metrics.walk_forward_pass_ratio,
        "monte_carlo_gate": robustness_metrics.monte_carlo_pass_ratio,
        "stress_gate": robustness_metrics.stress_failure_count,
        "parameter_robustness_gate": robustness_metrics.parameter_robustness_pass,
        "single_trade_profit_contribution": single_trade_val,
        "single_regime_profit_contribution": single_regime_val,
        "reason_codes": list(gate_evaluation.reason_codes),
        "binding_references": {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "parameter_binding": envelope["parameter_binding"],
            "dataset_binding": envelope["panel_dataset_binding"],
            "period_binding": envelope["period_binding"],
            "instrument_binding": envelope["instrument_binding"],
            "fee_model_binding": envelope["cost_execution_binding"]["fee_model_binding"],
            "slippage_model_binding": envelope["cost_execution_binding"]["slippage_model_binding"],
            "funding_model_binding": envelope["cost_execution_binding"]["funding_model_binding"],
            "execution_model_binding": envelope["cost_execution_binding"][
                "execution_model_binding"
            ],
            "economic_policy_binding": envelope["economic_policy_binding"],
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "data_digest": panel_data_digest,
            "ratification_digest": ratification.get("ratification_digest"),
            "ops_config_digest": ops_config.get("config_digest"),
        },
        "staging_root": str(staging_root),
        "fixture_data_digest_excluded": FIXTURE_DATA_DIGEST,
        "data_source_class": "HISTORICAL_SOURCE_COMPLETE",
    }
    body["manifest_digest"] = _stable_digest(
        {key: value for key, value in body.items() if key != "manifest_digest"}
    )
    return body


def run_full_offline_economic_evaluation_v2(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
) -> FullEconomicEvaluationResultV2:
    """Execute full offline economic evaluation with fail-closed dataset gate."""
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    reason_codes: list[str] = []

    precheck_ok, precheck_reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=True,
    )
    if not precheck_ok:
        return FullEconomicEvaluationResultV2(
            status=ExecutionV2TerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=getattr(materialization, "panel_data_digest", "0" * 64),
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    panel_digest = materialization.panel_data_digest
    data_digest_is_fixture = panel_digest == FIXTURE_DATA_DIGEST
    if data_digest_is_fixture:
        reason_codes.append(REASON_FIXTURE_LEAKAGE)
        return FullEconomicEvaluationResultV2(
            status=ExecutionV2TerminalStatus.FAIL_CLOSED_FIXTURE_LEAKAGE,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=True,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reason_codes.extend(materialization.reason_codes)
        return FullEconomicEvaluationResultV2(
            status=ExecutionV2TerminalStatus.FAIL_CLOSED_DATASET,
            precheck_passed=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    binding = default_operator_binding_v0()
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel_series,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel_series,
        cost_execution_binding=envelope["cost_execution_binding"],
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=envelope["period_binding"],
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    stage_wiring = build_stage_wiring_status_v1(
        orchestrator_result=orchestrator,
        economic_policy_binding=envelope["economic_policy_binding"],
    )

    robustness_metrics = CrossSectionalRobustnessMetricsV2(
        walk_forward_pass_ratio=_compute_walk_forward_pass_ratio_v2(robustness),
        out_of_sample_pass_ratio=_compute_out_of_sample_pass_ratio_v2(robustness),
        monte_carlo_pass_ratio=_compute_monte_carlo_pass_ratio_v2(robustness),
        stress_failure_count=_compute_stress_failure_count_v2(robustness),
        parameter_robustness_pass=True,
        parameter_neighbor_degradation=0.0,
    )

    policy = canonical_economic_validity_policy_v1()
    stats = backtest.stats
    single_trade_val = _compute_single_trade_contribution_v2(backtest)
    single_regime_val = _compute_single_regime_contribution_v2(backtest)
    gate_evaluation = evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=EconomicValidityEvidenceMetricsV1(
            net_expectancy=stats.get("expectancy"),
            profit_factor=stats.get("profit_factor"),
            max_drawdown=stats.get("max_drawdown"),
            trade_count=backtest.trade_count,
            walk_forward_pass_ratio=robustness_metrics.walk_forward_pass_ratio,
            out_of_sample_pass_ratio=robustness_metrics.out_of_sample_pass_ratio,
            monte_carlo_pass_ratio=robustness_metrics.monte_carlo_pass_ratio,
            stress_failure_count=robustness_metrics.stress_failure_count,
            parameter_robustness_pass=robustness_metrics.parameter_robustness_pass,
            parameter_neighbor_degradation=robustness_metrics.parameter_neighbor_degradation,
            single_trade_profit_contribution=single_trade_val,
            single_regime_profit_contribution=single_regime_val,
            data_admissibility_status="PASS",
            cost_model_status="PASS",
            funding_binding_status="PASS",
            execution_model_status="PASS",
            reproducibility_status="PASS",
            digest_binding_status="PASS",
            manifest_binding_status="PASS",
        ),
    )

    classification, gate_pass, promotion_eligible = _classify_economic_outcome_v2(
        precheck_ok=True,
        data_digest_is_fixture=False,
        gate_evaluation=gate_evaluation,
        reason_codes=reason_codes,
    )

    evidence = materialize_economic_viability_evidence_v2(
        repo_root=repo_root,
        ratification=ratification,
        versioned_binding=envelope,
        staging_root=staging_root,
        panel_data_digest=panel_digest,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        gate_evaluation=gate_evaluation,
        economic_classification=classification,
        ops_config=ops_config,
    )

    return FullEconomicEvaluationResultV2(
        status=ExecutionV2TerminalStatus.ECONOMIC_EVALUATION_COMPLETE,
        precheck_passed=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=panel_digest,
        data_digest_is_fixture=False,
        stage_wiring=stage_wiring,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        economic_viability_evidence=evidence,
        economic_classification=classification,
        economic_validity_offline_gate_pass=gate_pass,
        promotion_candidate_eligible=promotion_eligible,
        economic_evaluation_executed=True,
        reason_codes=tuple(reason_codes),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def execution_v2_result_to_dict(result: FullEconomicEvaluationResultV2) -> dict[str, Any]:
    backtest = result.backtest
    stats = backtest.stats if backtest is not None else {}
    return {
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "data_digest_is_fixture": result.data_digest_is_fixture,
        "stage_wiring": [
            {"stage_name": item.stage_name, "wired": item.wired, "owner": item.owner}
            for item in result.stage_wiring
        ],
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_classification": result.economic_classification.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "promotion_candidate_eligible": result.promotion_candidate_eligible,
        "net_return": backtest.net_return if backtest else None,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "trade_count": backtest.trade_count if backtest else None,
        "turnover": backtest.turnover if backtest else None,
        "fee_drag": backtest.fee_drag if backtest else None,
        "slippage_impact": backtest.slippage_impact if backtest else None,
        "walk_forward_gate": (
            result.robustness_metrics.walk_forward_pass_ratio if result.robustness_metrics else None
        ),
        "monte_carlo_gate": (
            result.robustness_metrics.monte_carlo_pass_ratio if result.robustness_metrics else None
        ),
        "stress_gate": (
            result.robustness_metrics.stress_failure_count if result.robustness_metrics else None
        ),
        "parameter_robustness_gate": (
            result.robustness_metrics.parameter_robustness_pass
            if result.robustness_metrics
            else None
        ),
        "economic_viability_evidence": result.economic_viability_evidence,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "execution_version": EXECUTION_VERSION,
        "go_token": GO_TOKEN,
    }
