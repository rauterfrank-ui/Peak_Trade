# src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py
"""
Scenario replay adapter: binds offline Double Play scenario ticks to canonical
``survival_assessment_v1`` and ``suitability_binding_v1`` without legacy envelope authority.

Wiring-only parity slice (Surface E) — no runtime authority, no trading semantic extension.
Legacy envelope inputs remain compatibility-only and must not override canonical owners.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, Tuple, Tuple

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    ScopeEventRefV1,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionBlockReason,
    DoublePlayCompositionDecision,
    DoublePlayCompositionInput,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityBindingStatus,
    SuitabilityHardBlockReason,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityResultV1,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
    mirror_suitability_strategy_entry_for_short,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalAssessmentStatus,
    SurvivalCostInputsV1,
    SurvivalHardFailReason,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    evaluate_survival_assessment_v1,
)

SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_LAYER_VERSION = "v0"
SURVIVAL_SUITABILITY_SCENARIO_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.survival_suitability_scenario_binding_adapter_v0"
)
CANONICAL_SURVIVAL_ASSESSMENT_OWNER = "trading.master_v2.survival_assessment_v1"
CANONICAL_SUITABILITY_BINDING_OWNER = "trading.master_v2.suitability_binding_v1"

RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"
ORDER_EFFECT_NONE = "NONE"

_STUB_DIGEST = "a" * 64

_DEFAULT_SCENARIO_METRICS = SurvivalMetricInputsV1(
    data_completeness_complete=True,
    volatility_survival_ratio=0.8,
    sequence_survival_ratio=0.8,
    drawdown_survival_ratio=0.8,
    liquidation_buffer_ratio=0.2,
)


@dataclass(frozen=True)
class ScenarioSurvivalSuitabilityOverridesV0:
    """Test and evidence injection only; does not introduce parallel owners."""

    bull_survival_status: SurvivalAssessmentStatus | None = None
    bear_survival_status: SurvivalAssessmentStatus | None = None
    bull_suitability_status: SuitabilityBindingStatus | None = None
    bear_suitability_status: SuitabilityBindingStatus | None = None
    bull_metric_inputs: SurvivalMetricInputsV1 | None = None
    bear_metric_inputs: SurvivalMetricInputsV1 | None = None
    bull_explicit_hard_fail_reasons: Tuple[SurvivalHardFailReason, ...] = ()
    bear_explicit_hard_fail_reasons: Tuple[SurvivalHardFailReason, ...] = ()
    regime_status: SuitabilityRegimeStatus | None = None
    strategy_registry: SuitabilityStrategyRegistryV1 | None = None


@dataclass(frozen=True)
class ScenarioSurvivalSuitabilityEvaluationV0:
    bull_assessment: DirectionalAssessmentV1
    bear_assessment: DirectionalAssessmentV1
    bull_survival: SurvivalResultV1
    bear_survival: SurvivalResultV1
    bull_suitability: SuitabilityResultV1
    bear_suitability: SuitabilityResultV1


def scenario_survival_policy_v0() -> SurvivalAssessmentPolicyV1:
    return SurvivalAssessmentPolicyV1(
        min_net_edge=0.001,
        min_volatility_survival_ratio=0.5,
        min_sequence_survival_ratio=0.5,
        min_drawdown_survival_ratio=0.5,
        min_liquidation_buffer_ratio=0.1,
        validity_epochs=3,
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )


def scenario_suitability_ranking_policy_v0() -> SuitabilityRankingPolicyV1:
    return SuitabilityRankingPolicyV1(
        validity_epochs=3,
        no_match_status=SuitabilityBindingStatus.FAIL,
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )


def scenario_strategy_registry_v0() -> SuitabilityStrategyRegistryV1:
    return SuitabilityStrategyRegistryV1(
        entries=(
            SuitabilityStrategyEntryV1(
                strategy_id="scenario-replay-v0",
                supported_regime_ids=("trending",),
                supported_sides=(DirectionalAssessmentSide.LONG,),
                priority_rank=10,
                disabled=False,
                confidence_score=0.75,
            ),
        )
    )


def legacy_side_to_assessment_statuses_v0(
    side_st: SideState,
) -> Tuple[DirectionalAssessmentStatus, DirectionalAssessmentStatus]:
    if side_st is SideState.CHOP_GUARD_BLOCK:
        return (
            DirectionalAssessmentStatus.CONFIRMED,
            DirectionalAssessmentStatus.CONFIRMED,
        )
    if side_st in (SideState.LONG_ACTIVE, SideState.LONG_ARMED):
        return (
            DirectionalAssessmentStatus.CONFIRMED,
            DirectionalAssessmentStatus.OBSERVE,
        )
    if side_st in (SideState.SHORT_ACTIVE, SideState.SHORT_ARMED):
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.CONFIRMED,
        )
    if side_st == SideState.LONG_BLOCKED:
        return (
            DirectionalAssessmentStatus.BLOCKED,
            DirectionalAssessmentStatus.OBSERVE,
        )
    if side_st == SideState.SHORT_BLOCKED:
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.BLOCKED,
        )
    if side_st == SideState.SWITCH_LONG_TO_SHORT_PENDING:
        return (
            DirectionalAssessmentStatus.OBSERVE,
            DirectionalAssessmentStatus.CANDIDATE,
        )
    if side_st == SideState.SWITCH_SHORT_TO_LONG_PENDING:
        return (
            DirectionalAssessmentStatus.CANDIDATE,
            DirectionalAssessmentStatus.OBSERVE,
        )
    return (
        DirectionalAssessmentStatus.OBSERVE,
        DirectionalAssessmentStatus.OBSERVE,
    )


def stub_scenario_directional_assessment_v0(
    *,
    side: DirectionalAssessmentSide,
    status: DirectionalAssessmentStatus,
    instrument_id: str,
    trading_epoch: int,
) -> DirectionalAssessmentV1:
    side_label = "long" if side is DirectionalAssessmentSide.LONG else "short"
    return DirectionalAssessmentV1(
        assessment_id=f"scenario-{side_label}-{trading_epoch}",
        side=side,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        status=status,
        signal_strength=0.02 if status is DirectionalAssessmentStatus.CONFIRMED else 0.0,
        confidence=0.9 if status is DirectionalAssessmentStatus.CONFIRMED else 0.1,
        feature_refs=("scenario-replay-v0",),
        scope_event_ref=ScopeEventRefV1(
            scope_event_id=f"scope-{instrument_id}-{trading_epoch}",
            semantic_digest=_STUB_DIGEST,
            event_type="noop",
            trading_epoch=trading_epoch - 1,
        ),
        survival_preconditions=("scenario_replay_ref_only",),
        hard_block_reasons=(),
        reason_codes=(f"scenario_{side_label}_{status.value}",),
        valid_until_epoch=trading_epoch + 3,
        semantic_digest=_STUB_DIGEST,
    )


def evaluate_scenario_directional_survival_v0(
    assessment: DirectionalAssessmentV1,
    *,
    metric_inputs: SurvivalMetricInputsV1 | None = None,
    explicit_hard_fail_reasons: Tuple[SurvivalHardFailReason, ...] = (),
    status_override: SurvivalAssessmentStatus | None = None,
) -> SurvivalResultV1:
    inp = SurvivalAssessmentInputV1(
        instrument_id=assessment.instrument_id,
        trading_epoch=assessment.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        cost_inputs=SurvivalCostInputsV1(
            entry_fee=0.0005,
            expected_entry_slippage=0.0002,
            exit_fee=0.0005,
            expected_exit_slippage=0.0002,
            expected_funding_cost=0.0001,
            expected_gross_edge=0.02,
            funding_cost_required=True,
        ),
        metric_inputs=metric_inputs or _DEFAULT_SCENARIO_METRICS,
        last_evaluated_trading_epoch=assessment.trading_epoch - 1,
        input_complete=True,
        explicit_hard_fail_reasons=explicit_hard_fail_reasons,
        explicit_blocked_reasons=(),
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )
    result = evaluate_survival_assessment_v1(inp, scenario_survival_policy_v0())
    if status_override is not None:
        return replace(result, status=status_override)
    return result


def _scenario_strategy_entry(side: DirectionalAssessmentSide) -> SuitabilityStrategyEntryV1:
    return SuitabilityStrategyEntryV1(
        strategy_id="scenario-replay-v0",
        supported_regime_ids=("trending",),
        supported_sides=(side,),
        priority_rank=10,
        disabled=False,
        confidence_score=0.75,
    )


def evaluate_scenario_directional_suitability_v0(
    assessment: DirectionalAssessmentV1,
    survival: SurvivalResultV1,
    *,
    regime_status: SuitabilityRegimeStatus = SuitabilityRegimeStatus.KNOWN,
    strategy_registry: SuitabilityStrategyRegistryV1 | None = None,
    status_override: SuitabilityBindingStatus | None = None,
) -> SuitabilityResultV1:
    entry = _scenario_strategy_entry(assessment.side)
    if assessment.side is DirectionalAssessmentSide.SHORT:
        entry = mirror_suitability_strategy_entry_for_short(
            _scenario_strategy_entry(DirectionalAssessmentSide.LONG)
        )
    registry = (
        strategy_registry
        if strategy_registry is not None
        else SuitabilityStrategyRegistryV1(entries=(entry,))
    )
    inp = SuitabilityBindingInputV1(
        instrument_id=assessment.instrument_id,
        trading_epoch=assessment.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        survival_result=survival,
        regime_id="trending",
        regime_status=regime_status,
        strategy_registry=registry,
        last_evaluated_trading_epoch=assessment.trading_epoch - 1,
        input_complete=True,
        explicit_hard_block_reasons=(),
        explicit_blocked_reasons=(),
        ranking_policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )
    result = evaluate_suitability_binding_v1(inp, scenario_suitability_ranking_policy_v0())
    if status_override is not None:
        return replace(result, status=status_override, selected_strategy_id=None)
    return result


def evaluate_scenario_survival_suitability_v0(
    *,
    instrument_id: str,
    trading_epoch: int,
    side_st: SideState,
    overrides: ScenarioSurvivalSuitabilityOverridesV0 | None = None,
) -> ScenarioSurvivalSuitabilityEvaluationV0:
    ovr = overrides or ScenarioSurvivalSuitabilityOverridesV0()
    bull_status, bear_status = legacy_side_to_assessment_statuses_v0(side_st)
    bull = stub_scenario_directional_assessment_v0(
        side=DirectionalAssessmentSide.LONG,
        status=bull_status,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )
    bear = stub_scenario_directional_assessment_v0(
        side=DirectionalAssessmentSide.SHORT,
        status=bear_status,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
    )

    bull_survival = evaluate_scenario_directional_survival_v0(
        bull,
        metric_inputs=ovr.bull_metric_inputs,
        explicit_hard_fail_reasons=ovr.bull_explicit_hard_fail_reasons,
        status_override=ovr.bull_survival_status,
    )
    bear_survival = evaluate_scenario_directional_survival_v0(
        bear,
        metric_inputs=ovr.bear_metric_inputs,
        explicit_hard_fail_reasons=ovr.bear_explicit_hard_fail_reasons,
        status_override=ovr.bear_survival_status,
    )

    regime_status = ovr.regime_status or SuitabilityRegimeStatus.KNOWN
    registry = ovr.strategy_registry

    bull_suit = evaluate_scenario_directional_suitability_v0(
        bull,
        bull_survival,
        regime_status=regime_status,
        strategy_registry=registry,
        status_override=ovr.bull_suitability_status,
    )
    bear_suit = evaluate_scenario_directional_suitability_v0(
        bear,
        bear_survival,
        regime_status=regime_status,
        strategy_registry=registry,
        status_override=ovr.bear_suitability_status,
    )

    return ScenarioSurvivalSuitabilityEvaluationV0(
        bull_assessment=bull,
        bear_assessment=bear,
        bull_survival=bull_survival,
        bear_survival=bear_survival,
        bull_suitability=bull_suit,
        bear_suitability=bear_suit,
    )


def canonical_survival_blocks_entry_v0(survival: SurvivalResultV1) -> bool:
    return survival.status is not SurvivalAssessmentStatus.PASS


def canonical_suitability_blocks_entry_v0(suitability: SuitabilityResultV1) -> bool:
    return suitability.status is not SuitabilityBindingStatus.PASS


def canonical_survival_suitability_allows_composition_v0(
    evaluation: ScenarioSurvivalSuitabilityEvaluationV0,
    *,
    requested_side: RequestedSide,
) -> bool:
    if canonical_survival_blocks_entry_v0(evaluation.bull_survival):
        return False
    if canonical_survival_blocks_entry_v0(evaluation.bear_survival):
        return False
    if requested_side is RequestedSide.LONG_BULL:
        return not canonical_suitability_blocks_entry_v0(evaluation.bull_suitability)
    if requested_side is RequestedSide.SHORT_BEAR:
        return not canonical_suitability_blocks_entry_v0(evaluation.bear_suitability)
    return True


def legacy_envelope_would_block_but_canonical_passes_v0(
    *,
    legacy_survival_blocked: bool,
    legacy_suitability_blocked: bool,
    evaluation: ScenarioSurvivalSuitabilityEvaluationV0,
    requested_side: RequestedSide,
) -> bool:
    legacy_blocked = legacy_survival_blocked or legacy_suitability_blocked
    if not legacy_blocked:
        return False
    return canonical_survival_suitability_allows_composition_v0(
        evaluation,
        requested_side=requested_side,
    )


def apply_canonical_survival_suitability_pre_matrix_gates_v0(
    inp: DoublePlayCompositionInput,
    evaluation: ScenarioSurvivalSuitabilityEvaluationV0,
) -> Optional[DoublePlayCompositionDecision]:
    if evaluation.bull_survival.status is SurvivalAssessmentStatus.FAIL or (
        evaluation.bear_survival.status is SurvivalAssessmentStatus.FAIL
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SURVIVAL_BLOCKED,),
            reason="Canonical survival hard fail blocks composition.",
            live_authorization=False,
        )

    if evaluation.bull_survival.status is SurvivalAssessmentStatus.BLOCKED or (
        evaluation.bear_survival.status is SurvivalAssessmentStatus.BLOCKED
    ):
        return DoublePlayCompositionDecision(
            status=DoublePlayCompositionStatus.BLOCKED,
            block_reasons=(DoublePlayCompositionBlockReason.SURVIVAL_BLOCKED,),
            reason="Canonical survival required unknown blocks composition.",
            live_authorization=False,
        )

    req = inp.requested_side
    if req is RequestedSide.LONG_BULL:
        suit = evaluation.bull_suitability
        if suit.status is SuitabilityBindingStatus.BLOCKED:
            if SuitabilityHardBlockReason.NO_SUITABLE_STRATEGY.value not in suit.hard_block_reasons:
                if any("regime" in code for code in suit.reason_codes):
                    return DoublePlayCompositionDecision(
                        status=DoublePlayCompositionStatus.BLOCKED,
                        block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_UNKNOWN,),
                        reason="Canonical suitability unknown; fail closed.",
                        live_authorization=False,
                    )
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
                reason="Requested Long/Bull but canonical suitability does not allow long/bull pool.",
                live_authorization=False,
            )
        if suit.status is SuitabilityBindingStatus.FAIL:
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_DISABLED,),
                reason="Canonical suitability fail blocks long/bull pool.",
                live_authorization=False,
            )

    if req is RequestedSide.SHORT_BEAR:
        suit = evaluation.bear_suitability
        if suit.status is SuitabilityBindingStatus.BLOCKED:
            if any("regime" in code for code in suit.reason_codes):
                return DoublePlayCompositionDecision(
                    status=DoublePlayCompositionStatus.BLOCKED,
                    block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_UNKNOWN,),
                    reason="Canonical suitability unknown; fail closed.",
                    live_authorization=False,
                )
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.REQUESTED_SIDE_NOT_ELIGIBLE,),
                reason="Requested Short/Bear but canonical suitability does not allow short/bear pool.",
                live_authorization=False,
            )
        if suit.status is SuitabilityBindingStatus.FAIL:
            return DoublePlayCompositionDecision(
                status=DoublePlayCompositionStatus.BLOCKED,
                block_reasons=(DoublePlayCompositionBlockReason.SUITABILITY_DISABLED,),
                reason="Canonical suitability fail blocks short/bear pool.",
                live_authorization=False,
            )

    return None


def survival_suitability_binding_non_authority_boundary_ok_v0() -> bool:
    return True


def system_economic_evidence_admissible_v0() -> bool:
    return False


def canonical_survival_owner_ref_v0() -> str:
    return CANONICAL_SURVIVAL_ASSESSMENT_OWNER


def canonical_suitability_owner_ref_v0() -> str:
    return CANONICAL_SUITABILITY_BINDING_OWNER
