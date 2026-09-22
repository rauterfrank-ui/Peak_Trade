"""Tests for Full-Core K1 opaque signing-handle pre-POST seam.

No real Keychain. No network POST. No permit mint.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    build_k1_okx_venue_auth_headers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    ALLOWED_EPHEMERAL_KEYCHAIN_ACCESS_CONSUMERS_V1,
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    FullCoreCheckoutIndependentOsNativeStoreAcquisitionError,
    bounded_ephemeral_keychain_access_v1,
    opaque_os_native_store_material_is_held_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
    OWNER_GO,
    CurrentProductiveK1OpaqueSigningHandleError,
    open_current_productive_k1_opaque_signing_handle_session_v1,
    parse_full_core_k1_keychain_utf8_json_material_v1,
    prove_k1_opaque_signing_handle_does_not_authorize_post_v1,
    prove_productive_http_transport_rejects_without_one_shot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

FAKE_OPAQUE = json.dumps(
    {"apiKey": "ak-test", "secretKey": "sk-test", "passphrase": "pp-test"},
    separators=(",", ":"),
).encode("utf-8")

SEAM_PATH = Path(
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.py"
)


class _FakeKeychainBackend:
    def __init__(self, *, payload: bytes | None = FAKE_OPAQUE, absent: bool = False) -> None:
        self.payload = payload
        self.absent = absent
        self.calls = 0

    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        self.calls += 1
        assert service == KEYCHAIN_SERVICE_ID
        assert account == KEYCHAIN_ACCOUNT_ID
        assert item_class == KEYCHAIN_ITEM_CLASS
        if self.absent is True:
            raise FullCoreCheckoutIndependentOsNativeStoreAcquisitionError("KEYCHAIN_ITEM_ABSENT")
        if self.payload is None:
            raise FullCoreCheckoutIndependentOsNativeStoreAcquisitionError(
                "KEYCHAIN_VALUE_UNEXPECTED_REPRESENTATION"
            )
        return self.payload


def test_ephemeral_consumer_allowlist_includes_k1_pre_post_and_rejects_unknown() -> None:
    assert EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002 in (
        ALLOWED_EPHEMERAL_KEYCHAIN_ACCESS_CONSUMERS_V1
    )
    assert EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST in (
        ALLOWED_EPHEMERAL_KEYCHAIN_ACCESS_CONSUMERS_V1
    )
    with pytest.raises(
        FullCoreCheckoutIndependentOsNativeStoreAcquisitionError,
        match="EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_FORBIDDEN",
    ):
        with bounded_ephemeral_keychain_access_v1(consumer_id="NOT_AN_ALLOWED_CONSUMER"):
            pass


def test_standing_pins_remain_false_and_first_blocker_unchanged() -> None:
    assert REAL_KEYCHAIN_ACCESS_AUTHORIZED is False
    assert REAL_KEYCHAIN_ACCESS_IMPLEMENTED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert current_productive_first_real_blocker_v1() == (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    )
    proof = prove_k1_opaque_signing_handle_does_not_authorize_post_v1()
    assert proof["ONE_SHOT_REAL_POST"] == "false"
    assert proof["PERMIT_MINTED"] == "false"


def test_success_seam_binds_opaque_signing_handle_without_material_loaded() -> None:
    backend = _FakeKeychainBackend()
    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=OWNER_GO,
        backend=backend,
    ) as session:
        assert backend.calls == 1
        assert session.proof.disposition == "OPAQUE_SIGNING_HANDLE_BOUND"
        assert session.proof.material_loaded == "false"
        assert session.proof.permit_minted == "false"
        assert session.proof.one_shot_real_post == "false"
        assert session.proof.network_post_attempted == "false"
        assert session.proof.source_ref_uri == SOURCE_REF_URI
        assert session.signing_handle.bound is True
        assert session.signing_handle.can_sign is True
        assert session.signing_handle.material_loaded is False
        headers = build_k1_okx_venue_auth_headers_v1(
            handle=session.signing_handle,
            url="https://eea.okx.com/api/v5/account/balance",
            method="GET",
            body="",
        )
        assert "OK-ACCESS-KEY" in headers
        assert "OK-ACCESS-SIGN" in headers
        proof_blob = json.dumps(session.proof.to_dict())
        assert "sk-test" not in proof_blob
        assert "ak-test" not in proof_blob
        assert "pp-test" not in proof_blob
        transport_proof = prove_productive_http_transport_rejects_without_one_shot_v1(
            signing_handle=session.signing_handle,
        )
        assert transport_proof["TRANSPORT_POST_COUNT"] == "0"
        assert transport_proof["VENUE_LIVE_CONTACT"] == "false"
    assert opaque_os_native_store_material_is_held_v1(id(object())) is False


def test_owner_go_mismatch_and_missing_backend_fail_closed() -> None:
    with pytest.raises(CurrentProductiveK1OpaqueSigningHandleError, match="OWNER_GO_MISMATCH"):
        with open_current_productive_k1_opaque_signing_handle_session_v1(
            owner_go="WRONG_GO",
            backend=_FakeKeychainBackend(),
        ):
            pass
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError,
        match="LOOKUP_BACKEND_REQUIRED_NO_DEFAULT_REAL_KEYCHAIN_IN_THIS_WP",
    ):
        with open_current_productive_k1_opaque_signing_handle_session_v1(owner_go=OWNER_GO):
            pass


def test_absent_item_and_malformed_opaque_fail_closed() -> None:
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError,
        match="K1_CREDENTIAL_ACQUISITION_FAIL_CLOSED",
    ):
        with open_current_productive_k1_opaque_signing_handle_session_v1(
            owner_go=OWNER_GO,
            backend=_FakeKeychainBackend(absent=True),
        ):
            pass

    with pytest.raises(CurrentProductiveK1OpaqueSigningHandleError, match="K1_OPAQUE_EMPTY"):
        parse_full_core_k1_keychain_utf8_json_material_v1(b"")
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError, match="K1_OPAQUE_UTF8_DECODE_FAIL"
    ):
        parse_full_core_k1_keychain_utf8_json_material_v1(b"\xff\xfe")
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError, match="K1_OPAQUE_JSON_MALFORMED"
    ):
        parse_full_core_k1_keychain_utf8_json_material_v1(b"{not-json")
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError, match="K1_OPAQUE_JSON_NOT_OBJECT"
    ):
        parse_full_core_k1_keychain_utf8_json_material_v1(b"[1,2]")
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError, match="K1_OPAQUE_JSON_FIELD_SET_MISMATCH"
    ):
        parse_full_core_k1_keychain_utf8_json_material_v1(
            json.dumps({"apiKey": "a", "secretKey": "b"}).encode("utf-8")
        )
    with pytest.raises(
        CurrentProductiveK1OpaqueSigningHandleError, match="K1_CREDENTIAL_FIELDS_INCOMPLETE"
    ):
        parse_full_core_k1_keychain_utf8_json_material_v1(
            json.dumps(
                {"apiKey": "a", "secretKey": "b", "passphrase": "  "},
                separators=(",", ":"),
            ).encode("utf-8")
        )


def test_handle_released_after_session_exit() -> None:
    backend = _FakeKeychainBackend()
    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=OWNER_GO,
        backend=backend,
    ) as session:
        handle = session.signing_handle
    with pytest.raises(Exception, match="EPHEMERAL_MATERIAL_GONE"):
        build_k1_okx_venue_auth_headers_v1(
            handle=handle,
            url="https://eea.okx.com/api/v5/account/balance",
            method="GET",
            body="",
        )


def test_seam_source_forbids_post_and_permit_and_fallback_markers() -> None:
    source = SEAM_PATH.read_text(encoding="utf-8")
    for marker in (
        "one_shot_real_post=True",
        "issue_external_effect_permit",
        "attempt_envelope_bound_external_effect_send",
        "os.environ",
        "SECRETREF",
        "FILE_VAULT",
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED = True",
        "REAL_KEYCHAIN_ACCESS_IMPLEMENTED = True",
    ):
        assert marker not in source
    assert "LOOKUP_BACKEND_REQUIRED_NO_DEFAULT_REAL_KEYCHAIN_IN_THIS_WP" in source
