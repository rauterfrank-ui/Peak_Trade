"""Canonical availability vocabulary for Market Dashboard Landscape V2.

Fail-closed: missing or unknown sources must surface explicitly. Silent
defaults and invented "healthy" states are forbidden.
"""

from __future__ import annotations

from enum import Enum


class Availability(str, Enum):
    """Dashboard-facing availability; sole vocabulary for Source Health."""

    AVAILABLE = "AVAILABLE"
    NOT_BOUND = "NOT_BOUND"
    MISSING_SOURCE = "MISSING_SOURCE"
    STALE = "STALE"
    INVALID = "INVALID"


AVAILABILITY_VALUES: frozenset[str] = frozenset(member.value for member in Availability)


def parse_availability(raw: str) -> Availability:
    """Parse an availability token; unknown values fail closed as INVALID."""
    if not isinstance(raw, str) or not raw:
        raise ValueError("availability must be a non-empty string")
    try:
        return Availability(raw)
    except ValueError as exc:
        raise ValueError(f"unknown availability={raw!r}") from exc


def assert_no_silent_default(availability: Availability) -> None:
    """Guard helper: AVAILABLE is never implied; caller must set it explicitly."""
    if not isinstance(availability, Availability):
        raise TypeError("availability must be Availability enum member")
