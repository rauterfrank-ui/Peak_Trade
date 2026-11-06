"""Measured local research observations for the existing Phase10 contract.

No fixture producer, parameter aliasing, new metric policy or network/data loader.
Source-code bytes are read for explicit provenance binding.
Engine equity and actual funding cashflows remain distinct evidence surfaces.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

import pandas as pd

from src.backtest.cost_config_v0 import resolve_effective_backtest_cost_config
from src.backtest.mv2_research_wiring_v1 import (
    run_mv2_research_backtest_wiring_v1,
    _ensure_supported_instrument,
    STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
)
from src.backtest.parameter_sensitivity_v1 import split_bars_train_validation_oos_v1
from src.backtest.stats import compute_backtest_stats
from src.experiments.canonical_automated_offline_research_loop_v1 import (
    OfflineExperimentObservationsV1,
    CanonicalAutomatedOfflineResearchLoopRequestV1,
    ResearchHypothesisCandidateV1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    domain_separated_digest,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_comparison_ssot_v1 import (
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
)
from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


class NativeResearchMeasurementError(ValueError):
    """Inputs cannot support an identified local measurement."""


@dataclass(frozen=True)
class NativeResearchMeasurementsV1:
    observations: OfflineExperimentObservationsV1
    receipt: Mapping[str, Any]


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return deepcopy(value)


def native_research_identity_sources_v1(
    cfg: Mapping[str, Any],
    *,
    instrument_id: str,
    bars: pd.DataFrame,
    instrument_admission_mode: str = STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
) -> Mapping[str, str]:
    """Source-specific raw bindings; Phase1 owns their canonical digest domains.

    Model binding describes configured inputs, not proof of applied funding cash.
    Core/feature provenance is not authenticated by these source bindings.
    """
    _ensure_supported_instrument(instrument_id, admission_mode=instrument_admission_mode)
    config = _plain(cfg)
    risk = config.get("risk")
    initial = config.get("backtest", {}).get("initial_cash")
    if not isinstance(risk, Mapping) or not {
        "risk_per_trade",
        "max_position_size",
        "min_position_value",
        "min_stop_distance",
    } <= set(risk):
        raise NativeResearchMeasurementError("EXPLICIT_RISK_INPUTS_REQUIRED")
    if (
        isinstance(initial, bool)
        or not isinstance(initial, (int, float))
        or not math.isfinite(initial)
        or initial <= 0
    ):
        raise NativeResearchMeasurementError("EXPLICIT_INITIAL_EQUITY_REQUIRED")
    cost = resolve_effective_backtest_cost_config(config)
    root = Path(__file__).resolve().parents[2]
    implementation = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in (
            "src/backtest/cost_config_v0.py",
            "src/backtest/backtest_engine_position_feedback_adapter_v1.py",
            "src/backtest/engine.py",
            "src/experiments/canonical_native_research_measurements_v1.py",
        )
    }
    split_frames = split_bars_train_validation_oos_v1(bars)
    if any(frame.empty for frame in split_frames):
        raise NativeResearchMeasurementError("NONEMPTY_SPLIT_FRAMES_REQUIRED")
    split_binding = {
        "owner": "src.backtest.parameter_sensitivity_v1.split_bars_train_validation_oos_v1",
        "implementation_sha256": hashlib.sha256(
            (root / "src/backtest/parameter_sensitivity_v1.py").read_bytes()
        ).hexdigest(),
        "frames": [
            {
                "name": name,
                "rows": len(frame),
                "start": str(frame.index[0]),
                "end": str(frame.index[-1]),
            }
            for name, frame in zip(("train", "validation", "holdout"), split_frames)
        ],
    }
    payloads = {
        "split_policy_digest": split_binding,
        "fee_model_digest": {
            "model": cost.fee_model_version,
            "maker_fee_bps": cost.maker_fee_bps,
            "taker_fee_bps": cost.taker_fee_bps,
        },
        "slippage_model_digest": {
            "model": cost.slippage_model_version,
            "entry_slippage_bps": cost.entry_slippage_bps,
            "exit_slippage_bps": cost.exit_slippage_bps,
            "spread_model": cost.spread_model_version,
            "spread_policy": cost.spread_application_policy,
            "execution_model": cost.execution_model_version,
            "research_execution_cost": config.get("backtest", {}).get(
                "economic_research_execution_cost"
            ),
        },
        "funding_model_digest": {
            "model": cost.funding_model_version,
            "rate_source": cost.funding_rate_source,
            "application_policy": cost.funding_application_policy,
            "declared_config": config.get("backtest", {}).get("funding"),
            "engine_cashflow_application": "NOT_AUTHENTICATED_BY_MODEL_BINDING",
        },
        "risk_policy_digest": {
            "risk": risk,
            "offline_sizing_contract": config.get("offline_evaluation_sizing_contract_v1"),
        },
        "portfolio_digest": {
            "scope": "SINGLE_INSTRUMENT_RESEARCH",
            "instrument_id": instrument_id,
            "initial_cash": initial,
        },
    }
    if instrument_admission_mode != STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0:
        payloads["portfolio_digest"]["instrument_admission_mode"] = instrument_admission_mode
    return MappingProxyType(
        {
            field: compute_content_sha256(
                {
                    "schema_version": "native_research_identity_sources_v1",
                    "source_field": field,
                    "payload": payload,
                    "implementation_sha256": implementation,
                }
            )
            for field, payload in payloads.items()
        }
    )


def native_research_input_hashes_v1(
    bars: pd.DataFrame, cfg: Mapping[str, Any]
) -> Mapping[str, str]:
    """Declared source bytes, before Phase1's separate digest domains."""
    dataset = bars.to_csv(float_format="%.17g").encode("utf-8")
    config = json.dumps(_plain(cfg), sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )
    return MappingProxyType(
        {
            "dataset_sha256": hashlib.sha256(dataset).hexdigest(),
            "config_sha256": hashlib.sha256(config).hexdigest(),
        }
    )


def measure_native_research_candidate_v1(
    *,
    candidate: Mapping[str, Any],
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
    strategy_id: str,
    strategy_version: str,
    expected_dataset_sha256: str,
    expected_config_sha256: str,
    instrument_id: str,
    instrument_admission_mode: str = STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
) -> NativeResearchMeasurementsV1:
    """Run full path and3 chronological splits; supply actual returns to Phase4.

    Caller supplies fully resolved config; this owner changes no parameter or
    policy. Dataset and parameter bindings are verified before invoking engines.
    This does not establish that arbitrary caller cost/core provenance is true.
    """
    if not isinstance(bars.index, pd.DatetimeIndex) or bars.empty:
        raise NativeResearchMeasurementError("NONEMPTY_DATETIME_BARS_REQUIRED")
    if (
        bars.index.tz is None
        or bars.index.hasnans
        or not bars.index.is_unique
        or not bars.index.is_monotonic_increasing
    ):
        raise NativeResearchMeasurementError("ORDERED_UNIQUE_TIMEZONE_BOUND_BARS_REQUIRED")
    local_bars, local_cfg = bars.copy(deep=True), _plain(cfg)
    hashes = native_research_input_hashes_v1(local_bars, local_cfg)
    if dict(hashes) != {
        "dataset_sha256": expected_dataset_sha256,
        "config_sha256": expected_config_sha256,
    }:
        raise NativeResearchMeasurementError("INPUT_BYTE_BINDING_MISMATCH")
    identity = candidate["experiment_identity"]
    validate_canonical_experiment_identity_v1(identity)
    if candidate.get("status") != "PROPOSED" or candidate.get(
        "experiment_id"
    ) != derive_experiment_id_v1(identity["identity_digest"]):
        raise NativeResearchMeasurementError("IDENTIFIED_PROPOSED_CANDIDATE_REQUIRED")
    if identity["dataset_digest"] != domain_separated_digest(
        "dataset", {"source_digest": expected_dataset_sha256}
    ):
        raise NativeResearchMeasurementError("CANONICAL_DATASET_DOMAIN_MISMATCH")
    params = local_cfg.get("economic_evaluation_v1", {}).get("strategy_params")
    if not isinstance(params, Mapping) or identity[
        "strategy_params_digest"
    ] != domain_separated_digest("strategy_params", params):
        raise NativeResearchMeasurementError("CANONICAL_PARAMETER_DOMAIN_MISMATCH")
    if any(params.get(key) != value for key, value in candidate["parameter_region"].items()):
        raise NativeResearchMeasurementError("PARAMETER_REGION_MISMATCH")
    if identity["strategy_identity"] != f"{strategy_id}.{strategy_version}":
        raise NativeResearchMeasurementError("EXPLICIT_STRATEGY_IDENTITY_MISMATCH")
    identity_sources = native_research_identity_sources_v1(
        local_cfg,
        instrument_id=instrument_id,
        bars=local_bars,
        instrument_admission_mode=instrument_admission_mode,
    )
    for field, raw_digest in identity_sources.items():
        domain = field.removesuffix("_digest")
        if identity[field] != domain_separated_digest(domain, {"source_digest": raw_digest}):
            raise NativeResearchMeasurementError(f"CANONICAL_CONFIG_SOURCE_MISMATCH:{field}")
    expected_cost = resolve_effective_backtest_cost_config(local_cfg)
    raw_stats: dict[str, Mapping[str, float]] = {}
    runs = []
    full_returns = None
    splits = split_bars_train_validation_oos_v1(local_bars)
    for name, frame in zip(("full", "train", "validation", "holdout"), (local_bars, *splits)):
        wiring = run_mv2_research_backtest_wiring_v1(
            frame.copy(deep=True),
            strategy_id=strategy_id,
            cfg=deepcopy(local_cfg),
            instrument_id=instrument_id,
            step29l_instrument_admission_mode=instrument_admission_mode,
        )
        if wiring.effective_cost_config.config_digest != expected_cost.config_digest:
            raise NativeResearchMeasurementError("EXECUTED_COST_CONFIG_MISMATCH")
        provenance = wiring.strategy_signal_provenance.to_dict()
        if provenance["configured_strategy_params"] != dict(params) or provenance[
            "effective_strategy_params"
        ] != dict(params):
            raise NativeResearchMeasurementError("EXECUTED_PARAMETERS_DIFFER_FROM_IDENTITY")
        if provenance["strategy_version"] != strategy_version:
            raise NativeResearchMeasurementError("EXECUTED_STRATEGY_VERSION_MISMATCH")
        equity = wiring.backtest_result.equity_curve
        if not equity.map(lambda x: math.isfinite(float(x)) and float(x) > 0).all():
            raise NativeResearchMeasurementError("FINITE_POSITIVE_EQUITY_REQUIRED")
        returns = equity.pct_change().dropna()
        if len(returns) < 2 or not returns.map(lambda x: math.isfinite(float(x))).all():
            raise NativeResearchMeasurementError("FINITE_MEASURED_RETURNS_REQUIRED")
        trades = wiring.backtest_result.trades
        stats = compute_backtest_stats(
            trades=[] if trades is None else trades.to_dict(orient="records"),
            equity_curve=equity,
            periods_per_year=1,
        )
        if not math.isfinite(stats["sharpe"]):
            raise NativeResearchMeasurementError("NONFINITE_NONANNUAL_SHARPE")
        raw_stats[name] = stats
        if name == "full":
            full_returns = [float(x) for x in returns]
        runs.append(
            {
                "split": name,
                "period_start": str(frame.index[0]),
                "period_end": str(frame.index[-1]),
                "return_observations": len(returns),
                "equity": [
                    {"timestamp": str(ts), "value": float(value)} for ts, value in equity.items()
                ],
                "mapped_signal_values": [int(value) for value in wiring.signals],
                "closed_trade_quantities": []
                if trades is None or trades.empty
                else [float(value) for value in trades["size"]],
                "closed_trade_intervals": []
                if trades is None or trades.empty
                else [
                    {
                        "entry_time": str(row["entry_time"]),
                        "exit_time": str(row["exit_time"]),
                        "quantity": float(row["size"]),
                    }
                    for row in trades.to_dict(orient="records")
                ],
                "strategy_provenance": provenance,
                "engine_signal_digest": wiring.backtest_engine_signal_digest,
                "mv2_signal_digest": wiring.mv2_replay_signal_digest,
                "cost_binding": wiring.effective_cost_config.to_dict(),
                "statistics": {
                    key: {"status": "COMPUTED", "value": value}
                    if math.isfinite(value)
                    else {"status": "NONFINITE", "value": None}
                    for key, value in stats.items()
                },
            }
        )
    # Match the target's explicitly nonannual Sharpe convention; do not invent
    # turnover, parameter stability, cost sensitivity or later outcomes.
    metrics = {
        "engine_pre_funding_sharpe": raw_stats["full"]["sharpe"],
        "engine_pre_funding_oos_sharpe": raw_stats["holdout"]["sharpe"],
    }
    split_metrics = {
        row["split"]: {
            "sharpe": raw_stats[row["split"]]["sharpe"],
            "sample_size": row["return_observations"],
        }
        for row in runs
        if row["split"] != "full"
    }
    observations = OfflineExperimentObservationsV1(
        metrics=metrics,
        robustness_results={},
        regime_results={},
        artifacts=(),
        robustness_observations={"returns": full_returns, "split_metrics": split_metrics},
    )
    body = {
        "schema_version": "canonical_native_research_measurements_v1",
        "experiment_id": candidate["experiment_id"],
        "identity_digest": identity["identity_digest"],
        "source_hashes": dict(hashes),
        "verified_identity_source_fields": dict(identity_sources),
        "parameters": dict(params),
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "instrument_id": instrument_id,
        "instrument_admission_mode": instrument_admission_mode,
        "engine_invocations": 4,
        "returns_basis": "FULL_ENGINE_EQUITY_NOT_CONCATENATED_RESET_SPLITS",
        "sharpe_convention": "MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION",
        "funding_effect_in_equity": "NOT_ESTABLISHED_BY_SIGNAL_OR_MODEL_BINDING",
        "funding_unit_signal_is_actual_quantity": False,
        "source_authenticated": False,
        "unverified_identity_provenance": [
            "git_sha",
            "feature_pipeline_digest",
            "canonical_trading_core_bindings",
        ],
        "productive_apply_authorized": False,
        "runs": runs,
    }
    body["content_digest"] = compute_content_sha256(body)
    return NativeResearchMeasurementsV1(observations, MappingProxyType(body))


@dataclass(frozen=True)
class NativeResearchExecutionContextV1:
    """Explicit existing-owner context; unavailable Shadow/gap truth is not invented."""

    identity_template: CanonicalExperimentIdentityRequestV1
    champion: ComparisonCandidateV1
    champion_measurements: NativeResearchMeasurementsV1
    created_at: str
    time_horizon: Mapping[str, str]
    market_universe: Sequence[str]
    gap_dimensions: Sequence[RealityGapDimensionV1]
    observed_surface: str
    threshold_policy_digest: str
    robustness_policy: Mapping[str, Any]
    parent_experiment: str | None = None
    existing_failure_records: Sequence[Mapping[str, Any]] = ()
    retest_reason: str | None = None
    experiment_memory_store: CanonicalExperimentMemoryStoreV1 | None = None
    failure_memory_store: CanonicalFailureMemoryStoreV1 | None = None
    reality_gap_store: CanonicalRealityGapStoreV1 | None = None
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None
    instrument_admission_mode: str = STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0


@dataclass(frozen=True)
class NativeResearchExperimentProviderV1:
    """Caller-owned actual experiment provider for the existing execution bridge.

    Resolve the explicitly requested native region, measure it and build the
    existing Phase10 request. Both comparison scores come from measured full
    engine equity, never a fixture score or a promoted candidate ranking.
    """

    bars: pd.DataFrame
    base_cfg: Mapping[str, Any]
    strategy_id: str
    strategy_version: str
    instrument_id: str
    context: NativeResearchExecutionContextV1
    measurement_observer: Callable[[NativeResearchMeasurementsV1], None] | None = None

    def __call__(
        self, candidate: Mapping[str, Any]
    ) -> CanonicalAutomatedOfflineResearchLoopRequestV1:
        from src.experiments.canonical_failure_memory_v1 import derive_hypothesis_fingerprint_v1
        from src.experiments.canonical_robustness_suite_v1 import derive_robustness_policy_digest_v1

        ctx = self.context
        champion_receipt = _plain(ctx.champion_measurements.receipt)
        if (
            champion_receipt.get(
                "instrument_admission_mode",
                STEP29L_INSTRUMENT_ADMISSION_LEGACY_RESEARCH_SINGLETON_V0,
            )
            != ctx.instrument_admission_mode
            or champion_receipt.get("instrument_id") != self.instrument_id
        ):
            raise NativeResearchMeasurementError("CHAMPION_INSTRUMENT_ADMISSION_MISMATCH")
        expected_digest = compute_content_sha256(
            {key: value for key, value in champion_receipt.items() if key != "content_digest"}
        )
        if champion_receipt.get("content_digest") != expected_digest:
            raise NativeResearchMeasurementError("CHAMPION_MEASUREMENT_DIGEST_MISMATCH")
        if (
            champion_receipt["identity_digest"]
            != ctx.champion.experiment_identity["identity_digest"]
        ):
            raise NativeResearchMeasurementError("CHAMPION_MEASUREMENT_IDENTITY_MISMATCH")
        if champion_receipt["experiment_id"] != derive_experiment_id_v1(
            ctx.champion.experiment_identity["identity_digest"]
        ):
            raise NativeResearchMeasurementError("CHAMPION_EXPERIMENT_ID_MISMATCH")
        if not ctx.gap_dimensions:
            raise NativeResearchMeasurementError("EXPLICIT_REALITY_GAP_CONTEXT_REQUIRED")
        if not isinstance(ctx.time_horizon, Mapping) or set(ctx.time_horizon) != {"start", "end"}:
            raise NativeResearchMeasurementError("EXPLICIT_BAR_INDEX_HORIZON_REQUIRED")
        if (
            pd.Timestamp(ctx.time_horizon["start"]) != self.bars.index[0]
            or pd.Timestamp(ctx.time_horizon["end"]) != self.bars.index[-1]
        ):
            raise NativeResearchMeasurementError("HORIZON_DOES_NOT_BIND_BAR_INDEX_SPAN")
        if dict(ctx.champion.time_horizon or {}) != dict(ctx.time_horizon) or tuple(
            ctx.champion.market_universe or ()
        ) != tuple(ctx.market_universe):
            raise NativeResearchMeasurementError("CHAMPION_MEASUREMENT_CONTEXT_MISMATCH")
        base_params = self.base_cfg.get("economic_evaluation_v1", {}).get("strategy_params")
        if not isinstance(base_params, Mapping) or dict(base_params) != dict(
            ctx.identity_template.strategy_params
        ):
            raise NativeResearchMeasurementError("BASE_TEMPLATE_CONFIG_PARAMETER_MISMATCH")
        params = {
            **dict(ctx.identity_template.strategy_params),
            **dict(candidate["parameter_region"]),
        }
        request_identity = replace(ctx.identity_template, strategy_params=params)
        identity = build_canonical_experiment_identity_v1(request_identity)
        if _plain(identity) != _plain(candidate["experiment_identity"]):
            raise NativeResearchMeasurementError("CANDIDATE_TEMPLATE_IDENTITY_MISMATCH")
        policy_snapshot = _plain(ctx.robustness_policy)
        policy_digest = derive_robustness_policy_digest_v1(policy_snapshot)
        fingerprint = derive_hypothesis_fingerprint_v1(
            identity_digest=identity["identity_digest"],
            hypothesis_id=candidate["hypothesis_id"],
            parameter_region=candidate["parameter_region"],
            regime=candidate["offline_experiment_request"]["regime"],
            robustness_policy_digest=policy_digest,
            parent_lineage_ref=identity["parent_lineage"]["parent_lineage_ref"],
        )
        if fingerprint != candidate["hypothesis_fingerprint"]:
            raise NativeResearchMeasurementError("SEARCH_RESEARCH_POLICY_FINGERPRINT_MISMATCH")
        cfg = _plain(self.base_cfg)
        cfg["economic_evaluation_v1"]["strategy_params"] = params
        hashes = native_research_input_hashes_v1(self.bars, cfg)
        measured = measure_native_research_candidate_v1(
            candidate=candidate,
            bars=self.bars,
            cfg=cfg,
            strategy_id=self.strategy_id,
            strategy_version=self.strategy_version,
            expected_dataset_sha256=hashes["dataset_sha256"],
            expected_config_sha256=hashes["config_sha256"],
            instrument_id=self.instrument_id,
            instrument_admission_mode=ctx.instrument_admission_mode,
        )
        full = next(row for row in champion_receipt["runs"] if row["split"] == "full")
        if full["statistics"]["sharpe"]["status"] != "COMPUTED":
            raise NativeResearchMeasurementError("MEASURED_CHAMPION_SCORE_REQUIRED")
        if self.measurement_observer is not None:
            # Observation must not become a write port into metrics or decisions.
            observed = measured.observations
            snapshot = NativeResearchMeasurementsV1(
                replace(
                    observed,
                    metrics=_plain(observed.metrics),
                    robustness_results=_plain(observed.robustness_results),
                    regime_results=_plain(observed.regime_results),
                    artifacts=_plain(observed.artifacts),
                    robustness_observations=_plain(observed.robustness_observations),
                    robustness_policy=_plain(observed.robustness_policy),
                ),
                MappingProxyType(_plain(measured.receipt)),
            )
            self.measurement_observer(snapshot)
        hypothesis = ResearchHypothesisCandidateV1(
            hypothesis_id=candidate["hypothesis_id"],
            identity_request=request_identity,
            parameter_region=candidate["parameter_region"],
            regime=candidate["offline_experiment_request"]["regime"],
            candidate_ref=candidate["candidate_ref"],
            strategy_family=candidate["strategy_family"],
            time_horizon=dict(ctx.time_horizon),
            market_universe=tuple(ctx.market_universe),
        )
        return CanonicalAutomatedOfflineResearchLoopRequestV1(
            hypotheses=(hypothesis,),
            selected_hypothesis_id=hypothesis.hypothesis_id,
            created_at=ctx.created_at,
            experiment_observations=replace(
                measured.observations, robustness_policy=policy_snapshot
            ),
            champion=ctx.champion,
            champion_score=full["statistics"]["sharpe"]["value"],
            challenger_score=measured.observations.metrics["engine_pre_funding_sharpe"],
            gap_dimensions=tuple(ctx.gap_dimensions),
            observed_surface=ctx.observed_surface,
            threshold_policy_digest=ctx.threshold_policy_digest,
            parent_experiment=ctx.parent_experiment,
            existing_failure_records=ctx.existing_failure_records,
            retest_reason=ctx.retest_reason,
            experiment_memory_store=ctx.experiment_memory_store,
            failure_memory_store=ctx.failure_memory_store,
            reality_gap_store=ctx.reality_gap_store,
            compatibility_contract=ctx.compatibility_contract,
        )
