"""Tests for Cap 11 productive credential-load reference-only."""

from __future__ import annotations

import pytest

from src.ops.capability_11_productive_credential_load_reference_only_v1.constants_v1 import (
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT,
)
from src.ops.capability_11_productive_credential_load_reference_only_v1.reference_only_load_v1 import (
    ProductiveCredentialLoadReferenceOnlyError,
    attempt_credential_materialization_via_reference_only_v1,
    build_productive_credential_load_reference_only_v1,
    mark_cap_11_2_path_bound_for_reference_only_v1,
    mark_owner_auth_artifact_bound_for_reference_only_v1,
    prove_productive_credential_load_reference_only_v1,
    refuse_authorization_consumption_v1,
    refuse_cap_11_4_testnet_execution_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_credential_consumption_v1,
    refuse_env_keychain_provider_access_v1,
    refuse_network_session_v1,
    refuse_order_send_v1,
)
from src.ops.capability_11_productive_credential_load_reference_only_v1.verifier_v1 import (
    verify_capability_11_productive_credential_load_reference_only_v1,
)

_SHA = "0f75652dd5aca26284ff98e84c183186b87e6796"
_CFG = "cfg-" + ("a" * 64)


def _complete_kwargs(**overrides):
    cap112_bound = mark_cap_11_2_path_bound_for_reference_only_v1(
        repository_sha=_SHA, config_digest=_CFG
    )
    owner_auth_bound, owner_auth_digest = mark_owner_auth_artifact_bound_for_reference_only_v1(
        repository_sha=_SHA, config_digest=_CFG
    )
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
        "authorization_id": "owner-auth-for-reference-only-load",
        "owner_auth_artifact_bound": owner_auth_bound,
        "owner_auth_artifact_digest": owner_auth_digest,
        "cap_11_2_credential_load_path_bound": cap112_bound,
    }
    base.update(overrides)
    return base


def test_default_reference_only_load_admissible_false() -> None:
    assert REFERENCE_ONLY_LOAD_ADMISSIBLE_DEFAULT is False
    record = build_productive_credential_load_reference_only_v1(
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
        authorization_id="owner-auth-default",
    )
    assert record.reference_only_load_admissible is False
    assert "owner_auth_artifact_bound" in record.missing_preconditions
    assert "cap_11_2_credential_load_path_bound" in record.missing_preconditions


def test_complete_preconditions_admit_reference_but_never_materialize() -> None:
    record = build_productive_credential_load_reference_only_v1(**_complete_kwargs())
    assert record.reference_only_load_admissible is True
    assert record.missing_preconditions == ()
    assert record.credential_ref_id == "cred-ref-test"
    assert record.secret_reference == "secretref://vault/peak-trade/testnet-demo"
    assert record.instrument_scope == ("BTC-USDT-SWAP",)
    assert record.reference_only is True
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.authorization_consumed is False
    assert record.credential_consumed is False
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError,
        match="CREDENTIAL_MATERIALIZATION_FORBIDDEN_IN_REFERENCE_ONLY_LOAD",
    ):
        attempt_credential_materialization_via_reference_only_v1(record)
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False


def test_order_send_and_consumption_hard_rejected() -> None:
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="AUTHORIZATION_CONSUMPTION_FORBIDDEN"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(authorization_consumed=True)
        )
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="CREDENTIAL_CONSUMPTION_FORBIDDEN"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(credential_consumed=True)
        )


def test_plaintext_and_withdrawal_rejected() -> None:
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="PLAINTEXT_SECRET_FORBIDDEN"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(plaintext_secret="leak")
        )
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="WITHDRAWAL_PERMISSION_FORBIDDEN"
    ):
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(withdrawal_permission=True)
        )


def test_non_testnet_and_binding_mismatches_fail_closed() -> None:
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(runtime_mode="LIVE")
        ).reference_only_load_admissible
        is False
    )
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(expected_repository_sha="0" * 40)
        ).reference_only_load_admissible
        is False
    )
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(expected_venue="BINANCE")
        ).reference_only_load_admissible
        is False
    )


def test_refusals_for_consume_network_order_cap114_cap1113() -> None:
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="AUTHORIZATION_CONSUMPTION_FORBIDDEN"
    ):
        refuse_authorization_consumption_v1()
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="CREDENTIAL_CONSUMPTION_FORBIDDEN"
    ):
        refuse_credential_consumption_v1()
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="NETWORK_SESSION_FORBIDDEN"
    ):
        refuse_network_session_v1()
    with pytest.raises(ProductiveCredentialLoadReferenceOnlyError, match="ORDER_SEND_FORBIDDEN"):
        refuse_order_send_v1()
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError,
        match="CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN",
    ):
        refuse_cap_11_4_testnet_execution_v1()
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="CREDENTIAL_PROVIDER_ACCESS_FORBIDDEN"
    ):
        refuse_env_keychain_provider_access_v1(provider="KEYCHAIN")
    assert CAPABILITY_11_4_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_started_flags_block_admissibility() -> None:
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(network_session_started=True)
        ).reference_only_load_admissible
        is False
    )
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(cap_11_4_started=True)
        ).reference_only_load_admissible
        is False
    )
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(cap_11_13_started=True)
        ).reference_only_load_admissible
        is False
    )
    assert (
        build_productive_credential_load_reference_only_v1(
            **_complete_kwargs(provider_access_attempted=True)
        ).reference_only_load_admissible
        is False
    )


def test_incomplete_preconditions_block_materialization_attempt() -> None:
    record = build_productive_credential_load_reference_only_v1(
        credential_ref_id="cred-ref-incomplete",
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
        authorization_id="owner-auth-incomplete",
    )
    assert record.reference_only_load_admissible is False
    with pytest.raises(
        ProductiveCredentialLoadReferenceOnlyError, match="REFERENCE_ONLY_LOAD_NOT_ADMISSIBLE"
    ):
        attempt_credential_materialization_via_reference_only_v1(record)


def test_prove_and_verify_pass() -> None:
    proof = prove_productive_credential_load_reference_only_v1()
    assert proof["ok"] is True
    assert proof["complete_reference_only_load_admissible"] is True
    assert proof["intended_credential_object_bound"] is True
    assert proof["complete_path_materialization_still_forbidden"] is True
    assert proof["order_send_disabled"] is True
    assert proof["orders_authorized"] is False
    assert proof["credential_load_performed"] is False
    assert proof["credential_plaintext_loaded"] is False
    assert proof["authorization_consumed"] is False
    result = verify_capability_11_productive_credential_load_reference_only_v1()
    assert result["ok"] is True
    assert result["VERIFIER_RESULT"] == "PASS"
    assert result["claims"]["ORDER_SEND_DISABLED"] is True
    assert result["claims"]["ORDERS_AUTHORIZED"] is False
    assert result["claims"]["AUTHORIZATION_CONSUMPTION_ALLOWED"] is False
    assert result["claims"]["CREDENTIAL_LOAD_PERFORMED"] is False
    assert result["claims"]["CREDENTIAL_PLAINTEXT_LOADED"] is False
    assert result["claims"]["CAPABILITY_11_4_STARTED"] is False
    assert result["claims"]["CAPABILITY_11_13_STARTED"] is False
    assert result["claims"]["REFERENCE_ONLY"] is True
