"""Tests for CAPABILITY_11_6 long-running autonomous Testnet evidence."""

from __future__ import annotations

import pytest

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_capability_11_5_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.long_running_campaign_evidence_contract_v1 import (
    LongRunningCampaignEvidenceError,
    prove_long_running_campaign_evidence_contract_v1,
    refuse_cap_11_7_live_private_readonly_v1,
    refuse_long_running_campaign_activation_v1,
    refuse_long_running_campaign_network_session_v1,
    run_long_running_campaign_evidence_fixture_path_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.observability_audit_evidence_contract_v1 import (
    ObservabilityAuditEvidenceError,
    build_observability_domain_evidence_record_v1,
    prove_observability_audit_evidence_contract_v1,
    refuse_dashboard_trading_authority_v1,
    refuse_observability_network_side_effect_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.testnet_evidence_closure_contract_v1 import (
    TestnetEvidenceClosureError,
    build_testnet_evidence_closure_field_record_v1,
    prove_testnet_evidence_closure_contract_v1,
    refuse_testnet_evidence_activation_v1,
    refuse_testnet_proven_overclaim_v1,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.verifier_v1 import (
    verify_capability_11_6_v1,
)


def test_long_running_campaign_evidence_fixture_paths() -> None:
    for path_name in (
        "long_running_autonomous_campaign_continuity",
        "long_running_autonomous_campaign_degradation_evidence",
        "long_running_autonomous_campaign_evidence_cursor",
    ):
        record = run_long_running_campaign_evidence_fixture_path_v1(path_name=path_name)
        assert record.terminal_state == "EVIDENCED"
        assert record.campaign_activated is False
        assert record.exchange_submit_performed is False
        assert record.source == "FIXTURE_ONLY"
    with pytest.raises(LongRunningCampaignEvidenceError, match="UNKNOWN_LONG_RUNNING"):
        run_long_running_campaign_evidence_fixture_path_v1(path_name="invented_campaign")
    with pytest.raises(LongRunningCampaignEvidenceError, match="ACTIVATION_FORBIDDEN"):
        refuse_long_running_campaign_activation_v1(campaign_id="campaign-demo")
    with pytest.raises(LongRunningCampaignEvidenceError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_long_running_campaign_network_session_v1(session_id="session-demo")
    with pytest.raises(LongRunningCampaignEvidenceError, match="CAPABILITY_11_7_SURFACE_FORBIDDEN"):
        refuse_cap_11_7_live_private_readonly_v1(claimed_surface="live_private_read_only")
    proof = prove_long_running_campaign_evidence_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_EVIDENCE_VERIFIED"] is False
    assert proof["LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED"] is False
    assert proof["CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED"] is False


def test_testnet_evidence_closure_contract_no_proven_overclaim() -> None:
    record = build_testnet_evidence_closure_field_record_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    assert record.contract_bound is True
    assert record.proven_claimed is False
    with pytest.raises(TestnetEvidenceClosureError, match="UNKNOWN_TESTNET_CLOSURE"):
        build_testnet_evidence_closure_field_record_v1(field_name="LIVE_ORDER_LIFECYCLE_PROVEN")
    with pytest.raises(TestnetEvidenceClosureError, match="PROVEN_OVERCLAIM_FORBIDDEN"):
        refuse_testnet_proven_overclaim_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    with pytest.raises(TestnetEvidenceClosureError, match="EVIDENCE_ACTIVATION_FORBIDDEN"):
        refuse_testnet_evidence_activation_v1(claimed_action="mark_verified")
    proof = prove_testnet_evidence_closure_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_EVIDENCE_VERIFIED"] is False
    assert proof["TESTNET_KILL_SWITCH_PROVEN"] is False
    assert proof["TESTNET_EVIDENCE_CLOSURE_CONTRACT_ACTIVATED"] is False


def test_observability_audit_evidence_contract() -> None:
    record = build_observability_domain_evidence_record_v1(domain="evidence_cursor_health")
    assert record.telemetry_declared is True
    assert record.dashboard_trading_authority is False
    assert record.audit_chain_bound is True
    with pytest.raises(ObservabilityAuditEvidenceError, match="UNKNOWN_OBSERVABILITY_DOMAIN"):
        build_observability_domain_evidence_record_v1(domain="live_submit_authority")
    with pytest.raises(ObservabilityAuditEvidenceError, match="DASHBOARD_TRADING_AUTHORITY"):
        refuse_dashboard_trading_authority_v1(claimed_action="submit_order")
    with pytest.raises(ObservabilityAuditEvidenceError, match="NETWORK_SIDE_EFFECT_FORBIDDEN"):
        refuse_observability_network_side_effect_v1(claimed_effect="private_stream_connect")
    proof = prove_observability_audit_evidence_contract_v1()
    assert proof["ok"] is True
    assert proof["OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_ACTIVATED"] is False
    assert proof["DASHBOARD_TRADING_AUTHORITY"] is False


def test_capability_11_1_to_11_5_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    dep_11_5 = prove_capability_11_5_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_5["ok"] is True
    assert dep_11_5["CAPABILITY_11_5_NOT_ACTIVATED_RETAINED"] is True


def test_negative_reachability_parity_and_ownership() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    assert reach["TESTNET_EXECUTION_ADAPTER_ACTIVATED"] is False
    assert reach["CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED"] is True
    assert reach["LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED"] is False
    assert reach["CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["LONG_RUNNING_CAMPAIGN_EVIDENCE_OWNER"].endswith(
        "capability_11_6_long_running_autonomous_testnet_evidence_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "long_running_campaign_evidence" in matrix_fields
    assert "testnet_evidence_closure" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_6_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6"] is False
    assert claims["TESTNET_EVIDENCE_VERIFIED"] is False
    assert claims["TESTNET_RESTART_PROVEN"] is False
    assert claims["TESTNET_KILL_SWITCH_PROVEN"] is False
    assert claims["CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED"] is True
    assert claims["LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED"] is False
    assert claims["CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED"] is False
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_4_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_5_DEPENDENCY_SATISFIED"] is True
    assert claims["LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND"] is True
    assert claims["TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND"] is True
    assert claims["OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND"] is True
    assert claims["LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED"] is False
