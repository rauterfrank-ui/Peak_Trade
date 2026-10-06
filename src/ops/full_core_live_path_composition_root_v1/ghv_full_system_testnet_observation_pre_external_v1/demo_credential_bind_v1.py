"""Demo credential slot bind for GHV Testnet Observation GET-only Fresh-Pretrade."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    CREDENTIAL_PURPOSE,
    DEMO_SECRET_REFERENCE,
    LIVE_K1_REUSE,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_okx_venue_auth_headers_v1 import (
    FullCoreDemoBoundVenueAuthHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_read_only_get_transport_v1 import (
    GhvDemoReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.demo_vault_credential_loader_v1 import (
    GhvTestnetDemoSecretrefVaultLoaderError,
    load_ghv_testnet_demo_credential_handle_for_bind_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.governance_v1 import (
    assert_full_system_testnet_observation_owner_go_v1,
    prove_standing_fail_closed_pins_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS as LIVE_K1_REQUIRED_CREDENTIAL_CLASS,
)

JOIN_SEAM_ID = "GHV_FULL_SYSTEM_TESTNET_OBSERVATION_DEMO_CREDENTIAL_GET_ONLY_BIND_V1"


class GhvTestnetDemoCredentialBindError(RuntimeError):
    """Fail-closed Demo credential bind violation."""


def assert_demo_credential_class_v1(credential_class: str) -> None:
    cc = str(credential_class or "")
    if cc == LIVE_K1_REQUIRED_CREDENTIAL_CLASS:
        raise GhvTestnetDemoCredentialBindError("LIVE_CREDENTIAL_IN_DEMO_BIND_REJECTED")
    if cc != CREDENTIAL_CLASS:
        raise GhvTestnetDemoCredentialBindError("DEMO_CREDENTIAL_CLASS_REJECTED")


def assert_live_k1_credential_class_v1(credential_class: str) -> None:
    if str(credential_class or "") == CREDENTIAL_CLASS:
        raise GhvTestnetDemoCredentialBindError("DEMO_CREDENTIAL_IN_LIVE_BIND_REJECTED")


def prove_credential_isolation_v1() -> dict[str, str]:
    return {
        "LIVE_K1_DEMO_HEADER_ALLOWED": "false",
        "DEMO_CREDENTIAL_LIVE_K1_REUSE_ALLOWED": "false" if LIVE_K1_REUSE is False else "true",
        "LIVE_CREDENTIAL_DEMO_REUSE_ALLOWED": "false",
        "CREDENTIAL_CLASS": CREDENTIAL_CLASS,
        "CREDENTIAL_PURPOSE": CREDENTIAL_PURPOSE,
        "DEMO_SECRET_REFERENCE": DEMO_SECRET_REFERENCE,
        "LIVE_K1_REQUIRED_CREDENTIAL_CLASS": LIVE_K1_REQUIRED_CREDENTIAL_CLASS,
    }


def fail_closed_demo_credential_loader_v1(
    *_a: object, **_k: object
) -> FullCoreDemoBoundVenueAuthHandleV1:
    """Explicit fail-closed slot when auto SecretRef resolution must not run."""

    raise GhvTestnetDemoCredentialBindError("DEMO_CREDENTIAL_BIND_FAIL_CLOSED")


def _default_demo_credential_loader_v1() -> FullCoreDemoBoundVenueAuthHandleV1:
    try:
        return load_ghv_testnet_demo_credential_handle_for_bind_v1()
    except GhvTestnetDemoSecretrefVaultLoaderError as exc:
        raise GhvTestnetDemoCredentialBindError(str(exc)) from exc


@contextmanager
def open_ghv_testnet_demo_get_only_fresh_pretrade_transport_v1(
    *,
    owner_go: str,
    max_request_count: int,
    demo_handle: FullCoreDemoBoundVenueAuthHandleV1 | None = None,
    credential_loader: object = _default_demo_credential_loader_v1,
) -> Iterator[tuple[GhvDemoReadOnlyGetTransportV1, dict[str, str]]]:
    governance = assert_full_system_testnet_observation_owner_go_v1(owner_go)
    prove_standing_fail_closed_pins_v1()
    if int(max_request_count) <= 0:
        raise GhvTestnetDemoCredentialBindError("MAX_REQUEST_COUNT_INVALID")

    handle = demo_handle
    if handle is None:
        loaded = credential_loader()  # type: ignore[operator]
        if isinstance(loaded, FullCoreK1BoundVenueAuthHandleV1):
            raise GhvTestnetDemoCredentialBindError("LIVE_K1_HANDLE_IN_DEMO_BIND_REJECTED")
        if not isinstance(loaded, FullCoreDemoBoundVenueAuthHandleV1):
            raise GhvTestnetDemoCredentialBindError("DEMO_HANDLE_TYPE_FORBIDDEN")
        handle = loaded
    if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        raise GhvTestnetDemoCredentialBindError("LIVE_K1_HANDLE_IN_DEMO_BIND_REJECTED")
    assert_demo_credential_class_v1(handle.credential_class)

    transport = GhvDemoReadOnlyGetTransportV1(
        handle=handle, max_request_count=int(max_request_count)
    )
    bind_proof = {
        **governance,
        **prove_credential_isolation_v1(),
        "JOIN_SEAM_ID": JOIN_SEAM_ID,
        "TARGET_TRANSPORT": "GhvDemoReadOnlyGetTransportV1",
        "CREDENTIAL_HANDLE_TYPE": "FullCoreDemoBoundVenueAuthHandleV1",
        "CREDENTIAL_HANDLE_PRESENT": "true",
        "LIVE_K1_REUSE": "false",
        "READY_TO_EXECUTE_TESTNET_OBSERVATION": "false",
    }
    yield transport, bind_proof
