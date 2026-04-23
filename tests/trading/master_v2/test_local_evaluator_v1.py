# tests/trading/master_v2/test_local_evaluator_v1.py
from __future__ import annotations

from trading.master_v2.decision_packet_fixtures_v1 import (
    sample_doubleplay_decision_v1,
    sample_risk_caps_result_v1,
    sample_safety_decision_v1,
    sample_scope_envelope_v1,
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


def test_layer_version() -> None:
    assert LOCAL_FLOW_LAYER_VERSION == "v1"


def test_reject_empty_correlation_id() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    r = evaluate_master_v2_local_flow_v1("   ", sei)
    _assert_typed_reject(r, "INVALID_CORRELATION_ID")


def test_reject_invalid_staged_type() -> None:
    r = evaluate_master_v2_local_flow_v1("c1", object())  # type: ignore[arg-type]
    assert r.flow_ok is False
    assert r.rejection_reason is not None
    assert "STAGED_INPUT_INVALID" in (r.rejection_reason or "")
    assert r.packet is None
    assert r.critic_report is None


def test_happy_path_matches_scenario() -> None:
    sc = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    s = sc.packet.staged
    r = evaluate_master_v2_local_flow_v1(
        sc.packet.correlation_id,
        s,
        universe=sc.packet.universe,
        doubleplay=sc.packet.doubleplay,
        scope_envelope=sc.packet.scope_envelope,
        risk_cap=sc.packet.risk_cap,
        safety=sc.packet.safety,
    )
    assert r.flow_ok is True
    assert r.rejection_reason is None
    assert r.packet is not None
    assert r.validation is not None and r.validation.ok
    assert r.critic_report is not None
    assert r.snapshot is not None
    validate_decision_packet_snapshot_v1(r.snapshot)


def test_safety_blocked_flow_not_ok() -> None:
    sc = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    s = sc.packet.staged
    r = evaluate_master_v2_local_flow_v1(sc.packet.correlation_id, s, safety=sc.packet.safety)
    assert r.flow_ok is False
    assert r.validation is not None and not r.validation.ok
    assert r.critic_report is not None
    assert r.critic_report.has_error_findings
    assert r.snapshot is None


def test_live_auth_flow_not_ok() -> None:
    sc = get_master_v2_scenario_case_v1(SCENARIO_LIVE_AUTH_MISSING_ACK)
    s = sc.packet.staged
    r = evaluate_master_v2_local_flow_v1(sc.packet.correlation_id, s, safety=sc.packet.safety)
    assert r.flow_ok is False
    assert "LIVE_AUTH_ACK_REQUIRED" in r.validation.reason_codes  # type: ignore[union-attr]


def test_optional_layers_ok_with_critic_warning() -> None:
    sc = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    s = sc.packet.staged
    r = evaluate_master_v2_local_flow_v1(sc.packet.correlation_id, s)
    assert r.flow_ok is True
    assert r.critic_report is not None
    assert any(f.code == "LAYER_MISSING_OPTIONAL" for f in r.critic_report.findings)


def test_with_snapshot_false() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    r = evaluate_master_v2_local_flow_v1(
        "dry-1",
        sei,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
        scope_envelope=sample_scope_envelope_v1(),
        risk_cap=sample_risk_caps_result_v1(),
        safety=sample_safety_decision_v1(),
        with_snapshot=False,
    )
    assert r.flow_ok is True
    assert r.snapshot is None
    assert r.rejection_reason is None


def test_result_is_typed() -> None:
    r = MasterV2LocalFlowResultV1(
        layer_version="v1",
        flow_ok=False,
        correlation_id="x",
    )
    assert r.packet is None


def _assert_typed_reject(r: MasterV2LocalFlowResultV1, code: str) -> None:
    assert r.flow_ok is False
    assert r.rejection_reason == code
    assert r.packet is None
    assert r.validation is None
    assert r.critic_report is None
