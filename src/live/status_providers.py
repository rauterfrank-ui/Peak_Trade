# src/live/status_providers.py
"""
Peak_Trade – Live Status Panel Providers

This module is intentionally READ-ONLY.

Purpose:
- Provide "custom" panel providers for the Live Status Snapshot.
- Discovered via src.reporting.live_status_snapshot_builder.get_auto_panel_providers()
  which calls get_live_panel_providers() from this module.

Design goals:
- No hard dependencies (optional imports).
- No network calls.
- Safe in all environments (paper/testnet/dry/live).
"""

from __future__ import annotations

from typing import Any, Callable, Dict

PanelProvider = Callable[..., Any]

_PRESENTATION_HTTP_RETIRED_NOTE = (
    "Presentation HTTP / WebUI live panel services retired; read-only fallback only."
)


def get_live_panel_providers() -> Dict[str, PanelProvider]:
    """Return dict of {panel_id: provider_callable}."""
    return {
        "alerts": _panel_alerts,
        "live_sessions": _panel_live_sessions,
        "telemetry": _panel_telemetry,
        "positions": _panel_positions,
        "portfolio": _panel_portfolio,
        "risk": _panel_risk,
    }


def _fallback_panel(panel_id: str, title: str) -> dict[str, Any]:
    return {
        "id": panel_id,
        "title": title,
        "status": "unknown",
        "details": {"message": _PRESENTATION_HTTP_RETIRED_NOTE},
        "note": _PRESENTATION_HTTP_RETIRED_NOTE,
    }


def _panel_alerts(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("alerts", "Alerts")


def _panel_live_sessions(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("live_sessions", "Live Sessions")


def _panel_telemetry(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("telemetry", "Telemetry")


def _panel_positions(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("positions", "Positions")


def _panel_portfolio(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("portfolio", "Portfolio")


def _panel_risk(*args: Any, **kwargs: Any) -> Any:
    return _fallback_panel("risk", "Risk")
