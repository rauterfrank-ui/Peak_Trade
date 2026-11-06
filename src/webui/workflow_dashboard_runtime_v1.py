"""SSR display context for Workflow Dashboard V1 (env-gated, read-only)."""

from __future__ import annotations

import logging
import os
from typing import Any

from .workflow_dashboard_archive_root_v1 import (
    ENV_ARCHIVE_ROOT,
    resolve_workflow_dashboard_archive_root,
)
from .workflow_dashboard_readmodel_v1 import build_workflow_dashboard_readmodel_v1, to_json_dict

logger = logging.getLogger(__name__)

ENV_ENABLED = "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED"


def _dashboard_enabled() -> bool:
    return (os.getenv(ENV_ENABLED) or "").strip() == "1"


def _resolved_archive_root():
    # Shared contract owner: explicit N/A here; Env override; then canonical default.
    # require_existing_directory=True preserves unconfigured semantics when the
    # default path has not been created by an explicit writer.
    return resolve_workflow_dashboard_archive_root(require_existing_directory=True)


def build_workflow_dashboard_display_context() -> dict[str, Any]:
    """Fail-soft SSR context for GET /observability (default off)."""

    base: dict[str, Any] = {
        "section_visible": False,
        "gate_enabled": False,
        "display_status": "disabled",
        "readmodel": None,
        "error": None,
    }

    if not _dashboard_enabled():
        return base

    base["gate_enabled"] = True
    archive_root = _resolved_archive_root()
    if archive_root is None:
        base["display_status"] = "unconfigured"
        return base

    try:
        model = build_workflow_dashboard_readmodel_v1(archive_root)
        base["section_visible"] = True
        base["display_status"] = model.load_status
        base["readmodel"] = to_json_dict(model)
        return base
    except ValueError as e:
        logger.warning("Workflow dashboard archive load failed: %s", e)
        base["section_visible"] = True
        base["display_status"] = "error"
        base["error"] = type(e).__name__
        return base
    except Exception as e:
        logger.warning("Workflow dashboard unexpected error: %s", e)
        base["section_visible"] = True
        base["display_status"] = "error"
        base["error"] = type(e).__name__
        return base
