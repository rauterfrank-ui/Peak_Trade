# tests/trading/master_v2/test_strategy_suitability_agreement_consumer_contract_v1.py
"""Focused consumer/contract tests for Decision-D suitability agreement binding."""

from __future__ import annotations

from typing import Optional

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    evaluate_directional_assessment_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    build_integrated_offline_replay_input_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategySideAgreementV1,
    StrategySignalEncodingClassV1,
    StrategySuitabilityAgreementMaterialV1,
    compute_strategy_suitability_agreement_material_digest_v1,
    fold_strategy_suitability_agreement_into_input_digest_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalAssessmentStatus,
    SurvivalCostInputsV1,
    SurvivalMetricInputsV1,
    evaluate_survival_assessment_v1,
)

_INSTRUMENT = "inst-eth-usdt-perp"
_EPOCH = 43
_DIGEST = "d" * 64


def _scope_ref() -> ScopeEventRefV1:
    return ScopeEventRefV1(
        scope_event_id="scope-event-inst-eth-usdt-perp-epoch42-upscope_candidate",
        semantic_digest="a" * 64,
        event_type="upscope_candidate",
        trading_epoch=42,
    )


def _assessment(side: DirectionalAssessmentSide = DirectionalAssessmentSide.LONG):
    policy = DirectionalAssessmentPolicyV1(
        observe_signal_threshold=0.001,
        candidate_signal_threshold=0.005,
        confirmation_signal_threshold=0.01,
        confirmation_epochs=2,
        validity_epochs=3,
        policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    )
    price_path = (3500.0, 3570.0) if side is DirectionalAssessmentSide.LONG else (3500.0, 3430.0)
    inp = DirectionalAssessmentInputV1(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side=side,
        price_path=price_path,
        reference_price=3500.0,
        feature_refs=("feat-momentum-v1",),
        scope_event_ref=_scope_ref(),
        survival_preconditions=("survival_precondition_ref_only",),
        confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=_EPOCH - 1,
            last_signal_strength=0.02,
        ),
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        bar_finality_status=BarFinalityStatus.FINALIZED,
        trusted_data=True,
        input_complete=True,
        explicit_hard_block_reasons=(),
        policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    )
    return evaluate_directional_assessment_v1(inp, policy)


def _survival(assessment):
    policy = SurvivalAssessmentPolicyV1(
        min_net_edge=0.001,
        min_volatility_survival_ratio=0.5,
        min_sequence_survival_ratio=0.5,
        min_drawdown_survival_ratio=0.5,
        min_liquidation_buffer_ratio=0.1,
        validity_epochs=3,
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )
    inp = SurvivalAssessmentInputV1(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
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
        metric_inputs=SurvivalMetricInputsV1(
            data_completeness_complete=True,
            volatility_survival_ratio=0.8,
            sequence_survival_ratio=0.8,
            drawdown_survival_ratio=0.8,
            liquidation_buffer_ratio=0.2,
        ),
        last_evaluated_trading_epoch=_EPOCH - 1,
        input_complete=True,
        explicit_hard_fail_reasons=(),
        explicit_blocked_reasons=(),
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )
    return evaluate_survival_assessment_v1(inp, policy)


def _registry(*strategy_ids: str) -> SuitabilityStrategyRegistryV1:
    entries = []
    for idx, sid in enumerate(strategy_ids):
        entries.append(
            SuitabilityStrategyEntryV1(
                strategy_id=sid,
                supported_regime_ids=("trending",),
                supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
                priority_rank=10 + idx,
                disabled=False,
                confidence_score=0.8,
            )
        )
    return SuitabilityStrategyRegistryV1(entries=tuple(entries))


def _material(
    *,
    encoding_class: StrategySignalEncodingClassV1,
    executed_strategy_id: str = "rsi_reversion",
    cycle_signal_value: int = 1,
    side_agreement: StrategySideAgreementV1 = StrategySideAgreementV1.NEUTRAL,
    filter_pass: Optional[bool] = None,
    event_kind: Optional[StrategyAgreementEventKindV1] = None,
    instrument_id: str = _INSTRUMENT,
    trading_epoch: int = _EPOCH,
    strategy_params_digest: str = _DIGEST,
    strategy_signal_digest: str = _DIGEST,
    strategy_version: str = "v1",
) -> StrategySuitabilityAgreementMaterialV1:
    material_digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding_class,
        configured_strategy_id=executed_strategy_id,
        executed_strategy_id=executed_strategy_id,
        strategy_version=strategy_version,
        strategy_params_digest=strategy_params_digest,
        strategy_signal_digest=strategy_signal_digest,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle_signal_value,
        side_agreement=side_agreement,
        filter_pass=filter_pass,
        event_kind=event_kind,
    )
    return StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding_class,
        configured_strategy_id=executed_strategy_id,
        executed_strategy_id=executed_strategy_id,
        strategy_version=strategy_version,
        strategy_params_digest=strategy_params_digest,
        strategy_signal_digest=strategy_signal_digest,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        cycle_signal_value=cycle_signal_value,  # type: ignore[arg-type]
        side_agreement=side_agreement,
        filter_pass=filter_pass,
        event_kind=event_kind,
        material_digest=material_digest,
    )


def _binding_input(material: StrategySuitabilityAgreementMaterialV1 | None, *strategy_ids: str):
    assessment = _assessment(DirectionalAssessmentSide.LONG)
    survival = _survival(assessment)
    assert survival.status is SurvivalAssessmentStatus.PASS
    assert assessment.status is not DirectionalAssessmentStatus.BLOCKED
    return SuitabilityBindingInputV1(
        instrument_id=_INSTRUMENT,
        trading_epoch=_EPOCH,
        side=DirectionalAssessmentSide.LONG,
        directional_assessment=assessment,
        survival_result=survival,
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        strategy_registry=_registry(*(strategy_ids or ("rsi_reversion",))),
        last_evaluated_trading_epoch=_EPOCH - 1,
        input_complete=True,
        explicit_hard_block_reasons=(),
        explicit_blocked_reasons=(),
        ranking_policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        strategy_suitability_agreement_material=material,
    )


def _policy() -> SuitabilityRankingPolicyV1:
    return SuitabilityRankingPolicyV1(
        validity_epochs=3,
        no_match_status=SuitabilityBindingStatus.FAIL,
        policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )


def test_same_context_two_positional_bindings_diverge_digest_and_eligibility() -> None:
    m_agree = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle_signal_value=1,
        executed_strategy_id="rsi_reversion",
    )
    m_disagree = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle_signal_value=-1,
        executed_strategy_id="rsi_reversion",
        strategy_signal_digest="e" * 64,
    )
    assert m_agree.material_digest != m_disagree.material_digest
    base = "f" * 64
    assert fold_strategy_suitability_agreement_into_input_digest_v1(
        base, m_agree
    ) != fold_strategy_suitability_agreement_into_input_digest_v1(base, m_disagree)

    result_agree = evaluate_suitability_binding_v1(
        _binding_input(m_agree, "rsi_reversion"), _policy()
    )
    result_disagree = evaluate_suitability_binding_v1(
        _binding_input(m_disagree, "rsi_reversion"), _policy()
    )
    assert result_agree.status is SuitabilityBindingStatus.PASS
    assert result_agree.selected_strategy_id == "rsi_reversion"
    assert "strategy_signal_agreement_agree" in result_agree.reason_codes
    assert result_disagree.selected_strategy_id is None
    assert "rsi_reversion" not in result_disagree.eligible_strategy_ids
    assert "strategy_signal_agreement_disagree" in result_disagree.reason_codes


def test_entry_exit_minus_one_demotes_eligibility_without_exit_authority() -> None:
    material = _material(
        encoding_class=StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1,
        executed_strategy_id="macd",
        cycle_signal_value=-1,
        side_agreement=StrategySideAgreementV1.NOT_APPLICABLE,
        event_kind=StrategyAgreementEventKindV1.EXIT,
    )
    result = evaluate_suitability_binding_v1(
        _binding_input(material, "macd", "rsi_reversion"), _policy()
    )
    assert "macd" not in result.eligible_strategy_ids
    assert "strategy_signal_exit_demotion" in result.reason_codes
    assert result.authority_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.risk_effect == "NONE"


def test_filter_mask_zero_blocks_and_one_allows() -> None:
    blocked = _material(
        encoding_class=StrategySignalEncodingClassV1.FILTER_MASK01_V1,
        executed_strategy_id="vol_regime_filter",
        cycle_signal_value=0,
        side_agreement=StrategySideAgreementV1.NOT_APPLICABLE,
        filter_pass=False,
    )
    allowed = _material(
        encoding_class=StrategySignalEncodingClassV1.FILTER_MASK01_V1,
        executed_strategy_id="vol_regime_filter",
        cycle_signal_value=1,
        side_agreement=StrategySideAgreementV1.NOT_APPLICABLE,
        filter_pass=True,
        strategy_signal_digest="e" * 64,
    )
    blocked_result = evaluate_suitability_binding_v1(
        _binding_input(blocked, "vol_regime_filter"), _policy()
    )
    allowed_result = evaluate_suitability_binding_v1(
        _binding_input(allowed, "vol_regime_filter"), _policy()
    )
    assert blocked_result.selected_strategy_id is None
    assert "strategy_signal_filter_blocked" in blocked_result.reason_codes
    assert allowed_result.status is SuitabilityBindingStatus.PASS
    assert allowed_result.selected_strategy_id == "vol_regime_filter"
    assert "strategy_signal_filter_pass" in allowed_result.reason_codes


def test_instrument_epoch_mismatch_fail_closed() -> None:
    material = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        instrument_id="inst-sol-usdt-perp",
    )
    result = evaluate_suitability_binding_v1(_binding_input(material, "rsi_reversion"), _policy())
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert "instrument_mismatch" in result.reason_codes

    material_epoch = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        trading_epoch=_EPOCH + 5,
    )
    result_epoch = evaluate_suitability_binding_v1(
        _binding_input(material_epoch, "rsi_reversion"), _policy()
    )
    assert result_epoch.status is SuitabilityBindingStatus.BLOCKED
    assert "trading_epoch_mismatch" in result_epoch.reason_codes


def test_builder_folds_material_into_input_digest() -> None:
    from dataclasses import fields as dc_fields

    from tests.trading.master_v2 import (
        test_integrated_offline_trading_logic_replay_v1 as replay_tests,
    )

    base = replay_tests._replay_input()
    m1 = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle_signal_value=1,
        trading_epoch=base.trading_epoch,
        instrument_id=base.instrument_id,
    )
    m2 = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle_signal_value=-1,
        strategy_signal_digest="e" * 64,
        trading_epoch=base.trading_epoch,
        instrument_id=base.instrument_id,
    )
    kwargs = {f.name: getattr(base, f.name) for f in dc_fields(base)}
    kwargs.pop("strategy_suitability_agreement_material", None)
    kwargs.pop("input_digest", None)
    base_digest = "a" * 64
    inp1 = build_integrated_offline_replay_input_v1(
        **kwargs,
        input_digest=base_digest,
        strategy_suitability_agreement_material=m1,
    )
    inp2 = build_integrated_offline_replay_input_v1(
        **kwargs,
        input_digest=base_digest,
        strategy_suitability_agreement_material=m2,
    )
    assert inp1.input_digest != inp2.input_digest
    assert inp1.input_digest != base_digest


def test_cmc_untrusted_blocks_when_agreement_material_present() -> None:
    from dataclasses import fields as dc_fields, replace

    from tests.trading.master_v2 import (
        test_integrated_offline_trading_logic_replay_v1 as replay_tests,
    )
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        run_integrated_offline_trading_logic_replay_v1,
    )

    base = replay_tests._replay_input()
    untrusted_ctx = replace(
        base.canonical_market_context,
        data_integrity_status=DataIntegrityStatus.UNTRUSTED,
    )
    material = _material(
        encoding_class=StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1,
        cycle_signal_value=1,
        trading_epoch=base.trading_epoch,
        instrument_id=base.instrument_id,
    )
    kwargs = {f.name: getattr(base, f.name) for f in dc_fields(base)}
    kwargs.pop("strategy_suitability_agreement_material", None)
    kwargs.pop("input_digest", None)
    kwargs["canonical_market_context"] = untrusted_ctx
    replay_input = build_integrated_offline_replay_input_v1(
        **kwargs,
        input_digest="a" * 64,
        strategy_suitability_agreement_material=material,
    )
    result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    assert result.replay_pass is False
    assert "cmc_untrusted_or_nonfinal" in result.fail_reasons
