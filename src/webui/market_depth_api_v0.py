"""Market Depth read-model API v0 — read-only GET for `market_depth_readmodel_v0` (server-configured bundle only)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .market_depth_readmodel_v0 import (
    MarketDepthReadmodelError,
    build_market_depth_readmodel_v0,
    to_json_dict,
)
from .market_depth_readmodel_v0.builder import READMODEL_ID

_ENV_ENABLED = "PEAK_TRADE_MARKET_DEPTH_ENABLED"
_ENV_BUNDLE_ROOT = "PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT"
_FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"

_NO_STORE = {"Cache-Control": "no-store"}

router = APIRouter(prefix="/api/market", tags=["market-depth-api-v0"])


def _generated_at_iso() -> str:
    fixed = os.environ.get(_FIXED_GEN_ENV)
    if fixed:
        return fixed.strip()
    return datetime.now(tz=timezone.utc).isoformat()


def _enabled_explicitly_on() -> bool:
    raw = os.environ.get(_ENV_ENABLED)
    return raw is not None and raw.strip() == "1"


def _resolved_bundle_root_or_none() -> Path | None:
    raw = os.environ.get(_ENV_BUNDLE_ROOT)
    if raw is None or not str(raw).strip():
        return None
    p = Path(raw).expanduser()
    try:
        p = p.resolve(strict=True)
    except OSError:
        return None
    if not p.is_dir():
        return None
    return p


def _disabled_envelope() -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": _generated_at_iso(),
        "source": "unavailable",
        "runtime_source_status": "disabled",
        "stale": True,
        "stale_reason": "source_disabled",
        "warnings": ["market_depth_source_disabled"],
        "errors": ["runtime_source_unavailable"],
    }


def _unconfigured_envelope() -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": _generated_at_iso(),
        "source": "unavailable",
        "runtime_source_status": "unconfigured",
        "stale": True,
        "stale_reason": "bundle_root_unconfigured",
        "warnings": ["market_depth_bundle_root_unconfigured"],
        "errors": ["runtime_source_unavailable"],
    }


def _builder_error_envelope() -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": _generated_at_iso(),
        "source": "unavailable",
        "runtime_source_status": "builder_error",
        "stale": True,
        "stale_reason": "bundle_build_failed",
        "warnings": ["market_depth_bundle_build_failed"],
        "errors": ["readmodel_build_failed"],
    }


@router.get("/depth")
async def get_market_depth() -> JSONResponse:
    if not _enabled_explicitly_on():
        return JSONResponse(
            status_code=503,
            content=_disabled_envelope(),
            headers=_NO_STORE,
        )

    bundle_root = _resolved_bundle_root_or_none()
    if bundle_root is None:
        return JSONResponse(
            status_code=503,
            content=_unconfigured_envelope(),
            headers=_NO_STORE,
        )

    try:
        readmodel = build_market_depth_readmodel_v0(
            bundle_root=bundle_root,
            generated_at_iso=_generated_at_iso(),
        )
    except MarketDepthReadmodelError:
        return JSONResponse(
            status_code=503,
            content=_builder_error_envelope(),
            headers=_NO_STORE,
        )

    return JSONResponse(
        content=to_json_dict(readmodel),
        headers=_NO_STORE,
    )


__all__ = ["router"]
