# src/webui/services/__init__.py
"""
Peak_Trade: WebUI Service Layer
================================

Shared service functions for WebUI endpoints and status panels.
"""

from .live_panel_data import (
    get_alerts_stats,
    get_live_sessions_stats,
    get_telemetry_summary,
    get_positions_snapshot,
    get_portfolio_snapshot,
    get_risk_status,
)

__all__ = [
    "get_alerts_stats",
    "get_live_sessions_stats",
    "get_telemetry_summary",
    "get_positions_snapshot",
    "get_portfolio_snapshot",
    "get_risk_status",
]
