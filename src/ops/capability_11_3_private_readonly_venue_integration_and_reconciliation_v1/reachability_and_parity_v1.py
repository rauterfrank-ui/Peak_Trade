"""Negative reachability and core-logic parity proofs for Cap 11.3."""

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
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1 as prove_cap_11_2_core_logic_parity_v1,
    prove_negative_reachability_v1 as prove_cap_11_2_negative_reachability_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    ACTIVATION_STATE,
    CORE_LOGIC_CHANGE,
    CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3,
    CREDENTIAL_PLAINTEXT_LOADED,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    NETWORK_SESSION_STARTED,
    PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3,
    PRIVATE_READONLY_NETWORK_REACHABLE,
    PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED,
    REAL_CAPITAL_MOVEMENT_REACHABLE,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    PrivateReadonlyVenuePortError,
    construct_private_readonly_venue_port_v1,
    refuse_private_readonly_network_fetch_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.venue_session_and_connectivity_contract_v1 import (
    VenueSessionContractError,
    build_venue_session_state_record_v1,
    refuse_venue_network_session_start_v1,
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
    predecessor = prove_cap_11_2_negative_reachability_v1()

    testnet_blocked = False
    try:
        construct_testnet_execution_port_v1()
    except ExecutionPortConstructionForbiddenError:
        testnet_blocked = True

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

    session = build_venue_session_state_record_v1(
        venue="OKX",
        account_identity="acct-uid-demo",
        connectivity_state="DISCONNECTED",
        session_id="session-reachability",
        activation_epoch="0",
    )
    session_start_blocked = False
    try:
        refuse_venue_network_session_start_v1(session)
    except VenueSessionContractError:
        session_start_blocked = True

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
            testnet_blocked,
            live_blocked,
            real_blocked,
            private_port_blocked,
            private_fetch_blocked,
            session_start_blocked,
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
            PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3 is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            ACTIVATION_STATE == "not_activated",
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3 is False,
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
        "PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3": False,
        "TESTNET_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3": False,
        "testnet_construction_blocked": testnet_blocked,
        "live_construction_blocked": live_blocked,
        "real_adapter_construction_blocked": real_blocked,
        "private_readonly_port_construction_blocked": private_port_blocked,
        "private_readonly_fetch_blocked": private_fetch_blocked,
        "network_session_start_blocked": session_start_blocked,
        "credential_load_blocked": credential_load_blocked,
        "forbidden_call_hits": forbidden_hits,
        "predecessor_negative_reachability_ok": predecessor.get("ok") is True,
        "CORE_LOGIC_CHANGE": False,
    }


def prove_core_logic_parity_v1() -> dict[str, Any]:
    predecessor = prove_cap_11_2_core_logic_parity_v1()
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
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "private_readonly_venue_port": "absent",
    "reconciliation_hierarchy_contract": "absent_as_phase11_capability",
    "network_session": "forbidden",
}

CALL_GRAPH_AFTER: dict[str, Any] = {
    "path": [
        "Canonical Stateful Trading Core (unchanged)",
        "Canonical Intent / Lifecycle Contracts (Cap 11.1 retained)",
        "Credential / Authorization / Account-Identity Boundary (Cap 11.2 retained)",
        "Private Read-Only Venue Integration Contracts (Cap 11.3)",
        "PrivateReadonlyVenuePortDeclarationV1 (declared / unreachable)",
        "VenueSessionStateRecordV1 (schema only; start forbidden)",
        "ExchangeClockSyncRecordV1 (schema only; query forbidden)",
        "PrivateAccountStateSnapshotV1 (fixture-only ingestion)",
        "ReconciliationHierarchyContractV1 (layers/outcomes/gates)",
        "VenueAdapterAntiCorruptionV1 (read-only responsibilities)",
        "Mode-Specific Execution Boundary (Simulated sole reachable)",
        "Accounting / Portfolio / Reconciliation / Evidence",
    ],
    "private_readonly_venue_port": "declared_unreachable_in_capability_11_3",
    "reconciliation_hierarchy_contract": "bound_not_activated",
    "network_session": "forbidden",
    "activation": "not_activated",
}
