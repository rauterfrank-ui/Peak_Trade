"""Canonical missing-open-interest semantics for cross-sectional research v0.

Fail-closed: missing OI stays explicit None; synthetic zero is forbidden.
Research-only; no runtime or authority effect.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

PACKAGE_MARKER = "MISSING_OPEN_INTEREST_POLICY_V0=true"
POLICY_VERSION = "missing_open_interest_policy.v0"

MISSING_OPEN_INTEREST_VALUE: None = None
MISSING_OPEN_INTEREST_IS_ZERO = False
MISSING_OPEN_INTEREST_FAIL_CLOSED = True

FORBIDDEN_MISSING_FALLBACKS = frozenset({"0", "0.0", 0, 0.0, Decimal("0"), Decimal("0.0")})

MISSING_REASON_NO_PRIOR_OI = "MISSING_OI_NO_PRIOR_OBSERVATION"
MISSING_REASON_FIELD_ABSENT = "MISSING_OI_FIELD_ABSENT"
MISSING_REASON_SYNTHETIC_ZERO_BLOCKED = "MISSING_OI_SYNTHETIC_ZERO_BLOCKED"
MISSING_REASON_STALE_OBSERVATION = "MISSING_OI_STALE_OBSERVATION"
MISSING_REASON_LOOKAHEAD_REJECTED = "MISSING_OI_LOOKAHEAD_REJECTED"


def is_missing_open_interest_value_v0(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def reject_synthetic_zero_open_interest_fallback_v0(value: Any) -> None:
    if value in FORBIDDEN_MISSING_FALLBACKS:
        raise ValueError(MISSING_REASON_SYNTHETIC_ZERO_BLOCKED)
    if isinstance(value, str) and value.strip() in {"0", "0.0"}:
        raise ValueError(MISSING_REASON_SYNTHETIC_ZERO_BLOCKED)


def resolve_open_interest_or_missing_v0(
    *,
    raw_value: Any,
    allow_explicit_zero: bool = True,
) -> str | None:
    if is_missing_open_interest_value_v0(raw_value):
        return MISSING_OPEN_INTEREST_VALUE
    text = str(raw_value).strip()
    if not text:
        return MISSING_OPEN_INTEREST_VALUE
    if not allow_explicit_zero:
        reject_synthetic_zero_open_interest_fallback_v0(text)
    return text
