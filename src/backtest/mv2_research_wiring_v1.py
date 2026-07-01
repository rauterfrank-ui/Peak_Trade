"""
Canonical MV2 research wiring owner (RUNBOOK STEP 29L).

Fail-closed offline wiring:
Historical bars -> CanonicalMarketContextV1 -> integrated replay ->
CanonicalTradingDecisionEvidenceV1 -> {-1,0,1} position signals ->
BacktestEngine with cost_config_v0 and strategy registry snapshot binding.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Callable, Mapping, Optional, Sequence

import pandas as pd

from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DatasetProfileBindingV1,
    DatasetProfileV1,
    L1ObservationStatusV1,
    default_runtime_profile_binding_v1,
)
from src.backtest.cost_config_v0 import (
    EffectiveBacktestCostConfigV0,
    EconomicResearchExecutionCostBindingV0,
    resolve_economic_research_execution_cost_binding,
    resolve_effective_backtest_cost_config,
)
from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult
from src.backtest.stats import compute_backtest_stats
from src.backtest.strategy_signal_binding_v1 import (
    MV2_REPLAY_SIGNAL_SOURCE,
    StrategySignalBindingError,
    StrategySignalProvenanceV1,
    assert_engine_signal_provenance_consistency_v1,
    compute_strategy_signal_digest_v1,
    execute_configured_strategy_signal_series_v1,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    OfflineEvaluationSizingError,
    bind_offline_evaluation_sizing_v1,
    offline_evaluation_sizing_contract_requested,
)
from src.experiments.monte_carlo import (
    MonteCarloConfig,
    MonteCarloSummaryResult,
    run_monte_carlo_from_equity,
)
from src.experiments.stress_tests import (
    StressScenarioConfig,
    StressScenarioResult,
    StressTestSuiteResult,
    run_stress_test_suite,
)
from src.risk.limits import RiskLimits, RiskLimitsConfig
from src.strategies.registry import (
    REGISTRY_SCHEMA_VERSION,
    StrategyRegistrySnapshotV1,
    build_registry_snapshot,
)
from src.strategies.suitability_registry_adapter_v1 import build_suitability_registry_from_snapshot
from src.trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from src.trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from src.trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    CanonicalTradingDecisionEvidenceV1,
)
from src.trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorPolicyV1,
)
from src.trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentPolicyV1,
    DirectionalConfirmationStateV1,
)
from src.trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionDirectionState,
    DoublePlayCompositionPolicyV1,
    PositionManagementContext,
)
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_VERSION,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from src.trading.master_v2.double_play_futures_input import FuturesMarketType
from src.trading.master_v2.double_play_state import SideState
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayPoliciesV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from src.trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
)
from src.trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentPolicyV1,
)

MV2_RESEARCH_WIRING_LAYER_VERSION = "v1"
MV2_RESEARCH_WIRING_OWNER = "backtest.mv2_research_wiring_v1"
MV2_REQUIRED_INSTRUMENT_ID = "inst-eth-usdt-perp"

_REPLAY_IMPLEMENTATION_DIGEST = hashlib.sha256(
    b"trading.master_v2.integrated_offline_trading_logic_replay_v1"
).hexdigest()
_SUPPORTED_STRESS_CLASSES = (
    "single_crash_bar",
    "vol_spike",
    "drawdown_extension",
    "gap_down_open",
)
_DEFERRED_STRESS_CLASSES = (
    "fee_multiplier_stress",
    "slippage_multiplier_stress",
    "funding_stress",
    "spread_expansion_stress",
    "fill_quality_stress",
    "latency_stress",
    "trade_omission_stress",
)


class StressClassBindingStatus(str, Enum):
    BOUND = "BOUND"
    SUPPORTED_BY_EXISTING_OWNER = "SUPPORTED_BY_EXISTING_OWNER"
    ADAPTER_REQUIRED_AND_IMPLEMENTED = "ADAPTER_REQUIRED_AND_IMPLEMENTED"
    DEFERRED_EXPLICIT = "DEFERRED_EXPLICIT"
    UNSUPPORTED_BLOCKING = "UNSUPPORTED_BLOCKING"


@dataclass(frozen=True)
class MV2ReplayBarOutcomeV1:
    trading_epoch: int
    context: CanonicalMarketContextV1
    evidence: CanonicalTradingDecisionEvidenceV1
    position_signal: int
    replay_pass: bool
    fail_reasons: tuple[str, ...]
    l1_observation_status: L1ObservationStatusV1
    observed_l1_used: bool


@dataclass(frozen=True)
class MV2ResearchWiringResultV1:
    instrument_id: str
    registry_snapshot: StrategyRegistrySnapshotV1
    effective_cost_config: EffectiveBacktestCostConfigV0
    bar_outcomes: tuple[MV2ReplayBarOutcomeV1, ...]
    signals: pd.Series
    backtest_result: BacktestResult
    mv2_replay_signals: pd.Series
    strategy_signal_provenance: StrategySignalProvenanceV1
    mv2_replay_signal_digest: str
    mv2_replay_nonzero_signal_count: int
    sizing_provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StressClassBindingOutcomeV1:
    statuses: Mapping[str, StressClassBindingStatus]
    suite_result: Optional[StressTestSuiteResult]


@dataclass(frozen=True)
class MV2WalkForwardWindowResultV1:
    window_index: int
    train_slice: slice
    test_slice: slice
    train_period_digest: str
    test_period_digest: str
    config_digest: str
    oos_wiring_result: MV2ResearchWiringResultV1


@dataclass(frozen=True)
class MV2WalkForwardWiringResultV1:
    split_contract_digest: str
    windows: tuple[MV2WalkForwardWindowResultV1, ...]
    oos_results: tuple[MV2ResearchWiringResultV1, ...]


def _fail_closed(condition: bool, reason: str) -> None:
    if condition:
        raise ValueError(reason)


def risk_max_position_fraction_to_percent_v1(fraction: float) -> float:
    """Convert cfg.risk.max_position_size fraction (0, 1] to RiskLimits percent scale."""
    if not isinstance(fraction, (int, float)) or not math.isfinite(float(fraction)):
        raise ValueError("risk_max_position_size_invalid")
    value = float(fraction)
    if value <= 0.0 or value > 1.0:
        raise ValueError("risk_max_position_size_out_of_range")
    return value * 100.0


def build_mv2_research_risk_limits_v1(cfg: Mapping[str, Any]) -> RiskLimits:
    """Bind BacktestEngine RiskLimits from canonical cfg.risk.max_position_size fraction."""
    risk_section = cfg.get("risk")
    if not isinstance(risk_section, Mapping):
        raise ValueError("risk_section_missing")
    if risk_section.get("max_position_size") is None:
        raise ValueError("risk_max_position_size_missing")
    max_position_pct = risk_max_position_fraction_to_percent_v1(
        float(risk_section["max_position_size"])
    )
    return RiskLimits(RiskLimitsConfig(max_position_pct=max_position_pct))


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _default_component_versions() -> dict[str, str]:
    return {
        "canonical_market_context": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "canonical_scope_initialization": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "deterministic_scope_event_generator": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "directional_assessment": "v1",
        "survival_assessment": "v1",
        "suitability_binding": "v1",
        "double_play_composition_matrix": "v1",
        "double_play_entry_exit_policy": "v0",
        "double_play_state": "v0",
        "integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "canonical_trading_decision_evidence": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    }


def _default_policy_versions() -> dict[str, str]:
    return {
        "scope_initialization": SCOPE_INITIALIZATION_POLICY_VERSION,
        "scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        "directional": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        "survival": SURVIVAL_ASSESSMENT_POLICY_VERSION,
        "suitability": SUITABILITY_RANKING_POLICY_VERSION,
        "composition": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        "entry_exit": ENTRY_EXIT_POLICY_VERSION,
    }


def _default_policies() -> IntegratedOfflineReplayPoliciesV1:
    return IntegratedOfflineReplayPoliciesV1(
        scope_initialization=CanonicalScopeInitializationPolicyV1(
            min_scope_band=30.0,
            max_scope_band=800.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        scope_event_generator=ScopeEventGeneratorPolicyV1(
            hard_max_scope_distance=2000.0,
            hard_max_adverse_distance=900.0,
            hard_max_reversal_distance=1200.0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        directional=DirectionalAssessmentPolicyV1(
            observe_signal_threshold=0.001,
            candidate_signal_threshold=0.005,
            confirmation_signal_threshold=0.01,
            confirmation_epochs=2,
            validity_epochs=3,
            policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        ),
        survival=SurvivalAssessmentPolicyV1(
            min_net_edge=0.001,
            min_volatility_survival_ratio=0.5,
            min_sequence_survival_ratio=0.5,
            min_drawdown_survival_ratio=0.5,
            min_liquidation_buffer_ratio=0.1,
            validity_epochs=3,
            policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
        ),
        suitability=SuitabilityRankingPolicyV1(
            validity_epochs=3,
            no_match_status=SuitabilityBindingStatus.FAIL,
            policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        ),
        composition=DoublePlayCompositionPolicyV1(
            validity_epochs=3,
            both_candidate_outcome=BothCandidateOutcome.OBSERVE,
            both_invalid_outcome=BothInvalidOutcome.BLOCKED,
            policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        ),
        entry_exit=DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION),
    )


def _ensure_supported_instrument(instrument_id: str) -> None:
    lowered = instrument_id.lower()
    _fail_closed(
        instrument_id != MV2_REQUIRED_INSTRUMENT_ID, "instrument_not_supported_for_step29l"
    )
    _fail_closed("btc" in lowered or "xbt" in lowered, "bitcoin_instrument_forbidden")
    _fail_closed("spot" in lowered, "spot_instrument_forbidden")


def _ensure_no_lookahead(bars: pd.DataFrame) -> None:
    _fail_closed(not isinstance(bars.index, pd.DatetimeIndex), "bars_must_use_datetimeindex")
    _fail_closed(not bars.index.is_monotonic_increasing, "lookahead_index_not_monotonic")
    if "decision_time" in bars.columns:
        for ts, decision_time in zip(bars.index, bars["decision_time"]):
            decision_ts = pd.Timestamp(decision_time)
            _fail_closed(decision_ts > ts, "lookahead_decision_after_market_event")


def _price(row: pd.Series, key: str, fallback: str = "close") -> float:
    value = row.get(key, row.get(fallback))
    if value is None:
        raise ValueError(f"missing_price_field:{key}")
    return float(value)


def _resolve_warmup_status(bar: pd.Series) -> WarmupStatus:
    if "warmup_status" in bar.index:
        raw = str(bar["warmup_status"]).lower()
        if raw in {"warmup_required", "warmup_in_progress", "in_progress"}:
            return WarmupStatus.WARMUP_REQUIRED
        if raw == "warmup_invalid":
            return WarmupStatus.WARMUP_INVALID
        if raw == "warmup_complete":
            return WarmupStatus.WARMUP_COMPLETE
    if "warmup_complete" in bar.index and not bool(bar["warmup_complete"]):
        return WarmupStatus.WARMUP_REQUIRED
    return WarmupStatus.WARMUP_COMPLETE


def _period_digest(bars: pd.DataFrame) -> str:
    if bars.empty:
        return _stable_digest({"empty": True})
    return _stable_digest(
        {
            "start": str(bars.index[0]),
            "end": str(bars.index[-1]),
            "count": len(bars),
        }
    )


def _has_observed_l1(bar: pd.Series) -> bool:
    if "best_bid" not in bar.index or "best_ask" not in bar.index:
        return False
    bid = bar.get("best_bid")
    ask = bar.get("best_ask")
    if bid is None or ask is None:
        return False
    if pd.isna(bid) or pd.isna(ask):
        return False
    return float(bid) > 0.0 and float(ask) > 0.0 and float(ask) >= float(bid)


def _model_bound_l1_from_mark_price(
    mark_price: float,
    *,
    half_spread_bps: float,
) -> tuple[float, float, float]:
    half_spread_abs = mark_price * half_spread_bps / 10_000.0
    best_bid = mark_price - half_spread_abs
    best_ask = mark_price + half_spread_abs
    spread = best_ask - best_bid
    return best_bid, best_ask, spread


def bind_bar_for_mv2_wiring_v1(
    *,
    bar: pd.Series,
    instrument_id: str,
    trading_epoch: int,
    profile_binding: DatasetProfileBindingV1,
    research_execution_cost: Optional[EconomicResearchExecutionCostBindingV0] = None,
) -> tuple[CanonicalMarketContextV1, L1ObservationStatusV1, bool]:
    profile = profile_binding.dataset_profile
    l1_status = profile_binding.l1_observation_status

    if profile is DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1:
        if l1_status is not L1ObservationStatusV1.OBSERVED_HISTORICAL_L1:
            raise ValueError("runtime_profile_rejects_execution_model_bound_l1")
        context = bind_historical_bar_to_canonical_market_context_v1(
            bar=bar,
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
        )
        return context, L1ObservationStatusV1.OBSERVED_HISTORICAL_L1, True

    if profile is not DatasetProfileV1.ECONOMIC_RESEARCH_V1:
        raise ValueError(f"dataset_profile_unsupported:{profile.value}")
    if l1_status is not L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED:
        raise ValueError("research_profile_requires_execution_model_bound_l1_status")

    _ensure_supported_instrument(instrument_id)
    is_final = bool(bar.get("is_final", True))
    _fail_closed(not is_final, "bar_unfinalized")

    ts = pd.Timestamp(bar.name)
    market_event_time = ts.isoformat()
    decision_ts = pd.Timestamp(bar.get("decision_time", ts + timedelta(seconds=1)))
    _fail_closed(decision_ts < ts, "decision_time_before_market_event")

    mark_price = _price(bar, "mark_price")
    observed_l1_used = False
    outcome_l1_status = L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED

    if _has_observed_l1(bar):
        best_bid = float(bar["best_bid"])
        best_ask = float(bar["best_ask"])
        spread = float(bar.get("spread", best_ask - best_bid))
        observed_l1_used = True
        outcome_l1_status = L1ObservationStatusV1.OBSERVED_HISTORICAL_L1
    else:
        if research_execution_cost is None:
            raise ValueError("research_execution_cost_binding_missing")
        best_bid, best_ask, spread = _model_bound_l1_from_mark_price(
            mark_price,
            half_spread_bps=research_execution_cost.conservative_half_spread_bps,
        )

    context = CanonicalMarketContextV1(
        context_id=f"mv2-ctx-{instrument_id}-{trading_epoch}",
        instrument_id=instrument_id,
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=trading_epoch,
        market_event_time=market_event_time,
        decision_time=decision_ts.isoformat(),
        bar_interval=str(bar.get("bar_interval", "1m")),
        bar_finality_status=BarFinalityStatus.FINALIZED
        if is_final
        else BarFinalityStatus.UNFINALIZED,
        mark_price=mark_price,
        index_price=_price(bar, "index_price"),
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        volume=float(bar.get("volume", 0.0)),
        open_interest=float(bar.get("open_interest", 0.0)),
        funding_rate=float(bar.get("funding_rate", 0.0)),
        volatility_estimate=float(bar.get("volatility_estimate", 0.2)),
        trend_feature_set={"trend_slope": float(bar.get("trend_slope", 0.01))},
        momentum_feature_set={"momentum": float(bar.get("momentum", 0.01))},
        liquidity_feature_set={"liq_score": float(bar.get("liq_score", 0.9))},
        market_structure_feature_set={"range_ratio": float(bar.get("range_ratio", 0.4))},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=_resolve_warmup_status(bar),
        feature_contract_version=FEATURE_CONTRACT_VERSION,
    )
    return with_computed_input_digest(context), outcome_l1_status, observed_l1_used


def bind_historical_bar_to_canonical_market_context_v1(
    *,
    bar: pd.Series,
    instrument_id: str,
    trading_epoch: int,
) -> CanonicalMarketContextV1:
    _ensure_supported_instrument(instrument_id)
    is_final = bool(bar.get("is_final", True))
    _fail_closed(not is_final, "bar_unfinalized")

    ts = pd.Timestamp(bar.name)
    market_event_time = ts.isoformat()
    decision_ts = pd.Timestamp(bar.get("decision_time", ts + timedelta(seconds=1)))
    _fail_closed(decision_ts < ts, "decision_time_before_market_event")

    best_bid = _price(bar, "best_bid")
    best_ask = _price(bar, "best_ask")
    spread = float(bar.get("spread", best_ask - best_bid))
    context = CanonicalMarketContextV1(
        context_id=f"mv2-ctx-{instrument_id}-{trading_epoch}",
        instrument_id=instrument_id,
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=trading_epoch,
        market_event_time=market_event_time,
        decision_time=decision_ts.isoformat(),
        bar_interval=str(bar.get("bar_interval", "1m")),
        bar_finality_status=BarFinalityStatus.FINALIZED
        if is_final
        else BarFinalityStatus.UNFINALIZED,
        mark_price=_price(bar, "mark_price"),
        index_price=_price(bar, "index_price"),
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        volume=float(bar.get("volume", 0.0)),
        open_interest=float(bar.get("open_interest", 0.0)),
        funding_rate=float(bar.get("funding_rate", 0.0)),
        volatility_estimate=float(bar.get("volatility_estimate", 0.2)),
        trend_feature_set={"trend_slope": float(bar.get("trend_slope", 0.01))},
        momentum_feature_set={"momentum": float(bar.get("momentum", 0.01))},
        liquidity_feature_set={"liq_score": float(bar.get("liq_score", 0.9))},
        market_structure_feature_set={"range_ratio": float(bar.get("range_ratio", 0.4))},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=_resolve_warmup_status(bar),
        feature_contract_version=FEATURE_CONTRACT_VERSION,
    )
    return with_computed_input_digest(context)


def map_decision_evidence_to_position_signal_v1(
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> int:
    """Adapter-only mapping from canonical decision outcome to backtest signal."""
    outcome = str(evidence.decision_outcome).lower()
    if outcome in {"enter_long"}:
        return 1
    if outcome in {"enter_short"}:
        return -1
    return 0


def bind_walk_forward_windows_v1(
    bars: pd.DataFrame,
    *,
    train_bars: int,
    test_bars: int,
    step_bars: int,
) -> tuple[tuple[slice, slice], ...]:
    _fail_closed(train_bars <= 0, "walk_forward_train_bars_invalid")
    _fail_closed(test_bars <= 0, "walk_forward_test_bars_invalid")
    _fail_closed(step_bars <= 0, "walk_forward_step_bars_invalid")
    _fail_closed(len(bars) < train_bars + test_bars, "walk_forward_insufficient_bars")

    windows: list[tuple[slice, slice]] = []
    start = 0
    while start + train_bars + test_bars <= len(bars):
        train_slice = slice(start, start + train_bars)
        test_slice = slice(start + train_bars, start + train_bars + test_bars)
        windows.append((train_slice, test_slice))
        start += step_bars
    return tuple(windows)


def bind_monte_carlo_analysis_v1(
    backtest_result: BacktestResult,
    config: MonteCarloConfig,
) -> MonteCarloSummaryResult:
    _fail_closed(config.seed is None, "monte_carlo_seed_missing")
    return run_monte_carlo_from_equity(backtest_result.equity_curve, config)


def bind_stress_class_suite_v1(
    returns: pd.Series,
    *,
    requested_classes: Optional[Sequence[str]] = None,
    stats_fn: Optional[Callable[[pd.Series], Mapping[str, float]]] = None,
) -> StressClassBindingOutcomeV1:
    if stats_fn is None:

        def _default_stats_fn(ret: pd.Series) -> Mapping[str, float]:
            equity = (1.0 + ret).cumprod() * 10_000.0
            return compute_backtest_stats([], equity)

        stats_fn = _default_stats_fn

    classes = tuple(requested_classes or _SUPPORTED_STRESS_CLASSES)
    statuses: dict[str, StressClassBindingStatus] = {}
    scenarios: list[StressScenarioConfig] = []
    for cls in classes:
        if cls in _SUPPORTED_STRESS_CLASSES:
            statuses[cls] = StressClassBindingStatus.SUPPORTED_BY_EXISTING_OWNER
            scenarios.append(StressScenarioConfig(scenario_type=cls))
        elif cls in _DEFERRED_STRESS_CLASSES:
            statuses[cls] = StressClassBindingStatus.DEFERRED_EXPLICIT
        else:
            statuses[cls] = StressClassBindingStatus.UNSUPPORTED_BLOCKING

    for deferred in _DEFERRED_STRESS_CLASSES:
        statuses.setdefault(deferred, StressClassBindingStatus.DEFERRED_EXPLICIT)

    for required in _SUPPORTED_STRESS_CLASSES:
        statuses.setdefault(required, StressClassBindingStatus.BOUND)
        _fail_closed(
            statuses[required] is StressClassBindingStatus.UNSUPPORTED_BLOCKING,
            f"required_stress_class_unsupported:{required}",
        )

    suite: Optional[StressTestSuiteResult] = None
    if scenarios:
        suite = run_stress_test_suite(returns=returns, scenarios=scenarios, stats_fn=stats_fn)

    return StressClassBindingOutcomeV1(statuses=statuses, suite_result=suite)


def compute_mv2_evidence_chain_digests_v1(
    *,
    context: CanonicalMarketContextV1,
    evidence: CanonicalTradingDecisionEvidenceV1,
    registry_snapshot: StrategyRegistrySnapshotV1,
    cost_config: EffectiveBacktestCostConfigV0,
    strategy_id: str = "",
    strategy_version: str = "",
    data_period: str = "",
    train_period: str = "",
    validation_period: str = "",
    oos_period: str = "",
    fee_model_version: str = "",
    slippage_model_version: str = "",
    funding_model_version_or_status: str = "",
    execution_model_version: str = "",
    config_digest: str = "",
    implementation_digest: str = "",
    data_digest: str = "",
    replay_digest: str = "",
    backtest_result_digest: str = "",
    walk_forward_result_digest_or_status: str = "not_run",
    monte_carlo_result_digest_or_status: str = "not_run",
    stress_result_digest_or_status: str = "not_run",
    metrics_digest: str = "",
    manifest_digest: str = "",
) -> Mapping[str, str]:
    chain = {
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "registry_snapshot_digest": registry_snapshot.semantic_digest,
        "canonical_trading_logic_version": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "data_period": data_period,
        "train_period": train_period,
        "validation_period": validation_period,
        "oos_period": oos_period,
        "fee_model_version": fee_model_version or cost_config.cost_model_version,
        "slippage_model_version": slippage_model_version or cost_config.cost_model_version,
        "funding_model_version_or_status": funding_model_version_or_status or "deferred",
        "execution_model_version": execution_model_version or "offline_replay_v1",
        "config_digest": config_digest,
        "implementation_digest": implementation_digest or _REPLAY_IMPLEMENTATION_DIGEST,
        "data_digest": data_digest or context.input_digest,
        "replay_digest": replay_digest or evidence.semantic_digest,
        "market_context_input_digest": context.input_digest,
        "decision_evidence_semantic_digest": evidence.semantic_digest,
        "registry_input_digest": registry_snapshot.input_digest,
        "registry_semantic_digest": registry_snapshot.semantic_digest,
        "cost_config_digest": cost_config.config_digest,
        "backtest_result_digest": backtest_result_digest,
        "walk_forward_result_digest_or_status": walk_forward_result_digest_or_status,
        "monte_carlo_result_digest_or_status": monte_carlo_result_digest_or_status,
        "stress_result_digest_or_status": stress_result_digest_or_status,
        "metrics_digest": metrics_digest,
        "manifest_digest": manifest_digest,
    }
    chain_digest = _stable_digest(chain)
    return {**chain, "wiring_chain_digest": chain_digest}


def compute_mv2_backtest_metrics_v1(result: BacktestResult) -> Mapping[str, float]:
    trades: list[dict[str, Any]] = []
    if result.trades is not None and not result.trades.empty:
        trades = result.trades.to_dict(orient="records")
    return compute_backtest_stats(trades=trades, equity_curve=result.equity_curve)


def _build_replay_input(
    *,
    replay_id: str,
    instrument_id: str,
    trading_epoch: int,
    context: CanonicalMarketContextV1,
    strategy_registry: Any,
    config_digest: str,
    implementation_digest: str,
    input_digest: str,
) -> IntegratedOfflineReplayInputV1:
    price_path = (float(context.mark_price), float(context.mark_price + 5.0))
    return IntegratedOfflineReplayInputV1(
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        canonical_market_context=context,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=None,
        scope_direction_state=ScopeDirectionState.LONG,
        scope_confirmation_state=ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
        ),
        scope_cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        up_distance=120.0,
        adverse_exit_distance=60.0,
        reversal_distance=90.0,
        confirmation_epochs=2,
        current_price=float(context.mark_price),
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
            last_signal_strength=0.02,
        ),
        strategy_registry=strategy_registry,
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_composition_direction_state=CompositionDirectionState.NEUTRAL,
        position_management_context=PositionManagementContext.FLAT,
        last_evaluated_trading_epoch=trading_epoch - 1,
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
        position_state=PositionState.FLAT_RECONCILED,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
        cooldown_pass=True,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        policies=_default_policies(),
        component_versions=_default_component_versions(),
        policy_versions=_default_policy_versions(),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        input_digest=input_digest,
        expected_component_contracts=_default_component_versions(),
        context_reference=f"mv2-research-{trading_epoch}",
        now_tick=trading_epoch,
    )


def run_mv2_research_backtest_wiring_v1(
    bars: pd.DataFrame,
    *,
    strategy_id: str,
    cfg: Mapping[str, Any],
    instrument_id: str = MV2_REQUIRED_INSTRUMENT_ID,
    expected_registry_input_digest: Optional[str] = None,
    expected_registry_semantic_digest: Optional[str] = None,
    expected_registry_schema_version: str = REGISTRY_SCHEMA_VERSION,
    expected_cost_model_version: str = "backtest_cost_v0",
    expected_data_layer_version: str = CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    expected_replay_layer_version: str = INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    expected_implementation_digest: Optional[str] = None,
    explicit_zero_cost_non_economic: bool = False,
    profile_binding: Optional[DatasetProfileBindingV1] = None,
) -> MV2ResearchWiringResultV1:
    _fail_closed(bars.empty, "bars_empty")
    _ensure_supported_instrument(instrument_id)
    _ensure_no_lookahead(bars)

    effective_profile = profile_binding or default_runtime_profile_binding_v1()
    if effective_profile.dataset_profile is DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1:
        if (
            effective_profile.l1_observation_status
            is L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED
        ):
            raise ValueError("runtime_consumer_rejects_execution_model_bound_l1")

    research_execution_cost: Optional[EconomicResearchExecutionCostBindingV0] = None
    if effective_profile.dataset_profile is DatasetProfileV1.ECONOMIC_RESEARCH_V1:
        research_execution_cost = resolve_economic_research_execution_cost_binding(cfg)

    snapshot = build_registry_snapshot()
    _fail_closed(
        snapshot.registry_schema_version != expected_registry_schema_version,
        "registry_schema_version_mismatch",
    )
    if expected_registry_input_digest is not None:
        _fail_closed(
            snapshot.input_digest != expected_registry_input_digest,
            "registry_input_digest_mismatch",
        )
    if expected_registry_semantic_digest is not None:
        _fail_closed(
            snapshot.semantic_digest != expected_registry_semantic_digest,
            "registry_semantic_digest_mismatch",
        )

    _fail_closed(strategy_id not in set(snapshot.strategy_ids_sorted), "unknown_strategy")
    suitability_registry = build_suitability_registry_from_snapshot(snapshot)
    _fail_closed(
        suitability_registry is None or len(suitability_registry.entries) == 0, "missing_registry"
    )

    effective_cost = resolve_effective_backtest_cost_config(
        cfg,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
        research_execution_cost_binding=research_execution_cost,
    )
    _fail_closed(
        effective_cost.taker_fee_bps == 0.0
        and effective_cost.entry_slippage_bps == 0.0
        and not explicit_zero_cost_non_economic,
        "zero_cost_without_explicit_flag",
    )
    _fail_closed(
        effective_cost.cost_model_version != expected_cost_model_version,
        "cost_model_version_mismatch",
    )
    _fail_closed(
        expected_data_layer_version != CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "data_layer_version_mismatch",
    )
    _fail_closed(
        expected_replay_layer_version != INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "replay_layer_version_mismatch",
    )

    implementation_digest = expected_implementation_digest or _REPLAY_IMPLEMENTATION_DIGEST
    _fail_closed(
        expected_implementation_digest is not None
        and expected_implementation_digest != _REPLAY_IMPLEMENTATION_DIGEST,
        "implementation_digest_mismatch",
    )

    replay_id = f"mv2-research-{len(bars)}"
    config_digest = _stable_digest({"cfg": dict(cfg), "owner": MV2_RESEARCH_WIRING_OWNER})

    try:
        strategy_binding = execute_configured_strategy_signal_series_v1(
            bars,
            strategy_id=strategy_id,
            cfg=cfg,
        )
    except StrategySignalBindingError as exc:
        raise ValueError(f"configured_strategy_signal_binding_failed:{exc}") from exc
    assert_engine_signal_provenance_consistency_v1(strategy_binding.provenance)
    engine_signal_series = strategy_binding.signals

    outcomes: list[MV2ReplayBarOutcomeV1] = []
    replay_signals: list[int] = []
    signal_index: list[pd.Timestamp] = []
    for i, (_, row) in enumerate(bars.iterrows()):
        context, l1_status, observed_l1_used = bind_bar_for_mv2_wiring_v1(
            bar=row,
            instrument_id=instrument_id,
            trading_epoch=i,
            profile_binding=effective_profile,
            research_execution_cost=research_execution_cost,
        )
        input_digest = _stable_digest(
            {
                "context_digest": context.input_digest,
                "epoch": i,
                "registry_input_digest": snapshot.input_digest,
                "cost_digest": effective_cost.config_digest,
                "profile_binding": effective_profile.to_dict(),
                "l1_observation_status": l1_status.value,
                "observed_l1_used": observed_l1_used,
            }
        )
        replay_input = _build_replay_input(
            replay_id=replay_id,
            instrument_id=instrument_id,
            trading_epoch=i,
            context=context,
            strategy_registry=suitability_registry,
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            input_digest=input_digest,
        )
        replay_result = run_integrated_offline_trading_logic_replay_v1(replay_input)
        signal = map_decision_evidence_to_position_signal_v1(replay_result.evidence)
        if context.warmup_status is not WarmupStatus.WARMUP_COMPLETE:
            signal = 0
        outcomes.append(
            MV2ReplayBarOutcomeV1(
                trading_epoch=i,
                context=context,
                evidence=replay_result.evidence,
                position_signal=signal,
                replay_pass=replay_result.replay_pass,
                fail_reasons=replay_result.fail_reasons,
                l1_observation_status=l1_status,
                observed_l1_used=observed_l1_used,
            )
        )
        replay_signals.append(signal)
        signal_index.append(pd.Timestamp(row.name))

    mv2_replay_series = pd.Series(replay_signals, index=pd.DatetimeIndex(signal_index), dtype=int)
    mv2_replay_digest = compute_strategy_signal_digest_v1(
        mv2_replay_series,
        strategy_id=strategy_id,
        strategy_params_digest=_stable_digest(
            {"source": MV2_REPLAY_SIGNAL_SOURCE, "owner": MV2_RESEARCH_WIRING_OWNER}
        ),
    )
    mv2_replay_nonzero = int((mv2_replay_series != 0).sum())

    def _signal_fn(df: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:  # noqa: ARG001
        aligned = engine_signal_series.reindex(df.index)
        if aligned.isna().any():
            raise ValueError("engine_strategy_signal_index_mismatch")
        return aligned.astype(int)

    engine_cfg = dict(cfg)
    sizing_provenance: dict[str, Any] = {}
    strategy_params = {
        **dict(strategy_binding.provenance.effective_strategy_params),
        "strategy_id": strategy_id,
    }
    if offline_evaluation_sizing_contract_requested(cfg):
        binding = cfg.get("real_admissible_futures_evaluation_binding_v1", {})
        dataset_digest = ""
        if isinstance(binding, Mapping):
            dataset_digest = str(binding.get("expected_dataset_digest", ""))
        try:
            contract, _accounting = bind_offline_evaluation_sizing_v1(
                engine_cfg,
                strategy_params_digest=strategy_binding.provenance.strategy_params_digest,
                dataset_digest=dataset_digest,
            )
        except OfflineEvaluationSizingError as exc:
            raise ValueError(f"offline_evaluation_sizing_contract_invalid:{exc}") from exc
        strategy_params["stop_pct"] = contract.stop_pct
        engine_cfg["offline_evaluation_sizing_contract_v1"] = contract.to_dict()

    engine = BacktestEngine(
        use_execution_pipeline=False,
        risk_limits=build_mv2_research_risk_limits_v1(cfg),
    )
    engine.config = engine_cfg
    backtest_result = engine.run_realistic(
        df=bars,
        strategy_signal_fn=_signal_fn,
        strategy_params=strategy_params,
        symbol=instrument_id,
        cost_config=effective_cost,
        explicit_zero_cost_non_economic=explicit_zero_cost_non_economic,
    )

    if offline_evaluation_sizing_contract_requested(cfg):
        from src.backtest.offline_evaluation_sizing_contract_v1 import (
            get_offline_sizing_accounting_v1,
            load_offline_evaluation_sizing_contract_v1,
            serialize_sizing_provenance_v1,
        )

        contract = load_offline_evaluation_sizing_contract_v1(engine_cfg)
        accounting = get_offline_sizing_accounting_v1(engine_cfg)
        if accounting is None:
            raise ValueError("offline_sizing_accounting_missing")
        sizing_provenance = serialize_sizing_provenance_v1(contract, accounting)

    return MV2ResearchWiringResultV1(
        instrument_id=instrument_id,
        registry_snapshot=snapshot,
        effective_cost_config=effective_cost,
        bar_outcomes=tuple(outcomes),
        signals=engine_signal_series,
        backtest_result=backtest_result,
        mv2_replay_signals=mv2_replay_series,
        strategy_signal_provenance=strategy_binding.provenance,
        mv2_replay_signal_digest=mv2_replay_digest,
        mv2_replay_nonzero_signal_count=mv2_replay_nonzero,
        sizing_provenance=sizing_provenance,
    )


def run_mv2_walk_forward_wiring_v1(
    bars: pd.DataFrame,
    *,
    strategy_id: str,
    cfg: Mapping[str, Any],
    train_bars: int,
    test_bars: int,
    step_bars: int,
    instrument_id: str = MV2_REQUIRED_INSTRUMENT_ID,
    expected_registry_input_digest: Optional[str] = None,
    expected_registry_semantic_digest: Optional[str] = None,
    expected_registry_schema_version: str = REGISTRY_SCHEMA_VERSION,
    expected_cost_model_version: str = "backtest_cost_v0",
    expected_data_layer_version: str = CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    expected_replay_layer_version: str = INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    expected_implementation_digest: Optional[str] = None,
    explicit_zero_cost_non_economic: bool = False,
    profile_binding: Optional[DatasetProfileBindingV1] = None,
) -> MV2WalkForwardWiringResultV1:
    """Run MV2 replay on OOS test windows only; train windows bind split contract only."""
    windows = bind_walk_forward_windows_v1(
        bars,
        train_bars=train_bars,
        test_bars=test_bars,
        step_bars=step_bars,
    )
    _fail_closed(len(windows) == 0, "walk_forward_no_windows")

    split_contract_digest = _stable_digest(
        {
            "train_bars": train_bars,
            "test_bars": test_bars,
            "step_bars": step_bars,
            "data_digest": _period_digest(bars),
            "owner": MV2_RESEARCH_WIRING_OWNER,
        }
    )

    wiring_kwargs = {
        "strategy_id": strategy_id,
        "cfg": cfg,
        "instrument_id": instrument_id,
        "expected_registry_input_digest": expected_registry_input_digest,
        "expected_registry_semantic_digest": expected_registry_semantic_digest,
        "expected_registry_schema_version": expected_registry_schema_version,
        "expected_cost_model_version": expected_cost_model_version,
        "expected_data_layer_version": expected_data_layer_version,
        "expected_replay_layer_version": expected_replay_layer_version,
        "expected_implementation_digest": expected_implementation_digest,
        "explicit_zero_cost_non_economic": explicit_zero_cost_non_economic,
        "profile_binding": profile_binding,
    }

    window_results: list[MV2WalkForwardWindowResultV1] = []
    oos_results: list[MV2ResearchWiringResultV1] = []
    for idx, (train_slice, test_slice) in enumerate(windows):
        train_df = bars.iloc[train_slice]
        test_df = bars.iloc[test_slice]
        _fail_closed(train_df.empty or test_df.empty, "walk_forward_empty_window")
        train_digest = _period_digest(train_df)
        test_digest = _period_digest(test_df)
        window_config_digest = _stable_digest(
            {
                "split_contract_digest": split_contract_digest,
                "window_index": idx,
                "train_period_digest": train_digest,
                "test_period_digest": test_digest,
            }
        )
        oos_result = run_mv2_research_backtest_wiring_v1(test_df, **wiring_kwargs)
        window_results.append(
            MV2WalkForwardWindowResultV1(
                window_index=idx,
                train_slice=train_slice,
                test_slice=test_slice,
                train_period_digest=train_digest,
                test_period_digest=test_digest,
                config_digest=window_config_digest,
                oos_wiring_result=oos_result,
            )
        )
        oos_results.append(oos_result)

    return MV2WalkForwardWiringResultV1(
        split_contract_digest=split_contract_digest,
        windows=tuple(window_results),
        oos_results=tuple(oos_results),
    )
