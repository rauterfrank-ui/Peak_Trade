"""Contract: Master V2 Decision Packet Critic v1 findings and fail-closed posture.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy

from trading.master_v2.decision_packet_critic_v1 import (
    DECISION_PACKET_CRITIC_LAYER_VERSION,
    CriticFindingSeverityV1,
    DecisionPacketCriticFindingV1,
    DecisionPacketCriticReportV1,
    critique_master_v2_decision_packet_v1,
)
from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
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

_EXPECTED_ERROR_CODES = frozenset(
    {
        "SAFETY_ENABLEMENT_MISMATCH",
        "BLOCKED_BUT_ENABLEMENT_ALLOWED",
        "LIVE_AUTH_ACK_MISSING",
    }
)
_EXPECTED_WARNING_CODES = frozenset({"LAYER_MISSING_OPTIONAL"})


def _assert_finding_contract(f: DecisionPacketCriticFindingV1) -> None:
    assert isinstance(f.code, str) and f.code
    assert isinstance(f.message, str) and f.message
    assert isinstance(f.severity, CriticFindingSeverityV1)
    assert f.severity in (CriticFindingSeverityV1.ERROR, CriticFindingSeverityV1.WARNING)


def _assert_report_contract(cr: DecisionPacketCriticReportV1) -> None:
    assert cr.layer_version == DECISION_PACKET_CRITIC_LAYER_VERSION
    assert isinstance(cr.findings, list)
    for f in cr.findings:
        _assert_finding_contract(f)


def _critique_without_mutation(packet: MasterV2DecisionPacketV1) -> DecisionPacketCriticReportV1:
    original = copy.deepcopy(packet)
    cr = critique_master_v2_decision_packet_v1(packet)
    assert packet == original
    return cr


def test_critic_v1_layer_version_contract() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    cr = _critique_without_mutation(case.packet)
    assert cr.layer_version == "v1"


def test_critic_v1_valid_baseline_no_unexpected_findings() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    v = validate_master_v2_decision_packet_v1(case.packet)
    assert v.ok is True

    cr = _critique_without_mutation(case.packet)
    _assert_report_contract(cr)
    assert cr.findings == []
    assert cr.has_error_findings is False


def test_critic_v1_error_finding_safety_enablement_mismatch() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    cr = _critique_without_mutation(case.packet)
    _assert_report_contract(cr)
    assert cr.has_error_findings is True

    codes = [f.code for f in cr.findings]
    assert codes == ["SAFETY_ENABLEMENT_MISMATCH"]
    finding = cr.findings[0]
    assert finding.severity is CriticFindingSeverityV1.ERROR
    assert finding.code in _EXPECTED_ERROR_CODES
    assert "safety handoff" in finding.message


def test_critic_v1_error_finding_blocked_but_enablement_allowed() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_RISK_BLOCKED)
    cr = _critique_without_mutation(case.packet)
    _assert_report_contract(cr)
    assert cr.has_error_findings is True

    codes = [f.code for f in cr.findings]
    assert codes == ["BLOCKED_BUT_ENABLEMENT_ALLOWED"]
    finding = cr.findings[0]
    assert finding.severity is CriticFindingSeverityV1.ERROR
    assert finding.code in _EXPECTED_ERROR_CODES
    assert "risiko cap" in finding.message


def test_critic_v1_error_finding_live_auth_ack_missing() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_LIVE_AUTH_MISSING_ACK)
    cr = _critique_without_mutation(case.packet)
    _assert_report_contract(cr)
    assert cr.has_error_findings is True

    codes = [f.code for f in cr.findings]
    assert codes == ["LIVE_AUTH_ACK_MISSING"]
    finding = cr.findings[0]
    assert finding.severity is CriticFindingSeverityV1.ERROR
    assert finding.code in _EXPECTED_ERROR_CODES
    assert "live_authority_acknowledged" in finding.message


def test_critic_v1_warning_finding_layer_missing_optional() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    v = validate_master_v2_decision_packet_v1(case.packet)
    assert v.ok is True

    cr = _critique_without_mutation(case.packet)
    _assert_report_contract(cr)
    assert cr.has_error_findings is False

    codes = [f.code for f in cr.findings]
    assert codes == ["LAYER_MISSING_OPTIONAL"]
    finding = cr.findings[0]
    assert finding.severity is CriticFindingSeverityV1.WARNING
    assert finding.code in _EXPECTED_WARNING_CODES
    assert "optional handoffs missing" in finding.message
    for layer in ("universe", "doubleplay", "scope_envelope", "risk_cap"):
        assert layer in finding.message


def test_critic_v1_severity_enum_canonical_values() -> None:
    assert CriticFindingSeverityV1.ERROR.value == "error"
    assert CriticFindingSeverityV1.WARNING.value == "warning"

    error_case = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    warning_case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    error_cr = critique_master_v2_decision_packet_v1(error_case.packet)
    warning_cr = critique_master_v2_decision_packet_v1(warning_case.packet)

    assert error_cr.findings[0].severity.value == "error"
    assert warning_cr.findings[0].severity.value == "warning"


def test_critic_v1_deterministic_output_for_identical_input() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    first = critique_master_v2_decision_packet_v1(case.packet)
    second = critique_master_v2_decision_packet_v1(case.packet)
    assert first.layer_version == second.layer_version
    assert [(f.code, f.message, f.severity) for f in first.findings] == [
        (f.code, f.message, f.severity) for f in second.findings
    ]


def test_critic_v1_multiple_error_findings_deterministic_order() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    packet = build_master_v2_decision_packet_v1(
        "dpcr-multi-error",
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
    v = validate_master_v2_decision_packet_v1(packet)
    assert v.ok is False
    assert len(v.reason_codes) >= 2

    cr = _critique_without_mutation(packet)
    _assert_report_contract(cr)
    assert cr.has_error_findings is True
    codes = [f.code for f in cr.findings]
    assert codes == [
        "SAFETY_ENABLEMENT_MISMATCH",
        "BLOCKED_BUT_ENABLEMENT_ALLOWED",
        "LIVE_AUTH_ACK_MISSING",
    ]
    assert all(f.severity is CriticFindingSeverityV1.ERROR for f in cr.findings)

    repeat = critique_master_v2_decision_packet_v1(packet)
    assert [f.code for f in repeat.findings] == codes


def test_critic_v1_fail_closed_has_error_findings_property() -> None:
    error_case = get_master_v2_scenario_case_v1(SCENARIO_RISK_BLOCKED)
    warning_case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)

    error_cr = critique_master_v2_decision_packet_v1(error_case.packet)
    warning_cr = critique_master_v2_decision_packet_v1(warning_case.packet)

    assert error_cr.has_error_findings is True
    assert warning_cr.has_error_findings is False


def test_critic_v1_non_authorizing_does_not_mutate_input_packet() -> None:
    for name in (
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    ):
        case = get_master_v2_scenario_case_v1(name)
        _critique_without_mutation(case.packet)
