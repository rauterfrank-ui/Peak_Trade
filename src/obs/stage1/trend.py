"""
Peak_Trade Stage1 Trend Analysis
=================================

Compute or load trend analysis for Stage1 monitoring.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .io import load_all_summaries
from .models import (
    Stage1Summary,
    Stage1Trend,
    Stage1TrendRange,
    Stage1TrendRollups,
    Stage1TrendSeries,
)

logger = logging.getLogger(__name__)


def compute_trend_from_summaries(
    summaries: List[Stage1Summary],
    days: int = 14,
) -> Stage1Trend:
    """
    Compute trend analysis from a list of summaries.

    Args:
        summaries: List of Stage1Summary objects (should be sorted newest first)
        days: Number of days to analyze

    Returns:
        Stage1Trend object with analysis.
    """
    # Take the most recent N days
    summaries = summaries[:days]

    # Build series
    series = []
    for summary in reversed(summaries):  # Oldest first for series
        series.append(
            Stage1TrendSeries(
                date=summary.date,
                new_alerts=summary.metrics.new_alerts,
                critical_alerts=summary.metrics.critical_alerts,
                parse_errors=summary.metrics.parse_errors,
                operator_actions=summary.metrics.operator_actions,
            )
        )

    # Compute rollups
    new_alerts_total = sum(s.new_alerts for s in series)
    new_alerts_avg = new_alerts_total / len(series) if series else 0.0
    critical_days = sum(1 for s in series if s.critical_alerts > 0)
    parse_error_days = sum(1 for s in series if s.parse_errors > 0)
    operator_action_days = sum(1 for s in series if s.operator_actions > 0)

    # Go/No-Go heuristic
    go_no_go = "GO"
    reasons = []

    if critical_days > 0:
        go_no_go = "NO_GO"
        reasons.append(f"critical alerts on {critical_days} days")
    elif new_alerts_total > 5:
        go_no_go = "HOLD"
        reasons.append(f"new_alerts_total={new_alerts_total} > threshold(5)")
    elif parse_error_days > 0:
        go_no_go = "HOLD"
        reasons.append(f"parse_error_days={parse_error_days}")

    if not reasons:
        reasons.append("all checks passed")

    rollups = Stage1TrendRollups(
        new_alerts_total=new_alerts_total,
        new_alerts_avg=new_alerts_avg,
        critical_days=critical_days,
        parse_error_days=parse_error_days,
        operator_action_days=operator_action_days,
        go_no_go=go_no_go,
        reasons=reasons,
    )

    # Build range (days must be >= 1, use min 1 for empty series)
    range_data = Stage1TrendRange(
        days=max(1, len(series)),
        start=series[0].date if series else None,
        end=series[-1].date if series else None,
    )

    now_utc = datetime.now(timezone.utc)

    return Stage1Trend(
        schema_version=1,
        generated_at_utc=now_utc.isoformat(),
        range=range_data,
        series=series,
        rollups=rollups,
    )


def load_trend(report_root: Path, days: int = 14) -> Optional[Stage1Trend]:
    """
    Load or compute Stage1 trend analysis.

    Priority:
    1. Try to load pre-computed stage1_trend.json
    2. Fall back to computing from available summaries

    Args:
        report_root: Root directory for Stage1 reports
        days: Number of days to analyze (for computed trends)

    Returns:
        Stage1Trend object if data available, None otherwise.
    """
    if not report_root.exists():
        logger.warning(f"Stage1 report root does not exist: {report_root}")
        return None

    # Try to load pre-computed trend
    trend_path = report_root / "stage1_trend.json"
    if trend_path.exists():
        try:
            with trend_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            trend = Stage1Trend.model_validate(data)
            logger.info(f"Loaded pre-computed trend from {trend_path}")
            return trend
        except Exception as e:
            logger.warning(f"Failed to load pre-computed trend from {trend_path}: {e}")
            # Fall through to compute

    # Compute from summaries
    logger.info(f"Computing trend from summaries (last {days} days)")
    summaries = load_all_summaries(report_root, limit=days)

    if not summaries:
        logger.warning(f"No summaries available to compute trend in {report_root}")
        return None

    return compute_trend_from_summaries(summaries, days=days)
