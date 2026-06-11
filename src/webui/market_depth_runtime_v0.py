"""Market Depth runtime resolution (env + offline bundle builder), shared by HTTP and future SSR."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .market_depth_readmodel_v0 import (
    MarketDepthReadmodelError,
    build_market_depth_readmodel_v0,
    to_json_dict,
)
from .market_depth_readmodel_v0.builder import READMODEL_ID

ENV_ENABLED = "PEAK_TRADE_MARKET_DEPTH_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT"
ENV_CHART_ENABLED = "PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED"
FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"


def depth_chart_enabled_explicitly_on() -> bool:
    raw = os.environ.get(ENV_CHART_ENABLED)
    return raw is not None and raw.strip() == "1"


def generated_at_iso() -> str:
    fixed = os.environ.get(FIXED_GEN_ENV)
    if fixed:
        return fixed.strip()
    return datetime.now(tz=timezone.utc).isoformat()


def enabled_explicitly_on() -> bool:
    raw = os.environ.get(ENV_ENABLED)
    return raw is not None and raw.strip() == "1"


def resolved_bundle_root_or_none() -> Path | None:
    raw = os.environ.get(ENV_BUNDLE_ROOT)
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


def _disabled_envelope(*, ga: str) -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": ga,
        "source": "unavailable",
        "runtime_source_status": "disabled",
        "stale": True,
        "stale_reason": "source_disabled",
        "warnings": ["market_depth_source_disabled"],
        "errors": ["runtime_source_unavailable"],
    }


def _unconfigured_envelope(*, ga: str) -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": ga,
        "source": "unavailable",
        "runtime_source_status": "unconfigured",
        "stale": True,
        "stale_reason": "bundle_root_unconfigured",
        "warnings": ["market_depth_bundle_root_unconfigured"],
        "errors": ["runtime_source_unavailable"],
    }


def _builder_error_envelope(*, ga: str) -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": ga,
        "source": "unavailable",
        "runtime_source_status": "builder_error",
        "stale": True,
        "stale_reason": "bundle_build_failed",
        "warnings": ["market_depth_bundle_build_failed"],
        "errors": ["readmodel_build_failed"],
    }


def market_depth_json_payload_v0() -> tuple[int, dict[str, Any]]:
    """Return ``(status_code, body)`` mirroring ``GET`` ``/api/market/depth`` (no FastAPI types)."""

    ga = generated_at_iso()
    if not enabled_explicitly_on():
        return 503, _disabled_envelope(ga=ga)

    bundle_root = resolved_bundle_root_or_none()
    if bundle_root is None:
        return 503, _unconfigured_envelope(ga=ga)

    try:
        readmodel = build_market_depth_readmodel_v0(
            bundle_root=bundle_root,
            generated_at_iso=ga,
        )
    except MarketDepthReadmodelError:
        return 503, _builder_error_envelope(ga=ga)

    return 200, to_json_dict(readmodel)


__all__ = [
    "ENV_BUNDLE_ROOT",
    "ENV_CHART_ENABLED",
    "ENV_ENABLED",
    "FIXED_GEN_ENV",
    "depth_chart_enabled_explicitly_on",
    "enabled_explicitly_on",
    "generated_at_iso",
    "market_depth_json_payload_v0",
    "resolved_bundle_root_or_none",
]
