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

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

# PanelProvider signature is intentionally loose to avoid tight coupling.
# The snapshot builder will call these with its expected arguments.
PanelProvider = Callable[..., Any]


def _try_import(path: str):
    """Best-effort import helper. Returns module or None."""
    try:
        module = __import__(path, fromlist=["*"])
        return module
    except Exception:
        return None


def get_live_panel_providers() -> Dict[str, PanelProvider]:
    """
    Return dict of {panel_id: provider_callable}.

    Notes:
    - Keep panel ids stable (used by UI / snapshot HTML renderer).
    - Providers must be pure/read-only.
    """
    return {
        # High-signal panels first
        "alerts": _panel_alerts,
        "live_sessions": _panel_live_sessions,
        "telemetry": _panel_telemetry,
        "positions": _panel_positions,  # optional: may be empty unless feed/state exists
        "portfolio": _panel_portfolio,  # optional
        "risk": _panel_risk,  # optional
    }


# ─────────────────────────────────────────────────────────────
# Panel implementations (safe: best-effort, never raise)
# ─────────────────────────────────────────────────────────────


def _panel_alerts(*args: Any, **kwargs: Any) -> Any:
    """
    Provide recent/historical alert summary.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Same data source as /api/live/alerts/stats endpoint
    """
    try:
        from src.webui.services.live_panel_data import get_alerts_stats

        stats = get_alerts_stats(hours=24)

        # Determine status based on stats
        is_fallback = stats.get("_fallback", False)
        status = "unknown" if is_fallback else "ok"

        # Check for critical alerts
        if not is_fallback:
            critical_count = stats.get("by_severity", {}).get("CRITICAL", 0)
            if critical_count > 0:
                status = "warning"

        return {
            "id": "alerts",
            "title": "Alerts",
            "status": status,
            "details": stats,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "alerts",
        "title": "Alerts",
        "status": "unknown",
        "details": {"message": "Alert provider not wired (fallback)"},
        "note": "Service layer not available",
    }


def _panel_live_sessions(*args: Any, **kwargs: Any) -> Any:
    """
    Provide live-session status summary.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Same data source as /api/live_sessions/stats endpoint
    """
    try:
        from src.webui.services.live_panel_data import get_live_sessions_stats

        stats = get_live_sessions_stats()

        # Determine status based on stats
        is_fallback = stats.get("_fallback", False)
        status = "unknown" if is_fallback else "ok"

        # Highlight if there are active sessions
        if not is_fallback:
            active = stats.get("active_sessions", 0)
            if active > 0:
                status = "active"

        return {
            "id": "live_sessions",
            "title": "Live Sessions",
            "status": status,
            "details": stats,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "live_sessions",
        "title": "Live Sessions",
        "status": "unknown",
        "details": {"message": "No live session provider available (fallback)"},
    }


def _panel_telemetry(*args: Any, **kwargs: Any) -> Any:
    """
    Provide basic telemetry summary if available.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Same data source as /api/telemetry/health endpoint
    """
    try:
        from src.webui.services.live_panel_data import get_telemetry_summary

        summary = get_telemetry_summary()

        # Determine status from health status
        is_fallback = summary.get("_fallback", False)
        if is_fallback:
            status = "unknown"
        else:
            health_status = summary.get("status", "unknown")
            # Map health status to panel status
            status_map = {
                "ok": "ok",
                "degraded": "warning",
                "critical": "error",
                "unknown": "unknown",
            }
            status = status_map.get(health_status, "unknown")

        return {
            "id": "telemetry",
            "title": "Telemetry",
            "status": status,
            "details": summary,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "telemetry",
        "title": "Telemetry",
        "status": "unknown",
        "details": {"message": "Telemetry provider not available (fallback)"},
    }


def _panel_positions(*args: Any, **kwargs: Any) -> Any:
    """
    Provide positions overview from active sessions.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Same data source as active session metrics
    """
    try:
        from src.webui.services.live_panel_data import get_positions_snapshot

        snapshot = get_positions_snapshot()

        # Determine status based on snapshot
        is_fallback = snapshot.get("_fallback", False)
        if is_fallback:
            status = "unknown"
        else:
            open_positions = snapshot.get("open_positions", 0)
            status = "active" if open_positions > 0 else "ok"

        return {
            "id": "positions",
            "title": "Positions",
            "status": status,
            "details": snapshot,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "positions",
        "title": "Positions",
        "status": "unknown",
        "details": {"message": "Positions state not available (fallback)"},
        "note": "Will show data once a session is running.",
    }


def _panel_portfolio(*args: Any, **kwargs: Any) -> Any:
    """
    Provide portfolio/PNL overview from active sessions.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Aggregates PnL, equity, exposure from active sessions
    """
    try:
        from src.webui.services.live_panel_data import get_portfolio_snapshot

        snapshot = get_portfolio_snapshot()

        # Determine status based on snapshot
        is_fallback = snapshot.get("_fallback", False)
        if is_fallback:
            status = "unknown"
        else:
            num_sessions = snapshot.get("num_sessions", 0)
            status = "active" if num_sessions > 0 else "ok"

        return {
            "id": "portfolio",
            "title": "Portfolio",
            "status": status,
            "details": snapshot,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "portfolio",
        "title": "Portfolio",
        "status": "unknown",
        "details": {"message": "Portfolio snapshot not available (fallback)"},
    }


def _panel_risk(*args: Any, **kwargs: Any) -> Any:
    """
    Provide risk limits / risk gate status from active sessions.

    Strategy:
    - Use the shared service layer (src.webui.services.live_panel_data)
    - Aggregates risk status from active session metrics
    """
    try:
        from src.webui.services.live_panel_data import get_risk_status

        risk_status = get_risk_status()

        # Determine panel status from risk status
        is_fallback = risk_status.get("_fallback", False)
        if is_fallback:
            status = "unknown"
        else:
            # Map risk status to panel status
            risk_state = risk_status.get("status", "ok")
            status_map = {
                "ok": "ok",
                "warning": "warning",
                "blocked": "error",  # blocked → error for visibility
                "unknown": "unknown",
            }
            status = status_map.get(risk_state, "unknown")

        return {
            "id": "risk",
            "title": "Risk",
            "status": status,
            "details": risk_status,
        }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback if service layer not available
    return {
        "id": "risk",
        "title": "Risk",
        "status": "unknown",
        "details": {"message": "Risk status not wired (fallback)"},
    }
