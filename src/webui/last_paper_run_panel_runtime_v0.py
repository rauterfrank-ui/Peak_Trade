"""SSR display context for Last Paper Run panel (env-gated, read-only)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .last_paper_run_panel_readmodel_v0 import (
    build_last_paper_run_panel_readmodel_v0,
    to_json_dict,
)

logger = logging.getLogger(__name__)

ENV_ENABLED = "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT"


def _panel_enabled() -> bool:
    return (os.getenv(ENV_ENABLED) or "").strip() == "1"


def _resolved_bundle_root() -> Path | None:
    raw = (os.getenv(ENV_BUNDLE_ROOT) or "").strip()
    if not raw:
        return None
    p = Path(raw).expanduser()
    try:
        p = p.resolve(strict=True)
    except OSError:
        return None
    if not p.is_dir():
        return None
    return p


def build_last_paper_run_panel_display_context() -> dict[str, Any]:
    """Fail-soft SSR context for GET /observability (default off)."""

    base: dict[str, Any] = {
        "section_visible": False,
        "gate_enabled": False,
        "display_status": "disabled",
        "readmodel": None,
        "error": None,
    }

    if not _panel_enabled():
        return base

    base["gate_enabled"] = True
    bundle_root = _resolved_bundle_root()
    if bundle_root is None:
        base["display_status"] = "unconfigured"
        return base

    try:
        model = build_last_paper_run_panel_readmodel_v0(bundle_root)
        base["section_visible"] = True
        base["display_status"] = model.load_status
        base["readmodel"] = to_json_dict(model)
        return base
    except ValueError as e:
        logger.warning("Last paper run panel bundle load failed: %s", e)
        base["section_visible"] = True
        base["display_status"] = "error"
        base["error"] = type(e).__name__
        return base
    except Exception as e:
        logger.warning("Last paper run panel unexpected error: %s", e)
        base["section_visible"] = True
        base["display_status"] = "error"
        base["error"] = type(e).__name__
        return base
