"""
Strategy/Risk Runtime Telemetry (watch/paper/shadow safe)
=========================================================

Prometheus metrics for Strategy and Risk runtime behavior.

Hard constraints:
- NO-LIVE: telemetry only; must never enable trading or change decisions.
- Low-cardinality labels: NO symbol/instrument labels, NO run_id, NO PII.
- Graceful degradation: no-op if prometheus_client unavailable or registration fails.

Metrics (v1):
- peaktrade_strategy_decisions_total{strategy_id, decision}
- peaktrade_strategy_signals_total{strategy_id, signal}
- peaktrade_strategy_position_gross_exposure{strategy_id, ccy}
- peaktrade_risk_checks_total{check, result}
- peaktrade_risk_limit_utilization{limit_id}  (gauge 0..1, clamped)
- peaktrade_risk_blocks_total{reason}
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

Counter = Gauge = None  # type: ignore
_PROM_AVAILABLE = False


_METRICS_INIT = False

_STRATEGY_DECISIONS_TOTAL: Optional["Counter"] = None
_STRATEGY_SIGNALS_TOTAL: Optional["Counter"] = None
_STRATEGY_GROSS_EXPOSURE: Optional["Gauge"] = None

_RISK_CHECKS_TOTAL: Optional["Counter"] = None
_RISK_LIMIT_UTILIZATION: Optional["Gauge"] = None
_RISK_BLOCKS_TOTAL: Optional["Counter"] = None


def _metrics_mode() -> str:
    return (os.getenv("PEAKTRADE_METRICS_MODE", "") or "").strip().upper() or "A"


def _mode_b_multiproc_dir() -> str:
    # Default matches metricsd default.
    return (
        os.getenv("PEAKTRADE_METRICS_MULTIPROC_DIR", "") or ""
    ).strip() or ".ops_local/prom_multiproc"


_ALLOWED_STRATEGY_DECISIONS = {
    "entry_long",
    "exit_long",
    "entry_short",
    "exit_short",
    "close_long",
    "close_short",
}
_ALLOWED_STRATEGY_SIGNALS = {"long", "short", "flat"}

_ALLOWED_RISK_CHECKS = {"live_limits.check_orders", "runtime_risk.evaluate_pre_order"}
_ALLOWED_RISK_RESULTS = {"allow", "block", "warn", "disabled", "error"}

_ALLOWED_LIMIT_IDS = {
    "max_order_notional",
    "max_total_exposure",
    "max_symbol_exposure",
    "max_open_positions",
    "max_daily_loss_abs",
    "max_daily_loss_pct",
}

# Keep reasons finite and operator-facing.
_ALLOWED_BLOCK_REASONS = {
    "runtime:reject",
    "runtime:halt",
    "runtime:pause",
    "runtime:unknown",
    # limit:<limit_id> is validated separately
}


def _normalize_label(value: str, *, max_length: int) -> str:
    """
    Normalize label values to reduce cardinality risks:
    - lowercase
    - whitespace -> underscore
    - keep only [a-z0-9_.:-] (explicitly excludes '/' to avoid symbol labels)
    - truncate
    """
    raw = (value or "").strip()
    if not raw:
        return "na"
    s = raw.lower().replace(" ", "_")
    s = "".join(c for c in s if c.isalnum() or c in ("_", "-", ".", ":", ";"))
    if len(s) > max_length:
        s = s[:max_length]
    return s or "na"


def _sanitize_strategy_id(strategy_id: str) -> str:
    return _normalize_label(strategy_id, max_length=96)


def _sanitize_ccy(ccy: str) -> str:
    c = (ccy or "").strip().upper()
    c = "".join(ch for ch in c if ch.isalnum())
    if not c:
        return "NA"
    if len(c) > 8:
        c = c[:8]
    return c


def _sanitize_decision(decision: str) -> Optional[str]:
    d = _normalize_label(decision, max_length=32)
    return d if d in _ALLOWED_STRATEGY_DECISIONS else None


def _sanitize_signal(signal: str) -> Optional[str]:
    s = _normalize_label(signal, max_length=16)
    return s if s in _ALLOWED_STRATEGY_SIGNALS else None


def _sanitize_risk_check(check: str) -> Optional[str]:
    c = _normalize_label(check, max_length=64)
    return c if c in _ALLOWED_RISK_CHECKS else None


def _sanitize_risk_result(result: str) -> Optional[str]:
    r = _normalize_label(result, max_length=16)
    return r if r in _ALLOWED_RISK_RESULTS else None


def _sanitize_limit_id(limit_id: str) -> Optional[str]:
    lid = _normalize_label(limit_id, max_length=48)
    return lid if lid in _ALLOWED_LIMIT_IDS else None


def _sanitize_block_reason(reason: str) -> Optional[str]:
    rr = _normalize_label(reason, max_length=64)
    if rr.startswith("limit:"):
        # allowlist the limit id segment
        limit_id = rr.split("limit:", 1)[1]
        lid = _sanitize_limit_id(limit_id)
        return f"limit:{lid}" if lid is not None else None
    return rr if rr in _ALLOWED_BLOCK_REASONS else None


def _ensure_metrics() -> None:
    global _METRICS_INIT
    global _STRATEGY_DECISIONS_TOTAL, _STRATEGY_SIGNALS_TOTAL, _STRATEGY_GROSS_EXPOSURE
    global _RISK_CHECKS_TOTAL, _RISK_LIMIT_UTILIZATION, _RISK_BLOCKS_TOTAL

    if _METRICS_INIT:
        return
    _METRICS_INIT = True

    global Counter, Gauge, _PROM_AVAILABLE

    # Mode B: multiprocess workers must set PROMETHEUS_MULTIPROC_DIR before
    # importing prometheus_client.
    if _metrics_mode() == "B":
        os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", _mode_b_multiproc_dir())

    try:
        from prometheus_client import Counter as _Counter, Gauge as _Gauge  # type: ignore

        Counter, Gauge = _Counter, _Gauge  # type: ignore[misc]
        _PROM_AVAILABLE = True
    except Exception:  # pragma: no cover
        Counter = Gauge = None  # type: ignore
        _PROM_AVAILABLE = False
        return

    try:
        _STRATEGY_DECISIONS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_strategy_decisions_total",
            "Total number of strategy decisions finalized (watch/paper/shadow).",
            labelnames=("strategy_id", "decision"),
        )
        _STRATEGY_SIGNALS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_strategy_signals_total",
            "Total number of final strategy signal changes emitted (watch/paper/shadow).",
            labelnames=("strategy_id", "signal"),
        )
        if _metrics_mode() == "B":
            _STRATEGY_GROSS_EXPOSURE = Gauge(  # type: ignore[misc]
                "peaktrade_strategy_position_gross_exposure",
                "Gross exposure (abs notional) per strategy in ccy units.",
                labelnames=("strategy_id", "ccy"),
                multiprocess_mode="livemax",
            )
        else:
            _STRATEGY_GROSS_EXPOSURE = Gauge(  # type: ignore[misc]
                "peaktrade_strategy_position_gross_exposure",
                "Gross exposure (abs notional) per strategy in ccy units.",
                labelnames=("strategy_id", "ccy"),
            )

        _RISK_CHECKS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_risk_checks_total",
            "Total number of risk check evaluations (watch/paper/shadow).",
            labelnames=("check", "result"),
        )
        if _metrics_mode() == "B":
            _RISK_LIMIT_UTILIZATION = Gauge(  # type: ignore[misc]
                "peaktrade_risk_limit_utilization",
                "Risk limit utilization ratio (clamped 0..1).",
                labelnames=("limit_id",),
                multiprocess_mode="livemax",
            )
        else:
            _RISK_LIMIT_UTILIZATION = Gauge(  # type: ignore[misc]
                "peaktrade_risk_limit_utilization",
                "Risk limit utilization ratio (clamped 0..1).",
                labelnames=("limit_id",),
            )
        _RISK_BLOCKS_TOTAL = Counter(  # type: ignore[misc]
            "peaktrade_risk_blocks_total",
            "Total number of risk blocks by finite reason allowlist.",
            labelnames=("reason",),
        )
    except Exception:
        logger.warning(
            "Strategy/risk telemetry metrics init failed; telemetry will be no-op.",
            exc_info=True,
        )
        _STRATEGY_DECISIONS_TOTAL = None
        _STRATEGY_SIGNALS_TOTAL = None
        _STRATEGY_GROSS_EXPOSURE = None
        _RISK_CHECKS_TOTAL = None
        _RISK_LIMIT_UTILIZATION = None
        _RISK_BLOCKS_TOTAL = None


def ensure_registered() -> None:
    """
    Ensure Strategy/Risk metrics are registered in the default Prometheus registry.

    This is safe to call even when prometheus_client is unavailable (no-op),
    and allows /metrics to expose the metric *names* even before any activity occurs.
    """
    _ensure_metrics()


def inc_strategy_signal(*, strategy_id: str, signal: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _STRATEGY_SIGNALS_TOTAL is None:
        return
    try:
        sid = _sanitize_strategy_id(strategy_id)
        sig = _sanitize_signal(signal)
        if sig is None:
            return
        _STRATEGY_SIGNALS_TOTAL.labels(strategy_id=sid, signal=sig).inc(int(n))
    except Exception:
        logger.debug("inc_strategy_signal failed (ignored).", exc_info=True)


def inc_strategy_decision(*, strategy_id: str, decision: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _STRATEGY_DECISIONS_TOTAL is None:
        return
    try:
        sid = _sanitize_strategy_id(strategy_id)
        dec = _sanitize_decision(decision)
        if dec is None:
            return
        _STRATEGY_DECISIONS_TOTAL.labels(strategy_id=sid, decision=dec).inc(int(n))
    except Exception:
        logger.debug("inc_strategy_decision failed (ignored).", exc_info=True)


def set_strategy_position_gross_exposure(*, strategy_id: str, ccy: str, exposure: float) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _STRATEGY_GROSS_EXPOSURE is None:
        return
    try:
        sid = _sanitize_strategy_id(strategy_id)
        c = _sanitize_ccy(ccy)
        v = float(exposure)
        if v < 0:
            v = -v
        _STRATEGY_GROSS_EXPOSURE.labels(strategy_id=sid, ccy=c).set(v)
    except Exception:
        logger.debug("set_strategy_position_gross_exposure failed (ignored).", exc_info=True)


def inc_risk_check(*, check: str, result: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _RISK_CHECKS_TOTAL is None:
        return
    try:
        chk = _sanitize_risk_check(check)
        res = _sanitize_risk_result(result)
        if chk is None or res is None:
            return
        _RISK_CHECKS_TOTAL.labels(check=chk, result=res).inc(int(n))
    except Exception:
        logger.debug("inc_risk_check failed (ignored).", exc_info=True)


def set_risk_limit_utilization(*, limit_id: str, utilization_0_1: float) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _RISK_LIMIT_UTILIZATION is None:
        return
    try:
        lid = _sanitize_limit_id(limit_id)
        if lid is None:
            return
        v = float(utilization_0_1)
        if v < 0:
            v = 0.0
        if v > 1:
            v = 1.0
        _RISK_LIMIT_UTILIZATION.labels(limit_id=lid).set(v)
    except Exception:
        logger.debug("set_risk_limit_utilization failed (ignored).", exc_info=True)


def inc_risk_block(*, reason: str, n: int = 1) -> None:
    _ensure_metrics()
    if not _PROM_AVAILABLE or _RISK_BLOCKS_TOTAL is None:
        return
    try:
        rr = _sanitize_block_reason(reason)
        if rr is None:
            return
        _RISK_BLOCKS_TOTAL.labels(reason=rr).inc(int(n))
    except Exception:
        logger.debug("inc_risk_block failed (ignored).", exc_info=True)


__all__ = [
    "ensure_registered",
    "inc_strategy_signal",
    "inc_strategy_decision",
    "set_strategy_position_gross_exposure",
    "inc_risk_check",
    "set_risk_limit_utilization",
    "inc_risk_block",
]
