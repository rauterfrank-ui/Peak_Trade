"""Governed PL-TF-002 productive read-only GET session executor.

OWNER_GO-scoped transition to ephemeral K1 Keychain acquisition and
FullCoreProductiveReadOnlyGetTransportV1 bind. No POST. No evidence persist.
No standing status flip. No network unless caller invokes transport.get outside
this module after a successful bind (capture WP).
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_capability_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_concrete_backend_item_identity_v1 import (
    SOURCE_REF_URI,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_fail_closed_os_native_store_adapter_v1 import (
    FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    MAY_PERFORM_GET as K1_MAY_PERFORM_GET,
    MAY_POST as K1_MAY_POST,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED as K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    bind_already_held_k1_venue_auth_session_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_os_native_store_acquisition_v1 import (
    EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002,
    OsNativeStoreLookupBackendV1,
    bounded_ephemeral_keychain_access_v1,
    borrow_held_opaque_bytes_for_bounded_parse_v1,
    wipe_opaque_os_native_store_material_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    PRIVATE_GET_PATHS,
    PUBLIC_GET_PATHS,
    REQUIRED_GET_ITEM_SPECS,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FORBIDDEN_ENDPOINTS as TRANSPORT_FORBIDDEN_ENDPOINTS,
    FORBIDDEN_METHODS as TRANSPORT_FORBIDDEN_METHODS,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    NE_TF_001_ENDPOINT_PATH,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    ALLOWED_PRODUCTIVE_TRANSPORT_CLASSES,
    AUTHORIZED_HOST as CONTRACT_AUTHORIZED_HOST,
    EPHEMERAL_KEYCHAIN_CONSUMER,
    FORBIDDEN_HTTP_METHODS,
    FORBIDDEN_MUTATION_ENDPOINTS,
    JOIN_SEAM_ID,
    METHOD_ALLOWLIST,
    OWNER_GO,
    TRANSPORT_CLASS,
    WP_ID,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.k1_macos_opaque_utf8_json_material_v1 import (
    parse_k1_keychain_utf8_json_material_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.runtime_integrity_v1 import (
    PlTf002RuntimeIntegrityBackendV1,
    assert_pl_tf_002_runtime_integrity_v1,
    default_integrity_backend_v1,
)

FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


@dataclass(frozen=True)
class PlTf002ReadOnlyGetSessionPreflightV1:
    """Non-secret session envelope proof."""

    disposition: str
    wp_id: str
    owner_go_accepted: str
    origin_main_sha_bound: str
    authorized_host: str
    http_method_allowlist: tuple[str, ...]
    f1_endpoint_paths: tuple[str, ...]
    f2_endpoint_path: str
    transport_class: str
    k1_may_perform_get_standing: str
    k1_real_keychain_access_standing: str
    ephemeral_keychain_consumer: str
    external_effect_authorized: str
    post_allowed_standing: str
    credential_class: str
    source_ref_uri: str
    join_seam_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "disposition": self.disposition,
            "wp_id": self.wp_id,
            "owner_go_accepted": self.owner_go_accepted,
            "origin_main_sha_bound": self.origin_main_sha_bound,
            "authorized_host": self.authorized_host,
            "http_method_allowlist": ",".join(self.http_method_allowlist),
            "f1_endpoint_paths": ",".join(self.f1_endpoint_paths),
            "f2_endpoint_path": self.f2_endpoint_path,
            "transport_class": self.transport_class,
            "k1_may_perform_get_standing": self.k1_may_perform_get_standing,
            "k1_real_keychain_access_standing": self.k1_real_keychain_access_standing,
            "ephemeral_keychain_consumer": self.ephemeral_keychain_consumer,
            "external_effect_authorized": self.external_effect_authorized,
            "post_allowed_standing": self.post_allowed_standing,
            "credential_class": self.credential_class,
            "source_ref_uri": self.source_ref_uri,
            "join_seam_id": self.join_seam_id,
        }

    def __repr__(self) -> str:
        return "PlTf002ReadOnlyGetSessionPreflightV1(redacted)"


@dataclass
class PlTf002ProductiveReadOnlyGetSessionV1:
    """Bound read-only GET session. Transport may perform GET when caller invokes it."""

    preflight: PlTf002ReadOnlyGetSessionPreflightV1
    transport: FullCoreProductiveReadOnlyGetTransportV1
    k1_handle_id: str
    credential_acquired: bool
    network_executed_by_executor: bool

    def __repr__(self) -> str:
        return "PlTf002ProductiveReadOnlyGetSessionV1(redacted)"


def _assert_standing_pins_v1() -> None:
    if K1_MAY_PERFORM_GET is True or K1_MAY_POST is True:
        raise PlTf002ProductiveReadOnlySessionError("K1_STANDING_GET_POST_MUST_REMAIN_FALSE")
    if K1_REAL_KEYCHAIN_ACCESS_AUTHORIZED is True:
        raise PlTf002ProductiveReadOnlySessionError(
            "K1_STANDING_REAL_KEYCHAIN_ACCESS_MUST_REMAIN_FALSE"
        )
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise PlTf002ProductiveReadOnlySessionError("EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if POST_ALLOWED is True or REAL_VENUE_POST_ALLOWED is True:
        raise PlTf002ProductiveReadOnlySessionError("POST_STANDING_MUST_REMAIN_FALSE")
    if AUTHORIZED_HOST != CONTRACT_AUTHORIZED_HOST:
        raise PlTf002ProductiveReadOnlySessionError("AUTHORIZED_HOST_DRIFT")
    if TRANSPORT_CLASS not in ALLOWED_PRODUCTIVE_TRANSPORT_CLASSES:
        raise PlTf002ProductiveReadOnlySessionError("TRANSPORT_CLASS_NOT_PRODUCTIVE")
    if EPHEMERAL_KEYCHAIN_CONSUMER != EPHEMERAL_KEYCHAIN_ACCESS_CONSUMER_PL_TF_002:
        raise PlTf002ProductiveReadOnlySessionError("EPHEMERAL_CONSUMER_DRIFT")


def _validate_owner_go_and_runtime_integrity_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    integrity_backend: PlTf002RuntimeIntegrityBackendV1 | None,
) -> str:
    backend = integrity_backend if integrity_backend is not None else default_integrity_backend_v1()
    return assert_pl_tf_002_runtime_integrity_v1(
        owner_go=owner_go,
        declared_origin_main_sha=origin_main_sha,
        required_owner_go=OWNER_GO,
        integrity_backend=backend,
    )


def _f1_endpoint_paths_v1() -> tuple[str, ...]:
    paths = sorted({spec.endpoint_path for spec in REQUIRED_GET_ITEM_SPECS})
    return tuple(paths)


def _assert_get_only_surface_v1(*, endpoint_path: str, method: str) -> None:
    method_u = str(method or "").upper()
    if method_u not in METHOD_ALLOWLIST:
        raise PlTf002ProductiveReadOnlySessionError(f"HTTP_METHOD_FORBIDDEN:{method_u}")
    if method_u in FORBIDDEN_HTTP_METHODS or method_u in TRANSPORT_FORBIDDEN_METHODS:
        raise PlTf002ProductiveReadOnlySessionError(f"HTTP_METHOD_FORBIDDEN:{method_u}")
    path = str(endpoint_path or "").split("?", 1)[0]
    if path in FORBIDDEN_MUTATION_ENDPOINTS or path in TRANSPORT_FORBIDDEN_ENDPOINTS:
        raise PlTf002ProductiveReadOnlySessionError("TREASURY_OR_MUTATION_ENDPOINT_FORBIDDEN")
    allowed = PUBLIC_GET_PATHS | PRIVATE_GET_PATHS
    if path not in allowed:
        raise PlTf002ProductiveReadOnlySessionError("ENDPOINT_NOT_ON_FRESH_PRETRADE_ALLOWLIST")


def build_pl_tf_002_read_only_get_session_preflight_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    integrity_backend: PlTf002RuntimeIntegrityBackendV1 | None = None,
) -> PlTf002ReadOnlyGetSessionPreflightV1:
    """Preflight without credential load or network."""

    _assert_standing_pins_v1()
    bound_sha = _validate_owner_go_and_runtime_integrity_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        integrity_backend=integrity_backend,
    )
    for path in _f1_endpoint_paths_v1():
        _assert_get_only_surface_v1(endpoint_path=path, method="GET")
    _assert_get_only_surface_v1(endpoint_path=NE_TF_001_ENDPOINT_PATH, method="GET")
    return PlTf002ReadOnlyGetSessionPreflightV1(
        disposition="PREFLIGHT_PASS",
        wp_id=WP_ID,
        owner_go_accepted=TRUE_TOKEN,
        origin_main_sha_bound=bound_sha,
        authorized_host=AUTHORIZED_HOST,
        http_method_allowlist=METHOD_ALLOWLIST,
        f1_endpoint_paths=_f1_endpoint_paths_v1(),
        f2_endpoint_path=NE_TF_001_ENDPOINT_PATH,
        transport_class=TRANSPORT_CLASS,
        k1_may_perform_get_standing=FALSE_TOKEN,
        k1_real_keychain_access_standing=FALSE_TOKEN,
        ephemeral_keychain_consumer=EPHEMERAL_KEYCHAIN_CONSUMER,
        external_effect_authorized=FALSE_TOKEN,
        post_allowed_standing=FALSE_TOKEN,
        credential_class=REQUIRED_CREDENTIAL_CLASS,
        source_ref_uri=SOURCE_REF_URI,
        join_seam_id=JOIN_SEAM_ID,
    )


@contextmanager
def open_pl_tf_002_productive_read_only_get_session_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    acquire_credential: bool,
    backend: OsNativeStoreLookupBackendV1 | None = None,
    integrity_backend: PlTf002RuntimeIntegrityBackendV1 | None = None,
) -> Iterator[PlTf002ProductiveReadOnlyGetSessionV1]:
    """Ephemeral K1 bind + GET transport. Wipes opaque material and K1 handle on exit."""

    preflight = build_pl_tf_002_read_only_get_session_preflight_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        integrity_backend=integrity_backend,
    )
    if acquire_credential is not True:
        raise PlTf002ProductiveReadOnlySessionError("ACQUIRE_CREDENTIAL_REQUIRED_FOR_OPEN")

    adapter = FullCoreCheckoutIndependentFailClosedOsNativeStoreAdapterV1()
    handle = None
    session: PlTf002ProductiveReadOnlyGetSessionV1 | None = None
    try:
        with bounded_ephemeral_keychain_access_v1(consumer_id=EPHEMERAL_KEYCHAIN_CONSUMER):
            try:
                adapter.acquire_opaque_os_native_store_material_v1(
                    source_ref=SOURCE_REF_URI,
                    backend=backend,
                )
            except Exception as exc:
                raise PlTf002ProductiveReadOnlySessionError(
                    "K1_CREDENTIAL_ACQUISITION_FAIL_CLOSED"
                ) from exc
            opaque = borrow_held_opaque_bytes_for_bounded_parse_v1(holder_id=id(adapter))
            api_key, secret, phrase = parse_k1_keychain_utf8_json_material_v1(opaque)
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
            transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle)
            session = PlTf002ProductiveReadOnlyGetSessionV1(
                preflight=preflight,
                transport=transport,
                k1_handle_id=handle.handle_id,
                credential_acquired=True,
                network_executed_by_executor=False,
            )
            yield session
    finally:
        if handle is not None:
            release_k1_venue_auth_session_v1(handle)
        wipe_opaque_os_native_store_material_v1(id(adapter))
        if session is not None:
            session.transport = None  # type: ignore[misc]


def prove_pl_tf_002_session_does_not_authorize_post_v1() -> dict[str, str]:
    _assert_standing_pins_v1()
    return {
        "POST_ALLOWED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "K1_MAY_POST": FALSE_TOKEN,
        "TRANSPORT_FORBIDDEN_METHODS": ",".join(sorted(TRANSPORT_FORBIDDEN_METHODS)),
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
    }


def assert_host_is_authorized_eea_okx_v1(*, host: str) -> None:
    if str(host or "") != AUTHORIZED_HOST:
        raise PlTf002ProductiveReadOnlySessionError("HOST_NOT_EEA_OKX")


def public_session_proof_v1(proof: Mapping[str, Any]) -> dict[str, str]:
    """Strip to non-secret keys for logging/evidence envelopes."""

    allowed = {
        "disposition",
        "wp_id",
        "owner_go_accepted",
        "origin_main_sha_bound",
        "authorized_host",
        "transport_class",
        "join_seam_id",
        "credential_acquired",
        "network_executed_by_executor",
    }
    out: dict[str, str] = {}
    for key in allowed:
        if key in proof:
            out[key] = str(proof[key])
    blob = str(proof).lower()
    for forbidden in ("apikey", "secret", "passphrase", "api_key", "authorization"):
        if forbidden in blob:
            raise PlTf002ProductiveReadOnlySessionError("SECRET_LEAK_IN_PUBLIC_PROOF")
    return out
