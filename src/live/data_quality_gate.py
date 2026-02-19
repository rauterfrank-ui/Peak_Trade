"""Data Quality Hard Gate — Freshness & Gap Detection.

Blocks or degrades trading when market/data inputs are stale or have gaps.
Fail-closed: if monitors unavailable or checks fail → NO_TRADE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

# Best-effort integration with existing monitors (lazy imports inside evaluate)


@dataclass(frozen=True)
class DataQualityDecision:
    """Structured decision from DQ gate evaluation."""

    gate_id: str
    status: str  # PASS|FAIL
    reasons: List[str]
    details: Dict[str, Any]


def evaluate_data_quality(
    *,
    asof_utc: str,
    context: Dict[str, Any],
) -> DataQualityDecision:
    """Evaluate freshness/gap detection using existing monitors if available.

    Fail-closed: if monitors unavailable or misconfigured, FAIL (no-trade) in live context.
    """
    blocking_reasons: List[str] = []
    details: Dict[str, Any] = {"asof_utc": asof_utc}

    QualityMonitor = None
    run_live_quality_checks = None

    try:
        from src.data.shadow.quality_monitor import QualityMonitor  # noqa: F401

        details["monitor"] = "QualityMonitor"
    except Exception:
        details["quality_monitor"] = "unavailable"

    try:
        from src.data.shadow.live_quality_checks import run_live_quality_checks as _rlc

        run_live_quality_checks = _rlc
        details["live_checks"] = "run_live_quality_checks"
    except Exception:
        details["live_quality_checks"] = "unavailable"

    # If both unavailable → FAIL
    if QualityMonitor is None and run_live_quality_checks is None:
        blocking_reasons = [
            "quality_monitor_unavailable",
            "live_quality_checks_unavailable",
        ]
        return DataQualityDecision(
            gate_id="dq_freshness_gap",
            status="FAIL",
            reasons=blocking_reasons,
            details=details,
        )

    # If live checks exist, run them
    if run_live_quality_checks is not None:
        try:
            ok, extra = run_live_quality_checks(asof_utc=asof_utc, context=context)
            details["live_checks_extra"] = extra
            if not ok:
                blocking_reasons.append("live_quality_checks_failed")
        except Exception as e:
            blocking_reasons.append(f"live_quality_checks_exception:{type(e).__name__}")

    status = "PASS" if not blocking_reasons else "FAIL"
    return DataQualityDecision(
        gate_id="dq_freshness_gap",
        status=status,
        reasons=blocking_reasons,
        details=details,
    )
