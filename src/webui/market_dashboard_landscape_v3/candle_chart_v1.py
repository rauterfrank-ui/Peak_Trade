"""Fresh PT1M mark-price chart state (EEA public-MD semantics, no V2 digest)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ChartCandleV1:
    interval_start_ms: int
    open: float
    high: float
    low: float
    close: float
    finalized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts_ms": self.interval_start_ms,
            "o": self.open,
            "h": self.high,
            "l": self.low,
            "c": self.close,
            "finalized": self.finalized,
        }


@dataclass
class LandscapeV3ChartStateV1:
    venue_native_id: str
    candles: list[ChartCandleV1] = field(default_factory=list)
    sequence: int = 0

    def reset_for_instrument(self, venue_native_id: str) -> None:
        self.venue_native_id = venue_native_id
        self.candles = []
        self.sequence = 0

    def bootstrap_from_finalized_rows(
        self, rows: Sequence[Mapping[str, Any]], *, open_candle: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Load historical finalized PT1M marks; optional open candle overlay."""
        self.candles = []
        for row in sorted(rows, key=lambda r: int(r["interval_start_ms"])):
            px = float(row["mark_px"])
            self.candles.append(
                ChartCandleV1(
                    interval_start_ms=int(row["interval_start_ms"]),
                    open=px,
                    high=px,
                    low=px,
                    close=px,
                    finalized=True,
                )
            )
        events: list[dict[str, Any]] = []
        if open_candle is not None:
            events.extend(self.apply_live_mark(open_candle))
        else:
            self.sequence += 1
            events.append(self._snapshot_event("bootstrap"))
        return events

    def apply_live_mark(self, mark: Mapping[str, Any]) -> list[dict[str, Any]]:
        ts_ms = int(mark["interval_start_ms"])
        px = float(mark["mark_px"])
        finalized = str(mark.get("confirm", "0")) == "1"
        events: list[dict[str, Any]] = []
        if self.candles and self.candles[-1].interval_start_ms == ts_ms:
            last = self.candles[-1]
            if finalized and not last.finalized:
                updated = ChartCandleV1(
                    interval_start_ms=ts_ms,
                    open=last.open,
                    high=max(last.high, px),
                    low=min(last.low, px),
                    close=px,
                    finalized=True,
                )
                self.candles[-1] = updated
                self.sequence += 1
                events.append(
                    {
                        "chart_event": "finalize_candle",
                        "sequence": self.sequence,
                        "candle": updated.to_dict(),
                    }
                )
            elif not last.finalized:
                updated = ChartCandleV1(
                    interval_start_ms=ts_ms,
                    open=last.open,
                    high=max(last.high, px),
                    low=min(last.low, px),
                    close=px,
                    finalized=False,
                )
                self.candles[-1] = updated
                self.sequence += 1
                events.append(
                    {
                        "chart_event": "revise_open_candle",
                        "sequence": self.sequence,
                        "candle": updated.to_dict(),
                    }
                )
            return events
        if self.candles and ts_ms < self.candles[-1].interval_start_ms:
            self.sequence += 1
            events.append(
                {
                    "chart_event": "out_of_order_ignored",
                    "sequence": self.sequence,
                    "ts_ms": ts_ms,
                }
            )
            return events
        if self.candles and self.candles[-1].interval_start_ms == ts_ms - 60_000:
            prev = self.candles[-1]
            if not prev.finalized:
                self.candles[-1] = ChartCandleV1(
                    interval_start_ms=prev.interval_start_ms,
                    open=prev.open,
                    high=prev.high,
                    low=prev.low,
                    close=prev.close,
                    finalized=True,
                )
        open_px = px if not self.candles else self.candles[-1].close
        new = ChartCandleV1(
            interval_start_ms=ts_ms,
            open=open_px,
            high=max(open_px, px),
            low=min(open_px, px),
            close=px,
            finalized=finalized,
        )
        if self.candles and self.candles[-1].interval_start_ms == ts_ms:
            self.candles[-1] = new
        else:
            self.candles.append(new)
        self.sequence += 1
        kind = "append_finalized_candle" if finalized else "open_candle"
        events.append(
            {
                "chart_event": kind,
                "sequence": self.sequence,
                "candle": new.to_dict(),
            }
        )
        return events

    def candles_payload_v1(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.candles]

    def _snapshot_event(self, reason: str) -> dict[str, Any]:
        return {
            "chart_event": "snapshot",
            "sequence": self.sequence,
            "reason": reason,
            "candles": self.candles_payload_v1(),
        }


def pt1m_rows_from_rest_history(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Map EEA mark-history REST rows to interval_start_ms + mark_px."""
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, list) or len(item) < 5:
            continue
        confirm = str(item[5] if len(item) > 5 else item[-1])
        rows.append(
            {
                "interval_start_ms": int(str(item[0])),
                "mark_px": str(item[4]),
                "confirm": confirm,
            }
        )
    return rows


def ticker_to_open_mark_v1(
    ticker_row: Mapping[str, Any], *, interval_start_ms: int
) -> dict[str, Any]:
    px = ticker_row.get("last") or ticker_row.get("markPx") or ticker_row.get("idxPx")
    return {
        "interval_start_ms": interval_start_ms,
        "mark_px": str(px),
        "confirm": "0",
    }
