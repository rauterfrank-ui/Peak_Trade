"""
Data Quality Monitor — Gap Detection + Spike Alerts.

Prüft OHLCV Bars auf Qualitätsprobleme (fehlende Bars, Preis-/Volume-Spikes).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Union

from src.data.shadow.models import Bar


@dataclass(frozen=True)
class QualityEvent:
    """
    Quality Event (Gap oder Spike).

    Attributes:
        kind: "GAP" | "SPIKE"
        severity: "WARN" | "BLOCK"
        ts_ms: Timestamp des Events
        symbol: Symbol
        timeframe: Timeframe
        details: Zusätzliche Infos (dict)
    """

    kind: str  # "GAP" | "SPIKE"
    severity: str  # "WARN" | "BLOCK"
    ts_ms: int
    symbol: str
    timeframe: str
    details: dict[str, Any]


class DataQualityMonitor:
    """
    Überwacht Data Quality von Bars.

    Konfigurierbar via Config-Dict.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """
        Args:
            cfg: Config (nested dict)
        """
        quality_cfg = cfg.get("shadow", {}).get("quality", {})

        self.gap_severity = quality_cfg.get("gap_severity", "WARN")
        self.spike_severity = quality_cfg.get("spike_severity", "WARN")
        self.max_abs_log_return = quality_cfg.get("max_abs_log_return", 0.10)
        self.volume_spike_factor = quality_cfg.get("volume_spike_factor", 10.0)

    def check_bars(self, bars: list[Bar]) -> list[QualityEvent]:
        """
        Prüft Bars auf Gaps + Spikes.

        Args:
            bars: Liste von Bars (sollte sortiert sein nach start_ts_ms)

        Returns:
            List[QualityEvent]: Gefundene Events
        """
        events: list[QualityEvent] = []

        # Sort (sicherheitshalber)
        sorted_bars = sorted(bars, key=lambda b: b.start_ts_ms)

        if not sorted_bars:
            return events

        # Gap Detection
        gap_events = self._check_gaps(sorted_bars)
        events.extend(gap_events)

        # Spike Detection
        spike_events = self._check_spikes(sorted_bars)
        events.extend(spike_events)

        return events

    def _check_gaps(self, bars: list[Bar]) -> list[QualityEvent]:
        """Prüft auf fehlende Bars."""
        events: list[QualityEvent] = []

        if len(bars) < 2:
            return events

        # Timeframe (in ms)
        tf_ms = bars[0].end_ts_ms - bars[0].start_ts_ms

        for i in range(len(bars) - 1):
            current_bar = bars[i]
            next_bar = bars[i + 1]

            expected_next_start = current_bar.start_ts_ms + tf_ms
            actual_next_start = next_bar.start_ts_ms

            if actual_next_start != expected_next_start:
                # Gap gefunden
                missing_bars = (actual_next_start - expected_next_start) // tf_ms

                event = QualityEvent(
                    kind="GAP",
                    severity=self.gap_severity,
                    ts_ms=current_bar.start_ts_ms,
                    symbol=current_bar.symbol,
                    timeframe=current_bar.timeframe,
                    details={
                        "expected_next_start_ms": expected_next_start,
                        "actual_next_start_ms": actual_next_start,
                        "missing_bars": int(missing_bars),
                    },
                )
                events.append(event)

        return events

    def _check_spikes(self, bars: list[Bar]) -> list[QualityEvent]:
        """Prüft auf Preis-/Volume-Spikes."""
        events: list[QualityEvent] = []

        if len(bars) < 2:
            return events

        # Price Spikes (Log-Return)
        for i in range(1, len(bars)):
            prev_bar = bars[i - 1]
            curr_bar = bars[i]

            if prev_bar.close > 0 and curr_bar.close > 0:
                log_return = math.log(curr_bar.close / prev_bar.close)

                if abs(log_return) > self.max_abs_log_return:
                    event = QualityEvent(
                        kind="SPIKE",
                        severity=self.spike_severity,
                        ts_ms=curr_bar.start_ts_ms,
                        symbol=curr_bar.symbol,
                        timeframe=curr_bar.timeframe,
                        details={
                            "type": "price_spike",
                            "abs_log_return": abs(log_return),
                            "threshold": self.max_abs_log_return,
                            "prev_close": prev_bar.close,
                            "curr_close": curr_bar.close,
                        },
                    )
                    events.append(event)

        # Volume Spikes (gegen Median)
        if len(bars) >= 3:
            volumes = [b.volume for b in bars]
            median_volume = sorted(volumes)[len(volumes) // 2]

            if median_volume > 0:
                for bar in bars:
                    if bar.volume > median_volume * self.volume_spike_factor:
                        event = QualityEvent(
                            kind="SPIKE",
                            severity=self.spike_severity,
                            ts_ms=bar.start_ts_ms,
                            symbol=bar.symbol,
                            timeframe=bar.timeframe,
                            details={
                                "type": "volume_spike",
                                "volume": bar.volume,
                                "median_volume": median_volume,
                                "factor": bar.volume / median_volume,
                                "threshold_factor": self.volume_spike_factor,
                            },
                        )
                        events.append(event)

        return events
