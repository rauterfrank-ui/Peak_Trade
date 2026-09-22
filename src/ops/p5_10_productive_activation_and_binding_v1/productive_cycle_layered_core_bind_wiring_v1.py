"""Explicit productive-cycle kwargs for layered-core bind (store + scope carrier gate)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_SCHEMA_NAME,
    CURSOR_SCHEMA_VERSION,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)

LAYERED_CORE_STORE_ROOT_COLOCATED_WITH_CURSOR_OWNER = "ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1"


def incoming_cursor_has_existing_scope_carrier_v1(incoming_cursor: object | None) -> bool:
    """True when a restored/in-memory cursor already carries CanonicalScopeSnapshot."""
    if incoming_cursor is None:
        return False
    existing = getattr(incoming_cursor, "existing_scope", None)
    if existing is not None:
        return True
    if isinstance(incoming_cursor, Mapping):
        if incoming_cursor.get("schema_name") != CURSOR_SCHEMA_NAME:
            return False
        if incoming_cursor.get("schema_version") != CURSOR_SCHEMA_VERSION:
            return False
        raw = incoming_cursor.get("existing_scope")
        return raw is not None
    return False


def productive_layered_core_bind_cycle_kwargs_v1(
    *,
    layered_core_store_root: Path | str | None,
    incoming_cursor: object | None = None,
) -> dict[str, object]:
    """Return explicit cycle kwargs for layered bind, or {} to stay on legacy I-1..I-3 path.

    Bind is not requested on bootstrap/first-cycle (no scope carrier) or when the store
    root is absent. Same store root as the productive sidestate confirmation cursor.
    """
    if not PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED:
        return {}
    if layered_core_store_root is None:
        return {}
    if not incoming_cursor_has_existing_scope_carrier_v1(incoming_cursor):
        return {}
    root = Path(layered_core_store_root)
    if not str(root).strip():
        return {}
    return {
        "productive_layered_core_bind_requested": True,
        "layered_core_store_root": root,
    }


__all__ = [
    "LAYERED_CORE_STORE_ROOT_COLOCATED_WITH_CURSOR_OWNER",
    "incoming_cursor_has_existing_scope_carrier_v1",
    "productive_layered_core_bind_cycle_kwargs_v1",
]
