"""CURRENT productive execute_network read-only credential join (EEA/CZ authority).

Single fail-closed credential slot for productive FullCoreProductiveReadOnlyGetTransportV1
construction. Default loader binds §11.13.5 SecretRef vault + K1 READ session (#FC-01).

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_pl_tf_002_read_join_v1 import (
    ProductivePlTf002ReadSessionBorrowV1,
    release_pl_tf_002_read_session_borrow_v1,
    try_bind_pl_tf_002_read_transport_for_execute_network_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_execute_network_read_credential_loader_v1 import (
    productive_execute_network_read_credential_loader_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
)

CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS = "CREDENTIAL_HANDLE_FAIL_CLOSED"


def productive_fail_closed_credential_unavailable_v1(*_a: Any, **_k: Any) -> Any:
    """Productive credential loader slot; fail-closed unless vault + SecretRef bind succeeds."""
    return productive_execute_network_read_credential_loader_v1(*_a, **_k)


def bind_productive_read_only_get_transport_for_execute_network_v1(
    *,
    execute_network: bool,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None,
    vault_file: Path | str | None,
    repo_root: Path,
    origin_main_sha: str | None = None,
) -> tuple[FullCoreFreshPretradeGetTransportV1 | None, str, Any]:
    """Bind read-only GET transport for execute_network=true.

    Returns (transport, credential_join_status, handle). credential_join_status is
    NOT_REACHED when join not attempted, CREDENTIAL_HANDLE_FAIL_CLOSED on fail-closed
    credential unavailability, or empty string when transport was constructed.
    """
    if execute_network is not True or fresh_get_transport is not None:
        return fresh_get_transport, "NOT_REACHED", None

    if vault_file is not None and str(vault_file).strip():
        try:
            resolved_vault = Path(str(vault_file))
            backend = productive_fail_closed_credential_unavailable_v1(vault_file=resolved_vault)
            handle = productive_fail_closed_credential_unavailable_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
        except RuntimeError:
            return None, CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS, None
        transport = FullCoreProductiveReadOnlyGetTransportV1(handle=handle)
        return transport, "", handle

    pltf_transport, pltf_borrow = try_bind_pl_tf_002_read_transport_for_execute_network_v1(
        origin_main_sha=str(origin_main_sha or ""),
        repo_root=repo_root,
    )
    if pltf_transport is not None and pltf_borrow is not None:
        return pltf_transport, "", pltf_borrow

    try:
        productive_fail_closed_credential_unavailable_v1(repo_root=repo_root)
    except RuntimeError:
        return None, CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS, None
    return None, CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS, None


def release_productive_credential_handle_v1(handle: Any) -> None:
    if isinstance(handle, ProductivePlTf002ReadSessionBorrowV1):
        release_pl_tf_002_read_session_borrow_v1(handle)
        return
    if handle is not None:
        productive_fail_closed_credential_unavailable_v1(handle=handle)


__all__ = [
    "CREDENTIAL_HANDLE_FAIL_CLOSED_STATUS",
    "REQUIRED_CREDENTIAL_CLASS",
    "REQUIRED_SECRETREF_URI",
    "bind_productive_read_only_get_transport_for_execute_network_v1",
    "productive_fail_closed_credential_unavailable_v1",
    "release_productive_credential_handle_v1",
]
