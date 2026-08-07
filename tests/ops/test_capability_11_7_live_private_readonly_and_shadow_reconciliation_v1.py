"""Tests for CAPABILITY_11_7 Live private read-only and shadow reconciliation."""

from __future__ import annotations

import pytest

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_capability_11_4_dependency_retained_v1,
    prove_capability_11_5_dependency_retained_v1,
    prove_capability_11_6_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.live_evidence_ladder_contract_v1 import (
    LiveEvidenceLadderError,
    build_live_evidence_ladder_field_record_v1,
    prove_live_evidence_ladder_contract_v1,
    refuse_live_evidence_activation_v1,
    refuse_live_evidence_proven_overclaim_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.live_private_readonly_port_v1 import (
    LivePrivateReadonlyPortError,
    construct_live_private_readonly_port_v1,
    prove_live_private_readonly_port_v1,
    refuse_live_private_readonly_credential_access_v1,
    refuse_live_private_readonly_mutation_v1,
    refuse_live_private_readonly_network_fetch_v1,
    refuse_live_private_readonly_network_session_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.live_shadow_reconciliation_contract_v1 import (
    LiveShadowReconciliationError,
    build_live_shadow_reconciliation_checkpoint_v1,
    prove_live_shadow_reconciliation_contract_v1,
    refuse_cap_11_8_live_dry_run_order_plan_v1,
    refuse_live_shadow_exchange_fetch_v1,
    refuse_live_shadow_reconciliation_activation_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.verifier_v1 import (
    verify_capability_11_7_v1,
)


def test_live_private_readonly_port_declaration_fail_closed() -> None:
    proof = prove_live_private_readonly_port_v1()
    assert proof["ok"] is True
    assert proof["LIVE_PRIVATE_READONLY_PORT_DECLARED"] is True
    assert proof["LIVE_PRIVATE_READONLY_PORT_CONSTRUCTIBLE"] is False
    assert proof["LIVE_PRIVATE_READONLY_ACTIVATED"] is False
    assert proof["PRIVATE_NETWORK_SESSION_STARTED"] is False
    assert proof["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    with pytest.raises(LivePrivateReadonlyPortError, match="CONSTRUCTION_FORBIDDEN"):
        construct_live_private_readonly_port_v1()
    with pytest.raises(LivePrivateReadonlyPortError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_live_private_readonly_network_session_v1(session_id="session-demo")
    with pytest.raises(LivePrivateReadonlyPortError, match="NETWORK_FETCH_FORBIDDEN"):
        refuse_live_private_readonly_network_fetch_v1(endpoint="accounts")
    with pytest.raises(LivePrivateReadonlyPortError, match="ORDER_MUTATION_FORBIDDEN"):
        refuse_live_private_readonly_mutation_v1(action="submit_order")
    with pytest.raises(LivePrivateReadonlyPortError, match="CREDENTIAL_ACCESS_FORBIDDEN"):
        refuse_live_private_readonly_credential_access_v1(claimed_action="load_api_key")
    with pytest.raises(LivePrivateReadonlyPortError, match="NOT_ALLOWLISTED"):
        refuse_live_private_readonly_network_fetch_v1(endpoint="sendorder")


def test_live_shadow_reconciliation_contract_fail_closed() -> None:
    record = build_live_shadow_reconciliation_checkpoint_v1(
        stage="LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
        layer="positions",
        outcome="MATCH",
        divergence_detected=False,
    )
    assert record.source == "FIXTURE_ONLY"
    assert record.shadow_activated is False
    assert record.exchange_fetch_performed is False
    with pytest.raises(LiveShadowReconciliationError, match="EXCHANGE_TRUTH_ADOPTION"):
        build_live_shadow_reconciliation_checkpoint_v1(
            stage="LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
            layer="open_orders",
            outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
            divergence_detected=True,
        )
    with pytest.raises(LiveShadowReconciliationError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_shadow_reconciliation_activation_v1(claimed_action="start_shadow")
    with pytest.raises(LiveShadowReconciliationError, match="EXCHANGE_FETCH_FORBIDDEN"):
        refuse_live_shadow_exchange_fetch_v1(claimed_fetch="positions")
    with pytest.raises(LiveShadowReconciliationError, match="CAPABILITY_11_8_SURFACE_FORBIDDEN"):
        refuse_cap_11_8_live_dry_run_order_plan_v1(claimed_surface="LIVE_DRY_RUN_ORDER_PLAN")
    with pytest.raises(LiveShadowReconciliationError, match="CAPABILITY_11_8_SURFACE_FORBIDDEN"):
        build_live_shadow_reconciliation_checkpoint_v1(
            stage="LIVE_DRY_RUN_ORDER_PLAN",
            layer="positions",
            outcome="MATCH",
            divergence_detected=False,
        )
    proof = prove_live_shadow_reconciliation_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_SHADOW_RECONCILIATION_ACTIVATED"] is False
    assert proof["CAPABILITY_11_8_STARTED"] is False
    assert proof["NO_AUTOMATIC_STAGE_PROMOTION"] is True


def test_live_evidence_ladder_contract_no_proven_overclaim() -> None:
    record = build_live_evidence_ladder_field_record_v1(field_name="LIVE_PRIVATE_READ_ONLY_PROVEN")
    assert record.contract_bound is True
    assert record.proven_claimed is False
    with pytest.raises(LiveEvidenceLadderError, match="UNKNOWN_LIVE_EVIDENCE_LADDER"):
        build_live_evidence_ladder_field_record_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    with pytest.raises(LiveEvidenceLadderError, match="PROVEN_OVERCLAIM_FORBIDDEN"):
        refuse_live_evidence_proven_overclaim_v1(field_name="LIVE_PRIVATE_READ_ONLY_PROVEN")
    with pytest.raises(LiveEvidenceLadderError, match="ACTIVATION_FORBIDDEN"):
        refuse_live_evidence_activation_v1(claimed_action="mark_proven")
    proof = prove_live_evidence_ladder_contract_v1()
    assert proof["ok"] is True
    assert proof["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert proof["LIVE_END_TO_END_EVIDENCE_PROVEN"] is False
    assert proof["LIVE_EVIDENCE_LADDER_CONTRACT_ACTIVATED"] is False


def test_capability_11_1_to_11_6_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    dep_11_4 = prove_capability_11_4_dependency_retained_v1()
    dep_11_5 = prove_capability_11_5_dependency_retained_v1()
    dep_11_6 = prove_capability_11_6_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_4["ok"] is True
    assert dep_11_5["ok"] is True
    assert dep_11_6["ok"] is True
    assert dep_11_6["CAPABILITY_11_6_NOT_ACTIVATED_RETAINED"] is True


def test_negative_reachability_parity_and_ownership() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["PRIVATE_NETWORK_SESSION_STARTED"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    assert reach["CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED"] is True
    assert reach["LIVE_PRIVATE_READONLY_ACTIVATED"] is False
    assert reach["LIVE_SHADOW_RECONCILIATION_ACTIVATED"] is False
    assert reach["CAPABILITY_11_8_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    assert parity["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert ownership["LIVE_PRIVATE_READONLY_PORT_OWNER"].endswith(
        "capability_11_7_live_private_readonly_and_shadow_reconciliation_v1"
    )
    matrix_fields = {row["field"] for row in ownership["matrix"]}
    assert "live_private_readonly_port" in matrix_fields
    assert "live_shadow_reconciliation" in matrix_fields
    assert "live_evidence_ladder" in matrix_fields


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_7_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["PRIVATE_NETWORK_SESSION_STARTED"] is False
    assert claims["LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_7"] is False
    assert claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    assert claims["CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED"] is True
    assert claims["LIVE_PRIVATE_READONLY_ACTIVATED"] is False
    assert claims["LIVE_SHADOW_RECONCILIATION_ACTIVATED"] is False
    assert claims["CAPABILITY_11_8_STARTED"] is False
    assert claims["DASHBOARD_AUTHORITY_EFFECT"] == "NONE"
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_4_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_5_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_6_DEPENDENCY_SATISFIED"] is True
    assert claims["LIVE_PRIVATE_READONLY_CONTRACT_BOUND"] is True
    assert claims["LIVE_SHADOW_RECONCILIATION_CONTRACT_BOUND"] is True
    assert claims["LIVE_EVIDENCE_LADDER_CONTRACT_BOUND"] is True
    assert claims["LIVE_PRIVATE_READONLY_CONTRACT_ACTIVATED"] is False
