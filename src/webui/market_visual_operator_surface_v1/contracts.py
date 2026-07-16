"""Shared contracts for the market visual operator surface v1.

Defines activity-state vocabulary, environment variable names, and fail-closed helpers
for resolving offline evidence roots and parsing JSON. Nothing here reads request-time
market data or carries any runtime/order authority.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ENV_EVIDENCE_ROOT = "PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT"
ENV_LINEAR_DIAGNOSTICS_ROOT = "PEAK_TRADE_MARKET_LINEAR_DIAGNOSTICS_BUNDLE_ROOT"

ECONOMIC_EVIDENCE_BINDING_FILENAME = "economic_evidence_binding.json"


class ActivityState:
    """Canonical activity states for the visual operator surface.

    ``ACTIVE`` is intentionally distinct from ``AVAILABLE_NOT_RUN``: it is only reported
    when concrete processing evidence is present (see ``compute_ai_activity_state``).
    """

    NOT_AVAILABLE = "NOT_AVAILABLE"
    AVAILABLE_NOT_RUN = "AVAILABLE_NOT_RUN"
    PROCESSED = "PROCESSED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    FAILED = "FAILED"


ACTIVITY_STATES: tuple[str, ...] = (
    ActivityState.NOT_AVAILABLE,
    ActivityState.AVAILABLE_NOT_RUN,
    ActivityState.PROCESSED,
    ActivityState.ACTIVE,
    ActivityState.BLOCKED,
    ActivityState.STALE,
    ActivityState.FAILED,
)


def resolved_dir_or_none(env_name: str) -> Path | None:
    """Resolve an env-provided directory to an existing path, fail-closed otherwise."""
    raw = os.environ.get(env_name)
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


def load_json_or_none(path: Path) -> Any | None:
    """Fail-closed JSON load; returns ``None`` on any read/parse error."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_economic_evidence_dir(evidence_root: Path) -> tuple[Path, str | None]:
    """Resolve the concrete economic evidence dir from an evidence root.

    The evidence root may either contain an ``economic_evidence_binding.json`` pointer
    (materialized bundle) or be the PR5242 evidence dir itself. Returns the resolved
    directory and an optional binding file path (as a string) when a pointer was used.
    """
    binding_path = evidence_root / ECONOMIC_EVIDENCE_BINDING_FILENAME
    binding = load_json_or_none(binding_path)
    if isinstance(binding, dict):
        pointed = str(binding.get("economic_evidence_dir") or "").strip()
        if pointed:
            candidate = Path(pointed).expanduser()
            if candidate.is_dir():
                return candidate, str(binding_path)
    return evidence_root, None


def compute_ai_activity_state(
    *,
    funnel_loaded: bool,
    funnel_failed: bool,
    evidence_root_set: bool,
    trade_count_computed: bool,
    bar_count: int | None,
    zero_trade_degeneration_explicit: bool,
) -> str:
    """Compute the AI activity state.

    ``ACTIVE`` requires concrete processing evidence: either a computed trade count, or a
    positive bar count paired with an explicit zero-trade-degeneration flag. This keeps
    ``AVAILABLE_NOT_RUN`` (evidence configured but not processed) distinct from ``ACTIVE``.
    """
    if not evidence_root_set:
        return ActivityState.NOT_AVAILABLE
    if funnel_failed:
        return ActivityState.FAILED
    if not funnel_loaded:
        return ActivityState.AVAILABLE_NOT_RUN
    has_processing_evidence = trade_count_computed or (
        bar_count is not None and bar_count > 0 and zero_trade_degeneration_explicit
    )
    if has_processing_evidence:
        return ActivityState.ACTIVE
    return ActivityState.AVAILABLE_NOT_RUN


__all__ = [
    "ACTIVITY_STATES",
    "ECONOMIC_EVIDENCE_BINDING_FILENAME",
    "ENV_EVIDENCE_ROOT",
    "ENV_LINEAR_DIAGNOSTICS_ROOT",
    "ActivityState",
    "compute_ai_activity_state",
    "load_json_or_none",
    "resolve_economic_evidence_dir",
    "resolved_dir_or_none",
]
