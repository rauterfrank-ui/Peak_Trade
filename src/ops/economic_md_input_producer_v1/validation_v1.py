"""Fail-closed MVR raw-input validation. No ranking, no score, no fill."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    MARK_ENDPOINT_PATH,
    MARK_SOURCE_CLASS,
    MINIMUM_FINALIZED_PT1M_MARKS,
    NOT_OBSERVED,
    PT1M_STEP_MS,
    TICKER_ENDPOINT_PATH,
    TICKER_SOURCE_CLASS,
    UNRESOLVED_COLLECTION_SKEW,
    UNRESOLVED_LOCKED_MARKET,
    UNRESOLVED_NEAR_ZERO_SPREAD,
    UNRESOLVED_STALE_SECONDS,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    FinalizedPt1mMarkObservationV1,
    SameCycleTickerObservationV1,
    UnresolvedValidityDimensionsV1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1


def _parse_positive_decimal(raw: str | None) -> Optional[Decimal]:
    if raw is None or not str(raw).strip():
        return None
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError):
        return None
    return value


def _parse_ts_ms(raw: str) -> Optional[int]:
    text = str(raw or "").strip()
    if not text.isdigit():
        return None
    value = int(text)
    return value if value > 0 else None


def classify_unresolved_validity_v1(
    *,
    bid: Optional[Decimal],
    ask: Optional[Decimal],
) -> UnresolvedValidityDimensionsV1:
    locked = NOT_OBSERVED
    if bid is not None and ask is not None and bid > 0 and ask > 0 and bid == ask:
        locked = UNRESOLVED_LOCKED_MARKET
    return UnresolvedValidityDimensionsV1(
        locked_market=locked,
        near_zero_spread=UNRESOLVED_NEAR_ZERO_SPREAD,
        stale_seconds=UNRESOLVED_STALE_SECONDS,
        collection_skew=UNRESOLVED_COLLECTION_SKEW,
    )


def select_finalized_contiguous_pt1m_marks_v1(
    marks: tuple[RawMarkCandleV1, ...],
) -> tuple[tuple[FinalizedPt1mMarkObservationV1, ...], tuple[str, ...]]:
    if not marks:
        return (), (EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,)
    parsed: list[tuple[int, RawMarkCandleV1]] = []
    for row in marks:
        ts = _parse_ts_ms(row.ts_ms)
        px = _parse_positive_decimal(row.mark_px)
        if ts is None or px is None or px <= 0:
            return (), (EconomicMdFailureCodeV1.INVALID_MARK_PRICE.value,)
        if str(row.confirm).strip() != "1":
            continue
        parsed.append((ts, row))
    if any(str(row.confirm).strip() != "1" for row in marks) and not parsed:
        return (), (EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value,)
    by_ts: dict[int, RawMarkCandleV1] = {}
    for ts, row in parsed:
        existing = by_ts.get(ts)
        if existing is not None and (
            existing.mark_px != row.mark_px or existing.confirm != row.confirm
        ):
            return (), (EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value,)
        by_ts[ts] = row
    ordered_ts = sorted(by_ts)
    if len(ordered_ts) < MINIMUM_FINALIZED_PT1M_MARKS:
        if any(str(row.confirm).strip() != "1" for row in marks):
            return (), (EconomicMdFailureCodeV1.NON_FINALIZED_MARK.value,)
        return (), (EconomicMdFailureCodeV1.INSUFFICIENT_FINALIZED_PT1M_MARKS.value,)
    trailing = ordered_ts[-MINIMUM_FINALIZED_PT1M_MARKS:]
    for prev, cur in zip(trailing, trailing[1:]):
        if cur - prev != PT1M_STEP_MS:
            return (), (EconomicMdFailureCodeV1.MISSING_MARK_BAR_NO_IMPLICIT_FILL.value,)
    selected = tuple(
        FinalizedPt1mMarkObservationV1(
            mark_px=by_ts[ts].mark_px,
            event_timestamp=str(ts),
            receive_or_capture_timestamp=by_ts[ts].receive_or_capture_timestamp,
            finalization_status="FINALIZED",
            source_class=by_ts[ts].source_class or MARK_SOURCE_CLASS,
            source_endpoint=by_ts[ts].source_endpoint or MARK_ENDPOINT_PATH,
        )
        for ts in trailing
    )
    return selected, ()


def validate_ticker_quotes_v1(
    bundle: InstrumentPublicMdBundleV1,
) -> tuple[Optional[SameCycleTickerObservationV1], tuple[str, ...]]:
    ticker = bundle.ticker
    if ticker is None:
        return None, (EconomicMdFailureCodeV1.MISSING_BIDPX.value,)
    observation = SameCycleTickerObservationV1(
        bid_px=str(ticker.bid_px),
        ask_px=str(ticker.ask_px),
        ticker_event_timestamp=ticker.ticker_event_timestamp,
        capture_or_receive_timestamp=ticker.capture_or_receive_timestamp,
        source_class=ticker.source_class or TICKER_SOURCE_CLASS,
        source_endpoint=ticker.source_endpoint or TICKER_ENDPOINT_PATH,
    )
    reasons: list[str] = []
    if ticker.bid_px in (None, ""):
        reasons.append(EconomicMdFailureCodeV1.MISSING_BIDPX.value)
    if ticker.ask_px in (None, ""):
        reasons.append(EconomicMdFailureCodeV1.MISSING_ASKPX.value)
    bid = _parse_positive_decimal(ticker.bid_px)
    ask = _parse_positive_decimal(ticker.ask_px)
    if ticker.bid_px not in (None, "") and (bid is None or bid <= 0):
        reasons.append(EconomicMdFailureCodeV1.NON_POSITIVE_BIDPX.value)
    if ticker.ask_px not in (None, "") and (ask is None or ask <= 0):
        reasons.append(EconomicMdFailureCodeV1.NON_POSITIVE_ASKPX.value)
    if bid is not None and ask is not None and bid > 0 and ask > 0 and bid > ask:
        reasons.append(EconomicMdFailureCodeV1.CROSSED_MARKET_BID_GT_ASK.value)
    persistable = ticker.bid_px not in (None, "") and ticker.ask_px not in (None, "")
    return (observation if persistable else None), tuple(reasons)
