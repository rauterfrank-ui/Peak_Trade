"""Contract: Master V2 Decision Packet v1 validate_master_v2_decision_packet_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy

from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    MasterV2DecisionPacketValidationV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    build_master_v2_decision_packet_v1,
    validate_master_v2_decision_packet_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    get_master_v2_scenario_case_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

_EXPECTED_REASON_CODES = frozenset(
    {
        "SAFETY_HANDOFF_STAGED_INPUT_MISMATCH",
        "RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED",
        "LIVE_AUTH_ACK_REQUIRED",
    }
)


def _assert_validation_contract(v: MasterV2DecisionPacketValidationV1) -> None:
    assert isinstance(v, MasterV2DecisionPacketValidationV1)
    assert isinstance(v.ok, bool)
    assert isinstance(v.reason_codes, tuple)
    for code in v.reason_codes:
        assert isinstance(code, str) and code
        assert code in _EXPECTED_REASON_CODES


def _validate_without_mutation(
    packet: MasterV2DecisionPacketV1,
) -> MasterV2DecisionPacketValidationV1:
    original = copy.deepcopy(packet)
    v = validate_master_v2_decision_packet_v1(packet)
    assert packet == original
    return v


def test_validate_v1_valid_baseline_ok_true_empty_reason_codes() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    v = _validate_without_mutation(case.packet)
    _assert_validation_contract(v)
    assert v.ok is True
    assert v.reason_codes == ()


def test_validate_v1_optional_layers_missing_still_ok_true() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    v = _validate_without_mutation(case.packet)
    _assert_validation_contract(v)
    assert v.ok is True
    assert v.reason_codes == ()


def test_validate_v1_safety_handoff_staged_input_mismatch() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    v = _validate_without_mutation(case.packet)
    _assert_validation_contract(v)
    assert v.ok is False
    assert v.reason_codes == ("SAFETY_HANDOFF_STAGED_INPUT_MISMATCH",)


def test_validate_v1_risk_cap_blocked_but_enablement_allowed() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_RISK_BLOCKED)
    v = _validate_without_mutation(case.packet)
    _assert_validation_contract(v)
    assert v.ok is False
    assert v.reason_codes == ("RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED",)


def test_validate_v1_live_auth_ack_required() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_LIVE_AUTH_MISSING_ACK)
    v = _validate_without_mutation(case.packet)
    _assert_validation_contract(v)
    assert v.ok is False
    assert v.reason_codes == ("LIVE_AUTH_ACK_REQUIRED",)


def test_validate_v1_multiple_reason_codes_deterministic_order() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    packet = build_master_v2_decision_packet_v1(
        "dpv-multi-error",
        sei,
        risk_cap=RiskExposureCapHandoffV1(
            layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
            cap_satisfied=False,
        ),
        safety=SafetyKillSwitchHandoffV1(
            layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
            safety_decision_allowed=False,
        ),
    )
    v = _validate_without_mutation(packet)
    _assert_validation_contract(v)
    assert v.ok is False
    assert v.reason_codes == (
        "SAFETY_HANDOFF_STAGED_INPUT_MISMATCH",
        "RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED",
        "LIVE_AUTH_ACK_REQUIRED",
    )

    repeat = validate_master_v2_decision_packet_v1(packet)
    assert repeat.reason_codes == v.reason_codes


def test_validate_v1_risk_cap_absent_skips_blocked_check() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    packet = build_master_v2_decision_packet_v1(
        "dpv-no-risk-cap",
        sei,
        safety=SafetyKillSwitchHandoffV1(
            layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
            safety_decision_allowed=sei.safety_decision_allowed,
        ),
    )
    v = _validate_without_mutation(packet)
    _assert_validation_contract(v)
    assert v.ok is True
    assert v.reason_codes == ()


def test_validate_v1_safety_absent_skips_mismatch_check() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    packet = MasterV2DecisionPacketV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        correlation_id="dpv-no-safety",
        staged=sei,
        safety=None,
    )
    v = _validate_without_mutation(packet)
    _assert_validation_contract(v)
    assert v.ok is True
    assert v.reason_codes == ()


def test_validate_v1_deterministic_output_for_identical_input() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_RISK_BLOCKED)
    first = validate_master_v2_decision_packet_v1(case.packet)
    second = validate_master_v2_decision_packet_v1(case.packet)
    assert first.ok == second.ok
    assert first.reason_codes == second.reason_codes


def test_validate_v1_fail_closed_ok_false_on_contradictions() -> None:
    for name in (
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
    ):
        case = get_master_v2_scenario_case_v1(name)
        v = validate_master_v2_decision_packet_v1(case.packet)
        assert v.ok is False
        assert len(v.reason_codes) >= 1


def test_validate_v1_non_authorizing_ok_true_is_validator_success_only() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    v = _validate_without_mutation(case.packet)
    assert v.ok is True
    assert isinstance(v, MasterV2DecisionPacketValidationV1)
    assert not hasattr(v, "authorized")
    assert not hasattr(v, "execution_started")
    assert not hasattr(v, "armed")
    assert not hasattr(v, "promoted")
    assert not hasattr(v, "live_started")


def test_validate_v1_non_authorizing_does_not_mutate_input_packet() -> None:
    for name in (
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    ):
        case = get_master_v2_scenario_case_v1(name)
        _validate_without_mutation(case.packet)
