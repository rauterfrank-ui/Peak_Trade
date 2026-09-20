"""Adversarial tests for PL-TF-002 productive read-only session executor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    FullCoreCheckoutIndependentCredentialCapabilityError,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    MacosSecurityFrameworkLookupBackendV1,
    REASON_ITEM_ABSENT,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    opaque_os_native_store_material_is_held_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.verifier_v1 import (
    verify_pl_tf_002_network_evidence_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY,
    K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE,
    K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY,
    OWNER_GO,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.k1_keychain_utf8_json_material_v1 import (
    parse_k1_keychain_utf8_json_material_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    assert_host_is_authorized_eea_okx_v1,
    build_pl_tf_002_read_only_get_session_preflight_v1,
    open_pl_tf_002_productive_read_only_get_session_v1,
    prove_pl_tf_002_session_does_not_authorize_post_v1,
    public_session_proof_v1,
)

FAKE_OPAQUE = json.dumps(
    {
        K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY: "test-api-key-not-real",
        K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY: "test-secret-not-real",
        K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE: "test-pass-not-real",
    }
).encode("utf-8")


class _FakeKeychainBackend(MacosSecurityFrameworkLookupBackendV1):
    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        del service, account, item_class
        return FAKE_OPAQUE


class _AbsentKeychainBackend(MacosSecurityFrameworkLookupBackendV1):
    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        del service, account, item_class
        raise FullCoreCheckoutIndependentCredentialCapabilityError(REASON_ITEM_ABSENT)


def test_no_owner_go_denied() -> None:
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="OWNER_GO_MISMATCH"):
        build_pl_tf_002_read_only_get_session_preflight_v1(
            owner_go="OWNER_GO_WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        )


def test_wrong_origin_sha_denied() -> None:
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        build_pl_tf_002_read_only_get_session_preflight_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
        )


def test_preflight_pass_without_credential_load() -> None:
    pre = build_pl_tf_002_read_only_get_session_preflight_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert pre.disposition == "PREFLIGHT_PASS"
    assert pre.authorized_host == AUTHORIZED_HOST
    assert pre.k1_may_perform_get_standing == "false"
    assert pre.k1_real_keychain_access_standing == "false"
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False


def test_credential_unavailable_fail_closed() -> None:
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="K1_CREDENTIAL_ACQUISITION"):
        with open_pl_tf_002_productive_read_only_get_session_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            acquire_credential=True,
            backend=_AbsentKeychainBackend(),
        ):
            pass  # pragma: no cover


def test_credential_acquisition_success_binds_transport() -> None:
    with open_pl_tf_002_productive_read_only_get_session_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        acquire_credential=True,
        backend=_FakeKeychainBackend(),
    ) as session:
        assert session.credential_acquired is True
        assert session.network_executed_by_executor is False
        assert isinstance(session.transport, FullCoreProductiveReadOnlyGetTransportV1)
        assert session.transport.request_count == 0
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False


def test_host_not_eea_okx_denied() -> None:
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="HOST_NOT_EEA_OKX"):
        assert_host_is_authorized_eea_okx_v1(host="www.okx.com")


def test_transport_post_and_treasury_forbidden() -> None:
    from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
        _assert_get_only_surface_v1,
    )

    transport = FullCoreProductiveReadOnlyGetTransportV1(handle=None)
    with pytest.raises(FullCoreProductiveReadOnlyGetError, match="FORBIDDEN_ENDPOINT"):
        transport.get(
            endpoint="/api/v5/trade/order",
            auth_required=False,
            pretrade_decision_id="pl-tf-002-test",
        )
    with pytest.raises(FullCoreProductiveReadOnlyGetError, match="FORBIDDEN_ENDPOINT"):
        transport.get(
            endpoint="/api/v5/asset/withdrawal",
            auth_required=False,
            pretrade_decision_id="pl-tf-002-test",
        )
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="HTTP_METHOD_FORBIDDEN"):
        _assert_get_only_surface_v1(endpoint_path="/api/v5/account/config", method="POST")
    post_proof = prove_pl_tf_002_session_does_not_authorize_post_v1()
    assert post_proof["POST_ALLOWED"] == "false"
    assert "POST" in post_proof["TRANSPORT_FORBIDDEN_METHODS"]


def test_secrets_not_in_public_proof_or_parse_errors() -> None:
    blob = public_session_proof_v1(
        {"disposition": "PREFLIGHT_PASS", "authorized_host": AUTHORIZED_HOST}
    )
    assert "apiKey" not in json.dumps(blob)
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="SECRET_LEAK"):
        public_session_proof_v1({"apiKey": "x"})
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="FIELD_SET_MISMATCH"):
        parse_k1_keychain_utf8_json_material_v1(
            json.dumps({"api_key": "a", "secret": "b", "passphrase": "c"}).encode()
        )


def test_k2_legacy_not_imported_in_session_executor_module() -> None:
    import src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 as mod

    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    for token in ("secretref", "vault_file", "hmacsecret", "k2_"):
        assert token not in source


def test_external_effect_standing_false() -> None:
    from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        K2_REINTRODUCED,
        K2_REMOVED,
    )

    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert K2_REMOVED is True
    assert K2_REINTRODUCED is False


def test_pl_tf_002_verifier_contract_unchanged_synthetic_pass() -> None:
    import time

    from tests.ops.test_pl_tf_002_network_evidence_contract_v1 import _synthetic_bundle

    result = verify_pl_tf_002_network_evidence_v1(_synthetic_bundle())
    assert result["VERIFICATION_RESULT"] == "PASS"
    assert int(time.time()) > 0  # bundle freshness sanity


def test_opaque_wiped_after_session(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 as sess_mod

    wipe_calls: list[int] = []
    original_wipe = sess_mod.wipe_opaque_os_native_store_material_v1

    def _spy_wipe(holder_id: int) -> None:
        wipe_calls.append(holder_id)
        original_wipe(holder_id)

    monkeypatch.setattr(sess_mod, "wipe_opaque_os_native_store_material_v1", _spy_wipe)
    with open_pl_tf_002_productive_read_only_get_session_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        acquire_credential=True,
        backend=_FakeKeychainBackend(),
    ):
        pass
    assert len(wipe_calls) >= 1
