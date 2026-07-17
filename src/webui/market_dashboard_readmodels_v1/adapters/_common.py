"""Shared fail-closed helpers for PR-C dashboard adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from src.webui.market_dashboard_readmodels_v1.contracts import (
    DashboardAvailabilityStateV1,
    UnavailableSnapshotV1,
    new_unavailable_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.validation import (
    MarketDashboardReadModelContractError,
)

ADAPTER_PRODUCER_VERSION = "market_dashboard_adapters.v1"
_FORBIDDEN_INSTRUMENT_TOKENS = ("btc", "bitcoin", "xbt")
_DUMMY_SOURCE_TOKENS = ("dummy", "source=dummy")


def source_get(source: Any, key: str, default: Any = None) -> Any:
    """Read a field from a Mapping or attribute-bearing object."""

    if source is None:
        return default
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def enum_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return str(value)


def parse_aware_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise MarketDashboardReadModelContractError(
                f"{field} must be timezone-aware (naive timestamps rejected)"
            )
        return value
    if not isinstance(value, str) or not value.strip():
        raise MarketDashboardReadModelContractError(
            f"{field} must be an aware datetime or ISO string"
        )
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise MarketDashboardReadModelContractError(f"{field} is not a valid ISO datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MarketDashboardReadModelContractError(f"{field} must be timezone-aware")
    return parsed


def is_forbidden_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in _FORBIDDEN_INSTRUMENT_TOKENS)


def is_dummy_source(source_text: str | None) -> bool:
    if source_text is None:
        return False
    lowered = source_text.strip().lower()
    return any(token in lowered for token in _DUMMY_SOURCE_TOKENS)


def unavailable(
    *,
    availability_state: DashboardAvailabilityStateV1 | str,
    reason_code: str,
    detail: str,
    expected_source: str,
    generated_at: datetime,
    source_reference: str | None = None,
) -> UnavailableSnapshotV1:
    return new_unavailable_snapshot_v1(
        availability_state=availability_state,
        reason_code=reason_code,
        detail=detail,
        expected_source=expected_source,
        generated_at=generated_at,
        source_reference=source_reference,
    )


def require_sha256_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    digest = value.strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise MarketDashboardReadModelContractError(
            "evidence_digest must be 64-char lowercase sha256"
        )
    return digest


def as_reason_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, (list, tuple)):
        items: list[str] = []
        for item in value:
            text = enum_text(item)
            if text:
                items.append(text)
        return tuple(items)
    text = enum_text(value)
    return (text,) if text else ()


def epoch_anchor_datetime(trading_epoch: Any, *, field: str = "trading_epoch") -> datetime:
    """Deterministic epoch→datetime projection without wall-clock reads.

    Maps a positive integer trading epoch to an aware UTC datetime anchored at
    the Unix epoch. This preserves ordering without inventing wall-clock event
    times that the source does not provide.
    """

    if isinstance(trading_epoch, bool) or not isinstance(trading_epoch, int):
        raise MarketDashboardReadModelContractError(f"{field} must be an integer")
    if trading_epoch < 0:
        raise MarketDashboardReadModelContractError(f"{field} must be >= 0")
    return datetime.fromtimestamp(trading_epoch, tz=timezone.utc)


__all__ = [
    "ADAPTER_PRODUCER_VERSION",
    "as_reason_tuple",
    "enum_text",
    "epoch_anchor_datetime",
    "is_dummy_source",
    "is_forbidden_instrument",
    "parse_aware_datetime",
    "require_sha256_or_none",
    "source_get",
    "unavailable",
]
