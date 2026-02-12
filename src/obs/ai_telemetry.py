"""
AI Telemetrie (watch-only safe)
===============================
Minimal, shared Telemetry-Modul für AI-Entscheidungen/Aktionen.

Kanonische Metriken:
- peaktrade_ai_decisions_total{decision,reason,component,run_id}
- peaktrade_ai_actions_total{action,component,run_id}
- peaktrade_ai_decision_latency_seconds (Histogram)
- peaktrade_ai_last_decision_timestamp_seconds (Gauge)
- peaktrade_ai_live_heartbeat (Gauge = 1)

Design:
- Leichtgewichtig (keine Imports aus execution/risk/governance heavy paths)
- Deterministisch/watch-only safe: nur Metriken, keine Side-Effects
- Graceful Degradation: no-op wenn prometheus_client nicht verfügbar
"""

from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram
    from prometheus_client.core import REGISTRY

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    Histogram = None  # type: ignore
    REGISTRY = None  # type: ignore
    _PROM_AVAILABLE = False


_METRICS_INIT = False
_DECISIONS_TOTAL: Optional["Counter"] = None
_ACTIONS_TOTAL: Optional["Counter"] = None
_DECISION_LATENCY_S: Optional["Histogram"] = None
_LAST_DECISION_TS_S: Optional["Gauge"] = None
_HEARTBEAT: Optional["Gauge"] = None
_DECISION_LATENCY_MS: Optional["Histogram"] = None
_EVENTS_PARSE_ERRORS_TOTAL: Optional["Counter"] = None
_EVENTS_DROPPED_TOTAL: Optional["Counter"] = None
_LAST_EVENT_TS_S: Optional["Gauge"] = None

_AI_TELEMETRY_V2_ALLOWED_SOURCES = {"sample_v1", "beta_exec_v1", "exec_event_v0", "unknown"}
_AI_TELEMETRY_V2_ALLOWED_DROP_REASONS = {"bad_json", "unknown_schema", "missing_fields", "other"}


def _normalize_label(value: str, *, max_length: int) -> str:
    """
    Normalize label values to reduce cardinality risks:
    - lowercase
    - whitespace -> underscore
    - keep only [a-z0-9_-]
    - truncate
    """
    raw = (value or "").strip()
    if not raw:
        return "na"
    s = raw.lower().replace(" ", "_")
    s = "".join(c for c in s if c.isalnum() or c in ("_", "-"))
    if len(s) > max_length:
        s = s[:max_length]
    return s or "na"


def _ensure_metrics() -> None:
    global _METRICS_INIT
    global _DECISIONS_TOTAL, _ACTIONS_TOTAL, _DECISION_LATENCY_S, _LAST_DECISION_TS_S, _HEARTBEAT
    global _DECISION_LATENCY_MS, _EVENTS_PARSE_ERRORS_TOTAL, _EVENTS_DROPPED_TOTAL, _LAST_EVENT_TS_S

    if _METRICS_INIT:
        return
    _METRICS_INIT = True

    if not _PROM_AVAILABLE:
        return

    try:
        _DECISIONS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_ai_decisions_total",
            "Total number of AI decisions made.",
            labelnames=("decision", "reason", "component", "run_id"),
        )
        _ACTIONS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_ai_actions_total",
            "Total number of AI actions executed.",
            labelnames=("action", "component", "run_id"),
        )
        _DECISION_LATENCY_S = Histogram(  # type: ignore[misc]
            "peaktrade_ai_decision_latency_seconds",
            "AI decision latency in seconds.",
            labelnames=("component", "run_id"),
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        )
        _LAST_DECISION_TS_S = Gauge(  # type: ignore[misc]
            "peaktrade_ai_last_decision_timestamp_seconds",
            "Unix timestamp of last AI decision (wallclock now at record time).",
            labelnames=("component", "run_id"),
        )
        _HEARTBEAT = Gauge(  # type: ignore[misc]
            "peaktrade_ai_live_heartbeat",
            "AI component heartbeat (1 = alive).",
            labelnames=("component", "run_id"),
        )

        # AI Live Telemetry v2 (cardinality-safe, source-scoped)
        _DECISION_LATENCY_MS = Histogram(  # type: ignore[misc]
            "peaktrade_ai_decision_latency_ms",
            "AI decision latency in milliseconds.",
            labelnames=("source", "decision"),
            buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000),
        )
        _EVENTS_PARSE_ERRORS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_ai_events_parse_errors_total",
            "Total number of AI live events that failed parsing.",
            labelnames=("source",),
        )
        _EVENTS_DROPPED_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_ai_events_dropped_total",
            "Total number of AI live events dropped (finite reasons).",
            labelnames=("source", "reason"),
        )
        _LAST_EVENT_TS_S = Gauge(  # type: ignore[misc]
            "peaktrade_ai_last_event_timestamp_seconds",
            "Unix timestamp of last successfully processed AI live event (by source).",
            labelnames=("source",),
        )
    except Exception:
        # If metrics registration fails (e.g. duplicate registry), degrade to no-op.
        logger.warning("AI telemetry metrics init failed; telemetry will be no-op.", exc_info=True)
        _DECISIONS_TOTAL = None
        _ACTIONS_TOTAL = None
        _DECISION_LATENCY_S = None
        _LAST_DECISION_TS_S = None
        _HEARTBEAT = None
        _DECISION_LATENCY_MS = None
        _EVENTS_PARSE_ERRORS_TOTAL = None
        _EVENTS_DROPPED_TOTAL = None
        _LAST_EVENT_TS_S = None


def get_registry():
    """
    Return Prometheus registry if available (default REGISTRY), else None.
    Intended for advanced embedding; most callers can ignore this.
    """
    return REGISTRY if _PROM_AVAILABLE else None


def record_decision(
    decision: str,
    reason: str = "none",
    component: str = "execution",
    run_id: str = "na",
    latency_s: Optional[float] = None,
    timestamp_s: Optional[float] = None,
) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return

    try:
        d = _normalize_label(decision, max_length=32)
        r = _normalize_label(reason, max_length=96)
        c = _normalize_label(component, max_length=48)
        rid = _normalize_label(run_id, max_length=96)

        if _DECISIONS_TOTAL is not None:
            _DECISIONS_TOTAL.labels(decision=d, reason=r, component=c, run_id=rid).inc()

        if latency_s is not None and _DECISION_LATENCY_S is not None:
            _DECISION_LATENCY_S.labels(component=c, run_id=rid).observe(float(latency_s))

        if _LAST_DECISION_TS_S is not None:
            ts = float(timestamp_s) if timestamp_s is not None else time.time()
            _LAST_DECISION_TS_S.labels(component=c, run_id=rid).set(ts)
    except Exception:
        # Telemetry must never crash decision flow.
        logger.debug("record_decision failed (ignored).", exc_info=True)


def record_action(
    action: str,
    component: str = "execution",
    run_id: str = "na",
) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return

    try:
        a = _normalize_label(action, max_length=48)
        c = _normalize_label(component, max_length=48)
        rid = _normalize_label(run_id, max_length=96)
        if _ACTIONS_TOTAL is not None:
            _ACTIONS_TOTAL.labels(action=a, component=c, run_id=rid).inc()
    except Exception:
        logger.debug("record_action failed (ignored).", exc_info=True)


def set_heartbeat(
    component: str = "execution",
    run_id: str = "na",
) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return

    try:
        c = _normalize_label(component, max_length=48)
        rid = _normalize_label(run_id, max_length=96)
        if _HEARTBEAT is not None:
            _HEARTBEAT.labels(component=c, run_id=rid).set(1.0)
    except Exception:
        logger.debug("set_heartbeat failed (ignored).", exc_info=True)


def _sanitize_v2_source(source: str) -> str:
    s = _normalize_label(source, max_length=32)
    return s if s in _AI_TELEMETRY_V2_ALLOWED_SOURCES else "unknown"


def _sanitize_v2_drop_reason(reason: str) -> str:
    r = _normalize_label(reason, max_length=32)
    return r if r in _AI_TELEMETRY_V2_ALLOWED_DROP_REASONS else "other"


def observe_decision_latency_ms(*, source: str, decision: str, latency_ms: float) -> None:
    """
    Observe decision latency in milliseconds.
    Note: Only call this when the event provides latency_ms (do not fabricate).
    """
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        s = _sanitize_v2_source(source)
        d = _normalize_label(decision, max_length=32)
        if _DECISION_LATENCY_MS is not None:
            _DECISION_LATENCY_MS.labels(source=s, decision=d).observe(float(latency_ms))
    except Exception:
        logger.debug("observe_decision_latency_ms failed (ignored).", exc_info=True)


def inc_events_parse_error(*, source: str) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        s = _sanitize_v2_source(source)
        if _EVENTS_PARSE_ERRORS_TOTAL is not None:
            _EVENTS_PARSE_ERRORS_TOTAL.labels(source=s).inc()
    except Exception:
        logger.debug("inc_events_parse_error failed (ignored).", exc_info=True)


def inc_events_dropped(*, source: str, reason: str) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        s = _sanitize_v2_source(source)
        r = _sanitize_v2_drop_reason(reason)
        if _EVENTS_DROPPED_TOTAL is not None:
            _EVENTS_DROPPED_TOTAL.labels(source=s, reason=r).inc()
    except Exception:
        logger.debug("inc_events_dropped failed (ignored).", exc_info=True)


def set_last_event_timestamp_seconds(*, source: str, timestamp_s: float) -> None:
    """
    Record source freshness timestamp for the last successfully processed event.
    Only update this for valid events (parse + schema/fields ok) and only with event ts.
    """
    _ensure_metrics()
    if not _PROM_AVAILABLE:
        return
    try:
        s = _sanitize_v2_source(source)
        if _LAST_EVENT_TS_S is not None:
            _LAST_EVENT_TS_S.labels(source=s).set(float(timestamp_s))
    except Exception:
        logger.debug("set_last_event_timestamp_seconds failed (ignored).", exc_info=True)


__all__ = [
    "get_registry",
    "record_decision",
    "record_action",
    "set_heartbeat",
    "observe_decision_latency_ms",
    "inc_events_parse_error",
    "inc_events_dropped",
    "set_last_event_timestamp_seconds",
]
