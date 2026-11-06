# tests/trading/master_v2/test_survival_assessment_v1.py
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
    SURVIVAL_ASSESSMENT_LAYER_VERSION,
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalAssessmentStatus,
    SurvivalBlockedReason,
    SurvivalCostInputsV1,
    SurvivalHardFailReason,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    SurvivalSubcheckStatus,
    aggregate_survival_status,
    compute_expected_roundtrip_cost,
    compute_net_expected_edge,
    compute_survival_result_semantic_digest,
    directional_assessment_ref_from_assessment,
    evaluate_survival_assessment_v1,
    mirror_survival_metric_inputs_for_short,
    serialize_survival_result_canonical,
    validate_survival_assessment_policy,
    with_computed_survival_result_digest,
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


def _policy(**overrides: object) -> SurvivalAssessmentPolicyV1:
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


def _costs(**overrides: object) -> SurvivalCostInputsV1:
    base: dict = {
        "entry_fee": 0.0005,
        "expected_entry_slippage": 0.0002,
        "exit_fee": 0.0005,
        "expected_exit_slippage": 0.0002,
        "expected_funding_cost": 0.0001,
        "expected_gross_edge": 0.02,
        "funding_cost_required": True,
    }
    base.update(overrides)
    return SurvivalCostInputsV1(**base)


def _metrics(**overrides: object) -> SurvivalMetricInputsV1:
    base: dict = {
        "data_completeness_complete": True,
        "volatility_survival_ratio": 0.8,
        "sequence_survival_ratio": 0.8,
        "drawdown_survival_ratio": 0.8,
        "liquidation_buffer_ratio": 0.2,
    }
    base.update(overrides)
    return SurvivalMetricInputsV1(**base)


def _input(**overrides: object) -> SurvivalAssessmentInputV1:
    assessment = overrides.pop("directional_assessment", None)
    if assessment is None:
        assessment = _directional_assessment(
            **{
                k: v
                for k, v in overrides.items()
                if k in DirectionalAssessmentInputV1.__annotations__
            }
        )
    base: dict = {
        "instrument_id": "inst-eth-usdt-perp",
        "trading_epoch": 43,
        "side": DirectionalAssessmentSide.LONG,
        "directional_assessment": assessment,
        "cost_inputs": _costs(),
        "metric_inputs": _metrics(),
        "last_evaluated_trading_epoch": 42,
        "input_complete": True,
        "explicit_hard_fail_reasons": (),
        "explicit_blocked_reasons": (),
        "policy_version": SURVIVAL_ASSESSMENT_POLICY_VERSION,
    }
    base.update(overrides)
    return SurvivalAssessmentInputV1(**base)


def _evaluate(**kwargs: object) -> SurvivalResultV1:
    inp = kwargs.pop("inp", _input(**{k: v for k, v in kwargs.items() if k != "policy"}))
    policy = kwargs.pop("policy", _policy())
    return evaluate_survival_assessment_v1(inp, policy)


def test_1_contract_schema_complete() -> None:
    names = {f.name for f in fields(SurvivalResultV1)}
    required = {
        "survival_id",
        "instrument_id",
        "side",
        "trading_epoch",
        "directional_assessment_ref",
        "data_completeness_result",
        "cost_survival_result",
        "volatility_survival_result",
        "sequence_survival_result",
        "drawdown_survival_result",
        "liquidation_buffer_result",
        "expected_gross_edge",
        "expected_roundtrip_cost",
        "net_expected_edge",
        "status",
        "hard_fail_reasons",
        "blocked_reasons",
        "reason_codes",
        "policy_version",
        "valid_until_epoch",
        "semantic_digest",
    }
    assert required.issubset(names)


def test_2_status_enum_exhaustiveness() -> None:
    assert {s.value for s in SurvivalAssessmentStatus} == {"pass", "fail", "blocked"}
    assert {s.value for s in SurvivalSubcheckStatus} == {
        "pass",
        "fail",
        "unknown",
        "not_applicable",
    }


def test_3_deterministic_serialization() -> None:
    result = _evaluate()
    first = serialize_survival_result_canonical(result)
    second = serialize_survival_result_canonical(result)
    assert first == second
    assert json.loads(first) == json.loads(second)


def test_4_stable_semantic_digest() -> None:
    result = _evaluate()
    recomputed = compute_survival_result_semantic_digest(result)
    assert result.semantic_digest == recomputed


def test_5_digest_changes_on_semantic_input_change() -> None:
    first = _evaluate(cost_inputs=_costs(expected_gross_edge=0.02))
    second = _evaluate(cost_inputs=_costs(expected_gross_edge=0.03))
    assert first.semantic_digest != second.semantic_digest


def test_6_identical_inputs_identical_result() -> None:
    inp = _input()
    policy = _policy()
    assert evaluate_survival_assessment_v1(inp, policy) == evaluate_survival_assessment_v1(
        inp, policy
    )


def test_7_long_short_mirror_structural_outcome() -> None:
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
    long_result = _evaluate(
        side=DirectionalAssessmentSide.LONG,
        directional_assessment=long_assessment,
    )
    short_result = _evaluate(
        side=DirectionalAssessmentSide.SHORT,
        directional_assessment=short_assessment,
        metric_inputs=mirror_survival_metric_inputs_for_short(_metrics()),
    )
    assert long_result.status is SurvivalAssessmentStatus.PASS
    assert short_result.status is SurvivalAssessmentStatus.PASS
    assert long_result.net_expected_edge == pytest.approx(short_result.net_expected_edge)


def test_8_directional_assessment_remains_immutable() -> None:
    assessment = _directional_assessment()
    before = assessment
    _evaluate(directional_assessment=assessment)
    assert assessment == before


def test_9_scope_event_ref_remains_immutable_via_directional_assessment() -> None:
    assessment = _directional_assessment()
    scope_before = assessment.scope_event_ref
    _evaluate(directional_assessment=assessment)
    assert assessment.scope_event_ref == scope_before


def test_10_required_unknown_blocks() -> None:
    result = _evaluate(metric_inputs=_metrics(data_completeness_complete=None))
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert result.data_completeness_result.status is SurvivalSubcheckStatus.UNKNOWN


def test_11_hard_fail_yields_fail() -> None:
    result = _evaluate(metric_inputs=_metrics(data_completeness_complete=False))
    assert result.status is SurvivalAssessmentStatus.FAIL
    assert SurvivalHardFailReason.DATA_COMPLETENESS_FAIL.value in result.hard_fail_reasons


def test_12_all_required_pass_yields_pass() -> None:
    result = _evaluate()
    assert result.status is SurvivalAssessmentStatus.PASS
    assert result.data_completeness_result.status is SurvivalSubcheckStatus.PASS
    assert result.cost_survival_result.status is SurvivalSubcheckStatus.PASS


def test_13_no_implicit_null_cost_assumption() -> None:
    costs = _costs(
        entry_fee=None,
        expected_entry_slippage=None,
        exit_fee=None,
        expected_exit_slippage=None,
        expected_funding_cost=None,
        expected_gross_edge=None,
    )
    result = _evaluate(cost_inputs=costs)
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert result.expected_roundtrip_cost is None
    assert result.net_expected_edge is None


def test_14_missing_fee_information_blocks() -> None:
    result = _evaluate(cost_inputs=_costs(entry_fee=None))
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.MISSING_ENTRY_FEE.value in result.blocked_reasons


def test_15_missing_slippage_information_blocks() -> None:
    result = _evaluate(cost_inputs=_costs(expected_entry_slippage=None))
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.MISSING_ENTRY_SLIPPAGE.value in result.blocked_reasons


def test_16_missing_funding_information_blocks_when_required() -> None:
    result = _evaluate(cost_inputs=_costs(expected_funding_cost=None, funding_cost_required=True))
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.MISSING_FUNDING_COST.value in result.blocked_reasons


def test_17_expected_roundtrip_cost_correctly_aggregated() -> None:
    costs = _costs(
        entry_fee=0.001,
        expected_entry_slippage=0.002,
        exit_fee=0.003,
        expected_exit_slippage=0.004,
        expected_funding_cost=0.005,
    )
    assert compute_expected_roundtrip_cost(costs) == pytest.approx(0.015)
    result = _evaluate(cost_inputs=costs)
    assert result.expected_roundtrip_cost == pytest.approx(0.015)


def test_18_net_expected_edge_correctly_calculated() -> None:
    costs = _costs(expected_gross_edge=0.02)
    roundtrip = compute_expected_roundtrip_cost(costs)
    assert compute_net_expected_edge(
        expected_gross_edge=costs.expected_gross_edge,
        expected_roundtrip_cost=roundtrip,
    ) == pytest.approx(0.02 - roundtrip)
    result = _evaluate(cost_inputs=costs)
    assert result.net_expected_edge == pytest.approx(0.02 - roundtrip)


def test_19_negative_or_insufficient_net_edge_fail_closed() -> None:
    result = _evaluate(cost_inputs=_costs(expected_gross_edge=0.0001))
    assert result.status is SurvivalAssessmentStatus.FAIL
    assert SurvivalHardFailReason.NET_EDGE_INSUFFICIENT.value in result.hard_fail_reasons


def test_20_directional_assessment_blocked_blocks_survival() -> None:
    blocked_assessment = replace(
        _directional_assessment(),
        status=DirectionalAssessmentStatus.BLOCKED,
    )
    result = _evaluate(directional_assessment=blocked_assessment)
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.DIRECTIONAL_ASSESSMENT_BLOCKED.value in result.blocked_reasons


def test_21_no_runtime_adapter_order_imports_or_side_effects() -> None:
    module_path = Path("src/trading/master_v2/survival_assessment_v1.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    forbidden = ("execution", "adapter", "scheduler", "broker", "exchange")
    for imp in imports:
        for token in forbidden:
            assert token not in imp


def test_22_futures_only_negative_instrument() -> None:
    result = _evaluate(instrument_id="inst-spot-eth-usdt")
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.INSTRUMENT_KIND_FORBIDDEN.value in result.blocked_reasons


def test_23_no_bitcoin_semantics_in_output() -> None:
    result = _evaluate(instrument_id="inst-sol-usdt-perp")
    serialized = serialize_survival_result_canonical(result).lower()
    assert "btc" not in serialized
    assert "bitcoin" not in serialized
    assert "xbt" not in serialized


def test_24_step29b_c_d_e_regression_imports_still_work() -> None:
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
    from trading.master_v2.canonical_scope_initialization_v1 import initialize_canonical_scope
    from trading.master_v2.deterministic_scope_event_generator_v1 import (
        generate_deterministic_scope_event,
    )
    from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentV1

    assert CanonicalMarketContextV1 is not None
    assert initialize_canonical_scope is not None
    assert generate_deterministic_scope_event is not None
    assert DirectionalAssessmentV1 is not None


def test_25_aggregate_survival_status_rules() -> None:
    from trading.master_v2.survival_assessment_v1 import SurvivalSubcheckResultV1

    pass_checks = tuple(
        SurvivalSubcheckResultV1(name=name, status=SurvivalSubcheckStatus.PASS)
        for name in (
            "data_completeness_check",
            "cost_survival_check",
            "volatility_survival_check",
            "sequence_survival_check",
            "drawdown_survival_check",
            "liquidation_buffer_check",
        )
    )
    assert aggregate_survival_status(pass_checks) is SurvivalAssessmentStatus.PASS

    fail_checks = (
        SurvivalSubcheckResultV1(
            name="data_completeness_check",
            status=SurvivalSubcheckStatus.FAIL,
        ),
        *pass_checks[1:],
    )
    assert aggregate_survival_status(fail_checks) is SurvivalAssessmentStatus.FAIL

    unknown_checks = (
        SurvivalSubcheckResultV1(
            name="data_completeness_check",
            status=SurvivalSubcheckStatus.UNKNOWN,
        ),
        *pass_checks[1:],
    )
    assert aggregate_survival_status(unknown_checks) is SurvivalAssessmentStatus.BLOCKED


def test_26_stale_trading_epoch_blocks() -> None:
    assessment = _directional_assessment(trading_epoch=44)
    result = _evaluate(trading_epoch=43, directional_assessment=assessment)
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert SurvivalBlockedReason.DIRECTIONAL_ASSESSMENT_REF_STALE.value in result.blocked_reasons


def test_27_no_authority_runtime_order_or_risk_effects() -> None:
    result = _evaluate()
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.order_effect == "NONE"
    assert result.risk_effect == "NONE"


def test_28_directional_assessment_ref_matches_upstream() -> None:
    assessment = _directional_assessment()
    result = _evaluate(directional_assessment=assessment)
    expected_ref = directional_assessment_ref_from_assessment(assessment)
    assert result.directional_assessment_ref == expected_ref


def test_29_with_computed_survival_result_digest_round_trip() -> None:
    result = _evaluate()
    bare = replace(result, semantic_digest="")
    bound = with_computed_survival_result_digest(bare)
    assert bound.semantic_digest == result.semantic_digest


def test_30_policy_validation_blocks_on_invalid_version() -> None:
    blocks = validate_survival_assessment_policy(
        _policy(policy_version="survival_assessment_policy_v0"),
        policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
    )
    assert SurvivalBlockedReason.POLICY_VERSION_INVALID in blocks


def test_31_nontrivial_result_has_reason_codes() -> None:
    result = _evaluate()
    assert result.reason_codes


def test_layer_version_constant() -> None:
    assert SURVIVAL_ASSESSMENT_LAYER_VERSION == "v1"


def test_valid_until_epoch_explicit_and_bounded() -> None:
    result = _evaluate(trading_epoch=43)
    assert result.valid_until_epoch == 46


def test_explicit_hard_fail_forces_fail() -> None:
    result = _evaluate(
        explicit_hard_fail_reasons=(SurvivalHardFailReason.EXPLICIT_HARD_FAIL,),
    )
    assert result.status is SurvivalAssessmentStatus.FAIL


def test_no_strategy_selection_fields_in_contract() -> None:
    result = _evaluate()
    serialized = serialize_survival_result_canonical(result)
    assert "selected_strategy" not in serialized.lower()
    assert "strategy_id" not in serialized.lower()


def test_module_has_no_evaluate_import_side_effects() -> None:
    source = inspect.getsource(evaluate_survival_assessment_v1)
    assert "import execution" not in source
    assert "import adapter" not in source
