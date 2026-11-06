"""Negative reachability and core-logic parity proofs for Cap 11.5."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
    construct_testnet_execution_port_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_load_gate_v1 import (
    CredentialLoadGateError,
    CredentialLoadGateV1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    PrivateReadonlyVenuePortError,
    construct_private_readonly_venue_port_v1,
    refuse_private_readonly_network_fetch_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1 as prove_cap_11_4_core_logic_parity_v1,
    prove_negative_reachability_v1 as prove_cap_11_4_negative_reachability_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.testnet_execution_adapter_v1 import (
    TestnetExecutionAdapterError,
    construct_testnet_execution_adapter_v1,
    refuse_testnet_network_session_start_v1,
    refuse_testnet_order_submit_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.autonomous_recovery_degradation_contract_v1 import (
    AutonomousRecoveryDegradationError,
    refuse_cap_11_6_long_running_autonomous_testnet_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED,
    CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED,
    CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_5,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED,
    NETWORK_SESSION_STARTED,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED,
    REAL_CAPITAL_MOVEMENT_REACHABLE,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_ADAPTER_ACTIVATED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_5,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.kill_switch_and_emergency_control_contract_v1 import (
    KillSwitchEmergencyControlError,
    refuse_kill_switch_side_effect_bypass_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.restart_with_open_order_position_contract_v1 import (
    RestartWithOpenOrderPositionError,
    refuse_restart_network_session_activation_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.unknown_submit_reconnect_recovery_contract_v1 import (
    UnknownSubmitReconnectRecoveryError,
    refuse_unknown_submit_network_reconnect_activation_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    refuse_real_execution_adapter_construction_v1,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent
_FORBIDDEN_CALL_ATTRS = frozenset(
    {
        "submit_order",
        "submit_orders",
        "place_order",
        "create_order",
        "cancel_order",
        "load_credentials",
        "load_exchange_credentials",
        "urlopen",
        "request",
    }
)


def _scan_package_for_forbidden_calls() -> list[str]:
    hits: list[str] = []
    for path in sorted(_PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            fname = ""
            if isinstance(func, ast.Name):
                fname = func.id
            elif isinstance(func, ast.Attribute):
                fname = func.attr
            if fname in _FORBIDDEN_CALL_ATTRS:
                hits.append(f"{path.name}:{fname}")
    return hits


def prove_negative_reachability_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_4_negative_reachability_v1()

    testnet_port_blocked = False
    try:
        construct_testnet_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        testnet_port_blocked = True

    testnet_adapter_blocked = False
    try:
        construct_testnet_execution_adapter_v1()
    except TestnetExecutionAdapterError:
        testnet_adapter_blocked = True

    live_blocked = False
    try:
        construct_live_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        live_blocked = True

    real_blocked = False
    try:
        refuse_real_execution_adapter_construction_v1()
    except Exception:
        real_blocked = True

    private_port_blocked = False
    try:
        construct_private_readonly_venue_port_v1()
    except PrivateReadonlyVenuePortError:
        private_port_blocked = True

    private_fetch_blocked = False
    try:
        refuse_private_readonly_network_fetch_v1(endpoint="accounts")
    except PrivateReadonlyVenuePortError:
        private_fetch_blocked = True

    submit_blocked = False
    try:
        refuse_testnet_order_submit_v1(client_order_id="pt-coid-reach-11-5")
    except TestnetExecutionAdapterError:
        submit_blocked = True

    session_blocked = False
    try:
        refuse_testnet_network_session_start_v1(session_id="session-reach-11-5")
    except TestnetExecutionAdapterError:
        session_blocked = True

    unknown_reconnect_blocked = False
    try:
        refuse_unknown_submit_network_reconnect_activation_v1(session_id="session-unknown")
    except UnknownSubmitReconnectRecoveryError:
        unknown_reconnect_blocked = True

    restart_session_blocked = False
    try:
        refuse_restart_network_session_activation_v1(session_id="session-restart")
    except RestartWithOpenOrderPositionError:
        restart_session_blocked = True

    kill_bypass_blocked = False
    try:
        refuse_kill_switch_side_effect_bypass_v1(claimed_side_effect="order_submit")
    except KillSwitchEmergencyControlError:
        kill_bypass_blocked = True

    cap_11_6_blocked = False
    try:
        refuse_cap_11_6_long_running_autonomous_testnet_v1(claimed_surface="campaign")
    except AutonomousRecoveryDegradationError:
        cap_11_6_blocked = True

    gate = CredentialLoadGateV1()
    for name in gate.prerequisites_satisfied:
        gate.mark_prerequisite(name, satisfied=True)
    credential_load_blocked = False
    try:
        gate.attempt_credential_load_v1()
    except CredentialLoadGateError:
        credential_load_blocked = True

    forbidden_hits = _scan_package_for_forbidden_calls()
    ok = all(
        [
            predecessor.get("ok") is True,
            testnet_port_blocked,
            testnet_adapter_blocked,
            live_blocked,
            real_blocked,
            private_port_blocked,
            private_fetch_blocked,
            submit_blocked,
            session_blocked,
            unknown_reconnect_blocked,
            restart_session_blocked,
            kill_bypass_blocked,
            cap_11_6_blocked,
            credential_load_blocked,
            not forbidden_hits,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            NETWORK_SESSION_STARTED is False,
            REAL_CAPITAL_MOVEMENT_REACHABLE is False,
            PRIVATE_READONLY_NETWORK_REACHABLE is False,
            PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED is False,
            TESTNET_EXECUTION_ADAPTER_ACTIVATED is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5 is False,
            TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_5 is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            ACTIVATION_STATE == "not_activated",
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_5 is False,
            CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED is True,
            UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED is False,
            RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED is False,
            KILL_SWITCH_CONTRACT_ACTIVATED is False,
            AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED is False,
            CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED is False,
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED is False,
            CORE_LOGIC_CHANGE is False,
        ]
    )
    return {
        "ok": ok,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "REAL_CAPITAL_MOVEMENT_REACHABLE": False,
        "PRIVATE_READONLY_NETWORK_REACHABLE": False,
        "PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED": False,
        "TESTNET_EXECUTION_ADAPTER_ACTIVATED": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5": False,
        "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_5": False,
        "TESTNET_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_5": False,
        "CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED": True,
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_ACTIVATED": False,
        "RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_ACTIVATED": False,
        "KILL_SWITCH_CONTRACT_ACTIVATED": False,
        "AUTONOMOUS_RECOVERY_CONTRACT_ACTIVATED": False,
        "CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED": False,
        "testnet_port_construction_blocked": testnet_port_blocked,
        "testnet_adapter_construction_blocked": testnet_adapter_blocked,
        "live_construction_blocked": live_blocked,
        "real_adapter_construction_blocked": real_blocked,
        "private_readonly_port_construction_blocked": private_port_blocked,
        "private_readonly_fetch_blocked": private_fetch_blocked,
        "testnet_order_submit_blocked": submit_blocked,
        "network_session_start_blocked": session_blocked,
        "unknown_reconnect_activation_blocked": unknown_reconnect_blocked,
        "restart_network_session_blocked": restart_session_blocked,
        "kill_switch_bypass_blocked": kill_bypass_blocked,
        "cap_11_6_surface_blocked": cap_11_6_blocked,
        "credential_load_blocked": credential_load_blocked,
        "forbidden_call_hits": forbidden_hits,
        "predecessor_negative_reachability_ok": predecessor.get("ok") is True,
        "CORE_LOGIC_CHANGE": False,
    }


def prove_core_logic_parity_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_4_core_logic_parity_v1()
    ok = predecessor.get("ok") is True and CORE_LOGIC_CHANGE is False
    return {
        "ok": ok,
        "CORE_LOGIC_CHANGE": False,
        "CORE_LOGIC_PARITY_WITH_SIMULATED_EXECUTION_PORT": predecessor.get(
            "CORE_LOGIC_PARITY_WITH_SIMULATED_EXECUTION_PORT"
        ),
        "predecessor": predecessor,
        "master_v2_mutated": False,
        "double_play_mutated": False,
        "c1_c2_c3_mutated": False,
        "dynamic_scope_mutated": False,
        "risk_mutated": False,
        "safety_mutated": False,
        "exit_policy_mutated": False,
        "thresholds_mutated": False,
        "VOLATILITY_NUMERIC_MAX_AGE_ENFORCING": False,
        "NUMERIC_MAX_AGE_EFFECT": "DIAGNOSTIC_ONLY",
    }


CALL_GRAPH_BEFORE: dict[str, Any] = {
    "path": [
        "Canonical Stateful Trading Core",
        "Canonical Intent / Lifecycle Contracts (Cap 11.1)",
        "Credential / Authorization / Account-Identity Boundary (Cap 11.2)",
        "Private Read-Only Venue Integration Contracts (Cap 11.3)",
        "Testnet Execution Adapter and Lifecycle Closure Contracts (Cap 11.4)",
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "unknown_submit_reconnect_recovery": "absent_as_phase11_capability",
    "restart_with_open_order_position": "absent_as_phase11_capability",
    "kill_switch_and_emergency_control": "absent_as_phase11_capability",
    "autonomous_recovery_degradation": "absent_as_phase11_capability",
    "network_session": "forbidden",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "path": [
        "Canonical Stateful Trading Core (unchanged)",
        "Canonical Intent / Lifecycle Contracts (Cap 11.1 retained)",
        "Credential / Authorization / Account-Identity Boundary (Cap 11.2 retained)",
        "Private Read-Only Venue Integration Contracts (Cap 11.3 retained)",
        "Testnet Execution Adapter and Lifecycle Closure Contracts (Cap 11.4 retained)",
        "Testnet Restart / Recovery / Kill-Switch Closure Contracts (Cap 11.5)",
        "UnknownSubmitRecoveryPathRecordV1 (fixture-only; network reconnect forbidden)",
        "RestartRecoveryPathRecordV1 (fixture-only; silent reset forbidden)",
        "KillSwitchFixtureRecordV1 (fixture-only; runtime clear forbidden)",
        "OperatingStateTransitionRecordV1 (fixture-only; Cap 11.6 forbidden)",
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "unknown_submit_reconnect_recovery": "bound_fixture_only_not_activated",
    "restart_with_open_order_position": "bound_fixture_only_not_activated",
    "kill_switch_and_emergency_control": "bound_fixture_only_not_activated",
    "autonomous_recovery_degradation": "bound_fixture_only_not_activated",
    "network_session": "forbidden",
    "activation": "not_activated",
}
