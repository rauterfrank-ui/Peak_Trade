"""Tests for Cap 11.3 productive private read-only path binding."""

from __future__ import annotations

import pytest

from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.constants_v1 import (
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    PRIVATE_READONLY_FETCH_PERFORMED,
    PRIVATE_READONLY_GET_ALLOWLIST,
    PRIVATE_READONLY_PATH_ALLOWED_DEFAULT,
)
from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.path_binding_v1 import (
    ProductivePrivateReadonlyPathBindingError,
    attempt_private_readonly_fetch_via_productive_path_v1,
    build_productive_private_readonly_path_binding_v1,
    mark_cap_11_2_credential_load_path_bound_v1,
    prove_productive_private_readonly_path_binding_v1,
    refuse_cap_11_4_testnet_execution_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_env_keychain_provider_access_v1,
    refuse_network_session_v1,
    refuse_private_readonly_mutation_v1,
)
from src.ops.capability_11_3_productive_private_readonly_path_binding_v1.verifier_v1 import (
    verify_capability_11_3_productive_private_readonly_path_binding_v1,
)
from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.private_readonly_venue_port_v1 import (
    declare_private_readonly_venue_port_v1,
)

_SHA = "a03ad3daa7d5a890aba0e70e27c99b1f57885247"
_CFG = "cfg-" + ("e" * 64)


def _complete_kwargs(**overrides):
    port = declare_private_readonly_venue_port_v1()
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
        "cap_11_2_credential_load_path_bound": mark_cap_11_2_credential_load_path_bound_v1(
            repository_sha=_SHA, config_digest=_CFG
        ),
        "cap_11_3_private_readonly_port_declared": (
            port.CONSTRUCTIBLE is False and port.PRIVATE_READONLY_GET_ONLY is True
        ),
    }
    base.update(overrides)
    return base


def test_default_private_readonly_path_allowed_false() -> None:
    assert PRIVATE_READONLY_PATH_ALLOWED_DEFAULT is False
    binding = build_productive_private_readonly_path_binding_v1(
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
    assert binding.private_readonly_path_allowed is False
    assert "exchange_credential_use_authorized" in binding.missing_preconditions
    assert "testnet_authorized" in binding.missing_preconditions
    assert "cap_11_2_credential_load_path_bound" in binding.missing_preconditions


def test_complete_preconditions_admit_path_but_never_fetch() -> None:
    binding = build_productive_private_readonly_path_binding_v1(**_complete_kwargs())
    assert binding.private_readonly_path_allowed is True
    assert binding.missing_preconditions == ()
    assert binding.allowed_get_endpoints == PRIVATE_READONLY_GET_ALLOWLIST
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError,
        match="PRIVATE_READONLY_FETCH_FORBIDDEN_IN_PRODUCTIVE_PATH_BINDING",
    ):
        attempt_private_readonly_fetch_via_productive_path_v1(binding, endpoint="accounts")
    assert PRIVATE_READONLY_FETCH_PERFORMED is False


def test_incomplete_preconditions_block_fetch_attempt() -> None:
    binding = build_productive_private_readonly_path_binding_v1(
        **_complete_kwargs(
            exchange_credential_use_authorized=False,
            testnet_authorized=False,
            cap_11_2_credential_load_path_bound=False,
        )
    )
    assert binding.private_readonly_path_allowed is False
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError, match="PRIVATE_READONLY_PATH_NOT_ALLOWED"
    ):
        attempt_private_readonly_fetch_via_productive_path_v1(binding, endpoint="accounts")


def test_plaintext_and_withdrawal_rejected() -> None:
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError, match="PLAINTEXT_SECRET_FORBIDDEN"
    ):
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(plaintext_secret="leak")
        )
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError, match="WITHDRAWAL_PERMISSION_FORBIDDEN"
    ):
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(withdrawal_permission=True)
        )


def test_get_allowlist_and_mutation_fail_closed() -> None:
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(allowed_get_endpoints=("accounts", "sendorder"))
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(mutation_endpoint_requested=True)
        ).private_readonly_path_allowed
        is False
    )
    binding = build_productive_private_readonly_path_binding_v1(**_complete_kwargs())
    with pytest.raises(ProductivePrivateReadonlyPathBindingError, match="NOT_ALLOWLISTED"):
        attempt_private_readonly_fetch_via_productive_path_v1(binding, endpoint="sendorder")
    with pytest.raises(ProductivePrivateReadonlyPathBindingError, match="ORDER_MUTATION_FORBIDDEN"):
        refuse_private_readonly_mutation_v1(action="submit_order")


def test_non_testnet_and_binding_mismatches_fail_closed() -> None:
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(runtime_mode="SIMULATED")
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(expected_repository_sha="0" * 40)
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(expected_venue="BINANCE")
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(expected_account_identity="other")
        ).private_readonly_path_allowed
        is False
    )


def test_network_cap114_cap1113_and_provider_refusals() -> None:
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError, match="NETWORK_SESSION_FORBIDDEN"
    ):
        refuse_network_session_v1()
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError,
        match="CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN",
    ):
        refuse_cap_11_4_testnet_execution_v1()
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    with pytest.raises(
        ProductivePrivateReadonlyPathBindingError,
        match="CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN",
    ):
        refuse_env_keychain_provider_access_v1(provider="KEYCHAIN")
    assert CAPABILITY_11_4_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_started_flags_and_provider_block_allowance() -> None:
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(network_session_started=True)
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(cap_11_4_started=True)
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(cap_11_13_started=True)
        ).private_readonly_path_allowed
        is False
    )
    assert (
        build_productive_private_readonly_path_binding_v1(
            **_complete_kwargs(provider_access_attempted=True)
        ).private_readonly_path_allowed
        is False
    )


def test_prove_and_verify_pass() -> None:
    proof = prove_productive_private_readonly_path_binding_v1()
    assert proof["ok"] is True
    assert proof["private_readonly_fetch_performed"] is False
    assert proof["allowed_get_endpoints"] == [
        "accounts",
        "open_positions",
        "open_orders",
    ]
    assert proof["WITHDRAWAL_PERMISSION"] is False
    result = verify_capability_11_3_productive_private_readonly_path_binding_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["claims"]["PRIVATE_READONLY_PATH_ALLOWED_DEFAULT"] is False
    assert result["claims"]["PRIVATE_READONLY_FETCH_PERFORMED"] is False
    assert result["claims"]["CAPABILITY_11_4_STARTED"] is False
    assert result["claims"]["CAPABILITY_11_13_STARTED"] is False
