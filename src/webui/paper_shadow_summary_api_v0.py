"""Paper/Shadow Summary API v0 — read-only GET for `paper_shadow_summary_readmodel_v0` (server-configured bundle only)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .paper_shadow_summary_readmodel_v0 import (
    SCHEMA_VERSION,
    build_paper_shadow_summary_readmodel_v0,
    to_json_dict,
)

_ENV_ENABLED = "PEAK_TRADE_PAPER_SHADOW_SUMMARY_ENABLED"
_ENV_BUNDLE_ROOT = "PEAK_TRADE_PAPER_SHADOW_SUMMARY_BUNDLE_ROOT"
_FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"

router = APIRouter(prefix="/api/observability", tags=["paper-shadow-summary-v0"])


def _generated_at_utc_iso() -> str:
    fixed = os.environ.get(_FIXED_GEN_ENV)
    if fixed:
        return fixed
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


def _diagnostic_envelope(
    *,
    runtime_source_status: Literal["disabled", "unconfigured"],
    warning_code: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _generated_at_utc_iso(),
        "source_kind": "disabled",
        "stale": True,
        "warnings": [warning_code],
        "errors": ["runtime_source_unavailable"],
        "runtime_source_status": runtime_source_status,
    }


@router.get("/paper-shadow-summary")
async def get_paper_shadow_summary() -> JSONResponse:
    if not _enabled_explicitly_on():
        return JSONResponse(
            status_code=503,
            content=_diagnostic_envelope(
                runtime_source_status="disabled",
                warning_code="paper_shadow_summary_source_disabled",
            ),
        )

    bundle_root = _resolved_bundle_root_or_none()
    if bundle_root is None:
        return JSONResponse(
            status_code=503,
            content=_diagnostic_envelope(
                runtime_source_status="unconfigured",
                warning_code="paper_shadow_summary_bundle_root_unconfigured",
            ),
        )

    try:
        model = build_paper_shadow_summary_readmodel_v0(bundle_root)
    except ValueError:
        return JSONResponse(
            status_code=503,
            content=_diagnostic_envelope(
                runtime_source_status="unconfigured",
                warning_code="paper_shadow_summary_bundle_root_unconfigured",
            ),
        )

    return JSONResponse(content=to_json_dict(model))
