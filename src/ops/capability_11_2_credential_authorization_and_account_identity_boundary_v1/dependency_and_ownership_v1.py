"""Cap 11.1 dependency retention + Cap 11.2 ownership matrix."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.verifier_v1 import (
    verify_capability_11_1_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_IDENTITY_BOUNDARY_OWNER,
    AUTHORIZATION_CONTRACT_OWNER,
    CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED,
    CAPABILITY_11_1_FAIL_CLOSED_RETAINED,
    CAPABILITY_11_1_IDEMPOTENCY_RETAINED,
    CAPABILITY_11_1_LIFECYCLE_RETAINED,
    CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED,
    CREDENTIAL_REFERENCE_METADATA_OWNER,
    OWNER,
    PREDECESSOR_CAPABILITY_ID,
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "authorization_id_scope_expiry",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": AUTHORIZATION_CONTRACT_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "credential_reference_metadata",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": CREDENTIAL_REFERENCE_METADATA_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "account_identity",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": ACCOUNT_IDENTITY_BOUNDARY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "plaintext_credentials",
        "classification": "FORBIDDEN_TO_PERSIST",
        "owner": "none",
        "mutable_by_adapter": "false",
    },
    {
        "field": "confirm_tokens_and_secret_material",
        "classification": "FORBIDDEN_TO_PERSIST",
        "owner": "none",
        "mutable_by_adapter": "false",
    },
)


def prove_capability_11_1_dependency_retained_v1() -> dict[str, Any]:
    """Consume Cap 11.1 verifier directly; refuse if predecessor contracts weakened."""
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
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "CAPABILITY_11_1_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_1_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_1_FAIL_CLOSED_RETAINED": CAPABILITY_11_1_FAIL_CLOSED_RETAINED,
        "CAPABILITY_11_1_IDEMPOTENCY_RETAINED": CAPABILITY_11_1_IDEMPOTENCY_RETAINED,
        "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED": CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED,
        "CAPABILITY_11_1_LIFECYCLE_RETAINED": CAPABILITY_11_1_LIFECYCLE_RETAINED,
        "CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED": CAPABILITY_11_1_AUDIT_CONTRACTS_RETAINED,
        "retained_claims": {
            "SUBMISSION_IDEMPOTENT": claims.get("SUBMISSION_IDEMPOTENT"),
            "UNKNOWN_BLIND_RETRY_FORBIDDEN": claims.get("UNKNOWN_BLIND_RETRY_FORBIDDEN"),
            "TERMINAL_STATE_IMMUTABLE": claims.get("TERMINAL_STATE_IMMUTABLE"),
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": claims.get(
                "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"
            ),
            "TESTNET_EXECUTION_REACHABLE": claims.get("TESTNET_EXECUTION_REACHABLE"),
            "LIVE_EXECUTION_REACHABLE": claims.get("LIVE_EXECUTION_REACHABLE"),
        },
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    owners = {row["field"]: row["owner"] for row in STATE_OWNERSHIP_MATRIX_V1}
    ok = all(
        [
            owners.get("credential_reference_metadata") == CREDENTIAL_REFERENCE_METADATA_OWNER,
            owners.get("authorization_id_scope_expiry") == AUTHORIZATION_CONTRACT_OWNER,
            owners.get("account_identity") == ACCOUNT_IDENTITY_BOUNDARY_OWNER,
            owners.get("plaintext_credentials") == "none",
            all(row["mutable_by_adapter"] == "false" for row in STATE_OWNERSHIP_MATRIX_V1),
        ]
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "CREDENTIAL_REFERENCE_METADATA_OWNER": CREDENTIAL_REFERENCE_METADATA_OWNER,
        "AUTHORIZATION_CONTRACT_OWNER": AUTHORIZATION_CONTRACT_OWNER,
        "ACCOUNT_IDENTITY_BOUNDARY_OWNER": ACCOUNT_IDENTITY_BOUNDARY_OWNER,
    }
