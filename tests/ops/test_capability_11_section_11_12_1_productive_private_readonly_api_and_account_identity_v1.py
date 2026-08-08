"""Tests for Cap 11 §11.12.1 productive private-readonly API and account identity."""

from __future__ import annotations

import pytest

from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.constants_v1 import (
    ACCOUNT_IDENTITY_PATH_CLASS,
    CAPABILITY_11_4_STARTED,
    CAPABILITY_11_13_STARTED,
    NETWORK_WRITES_AUTHORIZED,
    ORDER_SEND_DISABLED,
    ORDERS_AUTHORIZED,
    TRANSPORT_CLASS_GOVERNED_FIXTURE,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.section_11_12_1_v1 import (
    GovernedFixturePrivateReadonlyGetTransportV1,
    Section11121ProductivePrivateReadonlyError,
    execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1,
    mark_fetch_reference_only_predecessor_bound_v1,
    prove_section_11_12_1_productive_private_readonly_api_and_account_identity_v1,
    refuse_cap_11_4_testnet_execution_v1,
    refuse_cap_11_13_live_activation_v1,
    refuse_network_write_v1,
    refuse_order_send_v1,
    validate_get_allowlist_v1,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.verifier_v1 import (
    verify_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1,
)
from src.ops.capability_11_productive_private_readonly_fetch_reference_only_v1.reference_only_fetch_v1 import (
    mark_cap_11_3_path_bound_for_fetch_reference_only_v1,
)

_SHA = "806e55c4357b90a45c5362672e29f9d8f67949fc"
_CFG = "cfg-" + ("b" * 64)
_MATERIAL = "fixture-credential-material-never-logged-or-evidenced"


def _complete_kwargs(**overrides):
    (
        pred_bound,
        owner_auth_digest,
        _cred_load_digest,
        fetch_ref_digest,
    ) = mark_fetch_reference_only_predecessor_bound_v1(repository_sha=_SHA, config_digest=_CFG)
    path_bound = mark_cap_11_3_path_bound_for_fetch_reference_only_v1(
        repository_sha=_SHA, config_digest=_CFG
    )
    base = {
        "credential_ref_id": "cred-ref-section-11-12-1",
        "secret_reference": "secretref://vault/peak-trade/testnet-demo",
        "credential_material": _MATERIAL,
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
        "authorization_id": "owner-auth-for-section-11-12-1",
        "owner_auth_artifact_digest": owner_auth_digest,
        "fetch_reference_only_binding_digest": fetch_ref_digest,
        "fetch_reference_only_predecessor_bound": pred_bound,
        "owner_auth_artifact_bound": pred_bound,
        "credential_load_reference_only_bound": pred_bound,
        "cap_11_3_productive_private_readonly_path_bound": path_bound,
        "transport": GovernedFixturePrivateReadonlyGetTransportV1(
            expected_account_identity="acct-uid-demo"
        ),
    }
    base.update(overrides)
    return base


def test_productive_account_identity_fetch_consumes_auth_and_credential() -> None:
    record = execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
        **_complete_kwargs()
    )
    assert record.authorization_consumed is True
    assert record.credential_consumed is True
    assert record.network_session_started is True
    assert record.account_identity_fetch_performed is True
    assert record.http_method == "GET"
    assert record.endpoint == "accounts"
    assert record.path_class == ACCOUNT_IDENTITY_PATH_CLASS
    assert record.account_identity_observed == "acct-uid-demo"
    assert record.transport_class == TRANSPORT_CLASS_GOVERNED_FIXTURE
    assert record.venue_live_contact is False
    assert record.order_send_disabled is True
    assert record.orders_authorized is False
    assert record.network_writes_authorized is False
    assert record.network_write_performed is False
    assert record.exchange_order_submit_reachable is False
    assert record.reference_only is False
    assert _MATERIAL not in record.credential_material_digest
    assert ORDER_SEND_DISABLED is True
    assert ORDERS_AUTHORIZED is False
    assert NETWORK_WRITES_AUTHORIZED is False


def test_incomplete_preconditions_fail_closed() -> None:
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError, match="SECTION_11_12_1_NOT_ADMISSIBLE"
    ):
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **_complete_kwargs(
                fetch_reference_only_predecessor_bound=False,
                owner_auth_artifact_bound=False,
                credential_load_reference_only_bound=False,
            )
        )


def test_order_send_and_network_writes_hard_rejected() -> None:
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **_complete_kwargs(order_send_disabled=False)
        )
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError, match="ORDER_SEND_MUST_REMAIN_DISABLED"
    ):
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **_complete_kwargs(orders_authorized=True)
        )
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError, match="NETWORK_WRITES_FORBIDDEN"
    ):
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **_complete_kwargs(network_writes_authorized=True)
        )


def test_non_allowlisted_method_and_endpoint_fail_closed() -> None:
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError, match="HTTP_METHOD_NOT_ALLOWLISTED"
    ):
        validate_get_allowlist_v1(endpoint="accounts", http_method="POST")
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError,
        match="ENDPOINT_NOT_ALLOWLISTED_FOR_SECTION_11_12_1",
    ):
        validate_get_allowlist_v1(endpoint="open_positions", http_method="GET")
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError,
        match="ENDPOINT_NOT_IN_PRIVATE_READONLY_GET_ALLOWLIST",
    ):
        validate_get_allowlist_v1(endpoint="submit_order", http_method="GET")


def test_authorization_replay_and_cap_refusals() -> None:
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError,
        match="AUTHORIZATION_ALREADY_CONSUMED_REPLAY_FORBIDDEN",
    ):
        execute_section_11_12_1_productive_private_readonly_api_and_account_identity_v1(
            **_complete_kwargs(authorization_already_consumed=True)
        )
    with pytest.raises(Section11121ProductivePrivateReadonlyError, match="ORDER_SEND_FORBIDDEN"):
        refuse_order_send_v1()
    with pytest.raises(Section11121ProductivePrivateReadonlyError, match="NETWORK_WRITE_FORBIDDEN"):
        refuse_network_write_v1(method="POST")
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError,
        match="CAPABILITY_11_4_TESTNET_EXECUTION_FORBIDDEN",
    ):
        refuse_cap_11_4_testnet_execution_v1()
    with pytest.raises(
        Section11121ProductivePrivateReadonlyError,
        match="CAPABILITY_11_13_LIVE_ACTIVATION_FORBIDDEN",
    ):
        refuse_cap_11_13_live_activation_v1()
    assert CAPABILITY_11_4_STARTED is False
    assert CAPABILITY_11_13_STARTED is False


def test_prove_and_verifier_pass() -> None:
    proof = prove_section_11_12_1_productive_private_readonly_api_and_account_identity_v1()
    assert proof["ok"] is True
    assert proof["authorization_consumed"] is True
    assert proof["credential_consumed"] is True
    assert proof["account_identity_fetch_performed"] is True
    assert proof["http_method"] == "GET"
    assert proof["endpoint"] == "accounts"
    assert _MATERIAL not in str(proof)
    verification = verify_capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1()
    assert verification["ok"] is True
    assert verification["VERIFIER_RESULT"] == "PASS"
    assert verification["claims"]["ORDER_SEND_DISABLED"] is True
    assert verification["claims"]["ORDERS_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITES_AUTHORIZED"] is False
    assert verification["claims"]["NETWORK_WRITE_PERFORMED"] is False
    assert verification["claims"]["AUTHORIZATION_CONSUMED"] is True
    assert verification["claims"]["CREDENTIAL_CONSUMED"] is True
    assert verification["claims"]["ACCOUNT_IDENTITY_FETCH_PERFORMED"] is True
    assert verification["claims"]["CAPABILITY_11_4_STARTED"] is False
    assert verification["claims"]["CAPABILITY_11_13_STARTED"] is False
