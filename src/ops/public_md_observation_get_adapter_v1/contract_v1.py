"""Thin GET-only observation seam for external UI consumers (e.g. OpenTerminalUI).

AUTHORITY=NONE — read-only durable O5 public-MD/OHLCV observation surfaces.
No mutation routes, no selection/risk/execution authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_derived_public_md_read_model_v1.constants_v1 import (
    CANONICAL_OHLCV_API,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_SCHEMA_NAME,
)
from src.ops.canonical_derived_public_md_read_model_v1.durable_read_model_store_v1 import (
    load_durable_read_model_v1,
)

OTUI_AUTHORITY = "NONE"
OTUI_MUTATION_ROUTES = 0
OTUI_PUBLIC_MD_SOURCE = "canonical_derived_public_md_read_model_v1.durable_read_model_store_v1"
OTUI_OHLCV_GET_ROUTE = CANONICAL_OHLCV_API


def load_public_md_observation_snapshot_v1(
    *,
    archive_root: str | Path,
) -> Mapping[str, Any] | None:
    """GET-only helper: load persisted canonical_market_dashboard_read_model.v1 if present."""
    from pathlib import Path as _Path

    return load_durable_read_model_v1(_Path(archive_root))


def observation_get_contract_v1() -> dict[str, Any]:
    return {
        "authority": OTUI_AUTHORITY,
        "mutation_routes": OTUI_MUTATION_ROUTES,
        "read_model_schema": READ_MODEL_SCHEMA_NAME,
        "read_model_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
        "ohlcv_get_route": OTUI_OHLCV_GET_ROUTE,
        "public_md_source": OTUI_PUBLIC_MD_SOURCE,
    }
