"""
Trade Flow Telemetry (watch-only safe)
=====================================
Prometheus counters for core trade-flow events:

- peaktrade_signals_total{strategy_id, symbol, signal}
- peaktrade_orders_approved_total{strategy_id, symbol, venue, order_type}
- peaktrade_orders_blocked_total{strategy_id, symbol, reason}

Constraints:
- NO-LIVE / watch-only safe (telemetry only).
- Low-cardinality labels (no UUIDs/order IDs, no dynamic reason strings).
- Graceful degradation: no-op if prometheus_client is unavailable or registration fails.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter  # type: ignore

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    Counter = None  # type: ignore
    _PROM_AVAILABLE = False


_METRICS_INIT = False
_SIGNALS_TOTAL: Optional["Counter"] = None
_ORDERS_APPROVED_TOTAL: Optional["Counter"] = None
_ORDERS_BLOCKED_TOTAL: Optional["Counter"] = None


_ALLOWED_SIGNALS = {"buy", "sell", "flat"}
_ALLOWED_BLOCK_REASONS = {"risk_manager", "governance", "limits", "cooldown", "unknown"}


def _normalize_label(value: str, *, max_length: int) -> str:
    """
    Normalize label values to reduce cardinality risks:
    - lowercase
    - whitespace -> underscore
    - keep only [a-z0-9_./-] (allows common symbols like btc/eur)
    - truncate
    """
    raw = (value or "").strip()
    if not raw:
        return "na"
    s = raw.lower().replace(" ", "_")
    s = "".join(c for c in s if c.isalnum() or c in ("_", "-", ".", "/"))
    if len(s) > max_length:
        s = s[:max_length]
    return s or "na"


def _ensure_metrics() -> None:
    global _METRICS_INIT
    global _SIGNALS_TOTAL, _ORDERS_APPROVED_TOTAL, _ORDERS_BLOCKED_TOTAL

    if _METRICS_INIT:
        return
    _METRICS_INIT = True

    if not _PROM_AVAILABLE:
        return

    try:
        _SIGNALS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_signals_total",
            "Total number of final signal events emitted (watch-only).",
            labelnames=("strategy_id", "symbol", "signal"),
        )
        _ORDERS_APPROVED_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_orders_approved_total",
            "Total number of orders approved after risk/governance gates (watch-only).",
            labelnames=("strategy_id", "symbol", "venue", "order_type"),
        )
        _ORDERS_BLOCKED_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_orders_blocked_total",
            "Total number of orders blocked/rejected by gates (finite reason allowlist).",
            labelnames=("strategy_id", "symbol", "reason"),
        )
    except Exception:
        # If metrics registration fails (e.g. duplicate registry), degrade to no-op.
        logger.warning(
            "Trade flow telemetry metrics init failed; telemetry will be no-op.", exc_info=True
        )
        _SIGNALS_TOTAL = None
        _ORDERS_APPROVED_TOTAL = None
        _ORDERS_BLOCKED_TOTAL = None


def _sanitize_signal(signal: str) -> str:
    s = _normalize_label(signal, max_length=16)
    return s if s in _ALLOWED_SIGNALS else "flat"


def _sanitize_block_reason(reason: str) -> str:
    r = _normalize_label(reason, max_length=32)
    return r if r in _ALLOWED_BLOCK_REASONS else "unknown"


def map_block_reason(*, status: Optional[str] = None, raw_reason: Optional[str] = None) -> str:
    """
    Map internal status/reason strings to a finite allowlist.

    Allowlist:
      {risk_manager, governance, limits, cooldown, unknown}
    """
    st = _normalize_label(status or "", max_length=48)
    rr = _normalize_label(raw_reason or "", max_length=128)

    # ExecutionStatus-based fast paths
    if "blocked_by_governance" in st:
        return "governance"
    if "blocked_by_risk" in st:
        # In this codebase, risk blocks are typically risk-limits violations.
        return "limits"
    if "blocked_by_safety" in st or "blocked_by_environment" in st:
        # Safety/environment blocks are governance-like constraints from an operator standpoint.
        return "governance"

    # Reason-string heuristics (must stay finite / deterministic)
    if "cooldown" in rr:
        return "cooldown"
    if "govern" in rr or "live_mode" in rr or "locked" in rr:
        return "governance"
    if "risk_limit" in rr or "risk_limits" in rr or "limit" in rr:
        return "limits"
    if "risk" in rr:
        return "risk_manager"

    return "unknown"


def inc_signal(*, strategy_id: str, symbol: str, signal: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        sid = _normalize_label(strategy_id, max_length=96)
        sym = _normalize_label(symbol, max_length=64)
        sig = _sanitize_signal(signal)
        if _SIGNALS_TOTAL is not None:
            _SIGNALS_TOTAL.labels(strategy_id=sid, symbol=sym, signal=sig).inc(int(n))
    except Exception:
        logger.debug("inc_signal failed (ignored).", exc_info=True)


def inc_orders_approved(
    *,
    strategy_id: str,
    symbol: str,
    venue: str = "na",
    order_type: str = "na",
    n: int = 1,
) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        sid = _normalize_label(strategy_id, max_length=96)
        sym = _normalize_label(symbol, max_length=64)
        v = _normalize_label(venue, max_length=32)
        ot = _normalize_label(order_type, max_length=32)
        if _ORDERS_APPROVED_TOTAL is not None:
            _ORDERS_APPROVED_TOTAL.labels(strategy_id=sid, symbol=sym, venue=v, order_type=ot).inc(
                int(n)
            )
    except Exception:
        logger.debug("inc_orders_approved failed (ignored).", exc_info=True)


def inc_orders_blocked(*, strategy_id: str, symbol: str, reason: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        sid = _normalize_label(strategy_id, max_length=96)
        sym = _normalize_label(symbol, max_length=64)
        r = _sanitize_block_reason(reason)
        if _ORDERS_BLOCKED_TOTAL is not None:
            _ORDERS_BLOCKED_TOTAL.labels(strategy_id=sid, symbol=sym, reason=r).inc(int(n))
    except Exception:
        logger.debug("inc_orders_blocked failed (ignored).", exc_info=True)


__all__ = [
    "inc_signal",
    "inc_orders_approved",
    "inc_orders_blocked",
    "map_block_reason",
]
