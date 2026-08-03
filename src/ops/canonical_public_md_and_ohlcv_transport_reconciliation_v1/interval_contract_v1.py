"""Shared OHLCV interval contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    INTERVAL_1H,
    INTERVAL_PT1H,
    SUPPORTED_INTERVALS,
)


class IntervalContractErrorV1(ValueError):
    """Fail-closed interval contract violation."""


@dataclass(frozen=True)
class IntervalSpecV1:
    interval_id: str
    duration_seconds: int
    alias_of: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


INTERVAL_SPECS: dict[str, IntervalSpecV1] = {
    INTERVAL_PT1H: IntervalSpecV1(interval_id=INTERVAL_PT1H, duration_seconds=3600),
    INTERVAL_1H: IntervalSpecV1(
        interval_id=INTERVAL_1H, duration_seconds=3600, alias_of=INTERVAL_PT1H
    ),
}


def normalize_interval_id_v1(raw: str) -> str:
    token = str(raw or "").strip().upper()
    if token in {"1H", "PT1H", "60M"}:
        return INTERVAL_PT1H
    raise IntervalContractErrorV1(f"UNSUPPORTED_INTERVAL:{raw}")


def interval_duration_seconds_v1(interval_id: str) -> int:
    canonical = normalize_interval_id_v1(interval_id)
    return INTERVAL_SPECS[canonical].duration_seconds


def bar_open_close_times_v1(*, event_time: float, interval_id: str) -> tuple[float, float]:
    """Floor event_time into [open, close) using UTC epoch seconds."""
    if not isinstance(event_time, (int, float)) or isinstance(event_time, bool):
        raise IntervalContractErrorV1("INVALID_EVENT_TIME_TYPE")
    et = float(event_time)
    if et < 0:
        raise IntervalContractErrorV1("INVALID_EVENT_TIME_NEGATIVE")
    duration = interval_duration_seconds_v1(interval_id)
    open_time = float((int(et) // duration) * duration)
    close_time = open_time + float(duration)
    return open_time, close_time


def assert_same_interval_bucket_v1(
    *,
    left_event_time: float,
    right_event_time: float,
    interval_id: str,
) -> bool:
    lo, _ = bar_open_close_times_v1(event_time=left_event_time, interval_id=interval_id)
    ro, _ = bar_open_close_times_v1(event_time=right_event_time, interval_id=interval_id)
    return lo == ro


def supported_intervals_contract_v1() -> dict[str, Any]:
    return {
        "supported_intervals": sorted(SUPPORTED_INTERVALS),
        "input_aliases": {INTERVAL_1H: INTERVAL_PT1H, "60M": INTERVAL_PT1H},
        "cross_interval_contamination_forbidden": True,
    }
