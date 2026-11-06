"""Cap 11.1–11.4 dependency retention + Cap 11.5 ownership matrix."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.verifier_v1 import (
    verify_capability_11_1_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.verifier_v1 import (
    verify_capability_11_2_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.verifier_v1 import (
    verify_capability_11_3_v1,
)
from src.ops.capability_11_4_testnet_execution_adapter_and_lifecycle_closure_v1.verifier_v1 import (
    verify_capability_11_4_v1,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (
    AUTONOMOUS_RECOVERY_DEGRADATION_OWNER,
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
    CAPABILITY_11_3_NO_CREDENTIAL_LOAD_RETAINED,
    CAPABILITY_11_3_NO_NETWORK_FETCH_RETAINED,
    CAPABILITY_11_3_NOT_ACTIVATED_RETAINED,
    CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED,
    CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED,
    CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED,
    CAPABILITY_11_4_NO_NETWORK_SESSION_RETAINED,
    CAPABILITY_11_4_NO_ORDER_SUBMIT_RETAINED,
    CAPABILITY_11_4_NOT_ACTIVATED_RETAINED,
    CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED,
    KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER,
    OWNER,
    PREDECESSOR_CAPABILITY_ID_11_1,
    PREDECESSOR_CAPABILITY_ID_11_2,
    PREDECESSOR_CAPABILITY_ID_11_3,
    PREDECESSOR_CAPABILITY_ID_11_4,
    RESTART_WITH_OPEN_ORDER_POSITION_OWNER,
    UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER,
)


STATE_OWNERSHIP_MATRIX_V1: tuple[dict[str, str], ...] = (
    {
        "field": "unknown_submit_reconnect_recovery",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "restart_with_open_order_position",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": RESTART_WITH_OPEN_ORDER_POSITION_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "kill_switch_and_emergency_control",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER,
        "mutable_by_adapter": "false",
    },
    {
        "field": "autonomous_recovery_degradation",
        "classification": "DURABLE_CONTROL_STATE",
        "owner": AUTONOMOUS_RECOVERY_DEGRADATION_OWNER,
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


def prove_capability_11_3_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_3_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("PRIVATE_READONLY_VENUE_INTEGRATION_ACTIVATED") is False,
            claims.get("PRIVATE_READONLY_FETCH_PERFORMED_IN_CAPABILITY_11_3") is False,
            claims.get("PRIVATE_READONLY_NETWORK_REACHABLE") is False,
            claims.get("CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_3") is False,
            claims.get("AUTHORIZATION_CONSUMPTION_ALLOWED") is False,
            claims.get("RECONCILIATION_BEFORE_ALPHA") is True,
            claims.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_2_DEPENDENCY_SATISFIED") is True,
            CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED is True,
            CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED is True,
            CAPABILITY_11_3_NOT_ACTIVATED_RETAINED is True,
            CAPABILITY_11_3_NO_NETWORK_FETCH_RETAINED is True,
            CAPABILITY_11_3_NO_CREDENTIAL_LOAD_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_3,
        "CAPABILITY_11_3_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_3_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED": (
            CAPABILITY_11_3_PRIVATE_READONLY_BOUNDARY_RETAINED
        ),
        "CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED": (
            CAPABILITY_11_3_RECONCILIATION_HIERARCHY_RETAINED
        ),
        "CAPABILITY_11_3_NOT_ACTIVATED_RETAINED": CAPABILITY_11_3_NOT_ACTIVATED_RETAINED,
        "CAPABILITY_11_3_NO_NETWORK_FETCH_RETAINED": CAPABILITY_11_3_NO_NETWORK_FETCH_RETAINED,
        "CAPABILITY_11_3_NO_CREDENTIAL_LOAD_RETAINED": CAPABILITY_11_3_NO_CREDENTIAL_LOAD_RETAINED,
    }


def prove_capability_11_4_dependency_retained_v1() -> dict[str, Any]:
    result = verify_capability_11_4_v1()
    claims = result.get("claims") or {}
    ok = all(
        [
            result.get("ok") is True,
            result.get("VERIFIER_RESULT") == "PASS",
            claims.get("CORE_LOGIC_CHANGE") is False,
            claims.get("ACTIVATION_STATE") == "not_activated",
            claims.get("TESTNET_AUTHORIZED") is False,
            claims.get("LIVE_AUTHORIZED") is False,
            claims.get("TESTNET_EXECUTION_ADAPTER_ACTIVATED") is False,
            claims.get("TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_4") is False,
            claims.get("TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_4") is False,
            claims.get("TESTNET_EXECUTION_REACHABLE") is False,
            claims.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
            claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
            claims.get("NETWORK_SESSION_STARTED") is False,
            claims.get("CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED") is False,
            claims.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_2_DEPENDENCY_SATISFIED") is True,
            claims.get("CAPABILITY_11_3_DEPENDENCY_SATISFIED") is True,
            CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED is True,
            CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED is True,
            CAPABILITY_11_4_NOT_ACTIVATED_RETAINED is True,
            CAPABILITY_11_4_NO_ORDER_SUBMIT_RETAINED is True,
            CAPABILITY_11_4_NO_NETWORK_SESSION_RETAINED is True,
        ]
    )
    return {
        "ok": ok,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID_11_4,
        "CAPABILITY_11_4_DEPENDENCY_SATISFIED": ok,
        "CAPABILITY_11_4_VERIFIER_RESULT": result.get("VERIFIER_RESULT"),
        "CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED": (
            CAPABILITY_11_4_TESTNET_ADAPTER_BOUNDARY_RETAINED
        ),
        "CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED": CAPABILITY_11_4_LIFECYCLE_CLOSURE_RETAINED,
        "CAPABILITY_11_4_NOT_ACTIVATED_RETAINED": CAPABILITY_11_4_NOT_ACTIVATED_RETAINED,
        "CAPABILITY_11_4_NO_ORDER_SUBMIT_RETAINED": CAPABILITY_11_4_NO_ORDER_SUBMIT_RETAINED,
        "CAPABILITY_11_4_NO_NETWORK_SESSION_RETAINED": CAPABILITY_11_4_NO_NETWORK_SESSION_RETAINED,
    }


def prove_state_ownership_matrix_v1() -> dict[str, Any]:
    owners = {row["field"]: row["owner"] for row in STATE_OWNERSHIP_MATRIX_V1}
    ok = all(
        [
            owners.get("unknown_submit_reconnect_recovery")
            == UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER,
            owners.get("restart_with_open_order_position")
            == RESTART_WITH_OPEN_ORDER_POSITION_OWNER,
            owners.get("kill_switch_and_emergency_control")
            == KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER,
            owners.get("autonomous_recovery_degradation") == AUTONOMOUS_RECOVERY_DEGRADATION_OWNER,
            owners.get("plaintext_credentials") == "none",
            all(row["mutable_by_adapter"] == "false" for row in STATE_OWNERSHIP_MATRIX_V1),
        ]
    )
    return {
        "ok": ok,
        "owner": OWNER,
        "matrix": list(STATE_OWNERSHIP_MATRIX_V1),
        "UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER": UNKNOWN_SUBMIT_RECONNECT_RECOVERY_OWNER,
        "RESTART_WITH_OPEN_ORDER_POSITION_OWNER": RESTART_WITH_OPEN_ORDER_POSITION_OWNER,
        "KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER": KILL_SWITCH_AND_EMERGENCY_CONTROL_OWNER,
        "AUTONOMOUS_RECOVERY_DEGRADATION_OWNER": AUTONOMOUS_RECOVERY_DEGRADATION_OWNER,
    }
