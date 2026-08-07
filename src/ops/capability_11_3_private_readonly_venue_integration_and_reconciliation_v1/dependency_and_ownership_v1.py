"""Cap 11.1/11.2 dependency retention + Cap 11.3 ownership matrix."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.verifier_v1 import (
    verify_capability_11_1_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.verifier_v1 import (
    verify_capability_11_2_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CAPABILITY_11_1_ANTI_CORRUPTION_RETAINED,
    CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED,
    CAPABILITY_11_1_FAIL_CLOSED_RETAINED,
    CAPABILITY_11_1_IDEMPOTENCY_RETAINED,
    CAPABILITY_11_1_JOURNALING_RETAINED,
    CAPABILITY_11_1_LIFECYCLE_RETAINED,
    CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED,
    CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED,
    CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED,
    CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED,
    CAPABILITY_11_2_NO_AUTH_CONSUMPTION_RETAINED,
    CAPABILITY_11_2_NO_CREDENTIAL_LOAD_RETAINED,
    EXCHANGE_CLOCK_SYNC_OWNER,
    OWNER,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
    PRIVATE_READONLY_PORT_OWNER,
    RECONCILIATION_HIERARCHY_OWNER,
    VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
    VENUE_SESSION_CONTRACT_OWNER,
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "venue_session_and_connectivity_state",
        "classification": "EPHEMERAL_CONNECTION_STATE",
        "owner": VENUE_SESSION_CONTRACT_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "exchange_clock_offset_and_synchronization_state",
        "classification": "EPHEMERAL_CONNECTION_STATE",
        "owner": EXCHANGE_CLOCK_SYNC_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "private_account_state_snapshots",
        "classification": "DURABLE_ECONOMIC_STATE",
        "owner": PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "reconciliation_checkpoints",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": RECONCILIATION_HIERARCHY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "private_readonly_venue_port",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": PRIVATE_READONLY_PORT_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "venue_adapter_anti_corruption_boundary",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "plaintext_credentials",
        "classification": "FORBIDDEN_TO_PERSIST",
        "owner": "none",
        "mutable_by_adapter": "false",
    },
)


def prove_capability_11_1_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_1_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("TESTNET_EXECUTION_REACHABLE") is False,
            claims.get("LIVE_EXECUTION_REACHABLE") is False,
            claims.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED") is False,
            claims.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
            claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
            claims.get("NETWORK_SESSION_STARTED") is False,
            claims.get("SUBMISSION_IDEMPOTENT") is True,
            claims.get("UNKNOWN_BLIND_RETRY_FORBIDDEN") is True,
            claims.get("TERMINAL_STATE_IMMUTABLE") is True,
            claims.get("ORDER_LIFECYCLE_STATE_MACHINE_BOUND") is True,
            CAPABILITY_11_1_FAIL_CLOSED_RETAINED is True,
            CAPABILITY_11_1_IDEMPOTENCY_RETAINED is True,
            CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED is True,
            CAPABILITY_11_1_LIFECYCLE_RETAINED is True,
            CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED is True,
            CAPABILITY_11_1_ANTI_CORRUPTION_RETAINED is True,
            CAPABILITY_11_1_JOURNALING_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_1,
        "CAPABILITY_11_1_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_1_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_1_FAIL_CLOSED_RETAINED": CAPABILITY_11_1_FAIL_CLOSED_RETAINED,
        "CAPABILITY_11_1_IDEMPOTENCY_RETAINED": CAPABILITY_11_1_IDEMPOTENCY_RETAINED,
        "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED": CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED,
        "CAPABILITY_11_1_LIFECYCLE_RETAINED": CAPABILITY_11_1_LIFECYCLE_RETAINED,
        "CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED": CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED,
        "CAPABILITY_11_1_ANTI_CORRUPTION_RETAINED": CAPABILITY_11_1_ANTI_CORRUPTION_RETAINED,
        "CAPABILITY_11_1_JOURNALING_RETAINED": CAPABILITY_11_1_JOURNALING_RETAINED,
    }


def prove_capability_11_2_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_2_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
            claims.get("AUTHORIZATION_CONSUMPTION_ALLOWED") is False,
            claims.get("CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2") is False,
            claims.get("PLAINTEXT_SECRET_NEVER_PERSISTED") is True,
            claims.get("ACCOUNT_SCOPE_EXPLICIT") is True,
            claims.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
            CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED is True,
            CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED is True,
            CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED is True,
            CAPABILITY_11_2_NO_CREDENTIAL_LOAD_RETAINED is True,
            CAPABILITY_11_2_NO_AUTH_CONSUMPTION_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_2,
        "CAPABILITY_11_2_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_2_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED": CAPABILITY_11_2_CREDENTIAL_BOUNDARY_RETAINED,
        "CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED": (
            CAPABILITY_11_2_AUTHORIZATION_BOUNDARY_RETAINED
        ),
        "CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED": (
            CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY_RETAINED
        ),
        "CAPABILITY_11_2_NO_CREDENTIAL_LOAD_RETAINED": CAPABILITY_11_2_NO_CREDENTIAL_LOAD_RETAINED,
        "CAPABILITY_11_2_NO_AUTH_CONSUMPTION_RETAINED": CAPABILITY_11_2_NO_AUTH_CONSUMPTION_RETAINED,
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    owners = {row["field"]: row["owner"] for row in STATE_OWNERSHIP_MATRIX_V1}
    ok = all(
        [
            owners.get("venue_session_and_connectivity_state") == VENUE_SESSION_CONTRACT_OWNER,
            owners.get("exchange_clock_offset_and_synchronization_state")
            == EXCHANGE_CLOCK_SYNC_OWNER,
            owners.get("private_account_state_snapshots") == PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
            owners.get("reconciliation_checkpoints") == RECONCILIATION_HIERARCHY_OWNER,
            owners.get("private_readonly_venue_port") == PRIVATE_READONLY_PORT_OWNER,
            owners.get("venue_adapter_anti_corruption_boundary")
            == VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
            owners.get("plaintext_credentials") == "none",
            all(row["mutable_by_adapter"] == "false" for row in STATE_OWNERSHIP_MATRIX_V1),
        ]
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "PRIVATE_READONLY_PORT_OWNER": PRIVATE_READONLY_PORT_OWNER,
        "VENUE_SESSION_CONTRACT_OWNER": VENUE_SESSION_CONTRACT_OWNER,
        "EXCHANGE_CLOCK_SYNC_OWNER": EXCHANGE_CLOCK_SYNC_OWNER,
        "PRIVATE_ACCOUNT_STATE_INGESTION_OWNER": PRIVATE_ACCOUNT_STATE_INGESTION_OWNER,
        "RECONCILIATION_HIERARCHY_OWNER": RECONCILIATION_HIERARCHY_OWNER,
        "VENUE_ADAPTER_ANTI_CORRUPTION_OWNER": VENUE_ADAPTER_ANTI_CORRUPTION_OWNER,
    }
