"""Dedicated PT1M finalized-OHLCV shadow-calibration producer (Authority Surface B).

O4 remains unchanged. Dashboard/read-model surfaces are not source authority.
Venue candles are raw OHLCV input only; mark_price is a required separate field.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false,
    assert_source_not_forbidden,
)
from src.ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1.models_v1 import (
    InputAuthorityErrorV1,
    InstrumentBindingV1,
    MarkPriceInputV1,
    ProducedFinalizedBarV1,
    VenueNativeCandleInputV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)


def validate_instrument_binding(binding: InstrumentBindingV1) -> None:
    for field in C.REQUIRED_INSTRUMENT_FIELDS:
        value = getattr(binding, field, None)
        if not isinstance(value, str) or not value.strip():
            raise InputAuthorityErrorV1(f"INSTRUMENT_BINDING_INCOMPLETE:{field}")


def _bucket_open(event_time_epoch_s: int) -> int:
    if event_time_epoch_s < 0:
        raise InputAuthorityErrorV1("INVALID_EVENT_TIME_NEGATIVE")
    return (int(event_time_epoch_s) // C.PT1M_SECONDS) * C.PT1M_SECONDS


def _assert_ohlcv_sane(candle: VenueNativeCandleInputV1) -> None:
    for name in ("open", "high", "low", "close", "volume"):
        value = getattr(candle, name)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InputAuthorityErrorV1(f"OHLCV_TYPE_INVALID:{name}")
        if name != "volume" and float(value) <= 0:
            raise InputAuthorityErrorV1(f"OHLCV_NONPOSITIVE:{name}")
        if name == "volume" and float(value) < 0:
            raise InputAuthorityErrorV1("OHLCV_VOLUME_NEGATIVE")
    if float(candle.high) < float(candle.low):
        raise InputAuthorityErrorV1("OHLCV_HIGH_LT_LOW")
    if not (float(candle.low) <= float(candle.open) <= float(candle.high)):
        raise InputAuthorityErrorV1("OHLCV_OPEN_OUT_OF_RANGE")
    if not (float(candle.low) <= float(candle.close) <= float(candle.high)):
        raise InputAuthorityErrorV1("OHLCV_CLOSE_OUT_OF_RANGE")


def produce_pt1m_finalized_ohlcv_bars_v1(
    *,
    binding: InstrumentBindingV1,
    dataset_id: str,
    candles: Sequence[VenueNativeCandleInputV1],
    marks: Sequence[MarkPriceInputV1],
    allow_candle_mark_equivalence: bool = False,
    revisions: Mapping[int, int] | None = None,
) -> tuple[ProducedFinalizedBarV1, ...]:
    """Produce finalized PT1M bars under Surface B.

    Fail closed on open tips, unfinalized venue candles, missing marks,
    multi-instrument pooling attempts, and candle/mark/trade equivalence.
    """
    assert_forbidden_effects_remain_false()
    assert_source_not_forbidden(C.SOURCE_ID)
    validate_instrument_binding(binding)
    if allow_candle_mark_equivalence:
        raise InputAuthorityErrorV1("CANDLE_MARK_TRADE_EQUIVALENCE_FORBIDDEN")
    if not dataset_id or not str(dataset_id).strip():
        raise InputAuthorityErrorV1("DATASET_ID_REQUIRED")
    if not candles:
        raise InputAuthorityErrorV1("CANDLES_REQUIRED")
    if not marks:
        raise InputAuthorityErrorV1("MARKS_REQUIRED")

    mark_by_bucket: dict[int, MarkPriceInputV1] = {}
    for mark in marks:
        if float(mark.mark_price) <= 0:
            raise InputAuthorityErrorV1("MARK_PRICE_NONPOSITIVE")
        bucket = _bucket_open(int(mark.event_time_epoch_s))
        if bucket in mark_by_bucket:
            raise InputAuthorityErrorV1(f"DUPLICATE_MARK_BUCKET:{bucket}")
        mark_by_bucket[bucket] = mark

    produced: list[ProducedFinalizedBarV1] = []
    seen_buckets: set[int] = set()
    for candle in candles:
        if candle.open_tip:
            raise InputAuthorityErrorV1("OPEN_TIP_BARS_FORBIDDEN")
        if not candle.venue_finalized:
            raise InputAuthorityErrorV1("VENUE_CANDLE_NOT_FINALIZED")
        _assert_ohlcv_sane(candle)
        bucket = _bucket_open(int(candle.event_time_epoch_s))
        # Final only after event-time bucket is closed: candle event time must be
        # the bucket open (canonical bar identity) and venue_finalized confirmed.
        if int(candle.event_time_epoch_s) != bucket:
            raise InputAuthorityErrorV1("EVENT_TIME_MUST_BE_BUCKET_OPEN")
        if bucket in seen_buckets:
            raise InputAuthorityErrorV1(f"DUPLICATE_CANDLE_BUCKET:{bucket}")
        seen_buckets.add(bucket)
        mark = mark_by_bucket.get(bucket)
        if mark is None:
            raise InputAuthorityErrorV1(f"MARK_MISSING_FOR_BUCKET:{bucket}")
        # Equivalence of candle close and mark is not automatic authority; it is
        # allowed as coincident market values but never as a substitution policy.
        # Explicit substitution attempts are rejected via allow flag above.
        revision = int((revisions or {}).get(bucket, 0))
        produced.append(
            ProducedFinalizedBarV1(
                instrument_id=binding.canonical_instrument_id,
                event_time_epoch_s=bucket,
                open=float(candle.open),
                high=float(candle.high),
                low=float(candle.low),
                close=float(candle.close),
                mark_price=float(mark.mark_price),
                volume=float(candle.volume),
                finalized=True,
                dataset_id=str(dataset_id),
                source_id=C.SOURCE_ID,
                venue=binding.venue,
                revision=revision,
            )
        )

    produced.sort(key=lambda b: b.event_time_epoch_s)
    # Single instrument continuity: all bars share canonical id (enforced above).
    raw_digest = digest_mapping(
        {
            "candles": [
                {
                    "event_time_epoch_s": c.event_time_epoch_s,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                    "venue_finalized": c.venue_finalized,
                    "open_tip": c.open_tip,
                }
                for c in candles
            ],
            "marks": [
                {"event_time_epoch_s": m.event_time_epoch_s, "mark_price": m.mark_price}
                for m in marks
            ],
            "binding": binding.to_dict(),
            "dataset_id": dataset_id,
        }
    )
    # Attach digest for callers via attribute on tuple is awkward; return bars only.
    # raw digest is recomputed by observation pack builder from inputs.
    _ = raw_digest
    return tuple(produced)


def compute_raw_source_digest_v1(
    *,
    binding: InstrumentBindingV1,
    dataset_id: str,
    candles: Sequence[VenueNativeCandleInputV1],
    marks: Sequence[MarkPriceInputV1],
) -> str:
    return digest_mapping(
        {
            "candles": [
                {
                    "event_time_epoch_s": c.event_time_epoch_s,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                    "venue_finalized": c.venue_finalized,
                    "open_tip": c.open_tip,
                }
                for c in candles
            ],
            "marks": [
                {"event_time_epoch_s": m.event_time_epoch_s, "mark_price": m.mark_price}
                for m in marks
            ],
            "binding": binding.to_dict(),
            "dataset_id": dataset_id,
            "ohlcv_source": C.OHLCV_SOURCE,
            "mark_price_policy": C.MARK_PRICE_POLICY,
        }
    )
