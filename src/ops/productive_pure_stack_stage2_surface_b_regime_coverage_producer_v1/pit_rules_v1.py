"""Point-in-time / no-lookahead rules for Surface-B regime-coverage producer v1."""

from __future__ import annotations

from typing import Sequence

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
    RegimeCoverageProducerErrorV1,
)


def assert_bucket_open_event_time(event_time_epoch_s: int) -> int:
    if int(event_time_epoch_s) < 0:
        raise RegimeCoverageProducerErrorV1("INVALID_EVENT_TIME_NEGATIVE")
    bucket = (int(event_time_epoch_s) // C.PT1M_SECONDS) * C.PT1M_SECONDS
    if int(event_time_epoch_s) != bucket:
        raise RegimeCoverageProducerErrorV1("EVENT_TIME_MUST_BE_BUCKET_OPEN")
    return bucket


def assert_pit_no_lookahead_v1(
    bars: Sequence[RegimeCoverageBarInputV1],
    *,
    as_of_event_time_epoch_s: int,
) -> None:
    """Reject any observation strictly after the exclusive as-of tip."""
    as_of = assert_bucket_open_event_time(as_of_event_time_epoch_s)
    for bar in bars:
        et = assert_bucket_open_event_time(bar.event_time_epoch_s)
        if et > as_of:
            raise RegimeCoverageProducerErrorV1(f"LOOKAHEAD_FORBIDDEN:{et}>{as_of}")
        if not bar.finalized:
            raise RegimeCoverageProducerErrorV1(f"UNFINALIZED_BAR_FORBIDDEN:{et}")


def assert_chronological_unique_buckets(
    bars: Sequence[RegimeCoverageBarInputV1],
) -> None:
    seen: set[int] = set()
    previous: int | None = None
    for bar in bars:
        et = assert_bucket_open_event_time(bar.event_time_epoch_s)
        if et in seen:
            raise RegimeCoverageProducerErrorV1(f"DUPLICATE_EVENT_TIME:{et}")
        if previous is not None and et < previous:
            raise RegimeCoverageProducerErrorV1("BARS_NOT_CHRONOLOGICAL")
        seen.add(et)
        previous = et
