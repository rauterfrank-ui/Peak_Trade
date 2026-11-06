"""Regression: governed live-C1 product path binds GET-only K1 handle to transport."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    KEYCHAIN_ACCOUNT_ID,
    KEYCHAIN_SERVICE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_item_class_and_value_encoding_v1 import (
    KEYCHAIN_ITEM_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
    JOIN_SEAM_ID,
    open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
    prove_get_only_transport_separated_from_post_authority_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)

FAKE_OPAQUE = json.dumps(
    {"apiKey": "ak-test", "secretKey": "sk-test", "passphrase": "pp-test"},
    separators=(",", ":"),
).encode("utf-8")


class _FakeKeychainBackend:
    def copy_matching_generic_password_value_data_v1(
        self,
        *,
        service: str,
        account: str,
        item_class: str,
    ) -> bytes:
        assert service == KEYCHAIN_SERVICE_ID
        assert account == KEYCHAIN_ACCOUNT_ID
        assert item_class == KEYCHAIN_ITEM_CLASS
        return FAKE_OPAQUE


def test_get_only_separation_proof_standing_false() -> None:
    proof = prove_get_only_transport_separated_from_post_authority_v1()
    assert proof["JOIN_SEAM_ID"] == JOIN_SEAM_ID
    assert proof["READ_ONLY_TRANSPORT_CAN_POST"] == "false"
    assert proof["POST_ALLOWED"] == "false"
    assert proof["CREDENTIAL_ACCESS_GRANTED_POST_AUTHORITY"] == "false"


def test_open_bind_yields_transport_with_k1_handle_for_fresh_pretrade(tmp_path: Path) -> None:
    with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
        max_request_count=32,
        k1_lookup_backend=_FakeKeychainBackend(),
    ) as (transport, proof):
        assert isinstance(transport, FullCoreProductiveReadOnlyGetTransportV1)
        assert proof["CREDENTIAL_HANDLE_PRESENT"] == "true"
        assert transport._handle is not None  # noqa: SLF001


def test_transport_without_handle_still_fail_closed_at_private_get() -> None:
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    with pytest.raises(
        FullCoreProductiveReadOnlyGetError, match="PRIVATE_GET_REQUIRES_CREDENTIAL_HANDLE"
    ):
        transport.get(
            endpoint="/api/v5/account/balance",
            auth_required=True,
            pretrade_decision_id="2026-01-01T00:00:00Z",
        )
