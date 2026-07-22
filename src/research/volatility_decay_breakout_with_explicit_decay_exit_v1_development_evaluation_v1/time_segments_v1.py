"""CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1 segment partition.

Implements the preregistered measurement-contract definition only. Does not invent
thresholds or mutate the illustrative 60/20/20 split. Identical semantics to VEP/VDB.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_development_evaluation_v1.constants_v1 import (
    BAR_FREQUENCY,
    DEVELOPMENT_END_EXCLUSIVE,
    DEVELOPMENT_START,
    TIME_SEGMENT_COUNT,
    TIME_SEGMENT_DEFINITION_ID,
    TIME_SEGMENT_IDS,
)


class TimeSegmentError(ValueError):
    """Fail-closed time-segment partition error."""


@dataclass(frozen=True)
class TimeSegmentV1:
    segment_id: str
    index: int
    start_inclusive: str
    end_exclusive: str
    bar_count: int


def _parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def _ceil_to_hour(dt: datetime) -> datetime:
    floored = _floor_to_hour(dt)
    if floored == dt:
        return floored
    return floored + timedelta(hours=1)


def build_canonical_pt1h_bar_starts(
    *,
    start: str = DEVELOPMENT_START,
    end_exclusive: str = DEVELOPMENT_END_EXCLUSIVE,
) -> tuple[datetime, ...]:
    """Canonical PT1H bar-start grid covering [ceil(start), floor(end_exclusive))."""
    if BAR_FREQUENCY != "PT1H":
        raise TimeSegmentError("UNSUPPORTED_BAR_FREQUENCY")
    start_dt = _ceil_to_hour(_parse_utc(start))
    end_dt = _floor_to_hour(_parse_utc(end_exclusive))
    if end_dt <= start_dt:
        raise TimeSegmentError("EMPTY_DEVELOPMENT_PERIOD")
    bars: list[datetime] = []
    cursor = start_dt
    while cursor < end_dt:
        bars.append(cursor)
        cursor += timedelta(hours=1)
    if not bars:
        raise TimeSegmentError("NO_CANONICAL_BARS")
    return tuple(bars)


def partition_chronological_equal_duration_quarters_v1(
    bar_starts: Sequence[datetime] | None = None,
    *,
    start: str = DEVELOPMENT_START,
    end_exclusive: str = DEVELOPMENT_END_EXCLUSIVE,
) -> tuple[TimeSegmentV1, ...]:
    """Partition DEVELOPMENT bars into exactly four chronological equal-duration quarters.

    Remainder rule (preregistered): if total bars are not divisible by four, assign
    remaining bars deterministically to the earliest segments (at most one extra each).
    Denominator remains 4; non-evaluable segments are not removed.
    """
    if TIME_SEGMENT_DEFINITION_ID != "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1":
        raise TimeSegmentError("UNEXPECTED_TIME_SEGMENT_DEFINITION_ID")
    bars = (
        list(bar_starts)
        if bar_starts is not None
        else list(build_canonical_pt1h_bar_starts(start=start, end_exclusive=end_exclusive))
    )
    n = len(bars)
    if n < TIME_SEGMENT_COUNT:
        raise TimeSegmentError("INSUFFICIENT_BARS_FOR_FOUR_SEGMENTS")

    base = n // TIME_SEGMENT_COUNT
    remainder = n % TIME_SEGMENT_COUNT
    segments: list[TimeSegmentV1] = []
    cursor = 0
    for i in range(TIME_SEGMENT_COUNT):
        extra = 1 if i < remainder else 0
        count = base + extra
        if count <= 0:
            raise TimeSegmentError("NON_POSITIVE_SEGMENT_LENGTH")
        seg_bars = bars[cursor : cursor + count]
        segments.append(
            TimeSegmentV1(
                segment_id=TIME_SEGMENT_IDS[i],
                index=i + 1,
                start_inclusive=_fmt_utc(seg_bars[0]),
                end_exclusive=_fmt_utc(seg_bars[-1] + timedelta(hours=1)),
                bar_count=count,
            )
        )
        cursor += count
    if cursor != n:
        raise TimeSegmentError("SEGMENT_COVERAGE_DRIFT")
    if len(segments) != TIME_SEGMENT_COUNT:
        raise TimeSegmentError("SEGMENT_COUNT_DRIFT")
    return tuple(segments)


def assign_timestamp_to_segment(
    timestamp_utc: str, segments: Sequence[TimeSegmentV1]
) -> str | None:
    ts = _parse_utc(timestamp_utc)
    for segment in segments:
        start = _parse_utc(segment.start_inclusive)
        end = _parse_utc(segment.end_exclusive)
        if start <= ts < end:
            return segment.segment_id
    return None


def segments_to_dict(segments: Sequence[TimeSegmentV1]) -> list[dict[str, object]]:
    return [
        {
            "segment_id": s.segment_id,
            "index": s.index,
            "start_inclusive": s.start_inclusive,
            "end_exclusive": s.end_exclusive,
            "bar_count": s.bar_count,
            "range": f"{s.start_inclusive}..{s.end_exclusive}",
        }
        for s in segments
    ]
