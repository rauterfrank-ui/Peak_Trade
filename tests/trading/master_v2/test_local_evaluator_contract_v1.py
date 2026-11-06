"""Contract: Master V2 Local Evaluator v1 evaluate_master_v2_local_flow_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy

from trading.master_v2.decision_packet_fixtures_v1 import (
    sample_doubleplay_decision_v1,
    sample_risk_caps_result_v1,
    sample_safety_decision_v1,
    sample_scope_envelope_v1,
    sample_staged_execution_enablement_input_v1,
    sample_universe_selection_v1,
)
from trading.master_v2.decision_packet_snapshot_v1 import validate_decision_packet_snapshot_v1
from trading.master_v2.local_evaluator_v1 import (
    LOCAL_FLOW_LAYER_VERSION,
    MasterV2LocalFlowResultV1,
    evaluate_master_v2_local_flow_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_SAFETY_BLOCKED,
    get_master_v2_scenario_case_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

_EXPECTED_STRUCTURAL_REJECTION_REASONS = frozenset(
    {
        "INVALID_CORRELATION_ID",
    }
)


def _assert_local_flow_result_contract(r: MasterV2LocalFlowResultV1) -> None:
    assert isinstance(r, MasterV2LocalFlowResultV1)
    assert r.layer_version == LOCAL_FLOW_LAYER_VERSION
    assert isinstance(r.flow_ok, bool)
    assert isinstance(r.correlation_id, str)
    if r.rejection_reason is not None:
        assert isinstance(r.rejection_reason, str) and r.rejection_reason
    if r.rejection_reason in _EXPECTED_STRUCTURAL_REJECTION_REASONS:
        assert r.flow_ok is False
        assert r.packet is None
        assert r.validation is None
        assert r.critic_report is None
        assert r.snapshot is None
    elif r.rejection_reason is not None and r.rejection_reason.startswith("STAGED_INPUT_INVALID"):
        assert r.flow_ok is False
        assert r.packet is None
        assert r.validation is None
        assert r.critic_report is None
        assert r.snapshot is None


def _evaluate_without_mutation(
    correlation_id: str,
    staged: StagedExecutionEnablementInputV1,
    *,
    universe=None,
    doubleplay=None,
    scope_envelope=None,
    risk_cap=None,
    safety=None,
    with_snapshot: bool = True,
) -> MasterV2LocalFlowResultV1:
    staged_copy = copy.deepcopy(staged)
    universe_copy = copy.deepcopy(universe)
    doubleplay_copy = copy.deepcopy(doubleplay)
    scope_copy = copy.deepcopy(scope_envelope)
    risk_copy = copy.deepcopy(risk_cap)
    safety_copy = copy.deepcopy(safety)
    r = evaluate_master_v2_local_flow_v1(
        correlation_id,
        staged,
        universe=universe,
        doubleplay=doubleplay,
        scope_envelope=scope_envelope,
        risk_cap=risk_cap,
        safety=safety,
        with_snapshot=with_snapshot,
    )
    assert staged == staged_copy
    assert universe == universe_copy
    assert doubleplay == doubleplay_copy
    assert scope_envelope == scope_copy
    assert risk_cap == risk_copy
    assert safety == safety_copy
    return r


def test_evaluator_v1_valid_baseline_flow_ok_true_wire_shape() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = case.packet
    r = _evaluate_without_mutation(
        p.correlation_id,
        p.staged,
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is True
    assert r.rejection_reason is None
    assert r.correlation_id == p.correlation_id
    assert r.packet == p
    assert r.validation is not None and r.validation.ok
    assert r.critic_report is not None
    assert r.snapshot is not None
    validate_decision_packet_snapshot_v1(r.snapshot)


def test_evaluator_v1_optional_layers_missing_flow_ok_with_critic_warning() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    r = _evaluate_without_mutation(case.packet.correlation_id, case.packet.staged)
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is True
    assert r.validation is not None and r.validation.ok
    assert r.critic_report is not None
    assert any(f.code == "LAYER_MISSING_OPTIONAL" for f in r.critic_report.findings)


def test_evaluator_v1_correlation_id_stripped_on_success() -> None:
    sei = sample_staged_execution_enablement_input_v1()
    r = _evaluate_without_mutation(
        "  mv2le-strip-test  ",
        sei,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
        scope_envelope=sample_scope_envelope_v1(),
        risk_cap=sample_risk_caps_result_v1(),
        safety=sample_safety_decision_v1(),
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is True
    assert r.correlation_id == "mv2le-strip-test"
    assert r.packet is not None
    assert r.packet.correlation_id == "mv2le-strip-test"


def test_evaluator_v1_with_snapshot_false_no_snapshot_field() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    r = _evaluate_without_mutation(
        "dry-no-snap",
        sei,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
        scope_envelope=sample_scope_envelope_v1(),
        risk_cap=sample_risk_caps_result_v1(),
        safety=sample_safety_decision_v1(),
        with_snapshot=False,
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is True
    assert r.snapshot is None
    assert r.rejection_reason is None


def test_evaluator_v1_negative_safety_blocked_flow_not_ok() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    r = _evaluate_without_mutation(
        case.packet.correlation_id,
        case.packet.staged,
        safety=case.packet.safety,
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is False
    assert r.validation is not None and not r.validation.ok
    assert r.critic_report is not None
    assert r.critic_report.has_error_findings
    assert r.snapshot is None


def test_evaluator_v1_negative_live_auth_missing_ack_flow_not_ok() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_LIVE_AUTH_MISSING_ACK)
    r = _evaluate_without_mutation(
        case.packet.correlation_id,
        case.packet.staged,
        safety=case.packet.safety,
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is False
    assert r.validation is not None
    assert "LIVE_AUTH_ACK_REQUIRED" in r.validation.reason_codes  # type: ignore[union-attr]


def test_evaluator_v1_fail_closed_invalid_correlation_id() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    r = evaluate_master_v2_local_flow_v1("   ", sei)
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is False
    assert r.rejection_reason == "INVALID_CORRELATION_ID"


def test_evaluator_v1_fail_closed_invalid_staged_type() -> None:
    r = evaluate_master_v2_local_flow_v1("c1", object())  # type: ignore[arg-type]
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is False
    assert r.rejection_reason is not None
    assert r.rejection_reason.startswith("STAGED_INPUT_INVALID")


def test_evaluator_v1_fail_closed_invalid_staged_field_values() -> None:
    inp = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    bad = copy.copy(inp)
    object.__setattr__(bad, "safety_decision_allowed", None)  # type: ignore[arg-type]
    r = evaluate_master_v2_local_flow_v1("mv2le-bad-staged", bad)
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is False
    assert r.rejection_reason is not None
    assert r.rejection_reason.startswith("STAGED_INPUT_INVALID")


def test_evaluator_v1_deterministic_output_for_identical_input() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = case.packet
    kwargs = dict(
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
    )
    first = evaluate_master_v2_local_flow_v1(p.correlation_id, p.staged, **kwargs)
    second = evaluate_master_v2_local_flow_v1(p.correlation_id, p.staged, **kwargs)
    assert first == second


def test_evaluator_v1_deterministic_repeat_with_snapshot() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = case.packet
    kwargs = dict(
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
        with_snapshot=True,
    )
    first = evaluate_master_v2_local_flow_v1(p.correlation_id, p.staged, **kwargs)
    second = evaluate_master_v2_local_flow_v1(p.correlation_id, p.staged, **kwargs)
    assert first == second
    assert first.snapshot == second.snapshot


def test_evaluator_v1_non_authorizing_flow_ok_true_is_evaluation_only() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = case.packet
    r = _evaluate_without_mutation(
        p.correlation_id,
        p.staged,
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
    )
    _assert_local_flow_result_contract(r)
    assert r.flow_ok is True
    assert isinstance(r, MasterV2LocalFlowResultV1)
    assert not hasattr(r, "authorized")
    assert not hasattr(r, "execution_started")
    assert not hasattr(r, "armed")
    assert not hasattr(r, "promoted")
    assert not hasattr(r, "live_started")


def test_evaluator_v1_non_authorizing_does_not_mutate_staged_and_handoffs() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = case.packet
    _evaluate_without_mutation(
        p.correlation_id,
        p.staged,
        universe=p.universe,
        doubleplay=p.doubleplay,
        scope_envelope=p.scope_envelope,
        risk_cap=p.risk_cap,
        safety=p.safety,
    )
