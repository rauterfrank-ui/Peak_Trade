"""Tests for CAPABILITY_11_3 private read-only venue integration and reconciliation."""

from __future__ import annotations

import pytest

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.exchange_clock_sync_contract_v1 import (
    ExchangeClockSyncContractError,
    build_exchange_clock_sync_record_v1,
    prove_exchange_clock_sync_contract_v1,
    refuse_live_exchange_clock_query_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_account_state_ingestion_contract_v1 import (
    PrivateAccountStateIngestionError,
    build_private_account_state_snapshot_v1,
    prove_private_account_state_ingestion_contract_v1,
    refuse_network_private_account_ingestion_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    PrivateReadonlyVenuePortError,
    construct_private_readonly_venue_port_v1,
    declare_private_readonly_venue_port_v1,
    prove_private_readonly_venue_port_v1,
    refuse_private_readonly_mutation_v1,
    refuse_private_readonly_network_fetch_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.reconciliation_hierarchy_contract_v1 import (
    ReconciliationHierarchyContractError,
    build_reconciliation_checkpoint_v1,
    evaluate_unresolved_divergence_gate_v1,
    prove_reconciliation_hierarchy_contract_v1,
    refuse_silent_local_history_overwrite_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.venue_adapter_anti_corruption_v1 import (
    VenueAdapterAntiCorruptionError,
    prove_venue_adapter_anti_corruption_v1,
    refuse_venue_adapter_decision_authority_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.venue_session_and_connectivity_contract_v1 import (
    VenueSessionContractError,
    build_venue_session_state_record_v1,
    prove_venue_session_and_connectivity_contract_v1,
    refuse_venue_network_session_start_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.verifier_v1 import (
    verify_capability_11_3_v1,
)


def test_private_readonly_port_declared_and_construction_forbidden() -> None:
    port = declare_private_readonly_venue_port_v1()
    assert port.CONSTRUCTIBLE is False
    assert port.REACHABLE is False
    assert port.PRIVATE_READONLY_GET_ONLY is True
    with pytest.raises(PrivateReadonlyVenuePortError, match="CONSTRUCTION_FORBIDDEN"):
        construct_private_readonly_venue_port_v1()
    with pytest.raises(PrivateReadonlyVenuePortError, match="NETWORK_FETCH_FORBIDDEN"):
        refuse_private_readonly_network_fetch_v1(endpoint="accounts")
    with pytest.raises(PrivateReadonlyVenuePortError, match="NOT_ALLOWLISTED"):
        refuse_private_readonly_network_fetch_v1(endpoint="sendorder")
    with pytest.raises(PrivateReadonlyVenuePortError, match="ORDER_MUTATION_FORBIDDEN"):
        refuse_private_readonly_mutation_v1(action="submit_order")
    assert prove_private_readonly_venue_port_v1()["ok"] is True


def test_venue_session_schema_and_start_forbidden() -> None:
    record = build_venue_session_state_record_v1(
        venue="OKX",
        account_identity="acct-uid-demo",
        connectivity_state="DISCONNECTED",
        session_id="session-test",
        activation_epoch="0",
    )
    assert record.network_session_started is False
    with pytest.raises(VenueSessionContractError, match="NETWORK_SESSION_START_FORBIDDEN"):
        refuse_venue_network_session_start_v1(record)
    with pytest.raises(VenueSessionContractError, match="UNKNOWN_CONNECTIVITY_STATE"):
        build_venue_session_state_record_v1(
            venue="OKX",
            account_identity="acct-uid-demo",
            connectivity_state="FLYING",
            session_id="session-bad",
            activation_epoch="0",
        )
    assert prove_venue_session_and_connectivity_contract_v1()["ok"] is True


def test_exchange_clock_sync_schema_and_query_forbidden() -> None:
    record = build_exchange_clock_sync_record_v1(
        venue="OKX",
        local_clock_utc="1970-01-01T00:00:00Z",
        exchange_clock_utc="1970-01-01T00:00:00Z",
        offset_ms=0,
        sync_status="UNSYNCED",
    )
    with pytest.raises(ExchangeClockSyncContractError, match="CLOCK_QUERY_FORBIDDEN"):
        refuse_live_exchange_clock_query_v1(record)
    with pytest.raises(ExchangeClockSyncContractError, match="UNKNOWN_SYNC_STATUS"):
        build_exchange_clock_sync_record_v1(
            venue="OKX",
            local_clock_utc="1970-01-01T00:00:00Z",
            exchange_clock_utc="1970-01-01T00:00:00Z",
            offset_ms=0,
            sync_status="TELEPATHIC",
        )
    assert prove_exchange_clock_sync_contract_v1()["ok"] is True


def test_private_account_state_fixture_only_and_network_forbidden() -> None:
    snap = build_private_account_state_snapshot_v1(
        snapshot_kind="open_positions",
        venue="OKX",
        account_identity="acct-uid-demo",
        observed_at_utc="1970-01-01T00:00:00Z",
        payload={"positions": []},
    )
    assert snap.source == "FIXTURE_ONLY"
    with pytest.raises(PrivateAccountStateIngestionError, match="NON_FIXTURE"):
        build_private_account_state_snapshot_v1(
            snapshot_kind="accounts",
            venue="OKX",
            account_identity="acct-uid-demo",
            observed_at_utc="1970-01-01T00:00:00Z",
            payload={},
            source="LIVE_NETWORK",
        )
    with pytest.raises(PrivateAccountStateIngestionError, match="NETWORK_INGESTION_FORBIDDEN"):
        refuse_network_private_account_ingestion_v1(snapshot_kind="open_orders")
    assert prove_private_account_state_ingestion_contract_v1()["ok"] is True


def test_reconciliation_hierarchy_positive_and_negative() -> None:
    match_cp = build_reconciliation_checkpoint_v1(
        layer="positions",
        outcome="MATCH",
        divergence_detected=False,
    )
    assert evaluate_unresolved_divergence_gate_v1(match_cp)["new_entry_allowed"] is True
    halt_cp = build_reconciliation_checkpoint_v1(
        layer="balances_equity_and_available_margin",
        outcome="HARD_STOP_OWNER_REVIEW",
        divergence_detected=True,
    )
    assert evaluate_unresolved_divergence_gate_v1(halt_cp)["new_entry_allowed"] is False
    with pytest.raises(
        ReconciliationHierarchyContractError,
        match="EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY",
    ):
        build_reconciliation_checkpoint_v1(
            layer="open_orders",
            outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
            divergence_detected=True,
        )
    with pytest.raises(
        ReconciliationHierarchyContractError,
        match="SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN",
    ):
        refuse_silent_local_history_overwrite_v1(attempted_overwrite_of="decision_history")
    assert prove_reconciliation_hierarchy_contract_v1()["ok"] is True


def test_venue_adapter_anti_corruption() -> None:
    with pytest.raises(VenueAdapterAntiCorruptionError, match="AUTHORITY_FORBIDDEN"):
        refuse_venue_adapter_decision_authority_v1(claimed_authority="decision")
    with pytest.raises(VenueAdapterAntiCorruptionError, match="AUTHORITY_FORBIDDEN"):
        refuse_venue_adapter_decision_authority_v1(claimed_authority="order_mutation")
    proof = prove_venue_adapter_anti_corruption_v1()
    assert proof["ok"] is True
    assert proof["VENUE_ADAPTER_DECISION_AUTHORITY"] is False


def test_capability_11_1_and_11_2_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_1["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert dep_11_1["CAPABILITY_11_1_IDEMPOTENCY_RETAINED"] is True
    assert dep_11_1["CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED"] is True
    assert dep_11_1["CAPABILITY_11_1_LIFECYCLE_RETAINED"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_2["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert dep_11_2["CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED"] is True
    assert dep_11_2["CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED"] is True
    assert dep_11_2["CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED"] is True


def test_negative_reachability_parity_and_ownership() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["PRIVATE_READONLY_NETWORK_REACHABLE"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert "private_readonly_venue_integration" in ownership["PRIVATE_READONLY_PORT_OWNER"]


def test_failure_injection_contract_violations_only() -> None:
    with pytest.raises(ReconciliationHierarchyContractError, match="UNKNOWN_RECONCILIATION_LAYER"):
        build_reconciliation_checkpoint_v1(
            layer="vibes",
            outcome="MATCH",
            divergence_detected=False,
        )
    with pytest.raises(PrivateAccountStateIngestionError, match="UNKNOWN_SNAPSHOT_KIND"):
        build_private_account_state_snapshot_v1(
            snapshot_kind="withdrawals",
            venue="OKX",
            account_identity="acct",
            observed_at_utc="1970-01-01T00:00:00Z",
            payload={},
        )


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_3_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED"] is False
    assert claims["PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3"] is False
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["RECONCILIATION_BEFORE_ALPHA"] is True
    assert claims["VENUE_ADAPTER_DECISION_AUTHORITY"] is False
