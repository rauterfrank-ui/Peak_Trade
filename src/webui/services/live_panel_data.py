# src/webui/services/live_panel_data.py
"""
Peak_Trade: Live Panel Data Service Layer
==========================================

Read-only service functions providing stats for:
- Live panels (status_providers.py)
- WebUI API endpoints (/api/live/alerts/stats, /api/live_sessions/stats, etc.)

Design Principles:
- Single Source of Truth: Both panels and API use these functions
- READ-ONLY: No side effects, no writes
- Defensive: Graceful fallback on missing dependencies
- No Network Calls: Only local storage/registry access

Usage:
    from src.webui.services.live_panel_data import get_alerts_stats
    stats = get_alerts_stats(hours=24)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# ALERTS STATS
# =============================================================================


def get_alerts_stats(hours: int = 24) -> Dict[str, Any]:
    """
    Get alert statistics for the specified time window.

    Args:
        hours: Time window in hours (default: 24)

    Returns:
        Dict with:
        - total: Total number of alerts
        - by_severity: Dict of severity -> count
        - by_category: Dict of category -> count
        - sessions_with_alerts: Number of sessions with alerts
        - last_critical: Last critical alert (if any)
        - hours: Time window used

    Example:
        >>> stats = get_alerts_stats(hours=24)
        >>> print(f"Total alerts: {stats['total']}")
    """
    try:
        from src.live.alert_storage import get_alert_stats
    except ImportError as e:
        logger.debug("Alert storage not available: %s", e)
        return _alerts_stats_fallback(hours)
    except Exception as e:
        logger.warning("Error importing alert storage: %s", e)
        return _alerts_stats_fallback(hours)

    try:
        stats = get_alert_stats(hours=hours)

        # Ensure required keys exist
        return {
            "total": stats.get("total", 0),
            "by_severity": stats.get("by_severity", {"INFO": 0, "WARN": 0, "CRITICAL": 0}),
            "by_category": stats.get("by_category", {"RISK": 0, "EXECUTION": 0, "SYSTEM": 0}),
            "sessions_with_alerts": stats.get("sessions_with_alerts", 0),
            "last_critical": stats.get("last_critical"),
            "hours": stats.get("hours", hours),
        }
    except ImportError as e:
        logger.debug("Alert stats function not available: %s", e)
        return _alerts_stats_fallback(hours)
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting alert stats fields: %s", e)
        return _alerts_stats_fallback(hours)
    except Exception as e:
        logger.warning("Unexpected error getting alert stats: %s", e, exc_info=True)
        return _alerts_stats_fallback(hours)


def _alerts_stats_fallback(hours: int) -> Dict[str, Any]:
    """Fallback when alert stats are not available."""
    return {
        "total": 0,
        "by_severity": {"INFO": 0, "WARN": 0, "CRITICAL": 0},
        "by_category": {"RISK": 0, "EXECUTION": 0, "SYSTEM": 0},
        "sessions_with_alerts": 0,
        "last_critical": None,
        "hours": hours,
        "_fallback": True,
        "message": "Alert storage not available",
    }


# =============================================================================
# LIVE SESSIONS STATS
# =============================================================================


def get_live_sessions_stats(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get live session statistics.

    Args:
        base_dir: Optional override for session registry directory

    Returns:
        Dict with:
        - total_sessions: Total number of sessions
        - active_sessions: Number of currently running sessions
        - by_mode: Dict of mode -> count
        - by_status: Dict of status -> count
        - total_pnl: Sum of realized PnL
        - avg_drawdown: Average max drawdown

    Example:
        >>> stats = get_live_sessions_stats()
        >>> print(f"Active: {stats['active_sessions']}, Total: {stats['total_sessions']}")
    """
    # Direct implementation to avoid circular dependency
    try:
        from src.experiments.live_session_registry import get_session_summary, list_session_records
    except ImportError as e:
        logger.debug("Live session registry not available: %s", e)
        return _live_sessions_stats_fallback()
    except Exception as e:
        logger.warning("Error importing live session registry: %s", e)
        return _live_sessions_stats_fallback()

    try:
        kwargs = {}
        if base_dir is not None:
            kwargs["base_dir"] = base_dir

        summary = get_session_summary(**kwargs)

        # Mode-Verteilung berechnen
        records = list_session_records(**kwargs)
        mode_counts: Dict[str, int] = {}
        for r in records:
            mode = r.mode or "unknown"
            mode_counts[mode] = mode_counts.get(mode, 0) + 1

        # Active sessions count
        by_status = summary.get("by_status", {})
        active_sessions = by_status.get("started", 0)

        # Ensure required keys exist
        return {
            "total_sessions": summary.get("num_sessions", 0),
            "active_sessions": active_sessions,
            "by_mode": mode_counts,
            "by_status": by_status,
            "total_pnl": summary.get("total_realized_pnl", 0.0),
            "avg_drawdown": summary.get("avg_max_drawdown", 0.0),
        }
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting session stats fields: %s", e)
        return _live_sessions_stats_fallback()
    except Exception as e:
        logger.warning("Unexpected error getting session stats: %s", e, exc_info=True)
        return _live_sessions_stats_fallback()


def _live_sessions_stats_fallback() -> Dict[str, Any]:
    """Fallback when session stats are not available."""
    return {
        "total_sessions": 0,
        "active_sessions": 0,
        "by_mode": {},
        "by_status": {},
        "total_pnl": 0.0,
        "avg_drawdown": 0.0,
        "_fallback": True,
        "message": "Live session registry not available",
    }


# =============================================================================
# TELEMETRY SUMMARY
# =============================================================================


def get_telemetry_summary(root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get telemetry health summary.

    Args:
        root: Optional telemetry root directory (default: logs/execution)

    Returns:
        Dict with:
        - status: Overall health status (ok/degraded/critical)
        - total_sessions: Number of telemetry sessions found
        - disk_usage_mb: Disk usage in MB
        - recent_errors: Number of recent parse errors
        - health_checks: List of individual check results

    Example:
        >>> summary = get_telemetry_summary()
        >>> print(f"Health: {summary['status']}")
    """
    telemetry_root = root or Path("logs/execution")

    try:
        from src.execution.telemetry_health import run_health_checks
    except ImportError as e:
        logger.debug("Telemetry health module not available: %s", e)
        return _telemetry_summary_fallback(telemetry_root)
    except Exception as e:
        logger.warning("Error importing telemetry health: %s", e)
        return _telemetry_summary_fallback(telemetry_root)

    try:
        report = run_health_checks(telemetry_root)
        report_dict = report.to_dict()

        # Extract key metrics
        checks = report_dict.get("checks", [])
        disk_check = next((c for c in checks if "disk" in c.get("name", "").lower()), None)
        disk_usage_mb = disk_check.get("value", 0.0) if disk_check else 0.0

        # Count sessions (from file count check)
        file_check = next((c for c in checks if "files" in c.get("name", "").lower()), None)
        total_sessions = 0
        if file_check:
            # Extract from message like "Found 42 *.jsonl files"
            msg = file_check.get("message", "")
            import re

            match = re.search(r"(\d+)\s+\*\.jsonl", msg)
            if match:
                total_sessions = int(match.group(1))

        # Parse error check
        error_check = next((c for c in checks if "parse" in c.get("name", "").lower()), None)
        recent_errors = 0
        if error_check:
            msg = error_check.get("message", "")
            import re

            match = re.search(r"(\d+)\s+errors?", msg)
            if match:
                recent_errors = int(match.group(1))

        return {
            "status": report_dict.get("status", "unknown"),
            "total_sessions": total_sessions,
            "disk_usage_mb": round(disk_usage_mb, 2),
            "recent_errors": recent_errors,
            "health_checks": checks,
            "timestamp": report_dict.get("timestamp"),
        }
    except ImportError as e:
        logger.debug("Health check function not available: %s", e)
        return _telemetry_summary_fallback(telemetry_root)
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting telemetry health fields: %s", e)
        return _telemetry_summary_fallback(telemetry_root)
    except Exception as e:
        logger.warning("Unexpected error getting telemetry summary: %s", e, exc_info=True)
        return _telemetry_summary_fallback(telemetry_root)


def _telemetry_summary_fallback(root: Path) -> Dict[str, Any]:
    """Fallback when telemetry health is not available."""
    return {
        "status": "unknown",
        "total_sessions": 0,
        "disk_usage_mb": 0.0,
        "recent_errors": 0,
        "health_checks": [],
        "_fallback": True,
        "message": "Telemetry health module not available",
        "root": str(root),
    }


# =============================================================================
# POSITIONS SNAPSHOT
# =============================================================================


def get_positions_snapshot() -> Dict[str, Any]:
    """
    Get current positions snapshot from active sessions.

    Returns:
        Dict with:
        - open_positions: Number of open positions
        - symbols: List of symbols with positions
        - total_notional: Total position notional
        - positions: List of position details (if available)

    Example:
        >>> snapshot = get_positions_snapshot()
        >>> print(f"Open: {snapshot['open_positions']}")
    """
    try:
        from src.experiments.live_session_registry import list_session_records
    except ImportError as e:
        logger.debug("Live session registry not available: %s", e)
        return _positions_snapshot_fallback()
    except Exception as e:
        logger.warning("Error importing live session registry: %s", e)
        return _positions_snapshot_fallback()

    try:
        # Get active sessions (status=started)
        records = list_session_records(limit=100)
        active_sessions = [r for r in records if r.status == "started"]

        if not active_sessions:
            return {
                "open_positions": 0,
                "symbols": [],
                "total_notional": 0.0,
                "positions": [],
                "message": "No active sessions",
            }

        # Aggregate positions from active sessions
        positions_by_symbol: Dict[str, Dict[str, Any]] = {}
        total_notional = 0.0

        for session in active_sessions:
            metrics = session.metrics or {}

            # Try to extract position info from metrics
            num_positions = metrics.get("open_positions", 0)
            if num_positions > 0:
                # Try to get symbol-specific info
                symbol = session.symbol or "unknown"
                if symbol not in positions_by_symbol:
                    positions_by_symbol[symbol] = {
                        "symbol": symbol,
                        "sessions": 0,
                        "notional": 0.0,
                    }

                positions_by_symbol[symbol]["sessions"] += 1

                # Try to extract notional
                notional = metrics.get("total_notional", 0.0) or metrics.get("exposure", 0.0)
                positions_by_symbol[symbol]["notional"] += notional
                total_notional += notional

        positions_list = list(positions_by_symbol.values())

        return {
            "open_positions": sum(1 for p in positions_list if p["notional"] > 0),
            "symbols": [p["symbol"] for p in positions_list],
            "total_notional": round(total_notional, 2),
            "positions": positions_list,
            "active_sessions": len(active_sessions),
        }
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting position snapshot fields: %s", e)
        return _positions_snapshot_fallback()
    except Exception as e:
        logger.warning("Unexpected error getting position snapshot: %s", e, exc_info=True)
        return _positions_snapshot_fallback()


def _positions_snapshot_fallback() -> Dict[str, Any]:
    """Fallback when positions snapshot is not available."""
    return {
        "open_positions": 0,
        "symbols": [],
        "total_notional": 0.0,
        "positions": [],
        "_fallback": True,
        "message": "Position data not available",
    }


# =============================================================================
# PORTFOLIO SNAPSHOT
# =============================================================================


def get_portfolio_snapshot() -> Dict[str, Any]:
    """
    Get portfolio overview (PnL, equity, exposure).

    Returns:
        Dict with:
        - total_pnl: Realized PnL across all sessions
        - unrealized_pnl: Unrealized PnL (if available)
        - equity: Estimated equity
        - total_exposure: Total notional exposure
        - num_sessions: Number of active sessions contributing

    Example:
        >>> snapshot = get_portfolio_snapshot()
        >>> print(f"PnL: {snapshot['total_pnl']}")
    """
    try:
        from src.experiments.live_session_registry import list_session_records
    except ImportError as e:
        logger.debug("Live session registry not available: %s", e)
        return _portfolio_snapshot_fallback()
    except Exception as e:
        logger.warning("Error importing live session registry: %s", e)
        return _portfolio_snapshot_fallback()

    try:
        # Get all recent sessions
        records = list_session_records(limit=100)
        active_sessions = [r for r in records if r.status == "started"]

        if not active_sessions:
            # Return completed session stats as fallback
            total_pnl = 0.0
            for session in records[:10]:  # Last 10 sessions
                metrics = session.metrics or {}
                pnl = metrics.get("realized_pnl", 0.0) or metrics.get("pnl", 0.0)
                total_pnl += pnl

            return {
                "total_pnl": round(total_pnl, 2),
                "unrealized_pnl": 0.0,
                "equity": 0.0,
                "total_exposure": 0.0,
                "num_sessions": 0,
                "message": "No active sessions, showing historical PnL",
            }

        # Aggregate from active sessions
        total_pnl = 0.0
        total_unrealized = 0.0
        total_exposure = 0.0

        for session in active_sessions:
            metrics = session.metrics or {}

            # Realized PnL
            pnl = metrics.get("realized_pnl", 0.0) or metrics.get("pnl", 0.0)
            total_pnl += pnl

            # Unrealized PnL (if available)
            unrealized = metrics.get("unrealized_pnl", 0.0)
            total_unrealized += unrealized

            # Exposure
            exposure = metrics.get("total_notional", 0.0) or metrics.get("exposure", 0.0)
            total_exposure += exposure

        # Estimate equity (simplified)
        equity = total_exposure + total_pnl + total_unrealized

        return {
            "total_pnl": round(total_pnl, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "equity": round(equity, 2),
            "total_exposure": round(total_exposure, 2),
            "num_sessions": len(active_sessions),
        }
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting portfolio snapshot fields: %s", e)
        return _portfolio_snapshot_fallback()
    except Exception as e:
        logger.warning("Unexpected error getting portfolio snapshot: %s", e, exc_info=True)
        return _portfolio_snapshot_fallback()


def _portfolio_snapshot_fallback() -> Dict[str, Any]:
    """Fallback when portfolio snapshot is not available."""
    return {
        "total_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "equity": 0.0,
        "total_exposure": 0.0,
        "num_sessions": 0,
        "_fallback": True,
        "message": "Portfolio data not available",
    }


# =============================================================================
# RISK STATUS
# =============================================================================


def get_risk_status() -> Dict[str, Any]:
    """
    Get current risk status and limits.

    Returns:
        Dict with:
        - status: Overall risk status (ok/warning/breach)
        - severity: Risk severity level
        - limits_enabled: Whether risk limits are active
        - limit_details: List of individual limit checks
        - violations: List of current violations

    Example:
        >>> status = get_risk_status()
        >>> print(f"Risk: {status['status']}")
    """
    try:
        from src.experiments.live_session_registry import list_session_records
    except ImportError as e:
        logger.debug("Live session registry not available: %s", e)
        return _risk_status_fallback()
    except Exception as e:
        logger.warning("Error importing live session registry: %s", e)
        return _risk_status_fallback()

    try:
        # Get active sessions
        records = list_session_records(limit=50)
        active_sessions = [r for r in records if r.status == "started"]

        if not active_sessions:
            return {
                "status": "ok",
                "severity": "ok",
                "limits_enabled": False,
                "limit_details": [],
                "violations": [],
                "message": "No active sessions",
            }

        # Aggregate risk status from active sessions
        worst_severity = "ok"
        all_limit_details = []
        violations = []
        limits_enabled = False

        severity_order = {"ok": 0, "warning": 1, "breach": 2}

        for session in active_sessions:
            metrics = session.metrics or {}

            # Extract risk status from metrics
            risk_check = metrics.get("risk_check", {})
            if isinstance(risk_check, dict):
                severity = risk_check.get("severity", "ok")
                if severity_order.get(severity, 0) > severity_order.get(worst_severity, 0):
                    worst_severity = severity

                # Collect limit details
                limit_details = risk_check.get("limit_details", [])
                if isinstance(limit_details, list):
                    all_limit_details.extend(limit_details)

                # Check for violations
                if not risk_check.get("allowed", True):
                    reasons = risk_check.get("reasons", [])
                    violations.extend(reasons)

                limits_enabled = True

            # Also check top-level risk fields
            if "risk_severity" in metrics:
                severity = metrics["risk_severity"]
                if severity_order.get(severity, 0) > severity_order.get(worst_severity, 0):
                    worst_severity = severity

        # Map severity to status
        status_map = {"ok": "ok", "warning": "warning", "breach": "blocked"}
        status = status_map.get(worst_severity, "ok")

        return {
            "status": status,
            "severity": worst_severity,
            "limits_enabled": limits_enabled,
            "limit_details": all_limit_details,
            "violations": violations,
            "active_sessions": len(active_sessions),
        }
    except (KeyError, AttributeError) as e:
        logger.warning("Error extracting risk status fields: %s", e)
        return _risk_status_fallback()
    except Exception as e:
        logger.warning("Unexpected error getting risk status: %s", e, exc_info=True)
        return _risk_status_fallback()


def _risk_status_fallback() -> Dict[str, Any]:
    """Fallback when risk status is not available."""
    return {
        "status": "unknown",
        "severity": "ok",
        "limits_enabled": False,
        "limit_details": [],
        "violations": [],
        "_fallback": True,
        "message": "Risk status not available",
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "get_alerts_stats",
    "get_live_sessions_stats",
    "get_telemetry_summary",
    "get_positions_snapshot",
    "get_portfolio_snapshot",
    "get_risk_status",
]
