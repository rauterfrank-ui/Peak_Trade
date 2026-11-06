# src/reporting/live_status_snapshot_builder.py
"""
Peak_Trade Live Status Snapshot Builder (Phase 57 Extension)
=============================================================

Builder function for live status snapshots using Panel Provider Pattern.

Design:
- Defensive: graceful degradation per panel (try/except)
- Deterministic: sorted panels, normalized details
- Additiv: no hard dependencies, best-effort imports
- Flexible: Providers can return dict/tuple/PanelSnapshot

Usage:
    from src.reporting.live_status_snapshot_builder import build_live_status_snapshot

    # With custom providers
    def get_system_panel():
        return {"id": "system", "title": "System", "status": "ok", "details": {"health": "OK"}}

    snapshot = build_live_status_snapshot(
        panel_providers={"system": get_system_panel},
        meta={"config_path": "config/config.toml", "tag": "daily"}
    )

    # Without providers (fallback)
    snapshot = build_live_status_snapshot()  # Returns default system panel
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple, Union

from .status_snapshot_schema import (
    LiveStatusSnapshot,
    PanelSnapshot,
    create_default_system_panel,
    model_dump_helper,
    normalize_details,
    normalize_status,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Panel Provider Type Aliases
# =============================================================================

# Provider can return:
# - PanelSnapshot instance
# - dict with {id, title, status, details}
# - tuple (status, title, details) - id inferred from provider key
PanelProviderReturn = Union[PanelSnapshot, Dict[str, Any], Tuple[str, str, Dict[str, Any]]]
PanelProvider = Callable[[], PanelProviderReturn]


# =============================================================================
# Builder Function
# =============================================================================


def build_live_status_snapshot(
    panel_providers: Optional[Dict[str, PanelProvider]] = None,
    *,
    meta: Optional[Dict[str, Any]] = None,
) -> LiveStatusSnapshot:
    """
    Builds a live status snapshot from panel providers.

    Defensive Implementation:
    - Each provider is wrapped in try/except
    - Provider failures result in error panel (no exception propagation)
    - No providers -> fallback to default system panel

    Deterministic:
    - Panels sorted by panel.id
    - Details keys sorted
    - Generated timestamp in UTC ISO format

    Args:
        panel_providers: Dict of {panel_id: provider_callable}
                        Provider returns dict/tuple/PanelSnapshot
        meta: Optional metadata dict (e.g., config_path, tag)

    Returns:
        LiveStatusSnapshot with panels and metadata
    """
    # Generate timestamp (UTC ISO)
    generated_at = datetime.now(timezone.utc).isoformat()

    # Normalize meta
    normalized_meta = normalize_details(meta or {})

    # No providers -> fallback
    if not panel_providers:
        logger.debug("No panel providers configured, using default system panel")
        return LiveStatusSnapshot(
            version="0.1",
            generated_at=generated_at,
            panels=[create_default_system_panel()],
            meta=normalized_meta,
        )

    # Collect panels
    panels: list[PanelSnapshot] = []

    for panel_id, provider in panel_providers.items():
        try:
            panel = _invoke_provider_safely(panel_id, provider)
            panels.append(panel)
        except Exception as exc:
            # Defensive: provider failed -> create error panel
            logger.warning(f"Panel provider '{panel_id}' failed: {exc}")
            error_panel = PanelSnapshot(
                id=panel_id,
                title=f"Panel: {panel_id} (Error)",
                status="error",
                details={
                    "error": f"{type(exc).__name__}: {str(exc)}",
                    "note": "Provider failed during invocation",
                },
            )
            panels.append(error_panel)

    # Sort panels by id for determinism
    panels.sort(key=lambda p: p.id)

    # Normalize all panel details
    for panel in panels:
        panel.details = normalize_details(panel.details)

    return LiveStatusSnapshot(
        version="0.1",
        generated_at=generated_at,
        panels=panels,
        meta=normalized_meta,
    )


def _invoke_provider_safely(panel_id: str, provider: PanelProvider) -> PanelSnapshot:
    """
    Invokes a panel provider and converts result to PanelSnapshot.

    Handles multiple return formats:
    - PanelSnapshot: pass through
    - dict: convert to PanelSnapshot
    - tuple (status, title, details): convert with panel_id

    Args:
        panel_id: Panel identifier (used as fallback if not in result)
        provider: Provider callable

    Returns:
        PanelSnapshot instance

    Raises:
        Exception: If provider invocation or conversion fails
    """
    result = provider()

    # Case 1: Already a PanelSnapshot
    if isinstance(result, PanelSnapshot):
        return result

    # Case 2: Dict format
    if isinstance(result, dict):
        return _panel_from_dict(panel_id, result)

    # Case 3: Tuple format (status, title, details)
    if isinstance(result, tuple) and len(result) == 3:
        status, title, details = result
        return PanelSnapshot(
            id=panel_id,
            title=str(title),
            status=normalize_status(status),
            details=details if isinstance(details, dict) else {},
        )

    # Unknown format
    raise ValueError(
        f"Panel provider '{panel_id}' returned unsupported type: {type(result).__name__}. "
        f"Expected PanelSnapshot, dict, or tuple(status, title, details)."
    )


def _panel_from_dict(fallback_id: str, data: Dict[str, Any]) -> PanelSnapshot:
    """
    Converts a dict to PanelSnapshot.

    Required fields: status
    Optional fields: id, title, details

    Args:
        fallback_id: Panel ID to use if not in data
        data: Panel data dict

    Returns:
        PanelSnapshot instance
    """
    panel_id = data.get("id", fallback_id)
    title = data.get("title", panel_id.replace("_", " ").title())
    status = normalize_status(data.get("status", "unknown"))
    details = data.get("details", {})

    if not isinstance(details, dict):
        details = {"value": str(details)}

    return PanelSnapshot(
        id=panel_id,
        title=title,
        status=status,
        details=details,
    )


# =============================================================================
# Optional Live-Track Provider Registry Integration
# =============================================================================


def _try_load_live_providers() -> Optional[Dict[str, PanelProvider]]:
    """
    Best-effort attempt to load panel providers from live-track modules.

    Returns:
        Dict of {panel_id: provider} if found, else None
    """
    try:
        # Try importing from live module (if exists)
        # This is a best-effort import - if the module doesn't exist, we gracefully degrade
        from src.live.status_providers import get_default_panel_providers

        providers = get_default_panel_providers()
        if providers:
            logger.debug(f"Loaded {len(providers)} panel providers from src.live.status_providers")
            return providers
    except ImportError:
        logger.debug("No src.live.status_providers module found, using fallback")
    except Exception as exc:
        logger.warning(f"Failed to load live providers: {exc}")

    return None


def build_live_status_snapshot_auto(
    *,
    meta: Optional[Dict[str, Any]] = None,
) -> LiveStatusSnapshot:
    """
    Builds a live status snapshot with automatic provider discovery.

    Tries to load providers from live-track modules, falls back to default if not found.

    Args:
        meta: Optional metadata dict

    Returns:
        LiveStatusSnapshot
    """
    providers = _try_load_live_providers()
    return build_live_status_snapshot(panel_providers=providers, meta=meta)
