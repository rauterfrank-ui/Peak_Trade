"""
Daily Drift Report Generator - WP1C (Phase 1 Shadow Trading)

Generates deterministic daily drift reports in Markdown format.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.observability.drift.comparator import DriftMetrics

logger = logging.getLogger(__name__)


class DailyReportGenerator:
    """
    Generates daily drift reports.

    Reports include:
    - Match rate
    - Divergence statistics
    - Drift severity assessment
    - Recommendations

    Usage:
        >>> generator = DailyReportGenerator()
        >>> generator.generate_report(
        ...     metrics=metrics,
        ...     date=datetime.now(),
        ...     output_path=Path("reports/drift/daily.md")
        ... )
    """

    def generate_report(
        self,
        metrics: DriftMetrics,
        date: datetime,
        output_path: Path,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Generate daily drift report.

        Args:
            metrics: Drift metrics
            date: Report date
            output_path: Path to write report
            session_id: Optional session identifier
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown
        md = self._generate_markdown(metrics, date, session_id)

        # Write to file
        with open(output_path, "w") as f:
            f.write(md)

        logger.info(f"Drift report written to {output_path}")

    def _generate_markdown(
        self,
        metrics: DriftMetrics,
        date: datetime,
        session_id: Optional[str],
    ) -> str:
        """
        Generate markdown for report.

        Args:
            metrics: Drift metrics
            date: Report date
            session_id: Optional session ID

        Returns:
            Markdown string
        """
        date_str = date.strftime("%Y-%m-%d")
        session_str = f" - Session: {session_id}" if session_id else ""

        # Determine drift severity
        severity, severity_emoji = self._assess_severity(metrics.match_rate)

        md = f"""# Daily Drift Report - {date_str}{session_str}

## 📊 Overview

**Date:** {date_str}
**Match Rate:** {metrics.match_rate:.2%}
**Drift Severity:** {severity_emoji} **{severity}**

---

## 🎯 Signal Comparison

| Metric | Value |
|--------|-------|
| **Shadow Signals** | {metrics.total_signals_shadow} |
| **Backtest Signals** | {metrics.total_signals_backtest} |
| **Matched Signals** | {metrics.matched_signals} |
| **Divergent Signals** | {metrics.divergent_signals} |
| **Match Rate** | {metrics.match_rate:.2%} |

---

## 📈 Divergence Statistics

| Metric | Value |
|--------|-------|
| **Avg Price Divergence** | {metrics.avg_price_divergence:.2f}% |
| **Avg Quantity Divergence** | {metrics.avg_quantity_divergence:.2f}% |

---

## ⚠️ Assessment

{self._generate_assessment(metrics)}

---

## 💡 Recommendations

{self._generate_recommendations(metrics)}

---

## 📝 Details

**Shadow Symbols:** {", ".join(metrics.details.get("shadow_symbols", [])) or "None"}
**Backtest Symbols:** {", ".join(metrics.details.get("backtest_symbols", [])) or "None"}

---

**Generated:** {datetime.utcnow().isoformat()}Z
**Phase:** Shadow Trading (Phase 1)
"""

        return md

    def _assess_severity(self, match_rate: float) -> tuple[str, str]:
        """
        Assess drift severity.

        Args:
            match_rate: Match rate (0.0 - 1.0)

        Returns:
            Tuple of (severity_name, emoji)
        """
        if match_rate >= 0.95:
            return ("LOW", "🟢")
        elif match_rate >= 0.85:
            return ("MEDIUM", "🟡")
        elif match_rate >= 0.70:
            return ("HIGH", "🟠")
        else:
            return ("CRITICAL", "🔴")

    def _generate_assessment(self, metrics: DriftMetrics) -> str:
        """
        Generate assessment text.

        Args:
            metrics: Drift metrics

        Returns:
            Assessment markdown
        """
        if metrics.match_rate >= 0.95:
            return """✅ **Excellent alignment** between shadow and backtest.
Drift is within acceptable tolerances. No action required."""

        elif metrics.match_rate >= 0.85:
            return """⚠️ **Moderate drift detected** between shadow and backtest.
Signal execution is mostly aligned but some divergence observed.
Monitor closely for increasing drift."""

        elif metrics.match_rate >= 0.70:
            return """⚠️ **High drift detected** between shadow and backtest.
Significant divergence in signals. Investigation recommended."""

        else:
            return """🚨 **CRITICAL drift detected** between shadow and backtest.
Shadow trading is significantly diverging from backtest expectations.
**Immediate investigation required. Consider pausing shadow trading.**"""

    def _generate_recommendations(self, metrics: DriftMetrics) -> str:
        """
        Generate recommendations text.

        Args:
            metrics: Drift metrics

        Returns:
            Recommendations markdown
        """
        recommendations = []

        if metrics.match_rate < 0.70:
            recommendations.append(
                "🛑 **Consider pausing shadow trading** until drift is investigated."
            )
            recommendations.append(
                "🔍 **Investigate root cause:** Check data quality, timing, and execution logic."
            )

        elif metrics.match_rate < 0.85:
            recommendations.append("🔍 **Monitor drift closely** over next 24-48 hours.")
            recommendations.append("📊 **Review divergent signals** to identify patterns.")

        if metrics.avg_price_divergence > 2.0:
            recommendations.append(
                f"💰 **High price divergence** ({metrics.avg_price_divergence:.2f}%): "
                "Check market data feed quality."
            )

        if metrics.avg_quantity_divergence > 5.0:
            recommendations.append(
                f"📏 **High quantity divergence** ({metrics.avg_quantity_divergence:.2f}%): "
                "Review position sizing logic."
            )

        if metrics.divergent_signals > metrics.matched_signals:
            recommendations.append(
                "⚠️ **More divergent signals than matched:** Check signal generation logic."
            )

        if not recommendations:
            recommendations.append("✅ **No action required.** Continue monitoring.")

        return "\n".join(f"{i + 1}. {rec}" for i, rec in enumerate(recommendations))
