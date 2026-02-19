"""
Live Data Quality Checks - WP1A

Additional quality checks for live data:
- Timestamp monotonicity
- Missing bar detection
- Gap detection
- Staleness detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.data.shadow.models import Bar, Tick

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """
    Quality issue detected in live data.

    Attributes:
        kind: Issue type (e.g., "NON_MONOTONIC", "MISSING_BAR", "STALE")
        severity: "INFO" | "WARN" | "BLOCK"
        ts_ms: Timestamp of issue
        symbol: Symbol
        details: Additional details
    """

    kind: str
    severity: str
    ts_ms: int
    symbol: str
    details: dict

    def __str__(self) -> str:
        return f"[{self.severity}] {self.kind} @ {self.ts_ms}: {self.symbol} - {self.details}"


class LiveQualityChecker:
    """
    Quality checker for live data streams.

    Validates:
    - Timestamp monotonicity (within symbol)
    - Missing bars (gaps)
    - Staleness (no data for N seconds)

    Usage:
        >>> checker = LiveQualityChecker()
        >>> for tick in ticks:
        ...     issues = checker.check_tick(tick)
        ...     for issue in issues:
        ...         print(issue)
    """

    def __init__(
        self,
        stale_threshold_ms: int = 10_000,  # 10 seconds
    ):
        """
        Args:
            stale_threshold_ms: Threshold for staleness detection (ms)
        """
        self.stale_threshold_ms = stale_threshold_ms

        # Track last timestamp per symbol
        self._last_tick_ts: dict[str, int] = {}
        self._last_bar_ts: dict[str, int] = {}

        # Stats
        self._issues_found = 0

    def check_tick(self, tick: Tick) -> list[QualityIssue]:
        """
        Check tick quality.

        Args:
            tick: Tick to check

        Returns:
            List of quality issues
        """
        issues = []

        symbol = tick.symbol

        # Check monotonicity
        if symbol in self._last_tick_ts:
            last_ts = self._last_tick_ts[symbol]

            if tick.ts_ms < last_ts:
                # Non-monotonic tick
                issue = QualityIssue(
                    kind="NON_MONOTONIC_TICK",
                    severity="WARN",
                    ts_ms=tick.ts_ms,
                    symbol=symbol,
                    details={
                        "current_ts_ms": tick.ts_ms,
                        "last_ts_ms": last_ts,
                        "diff_ms": tick.ts_ms - last_ts,
                    },
                )
                issues.append(issue)
                self._issues_found += 1
                logger.warning(str(issue))

        # Update last timestamp
        self._last_tick_ts[symbol] = tick.ts_ms

        return issues

    def check_bar(
        self,
        bar: Bar,
        timeframe_ms: Optional[int] = None,
    ) -> list[QualityIssue]:
        """
        Check bar quality.

        Args:
            bar: Bar to check
            timeframe_ms: Expected timeframe (for gap detection)

        Returns:
            List of quality issues
        """
        issues = []

        symbol = bar.symbol

        # Check monotonicity
        if symbol in self._last_bar_ts:
            last_ts = self._last_bar_ts[symbol]

            if bar.start_ts_ms < last_ts:
                # Non-monotonic bar
                issue = QualityIssue(
                    kind="NON_MONOTONIC_BAR",
                    severity="WARN",
                    ts_ms=bar.start_ts_ms,
                    symbol=symbol,
                    details={
                        "current_start_ts_ms": bar.start_ts_ms,
                        "last_start_ts_ms": last_ts,
                        "diff_ms": bar.start_ts_ms - last_ts,
                    },
                )
                issues.append(issue)
                self._issues_found += 1
                logger.warning(str(issue))

            # Check for gap (if timeframe provided)
            if timeframe_ms:
                expected_next_start = last_ts + timeframe_ms
                actual_start = bar.start_ts_ms

                if actual_start != expected_next_start:
                    # Gap detected
                    missing_bars = (actual_start - expected_next_start) // timeframe_ms

                    severity = "WARN" if missing_bars < 5 else "BLOCK"

                    issue = QualityIssue(
                        kind="MISSING_BAR",
                        severity=severity,
                        ts_ms=bar.start_ts_ms,
                        symbol=symbol,
                        details={
                            "expected_start_ms": expected_next_start,
                            "actual_start_ms": actual_start,
                            "missing_bars": int(missing_bars),
                        },
                    )
                    issues.append(issue)
                    self._issues_found += 1
                    logger.warning(str(issue))

        # Update last timestamp
        self._last_bar_ts[symbol] = bar.start_ts_ms

        return issues

    def check_staleness(
        self,
        current_ts_ms: int,
        symbol: str,
    ) -> Optional[QualityIssue]:
        """
        Check if data for a symbol is stale.

        Args:
            current_ts_ms: Current timestamp (ms)
            symbol: Symbol to check

        Returns:
            QualityIssue if stale, None otherwise
        """
        if symbol not in self._last_tick_ts:
            return None

        last_ts = self._last_tick_ts[symbol]
        staleness_ms = current_ts_ms - last_ts

        if staleness_ms > self.stale_threshold_ms:
            issue = QualityIssue(
                kind="STALE_DATA",
                severity="WARN",
                ts_ms=current_ts_ms,
                symbol=symbol,
                details={
                    "last_ts_ms": last_ts,
                    "staleness_ms": staleness_ms,
                    "threshold_ms": self.stale_threshold_ms,
                },
            )
            self._issues_found += 1
            logger.warning(str(issue))
            return issue

        return None

    def get_stats(self) -> dict:
        """Get checker statistics."""
        return {
            "issues_found": self._issues_found,
            "symbols_tracked": len(self._last_tick_ts),
        }

    def reset(self) -> None:
        """Reset checker state."""
        self._last_tick_ts.clear()
        self._last_bar_ts.clear()
        self._issues_found = 0


def run_live_quality_checks(
    *,
    asof_utc: str,
    context: dict,
) -> tuple[bool, dict]:
    """Run live quality checks for gate evaluation.

    Stub: returns (True, {}) when no issues. Can be extended to use
    LiveQualityChecker state or external staleness/gap checks.

    Args:
        asof_utc: Evaluation timestamp (ISO UTC)
        context: Optional context (symbols, timeframes, etc.)

    Returns:
        (ok, extra): ok=True if checks pass, extra dict with details
    """
    return True, {"asof_utc": asof_utc}
