"""Tests for CAPABILITY_11_4 testnet execution adapter and lifecycle closure."""

from __future__ import annotations

import pytest

from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_capability_11_2_dependency_retained_v1,
    prove_capability_11_3_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.order_serialization_dry_run_contract_v1 import (
    OrderSerializationDryRunError,
    build_order_serialization_dry_run_record_v1,
    prove_order_serialization_dry_run_contract_v1,
    refuse_order_serialization_network_submit_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_execution_adapter_v1 import (
    TestnetExecutionAdapterError,
    construct_testnet_execution_adapter_v1,
    declare_testnet_execution_adapter_v1,
    prove_testnet_execution_adapter_v1,
    refuse_testnet_network_session_start_v1,
    refuse_testnet_order_submit_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_lifecycle_closure_contract_v1 import (
    TestnetLifecycleClosureError,
    prove_testnet_lifecycle_closure_contract_v1,
    refuse_cap_11_5_restart_recovery_kill_switch_v1,
    run_testnet_lifecycle_fixture_path_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.venue_adapter_anti_corruption_v1 import (
    VenueAdapterAntiCorruptionError,
    prove_venue_adapter_anti_corruption_v1,
    refuse_venue_adapter_decision_authority_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.verifier_v1 import (
    verify_capability_11_4_v1,
)


def test_testnet_execution_adapter_declared_and_construction_forbidden() -> None:
    adapter = declare_testnet_execution_adapter_v1()
    assert adapter.CONSTRUCTIBLE is False
    assert adapter.REACHABLE is False
    assert adapter.EXECUTION_MODE == "TESTNET"
    with pytest.raises(TestnetExecutionAdapterError, match="CONSTRUCTION_FORBIDDEN"):
        construct_testnet_execution_adapter_v1()
    with pytest.raises(TestnetExecutionAdapterError, match="ORDER_SUBMIT_FORBIDDEN"):
        refuse_testnet_order_submit_v1(client_order_id="pt-coid-demo")
    with pytest.raises(TestnetExecutionAdapterError, match="NETWORK_SESSION_START_FORBIDDEN"):
        refuse_testnet_network_session_start_v1(session_id="session-demo")
    assert prove_testnet_execution_adapter_v1()["ok"] is True


def test_order_serialization_dry_run_fixture_only() -> None:
    record = build_order_serialization_dry_run_record_v1(
        client_order_id="pt-coid-dryrun-demo",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
    )
    assert record.source == "FIXTURE_ONLY"
    assert record.submitted is False
    assert record.network_effect == "NONE"
    assert record.venue_native_payload["dry_run"] is True
    with pytest.raises(OrderSerializationDryRunError, match="NON_FIXTURE"):
        build_order_serialization_dry_run_record_v1(
            client_order_id="pt-coid-bad",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            source="LIVE_NETWORK",
        )
    with pytest.raises(OrderSerializationDryRunError, match="NOT_TESTNET"):
        build_order_serialization_dry_run_record_v1(
            client_order_id="pt-coid-live",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
            execution_mode="LIVE",
        )
    with pytest.raises(OrderSerializationDryRunError, match="NETWORK_SUBMIT_FORBIDDEN"):
        refuse_order_serialization_network_submit_v1(record=record)
    assert prove_order_serialization_dry_run_contract_v1()["ok"] is True


def test_testnet_lifecycle_fixture_paths_close() -> None:
    for path_name in (
        "single_controlled_order_lifecycle",
        "entry_lifecycle",
        "partial_fill_lifecycle",
        "cancel_lifecycle",
        "exit_lifecycle",
    ):
        record = run_testnet_lifecycle_fixture_path_v1(path_name=path_name)
        assert record.terminal_state == "EVIDENCED"
        assert record.exchange_submit_performed is False
        assert record.source == "FIXTURE_ONLY"
    with pytest.raises(TestnetLifecycleClosureError, match="UNKNOWN_TESTNET_LIFECYCLE_PATH"):
        run_testnet_lifecycle_fixture_path_v1(path_name="restart_with_open_order")
    with pytest.raises(TestnetLifecycleClosureError, match="CAPABILITY_11_5_SURFACE_FORBIDDEN"):
        refuse_cap_11_5_restart_recovery_kill_switch_v1(claimed_surface="kill_switch")
    proof = prove_testnet_lifecycle_closure_contract_v1()
    assert proof["ok"] is True
    assert proof["TESTNET_ORDER_LIFECYCLE_PROVEN"] is False
    assert proof["CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED"] is False


def test_venue_adapter_anti_corruption() -> None:
    with pytest.raises(VenueAdapterAntiCorruptionError, match="AUTHORITY_FORBIDDEN"):
        refuse_venue_adapter_decision_authority_v1(claimed_authority="decision")
    with pytest.raises(VenueAdapterAntiCorruptionError, match="AUTHORITY_FORBIDDEN"):
        refuse_venue_adapter_decision_authority_v1(claimed_authority="kill_switch_authority")
    proof = prove_venue_adapter_anti_corruption_v1()
    assert proof["ok"] is True
    assert proof["VENUE_ADAPTER_DECISION_AUTHORITY"] is False
    assert proof["NATIVE_ORDER_SERIALIZATION_EXPLICIT"] is True


def test_capability_11_1_11_2_11_3_dependencies_retained() -> None:
    dep_11_1 = prove_capability_11_1_dependency_retained_v1()
    dep_11_2 = prove_capability_11_2_dependency_retained_v1()
    dep_11_3 = prove_capability_11_3_dependency_retained_v1()
    assert dep_11_1["ok"] is True
    assert dep_11_1["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert dep_11_2["ok"] is True
    assert dep_11_2["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert dep_11_3["ok"] is True
    assert dep_11_3["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert dep_11_3["CAPABILITY_11_3_NOT_ACTIVATED_RETAINED"] is True


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
    assert reach["CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert "testnet_execution_adapter" in ownership["TESTNET_EXECUTION_ADAPTER_OWNER"]


def test_failure_injection_contract_violations_only() -> None:
    with pytest.raises(OrderSerializationDryRunError, match="ORDER_SERIALIZATION_FIELD_MISSING"):
        build_order_serialization_dry_run_record_v1(
            client_order_id="",
            instrument_id="BTC-USDT-SWAP",
            side="BUY",
            order_type="LIMIT",
            quantity="1",
        )
    with pytest.raises(TestnetLifecycleClosureError, match="UNKNOWN_TESTNET_LIFECYCLE_PATH"):
        run_testnet_lifecycle_fixture_path_v1(path_name="long_running_autonomous_campaign")


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_4_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["NETWORK_SESSION_STARTED"] is False
    assert claims["TESTNET_EXECUTION_ADAPTER_ACTIVATED"] is False
    assert claims["TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4"] is False
    assert claims["TESTNET_ORDER_LIFECYCLE_PROVEN"] is False
    assert claims["CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED"] is False
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_2_DEPENDENCY_SATISFIED"] is True
    assert claims["CAPABILITY_11_3_DEPENDENCY_SATISFIED"] is True
    assert claims["ORDER_SERIALIZATION_DRY_RUN_CONTRACT_BOUND"] is True
    assert claims["TESTNET_LIFECYCLE_CLOSURE_CONTRACT_BOUND"] is True
    assert claims["VENUE_ADAPTER_DECISION_AUTHORITY"] is False
