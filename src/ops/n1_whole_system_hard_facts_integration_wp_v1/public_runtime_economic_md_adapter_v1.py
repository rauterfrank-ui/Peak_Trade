"""Bridge durable public-runtime facts → Economic-MD raw input (real observation path)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.peak_trade_public_market_data_runtime_v1.historical_query_v1 import (
    query_historical_facts_v1,
)


@dataclass(frozen=True)
class PublicRuntimeEconomicMdPublicSourceV1:
    """Reads finalized public facts from a public MD runtime store (no www fallback)."""

    store_root: Path
    default_capture_timestamp: str = "2026-09-26T00:00:00Z"

    def collect_instrument_raw_input_v1(
        self, *, venue_native_id: str
    ) -> InstrumentPublicMdBundleV1:
        hist = query_historical_facts_v1(self.store_root)
        marks: list[RawMarkCandleV1] = []
        ticker: RawTickerQuoteV1 | None = None
        for fact in hist.facts:
            inst = fact.get("instrument") if isinstance(fact, dict) else None
            vid = str((inst or {}).get("venue_native_id") or "")
            if vid != venue_native_id:
                continue
            kind = str(fact.get("fact_kind") or "")
            if kind == "FinalizedPt1mMarkFactV1":
                marks.append(
                    RawMarkCandleV1(
                        venue_native_id=venue_native_id,
                        ts_ms=str(fact.get("interval_start_ms") or ""),
                        mark_px=str(fact.get("mark_px") or ""),
                        confirm=str(fact.get("confirm") or "1"),
                        receive_or_capture_timestamp=str(
                            fact.get("captured_at") or self.default_capture_timestamp
                        ),
                    )
                )
            elif kind == "BestBidAskFactV1" and ticker is None:
                bids = fact.get("bids") or []
                asks = fact.get("asks") or []
                bid_px = str(bids[0][0]) if bids else None
                ask_px = str(asks[0][0]) if asks else None
                ticker = RawTickerQuoteV1(
                    venue_native_id=venue_native_id,
                    bid_px=bid_px,
                    ask_px=ask_px,
                    ticker_event_timestamp=str(fact.get("ts") or ""),
                    capture_or_receive_timestamp=str(
                        fact.get("captured_at") or self.default_capture_timestamp
                    ),
                )
            elif kind == "MarkPriceFactV1" and not marks:
                ticker = RawTickerQuoteV1(
                    venue_native_id=venue_native_id,
                    bid_px=None,
                    ask_px=None,
                    ticker_event_timestamp=str(fact.get("ts") or ""),
                    capture_or_receive_timestamp=str(
                        fact.get("captured_at") or self.default_capture_timestamp
                    ),
                )
        if not marks:
            return InstrumentPublicMdBundleV1(
                venue_native_id=venue_native_id,
                marks=(),
                ticker=ticker,
                failure_codes=(EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,),
            )
        marks.sort(key=lambda m: int(m.ts_ms))
        return InstrumentPublicMdBundleV1(
            venue_native_id=venue_native_id,
            marks=tuple(marks),
            ticker=ticker,
            failure_codes=(),
        )
