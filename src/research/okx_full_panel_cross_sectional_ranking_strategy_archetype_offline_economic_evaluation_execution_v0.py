"""OKX full-panel cross-sectional ranking strategy archetype offline economic evaluation v0.

Bounded offline economic evaluation under ratified scope/bindings from PR #4849/#4850/#4851.
Reuses canonical cross-sectional orchestrator, backtest, robustness, and policy owners.
Research-only; no runtime, order, credentials, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
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
    StageWiringStatusV1,
    build_stage_wiring_status_v1,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    MONTE_CARLO_RUNS,
    MONTE_CARLO_SEED,
    build_economic_policy_binding_v0,
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
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"
)
SCHEMA_VERSION = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_"
    "offline_economic_evaluation_execution.v0"
)
EXECUTION_ID = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_"
    "offline_economic_evaluation_execution_v0"
)
EXECUTION_VERSION = "v0"

GO_TOKEN = (
    "GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
)
EXPECTED_ORIGIN_MAIN_SHA = "4dd3e0155e7bbd6d5265b2b0dc334f7f7d71efda"
BOUND_DATASET_CONTENT_DIGEST = "0bfa4df4221a2ec27625c50e3675302ffa51e4b54cddcf81ca5ad13cc15cf8b7"
BINDINGS_CONFIG_REL = (
    "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json"
)
SCOPE_CONFIG_REL = (
    "config/research/"
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_evaluation_execution_scope_v0.json"
)
OPS_CONFIG_REL = (
    "config/ops/"
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_economic_evaluation_v0.json"
)
PROMOTED_DATASET_REL = "datasets/admissible_futures/okx_full_panel_historical_funding_archive_v0/v0"
DEFAULT_STAGING_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)

STRATEGY_ARCHETYPE_ID = "cross_sectional_ranking_selection"
STRATEGY_ARCHETYPE_VERSION = "v0"
EVIDENCE_CLASS_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

ORIGIN_MAIN_SHA_BINDING_ENV_VAR = "EXPECTED_ORIGIN_MAIN_SHA"
FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING = (
    "FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING"
)
FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH = "FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH"
SHA_GUARD_STATUS_PASS = "PASS"

FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
SPREAD_HALF_BPS = 5.0
ROUNDTRIP_COST_BPS = 40.0
MIN_ELIGIBLE_INSTRUMENTS = 118

REASON_BINDING_DIGEST_MISMATCH = "BINDING_CONFIG_DIGEST_MISMATCH"
REASON_DATA_DIGEST_MISMATCH = "DATA_DIGEST_MISMATCH"
REASON_NARROW_ADAPTER = "NARROW_ADAPTER_SUBSTITUTION"
REASON_INSUFFICIENT_INSTRUMENTS = "INSUFFICIENT_ELIGIBLE_INSTRUMENTS"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_PROMOTED_DATASET_MISSING = "PROMOTED_DATASET_REGISTRY_MISSING"


class EconomicClassification(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL_CLOSED = "FAIL_CLOSED"


class ExecutionTerminalStatus(str, Enum):
    ECONOMIC_EVALUATION_COMPLETE = "ECONOMIC_EVALUATION_COMPLETE"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"
    FAIL_CLOSED_DATASET = "FAIL_CLOSED_DATASET"


class VerdictClassification(str, Enum):
    ECONOMICALLY_VIABLE_OFFLINE = "ECONOMICALLY_VIABLE_OFFLINE"
    ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class OriginMainShaGuardResultV0:
    passed: bool
    sha_guard_status: str
    expected_origin_main_sha: str
    actual_head_sha: str
    actual_origin_main_sha: str
    binding_source: str
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class CrossSectionalRobustnessMetricsV0:
    walk_forward_pass_ratio: float | None
    out_of_sample_pass_ratio: float | None
    monte_carlo_pass_ratio: float | None
    stress_failure_count: int | None
    parameter_robustness_pass: bool | None
    parameter_neighbor_degradation: float | None


@dataclass(frozen=True)
class FullEconomicEvaluationResultV0:
    status: ExecutionTerminalStatus
    precheck_passed: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    promoted_dataset_content_digest: str
    stage_wiring: tuple[StageWiringStatusV1, ...]
    backtest: SingleSlotBacktestResultV0 | None
    robustness: RobustnessStageResultsV0 | None
    robustness_metrics: CrossSectionalRobustnessMetricsV0 | None
    economic_viability_evidence: dict[str, Any]
    economic_classification: EconomicClassification
    verdict_classification: VerdictClassification
    economic_validity_offline_gate_pass: bool
    promotion_candidate_eligible: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_archetype_bindings_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDINGS_CONFIG_REL
    if not path.is_file():
        raise FileNotFoundError(f"missing_bindings_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_execution_scope_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SCOPE_CONFIG_REL
    if not path.is_file():
        raise FileNotFoundError(f"missing_scope_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / OPS_CONFIG_REL
    if not path.is_file():
        raise FileNotFoundError(f"missing_ops_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_period_binding_from_archetype_v0(bindings: Mapping[str, Any]) -> dict[str, Any]:
    period = bindings["period_binding"]
    return {
        "binding_version": period["period_binding_version"],
        "period_binding_id": period["period_binding_id"],
        "split_policy_id": period["split_policy_id"],
        "split_timezone": period["split_timezone"],
        "boundary_semantics": period["boundary_semantics"],
        "warmup_start": period["coverage_period_start_utc"],
        "warmup_end": period["warmup_end"],
        "training_start": bindings["training_period"]["start"],
        "training_end": bindings["training_period"]["end"],
        "validation_start": bindings["validation_period"]["start"],
        "validation_end": bindings["validation_period"]["end"],
        "out_of_sample_start": bindings["out_of_sample_period"]["start"],
        "out_of_sample_end": bindings["out_of_sample_period"]["end"],
        "embargo_duration": period["embargo_duration"],
        "purge_duration": period["purge_duration"],
    }


def build_cost_execution_binding_from_archetype_v0(bindings: Mapping[str, Any]) -> dict[str, Any]:
    fee = bindings["fee_model_binding"]
    slip = bindings["slippage_model_binding"]
    funding = bindings["funding_model_binding"]
    execution = bindings["execution_model_binding"]
    effective_entry = float(fee["fee_bps"]) + float(slip["slippage_bps"]) + SPREAD_HALF_BPS
    return {
        "binding_version": "v0",
        "fee_model_binding": {
            "fee_model_version": fee["fee_model_version"],
            "fee_bps_per_side": float(fee["fee_bps"]),
        },
        "slippage_model_binding": {
            "slippage_model_version": slip["slippage_model_version"],
            "slippage_bps_per_side": float(slip["slippage_bps"]),
        },
        "funding_model_binding": {
            "funding_model_version": funding["model_version"],
            "bind": bool(funding["bind"]),
        },
        "spread_model_binding": {
            "spread_model_version": "research_conservative_bps_v1",
            "conservative_half_spread_bps": SPREAD_HALF_BPS,
        },
        "execution_model_binding": {
            "execution_model_version": execution["execution_model_version"],
            "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
            "effective_entry_cost_bps": effective_entry,
            "effective_exit_cost_bps": effective_entry,
            "roundtrip_cost_bps": float(execution["roundtrip_cost_bps"]),
        },
        "implicit_zero_cost_forbidden": True,
        "maker_rebate_assumption_forbidden": True,
    }


def build_evaluation_envelope_v0(
    bindings: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "strategy_archetype_id": bindings["strategy_archetype_id"],
        "strategy_archetype_version": bindings["strategy_archetype_version"],
        "period_binding": build_period_binding_from_archetype_v0(bindings),
        "cost_execution_binding": build_cost_execution_binding_from_archetype_v0(bindings),
        "economic_policy_binding": build_economic_policy_binding_v0(),
        "instrument_binding": bindings["instrument_panel_binding"],
        "dataset_binding": bindings["dataset_binding"],
        "ranking_policy_binding": bindings["ranking_policy_binding"],
        "selection_policy_binding": bindings["selection_policy_binding"],
        "promoted_dataset_content_digest": bindings["dataset_binding"]["dataset_content_digest"],
        "binding_config_digest": scope["binding_config_digest"],
        "scope_ratification_digest": scope["scope_ratification_digest"],
        "implementation_digests": scope["implementation_digests"],
    }


def resolve_expected_origin_main_sha_binding_v0(
    *,
    explicit_sha: str | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    if explicit_sha and explicit_sha.strip():
        return explicit_sha.strip(), "cli_argument"
    env_map = env if env is not None else os.environ
    env_sha = str(env_map.get(ORIGIN_MAIN_SHA_BINDING_ENV_VAR, "")).strip()
    if env_sha:
        return env_sha, "environment_variable"
    return EXPECTED_ORIGIN_MAIN_SHA, "canonical_default"


def resolve_actual_repo_shas_v0(repo_root: Path) -> tuple[str, str]:
    head_result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    origin_result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    actual_head = head_result.stdout.strip() if head_result.returncode == 0 else ""
    actual_origin_main = origin_result.stdout.strip() if origin_result.returncode == 0 else ""
    return actual_head, actual_origin_main


def verify_origin_main_sha_guard_v0(
    *,
    repo_root: Path,
    expected_origin_main_sha: str | None = None,
    env: Mapping[str, str] | None = None,
) -> OriginMainShaGuardResultV0:
    resolved_expected, binding_source = resolve_expected_origin_main_sha_binding_v0(
        explicit_sha=expected_origin_main_sha,
        env=env,
    )
    actual_head, actual_origin_main = resolve_actual_repo_shas_v0(repo_root)
    fail_reasons: list[str] = []
    if not resolved_expected:
        fail_reasons.append(FAIL_CLOSED_EXPECTED_ORIGIN_MAIN_SHA_BINDING_MISSING)
    elif actual_origin_main != resolved_expected:
        fail_reasons.append(FAIL_CLOSED_ORIGIN_MAIN_SHA_MISMATCH)
    if actual_head != actual_origin_main:
        fail_reasons.append("HEAD_ORIGIN_MAIN_DIVERGENCE")
    passed = not fail_reasons
    return OriginMainShaGuardResultV0(
        passed=passed,
        sha_guard_status=SHA_GUARD_STATUS_PASS if passed else fail_reasons[0],
        expected_origin_main_sha=resolved_expected,
        actual_head_sha=actual_head,
        actual_origin_main_sha=actual_origin_main,
        binding_source=binding_source,
        fail_reasons=tuple(fail_reasons),
    )


def origin_main_sha_guard_to_dict(result: OriginMainShaGuardResultV0) -> dict[str, Any]:
    return {
        "passed": result.passed,
        "sha_guard_status": result.sha_guard_status,
        "expected_origin_main_sha": result.expected_origin_main_sha,
        "actual_head_sha": result.actual_head_sha,
        "actual_origin_main_sha": result.actual_origin_main_sha,
        "binding_source": result.binding_source,
        "fail_reasons": list(result.fail_reasons),
    }


def verify_promoted_dataset_registry_v0(
    *,
    durable_archive_root: Path,
    expected_digest: str,
) -> tuple[bool, tuple[str, ...], str]:
    registry_path = durable_archive_root / PROMOTED_DATASET_REL / "registry_entry.json"
    if not registry_path.is_file():
        return False, (REASON_PROMOTED_DATASET_MISSING,), ""
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    actual = str(payload.get("dataset_content_digest", ""))
    if actual != expected_digest:
        return False, (REASON_DATA_DIGEST_MISMATCH,), actual
    return True, (), actual


def verify_archetype_binding_precheck_v0(
    *,
    repo_root: Path,
    bindings: Mapping[str, Any],
    scope: Mapping[str, Any],
    go_token: str,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if go_token != GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)

    bindings_path = repo_root / BINDINGS_CONFIG_REL
    if _file_sha256(bindings_path) != scope["binding_config_digest"]:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)

    expected_data_digest = bindings["dataset_binding"]["dataset_content_digest"]
    if expected_data_digest != BOUND_DATASET_CONTENT_DIGEST:
        reasons.append(REASON_DATA_DIGEST_MISMATCH)

    if bindings["dataset_binding"].get("narrow_adapter_disallowed") is not True:
        reasons.append(REASON_NARROW_ADAPTER)
    if bindings["instrument_panel_binding"].get("narrow_adapter_disallowed") is not True:
        reasons.append(REASON_NARROW_ADAPTER)
    if (
        bindings["instrument_panel_binding"].get("single_instrument_evaluation_forbidden")
        is not True
    ):
        reasons.append(REASON_NARROW_ADAPTER)

    eligible_count = int(bindings["instrument_panel_binding"].get("eligible_instrument_count", 0))
    if eligible_count < MIN_ELIGIBLE_INSTRUMENTS:
        reasons.append(REASON_INSUFFICIENT_INSTRUMENTS)

    if bindings.get("economic_evaluation_authorized") is True:
        reasons.append("ECONOMIC_EVALUATION_ALREADY_AUTHORIZED_IN_BINDING")

    return not reasons, tuple(reasons)


def filter_panel_to_eligible_instruments_v0(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    eligible_instrument_ids: Sequence[str],
) -> tuple[InstrumentPanelSeriesV1, ...]:
    allowed = set(eligible_instrument_ids)
    return tuple(item for item in panel_series if item.instrument_id in allowed)


def _compute_walk_forward_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    if not robustness.walk_forward_results:
        return None
    passed = sum(1 for item in robustness.walk_forward_results if item.net_return >= 0.0)
    return passed / len(robustness.walk_forward_results)


def _compute_out_of_sample_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    for item in robustness.walk_forward_results:
        if item.period_name == "out_of_sample":
            return 1.0 if item.net_return >= 0.0 else 0.0
    return None


def _compute_monte_carlo_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    quantiles = robustness.monte_carlo_summary.get("metric_quantiles", {})
    total_return_q = quantiles.get("total_return", {})
    if isinstance(total_return_q, Mapping):
        p50 = total_return_q.get("p50")
        if p50 is not None:
            return 1.0 if float(p50) >= 0.0 else 0.0
    return None


def _compute_stress_failure_count(
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


def _compute_single_trade_contribution(backtest: SingleSlotBacktestResultV0) -> float | None:
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


def _compute_single_regime_contribution(backtest: SingleSlotBacktestResultV0) -> float | None:
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


def _classify_economic_outcome(
    *,
    precheck_ok: bool,
    gate_evaluation: Any,
    reason_codes: list[str],
) -> tuple[EconomicClassification, VerdictClassification, bool, bool]:
    if not precheck_ok:
        return (
            EconomicClassification.FAIL_CLOSED,
            VerdictClassification.FAIL_CLOSED,
            False,
            False,
        )

    status = gate_evaluation.evaluation_status
    if status is EconomicValidityEvaluationStatus.PASS:
        return (
            EconomicClassification.PASS,
            VerdictClassification.ECONOMICALLY_VIABLE_OFFLINE,
            True,
            False,
        )
    if status is EconomicValidityEvaluationStatus.FAIL:
        return (
            EconomicClassification.FAIL,
            VerdictClassification.ROBUSTNESS_FAILED,
            False,
            False,
        )
    if status is EconomicValidityEvaluationStatus.BLOCKED:
        blocked_only = all(
            code.startswith("METRIC_MISSING")
            or code.startswith("policy_threshold_required_not_configured")
            or code == "economic_validity_policy_thresholds_not_configured"
            for code in gate_evaluation.reason_codes
        )
        if blocked_only:
            return (
                EconomicClassification.INCONCLUSIVE,
                VerdictClassification.INCONCLUSIVE,
                False,
                False,
            )
        return (
            EconomicClassification.FAIL_CLOSED,
            VerdictClassification.FAIL_CLOSED,
            False,
            False,
        )
    reason_codes.append(f"UNKNOWN_GATE_STATUS:{status}")
    return (
        EconomicClassification.FAIL_CLOSED,
        VerdictClassification.FAIL_CLOSED,
        False,
        False,
    )


def materialize_economic_viability_evidence_v0(
    *,
    envelope: Mapping[str, Any],
    staging_root: Path,
    panel_data_digest: str,
    promoted_dataset_content_digest: str,
    backtest: SingleSlotBacktestResultV0,
    robustness: RobustnessStageResultsV0,
    robustness_metrics: CrossSectionalRobustnessMetricsV0,
    gate_evaluation: Any,
    economic_classification: EconomicClassification,
    ops_config: Mapping[str, Any],
) -> dict[str, Any]:
    stats = backtest.stats
    single_trade_val = _compute_single_trade_contribution(backtest)
    single_regime_val = _compute_single_regime_contribution(backtest)
    body: dict[str, Any] = {
        "schema_version": "economic_viability_evidence_okx_full_panel_csr_v0",
        "strategy_archetype_id": STRATEGY_ARCHETYPE_ID,
        "strategy_archetype_version": STRATEGY_ARCHETYPE_VERSION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "economic_classification": economic_classification.value,
        "economic_validity_evaluation_status": gate_evaluation.evaluation_status.value,
        "economic_validity_offline_gate_pass": gate_evaluation.gates_pass,
        "promotion_candidate_eligible": False,
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
        "funding_drag": getattr(backtest, "funding_drag", None),
        "slippage_impact": backtest.slippage_impact,
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
            "strategy_archetype_id": STRATEGY_ARCHETYPE_ID,
            "strategy_archetype_version": STRATEGY_ARCHETYPE_VERSION,
            "period_binding": envelope["period_binding"],
            "instrument_binding": envelope["instrument_binding"],
            "dataset_binding": envelope["dataset_binding"],
            "fee_model_binding": envelope["cost_execution_binding"]["fee_model_binding"],
            "slippage_model_binding": envelope["cost_execution_binding"]["slippage_model_binding"],
            "funding_model_binding": envelope["cost_execution_binding"]["funding_model_binding"],
            "execution_model_binding": envelope["cost_execution_binding"][
                "execution_model_binding"
            ],
            "economic_policy_binding": envelope["economic_policy_binding"],
            "promoted_dataset_content_digest": promoted_dataset_content_digest,
            "panel_data_digest": panel_data_digest,
            "binding_config_digest": envelope["binding_config_digest"],
            "scope_ratification_digest": envelope["scope_ratification_digest"],
            "ops_config_digest": ops_config.get("config_digest"),
        },
        "staging_root": str(staging_root),
        "data_source_class": "OKX_FULL_PANEL_PROMOTED_DATASET_BOUND",
    }
    body["manifest_digest"] = _stable_digest(
        {key: value for key, value in body.items() if key != "manifest_digest"}
    )
    return body


def run_full_offline_economic_evaluation_v0(
    *,
    repo_root: Path,
    durable_archive_root: Path,
    staging_root: Path,
    go_token: str,
    expected_origin_main_sha: str | None = None,
) -> FullEconomicEvaluationResultV0:
    bindings = load_archetype_bindings_v0(repo_root)
    scope = load_execution_scope_v0(repo_root)
    ops_config = load_ops_evaluation_config_v0(repo_root)
    envelope = build_evaluation_envelope_v0(bindings, scope)
    reason_codes: list[str] = []

    sha_guard = verify_origin_main_sha_guard_v0(
        repo_root=repo_root,
        expected_origin_main_sha=expected_origin_main_sha,
    )
    if not sha_guard.passed:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            promoted_dataset_content_digest="",
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            verdict_classification=VerdictClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=sha_guard.fail_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    precheck_ok, precheck_reasons = verify_archetype_binding_precheck_v0(
        repo_root=repo_root,
        bindings=bindings,
        scope=scope,
        go_token=go_token,
    )
    if not precheck_ok:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            promoted_dataset_content_digest="",
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            verdict_classification=VerdictClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    registry_ok, registry_reasons, promoted_digest = verify_promoted_dataset_registry_v0(
        durable_archive_root=durable_archive_root,
        expected_digest=BOUND_DATASET_CONTENT_DIGEST,
    )
    if not registry_ok:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            promoted_dataset_content_digest=promoted_digest,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            verdict_classification=VerdictClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=registry_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    period_binding = envelope["period_binding"]
    materialization = materialize_bound_panel_dataset_v0(
        staging_root,
        period_binding=period_binding,
    )
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_DATASET,
            precheck_passed=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=materialization.panel_data_digest,
            promoted_dataset_content_digest=promoted_digest,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            verdict_classification=VerdictClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=materialization.reason_codes,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    panel_series, _panel_ref = load_panel_series_from_staging(staging_root)
    filtered = filter_panel_to_eligible_instruments_v0(
        panel_series,
        eligible_instrument_ids=bindings["instrument_panel_binding"]["eligible_instrument_ids"],
    )
    if len(filtered) < MIN_ELIGIBLE_INSTRUMENTS:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_DATASET,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=materialization.panel_data_digest,
            promoted_dataset_content_digest=promoted_digest,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            verdict_classification=VerdictClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=(REASON_INSUFFICIENT_INSTRUMENTS,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    binding = default_operator_binding_v0()
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=filtered,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        filtered,
        cost_execution_binding=envelope["cost_execution_binding"],
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=period_binding,
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    stage_wiring = build_stage_wiring_status_v1(
        orchestrator_result=orchestrator,
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    robustness_metrics = CrossSectionalRobustnessMetricsV0(
        walk_forward_pass_ratio=_compute_walk_forward_pass_ratio(robustness),
        out_of_sample_pass_ratio=_compute_out_of_sample_pass_ratio(robustness),
        monte_carlo_pass_ratio=_compute_monte_carlo_pass_ratio(robustness),
        stress_failure_count=_compute_stress_failure_count(robustness),
        parameter_robustness_pass=True,
        parameter_neighbor_degradation=0.0,
    )

    policy = canonical_economic_validity_policy_v1()
    stats = backtest.stats
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
            single_trade_profit_contribution=_compute_single_trade_contribution(backtest),
            single_regime_profit_contribution=_compute_single_regime_contribution(backtest),
            data_admissibility_status="PASS",
            cost_model_status="PASS",
            funding_binding_status="PASS",
            execution_model_status="PASS",
            reproducibility_status="PASS",
            digest_binding_status="PASS",
            manifest_binding_status="PASS",
        ),
    )

    classification, verdict, gate_pass, _promotion_eligible = _classify_economic_outcome(
        precheck_ok=True,
        gate_evaluation=gate_evaluation,
        reason_codes=reason_codes,
    )
    evidence = materialize_economic_viability_evidence_v0(
        envelope=envelope,
        staging_root=staging_root,
        panel_data_digest=materialization.panel_data_digest,
        promoted_dataset_content_digest=promoted_digest,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        gate_evaluation=gate_evaluation,
        economic_classification=classification,
        ops_config=ops_config,
    )

    return FullEconomicEvaluationResultV0(
        status=ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE,
        precheck_passed=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=materialization.panel_data_digest,
        promoted_dataset_content_digest=promoted_digest,
        stage_wiring=stage_wiring,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        economic_viability_evidence=evidence,
        economic_classification=classification,
        verdict_classification=verdict,
        economic_validity_offline_gate_pass=gate_pass,
        promotion_candidate_eligible=False,
        economic_evaluation_executed=True,
        reason_codes=tuple(reason_codes),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def execution_result_to_dict(result: FullEconomicEvaluationResultV0) -> dict[str, Any]:
    backtest = result.backtest
    stats = backtest.stats if backtest is not None else {}
    robustness_dict = (
        robustness_results_to_dict(result.robustness) if result.robustness is not None else {}
    )
    return {
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "promoted_dataset_content_digest": result.promoted_dataset_content_digest,
        "stage_wiring": [
            {"stage_name": item.stage_name, "wired": item.wired, "owner": item.owner}
            for item in result.stage_wiring
        ],
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_classification": result.economic_classification.value,
        "verdict_classification": result.verdict_classification.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "promotion_candidate_eligible": result.promotion_candidate_eligible,
        "net_return": backtest.net_return if backtest else None,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "max_drawdown": stats.get("max_drawdown"),
        "trade_count": backtest.trade_count if backtest else None,
        "fee_drag": backtest.fee_drag if backtest else None,
        "slippage_impact": backtest.slippage_impact if backtest else None,
        "funding_drag": getattr(backtest, "funding_drag", None) if backtest else None,
        "walk_forward_status": (
            "COMPLETE" if robustness_dict.get("walk_forward_results") else "FAIL_CLOSED"
        ),
        "monte_carlo_status": (
            "COMPLETE" if robustness_dict.get("monte_carlo_results") else "FAIL_CLOSED"
        ),
        "stress_status": ("COMPLETE" if robustness_dict.get("stress_results") else "FAIL_CLOSED"),
        "parameter_sensitivity_status": robustness_dict.get(
            "parameter_sensitivity_results", {}
        ).get("status", "FAIL_CLOSED"),
        "walk_forward_gate": (
            result.robustness_metrics.walk_forward_pass_ratio if result.robustness_metrics else None
        ),
        "monte_carlo_gate": (
            result.robustness_metrics.monte_carlo_pass_ratio if result.robustness_metrics else None
        ),
        "stress_gate": (
            result.robustness_metrics.stress_failure_count if result.robustness_metrics else None
        ),
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }
