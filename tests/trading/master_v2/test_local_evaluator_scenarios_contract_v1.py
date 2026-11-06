"""Contract: Master V2 Scenario Harness v1 run_master_v2_scenario_matrix_v1 / assert_master_v2_scenario_harness_outcome_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
Matrix→Harness integration only — does not reopen MV2LE or MV2DC lanes.
"""

from __future__ import annotations

import copy

import pytest

from trading.master_v2.local_evaluator_scenarios_v1 import (
    SCENARIO_HARNESS_LAYER_VERSION,
    assert_master_v2_scenario_harness_outcome_v1,
    run_master_v2_scenario_case_v1,
    run_master_v2_scenario_matrix_v1,
)
from trading.master_v2.local_evaluator_v1 import (
    LOCAL_FLOW_LAYER_VERSION,
    MasterV2LocalFlowResultV1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    MasterV2ScenarioCaseV1,
    build_master_v2_scenario_matrix_v1,
    get_master_v2_scenario_case_v1,
    scenario_matrix_all_names_v1,
)

_CANONICAL_SCENARIO_ORDER = (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_SAFETY_BLOCKED,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
)

_POSITIVE_SCENARIOS = frozenset(
    {
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    }
)
_NEGATIVE_SCENARIOS = frozenset(
    {
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
    }
)

_NON_AUTHORIZING_KEYS = frozenset(
    {
        "authorized",
        "execution_started",
        "armed",
        "promoted",
        "live_started",
        "execution_authorized",
        "ready_for_operator_arming",
    }
)


def _assert_harness_result_contract(r: MasterV2LocalFlowResultV1) -> None:
    assert isinstance(r, MasterV2LocalFlowResultV1)
    assert r.layer_version == LOCAL_FLOW_LAYER_VERSION
    assert isinstance(r.flow_ok, bool)
    assert isinstance(r.correlation_id, str)
    for key in _NON_AUTHORIZING_KEYS:
        assert not hasattr(r, key)


def _run_case_without_mutation(
    name: str,
) -> tuple[MasterV2ScenarioCaseV1, MasterV2LocalFlowResultV1]:
    matrix_before = build_master_v2_scenario_matrix_v1()
    matrix_copy = copy.deepcopy(matrix_before)
    case = get_master_v2_scenario_case_v1(name)
    case_copy = copy.deepcopy(case)
    result = run_master_v2_scenario_case_v1(name)
    matrix_after = build_master_v2_scenario_matrix_v1()
    assert matrix_before == matrix_copy == matrix_after
    assert case == case_copy
    return case, result


def test_scenario_harness_v1_valid_baseline_consumes_matrix() -> None:
    assert SCENARIO_HARNESS_LAYER_VERSION == "v1"
    matrix = build_master_v2_scenario_matrix_v1()
    results = run_master_v2_scenario_matrix_v1()
    assert set(results.keys()) == set(matrix.keys()) == scenario_matrix_all_names_v1()


def test_scenario_harness_v1_complete_matrix_mapping_no_skips() -> None:
    matrix = build_master_v2_scenario_matrix_v1()
    results = run_master_v2_scenario_matrix_v1()
    assert len(results) == len(matrix) == 5
    for name, case in matrix.items():
        assert name in results
        r = results[name]
        _assert_harness_result_contract(r)
        assert_master_v2_scenario_harness_outcome_v1(case, r)


def test_scenario_harness_v1_deterministic_mapping_order() -> None:
    first = run_master_v2_scenario_matrix_v1()
    second = run_master_v2_scenario_matrix_v1()
    assert list(first.keys()) == list(_CANONICAL_SCENARIO_ORDER)
    assert list(second.keys()) == list(_CANONICAL_SCENARIO_ORDER)


@pytest.mark.parametrize("name", sorted(_POSITIVE_SCENARIOS))
def test_scenario_harness_v1_positive_scenarios_flow_ok_matches_validate_ok(name: str) -> None:
    case, r = _run_case_without_mutation(name)
    _assert_harness_result_contract(r)
    assert r.flow_ok is True
    assert r.flow_ok is case.expected.validate_ok
    assert r.rejection_reason is None
    assert_master_v2_scenario_harness_outcome_v1(case, r)


@pytest.mark.parametrize("name", sorted(_NEGATIVE_SCENARIOS))
def test_scenario_harness_v1_negative_scenarios_flow_ok_false(name: str) -> None:
    case, r = _run_case_without_mutation(name)
    _assert_harness_result_contract(r)
    assert r.flow_ok is False
    assert r.flow_ok is case.expected.validate_ok
    assert r.rejection_reason is None
    assert r.critic_report is not None
    assert r.critic_report.has_error_findings is True
    assert_master_v2_scenario_harness_outcome_v1(case, r)


def test_scenario_harness_v1_boundary_optional_layers_harness_ok_with_warning() -> None:
    case, r = _run_case_without_mutation(SCENARIO_OPTIONAL_LAYERS_MISSING)
    _assert_harness_result_contract(r)
    assert r.flow_ok is True
    assert case.expected.expect_critic_warning_layer_missing is True
    assert r.snapshot is not None
    assert_master_v2_scenario_harness_outcome_v1(case, r)


def test_scenario_harness_v1_expected_outcome_assertion_contract() -> None:
    matrix = build_master_v2_scenario_matrix_v1()
    for name in _CANONICAL_SCENARIO_ORDER:
        case = matrix[name]
        r = run_master_v2_scenario_case_v1(name)
        assert r.validation is not None
        assert r.validation.ok is case.expected.validate_ok
        assert_master_v2_scenario_harness_outcome_v1(case, r)


def test_scenario_harness_v1_fail_closed_unknown_scenario() -> None:
    with pytest.raises(KeyError, match="unbekanntes szenario"):
        run_master_v2_scenario_case_v1("no_such_harness_scenario")


def test_scenario_harness_v1_deterministic_repeat_identical_results() -> None:
    for name in _CANONICAL_SCENARIO_ORDER:
        first = run_master_v2_scenario_case_v1(name)
        second = run_master_v2_scenario_case_v1(name)
        assert first == second


def test_scenario_harness_v1_non_mutation_matrix_and_case_inputs() -> None:
    matrix = build_master_v2_scenario_matrix_v1()
    matrix_copy = copy.deepcopy(matrix)
    results = run_master_v2_scenario_matrix_v1()
    assert matrix == matrix_copy
    for name, case in matrix.items():
        assert case.packet == matrix_copy[name].packet
        assert results[name].packet == case.packet


def test_scenario_harness_v1_non_authorizing_flow_result() -> None:
    case, r = _run_case_without_mutation(SCENARIO_HAPPY_LIVE_GATED)
    _assert_harness_result_contract(r)
    assert r.flow_ok is True
    for key in _NON_AUTHORIZING_KEYS:
        assert not hasattr(r, key)
    assert_master_v2_scenario_harness_outcome_v1(case, r)
