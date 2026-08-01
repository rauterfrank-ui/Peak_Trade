"""Explicit campaign authorization expiry policy (contract, not test-only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    CAMPAIGN_AUTHORIZATION_TTL_SECONDS,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationError,
)

Clock = Callable[[], datetime]


def parse_aware_utc_datetime_v1(value: object, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CampaignAuthorizationError(f"{field_name}_naive_datetime_forbidden")
        return value.astimezone(timezone.utc)
    if not isinstance(value, str) or not value.strip():
        raise CampaignAuthorizationError(f"{field_name}_invalid")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CampaignAuthorizationError(f"{field_name}_parse_error") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CampaignAuthorizationError(f"{field_name}_naive_datetime_forbidden")
    return parsed.astimezone(timezone.utc)


def format_aware_utc_datetime_v1(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise CampaignAuthorizationError("naive_datetime_forbidden")
    utc = value.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_expires_at_v1(*, issued_at: datetime) -> datetime:
    issued = parse_aware_utc_datetime_v1(issued_at, field_name="issued_at")
    return issued + timedelta(seconds=int(CAMPAIGN_AUTHORIZATION_TTL_SECONDS))


def validate_issuance_window_v1(
    *,
    issued_at: datetime,
    earliest_start: datetime,
    expires_at: Optional[datetime] = None,
) -> tuple[datetime, datetime, datetime]:
    """Validate issuance timing. No grace period; no auto-extension."""
    issued = parse_aware_utc_datetime_v1(issued_at, field_name="issued_at")
    earliest = parse_aware_utc_datetime_v1(earliest_start, field_name="earliest_start")
    expected_expires = compute_expires_at_v1(issued_at=issued)
    expires = (
        expected_expires
        if expires_at is None
        else parse_aware_utc_datetime_v1(expires_at, field_name="expires_at")
    )
    if expires != expected_expires:
        raise CampaignAuthorizationError("expires_at_ttl_mismatch")
    if earliest < issued:
        raise CampaignAuthorizationError("earliest_start_before_issued_at")
    if earliest > expires:
        raise CampaignAuthorizationError("earliest_start_after_expires_at")
    return issued, earliest, expires


def assert_clock_within_authorization_window_v1(
    *,
    issued_at: object,
    earliest_start: object,
    expires_at: object,
    now: Optional[datetime] = None,
    clock: Optional[Clock] = None,
) -> datetime:
    """Fail-closed window check.

    Semantics:
    - now < earliest_start → fail-closed
    - now >= expires_at → fail-closed
    - clock parse/trust errors → fail-closed
    - no grace period
    """
    parse_aware_utc_datetime_v1(issued_at, field_name="issued_at")
    earliest = parse_aware_utc_datetime_v1(earliest_start, field_name="earliest_start")
    expires = parse_aware_utc_datetime_v1(expires_at, field_name="expires_at")
    try:
        if now is not None:
            current = parse_aware_utc_datetime_v1(now, field_name="now")
        elif clock is not None:
            current = parse_aware_utc_datetime_v1(clock(), field_name="clock")
        else:
            current = datetime.now(timezone.utc)
    except CampaignAuthorizationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise CampaignAuthorizationError("clock_trust_or_parse_error") from exc

    if current < earliest:
        raise CampaignAuthorizationError("before_earliest_start")
    if current >= expires:
        raise CampaignAuthorizationError("at_or_after_expires_at")
    return current
