"""Market Ranking Funnel runtime resolution (env + offline bundle), SSR-only."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .market_ranking_funnel_readmodel_v0 import (
    MarketRankingFunnelReadmodelError,
    build_market_ranking_funnel_readmodel,
)
from .market_ranking_funnel_readmodel_v0.builder import READMODEL_ID

ENV_ENABLED = "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT"

STAGE_DISPLAY_LABELS: dict[str, str] = {
    "universe": "Top Universe",
    "shortlist": "Shortlist",
    "selected": "Top Ranking / Selected Candidates",
}


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


def _base_context(*, gate_enabled: bool, display_status: str) -> dict[str, Any]:
    return {
        "gate_enabled": gate_enabled,
        "display_status": display_status,
        "readmodel_id": READMODEL_ID,
        "has_rows": False,
        "non_authorizing": True,
        "stale": True,
        "stale_reason": "",
        "source": "",
        "generated_at_iso": "",
        "summary_line": "",
        "stage_counts": {"universe": 0, "shortlist": 0, "selected": 0},
        "stages": {"universe": [], "shortlist": [], "selected": []},
        "stage_labels": dict(STAGE_DISPLAY_LABELS),
    }


def build_market_ranking_funnel_display_context() -> dict[str, Any]:
    """SSR-only ranking funnel panel context for GET /market (fail closed by default)."""
    if not enabled_explicitly_on():
        ctx = _base_context(gate_enabled=False, display_status="disabled")
        ctx["summary_line"] = "Ranking funnel producer disabled (env gate off)."
        ctx["stale_reason"] = "source_disabled"
        return ctx

    bundle_root = resolved_bundle_root_or_none()
    if bundle_root is None:
        ctx = _base_context(gate_enabled=True, display_status="unconfigured")
        ctx["summary_line"] = "Ranking funnel bundle root unconfigured."
        ctx["stale_reason"] = "bundle_root_unconfigured"
        return ctx

    try:
        readmodel = build_market_ranking_funnel_readmodel(bundle_root)
    except MarketRankingFunnelReadmodelError:
        ctx = _base_context(gate_enabled=True, display_status="builder_error")
        ctx["summary_line"] = "Ranking funnel bundle could not be loaded (read-only empty display)."
        ctx["stale_reason"] = "bundle_build_failed"
        return ctx

    stages = readmodel.get("stages") or {}
    stage_counts = readmodel.get("stage_counts") or {
        stage: len(stages.get(stage) or []) for stage in STAGE_DISPLAY_LABELS
    }
    has_rows = any(int(stage_counts.get(stage, 0)) > 0 for stage in STAGE_DISPLAY_LABELS)

    if has_rows:
        display_status = "ready"
        summary_line = (
            f"{readmodel.get('source', '')} — "
            f"universe {stage_counts.get('universe', 0)}, "
            f"shortlist {stage_counts.get('shortlist', 0)}, "
            f"selected {stage_counts.get('selected', 0)} "
            "(offline bundle, read-only display)"
        )
    else:
        display_status = "empty"
        summary_line = "Ranking funnel enabled but no stage rows in bundle (display-only empty)."

    return {
        "gate_enabled": True,
        "display_status": display_status,
        "readmodel_id": str(readmodel.get("readmodel_id", READMODEL_ID)),
        "has_rows": has_rows,
        "non_authorizing": bool(readmodel.get("non_authorizing") is True),
        "stale": bool(readmodel.get("stale") is True),
        "stale_reason": str(readmodel.get("stale_reason") or ""),
        "source": str(readmodel.get("source", "")),
        "generated_at_iso": str(readmodel.get("generated_at_iso", "")),
        "summary_line": summary_line.strip(),
        "stage_counts": stage_counts,
        "stages": {stage: list(stages.get(stage) or []) for stage in STAGE_DISPLAY_LABELS},
        "stage_labels": dict(STAGE_DISPLAY_LABELS),
    }


__all__ = [
    "ENV_BUNDLE_ROOT",
    "ENV_ENABLED",
    "STAGE_DISPLAY_LABELS",
    "build_market_ranking_funnel_display_context",
    "enabled_explicitly_on",
    "resolved_bundle_root_or_none",
]
