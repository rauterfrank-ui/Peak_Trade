"""Unusable economic numbers are blocked before the unchanged sealed owner."""

from dataclasses import replace
import json

import pytest

from trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus
from trading.master_v2.survival_numeric_admission_v1 import (
    compute_expected_roundtrip_cost,
    compute_net_expected_edge,
    evaluate_survival_with_numeric_admission_v1 as evaluate_survival_assessment_v1,
    serialize_survival_result_strict_v1 as serialize_survival_result_canonical,
)
from tests.trading.master_v2.test_survival_assessment_v1 import _input, _policy


COST_FIELDS = (
    "entry_fee",
    "expected_entry_slippage",
    "exit_fee",
    "expected_exit_slippage",
    "expected_funding_cost",
    "expected_gross_edge",
)
RATIO_FIELDS = (
    "volatility_survival_ratio",
    "sequence_survival_ratio",
    "drawdown_survival_ratio",
    "liquidation_buffer_ratio",
)
INVALID_NUMBERS = [float("nan"), float("inf"), -float("inf"), True, "0.5", 10**400]
INVALID_IDS = ["nan", "inf", "negative_inf", "bool", "string", "overflowing_int"]


def assert_blocked(inp, policy=None):
    result = evaluate_survival_assessment_v1(inp, policy or _policy())
    assert result.status is SurvivalAssessmentStatus.BLOCKED
    assert result.expected_gross_edge is None
    assert result.expected_roundtrip_cost is None
    assert result.net_expected_edge is None
    assert result.authority_effect == result.runtime_effect == result.order_effect == "NONE"
    assert result.risk_effect == "NONE"
    # No NaN/Infinity JSON tokens, even on the non-authorizing failure record.
    canonical = serialize_survival_result_canonical(result)
    json.loads(canonical, parse_constant=lambda value: pytest.fail(value))
    return result


@pytest.mark.parametrize("field", COST_FIELDS)
@pytest.mark.parametrize("value", INVALID_NUMBERS, ids=INVALID_IDS)
def test_invalid_cost_input_blocks(field, value):
    inp = _input()
    result = assert_blocked(replace(inp, cost_inputs=replace(inp.cost_inputs, **{field: value})))
    assert "cost_input_invalid:" + field in result.reason_codes


@pytest.mark.parametrize("field", RATIO_FIELDS)
@pytest.mark.parametrize("value", INVALID_NUMBERS, ids=INVALID_IDS)
def test_invalid_metric_input_blocks(field, value):
    inp = _input()
    result = assert_blocked(
        replace(inp, metric_inputs=replace(inp.metric_inputs, **{field: value}))
    )
    assert "metric_input_invalid:" + field in result.reason_codes


@pytest.mark.parametrize("value", [1, "False", [], float("nan")])
@pytest.mark.parametrize("field", ["funding_cost_required", "data_completeness_complete"])
def test_boolean_economic_inputs_are_not_truthy_coerced(field, value):
    inp = _input()
    if field == "funding_cost_required":
        inp = replace(inp, cost_inputs=replace(inp.cost_inputs, **{field: value}))
    else:
        inp = replace(inp, metric_inputs=replace(inp.metric_inputs, **{field: value}))
    assert_blocked(inp)


@pytest.mark.parametrize("field", ["min_net_edge", *("min_" + f for f in RATIO_FIELDS)])
@pytest.mark.parametrize("value", INVALID_NUMBERS, ids=INVALID_IDS)
def test_invalid_numeric_policy_blocks(field, value):
    result = assert_blocked(_input(), replace(_policy(), **{field: value}))
    assert "policy_validation_failed" in result.reason_codes


@pytest.mark.parametrize("value", [0, -1, True, 1.5, float("nan"), "3"])
def test_invalid_validity_yields_serializable_blocked_record(value):
    result = assert_blocked(_input(), replace(_policy(), validity_epochs=value))
    assert "policy_validity_epochs_invalid" in result.blocked_reasons
    assert result.valid_until_epoch == result.trading_epoch + 1


@pytest.mark.parametrize("field", ["entry_fee", "expected_gross_edge"])
def test_finite_input_arithmetic_overflow_blocks(field):
    inp = _input()
    values = {"entry_fee": 1e308, "exit_fee": 1e308}
    if field == "expected_gross_edge":
        values = {"expected_gross_edge": -1e308, "entry_fee": 1e308}
    result = assert_blocked(replace(inp, cost_inputs=replace(inp.cost_inputs, **values)))
    assert "cost_arithmetic_nonfinite" in result.blocked_reasons


@pytest.mark.parametrize("value", INVALID_NUMBERS, ids=INVALID_IDS)
def test_public_cost_helpers_do_not_emit_unusable_numbers(value):
    assert compute_expected_roundtrip_cost(replace(_input().cost_inputs, entry_fee=value)) is None
    assert compute_net_expected_edge(expected_gross_edge=value, expected_roundtrip_cost=0) is None
    assert compute_net_expected_edge(expected_gross_edge=0, expected_roundtrip_cost=value) is None


def test_finite_signed_economics_and_original_ratio_thresholds_are_preserved():
    inp = _input()
    # No new fee, funding, edge, or ratio bound is invented by numeric admission.
    costs = replace(inp.cost_inputs, entry_fee=-0.0001, expected_funding_cost=-0.0002)
    metrics = replace(inp.metric_inputs, volatility_survival_ratio=1.5)
    admitted = evaluate_survival_assessment_v1(
        replace(inp, cost_inputs=costs, metric_inputs=metrics), _policy()
    )
    assert admitted.status is SurvivalAssessmentStatus.PASS
    assert admitted.expected_roundtrip_cost == pytest.approx(0.0006)
    losing = evaluate_survival_assessment_v1(
        replace(inp, cost_inputs=replace(costs, expected_gross_edge=-0.02)), _policy()
    )
    assert losing.status is SurvivalAssessmentStatus.FAIL


def test_optional_funding_none_is_preserved_but_an_invalid_supplied_value_blocks():
    inp = _input()
    costs = replace(inp.cost_inputs, funding_cost_required=False, expected_funding_cost=None)
    assert (
        evaluate_survival_assessment_v1(replace(inp, cost_inputs=costs), _policy()).status
        is SurvivalAssessmentStatus.PASS
    )
    assert_blocked(replace(inp, cost_inputs=replace(costs, expected_funding_cost=float("nan"))))


def test_serializer_rejects_nonfinite_manually_constructed_result():
    result = evaluate_survival_assessment_v1(_input(), _policy())
    with pytest.raises(ValueError):
        serialize_survival_result_canonical(replace(result, expected_gross_edge=float("nan")))


def test_direct_legacy_owner_is_not_silently_redefined_as_current_admission():
    from trading.master_v2 import survival_assessment_v1 as original

    inp = _input()
    inp = replace(inp, cost_inputs=replace(inp.cost_inputs, entry_fee=float("nan")))
    legacy = original.evaluate_survival_assessment_v1(inp, _policy())
    assert legacy.status is SurvivalAssessmentStatus.PASS
    assert_blocked(inp)
    with pytest.raises(ValueError):
        serialize_survival_result_canonical(legacy)
