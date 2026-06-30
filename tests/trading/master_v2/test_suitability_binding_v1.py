# tests/trading/master_v2/test_suitability_binding_v1.py
from __future__ import annotations

import ast
import inspect
import json
from dataclasses import fields, replace
from pathlib import Path

import pytest

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
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    evaluate_directional_assessment_v1,
    mirror_price_path_for_short,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalAssessmentStatus,
    SurvivalCostInputsV1,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    evaluate_survival_assessment_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_BINDING_LAYER_VERSION,
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityBindingStatus,
    SuitabilityBlockedReason,
    SuitabilityHardBlockReason,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityResultV1,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    compute_suitability_result_semantic_digest,
    directional_assessment_ref_from_assessment_v1,
    evaluate_suitability_binding_v1,
    filter_eligible_strategies,
    mirror_suitability_strategy_entry_for_short,
    rank_eligible_strategies,
    select_strategy_deterministic,
    serialize_suitability_result_canonical,
    survival_result_ref_from_result,
    validate_suitability_ranking_policy,
    with_computed_suitability_result_digest,
)


def _scope_ref(**overrides: object) -> ScopeEventRefV1:
    base: dict = {
        "scope_event_id": "scope-event-inst-eth-usdt-perp-epoch42-upscope_candidate",
        "semantic_digest": "a" * 64,
        "event_type": "upscope_candidate",
        "trading_epoch": 42,
    }
    base.update(overrides)
    return ScopeEventRefV1(**base)


def _directional_policy(**overrides: object) -> DirectionalAssessmentPolicyV1:
    base: dict = {
        "observe_signal_threshold": 0.001,
        "candidate_signal_threshold": 0.005,
        "confirmation_signal_threshold": 0.01,
        "confirmation_epochs": 2,
        "validity_epochs": 3,
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentPolicyV1(**base)


def _directional_input(**overrides: object) -> DirectionalAssessmentInputV1:
    base: dict = {
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 43,
        "side": DirectionalAssessmentSide.LONG,
        "price_path": (3500.0, 3540.0),
        "reference_price": 3500.0,
        "feature_refs": ("feat-momentum-v1",),
        "scope_event_ref": _scope_ref(),
        "survival_preconditions": ("survival_precondition_ref_only",),
        "confirmation_state": DirectionalConfirmationStateV1(
            candidate_count=0,
            last_evaluated_trading_epoch=42,
            last_signal_strength=0.0,
        ),
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "trusted_data": True,
        "input_complete": True,
        "explicit_hard_block_reasons": (),
        "policy_version": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return DirectionalAssessmentInputV1(**base)


def _directional_assessment(**overrides: object) -> DirectionalAssessmentV1:
    inp = _directional_input(**{k: v for k, v in overrides.items() if k != "policy"})
    policy = overrides.get("policy", _directional_policy())
    return evaluate_directional_assessment_v1(inp, policy)


def _survival_policy(**overrides: object) -> SurvivalAssessmentPolicyV1:
    base: dict = {
        "min_net_edge": 0.001,
        "min_volatility_survival_ratio": 0.5,
        "min_sequence_survival_ratio": 0.5,
        "min_drawdown_survival_ratio": 0.5,
        "min_liquidation_buffer_ratio": 0.1,
        "validity_epochs": 3,
        "policy_version": SURVIVAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return SurvivalAssessmentPolicyV1(**base)


def _survival_input(**overrides: object) -> SurvivalAssessmentInputV1:
    assessment = overrides.pop("directional_assessment", None)
    if assessment is None:
        assessment = _directional_assessment()
    base: dict = {
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 43,
        "side": DirectionalAssessmentSide.LONG,
        "directional_assessment": assessment,
        "cost_inputs": SurvivalCostInputsV1(
            entry_fee=0.0005,
            expected_entry_slippage=0.0002,
            exit_fee=0.0005,
            expected_exit_slippage=0.0002,
            expected_funding_cost=0.0001,
            expected_gross_edge=0.02,
            funding_cost_required=True,
        ),
        "metric_inputs": SurvivalMetricInputsV1(
            data_completeness_complete=True,
            volatility_survival_ratio=0.8,
            sequence_survival_ratio=0.8,
            drawdown_survival_ratio=0.8,
            liquidation_buffer_ratio=0.2,
        ),
        "last_evaluated_trading_epoch": 42,
        "input_complete": True,
        "explicit_hard_fail_reasons": (),
        "explicit_blocked_reasons": (),
        "policy_version": SURVIVAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return SurvivalAssessmentInputV1(**base)


def _survival_result(**overrides: object) -> SurvivalResultV1:
    inp = _survival_input(**{k: v for k, v in overrides.items() if k != "policy"})
    policy = overrides.get("policy", _survival_policy())
    return evaluate_survival_assessment_v1(inp, policy)


def _strategy_entry(**overrides: object) -> SuitabilityStrategyEntryV1:
    base: dict = {
        "strategy_id": "strat-momentum-v1",
        "supported_regime_ids": ("trending", "ranging"),
        "supported_sides": (DirectionalAssessmentSide.LONG,),
        "priority_rank": 10,
        "disabled": False,
        "confidence_score": 0.75,
    }
    base.update(overrides)
    return SuitabilityStrategyEntryV1(**base)


def _registry(*entries: SuitabilityStrategyEntryV1) -> SuitabilityStrategyRegistryV1:
    return SuitabilityStrategyRegistryV1(entries=entries)


def _ranking_policy(**overrides: object) -> SuitabilityRankingPolicyV1:
    base: dict = {
        "validity_epochs": 3,
        "no_match_status": SuitabilityBindingStatus.FAIL,
        "policy_version": SUITABILITY_RANKING_POLICY_VERSION,
        "tie_break_field": "strategy_id",
    }
    base.update(overrides)
    return SuitabilityRankingPolicyV1(**base)


def _binding_input(**overrides: object) -> SuitabilityBindingInputV1:
    assessment = overrides.pop("directional_assessment", None)
    survival = overrides.pop("survival_result", None)
    if assessment is None:
        assessment = _directional_assessment()
    if survival is None:
        survival = _survival_result(directional_assessment=assessment)
    base: dict = {
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 43,
        "side": DirectionalAssessmentSide.LONG,
        "directional_assessment": assessment,
        "survival_result": survival,
        "regime_id": "trending",
        "regime_status": SuitabilityRegimeStatus.KNOWN,
        "strategy_registry": _registry(_strategy_entry()),
        "last_evaluated_trading_epoch": 42,
        "input_complete": True,
        "explicit_hard_block_reasons": (),
        "explicit_blocked_reasons": (),
        "ranking_policy_version": SUITABILITY_RANKING_POLICY_VERSION,
    }
    base.update(overrides)
    return SuitabilityBindingInputV1(**base)


def _evaluate(**kwargs: object) -> SuitabilityResultV1:
    inp = kwargs.pop("inp", _binding_input(**{k: v for k, v in kwargs.items() if k != "policy"}))
    policy = kwargs.pop("policy", _ranking_policy())
    return evaluate_suitability_binding_v1(inp, policy)


def test_1_contract_schema_complete() -> None:
    names = {f.name for f in fields(SuitabilityResultV1)}
    required = {
        "suitability_id",
        "instrument_id",
        "side",
        "trading_epoch",
        "directional_assessment_ref",
        "survival_result_ref",
        "regime_id",
        "regime_status",
        "eligible_strategy_ids",
        "selected_strategy_id",
        "ranking_policy_version",
        "tie_break_trace",
        "status",
        "hard_block_reasons",
        "reason_codes",
        "valid_until_epoch",
        "semantic_digest",
    }
    assert required.issubset(names)


def test_2_status_exhaustiveness() -> None:
    assert {s.value for s in SuitabilityBindingStatus} == {"pass", "fail", "blocked"}


def test_3_deterministic_serialization() -> None:
    result = _evaluate()
    first = serialize_suitability_result_canonical(result)
    second = serialize_suitability_result_canonical(result)
    assert first == second
    assert json.loads(first) == json.loads(second)


def test_4_stable_semantic_digest() -> None:
    result = _evaluate()
    recomputed = compute_suitability_result_semantic_digest(result)
    assert result.semantic_digest == recomputed


def test_5_digest_changes_on_semantic_input_change() -> None:
    first = _evaluate(regime_id="trending")
    second = _evaluate(regime_id="ranging")
    assert first.semantic_digest != second.semantic_digest


def test_6_identical_inputs_identical_result() -> None:
    inp = _binding_input()
    policy = _ranking_policy()
    assert evaluate_suitability_binding_v1(inp, policy) == evaluate_suitability_binding_v1(
        inp, policy
    )


def test_7_survival_not_pass_implies_suitability_not_pass() -> None:
    failed_survival = replace(
        _survival_result(),
        status=SurvivalAssessmentStatus.FAIL,
    )
    result = _evaluate(survival_result=failed_survival)
    assert result.status is not SuitabilityBindingStatus.PASS
    assert SuitabilityHardBlockReason.SURVIVAL_NOT_PASS.value in result.hard_block_reasons


def test_8_unknown_regime_blocks() -> None:
    result = _evaluate(regime_id="unknown_regime", regime_status=SuitabilityRegimeStatus.KNOWN)
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert "unknown_regime_blocked" in result.reason_codes

    result2 = _evaluate(regime_id="trending", regime_status=SuitabilityRegimeStatus.UNKNOWN)
    assert result2.status is SuitabilityBindingStatus.BLOCKED


def test_9_missing_registry_blocks() -> None:
    result = _evaluate(strategy_registry=None)
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert SuitabilityBlockedReason.MISSING_STRATEGY_REGISTRY.value in result.reason_codes


def test_10_no_matching_strategy_fail_closed() -> None:
    entry = _strategy_entry(supported_regime_ids=("breakout",))
    result = _evaluate(strategy_registry=_registry(entry), regime_id="trending")
    assert result.status is SuitabilityBindingStatus.FAIL
    assert result.selected_strategy_id is None
    assert SuitabilityHardBlockReason.NO_SUITABLE_STRATEGY.value in result.hard_block_reasons


def test_11_single_eligible_strategy_selected() -> None:
    result = _evaluate()
    assert result.status is SuitabilityBindingStatus.PASS
    assert result.selected_strategy_id == "strat-momentum-v1"
    assert result.tie_break_trace == ("single_eligible_strategy",)


def test_12_multiple_eligible_requires_ranking_policy() -> None:
    entries = (
        _strategy_entry(strategy_id="strat-b", priority_rank=20),
        _strategy_entry(strategy_id="strat-a", priority_rank=10),
    )
    result = _evaluate(strategy_registry=_registry(*entries))
    assert result.status is SuitabilityBindingStatus.PASS
    assert result.selected_strategy_id == "strat-a"
    assert result.tie_break_trace[0].startswith("ranking_policy_version=")


def test_13_invalid_ranking_policy_blocks() -> None:
    blocks = validate_suitability_ranking_policy(
        _ranking_policy(policy_version="suitability_ranking_policy_v0"),
        ranking_policy_version=SUITABILITY_RANKING_POLICY_VERSION,
    )
    assert SuitabilityBlockedReason.POLICY_VERSION_INVALID in blocks
    result = _evaluate(ranking_policy_version="suitability_ranking_policy_v0")
    assert result.status is SuitabilityBindingStatus.BLOCKED


def test_14_stable_tie_break_by_strategy_id() -> None:
    entries = (
        _strategy_entry(strategy_id="strat-z", priority_rank=10),
        _strategy_entry(strategy_id="strat-a", priority_rank=10),
    )
    selected, trace = select_strategy_deterministic(
        entries,
        policy=_ranking_policy(),
    )
    assert selected == "strat-a"
    assert "tie_break=strategy_id" in trace[0]


def test_15_selection_independent_of_list_order() -> None:
    entries_ab = (
        _strategy_entry(strategy_id="strat-a", priority_rank=10),
        _strategy_entry(strategy_id="strat-b", priority_rank=10),
    )
    entries_ba = (
        _strategy_entry(strategy_id="strat-b", priority_rank=10),
        _strategy_entry(strategy_id="strat-a", priority_rank=10),
    )
    reg_ab = _registry(*entries_ab)
    reg_ba = _registry(*entries_ba)
    result_ab = _evaluate(strategy_registry=reg_ab)
    result_ba = _evaluate(strategy_registry=reg_ba)
    assert result_ab.selected_strategy_id == result_ba.selected_strategy_id == "strat-a"


def test_16_selection_independent_of_dict_like_registry_order() -> None:
    eligible_ab = filter_eligible_strategies(
        _registry(
            _strategy_entry(strategy_id="strat-a", priority_rank=5),
            _strategy_entry(strategy_id="strat-b", priority_rank=5),
        ),
        side=DirectionalAssessmentSide.LONG,
        regime_id="trending",
    )
    eligible_ba = filter_eligible_strategies(
        _registry(
            _strategy_entry(strategy_id="strat-b", priority_rank=5),
            _strategy_entry(strategy_id="strat-a", priority_rank=5),
        ),
        side=DirectionalAssessmentSide.LONG,
        regime_id="trending",
    )
    ranked_ab = rank_eligible_strategies(eligible_ab, policy=_ranking_policy())
    ranked_ba = rank_eligible_strategies(eligible_ba, policy=_ranking_policy())
    assert [e.strategy_id for e in ranked_ab] == [e.strategy_id for e in ranked_ba]


def test_17_no_default_strategy_when_none_eligible() -> None:
    result = _evaluate(
        strategy_registry=_registry(_strategy_entry(disabled=True)),
    )
    assert result.selected_strategy_id is None


def test_18_no_fallback_strategy_on_blocked_survival() -> None:
    blocked_survival = replace(
        _survival_result(),
        status=SurvivalAssessmentStatus.BLOCKED,
    )
    result = _evaluate(survival_result=blocked_survival)
    assert result.selected_strategy_id is None


def test_19_selected_strategy_unset_on_fail_and_blocked() -> None:
    fail_result = _evaluate(
        strategy_registry=_registry(_strategy_entry(supported_regime_ids=("breakout",))),
        regime_id="trending",
    )
    assert fail_result.status is SuitabilityBindingStatus.FAIL
    assert fail_result.selected_strategy_id is None

    blocked_result = _evaluate(strategy_registry=None)
    assert blocked_result.status is SuitabilityBindingStatus.BLOCKED
    assert blocked_result.selected_strategy_id is None


def test_20_nontrivial_result_has_reason_codes() -> None:
    result = _evaluate()
    assert result.reason_codes


def test_21_stale_trading_epoch_blocks() -> None:
    assessment = _directional_assessment(trading_epoch=44)
    survival = _survival_result(directional_assessment=assessment, trading_epoch=44)
    result = _evaluate(
        trading_epoch=43,
        directional_assessment=assessment,
        survival_result=survival,
    )
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert "epoch_semantics_failed" in result.reason_codes[0]


def test_22_untrusted_input_no_pass() -> None:
    result = _evaluate(input_complete=False)
    assert result.status is not SuitabilityBindingStatus.PASS


def test_23_long_short_mirror_contract_types() -> None:
    anchor = 4000.0
    long_path = (anchor, anchor + 50.0)
    short_path = mirror_price_path_for_short(long_path, anchor)
    long_assessment = _directional_assessment(
        side=DirectionalAssessmentSide.LONG,
        price_path=long_path,
        reference_price=anchor,
    )
    short_assessment = _directional_assessment(
        side=DirectionalAssessmentSide.SHORT,
        price_path=short_path,
        reference_price=anchor,
    )
    long_survival = _survival_result(
        side=DirectionalAssessmentSide.LONG,
        directional_assessment=long_assessment,
    )
    short_survival = _survival_result(
        side=DirectionalAssessmentSide.SHORT,
        directional_assessment=short_assessment,
    )
    long_entry = _strategy_entry(supported_sides=(DirectionalAssessmentSide.LONG,))
    short_entry = mirror_suitability_strategy_entry_for_short(long_entry)
    long_result = _evaluate(
        side=DirectionalAssessmentSide.LONG,
        directional_assessment=long_assessment,
        survival_result=long_survival,
        strategy_registry=_registry(long_entry),
    )
    short_result = _evaluate(
        side=DirectionalAssessmentSide.SHORT,
        directional_assessment=short_assessment,
        survival_result=short_survival,
        strategy_registry=_registry(short_entry),
    )
    assert long_result.status is SuitabilityBindingStatus.PASS
    assert short_result.status is SuitabilityBindingStatus.PASS
    assert type(long_result) is type(short_result) is SuitabilityResultV1


def test_24_directional_assessment_immutable() -> None:
    assessment = _directional_assessment()
    before = assessment
    _evaluate(directional_assessment=assessment)
    assert assessment == before


def test_25_survival_result_immutable() -> None:
    assessment = _directional_assessment()
    survival = _survival_result(directional_assessment=assessment)
    before = survival
    _evaluate(directional_assessment=assessment, survival_result=survival)
    assert survival == before


def test_26_no_runtime_order_risk_sizing_side_effects() -> None:
    result = _evaluate()
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.risk_effect == "NONE"


def test_27_futures_only_negative_instrument() -> None:
    assessment = _directional_assessment(instrument_id="inst-spot-eth-usdt")
    survival = _survival_result(
        instrument_id="inst-spot-eth-usdt",
        directional_assessment=assessment,
    )
    result = _evaluate(
        instrument_id="inst-spot-eth-usdt",
        directional_assessment=assessment,
        survival_result=survival,
    )
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert SuitabilityBlockedReason.INSTRUMENT_KIND_FORBIDDEN.value in result.reason_codes


def test_28_no_bitcoin_semantics_in_output() -> None:
    result = _evaluate(instrument_id="inst-sol-usdt-perp")
    serialized = serialize_suitability_result_canonical(result).lower()
    assert "btc" not in serialized
    assert "bitcoin" not in serialized
    assert "xbt" not in serialized


def test_29_step29f_survival_tests_still_importable() -> None:
    from trading.master_v2.survival_assessment_v1 import (
        SurvivalResultV1 as SurvivalResultV1Type,
        evaluate_survival_assessment_v1,
    )

    assert SurvivalResultV1Type is not None
    assert evaluate_survival_assessment_v1 is not None


def test_30_no_runtime_adapter_order_imports_or_side_effects() -> None:
    module_path = Path("src/trading/master_v2/suitability_binding_v1.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden = ("execution", "adapter", "scheduler", "broker", "exchange", "strategies.registry")
    for imp in imports:
        for token in forbidden:
            assert token not in imp


def test_no_confidence_only_selection() -> None:
    high_conf = _strategy_entry(
        strategy_id="strat-high-confidence",
        priority_rank=50,
        confidence_score=0.99,
    )
    low_conf = _strategy_entry(
        strategy_id="strat-low-confidence",
        priority_rank=10,
        confidence_score=0.1,
    )
    result = _evaluate(strategy_registry=_registry(high_conf, low_conf))
    assert result.selected_strategy_id == "strat-low-confidence"


def test_refs_match_upstream() -> None:
    assessment = _directional_assessment()
    survival = _survival_result(directional_assessment=assessment)
    result = _evaluate(directional_assessment=assessment, survival_result=survival)
    assert result.directional_assessment_ref == directional_assessment_ref_from_assessment_v1(
        assessment
    )
    assert result.survival_result_ref == survival_result_ref_from_result(survival)


def test_with_computed_digest_round_trip() -> None:
    result = _evaluate()
    bare = replace(result, semantic_digest="")
    bound = with_computed_suitability_result_digest(bare)
    assert bound.semantic_digest == result.semantic_digest


def test_layer_version_constant() -> None:
    assert SUITABILITY_BINDING_LAYER_VERSION == "v1"


def test_valid_until_epoch_explicit_and_bounded() -> None:
    result = _evaluate(trading_epoch=43)
    assert result.valid_until_epoch == 46


def test_module_has_no_evaluate_import_side_effects() -> None:
    source = inspect.getsource(evaluate_suitability_binding_v1)
    assert "import execution" not in source
    assert "import adapter" not in source


def test_empty_registry_blocks() -> None:
    result = _evaluate(strategy_registry=_registry())
    assert result.status is SuitabilityBindingStatus.BLOCKED
    assert SuitabilityBlockedReason.STRATEGY_REGISTRY_EMPTY.value in result.reason_codes
