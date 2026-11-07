"""Decision binding and acquisition age, separate from venue event/decision clocks.

No GET, retry, clock reset or authority. Consumers retain the original acquisition
time; equal response bytes alone do not prove a new acquisition.
"""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def acquisition_age_seconds_v1(*, acquired_at_utc: str, now_utc: str) -> str:
    """Conservatively round up age; reject absent, naive or future timestamps."""
    try:
        acquired = datetime.fromisoformat(acquired_at_utc.replace("Z", "+00:00"))
        now = datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
        if acquired.utcoffset() is None or now.utcoffset() is None:
            raise ValueError("NAIVE_ACQUISITION_CLOCK")
        delta = (now - acquired).total_seconds()
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("ACQUISITION_TIME_MALFORMED") from exc
    if delta < 0:
        raise ValueError("ACQUISITION_TIME_IN_FUTURE")
    if delta > NUMERIC_EQUITY_TTL_SECONDS:
        raise ValueError("ACQUISITION_STALE")
    return str(ceil(delta))
