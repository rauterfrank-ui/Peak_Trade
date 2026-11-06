"""Canonical missing-funding semantics for cross-sectional research v0.

Fail-closed: missing funding stays explicit None; synthetic zero is forbidden.
Research-only; no runtime or authority effect.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

PACKAGE_MARKER = "MISSING_FUNDING_POLICY_V0=true"
POLICY_VERSION = "missing_funding_policy.v0"

MISSING_FUNDING_VALUE: None = None
MISSING_FUNDING_IS_ZERO = False
MISSING_FUNDING_FAIL_CLOSED = True

FORBIDDEN_MISSING_FALLBACKS = frozenset({"0", "0.0", 0, 0.0, Decimal("0"), Decimal("0.0")})

MISSING_REASON_NO_PRIOR_FUNDING = "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"
MISSING_REASON_FIELD_ABSENT = "MISSING_FUNDING_FIELD_ABSENT"
MISSING_REASON_SYNTHETIC_ZERO_BLOCKED = "MISSING_FUNDING_SYNTHETIC_ZERO_BLOCKED"


def is_missing_funding_value_v0(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def reject_synthetic_zero_funding_fallback_v0(value: Any) -> None:
    """Raise when a caller attempts to treat zero as a missing-funding substitute."""
    if value in FORBIDDEN_MISSING_FALLBACKS:
        raise ValueError(MISSING_REASON_SYNTHETIC_ZERO_BLOCKED)
    if isinstance(value, str) and value.strip() in {"0", "0.0"}:
        raise ValueError(MISSING_REASON_SYNTHETIC_ZERO_BLOCKED)


def resolve_funding_rate_or_missing_v0(
    *,
    raw_value: Any,
    allow_explicit_zero: bool = True,
) -> str | None:
    """Return normalized rate string or None; never synthesize zero for missing."""
    if is_missing_funding_value_v0(raw_value):
        return MISSING_FUNDING_VALUE
    text = str(raw_value).strip()
    if not text:
        return MISSING_FUNDING_VALUE
    if not allow_explicit_zero:
        reject_synthetic_zero_funding_fallback_v0(text)
    return text


def backward_asof_funding_rate_fail_closed_v0(
    funding_rows: list[dict[str, Any]],
    bar_timestamp_ms: int,
) -> tuple[str | None, str | None]:
    """PIT lookup returning (rate_or_none, missing_reason_or_none)."""
    from src.research.cross_sectional_bounded_panel_fetch_v0 import (
        backward_asof_funding_lookup_v0,
    )

    rate = backward_asof_funding_lookup_v0(funding_rows, bar_timestamp_ms)
    if rate is None or str(rate).strip() == "":
        return MISSING_FUNDING_VALUE, MISSING_REASON_NO_PRIOR_FUNDING
    return str(rate), None
