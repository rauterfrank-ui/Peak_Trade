"""Capability verifier for Cap 11.2 credential/authorization/account-identity boundary."""

from __future__ import annotations

from typing import Any

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    prove_account_identity_boundary_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.authorization_binding_contract_v1 import (
    build_authorization_binding_v1,
    prove_authorization_binding_contract_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.autonomy_scope_limits_v1 import (
    prove_autonomy_scope_limits_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACTIVATION_STATE,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    LIVE_AUTHORIZED,
    PREDECESSOR_CAPABILITY_ID,
    TESTNET_AUTHORIZED,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_contract_v1 import (
    prove_credential_contract_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_load_gate_v1 import (
    prove_credential_load_gate_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.reachability_and_parity_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)


def _demo_binding_for_autonomy_proof():
    return build_authorization_binding_v1(
        authorization_id="authz-cap11-2-verifier",
        repository_sha="0" * 40,
        config_digest="cfg-" + "b" * 64,
        runtime_mode="SIMULATED",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_or_active_set_scope=("BTC-USDT-SWAP",),
        maximum_notional="0",
        maximum_leverage="1",
        maximum_position_count=1,
        maximum_session_duration="PT0S",
        loss_and_drawdown_limits={"max_session_loss": "0", "max_drawdown": "0"},
        allowed_order_types=("NONE",),
        allowed_side_effects=("NONE",),
        activation_epoch="0",
        expiry="1970-01-01T00:00:00Z",
    )


def verify_capability_11_2_v1() -> dict[str, Any]:
    binding = _demo_binding_for_autonomy_proof()
    proofs = {
        "credential_contract": prove_credential_contract_v1(),
        "authorization_binding": prove_authorization_binding_contract_v1(),
        "account_identity": prove_account_identity_boundary_v1(),
        "credential_load_gate": prove_credential_load_gate_v1(),
        "autonomy_scope_limits": prove_autonomy_scope_limits_v1(binding),
        "dependency_11_1": prove_capability_11_1_dependency_retained_v1(),
        "state_ownership": prove_state_ownership_matrix_v1(),
        "negative_reachability": prove_negative_reachability_v1(),
        "core_logic_parity": prove_core_logic_parity_v1(),
    }
    ok = all(bool(p.get("ok")) for p in proofs.values())
    claims = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
        "CAPABILITY_11_1_DEPENDENCY_SATISFIED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_DEPENDENCY_SATISFIED"
        ),
        "LEAST_PRIVILEGE": proofs["credential_contract"].get("LEAST_PRIVILEGE"),
        "WITHDRAWAL_PERMISSION": proofs["credential_contract"].get("WITHDRAWAL_PERMISSION"),
        "SECRET_REFERENCE_ONLY_IN_CONFIG": proofs["credential_contract"].get(
            "SECRET_REFERENCE_ONLY_IN_CONFIG"
        ),
        "PLAINTEXT_SECRET_NEVER_PERSISTED": proofs["credential_contract"].get(
            "PLAINTEXT_SECRET_NEVER_PERSISTED"
        ),
        "CREDENTIAL_FAILURE_FAILS_CLOSED": proofs["credential_contract"].get(
            "CREDENTIAL_FAILURE_FAILS_CLOSED"
        ),
        "AUTHORIZATION_BINDINGS_COMPLETE": proofs["authorization_binding"].get("ok"),
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "ACCOUNT_SCOPE_EXPLICIT": proofs["account_identity"].get("ACCOUNT_SCOPE_EXPLICIT"),
        "CREDENTIAL_LOAD_GATE_BOUND": proofs["credential_load_gate"].get("ok"),
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2": False,
        "AUTONOMOUS_AUTHORIZATION_SCOPE_EXTENSION": False,
        "AUTONOMOUS_CAPITAL_LIMIT_INCREASE": False,
        "AUTONOMOUS_VENUE_ENABLEMENT": False,
        "AUTONOMOUS_TESTNET_TO_LIVE_TRANSITION": False,
        "TESTNET_EXECUTION_REACHABLE": False,
        "LIVE_EXECUTION_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "NETWORK_SESSION_STARTED": False,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ACTIVATION_STATE": ACTIVATION_STATE,
        "CAPABILITY_11_1_FAIL_CLOSED_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_FAIL_CLOSED_RETAINED"
        ),
        "CAPABILITY_11_1_IDEMPOTENCY_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_IDEMPOTENCY_RETAINED"
        ),
        "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED"
        ),
        "CAPABILITY_11_1_LIFECYCLE_RETAINED": proofs["dependency_11_1"].get(
            "CAPABILITY_11_1_LIFECYCLE_RETAINED"
        ),
    }
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "VERIFIER_RESULT": "PASS" if ok else "FAIL",
        "claims": claims,
        "proofs": proofs,
        "call_graph_before": CALL_GRAPH_BEFORE,
        "call_graph_after": CALL_GRAPH_AFTER,
    }
