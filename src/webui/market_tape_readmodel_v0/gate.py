"""Tape readmodel env gate resolution (default-off, fail-closed).

Shared by SSR display context on ``GET /market`` and future JSON routes.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .builder import (
    AUTHORITY_BOUNDARY,
    MarketTapeReadmodelError,
    READMODEL_ID,
    build_market_tape_readmodel_v0,
    to_json_dict,
)

ENV_ENABLED = "PEAK_TRADE_MARKET_TAPE_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT"
FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"


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
    path = Path(raw).expanduser()
    try:
        path = path.resolve(strict=True)
    except OSError:
        return None
    if not path.is_dir():
        return None
    return path


def _base_envelope(*, ga: str, runtime_source_status: str, stale_reason: str) -> dict[str, Any]:
    return {
        "readmodel_id": READMODEL_ID,
        "generated_at_iso": ga,
        "source": "unavailable",
        "runtime_source_status": runtime_source_status,
        "stale": True,
        "stale_reason": stale_reason,
        **AUTHORITY_BOUNDARY,
    }


def _disabled_envelope(*, ga: str) -> dict[str, Any]:
    envelope = _base_envelope(
        ga=ga,
        runtime_source_status="disabled",
        stale_reason="source_disabled",
    )
    envelope["warnings"] = ["market_tape_source_disabled"]
    envelope["errors"] = ["runtime_source_unavailable"]
    return envelope


def _unconfigured_envelope(*, ga: str) -> dict[str, Any]:
    envelope = _base_envelope(
        ga=ga,
        runtime_source_status="unconfigured",
        stale_reason="bundle_root_unconfigured",
    )
    envelope["warnings"] = ["market_tape_bundle_root_unconfigured"]
    envelope["errors"] = ["runtime_source_unavailable"]
    return envelope


def _builder_error_envelope(*, ga: str) -> dict[str, Any]:
    envelope = _base_envelope(
        ga=ga,
        runtime_source_status="builder_error",
        stale_reason="bundle_build_failed",
    )
    envelope["warnings"] = ["market_tape_bundle_build_failed"]
    envelope["errors"] = ["readmodel_build_failed"]
    return envelope


def resolve_market_tape_readmodel_payload_v0() -> tuple[int, dict[str, Any]]:
    """Return ``(status_code, body)`` for gated tape resolution (no FastAPI types)."""

    ga = generated_at_iso()
    if not enabled_explicitly_on():
        return 503, _disabled_envelope(ga=ga)

    bundle_root = resolved_bundle_root_or_none()
    if bundle_root is None:
        return 503, _unconfigured_envelope(ga=ga)

    try:
        readmodel = build_market_tape_readmodel_v0(
            bundle_root=bundle_root,
            generated_at_iso=ga,
        )
    except MarketTapeReadmodelError:
        return 503, _builder_error_envelope(ga=ga)

    return 200, to_json_dict(readmodel)


__all__ = [
    "ENV_BUNDLE_ROOT",
    "ENV_ENABLED",
    "FIXED_GEN_ENV",
    "enabled_explicitly_on",
    "generated_at_iso",
    "resolve_market_tape_readmodel_payload_v0",
    "resolved_bundle_root_or_none",
]
