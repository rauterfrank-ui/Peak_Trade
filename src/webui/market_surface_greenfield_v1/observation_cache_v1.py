"""Presentation-only TTL cache for non-market aggregate slices (read-only surface)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from .contracts_v1 import SYSTEM_INSTRUMENTS_CACHE_SECONDS


@dataclass
class _CacheEntry:
    payload: dict[str, Any]
    monotonic_saved_at: float


_SYSTEM_SLICE_CACHE: _CacheEntry | None = None


async def get_or_refresh_system_slice(
    *,
    builder: Callable[[], Awaitable[dict[str, Any]]],
    ttl_seconds: float = SYSTEM_INSTRUMENTS_CACHE_SECONDS,
    force: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Return cached system-side instrumentation unless TTL expired."""
    global _SYSTEM_SLICE_CACHE
    now = time.monotonic()
    if (
        not force
        and _SYSTEM_SLICE_CACHE is not None
        and (now - _SYSTEM_SLICE_CACHE.monotonic_saved_at) < ttl_seconds
    ):
        return dict(_SYSTEM_SLICE_CACHE.payload), True
    payload = await builder()
    _SYSTEM_SLICE_CACHE = _CacheEntry(payload=payload, monotonic_saved_at=now)
    return payload, False
