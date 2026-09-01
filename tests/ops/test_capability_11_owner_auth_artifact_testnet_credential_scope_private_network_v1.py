"""Tests for Owner Auth Artifact Testnet credential scope private network."""

from __future__ import annotations

import pytest

from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.constants_v1 import (
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    NETWORK_SCOPE_REQUIRED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT,
    PRIVATE_READONLY_GET_ALLOWLIST,
)
from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.owner_auth_artifact_v1 import (
    OwnerAuthArtifactError,
    build_owner_auth_artifact_testnet_credential_scope_private_network_v1,
    mark_cap_11_2_path_bound_for_owner_auth_v1,
    mark_cap_11_3_productive_private_readonly_path_bound_v1,
    prove_owner_auth_artifact_testnet_credential_scope_private_network_v1,
    refuse_authorization_consumption_v1,
    refuse_cap_11_4_testnet_execution_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_credential_load_v1,
    refuse_env_keychain_provider_access_v1,
    refuse_network_session_v1,
    refuse_order_send_v1,
    refuse_private_readonly_mutation_v1,
)
from src.ops.capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1.verifier_v1 import (
    verify_capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1,
)

_SHA = "869b3e1ddc79c0f5e65b378c1b39d97b0a28884a"
_CFG = "cfg-" + ("f" * 64)
_LIMITS = {"max_daily_loss": "0", "max_drawdown": "0"}


def _complete_kwargs(**overrides):
    base = {
        "authorization_id": "owner-auth-test",
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
        "maximum_notional": "0",
        "maximum_leverage": "1",
        "maximum_position_count": 1,
        "maximum_session_duration": "0s",
        "loss_and_drawdown_limits": _LIMITS,
        "activation_epoch": "epoch-0",
        "expiry": "never-activate-in-this-capability",
        "artifact_testnet_authorized": True,
        "artifact_exchange_credential_use_authorized": True,
        "artifact_network_session_authorized_private_readonly": True,
        "cap_11_2_credential_load_path_bound": mark_cap_11_2_path_bound_for_owner_auth_v1(
            repository_sha=_SHA, config_digest=_CFG
        ),
        "cap_11_3_productive_private_readonly_path_bound": (
            mark_cap_11_3_productive_private_readonly_path_bound_v1(
                repository_sha=_SHA, config_digest=_CFG
            )
        ),
    }
    base.update(overrides)
    return base


def test_default_owner_auth_artifact_admissible_false() -> None:
    assert OWNER_AUTH_ARTIFACT_ADMISSIBLE_DEFAULT is False
    artifact = build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
        authorization_id="owner-auth-default",
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
        maximum_notional="0",
        maximum_leverage="1",
        maximum_position_count=1,
        maximum_session_duration="0s",
        loss_and_drawdown_limits=_LIMITS,
        activation_epoch="epoch-0",
        expiry="never-activate-in-this-capability",
    )
    assert artifact.owner_auth_artifact_admissible is False
    assert "artifact_testnet_authorized" in artifact.missing_preconditions
    assert "cap_11_3_productive_private_readonly_path_bound" in artifact.missing_preconditions


def test_complete_preconditions_admit_artifact_but_never_consume_or_send() -> None:
    artifact = build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
        **_complete_kwargs()
    )
    assert artifact.owner_auth_artifact_admissible is True
    assert artifact.missing_preconditions == ()
    assert artifact.order_send_disabled is True
    assert artifact.orders_authorized is False
    assert artifact.network_scope == NETWORK_SCOPE_REQUIRED
    assert artifact.allowed_get_endpoints == PRIVATE_READONLY_GET_ALLOWLIST
    assert artifact.authorization_consumed is False
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False


def test_order_send_and_consumption_hard_rejected() -> None:
    with pytest.raises(OwnerAuthArtifactError, match="ORDER_SEND_MUST_REMAIN_DISABLED"):
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(OwnerAuthArtifactError, match="ORDER_SEND_MUST_REMAIN_DISABLED"):
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(OwnerAuthArtifactError, match="AUTHORIZATION_CONSUMPTION_FORBIDDEN"):
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(authorization_consumed=True)
        )


def test_plaintext_and_withdrawal_rejected() -> None:
    with pytest.raises(OwnerAuthArtifactError, match="PLAINTEXT_SECRET_FORBIDDEN"):
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(plaintext_secret="leak")
        )
    with pytest.raises(OwnerAuthArtifactError, match="WITHDRAWAL_PERMISSION_FORBIDDEN"):
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(withdrawal_permission=True)
        )


def test_network_scope_allowlist_and_order_types_fail_closed() -> None:
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(network_scope="PUBLIC_MARKET_DATA_ONLY")
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(allowed_get_endpoints=("accounts", "sendorder"))
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(allowed_order_types=("limit",))
        ).owner_auth_artifact_admissible
        is False
    )


def test_non_testnet_and_binding_mismatches_fail_closed() -> None:
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(runtime_mode="LIVE")
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(expected_repository_sha="0" * 40)
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(expected_venue="UNDECLARED_VENUE")
        ).owner_auth_artifact_admissible
        is False
    )


def test_refusals_for_consume_network_load_order_cap114_cap1113() -> None:
    with pytest.raises(OwnerAuthArtifactError, match="AUTHORIZATION_CONSUMPTION_FORBIDDEN"):
        refuse_authorization_consumption_v1()
    with pytest.raises(OwnerAuthArtifactError, match="NETWORK_SESSION_FORBIDDEN"):
        refuse_network_session_v1()
    with pytest.raises(OwnerAuthArtifactError, match="CREDENTIAL_LOAD_FORBIDDEN"):
        refuse_credential_load_v1()
    with pytest.raises(OwnerAuthArtifactError, match="ORDER_SEND_FORBIDDEN"):
        refuse_order_send_v1()
    with pytest.raises(OwnerAuthArtifactError, match="CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN"):
        refuse_cap_11_4_testnet_execution_v1()
    with pytest.raises(OwnerAuthArtifactError, match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN"):
        refuse_cap_11_13_live_activation_v1()
    with pytest.raises(OwnerAuthArtifactError, match="CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN"):
        refuse_env_keychain_provider_access_v1(provider="KEYCHAIN")
    with pytest.raises(OwnerAuthArtifactError, match="ORDER_MUTATION_FORBIDDEN"):
        refuse_private_readonly_mutation_v1(action="submit_order")
    assert CAPABILITY_11_4_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_started_flags_block_admissibility() -> None:
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(network_session_started=True)
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(cap_11_4_started=True)
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(cap_11_13_started=True)
        ).owner_auth_artifact_admissible
        is False
    )
    assert (
        build_owner_auth_artifact_testnet_credential_scope_private_network_v1(
            **_complete_kwargs(provider_access_attempted=True)
        ).owner_auth_artifact_admissible
        is False
    )


def test_prove_and_verify_pass() -> None:
    proof = prove_owner_auth_artifact_testnet_credential_scope_private_network_v1()
    assert proof["ok"] is True
    assert proof["order_send_disabled"] is True
    assert proof["orders_authorized"] is False
    assert proof["authorization_consumed"] is False
    assert proof["network_scope"] == "PRIVATE_READONLY_GET_ONLY"
    assert proof["allowed_get_endpoints"] == [
        "accounts",
        "open_positions",
        "open_orders",
    ]
    result = verify_capability_11_owner_auth_artifact_testnet_credential_scope_private_network_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["claims"]["ORDER_SEND_DISABLED"] is True
    assert result["claims"]["ORDERS_AUTHORIZED"] is False
    assert result["claims"]["CAPABILITY_11_4_STARTED"] is False
    assert result["claims"]["CAPABILITY_11_13_STARTED"] is False
