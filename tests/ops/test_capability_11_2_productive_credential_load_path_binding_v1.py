"""Tests for Cap 11.2 productive credential-load path binding."""

from __future__ import annotations

import pytest

from src.ops.capability_11_2_productive_credential_load_path_binding_v1.constants_v1 import (
    CAPABILITY_11_13_STARTED,
    CAPABILITY_11_3_STARTED,
    CREDENTIAL_LOAD_ALLOWED_DEFAULT,
    CREDENTIAL_LOAD_PERFORMED,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.path_binding_v1 import (
    ProductiveCredentialLoadPathBindingError,
    attempt_credential_load_via_productive_path_v1,
    build_productive_credential_load_path_binding_v1,
    mark_cap_11_2_gate_prerequisites_complete_v1,
    prove_productive_credential_load_path_binding_v1,
    refuse_cap_11_3_private_readonly_construction_v1,
    refuse_env_keychain_provider_access_v1,
    refuse_network_session_v1,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.verifier_v1 import (
    verify_capability_11_2_productive_credential_load_path_binding_v1,
)

_SHA = "5e4b71268a5cbb969a97b1522750b53cfb01c556"
_CFG = "cfg-" + ("d" * 64)


def _complete_kwargs(**overrides):
    gate = mark_cap_11_2_gate_prerequisites_complete_v1()
    base = {
        "credential_ref_id": "cred-ref-test",
        "secret_reference": "secretref://vault/peak-trade/testnet-demo",
        "runtime_mode": "TESTNET",
        "venue": "OKX",
        "account_identity": "acct-uid-demo",
        "instrument_scope": ("BTC-USDT-SWAP",),
        "repository_sha": _SHA,
        "config_digest": _CFG,
        "expected_repository_sha": _SHA,
        "expected_config_digest": _CFG,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": "OKX",
        "exchange_credential_use_authorized": True,
        "testnet_authorized": True,
        "cap_11_2_gate_prerequisites_satisfied": gate.evaluate_admissibility()[
            "admissible_for_future_load"
        ],
    }
    base.update(overrides)
    return base


def test_default_credential_load_allowed_false() -> None:
    assert CREDENTIAL_LOAD_ALLOWED_DEFAULT is False
    binding = build_productive_credential_load_path_binding_v1(
        credential_ref_id="cred-ref-default",
        secret_reference="secretref://vault/peak-trade/testnet-demo",
        runtime_mode="TESTNET",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
        repository_sha=_SHA,
        config_digest=_CFG,
        expected_repository_sha=_SHA,
        expected_config_digest=_CFG,
        expected_account_identity="acct-uid-demo",
        expected_venue="OKX",
    )
    assert binding.credential_load_allowed is False
    assert "exchange_credential_use_authorized" in binding.missing_preconditions
    assert "testnet_authorized" in binding.missing_preconditions


def test_complete_preconditions_admit_path_but_never_load() -> None:
    binding = build_productive_credential_load_path_binding_v1(**_complete_kwargs())
    assert binding.credential_load_allowed is True
    assert binding.missing_preconditions == ()
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError,
        match="CREDENTIAL_LOAD_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING",
    ):
        attempt_credential_load_via_productive_path_v1(binding)
    assert CREDENTIAL_LOAD_PERFORMED is False


def test_incomplete_preconditions_block_load_attempt() -> None:
    binding = build_productive_credential_load_path_binding_v1(
        **_complete_kwargs(
            exchange_credential_use_authorized=False,
            testnet_authorized=False,
            cap_11_2_gate_prerequisites_satisfied=False,
        )
    )
    assert binding.credential_load_allowed is False
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError, match="CREDENTIAL_LOAD_NOT_ALLOWED"
    ):
        attempt_credential_load_via_productive_path_v1(binding)


def test_plaintext_and_withdrawal_rejected() -> None:
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError, match="PLAINTEXT_SECRET_FORBIDDEN"
    ):
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(plaintext_secret="leak")
        )
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError, match="WITHDRAWAL_PERMISSION_FORBIDDEN"
    ):
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(withdrawal_permission=True)
        )


def test_non_testnet_and_binding_mismatches_fail_closed() -> None:
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(runtime_mode="SIMULATED")
        ).credential_load_allowed
        is False
    )
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(expected_repository_sha="0" * 40)
        ).credential_load_allowed
        is False
    )
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(expected_venue="BINANCE")
        ).credential_load_allowed
        is False
    )
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(expected_account_identity="other")
        ).credential_load_allowed
        is False
    )


def test_cap_11_3_network_and_provider_refusals() -> None:
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError,
        match="CAPABILITY_11_3_PRIVATE_READONLY_CONSTRUCTION_FORBIDDEN",
    ):
        refuse_cap_11_3_private_readonly_construction_v1()
    with pytest.raises(ProductiveCredentialLoadPathBindingError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_network_session_v1()
    with pytest.raises(
        ProductiveCredentialLoadPathBindingError,
        match="CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN",
    ):
        refuse_env_keychain_provider_access_v1(provider="KEYCHAIN")
    assert CAPABILITY_11_3_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_cap_11_3_started_or_network_started_blocks_allowance() -> None:
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(cap_11_3_started=True)
        ).credential_load_allowed
        is False
    )
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(network_session_started=True)
        ).credential_load_allowed
        is False
    )
    assert (
        build_productive_credential_load_path_binding_v1(
            **_complete_kwargs(provider_access_attempted=True)
        ).credential_load_allowed
        is False
    )


def test_prove_and_verify_pass() -> None:
    proof = prove_productive_credential_load_path_binding_v1()
    assert proof["ok"] is True
    assert proof["credential_load_performed"] is False
    assert proof["WITHDRAWAL_PERMISSION"] is False
    result = verify_capability_11_2_productive_credential_load_path_binding_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["claims"]["CREDENTIAL_LOAD_ALLOWED_DEFAULT"] is False
    assert result["claims"]["CAPABILITY_11_3_STARTED"] is False
    assert result["claims"]["CAPABILITY_11_13_STARTED"] is False
