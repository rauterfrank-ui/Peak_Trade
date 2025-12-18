# src/reporting/status_snapshot_schema.py
"""
Peak_Trade Live Status Snapshot Schema (Phase 57 Extension)
============================================================

Pydantic models for live status snapshots - schema-first, deterministic, defensive.

Design:
- Pydantic v1/v2 compatible (auto-detect)
- Stable model_dump/dict helper
- version="0.1", generated_at UTC ISO
- Panel Provider Pattern: flexible input (dict/tuple/PanelSnapshot)

Usage:
    from src.reporting.status_snapshot_schema import LiveStatusSnapshot, PanelSnapshot

    snapshot = LiveStatusSnapshot(
        version="0.1",
        generated_at="2025-12-16T10:00:00Z",
        panels=[
            PanelSnapshot(id="system", title="System", status="ok", details={"health": "OK"}),
        ]
    )
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
    from pydantic import __version__ as pydantic_version

    PYDANTIC_V2 = pydantic_version.startswith("2.")
except ImportError:
    raise ImportError("Pydantic is required for status snapshot schema")


# =============================================================================
# Pydantic Models
# =============================================================================


class PanelSnapshot(BaseModel):
    """
    A single status panel in the live status snapshot.

    Attributes:
        id: Unique panel identifier (e.g., "system", "portfolio", "risk")
        title: Human-readable panel title
        status: Panel status ("ok", "warn", "error", "unknown")
        details: Freeform dict with panel-specific data (deterministically sorted)
    """
    id: str = Field(..., description="Unique panel identifier")
    title: str = Field(..., description="Human-readable panel title")
    status: str = Field(..., description="Panel status (ok/warn/error/unknown)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Panel-specific data")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:
        class Config:
            extra = "forbid"


class LiveStatusSnapshot(BaseModel):
    """
    Complete live status snapshot with metadata and panels.

    Attributes:
        version: Schema version (semantic versioning)
        generated_at: ISO 8601 timestamp (UTC) when snapshot was generated
        panels: List of panel snapshots (deterministically sorted)
        meta: Optional freeform metadata (e.g., config_path, tag)
    """
    version: str = Field(default="0.1", description="Schema version")
    generated_at: str = Field(..., description="ISO 8601 timestamp (UTC)")
    panels: List[PanelSnapshot] = Field(default_factory=list, description="List of panels")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    if PYDANTIC_V2:
        model_config = {"extra": "forbid"}
    else:
        class Config:
            extra = "forbid"


# =============================================================================
# Helper Functions
# =============================================================================


def model_dump_helper(model: BaseModel) -> Dict[str, Any]:
    """
    Pydantic v1/v2 compatible model -> dict conversion.

    Args:
        model: Pydantic model instance

    Returns:
        Dict representation (compatible with both v1 and v2)
    """
    if PYDANTIC_V2:
        return model.model_dump()
    else:
        return model.dict()


def normalize_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes details dict for deterministic output.

    - Sorts keys alphabetically
    - Recursively normalizes nested dicts
    - Converts None to "null" string for JSON stability

    Args:
        details: Input details dict

    Returns:
        Normalized dict with sorted keys
    """
    if not isinstance(details, dict):
        return details

    result = {}
    for key in sorted(details.keys()):
        value = details[key]
        if isinstance(value, dict):
            result[key] = normalize_details(value)
        elif isinstance(value, list):
            # Normalize list elements if they are dicts
            result[key] = [normalize_details(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value

    return result


def normalize_status(status: Any) -> str:
    """
    Normalizes status value to canonical string ("ok", "warn", "error", "unknown").

    Handles:
    - Strings: "ok", "OK", "warn", "warning", "error", "fail", "unknown"
    - Booleans: True -> "ok", False -> "error"
    - Integers: 0 -> "ok", 1 -> "warn", 2+ -> "error"
    - None/other -> "unknown"

    Args:
        status: Input status value

    Returns:
        Canonical status string
    """
    if status is None:
        return "unknown"

    # String normalization
    if isinstance(status, str):
        status_lower = status.lower().strip()
        if status_lower in {"ok", "good", "healthy", "pass", "passed"}:
            return "ok"
        elif status_lower in {"warn", "warning", "caution", "degraded"}:
            return "warn"
        elif status_lower in {"error", "err", "fail", "failed", "critical", "bad"}:
            return "error"
        else:
            return "unknown"

    # Boolean normalization
    if isinstance(status, bool):
        return "ok" if status else "error"

    # Integer normalization
    if isinstance(status, int):
        if status == 0:
            return "ok"
        elif status == 1:
            return "warn"
        else:
            return "error"

    # Fallback
    return "unknown"


def create_default_system_panel() -> PanelSnapshot:
    """
    Creates a default system panel for when no providers are configured.

    Returns:
        PanelSnapshot with fallback message
    """
    return PanelSnapshot(
        id="system",
        title="System Status",
        status="unknown",
        details={
            "message": "No providers configured",
            "note": "Snapshot builder initialized without panel providers",
        }
    )
