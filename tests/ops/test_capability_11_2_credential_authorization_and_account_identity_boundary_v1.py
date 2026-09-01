"""Tests for CAPABILITY_11_2 credential/authorization/account-identity boundary."""

from __future__ import annotations

import pytest

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    AccountIdentityViolationError,
    build_account_identity_record_v1,
    prove_account_identity_boundary_v1,
    validate_account_identity_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.authorization_binding_contract_v1 import (
    AuthorizationBindingViolationError,
    build_authorization_binding_v1,
    prove_authorization_binding_contract_v1,
    refuse_authorization_consumption_v1,
    validate_authorization_binding_against_runtime_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.autonomy_scope_limits_v1 import (
    AutonomyScopeViolationError,
    admit_venue_session_renewal_within_auth_v1,
    prove_autonomy_scope_limits_v1,
    refuse_authorization_scope_extension_v1,
    refuse_capital_limit_increase_v1,
    refuse_testnet_to_live_transition_v1,
    refuse_venue_enablement_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_contract_v1 import (
    CredentialContractViolationError,
    build_credential_reference_metadata_v1,
    prove_credential_contract_v1,
    refuse_plaintext_secret_persistence_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.credential_load_gate_v1 import (
    CredentialLoadGateError,
    CredentialLoadGateV1,
    prove_credential_load_gate_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.dependency_and_ownership_v1 import (
    prove_capability_11_1_dependency_retained_v1,
    prove_state_ownership_matrix_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.reachability_and_parity_v1 import (
    prove_core_logic_parity_v1,
    prove_negative_reachability_v1,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.verifier_v1 import (
    verify_capability_11_2_v1,
)


def _demo_binding():
    return build_authorization_binding_v1(
        authorization_id="authz-test",
        repository_sha="a" * 40,
        config_digest="cfg-" + "c" * 64,
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


def test_credential_reference_metadata_positive() -> None:
    meta = build_credential_reference_metadata_v1(
        credential_ref_id="cred-ref-1",
        secret_reference="secretref://vault/peak-trade/demo",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
    )
    assert meta.plaintext_present is False
    assert meta.withdrawal_permission is False
    assert meta.digest()


def test_credential_plaintext_and_withdrawal_negative() -> None:
    with pytest.raises(CredentialContractViolationError, match="PLAINTEXT_SECRET_FORBIDDEN"):
        build_credential_reference_metadata_v1(
            credential_ref_id="cred-ref-1",
            secret_reference="secretref://vault/peak-trade/demo",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            plaintext_secret="leak",
        )
    with pytest.raises(CredentialContractViolationError, match="WITHDRAWAL_PERMISSION_FORBIDDEN"):
        build_credential_reference_metadata_v1(
            credential_ref_id="cred-ref-1",
            secret_reference="secretref://vault/peak-trade/demo",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            withdrawal_permission=True,
        )
    with pytest.raises(CredentialContractViolationError):
        refuse_plaintext_secret_persistence_v1(candidate="x", surface="evidence")
    proof = prove_credential_contract_v1()
    assert proof["ok"] is True
    assert proof["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False


def test_authorization_binding_complete_and_mismatch_fail_closed() -> None:
    binding = _demo_binding()
    match = validate_authorization_binding_against_runtime_v1(
        binding,
        repository_sha=binding.repository_sha,
        config_digest=binding.config_digest,
        runtime_mode=binding.runtime_mode,
        venue=binding.venue,
        account_identity=binding.account_identity,
    )
    assert match["ok"] is True
    mismatch = validate_authorization_binding_against_runtime_v1(
        binding,
        repository_sha="deadbeef",
        config_digest=binding.config_digest,
        runtime_mode=binding.runtime_mode,
        venue=binding.venue,
        account_identity=binding.account_identity,
    )
    assert mismatch["ok"] is False
    assert "REPOSITORY_SHA_MISMATCH" in mismatch["blockers"]
    proof = prove_authorization_binding_contract_v1()
    assert proof["ok"] is True


def test_authorization_incomplete_and_consumption_forbidden() -> None:
    with pytest.raises(AuthorizationBindingViolationError, match="INCOMPLETE"):
        build_authorization_binding_v1(
            authorization_id="authz-bad",
            repository_sha="",
            config_digest="cfg",
            runtime_mode="SIMULATED",
            venue="OKX",
            account_identity="acct",
            instrument_or_active_set_scope=("BTC-USDT-SWAP",),
            maximum_notional="0",
            maximum_leverage="1",
            maximum_position_count=1,
            maximum_session_duration="PT0S",
            loss_and_drawdown_limits={"max_session_loss": "0"},
            allowed_order_types=("NONE",),
            allowed_side_effects=("NONE",),
            activation_epoch="0",
            expiry="1970-01-01T00:00:00Z",
        )
    with pytest.raises(AuthorizationBindingViolationError, match="CONSUMPTION_FORBIDDEN"):
        refuse_authorization_consumption_v1(_demo_binding())


def test_account_identity_boundary_positive_and_negative() -> None:
    record = build_account_identity_record_v1(
        account_identity="acct-uid-demo",
        venue="OKX",
        credential_ref_id="cred-ref-1",
        account_scope="trading-only",
        expected_uid="acct-uid-demo",
    )
    ok = validate_account_identity_v1(
        record, observed_account_identity="acct-uid-demo", observed_venue="OKX"
    )
    assert ok["ok"] is True
    unknown = validate_account_identity_v1(
        record, observed_account_identity="", observed_venue="OKX"
    )
    assert unknown["ok"] is False
    assert "UNKNOWN_ACCOUNT_IDENTITY" in unknown["blockers"]
    with pytest.raises(AccountIdentityViolationError, match="UID_MISMATCH"):
        build_account_identity_record_v1(
            account_identity="a",
            venue="OKX",
            credential_ref_id="cred-ref-1",
            account_scope="trading-only",
            expected_uid="b",
        )
    assert prove_account_identity_boundary_v1()["ok"] is True


def test_credential_load_gate_incomplete_and_complete_still_forbidden() -> None:
    gate = CredentialLoadGateV1()
    with pytest.raises(CredentialLoadGateError, match="PREREQUISITES_UNSATISFIED"):
        gate.attempt_credential_load_v1()
    for name in list(gate.prerequisites_satisfied):
        gate.mark_prerequisite(name, satisfied=True)
    assert gate.evaluate_admissibility()["admissible_for_future_load"] is True
    with pytest.raises(CredentialLoadGateError, match="FORBIDDEN_IN_CAPABILITY_11_2"):
        gate.attempt_credential_load_v1()
    assert prove_credential_load_gate_v1()["ok"] is True


def test_autonomy_scope_limits_positive_renewal_and_negative_extensions() -> None:
    binding = _demo_binding()
    renew = admit_venue_session_renewal_within_auth_v1(binding, authorization_still_valid=True)
    assert renew["admitted"] is True
    assert renew["network_session_started"] is False
    with pytest.raises(AutonomyScopeViolationError, match="SCOPE_EXTENSION"):
        refuse_authorization_scope_extension_v1(binding, requested_change="more_notional")
    with pytest.raises(AutonomyScopeViolationError, match="CAPITAL_LIMIT"):
        refuse_capital_limit_increase_v1(binding)
    with pytest.raises(AutonomyScopeViolationError, match="VENUE_ENABLEMENT"):
        refuse_venue_enablement_v1(binding, new_venue="UNDECLARED_VENUE")
    with pytest.raises(AutonomyScopeViolationError, match="TESTNET_TO_LIVE"):
        refuse_testnet_to_live_transition_v1(binding)
    assert prove_autonomy_scope_limits_v1(binding)["ok"] is True


def test_capability_11_1_dependency_retained() -> None:
    proof = prove_capability_11_1_dependency_retained_v1()
    assert proof["ok"] is True
    assert proof["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert proof["CAPABILITY_11_1_FAIL_CLOSED_RETAINED"] is True
    assert proof["CAPABILITY_11_1_IDEMPOTENCY_RETAINED"] is True
    assert proof["CAPABILITY_11_1_UNKNOWN_SEMANTICS_RETAINED"] is True
    assert proof["CAPABILITY_11_1_LIFECYCLE_RETAINED"] is True


def test_negative_reachability_and_parity() -> None:
    reach = prove_negative_reachability_v1()
    assert reach["ok"] is True
    assert reach["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False
    assert reach["EXCHANGE_ORDER_SUBMIT_REACHABLE"] is False
    assert reach["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert reach["NETWORK_SESSION_STARTED"] is False
    assert reach["TESTNET_EXECUTION_REACHABLE"] is False
    assert reach["LIVE_EXECUTION_REACHABLE"] is False
    parity = prove_core_logic_parity_v1()
    assert parity["ok"] is True
    assert parity["CORE_LOGIC_CHANGE"] is False


def test_state_ownership_matrix() -> None:
    ownership = prove_state_ownership_matrix_v1()
    assert ownership["ok"] is True
    assert (
        "credential_authorization_and_account_identity_boundary_v1"
        in ownership["CREDENTIAL_REFERENCE_METADATA_OWNER"]
    )


def test_failure_injection_contract_violations_only() -> None:
    gate = CredentialLoadGateV1()
    with pytest.raises(CredentialLoadGateError):
        gate.mark_prerequisite("not_a_real_prerequisite", satisfied=True)
    with pytest.raises(CredentialContractViolationError):
        build_credential_reference_metadata_v1(
            credential_ref_id="x",
            secret_reference="plaintext:abc",
            venue="OKX",
            account_identity="acct",
            instrument_scope=("BTC-USDT-SWAP",),
        )


def test_capability_verifier_pass() -> None:
    result = verify_capability_11_2_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    claims = result["claims"]
    assert claims["CORE_LOGIC_CHANGE"] is False
    assert claims["ACTIVATION_STATE"] == "not_activated"
    assert claims["TESTNET_AUTHORIZED"] is False
    assert claims["LIVE_AUTHORIZED"] is False
    assert claims["EXCHANGE_CREDENTIAL_ACCESS_REACHABLE"] is False
    assert claims["CAPABILITY_11_1_DEPENDENCY_SATISFIED"] is True
    assert claims["CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2"] is False
