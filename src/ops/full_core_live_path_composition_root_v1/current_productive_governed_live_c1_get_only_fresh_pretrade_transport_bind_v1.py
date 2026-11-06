"""Bind GET-only K1 credential handle to productive Fresh-Pretrade transport.

GHV / governed live-C1 product path: ephemeral macOS Keychain → K1 signing
handle → FullCoreProductiveReadOnlyGetTransportV1. Does not authorize POST,
permit mint, or external effect. Standing REAL_KEYCHAIN_ACCESS_* pins stay false.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    MacosSecurityFrameworkLookupBackendV1,
    OsNativeStoreLookupBackendV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
    OWNER_GO as K1_OPAQUE_SIGNING_OWNER_GO,
    open_current_productive_k1_opaque_signing_handle_session_v1,
    prove_k1_opaque_signing_handle_does_not_authorize_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FORBIDDEN_ENDPOINTS,
    FORBIDDEN_METHODS,
    FullCoreProductiveReadOnlyGetTransportV1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_GOVERNED_LIVE_C1_GET_ONLY_FRESH_PRETRADE_TRANSPORT_BIND_V1"
PRODUCT_LAUNCHER_CREDENTIAL_BINDING = JOIN_SEAM_ID

K1_HANDLE_PROVIDER = "open_current_productive_k1_opaque_signing_handle_session_v1"
CREDENTIAL_HANDLE_TYPE = "FullCoreK1BoundVenueAuthHandleV1"
CREDENTIAL_HANDLE_OWNER = K1_OPAQUE_SIGNING_OWNER_GO
KEYCHAIN_ADAPTER = "FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1"
PRIVATE_GET_SIGNER = "build_k1_okx_venue_auth_headers_v1"
EXISTING_GET_ONLY_AUTHORITY_GATE = "bounded_ephemeral_keychain_access_v1"
EXISTING_KEYCHAIN_AUTHORITY_GATE = "assert_real_keychain_access_authorized_for_os_lookup_v1"


class GovernedLiveC1GetOnlyFreshPretradeTransportBindError(RuntimeError):
    """Fail-closed GET-only Fresh-Pretrade transport bind violation."""


def prove_get_only_transport_separated_from_post_authority_v1() -> dict[str, str]:
    """Non-secret proof that read-only transport cannot POST or mutate venue."""

    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise GovernedLiveC1GetOnlyFreshPretradeTransportBindError(
            "POST_STANDING_MUST_REMAIN_FALSE"
        )
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise GovernedLiveC1GetOnlyFreshPretradeTransportBindError(
            "EXTERNAL_EFFECT_MUST_REMAIN_FALSE"
        )
    k1_proof = prove_k1_opaque_signing_handle_does_not_authorize_post_v1()
    return {
        "JOIN_SEAM_ID": JOIN_SEAM_ID,
        "TARGET_TRANSPORT": "FullCoreProductiveReadOnlyGetTransportV1",
        "TARGET_TRANSPORT_ALLOWED_METHODS": "GET_ONLY",
        "READ_ONLY_TRANSPORT_CAN_POST": "false",
        "READ_ONLY_TRANSPORT_CAN_PLACE_ORDER": "false",
        "READ_ONLY_TRANSPORT_CAN_AMEND_ORDER": "false",
        "READ_ONLY_TRANSPORT_CAN_CANCEL_ORDER": "false",
        "READ_ONLY_TRANSPORT_CAN_TRANSFER": "false",
        "READ_ONLY_TRANSPORT_CAN_WITHDRAW": "false",
        "TRANSPORT_FORBIDDEN_METHODS": ",".join(sorted(FORBIDDEN_METHODS)),
        "TRANSPORT_FORBIDDEN_ENDPOINTS": ",".join(sorted(FORBIDDEN_ENDPOINTS)),
        "POST_ALLOWED": "false",
        "EXTERNAL_EFFECT_AUTHORIZED": "false",
        "REAL_VENUE_POST_ALLOWED": "false",
        "K1_MAY_POST": k1_proof.get("K1_MAY_POST", "false"),
        "CREDENTIAL_ACCESS_GRANTED_POST_AUTHORITY": "false",
    }


@contextmanager
def open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
    *,
    max_request_count: int,
    k1_lookup_backend: OsNativeStoreLookupBackendV1 | None = None,
) -> Iterator[tuple[FullCoreProductiveReadOnlyGetTransportV1, dict[str, str]]]:
    """Ephemeral K1 handle bound to GET-only transport for one product run."""

    prove_get_only_transport_separated_from_post_authority_v1()
    if int(max_request_count) <= 0:
        raise GovernedLiveC1GetOnlyFreshPretradeTransportBindError("MAX_REQUEST_COUNT_INVALID")
    backend = k1_lookup_backend or MacosSecurityFrameworkLookupBackendV1()
    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        backend=backend,
    ) as session:
        transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=session.signing_handle,
            max_request_count=int(max_request_count),
        )
        bind_proof = {
            **prove_get_only_transport_separated_from_post_authority_v1(),
            "K1_HANDLE_PROVIDER": K1_HANDLE_PROVIDER,
            "CREDENTIAL_HANDLE_TYPE": CREDENTIAL_HANDLE_TYPE,
            "CREDENTIAL_HANDLE_OWNER": CREDENTIAL_HANDLE_OWNER,
            "PRIVATE_GET_SIGNER": PRIVATE_GET_SIGNER,
            "CREDENTIAL_HANDLE_PRESENT": "true",
            "K1_MATERIAL_LOADED": session.proof.material_loaded,
            "HANDLE_ID": session.proof.handle_id,
            "EPHEMERAL_KEYCHAIN_CONSUMER": session.proof.ephemeral_keychain_consumer,
        }
        yield transport, bind_proof


__all__ = [
    "CREDENTIAL_HANDLE_OWNER",
    "CREDENTIAL_HANDLE_TYPE",
    "EXISTING_GET_ONLY_AUTHORITY_GATE",
    "EXISTING_KEYCHAIN_AUTHORITY_GATE",
    "GovernedLiveC1GetOnlyFreshPretradeTransportBindError",
    "JOIN_SEAM_ID",
    "K1_HANDLE_PROVIDER",
    "KEYCHAIN_ADAPTER",
    "PRIVATE_GET_SIGNER",
    "PRODUCT_LAUNCHER_CREDENTIAL_BINDING",
    "open_governed_live_c1_get_only_fresh_pretrade_transport_v1",
    "prove_get_only_transport_separated_from_post_authority_v1",
]
