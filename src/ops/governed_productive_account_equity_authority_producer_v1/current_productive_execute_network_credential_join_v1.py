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
) -> tuple[FullCoreFreshPretradeGetTransportV1 | None, str, Any]:
    """Bind read-only GET transport for execute_network=true.

    Returns (transport, credential_join_status, handle). credential_join_status is
    NOT_REACHED when join not attempted, CREDENTIAL_HANDLE_FAIL_CLOSED on fail-closed
    credential unavailability, or empty string when transport was constructed.
    """
    if execute_network is not True or fresh_get_transport is not None:
        return fresh_get_transport, "NOT_REACHED", None

    try:
        resolved_vault = (
            Path(str(vault_file))
            if vault_file is not None and str(vault_file).strip()
            else productive_fail_closed_credential_unavailable_v1(repo_root=repo_root)
        )
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


def release_productive_credential_handle_v1(handle: Any) -> None:
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
