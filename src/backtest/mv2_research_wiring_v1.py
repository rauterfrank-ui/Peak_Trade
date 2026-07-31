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
from dataclasses import dataclass, field, fields, replace
from datetime import timedelta
from enum import Enum
from pathlib import Path
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
    CANONICAL_MV2_SYSTEM_PATH_CLASSIFICATION,
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    CANONICAL_SYSTEM_REPLAY,
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    MV2_REPLAY_SIGNAL_SOURCE,
    RUN_BACKTEST_PATH_CLASSIFICATION,
    StrategySignalBindingError,
    StrategySignalProvenanceV1,
    assert_decision_funnel_trade_alignment_v1,
    assert_engine_signal_provenance_consistency_v1,
    assert_backtest_engine_mv2_replay_signal_parity_v1,
    assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1,
    compute_strategy_signal_digest_v1,
    execute_configured_strategy_signal_series_v1,
    resolve_mv2_research_engine_signal_source_v1,
    validate_mv2_replay_engine_signal_contract_v1,
)
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementErrorV1,
    StrategySuitabilityAgreementMaterialV1,
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
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    DecisionFunnelAccumulatorV0,
    materialize_block_reason_counts_v0,
)
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
    CanonicalScopeSnapshotV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from src.trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    CanonicalTradingDecisionEvidenceV1,
    derive_decision_id,
    with_computed_evidence_semantic_digest,
)
from src.trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorPolicyV1,
)
from src.trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
    initial_directional_confirmation_side_state_carrier_v1,
)
from src.trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
)
from src.trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from src.trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionDirectionState,
    CompositionSelectedSide,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
)
from src.trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0 import (
    side_state_to_entry_exit_direction,
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
from src.trading.master_v2.double_play_state import RuntimeScopeState, SideState
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayIntermediateV1,
    IntegratedOfflineReplayPoliciesV1,
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
    scope_direction_from_side_state_v1,
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
from src.trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KillSwitchBacktestStateFileRecordV0,
    KillSwitchBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_killswitch_exposure_gate_v0,
    bind_killswitch_boundary_backtest_state_file_evidence_v0,
    load_killswitch_backtest_state_file_record_v0,
)
from src.trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
    ReconciliationBacktestStateFileRecordV0,
    ReconciliationBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_reconciliation_exposure_gate_v0,
    bind_reconciliation_boundary_backtest_state_file_evidence_v0,
    load_reconciliation_backtest_state_file_record_v0,
)
from src.trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
    CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_capital_risk_sizing_exposure_gate_v0,
    bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0,
    load_capital_risk_sizing_backtest_state_file_record_v0,
)
from src.trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
    CanonicalOrderIntentBacktestStateFileRecordV0,
    CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_canonical_order_intent_exposure_gate_v0,
    bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0,
    load_canonical_order_intent_backtest_state_file_record_v0,
)
from src.trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
    SafetyKernelBacktestStateFileRecordV0,
    SafetyKernelBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_safety_kernel_exposure_gate_v0,
    bind_safety_kernel_boundary_backtest_state_file_evidence_v0,
    load_safety_kernel_backtest_state_file_record_v0,
)
from src.trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0 import (
    PromotionGateBacktestStateFileRecordV0,
    PromotionGateBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_promotion_gate_exposure_gate_v0,
    bind_promotion_gate_boundary_backtest_state_file_evidence_v0,
    load_promotion_gate_backtest_state_file_record_v0,
)
from src.trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0 import (
    AiObservabilityBacktestStateFileRecordV0,
    AiObservabilityBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_ai_observability_exposure_gate_v0,
    bind_ai_observability_boundary_backtest_state_file_evidence_v0,
    load_ai_observability_backtest_state_file_record_v0,
)
from src.trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0 import (
    FeedbackLearningBacktestStateFileRecordV0,
    FeedbackLearningBoundaryBacktestStateFileEvidenceV0,
    apply_backtest_feedback_learning_exposure_gate_v0,
    bind_feedback_learning_boundary_backtest_state_file_evidence_v0,
    load_feedback_learning_backtest_state_file_record_v0,
)
from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    BACKTEST_ENGINE_POSITION_FEEDBACK_ADAPTER_OWNER,
    CANONICAL_BACKTEST_POSITION_OWNER,
    BacktestEnginePositionFeedbackV1,
    LegacyRealisticBarLoopStateV1,
    capture_backtest_engine_position_feedback_v1,
    coerce_backtest_position_state_v1,
    finalize_legacy_realistic_bar_loop_v1,
    init_legacy_realistic_bar_loop_state_v1,
    step_legacy_realistic_bar_v1,
)

MV2_RESEARCH_WIRING_LAYER_VERSION = "v1"
MV2_RESEARCH_WIRING_OWNER = "backtest.mv2_research_wiring_v1"
ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON = "warmup_required"
ECONOMIC_RESEARCH_WARMUP_INVALID_BLOCK_REASON = "warmup_invalid_blocked"
ECONOMIC_RESEARCH_NO_WARMUP_COMPLETE_BAR_REASON = "no_warmup_complete_bar"
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
class KillSwitchBacktestStateFileBindingConfigV1:
    """Optional backtest KillSwitch state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: KillSwitchBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False
    has_existing_position: bool = False


@dataclass(frozen=True)
class ReconciliationBacktestStateFileBindingConfigV1:
    """Optional backtest reconciliation state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: ReconciliationBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class CapitalRiskSizingBacktestStateFileBindingConfigV1:
    """Optional backtest capital/risk/sizing state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: CapitalRiskSizingBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class CanonicalOrderIntentBacktestStateFileBindingConfigV1:
    """Optional backtest canonical order intent state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: CanonicalOrderIntentBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class SafetyKernelBacktestStateFileBindingConfigV1:
    """Optional backtest Safety Kernel state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: SafetyKernelBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class PromotionGateBacktestStateFileBindingConfigV1:
    """Optional backtest Promotion Gate state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: PromotionGateBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class AiObservabilityBacktestStateFileBindingConfigV1:
    """Optional backtest AI / Observability state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: AiObservabilityBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class FeedbackLearningBacktestStateFileBindingConfigV1:
    """Optional backtest Feedback / Learning state-file binding — offline evidence only."""

    state_file_path: Path | None = None
    state_file_record: FeedbackLearningBacktestStateFileRecordV0 | None = None
    expected_state_file_digest_ref: str = ""
    require_state_file: bool = False


@dataclass(frozen=True)
class MV2IntegratedReplayBarSequenceStateV1:
    """Deterministic per-run bar-sequence carrier for integrated offline replay inputs."""

    existing_scope: CanonicalScopeSnapshotV1 | None
    scope_direction_state: ScopeDirectionState
    scope_confirmation_state: ScopeConfirmationStateV1
    scope_cooldown_state: ScopeCooldownStateV1
    # LEGACY_NON_AUTHORITY: retained for API compatibility; not used for confirmation.
    directional_confirmation_state: DirectionalConfirmationStateV1
    previous_composition_direction_state: CompositionDirectionState
    position_management_context: PositionManagementContext
    last_evaluated_trading_epoch: int
    side_state: SideState
    direction_state: EntryExitDirectionState
    position_state: PositionState
    reconciliation_state: ReconciliationState
    trading_gate: TradingGate
    safety_mode: SafetyMode
    existing_position_side: ExistingPositionSide
    venue_flat: bool
    cooldown_pass: bool
    scope_adverse_exit_signal: PolicySignalV0
    profit_protection_signal: PolicySignalV0
    time_exit_signal: PolicySignalV0
    strategy_invalidation_signal: PolicySignalV0
    hard_risk_reduction_signal: PolicySignalV0
    safety_exit_signal: PolicySignalV0
    now_tick: int
    runtime_scope_state: RuntimeScopeState | None = None
    runtime_scope_bound_instrument_id: str | None = None
    dynamic_scope_rules: Any | None = None
    # Prior bar mark for market-context price_path when strategy direction is unbound.
    prior_mark_price: float | None = None
    # C3 productive confirmation carrier (Bull/Bear isolated).
    directional_confirmation_progress: DirectionalConfirmationSideStateCarrierV1 | None = None
    confirmation_progress_session_id: str | None = None
    confirmation_progress_venue: str | None = None
    confirmation_progress_instrument: InstrumentObservationKeyV1 | None = None


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
    killswitch_backtest_state_file_evidence: (
        KillSwitchBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    reconciliation_backtest_state_file_evidence: (
        ReconciliationBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    capital_risk_sizing_backtest_state_file_evidence: (
        CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    canonical_order_intent_backtest_state_file_evidence: (
        CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    safety_kernel_backtest_state_file_evidence: (
        SafetyKernelBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    promotion_gate_backtest_state_file_evidence: (
        PromotionGateBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    ai_observability_backtest_state_file_evidence: (
        AiObservabilityBoundaryBacktestStateFileEvidenceV0 | None
    ) = None
    feedback_learning_backtest_state_file_evidence: (
        FeedbackLearningBoundaryBacktestStateFileEvidenceV0 | None
    ) = None


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
    backtest_engine_signal_source: str = CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE
    backtest_engine_signal_digest: str = ""
    decision_funnel_counts: Mapping[str, int] = field(default_factory=dict)
    block_reason_counts: Mapping[str, int] = field(default_factory=dict)


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


def _resolve_volatility_estimate_for_economic_research_wiring_v1(
    bar: pd.Series,
    *,
    warmup_status: WarmupStatus,
) -> float:
    """Fail-closed volatility binding for economic_research_v1 MV2 wiring."""
    _fail_closed(warmup_status is not WarmupStatus.WARMUP_COMPLETE, "warmup_status_not_complete")
    if "volatility_estimate" not in bar.index:
        _fail_closed(True, "volatility_estimate_missing")
    raw = bar["volatility_estimate"]
    if raw is None or pd.isna(raw):
        _fail_closed(True, "volatility_estimate_null")
    value = float(raw)
    _fail_closed(not math.isfinite(value), "volatility_estimate_non_finite")
    _fail_closed(value <= 0.0, "volatility_estimate_non_positive")
    return value


def _validate_economic_research_bar_structural_contract_v1(bar: pd.Series) -> None:
    """Structural finalized-bar contract for economic_research_v1 observation-only bars."""
    is_final = bool(bar.get("is_final", True))
    _fail_closed(not is_final, "bar_unfinalized")
    ts = pd.Timestamp(bar.name)
    decision_ts = pd.Timestamp(bar.get("decision_time", ts + timedelta(seconds=1)))
    _fail_closed(decision_ts < ts, "decision_time_before_market_event")
    _price(bar, "mark_price")


def _bind_economic_research_l1_fields_v1(
    *,
    bar: pd.Series,
    mark_price: float,
    research_execution_cost: Optional[EconomicResearchExecutionCostBindingV0],
) -> tuple[float, float, float, L1ObservationStatusV1, bool]:
    if _has_observed_l1(bar):
        best_bid = float(bar["best_bid"])
        best_ask = float(bar["best_ask"])
        spread = float(bar.get("spread", best_ask - best_bid))
        return (
            best_bid,
            best_ask,
            spread,
            L1ObservationStatusV1.OBSERVED_HISTORICAL_L1,
            True,
        )
    if research_execution_cost is None:
        raise ValueError("research_execution_cost_binding_missing")
    best_bid, best_ask, spread = _model_bound_l1_from_mark_price(
        mark_price,
        half_spread_bps=research_execution_cost.conservative_half_spread_bps,
    )
    return (
        best_bid,
        best_ask,
        spread,
        L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
        False,
    )


def _bind_economic_research_warmup_observation_bar_v1(
    *,
    bar: pd.Series,
    instrument_id: str,
    trading_epoch: int,
    research_execution_cost: Optional[EconomicResearchExecutionCostBindingV0],
) -> tuple[CanonicalMarketContextV1, L1ObservationStatusV1, bool]:
    """Observation-only economic_research_v1 binding for WARMUP_REQUIRED bars."""
    _ensure_supported_instrument(instrument_id)
    _validate_economic_research_bar_structural_contract_v1(bar)
    ts = pd.Timestamp(bar.name)
    market_event_time = ts.isoformat()
    decision_ts = pd.Timestamp(bar.get("decision_time", ts + timedelta(seconds=1)))
    mark_price = _price(bar, "mark_price")
    best_bid, best_ask, spread, l1_status, observed_l1_used = _bind_economic_research_l1_fields_v1(
        bar=bar,
        mark_price=mark_price,
        research_execution_cost=research_execution_cost,
    )
    context = CanonicalMarketContextV1(
        context_id=f"mv2-ctx-{instrument_id}-{trading_epoch}",
        instrument_id=instrument_id,
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=trading_epoch,
        market_event_time=market_event_time,
        decision_time=decision_ts.isoformat(),
        bar_interval=str(bar.get("bar_interval", "1m")),
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=mark_price,
        index_price=_price(bar, "index_price"),
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        volume=float(bar.get("volume", 0.0)),
        open_interest=float(bar.get("open_interest", 0.0)),
        funding_rate=float(bar.get("funding_rate", 0.0)),
        volatility_estimate=float("nan"),
        trend_feature_set={"trend_slope": float(bar.get("trend_slope", 0.01))},
        momentum_feature_set={"momentum": float(bar.get("momentum", 0.01))},
        liquidity_feature_set={"liq_score": float(bar.get("liq_score", 0.9))},
        market_structure_feature_set={"range_ratio": float(bar.get("range_ratio", 0.4))},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_REQUIRED,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
    )
    return with_computed_input_digest(context), l1_status, observed_l1_used


def _build_economic_research_warmup_required_skip_evidence_v1(
    *,
    replay_id: str,
    instrument_id: str,
    trading_epoch: int,
    config_digest: str,
    implementation_digest: str,
    input_digest: str,
    direction_state: EntryExitDirectionState,
) -> CanonicalTradingDecisionEvidenceV1:
    decision_id = derive_decision_id(
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        input_digest=input_digest,
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        market_context_ref="",
        scope_initialization_ref="",
        scope_event_ref="",
        bull_assessment_ref="",
        bear_assessment_ref="",
        state_switch_ref="",
        bull_survival_ref="",
        bear_survival_ref="",
        bull_suitability_ref="",
        bear_suitability_ref="",
        composition_result_ref="",
        entry_exit_policy_ref="",
        current_scope_ref="",
        next_scope_ref="",
        previous_direction_state=direction_state.value,
        next_direction_state=direction_state.value,
        selected_side=CompositionSelectedSide.NONE.value,
        selected_strategy_ref="",
        decision_outcome="observe",
        entry_or_exit_policy_ref="",
        reason_codes=(ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON,),
        decision_precedence_trace=(),
        component_versions=_default_component_versions(),
        policy_versions=_default_policy_versions(),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    return with_computed_evidence_semantic_digest(evidence)


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
    best_bid, best_ask, spread, outcome_l1_status, observed_l1_used = (
        _bind_economic_research_l1_fields_v1(
            bar=bar,
            mark_price=mark_price,
            research_execution_cost=research_execution_cost,
        )
    )

    warmup_status = _resolve_warmup_status(bar)
    volatility_estimate = _resolve_volatility_estimate_for_economic_research_wiring_v1(
        bar,
        warmup_status=warmup_status,
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
        volatility_estimate=volatility_estimate,
        trend_feature_set={"trend_slope": float(bar.get("trend_slope", 0.01))},
        momentum_feature_set={"momentum": float(bar.get("momentum", 0.01))},
        liquidity_feature_set={"liq_score": float(bar.get("liq_score", 0.9))},
        market_structure_feature_set={"range_ratio": float(bar.get("range_ratio", 0.4))},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=warmup_status,
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


def _advance_scope_cooldown_state_v1(
    state: ScopeCooldownStateV1,
) -> ScopeCooldownStateV1:
    if not state.active or state.remaining_epochs <= 0:
        return ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=state.policy_version,
        )
    remaining = state.remaining_epochs - 1
    return ScopeCooldownStateV1(
        active=remaining > 0,
        remaining_epochs=max(0, remaining),
        policy_version=state.policy_version,
    )


def _composition_direction_from_result_v1(
    composition_result: DoublePlayCompositionResultV1,
) -> CompositionDirectionState:
    if composition_result.selected_side is CompositionSelectedSide.LONG:
        return CompositionDirectionState.LONG
    if composition_result.selected_side is CompositionSelectedSide.SHORT:
        return CompositionDirectionState.SHORT
    return composition_result.previous_direction_state


def _derive_existing_position_side_and_venue_flat_v1(
    *,
    side_state: SideState,
    position_state: PositionState,
) -> tuple[ExistingPositionSide, bool]:
    if position_state is PositionState.FLAT_RECONCILED:
        return ExistingPositionSide.NONE, True
    open_states = {
        PositionState.OPEN_FULL,
        PositionState.OPEN_PARTIAL,
        PositionState.REDUCING_PARTIAL,
        PositionState.EXIT_PENDING,
    }
    if position_state in open_states:
        if side_state in (
            SideState.LONG_ACTIVE,
            SideState.LONG_ARMED,
            SideState.SWITCH_SHORT_TO_LONG_PENDING,
        ):
            return ExistingPositionSide.LONG, False
        if side_state in (
            SideState.SHORT_ACTIVE,
            SideState.SHORT_ARMED,
            SideState.SWITCH_LONG_TO_SHORT_PENDING,
        ):
            return ExistingPositionSide.SHORT, False
    return ExistingPositionSide.NONE, True


def build_initial_mv2_integrated_replay_bar_sequence_state_v1(
    *,
    trading_epoch: int,
) -> MV2IntegratedReplayBarSequenceStateV1:
    """Create the canonical MV2 integrated-replay initial state exactly once per wiring run."""
    return MV2IntegratedReplayBarSequenceStateV1(
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
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=0,
            last_evaluated_trading_epoch=trading_epoch - 1,
            last_signal_strength=0.0,
        ),
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
        now_tick=trading_epoch,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=None,
        dynamic_scope_rules=None,
        prior_mark_price=None,
    )


def project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1(
    *,
    intermediate: IntegratedOfflineReplayIntermediateV1,
    previous: MV2IntegratedReplayBarSequenceStateV1,
    next_trading_epoch: int,
) -> MV2IntegratedReplayBarSequenceStateV1:
    """Project canonical integrated replay intermediate outputs into the next bar input state."""
    side_state = SideState(intermediate.state_switch.next_side_state)
    direction_state = side_state_to_entry_exit_direction(side_state)
    scope_direction_state = scope_direction_from_side_state_v1(
        side_state,
        fallback=previous.scope_direction_state,
    )
    entry_exit = intermediate.entry_exit_decision
    composition = intermediate.composition_result
    existing_position_side, venue_flat = _derive_existing_position_side_and_venue_flat_v1(
        side_state=side_state,
        position_state=entry_exit.position_state,
    )
    scope_confirmation = intermediate.scope_event.next_confirmation_state
    # C3 carrier is the sole productive confirmation projection authority.
    directional_confirmation_progress = intermediate.directional_confirmation_progress_after
    if directional_confirmation_progress is None:
        directional_confirmation_progress = previous.directional_confirmation_progress
    # Legacy field retained as non-authority placeholder (never projected from assessments).
    directional_confirmation_state = previous.directional_confirmation_state
    return MV2IntegratedReplayBarSequenceStateV1(
        existing_scope=intermediate.current_scope,
        scope_direction_state=scope_direction_state,
        scope_confirmation_state=scope_confirmation,
        scope_cooldown_state=_advance_scope_cooldown_state_v1(previous.scope_cooldown_state),
        directional_confirmation_state=directional_confirmation_state,
        previous_composition_direction_state=_composition_direction_from_result_v1(composition),
        position_management_context=composition.position_management_context,
        last_evaluated_trading_epoch=next_trading_epoch - 1,
        side_state=side_state,
        direction_state=direction_state,
        position_state=entry_exit.position_state,
        reconciliation_state=entry_exit.reconciliation_state,
        trading_gate=previous.trading_gate,
        safety_mode=previous.safety_mode,
        existing_position_side=existing_position_side,
        venue_flat=venue_flat,
        cooldown_pass=previous.cooldown_pass,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        now_tick=next_trading_epoch,
        runtime_scope_state=intermediate.runtime_scope_state_after,
        runtime_scope_bound_instrument_id=intermediate.current_scope.instrument_id,
        dynamic_scope_rules=previous.dynamic_scope_rules,
        prior_mark_price=previous.prior_mark_price,
        directional_confirmation_progress=directional_confirmation_progress,
        confirmation_progress_session_id=previous.confirmation_progress_session_id,
        confirmation_progress_venue=previous.confirmation_progress_venue,
        confirmation_progress_instrument=previous.confirmation_progress_instrument,
    )


def apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1(
    sequence_state: MV2IntegratedReplayBarSequenceStateV1,
    feedback: BacktestEnginePositionFeedbackV1,
) -> MV2IntegratedReplayBarSequenceStateV1:
    """Overlay backtest **position observation** onto the next MV2 replay bar input.

    Fail-closed quarantine: does **not** overwrite ``side_state``, ``direction_state``,
    ``scope_direction_state``, or ``runtime_scope_state``. Bull/Bear / Switch authority
    remains ``transition_state``; RuntimeScopeState remains trailing SSOT.
    """
    position_state = coerce_backtest_position_state_v1(feedback.position_state)
    return replace(
        sequence_state,
        position_state=position_state,
        reconciliation_state=feedback.reconciliation_state,
        existing_position_side=feedback.existing_position_side,
        venue_flat=feedback.venue_flat,
        position_management_context=feedback.position_management_context,
    )


def _coerce_canonical_market_context_for_integrated_replay_v1(
    context: CanonicalMarketContextV1,
) -> CanonicalMarketContextV1:
    """Align enum identities with trading.master_v2 imports consumed by integrated replay."""
    from trading.master_v2.canonical_market_context_v1 import (
        BarFinalityStatus as IntegratedBarFinalityStatus,
        CanonicalMarketContextV1 as IntegratedCanonicalMarketContextV1,
        ClockTrustStatus as IntegratedClockTrustStatus,
        DataIntegrityStatus as IntegratedDataIntegrityStatus,
        WarmupStatus as IntegratedWarmupStatus,
    )
    from trading.master_v2.double_play_futures_input import (
        FuturesMarketType as IntegratedFuturesMarketType,
    )

    return IntegratedCanonicalMarketContextV1(
        context_id=context.context_id,
        instrument_id=context.instrument_id,
        market_type=IntegratedFuturesMarketType(context.market_type.value),
        trading_epoch=context.trading_epoch,
        market_event_time=context.market_event_time,
        decision_time=context.decision_time,
        bar_interval=context.bar_interval,
        bar_finality_status=IntegratedBarFinalityStatus(context.bar_finality_status.value),
        mark_price=context.mark_price,
        index_price=context.index_price,
        best_bid=context.best_bid,
        best_ask=context.best_ask,
        spread=context.spread,
        volume=context.volume,
        open_interest=context.open_interest,
        funding_rate=context.funding_rate,
        volatility_estimate=context.volatility_estimate,
        trend_feature_set=dict(context.trend_feature_set),
        momentum_feature_set=dict(context.momentum_feature_set),
        liquidity_feature_set=dict(context.liquidity_feature_set),
        market_structure_feature_set=dict(context.market_structure_feature_set),
        data_integrity_status=IntegratedDataIntegrityStatus(context.data_integrity_status.value),
        clock_trust_status=IntegratedClockTrustStatus(context.clock_trust_status.value),
        warmup_status=IntegratedWarmupStatus(context.warmup_status.value),
        feature_contract_version=context.feature_contract_version,
        input_digest=context.input_digest,
    )


def _coerce_scope_snapshot_for_integrated_replay_v1(
    scope: CanonicalScopeSnapshotV1,
) -> CanonicalScopeSnapshotV1:
    from trading.master_v2.canonical_scope_initialization_v1 import (
        CanonicalScopeLifecycleState as IntegratedScopeLifecycleState,
        CanonicalScopeSnapshotV1 as IntegratedCanonicalScopeSnapshotV1,
    )

    payload = {item.name: getattr(scope, item.name) for item in fields(scope)}
    payload["lifecycle_state"] = IntegratedScopeLifecycleState(scope.lifecycle_state.value)
    return IntegratedCanonicalScopeSnapshotV1(**payload)


def _coerce_replay_input_enums_for_integrated_replay_v1(
    replay_input: IntegratedOfflineReplayInputV1,
) -> IntegratedOfflineReplayInputV1:
    from trading.master_v2.canonical_market_context_v1 import (
        CanonicalMarketContextBindingStateV1 as IntegratedMarketContextBindingStateV1,
    )
    from trading.master_v2.canonical_scope_initialization_v1 import (
        CanonicalScopeInitializationPolicyV1 as IntegratedScopeInitializationPolicyV1,
        ScopeInitializationPrerequisitesV1 as IntegratedScopeInitializationPrerequisitesV1,
        ScopeReinitializationGuardV1 as IntegratedScopeReinitializationGuardV1,
    )
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        ScopeConfirmationStateV1 as IntegratedScopeConfirmationStateV1,
        ScopeCooldownStateV1 as IntegratedScopeCooldownStateV1,
        ScopeDirectionState as IntegratedScopeDirectionState,
        ScopeEventGeneratorPolicyV1 as IntegratedScopeEventGeneratorPolicyV1,
    )
    from trading.master_v2.directional_assessment_v1 import (
        DirectionalAssessmentPolicyV1 as IntegratedDirectionalAssessmentPolicyV1,
        DirectionalConfirmationStateV1 as IntegratedDirectionalConfirmationStateV1,
    )
    from trading.master_v2.double_play_composition_matrix_v1 import (
        CompositionDirectionState as IntegratedCompositionDirectionState,
        DoublePlayCompositionPolicyV1 as IntegratedDoublePlayCompositionPolicyV1,
        PositionManagementContext as IntegratedPositionManagementContext,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        DoublePlayEntryExitPolicyV0 as IntegratedDoublePlayEntryExitPolicyV0,
        EntryExitDirectionState as IntegratedEntryExitDirectionState,
        ExistingPositionSide as IntegratedExistingPositionSide,
        PolicySignalV0 as IntegratedPolicySignalV0,
        PositionState as IntegratedPositionState,
        ReconciliationState as IntegratedReconciliationState,
        SafetyMode as IntegratedSafetyMode,
        TradingGate as IntegratedTradingGate,
    )
    from trading.master_v2.double_play_state import SideState as IntegratedSideState
    from trading.master_v2 import integrated_offline_trading_logic_replay_v1 as integrated_replay_v1
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayPoliciesV1 as IntegratedOfflineReplayPoliciesV1Integrated,
    )
    from trading.master_v2.suitability_binding_v1 import (
        SuitabilityRankingPolicyV1 as IntegratedSuitabilityRankingPolicyV1,
        SuitabilityRegimeStatus as IntegratedSuitabilityRegimeStatus,
    )
    from trading.master_v2.survival_assessment_v1 import (
        SurvivalAssessmentPolicyV1 as IntegratedSurvivalAssessmentPolicyV1,
    )

    policies = replay_input.policies
    coerced_policies = IntegratedOfflineReplayPoliciesV1Integrated(
        scope_initialization=IntegratedScopeInitializationPolicyV1(
            min_scope_band=policies.scope_initialization.min_scope_band,
            max_scope_band=policies.scope_initialization.max_scope_band,
            policy_version=policies.scope_initialization.policy_version,
        ),
        scope_event_generator=IntegratedScopeEventGeneratorPolicyV1(
            hard_max_scope_distance=policies.scope_event_generator.hard_max_scope_distance,
            hard_max_adverse_distance=policies.scope_event_generator.hard_max_adverse_distance,
            hard_max_reversal_distance=policies.scope_event_generator.hard_max_reversal_distance,
            policy_version=policies.scope_event_generator.policy_version,
        ),
        directional=IntegratedDirectionalAssessmentPolicyV1(
            observe_signal_threshold=policies.directional.observe_signal_threshold,
            candidate_signal_threshold=policies.directional.candidate_signal_threshold,
            confirmation_signal_threshold=policies.directional.confirmation_signal_threshold,
            confirmation_epochs=policies.directional.confirmation_epochs,
            validity_epochs=policies.directional.validity_epochs,
            policy_version=policies.directional.policy_version,
        ),
        survival=IntegratedSurvivalAssessmentPolicyV1(
            min_net_edge=policies.survival.min_net_edge,
            min_volatility_survival_ratio=policies.survival.min_volatility_survival_ratio,
            min_sequence_survival_ratio=policies.survival.min_sequence_survival_ratio,
            min_drawdown_survival_ratio=policies.survival.min_drawdown_survival_ratio,
            min_liquidation_buffer_ratio=policies.survival.min_liquidation_buffer_ratio,
            validity_epochs=policies.survival.validity_epochs,
            policy_version=policies.survival.policy_version,
        ),
        suitability=IntegratedSuitabilityRankingPolicyV1(
            validity_epochs=policies.suitability.validity_epochs,
            no_match_status=policies.suitability.no_match_status,
            policy_version=policies.suitability.policy_version,
        ),
        composition=IntegratedDoublePlayCompositionPolicyV1(
            validity_epochs=policies.composition.validity_epochs,
            both_candidate_outcome=policies.composition.both_candidate_outcome,
            both_invalid_outcome=policies.composition.both_invalid_outcome,
            policy_version=policies.composition.policy_version,
        ),
        entry_exit=IntegratedDoublePlayEntryExitPolicyV0(
            policy_version=policies.entry_exit.policy_version,
        ),
    )
    scope_confirmation = replay_input.scope_confirmation_state
    coerced_scope_confirmation = IntegratedScopeConfirmationStateV1(
        candidate_kind=scope_confirmation.candidate_kind,
        candidate_count=scope_confirmation.candidate_count,
        last_evaluated_trading_epoch=scope_confirmation.last_evaluated_trading_epoch,
    )
    scope_cooldown = replay_input.scope_cooldown_state
    coerced_scope_cooldown = IntegratedScopeCooldownStateV1(
        active=scope_cooldown.active,
        remaining_epochs=scope_cooldown.remaining_epochs,
        policy_version=scope_cooldown.policy_version,
    )
    directional_confirmation = replay_input.directional_confirmation_state
    coerced_directional_confirmation = IntegratedDirectionalConfirmationStateV1(
        candidate_count=directional_confirmation.candidate_count,
        last_evaluated_trading_epoch=directional_confirmation.last_evaluated_trading_epoch,
        last_signal_strength=directional_confirmation.last_signal_strength,
    )

    def _signal(signal: PolicySignalV0) -> IntegratedPolicySignalV0:
        return IntegratedPolicySignalV0(triggered=signal.triggered)

    return integrated_replay_v1.build_integrated_offline_replay_input_v1(
        replay_id=replay_input.replay_id,
        instrument_id=replay_input.instrument_id,
        trading_epoch=replay_input.trading_epoch,
        canonical_market_context=_coerce_canonical_market_context_for_integrated_replay_v1(
            replay_input.canonical_market_context
        ),
        market_context_binding_state=IntegratedMarketContextBindingStateV1(),
        scope_prerequisites=IntegratedScopeInitializationPrerequisitesV1(
            required_window_complete=replay_input.scope_prerequisites.required_window_complete,
            instrument_metadata_valid=replay_input.scope_prerequisites.instrument_metadata_valid,
            finalized_market_context=replay_input.scope_prerequisites.finalized_market_context,
        ),
        scope_reinitialization_guard=IntegratedScopeReinitializationGuardV1(),
        existing_scope=(
            _coerce_scope_snapshot_for_integrated_replay_v1(replay_input.existing_scope)
            if replay_input.existing_scope is not None
            else None
        ),
        scope_direction_state=IntegratedScopeDirectionState(
            replay_input.scope_direction_state.value
        ),
        scope_confirmation_state=coerced_scope_confirmation,
        scope_cooldown_state=coerced_scope_cooldown,
        up_distance=replay_input.up_distance,
        adverse_exit_distance=replay_input.adverse_exit_distance,
        reversal_distance=replay_input.reversal_distance,
        confirmation_epochs=replay_input.confirmation_epochs,
        current_price=replay_input.current_price,
        price_path=replay_input.price_path,
        directional_confirmation_state=coerced_directional_confirmation,
        strategy_registry=replay_input.strategy_registry,
        regime_id=replay_input.regime_id,
        regime_status=IntegratedSuitabilityRegimeStatus(replay_input.regime_status.value),
        previous_composition_direction_state=IntegratedCompositionDirectionState(
            replay_input.previous_composition_direction_state.value
        ),
        position_management_context=IntegratedPositionManagementContext(
            replay_input.position_management_context.value
        ),
        last_evaluated_trading_epoch=replay_input.last_evaluated_trading_epoch,
        side_state=IntegratedSideState(replay_input.side_state.value),
        direction_state=IntegratedEntryExitDirectionState(replay_input.direction_state.value),
        position_state=IntegratedPositionState(replay_input.position_state.value),
        reconciliation_state=IntegratedReconciliationState(replay_input.reconciliation_state.value),
        trading_gate=IntegratedTradingGate(replay_input.trading_gate.value),
        safety_mode=IntegratedSafetyMode(replay_input.safety_mode.value),
        existing_position_side=IntegratedExistingPositionSide(
            replay_input.existing_position_side.value
        ),
        venue_flat=replay_input.venue_flat,
        cooldown_pass=replay_input.cooldown_pass,
        scope_adverse_exit_signal=_signal(replay_input.scope_adverse_exit_signal),
        profit_protection_signal=_signal(replay_input.profit_protection_signal),
        time_exit_signal=_signal(replay_input.time_exit_signal),
        strategy_invalidation_signal=_signal(replay_input.strategy_invalidation_signal),
        hard_risk_reduction_signal=_signal(replay_input.hard_risk_reduction_signal),
        safety_exit_signal=_signal(replay_input.safety_exit_signal),
        policies=coerced_policies,
        component_versions=dict(replay_input.component_versions),
        policy_versions=dict(replay_input.policy_versions),
        config_digest=replay_input.config_digest,
        implementation_digest=replay_input.implementation_digest,
        input_digest=replay_input.input_digest,
        expected_component_contracts=dict(replay_input.expected_component_contracts),
        context_reference=replay_input.context_reference,
        now_tick=replay_input.now_tick,
        strategy_suitability_agreement_material=(
            replay_input.strategy_suitability_agreement_material
        ),
        runtime_scope_state=getattr(replay_input, "runtime_scope_state", None),
        runtime_scope_bound_instrument_id=getattr(
            replay_input, "runtime_scope_bound_instrument_id", None
        ),
        dynamic_scope_rules=getattr(replay_input, "dynamic_scope_rules", None),
        explicit_runtime_scope_reset=bool(
            getattr(replay_input, "explicit_runtime_scope_reset", False)
        ),
    )


# Scale-invariant relative impulse for agreement-bound price_path projection.
# Matches existing directional fixture convention (anchor * 1.02), not absolute +5.
MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1 = 0.02


def resolve_agreement_bound_directional_cycle_v1(
    material: StrategySuitabilityAgreementMaterialV1 | None,
) -> int | None:
    """Return +1 / -1 only when agreement material carries a deterministic side.

    ENTRY_EXIT_EVENT uses only the explicit ``entry_side`` carrier:
    LONG → +1, SHORT → -1, NONE/missing → None. ``cycle_signal_value=+1`` is ENTRY
    only and never invents LONG. EXIT never invents a side.
    POSITIONAL_LS / POSITIONAL_LONG01 use ``cycle_signal_value`` as the side carrier.
    """
    if material is None:
        return None
    encoding = material.encoding_class
    cycle = int(material.cycle_signal_value)
    if encoding is StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1:
        if cycle in (-1, 1):
            return cycle
        return None
    if encoding is StrategySignalEncodingClassV1.POSITIONAL_LONG01_STATE_V1:
        if cycle == 1:
            return 1
        return None
    if encoding is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1:
        if material.event_kind is StrategyAgreementEventKindV1.EXIT or cycle == -1:
            return None
        if material.event_kind is StrategyAgreementEventKindV1.ENTRY or cycle == 1:
            entry_side = getattr(material, "entry_side", StrategyEntrySideCarrierV1.NONE)
            if entry_side is StrategyEntrySideCarrierV1.LONG:
                return 1
            if entry_side is StrategyEntrySideCarrierV1.SHORT:
                return -1
            return None
        return None
    if material.side_agreement is StrategySideAgreementV1.AGREE and cycle in (-1, 1):
        return cycle
    return None


def project_mv2_agreement_bound_price_path_v1(
    *,
    mark_price: float,
    material: StrategySuitabilityAgreementMaterialV1 | None,
    relative_impulse: float = MV2_AGREEMENT_BOUND_RELATIVE_IMPULSE_V1,
    prior_mark_price: float | None = None,
) -> tuple[float, float]:
    """Project a dimension-safe long-convention price_path for dual-lane DA.

    - No absolute mark+5 impulse.
    - Scale-invariant relative impulse when an explicitly resolved directional cycle
      is present (POSITIONAL_* cycle carrier or ENTRY_EXIT ``entry_side`` LONG/SHORT).
    - When strategy direction is unbound (OPTION_D ``entry_side=NONE`` / neutral):
      use the bar-to-bar market path ``(prior_mark, mark)`` when prior is bound.
      Dual-lane DA + ``transition_state`` + composition matrix own direction —
      never invent asymmetry from ``cycle_signal_value=+1`` alone.
    - First bar / missing prior → flat ``(mark, mark)`` fail-closed.
    """
    mark = float(mark_price)
    if not math.isfinite(mark) or mark <= 0.0:
        raise ValueError("agreement_bound_price_path_mark_invalid")
    impulse = float(relative_impulse)
    if not math.isfinite(impulse) or impulse <= 0.0:
        raise ValueError("agreement_bound_price_path_impulse_invalid")
    direction = resolve_agreement_bound_directional_cycle_v1(material)
    if direction is not None:
        if direction > 0:
            return (mark, mark * (1.0 + impulse))
        return (mark, mark * (1.0 - impulse))
    if prior_mark_price is not None:
        prior = float(prior_mark_price)
        if not math.isfinite(prior) or prior <= 0.0:
            raise ValueError("agreement_bound_price_path_prior_mark_invalid")
        return (prior, mark)
    return (mark, mark)


def project_directional_confirmation_state_from_assessments_v1(
    *,
    bull_assessment: DirectionalAssessmentV1,
    bear_assessment: DirectionalAssessmentV1,
    previous: DirectionalConfirmationStateV1,
    next_trading_epoch: int,
    candidate_signal_threshold: float,
) -> DirectionalConfirmationStateV1:
    """LEGACY_NON_AUTHORITY / QUARANTINED.

    Historical lossy Bull/Bear merge projector. Must not be used as productive
    confirmation authority after C3. Retained only so static imports and older
    research helpers do not break; productive bar projection uses the C3 carrier.
    """
    raise RuntimeError(
        "LEGACY_LOSSY_CROSS_SIDE_PROJECTOR_AUTHORITY_FORBIDDEN:"
        "use_DirectionalConfirmationSideStateCarrierV1_from_C3_intermediate"
    )


def _legacy_project_directional_confirmation_state_from_assessments_v1_quarantined(
    *,
    bull_assessment: DirectionalAssessmentV1,
    bear_assessment: DirectionalAssessmentV1,
    previous: DirectionalConfirmationStateV1,
    next_trading_epoch: int,
    candidate_signal_threshold: float,
) -> DirectionalConfirmationStateV1:
    """Internal quarantine copy — not reachable from productive projection."""
    threshold = float(candidate_signal_threshold)
    active = [
        assessment
        for assessment in (bull_assessment, bear_assessment)
        if assessment.status
        in {
            DirectionalAssessmentStatus.CANDIDATE,
            DirectionalAssessmentStatus.CONFIRMED,
        }
    ]
    if active:
        chosen = max(active, key=lambda item: float(item.signal_strength))
        strength = float(chosen.signal_strength)
        if strength >= threshold and previous.last_signal_strength >= threshold:
            count = int(previous.candidate_count) + 1
        elif strength >= threshold:
            count = 1
        else:
            count = 0
    else:
        strength = max(
            float(bull_assessment.signal_strength),
            float(bear_assessment.signal_strength),
            0.0,
        )
        count = 0
    return DirectionalConfirmationStateV1(
        candidate_count=max(0, int(count)),
        last_evaluated_trading_epoch=int(next_trading_epoch) - 1,
        last_signal_strength=float(strength),
    )


# Research-wiring scope distances: generator contract expects absolute price units
# equal to mark units. Legacy hardcoded 120/60/90 were ETH-fixture-scale absolutes
# (UNIT_MISMATCH on sub-1.0 research marks). Bind relative BPS, convert once.
# Legacy relation preserved: up:adverse:reversal = 120:60:90 = 1:0.5:0.75.
_MV2_RESEARCH_SCOPE_UP_DISTANCE_BPS = 100.0  # 1% of current mark
_MV2_RESEARCH_SCOPE_ADVERSE_TO_UP_RATIO = 60.0 / 120.0  # legacy 60/120
_MV2_RESEARCH_SCOPE_REVERSAL_TO_UP_RATIO = 90.0 / 120.0  # legacy 90/120
_MV2_RESEARCH_SCOPE_BPS_PER_UNIT = 10_000.0


@dataclass(frozen=True)
class MV2ResearchScopeDistancesAbsoluteV1:
    """Absolute price distances for scope-event generator input (mark units)."""

    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float


def compute_mv2_research_scope_distances_absolute_from_mark_v1(
    mark_price: float,
) -> MV2ResearchScopeDistancesAbsoluteV1:
    """Scale research scope distances from current mark (BPS → absolute price).

    Fail-closed on non-finite or non-positive mark. Never falls back to legacy
    absolute 120/60/90 and never invents direction / SideState.
    """
    _fail_closed(mark_price is None, "mv2_research_scope_distance_mark_missing")
    try:
        mark = float(mark_price)
    except (TypeError, ValueError) as exc:
        raise ValueError("mv2_research_scope_distance_mark_invalid") from exc
    _fail_closed(not math.isfinite(mark), "mv2_research_scope_distance_mark_non_finite")
    _fail_closed(mark <= 0.0, "mv2_research_scope_distance_mark_non_positive")
    up = mark * (_MV2_RESEARCH_SCOPE_UP_DISTANCE_BPS / _MV2_RESEARCH_SCOPE_BPS_PER_UNIT)
    adverse = up * _MV2_RESEARCH_SCOPE_ADVERSE_TO_UP_RATIO
    reversal = up * _MV2_RESEARCH_SCOPE_REVERSAL_TO_UP_RATIO
    _fail_closed(not math.isfinite(up) or up <= 0.0, "mv2_research_scope_up_distance_invalid")
    _fail_closed(
        not math.isfinite(adverse) or adverse <= 0.0,
        "mv2_research_scope_adverse_distance_invalid",
    )
    _fail_closed(
        not math.isfinite(reversal) or reversal <= 0.0,
        "mv2_research_scope_reversal_distance_invalid",
    )
    _fail_closed(adverse > reversal, "mv2_research_scope_adverse_exceeds_reversal")
    return MV2ResearchScopeDistancesAbsoluteV1(
        up_distance=up,
        adverse_exit_distance=adverse,
        reversal_distance=reversal,
    )


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
    sequence_state: MV2IntegratedReplayBarSequenceStateV1,
    strategy_suitability_agreement_material: Optional[
        StrategySuitabilityAgreementMaterialV1
    ] = None,
) -> IntegratedOfflineReplayInputV1:
    mark_price = float(context.mark_price)
    price_path = project_mv2_agreement_bound_price_path_v1(
        mark_price=mark_price,
        material=strategy_suitability_agreement_material,
        prior_mark_price=sequence_state.prior_mark_price,
    )
    scope_distances = compute_mv2_research_scope_distances_absolute_from_mark_v1(mark_price)
    return build_integrated_offline_replay_input_v1(
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
        existing_scope=sequence_state.existing_scope,
        scope_direction_state=sequence_state.scope_direction_state,
        scope_confirmation_state=sequence_state.scope_confirmation_state,
        scope_cooldown_state=sequence_state.scope_cooldown_state,
        up_distance=scope_distances.up_distance,
        adverse_exit_distance=scope_distances.adverse_exit_distance,
        reversal_distance=scope_distances.reversal_distance,
        confirmation_epochs=2,
        current_price=mark_price,
        price_path=price_path,
        directional_confirmation_state=sequence_state.directional_confirmation_state,
        strategy_registry=strategy_registry,
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_composition_direction_state=sequence_state.previous_composition_direction_state,
        position_management_context=sequence_state.position_management_context,
        last_evaluated_trading_epoch=sequence_state.last_evaluated_trading_epoch,
        side_state=sequence_state.side_state,
        direction_state=sequence_state.direction_state,
        position_state=sequence_state.position_state,
        reconciliation_state=sequence_state.reconciliation_state,
        trading_gate=sequence_state.trading_gate,
        safety_mode=sequence_state.safety_mode,
        existing_position_side=sequence_state.existing_position_side,
        venue_flat=sequence_state.venue_flat,
        cooldown_pass=sequence_state.cooldown_pass,
        scope_adverse_exit_signal=sequence_state.scope_adverse_exit_signal,
        profit_protection_signal=sequence_state.profit_protection_signal,
        time_exit_signal=sequence_state.time_exit_signal,
        strategy_invalidation_signal=sequence_state.strategy_invalidation_signal,
        hard_risk_reduction_signal=sequence_state.hard_risk_reduction_signal,
        safety_exit_signal=sequence_state.safety_exit_signal,
        policies=_default_policies(),
        component_versions=_default_component_versions(),
        policy_versions=_default_policy_versions(),
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        input_digest=input_digest,
        expected_component_contracts=_default_component_versions(),
        context_reference=f"mv2-research-{trading_epoch}",
        now_tick=sequence_state.now_tick,
        strategy_suitability_agreement_material=strategy_suitability_agreement_material,
        runtime_scope_state=sequence_state.runtime_scope_state,
        runtime_scope_bound_instrument_id=sequence_state.runtime_scope_bound_instrument_id,
        dynamic_scope_rules=sequence_state.dynamic_scope_rules,
        explicit_runtime_scope_reset=False,
        directional_confirmation_progress=sequence_state.directional_confirmation_progress,
        confirmation_progress_session_id=sequence_state.confirmation_progress_session_id,
        confirmation_progress_venue=sequence_state.confirmation_progress_venue,
        confirmation_progress_instrument=sequence_state.confirmation_progress_instrument,
    )


def _resolve_reconciliation_backtest_state_file_record_v1(
    binding: ReconciliationBacktestStateFileBindingConfigV1 | None,
) -> ReconciliationBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.reconciliation_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_reconciliation_backtest_state_file_digest_v0,
            )

            verify_reconciliation_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_reconciliation_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("reconciliation_backtest_state_file_missing")
    return None


def _resolve_capital_risk_sizing_backtest_state_file_record_v1(
    binding: CapitalRiskSizingBacktestStateFileBindingConfigV1 | None,
) -> CapitalRiskSizingBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_capital_risk_sizing_backtest_state_file_digest_v0,
            )

            verify_capital_risk_sizing_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_capital_risk_sizing_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("capital_risk_sizing_backtest_state_file_missing")
    return None


def _resolve_canonical_order_intent_backtest_state_file_record_v1(
    binding: CanonicalOrderIntentBacktestStateFileBindingConfigV1 | None,
) -> CanonicalOrderIntentBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_canonical_order_intent_backtest_state_file_digest_v0,
            )

            verify_canonical_order_intent_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_canonical_order_intent_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("canonical_order_intent_backtest_state_file_missing")
    return None


def _resolve_safety_kernel_backtest_state_file_record_v1(
    binding: SafetyKernelBacktestStateFileBindingConfigV1 | None,
) -> SafetyKernelBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_safety_kernel_backtest_state_file_digest_v0,
            )

            verify_safety_kernel_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_safety_kernel_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("safety_kernel_backtest_state_file_missing")
    return None


def _resolve_promotion_gate_backtest_state_file_record_v1(
    binding: PromotionGateBacktestStateFileBindingConfigV1 | None,
) -> PromotionGateBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.promotion_gate_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_promotion_gate_backtest_state_file_digest_v0,
            )

            verify_promotion_gate_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_promotion_gate_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("promotion_gate_backtest_state_file_missing")
    return None


def _resolve_ai_observability_backtest_state_file_record_v1(
    binding: AiObservabilityBacktestStateFileBindingConfigV1 | None,
) -> AiObservabilityBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.ai_observability_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_ai_observability_backtest_state_file_digest_v0,
            )

            verify_ai_observability_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_ai_observability_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("ai_observability_backtest_state_file_missing")
    return None


def _resolve_feedback_learning_backtest_state_file_record_v1(
    binding: FeedbackLearningBacktestStateFileBindingConfigV1 | None,
) -> FeedbackLearningBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.feedback_learning_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_feedback_learning_backtest_state_file_digest_v0,
            )

            verify_feedback_learning_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_feedback_learning_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("feedback_learning_backtest_state_file_missing")
    return None


def _resolve_killswitch_backtest_state_file_record_v1(
    binding: KillSwitchBacktestStateFileBindingConfigV1 | None,
) -> KillSwitchBacktestStateFileRecordV0 | None:
    if binding is None:
        return None
    if binding.state_file_record is not None:
        record = binding.state_file_record
        if binding.expected_state_file_digest_ref:
            from src.trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
                verify_killswitch_backtest_state_file_digest_v0,
            )

            verify_killswitch_backtest_state_file_digest_v0(
                record,
                expected_digest_ref=binding.expected_state_file_digest_ref,
            )
        return record
    if binding.state_file_path is not None:
        return load_killswitch_backtest_state_file_record_v0(
            binding.state_file_path,
            expected_digest_ref=binding.expected_state_file_digest_ref,
        )
    if binding.require_state_file:
        raise ValueError("killswitch_backtest_state_file_missing")
    return None


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
    killswitch_state_file_binding: KillSwitchBacktestStateFileBindingConfigV1 | None = None,
    reconciliation_state_file_binding: ReconciliationBacktestStateFileBindingConfigV1 | None = None,
    capital_risk_sizing_state_file_binding: (
        CapitalRiskSizingBacktestStateFileBindingConfigV1 | None
    ) = None,
    canonical_order_intent_state_file_binding: (
        CanonicalOrderIntentBacktestStateFileBindingConfigV1 | None
    ) = None,
    safety_kernel_state_file_binding: SafetyKernelBacktestStateFileBindingConfigV1 | None = None,
    promotion_gate_state_file_binding: PromotionGateBacktestStateFileBindingConfigV1 | None = None,
    ai_observability_state_file_binding: AiObservabilityBacktestStateFileBindingConfigV1
    | None = None,
    feedback_learning_state_file_binding: FeedbackLearningBacktestStateFileBindingConfigV1
    | None = None,
    backtest_engine_signal_source: str | None = None,
    expected_mv2_replay_signal_digest: Optional[str] = None,
    allow_legacy_raw_signal_research_engine_source: bool = False,
    system_economic_evidence_requested: bool | None = None,
    observational_bar_hook: Callable[..., None] | None = None,
    observational_panel_member_instrument_id: str | None = None,
) -> MV2ResearchWiringResultV1:
    _fail_closed(bars.empty, "bars_empty")
    _ensure_supported_instrument(instrument_id)
    _ensure_no_lookahead(bars)

    resolved_engine_signal_source = resolve_mv2_research_engine_signal_source_v1(
        explicit_source=backtest_engine_signal_source,
        cfg=cfg,
    )
    # C8 lock: configured_strategy cannot override replay as system engine source.
    # Legacy raw-signal research overrides require an explicit non-authoritative grant.
    if resolved_engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        system_evidence = (
            True
            if system_economic_evidence_requested is None
            else bool(system_economic_evidence_requested)
        )
        if not allow_legacy_raw_signal_research_engine_source:
            raise StrategySignalBindingError(
                "legacy_raw_signal_path_system_economic_evidence_blocked"
            )
        assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1(
            path_classification=RUN_BACKTEST_PATH_CLASSIFICATION,
            system_economic_evidence_requested=system_evidence,
        )
    else:
        # Canonical system MV2 wiring path classification (replay engine authority).
        if CANONICAL_MV2_SYSTEM_PATH_CLASSIFICATION != CANONICAL_SYSTEM_REPLAY:
            raise StrategySignalBindingError(
                "legacy_raw_signal_path_system_economic_evidence_blocked"
            )

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
    killswitch_state_file_record = _resolve_killswitch_backtest_state_file_record_v1(
        killswitch_state_file_binding
    )
    reconciliation_state_file_record = _resolve_reconciliation_backtest_state_file_record_v1(
        reconciliation_state_file_binding
    )
    capital_risk_sizing_state_file_record = (
        _resolve_capital_risk_sizing_backtest_state_file_record_v1(
            capital_risk_sizing_state_file_binding
        )
    )
    canonical_order_intent_state_file_record = (
        _resolve_canonical_order_intent_backtest_state_file_record_v1(
            canonical_order_intent_state_file_binding
        )
    )
    safety_kernel_state_file_record = _resolve_safety_kernel_backtest_state_file_record_v1(
        safety_kernel_state_file_binding
    )
    promotion_gate_state_file_record = _resolve_promotion_gate_backtest_state_file_record_v1(
        promotion_gate_state_file_binding
    )
    ai_observability_state_file_record = _resolve_ai_observability_backtest_state_file_record_v1(
        ai_observability_state_file_binding
    )
    feedback_learning_state_file_record = _resolve_feedback_learning_backtest_state_file_record_v1(
        feedback_learning_state_file_binding
    )
    if canonical_order_intent_state_file_record is not None and (
        capital_risk_sizing_state_file_record is None
    ):
        raise ValueError("canonical_order_intent_backtest_state_file_requires_sizing_state_file")
    killswitch_has_existing_position = (
        killswitch_state_file_binding.has_existing_position
        if killswitch_state_file_binding is not None
        else False
    )

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

    position_feedback_bound = resolved_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
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

    backtest_engine: BacktestEngine | None = None
    bar_loop_state: LegacyRealisticBarLoopStateV1 | None = None
    if position_feedback_bound:
        # Bind short-capable consumer; bar loop still uses step_legacy with
        # honor_mapped_short_entry so mapped -1 opens shorts (not exit-only no-op).
        backtest_engine = BacktestEngine(
            use_execution_pipeline=True,
            risk_limits=build_mv2_research_risk_limits_v1(cfg),
        )
        backtest_engine.config = engine_cfg
        backtest_engine.data = bars

    outcomes: list[MV2ReplayBarOutcomeV1] = []
    replay_signals: list[int] = []
    sequence_state: MV2IntegratedReplayBarSequenceStateV1 | None = None
    decision_funnel_accumulator = DecisionFunnelAccumulatorV0()
    economic_research_profile = (
        effective_profile.dataset_profile is DatasetProfileV1.ECONOMIC_RESEARCH_V1
    )
    panel_member_id_for_hook = (
        observational_panel_member_instrument_id
        if observational_panel_member_instrument_id is not None
        else instrument_id
    )

    def _emit_observational_bar_hook(
        *,
        trading_epoch: int,
        bar_row: pd.Series,
        warmup_status_value: str,
        warmup_skipped: bool,
        context_obj: CanonicalMarketContextV1,
        agreement_material_obj: StrategySuitabilityAgreementMaterialV1 | None,
        replay_result_obj: Any | None,
        replay_input_obj: Any | None,
        mapped_signal: int,
        replay_input_built: bool,
        decision_authority_reached: bool,
        fail_reasons: tuple[str, ...],
    ) -> None:
        if observational_bar_hook is None:
            return
        raw_signal = 0
        try:
            raw_signal = int(engine_signal_series.iloc[trading_epoch])
        except Exception:  # noqa: BLE001
            raw_signal = 0
        intermediate_obj = None
        decision_outcome_value = None
        evidence_codes: tuple[str, ...] = ()
        if replay_result_obj is not None:
            intermediate_obj = getattr(replay_result_obj, "intermediate", None)
            evidence_obj = getattr(replay_result_obj, "evidence", None)
            if evidence_obj is not None:
                decision_outcome_value = (
                    str(getattr(evidence_obj, "decision_outcome", "") or "") or None
                )
                evidence_codes = tuple(getattr(evidence_obj, "reason_codes", ()) or ())
        price_path_value = None
        regime_id_value = None
        eligible_strategy_count_value = None
        regime_wildcard_matched_value = None
        if replay_input_obj is not None:
            price_path_value = getattr(replay_input_obj, "price_path", None)
            regime_id_value = getattr(replay_input_obj, "regime_id", None)
        if replay_result_obj is not None and intermediate_obj is not None:
            bull_suit = getattr(intermediate_obj, "bull_suitability", None)
            bear_suit = getattr(intermediate_obj, "bear_suitability", None)
            bull_ids = tuple(getattr(bull_suit, "eligible_strategy_ids", ()) or ())
            bear_ids = tuple(getattr(bear_suit, "eligible_strategy_ids", ()) or ())
            eligible_strategy_count_value = len(set(bull_ids) | set(bear_ids))
        if regime_id_value is not None:
            from trading.master_v2.suitability_binding_v1 import regime_wildcard_matched_v1

            regime_wildcard_matched_value = any(
                regime_wildcard_matched_v1(entry.supported_regime_ids, str(regime_id_value))
                for entry in suitability_registry.entries
            )
        observational_bar_hook(
            trading_epoch=trading_epoch,
            bar_timestamp=str(pd.Timestamp(bar_row.name)),
            instrument_id=instrument_id,
            panel_member_instrument_id=panel_member_id_for_hook,
            raw_strategy_signal=raw_signal,
            warmup_status=warmup_status_value,
            warmup_skipped=warmup_skipped,
            context_id=str(getattr(context_obj, "context_id", "")),
            context_input_digest=str(getattr(context_obj, "input_digest", "")),
            agreement_material=agreement_material_obj,
            intermediate=intermediate_obj,
            decision_outcome=decision_outcome_value,
            evidence_reason_codes=evidence_codes,
            mapped_position_signal=int(mapped_signal),
            price_path=price_path_value,
            regime_id=regime_id_value,
            eligible_strategy_count=eligible_strategy_count_value,
            regime_wildcard_matched=regime_wildcard_matched_value,
            fail_reasons=fail_reasons,
            replay_input_built=replay_input_built,
            decision_authority_reached=decision_authority_reached,
        )

    if economic_research_profile:
        _fail_closed(
            not any(
                _resolve_warmup_status(row) is WarmupStatus.WARMUP_COMPLETE
                for _, row in bars.iterrows()
            ),
            ECONOMIC_RESEARCH_NO_WARMUP_COMPLETE_BAR_REASON,
        )
    for i, (_, row) in enumerate(bars.iterrows()):
        if sequence_state is None:
            sequence_state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(
                trading_epoch=i,
            )
        if position_feedback_bound and i > 0 and bar_loop_state is not None:
            feedback = capture_backtest_engine_position_feedback_v1(
                state=bar_loop_state,
                feedback_source_bar_epoch=i - 1,
            )
            sequence_state = apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1(
                sequence_state,
                feedback,
            )
        bar_warmup_status = _resolve_warmup_status(row)
        if economic_research_profile:
            if bar_warmup_status is WarmupStatus.WARMUP_INVALID:
                _fail_closed(True, ECONOMIC_RESEARCH_WARMUP_INVALID_BLOCK_REASON)
            if bar_warmup_status is WarmupStatus.WARMUP_REQUIRED:
                context, l1_status, observed_l1_used = (
                    _bind_economic_research_warmup_observation_bar_v1(
                        bar=row,
                        instrument_id=instrument_id,
                        trading_epoch=i,
                        research_execution_cost=research_execution_cost,
                    )
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
                        "warmup_skip_reason": ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON,
                    }
                )
                skip_evidence = _build_economic_research_warmup_required_skip_evidence_v1(
                    replay_id=replay_id,
                    instrument_id=instrument_id,
                    trading_epoch=i,
                    config_digest=config_digest,
                    implementation_digest=implementation_digest,
                    input_digest=input_digest,
                    direction_state=sequence_state.direction_state,
                )
                decision_funnel_accumulator.block_reason_counts[
                    ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON
                ] += 1
                signal = 0
                if position_feedback_bound:
                    if backtest_engine is None:
                        raise ValueError("backtest_engine_position_feedback_engine_missing")
                    if bar_loop_state is None:
                        bar_loop_state = init_legacy_realistic_bar_loop_state_v1(
                            backtest_engine,
                            strategy_params=strategy_params,
                        )
                    bar_loop_state = step_legacy_realistic_bar_v1(
                        backtest_engine,
                        bar_loop_state,
                        bar=row,
                        signal=signal,
                        symbol=instrument_id,
                        effective_cost=effective_cost,
                        honor_mapped_short_entry=True,
                    )
                outcomes.append(
                    MV2ReplayBarOutcomeV1(
                        trading_epoch=i,
                        context=context,
                        evidence=skip_evidence,
                        position_signal=signal,
                        replay_pass=False,
                        fail_reasons=(ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON,),
                        l1_observation_status=l1_status,
                        observed_l1_used=observed_l1_used,
                    )
                )
                replay_signals.append(signal)
                sequence_state = replace(
                    sequence_state,
                    prior_mark_price=float(context.mark_price),
                )
                _emit_observational_bar_hook(
                    trading_epoch=i,
                    bar_row=row,
                    warmup_status_value=str(bar_warmup_status.value),
                    warmup_skipped=True,
                    context_obj=context,
                    agreement_material_obj=None,
                    replay_result_obj=None,
                    replay_input_obj=None,
                    mapped_signal=signal,
                    replay_input_built=False,
                    decision_authority_reached=False,
                    fail_reasons=(ECONOMIC_RESEARCH_WARMUP_REQUIRED_SKIP_REASON,),
                )
                continue
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
        try:
            agreement_material = normalize_strategy_signal_to_suitability_agreement_material_v1(
                strategy_binding,
                instrument_id=instrument_id,
                trading_epoch=i,
                expected_configured_strategy_id=strategy_id,
            )
        except StrategySuitabilityAgreementErrorV1 as exc:
            raise ValueError(
                f"missing_agreement_material_on_canonical_strategy_path:{exc}"
            ) from exc
        replay_input = _coerce_replay_input_enums_for_integrated_replay_v1(
            _build_replay_input(
                replay_id=replay_id,
                instrument_id=instrument_id,
                trading_epoch=i,
                context=context,
                strategy_registry=suitability_registry,
                config_digest=config_digest,
                implementation_digest=implementation_digest,
                input_digest=input_digest,
                sequence_state=sequence_state,
                strategy_suitability_agreement_material=agreement_material,
            )
        )
        replay_result = run_integrated_offline_trading_logic_replay_v1(replay_input)
        decision_funnel_accumulator.accumulate_from_replay(
            intermediate=replay_result.intermediate,
            evidence_reason_codes=replay_result.evidence.reason_codes,
        )
        if replay_result.intermediate is not None:
            sequence_state = project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1(
                intermediate=replay_result.intermediate,
                previous=sequence_state,
                next_trading_epoch=i + 1,
            )
        # Trail prior mark for next-bar market-context price_path (OPTION_D).
        sequence_state = replace(
            sequence_state,
            prior_mark_price=float(context.mark_price),
        )
        signal = map_decision_evidence_to_position_signal_v1(replay_result.evidence)
        killswitch_evidence: KillSwitchBoundaryBacktestStateFileEvidenceV0 | None = None
        if killswitch_state_file_record is not None:
            killswitch_evidence = bind_killswitch_boundary_backtest_state_file_evidence_v0(
                replay_result.evidence,
                state_file=killswitch_state_file_record,
            )
            signal = apply_backtest_killswitch_exposure_gate_v0(
                signal,
                evidence=killswitch_evidence,
                has_existing_position=killswitch_has_existing_position,
            )
        reconciliation_evidence: ReconciliationBoundaryBacktestStateFileEvidenceV0 | None = None
        if reconciliation_state_file_record is not None:
            reconciliation_evidence = bind_reconciliation_boundary_backtest_state_file_evidence_v0(
                replay_result.evidence,
                state_file=reconciliation_state_file_record,
            )
            signal = apply_backtest_reconciliation_exposure_gate_v0(
                signal,
                evidence=reconciliation_evidence,
            )
        capital_risk_sizing_evidence: (
            CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0 | None
        ) = None
        if capital_risk_sizing_state_file_record is not None:
            capital_risk_sizing_evidence = (
                bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0(
                    replay_result.evidence,
                    state_file=capital_risk_sizing_state_file_record,
                )
            )
            signal = apply_backtest_capital_risk_sizing_exposure_gate_v0(
                signal,
                evidence=capital_risk_sizing_evidence,
            )
        canonical_order_intent_evidence: (
            CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0 | None
        ) = None
        if canonical_order_intent_state_file_record is not None:
            if capital_risk_sizing_evidence is None:
                raise ValueError(
                    "canonical_order_intent_backtest_state_file_sizing_evidence_missing"
                )
            canonical_order_intent_evidence = (
                bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0(
                    replay_result.evidence,
                    state_file=canonical_order_intent_state_file_record,
                    sizing_evidence=capital_risk_sizing_evidence,
                )
            )
            signal = apply_backtest_canonical_order_intent_exposure_gate_v0(
                signal,
                evidence=canonical_order_intent_evidence,
            )
        safety_kernel_evidence: SafetyKernelBoundaryBacktestStateFileEvidenceV0 | None = None
        if safety_kernel_state_file_record is not None:
            safety_kernel_evidence = bind_safety_kernel_boundary_backtest_state_file_evidence_v0(
                replay_result.evidence,
                state_file=safety_kernel_state_file_record,
            )
            signal = apply_backtest_safety_kernel_exposure_gate_v0(
                signal,
                evidence=safety_kernel_evidence,
            )
        if killswitch_evidence is not None and safety_kernel_evidence is not None:
            killswitch_evidence = replace(
                killswitch_evidence,
                no_order_without_safety_and_killswitch_pass_represented_in_backtest=(
                    killswitch_evidence.no_order_without_safety_and_killswitch_pass_represented_in_backtest
                    and safety_kernel_evidence.no_order_without_safety_pass_represented
                ),
            )
        promotion_gate_evidence: PromotionGateBoundaryBacktestStateFileEvidenceV0 | None = None
        if promotion_gate_state_file_record is not None:
            promotion_gate_evidence = bind_promotion_gate_boundary_backtest_state_file_evidence_v0(
                replay_result.evidence,
                state_file=promotion_gate_state_file_record,
            )
            signal = apply_backtest_promotion_gate_exposure_gate_v0(
                signal,
                evidence=promotion_gate_evidence,
            )
        ai_observability_evidence: AiObservabilityBoundaryBacktestStateFileEvidenceV0 | None = None
        if ai_observability_state_file_record is not None:
            ai_observability_evidence = (
                bind_ai_observability_boundary_backtest_state_file_evidence_v0(
                    replay_result.evidence,
                    state_file=ai_observability_state_file_record,
                )
            )
            signal = apply_backtest_ai_observability_exposure_gate_v0(
                signal,
                evidence=ai_observability_evidence,
            )
        feedback_learning_evidence: FeedbackLearningBoundaryBacktestStateFileEvidenceV0 | None = (
            None
        )
        if feedback_learning_state_file_record is not None:
            feedback_learning_evidence = (
                bind_feedback_learning_boundary_backtest_state_file_evidence_v0(
                    replay_result.evidence,
                    state_file=feedback_learning_state_file_record,
                )
            )
            signal = apply_backtest_feedback_learning_exposure_gate_v0(
                signal,
                evidence=feedback_learning_evidence,
            )
        if context.warmup_status is not WarmupStatus.WARMUP_COMPLETE:
            signal = 0
        if position_feedback_bound:
            if backtest_engine is None:
                raise ValueError("backtest_engine_position_feedback_engine_missing")
            if bar_loop_state is None:
                bar_loop_state = init_legacy_realistic_bar_loop_state_v1(
                    backtest_engine,
                    strategy_params=strategy_params,
                )
            bar_loop_state = step_legacy_realistic_bar_v1(
                backtest_engine,
                bar_loop_state,
                bar=row,
                signal=signal,
                symbol=instrument_id,
                effective_cost=effective_cost,
                honor_mapped_short_entry=True,
            )
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
                killswitch_backtest_state_file_evidence=killswitch_evidence,
                reconciliation_backtest_state_file_evidence=reconciliation_evidence,
                capital_risk_sizing_backtest_state_file_evidence=capital_risk_sizing_evidence,
                canonical_order_intent_backtest_state_file_evidence=canonical_order_intent_evidence,
                safety_kernel_backtest_state_file_evidence=safety_kernel_evidence,
                promotion_gate_backtest_state_file_evidence=promotion_gate_evidence,
                ai_observability_backtest_state_file_evidence=ai_observability_evidence,
                feedback_learning_backtest_state_file_evidence=feedback_learning_evidence,
            )
        )
        replay_signals.append(signal)
        _emit_observational_bar_hook(
            trading_epoch=i,
            bar_row=row,
            warmup_status_value=str(context.warmup_status.value),
            warmup_skipped=False,
            context_obj=context,
            agreement_material_obj=agreement_material,
            replay_result_obj=replay_result,
            replay_input_obj=replay_input,
            mapped_signal=signal,
            replay_input_built=True,
            decision_authority_reached=True,
            fail_reasons=tuple(replay_result.fail_reasons),
        )

    # Preserve the canonical bars.index identity (dtype/unit, tz, name, order).
    # Rebuilding via pd.DatetimeIndex([pd.Timestamp(...), ...]) can promote
    # datetime64[us, UTC] -> datetime64[ns, UTC] and fail Index.equals.
    mv2_replay_series = pd.Series(replay_signals, index=bars.index, dtype=int)
    mv2_replay_digest = compute_strategy_signal_digest_v1(
        mv2_replay_series,
        strategy_id=strategy_id,
        strategy_params_digest=_stable_digest(
            {"source": MV2_REPLAY_SIGNAL_SOURCE, "owner": MV2_RESEARCH_WIRING_OWNER}
        ),
    )
    mv2_replay_nonzero = int((mv2_replay_series != 0).sum())

    if resolved_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY:
        try:
            engine_signal_series, engine_provenance = validate_mv2_replay_engine_signal_contract_v1(
                mv2_replay_series,
                bars_index=bars.index,
                strategy_id=strategy_id,
                mv2_replay_signal_digest=mv2_replay_digest,
                expected_mv2_replay_signal_digest=expected_mv2_replay_signal_digest or "",
            )
        except StrategySignalBindingError as exc:
            raise ValueError(f"mv2_replay_engine_signal_binding_failed:{exc}") from exc
        backtest_engine_signal_digest = mv2_replay_digest
    elif resolved_engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        engine_provenance = strategy_binding.provenance
        backtest_engine_signal_digest = engine_provenance.engine_signal_digest
    else:
        raise ValueError(
            f"backtest_engine_signal_source_unsupported:{resolved_engine_signal_source}"
        )

    def _signal_fn(df: pd.DataFrame, params: Mapping[str, Any]) -> pd.Series:  # noqa: ARG001
        aligned = engine_signal_series.reindex(df.index)
        if aligned.isna().any():
            raise ValueError("engine_strategy_signal_index_mismatch")
        return aligned.astype(int)

    if position_feedback_bound:
        if backtest_engine is None or bar_loop_state is None:
            raise ValueError("backtest_engine_position_feedback_loop_incomplete")
        backtest_result = finalize_legacy_realistic_bar_loop_v1(
            backtest_engine,
            bar_loop_state,
            df=bars,
            effective_cost=effective_cost,
            symbol=instrument_id,
        )
    else:
        engine = BacktestEngine(
            use_execution_pipeline=True,
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

    if resolved_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY:
        assert_backtest_engine_mv2_replay_signal_parity_v1(
            mv2_replay_signals=mv2_replay_series,
            bar_outcomes=tuple(outcomes),
            backtest_engine_signal_source=resolved_engine_signal_source,
            backtest_engine_signal_digest=backtest_engine_signal_digest,
            mv2_replay_signal_digest=mv2_replay_digest,
        )
        assert_decision_funnel_trade_alignment_v1(
            bar_outcomes=tuple(outcomes),
            engine_signals=engine_signal_series,
            backtest_engine_signal_source=resolved_engine_signal_source,
            backtest_result=backtest_result,
        )

    trades_df = backtest_result.trades
    trade_count_fallback = len(trades_df) if trades_df is not None else 0
    decision_funnel_accumulator.set_trades_opened_count(
        int(backtest_result.stats.get("total_trades", trade_count_fallback))
    )

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
        decision_funnel_counts=decision_funnel_accumulator.counts_dict(),
        block_reason_counts=materialize_block_reason_counts_v0(decision_funnel_accumulator),
        backtest_engine_signal_source=resolved_engine_signal_source,
        backtest_engine_signal_digest=backtest_engine_signal_digest,
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
