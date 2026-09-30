"""Offline inject bundles for Economic-MD (tests and bounded harnesses only)."""

from __future__ import annotations

from typing import Sequence

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MINIMUM_FINALIZED_PT1M_MARKS,
    PT1M_STEP_MS,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)


def injected_economic_md_source_for_venue_native_ids_v1(
    venue_native_ids: Sequence[str],
    *,
    base_ts_ms: int = 1_757_631_540_000,
) -> InjectedEconomicMdPublicSourceV1:
    bundles: dict[str, InstrumentPublicMdBundleV1] = {}
    for vid in venue_native_ids:
        marks = tuple(
            RawMarkCandleV1(
                venue_native_id=vid,
                ts_ms=str(base_ts_ms + i * PT1M_STEP_MS),
                mark_px=str(100 + i),
                confirm="1",
                receive_or_capture_timestamp=str(base_ts_ms),
            )
            for i in range(MINIMUM_FINALIZED_PT1M_MARKS)
        )
        bundles[vid] = InstrumentPublicMdBundleV1(
            venue_native_id=vid,
            marks=marks,
            ticker=RawTickerQuoteV1(
                venue_native_id=vid,
                bid_px="99.0",
                ask_px="101.0",
                ticker_event_timestamp=str(base_ts_ms),
                capture_or_receive_timestamp=str(base_ts_ms),
            ),
        )
    return InjectedEconomicMdPublicSourceV1(bundles)
