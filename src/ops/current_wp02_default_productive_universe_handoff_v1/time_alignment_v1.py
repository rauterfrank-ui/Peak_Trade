"""Align Cap21 source_event_time with producer_observed_at_unix (cadence/restart semantics)."""

from __future__ import annotations

import time


def producer_observed_at_unix_from_source_event_v1(
    source_event_time: str,
    *,
    fallback_unix: float | None = None,
) -> float:
    raw = str(source_event_time or "").strip()
    if raw.isdigit():
        ms = int(raw)
        if ms <= 0:
            return fallback_unix if fallback_unix is not None else time.time()
        return ms / 1000.0 if ms > 10_000_000_000 else float(ms)
    return fallback_unix if fallback_unix is not None else time.time()
