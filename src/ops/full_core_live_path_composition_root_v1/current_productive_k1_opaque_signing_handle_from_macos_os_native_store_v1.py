"""Full-Core K1 opaque signing-handle seam from macOS Keychain (pre-POST).

Owner-GO-scoped ephemeral Keychain acquisition → closed-world UTF-8 JSON parse
→ FullCoreK1BoundVenueAuthHandleV1. Standing REAL_KEYCHAIN_ACCESS_AUTHORIZED
and REAL_KEYCHAIN_ACCESS_IMPLEMENTED remain false. Never mints a permit, never
sets one_shot_real_post, never opens a venue socket.

OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    MAY_PERFORM_GET as K1_MAY_PERFORM_GET,
    MAY_POST as K1_MAY_POST,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as K1_AUTH_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    FullCoreK1BoundVenueAuthHandleV1,
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as ACQ_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_KEYCHAIN_ACCESS_IMPLEMENTED as ACQ_REAL_KEYCHAIN_ACCESS_IMPLEMENTED,
    OsNativeStoreLookupBackendV1,
    bounded_ephemeral_keychain_access_v1,
    borrow_held_opaque_bytes_for_bounded_parse_v1,
    wipe_opaque_os_native_store_material_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)

OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)
THIS_SLICE = "CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_K1_OPAQUE_SIGNING_HANDLE_FROM_MACOS_KEYCHAIN_SEAM_V1"
EPHEMERAL_KEYCHAIN_CONSUMER = EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_K1_OPAQUE_SIGNING_HANDLE_PRE_POST
CONTRACT_VERSION = "v1"

K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY = "apiKey"
K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY = "secretKey"
K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE = "passphrase"
K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY,
        K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY,
        K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE,
    }
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key", "authorization")


class CurrentProductiveK1OpaqueSigningHandleError(RuntimeError):
    """Fail-closed K1 opaque signing-handle seam violation."""


@dataclass(frozen=True)
class CurrentProductiveK1OpaqueSigningHandleProofV1:
    """Non-secret proof that an opaque signing handle was bound."""

    disposition: str
    owner_go_accepted: str
    join_seam_id: str
    source_ref_uri: str
    credential_class: str
    ephemeral_keychain_consumer: str
    handle_id: str
    handle_bound: str
    handle_can_sign: str
    material_loaded: str
    standing_real_keychain_access_authorized: str
    standing_real_keychain_access_implemented: str
    external_effect_authorized: str
    post_allowed: str
    real_venue_post_allowed: str
    step_29q_status: str
    first_real_blocker: str
    permit_minted: str
    one_shot_real_post: str
    network_post_attempted: str

    def to_dict(self) -> dict[str, str]:
        return {
            "disposition": self.disposition,
            "owner_go_accepted": self.owner_go_accepted,
            "join_seam_id": self.join_seam_id,
            "source_ref_uri": self.source_ref_uri,
            "credential_class": self.credential_class,
            "ephemeral_keychain_consumer": self.ephemeral_keychain_consumer,
            "handle_id": self.handle_id,
            "handle_bound": self.handle_bound,
            "handle_can_sign": self.handle_can_sign,
            "material_loaded": self.material_loaded,
            "standing_real_keychain_access_authorized": (
                self.standing_real_keychain_access_authorized
            ),
            "standing_real_keychain_access_implemented": (
                self.standing_real_keychain_access_implemented
            ),
            "external_effect_authorized": self.external_effect_authorized,
            "post_allowed": self.post_allowed,
            "real_venue_post_allowed": self.real_venue_post_allowed,
            "step_29q_status": self.step_29q_status,
            "first_real_blocker": self.first_real_blocker,
            "permit_minted": self.permit_minted,
            "one_shot_real_post": self.one_shot_real_post,
            "network_post_attempted": self.network_post_attempted,
        }

    def __repr__(self) -> str:
        return "CurrentProductiveK1OpaqueSigningHandleProofV1(redacted)"

    def __str__(self) -> str:
        return "CurrentProductiveK1OpaqueSigningHandleProofV1(redacted)"


@dataclass
class CurrentProductiveK1OpaqueSigningHandleSessionV1:
    """Ephemeral opaque signing session. Caller must not persist secrets."""

    proof: CurrentProductiveK1OpaqueSigningHandleProofV1
    signing_handle: FullCoreK1BoundVenueAuthHandleV1

    def __repr__(self) -> str:
        return "CurrentProductiveK1OpaqueSigningHandleSessionV1(redacted)"


def parse_full_core_k1_keychain_utf8_json_material_v1(opaque: bytes) -> tuple[str, str, str]:
    """Decode opaque Keychain bytes to apiKey/secretKey/passphrase. Fail closed."""

    if not isinstance(opaque, (bytes, bytearray)) or len(opaque) == 0:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_OPAQUE_EMPTY")
    try:
        text = bytes(opaque).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_OPAQUE_UTF8_DECODE_FAIL") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_OPAQUE_JSON_MALFORMED") from exc
    if not isinstance(payload, Mapping):
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_OPAQUE_JSON_NOT_OBJECT")
    keys = frozenset(str(k) for k in payload.keys())
    if keys != K1_KEYCHAIN_UTF8_JSON_REQUIRED_FIELDS:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_OPAQUE_JSON_FIELD_SET_MISMATCH")
    api_key = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_API_KEY) or "").strip()
    secret = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_SECRET_KEY) or "").strip()
    phrase = str(payload.get(K1_KEYCHAIN_UTF8_JSON_FIELD_PASSPHRASE) or "").strip()
    if not api_key or not secret or not phrase:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_CREDENTIAL_FIELDS_INCOMPLETE")
    return api_key, secret, phrase


def _assert_standing_pins_v1() -> None:
    if ACQ_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError(
            "STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED"
        )
    if ACQ_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError(
            "STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNIMPLEMENTED"
        )
    if EA_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True or EA_REAL_KEYCHAIN_ACCESS_IMPLEMENTED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError("EA_REAL_KEYCHAIN_STANDING_DRIFT")
    if K1_AUTH_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError(
            "K1_AUTH_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_UNAUTHORIZED"
        )
    if K1_MAY_PERFORM_GET is True or K1_MAY_POST is True:
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_GET_POST_MUST_REMAIN_UNAUTHORIZED")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError(
            "STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE"
        )
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise CurrentProductiveK1OpaqueSigningHandleError("POST_STANDING_MUST_REMAIN_FALSE")
    if str(STEP_29Q_PLAN_ONLY) != "PLAN_ONLY":
        raise CurrentProductiveK1OpaqueSigningHandleError("STEP_29Q_MUST_REMAIN_PLAN_ONLY")


def _assert_no_secret_leak_v1(payload: Mapping[str, str]) -> None:
    blob = json.dumps(dict(payload), sort_keys=True).lower()
    for token in _SECRET_TOKENS:
        # handle_id / join tokens may contain substrings; forbid credential field names only
        # when accompanied by value-like patterns is too fuzzy — reject raw field dumps.
        if f'"{token}"' in blob or f"'{token}'" in blob:
            raise CurrentProductiveK1OpaqueSigningHandleError(f"SECRET_TOKEN_PRESENT:{token}")


def prove_k1_opaque_signing_handle_does_not_authorize_post_v1() -> dict[str, str]:
    _assert_standing_pins_v1()
    return {
        "POST_ALLOWED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "K1_MAY_POST": FALSE_TOKEN,
        "STANDING_REAL_KEYCHAIN_ACCESS_AUTHORIZED": FALSE_TOKEN,
        "STANDING_REAL_KEYCHAIN_ACCESS_IMPLEMENTED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "FIRST_REAL_BLOCKER": current_productive_first_real_blocker_v1(),
        "PERMIT_MINTED": FALSE_TOKEN,
        "ONE_SHOT_REAL_POST": FALSE_TOKEN,
    }


def prove_productive_http_transport_rejects_without_one_shot_v1(
    *,
    signing_handle: FullCoreK1BoundVenueAuthHandleV1,
) -> dict[str, str]:
    """Construct productive HTTP transport with signing handle; prove no socket without one_shot."""

    _assert_standing_pins_v1()
    if not isinstance(signing_handle, FullCoreK1BoundVenueAuthHandleV1):
        raise CurrentProductiveK1OpaqueSigningHandleError("K1_VENUE_AUTH_HANDLE_TYPE_FORBIDDEN")
    send_handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-k1-opaque-signing-send-handle",
        bound=True,
        material_loaded=False,
    )
    transport = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=send_handle,
        signing_handle=signing_handle,
    )
    try:
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST", "side": "buy", "sz": "1", "ordType": "market"},
            permit_id="eep-k1-must-not-post",
            envelope_id="env-k1-must-not-post",
            envelope_digest="0" * 64,
            one_shot_real_post=False,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveK1OpaqueSigningHandleError("HTTP_FORBIDDEN_MISSING") from exc
    else:
        raise CurrentProductiveK1OpaqueSigningHandleError("HTTP_MUST_NOT_POST")
    if int(transport.post_count) != 0:
        raise CurrentProductiveK1OpaqueSigningHandleError("HTTP_TRANSPORT_SIDE_EFFECT")
    if transport.venue_live_contact is True:
        raise CurrentProductiveK1OpaqueSigningHandleError("VENUE_LIVE_CONTACT_FORBIDDEN")
    return {
        "TRANSPORT_POST_COUNT": "0",
        "VENUE_LIVE_CONTACT": FALSE_TOKEN,
        "ONE_SHOT_REAL_POST": FALSE_TOKEN,
        "REJECT_REASON": "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE",
    }


@contextmanager
def open_current_productive_k1_opaque_signing_handle_session_v1(
    *,
    owner_go: str,
    backend: OsNativeStoreLookupBackendV1 | None = None,
) -> Iterator[CurrentProductiveK1OpaqueSigningHandleSessionV1]:
    """Ephemeral Keychain → opaque parse → K1 signing handle. Wipe on exit.

    Does not flip standing REAL_KEYCHAIN_ACCESS_* pins. Does not POST.
    """

    _assert_standing_pins_v1()
    if owner_go != OWNER_GO:
        raise CurrentProductiveK1OpaqueSigningHandleError("OWNER_GO_MISMATCH")
    if backend is None:
        raise CurrentProductiveK1OpaqueSigningHandleError(
            "LOOKUP_BACKEND_REQUIRED_NO_DEFAULT_REAL_KEYCHAIN_IN_THIS_WP"
        )

    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    handle: FullCoreK1BoundVenueAuthHandleV1 | None = None
    session: CurrentProductiveK1OpaqueSigningHandleSessionV1 | None = None
    try:
        with bounded_ephemeral_keychain_access_v1(consumer_id=EPHEMERAL_KEYCHAIN_CONSUMER):
            try:
                adapter.acquire_opaque_os_native_store_material_v1(
                    source_ref=SOURCE_REF_URI,
                    backend=backend,
                )
            except Exception as exc:
                raise CurrentProductiveK1OpaqueSigningHandleError(
                    "K1_CREDENTIAL_ACQUISITION_FAIL_CLOSED"
                ) from exc
            opaque = borrow_held_opaque_bytes_for_bounded_parse_v1(holder_id=id(adapter))
            api_key, secret, phrase = parse_full_core_k1_keychain_utf8_json_material_v1(opaque)
            try:
                handle = bind_already_held_k1_venue_auth_session_v1(
                    api_key=api_key,
                    api_secret=secret,
                    passphrase=phrase,
                )
            finally:
                api_key = ""
                secret = ""
                phrase = ""
            proof = CurrentProductiveK1OpaqueSigningHandleProofV1(
                disposition="OPAQUE_SIGNING_HANDLE_BOUND",
                owner_go_accepted=TRUE_TOKEN,
                join_seam_id=JOIN_SEAM_ID,
                source_ref_uri=SOURCE_REF_URI,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
                ephemeral_keychain_consumer=EPHEMERAL_KEYCHAIN_CONSUMER,
                handle_id=handle.handle_id,
                handle_bound=TRUE_TOKEN if handle.bound is True else FALSE_TOKEN,
                handle_can_sign=TRUE_TOKEN if handle.can_sign is True else FALSE_TOKEN,
                material_loaded=FALSE_TOKEN,
                standing_real_keychain_access_authorized=FALSE_TOKEN,
                standing_real_keychain_access_implemented=FALSE_TOKEN,
                external_effect_authorized=FALSE_TOKEN,
                post_allowed=FALSE_TOKEN,
                real_venue_post_allowed=FALSE_TOKEN,
                step_29q_status=STEP_29Q_PLAN_ONLY,
                first_real_blocker=current_productive_first_real_blocker_v1(),
                permit_minted=FALSE_TOKEN,
                one_shot_real_post=FALSE_TOKEN,
                network_post_attempted=FALSE_TOKEN,
            )
            _assert_no_secret_leak_v1(proof.to_dict())
            session = CurrentProductiveK1OpaqueSigningHandleSessionV1(
                proof=proof,
                signing_handle=handle,
            )
            yield session
    finally:
        if handle is not None:
            release_k1_venue_auth_session_v1(handle)
        wipe_opaque_os_native_store_material_v1(id(adapter))
        if session is not None:
            session.signing_handle = None  # type: ignore[misc]
