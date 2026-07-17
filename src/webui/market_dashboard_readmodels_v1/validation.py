"""Market Dashboard ReadModel contracts v1 — validation helpers (stdlib only).

Fail-closed validators for schema identity, timestamps, digests, numerics, and
ordering. No domain calculation and no current-time injection.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, TypeVar

_E = TypeVar("_E", bound=Enum)

SCHEMA_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PRODUCER_MODULE_PATTERN = re.compile(r"^[A-Za-z0-9_./-]+$")


class MarketDashboardReadModelContractError(ValueError):
    """Raised when a Market Dashboard ReadModel contract is invalid."""


def require_non_empty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MarketDashboardReadModelContractError(f"{field} must be a non-empty string")
    return value.strip()


def require_schema_id(value: Any, *, field: str = "schema_id") -> str:
    text = require_non_empty_str(value, field=field)
    if not SCHEMA_ID_PATTERN.fullmatch(text):
        raise MarketDashboardReadModelContractError(
            f"{field} must match schema id pattern, got {text!r}"
        )
    return text


def require_schema_version(value: Any, *, field: str = "schema_version") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MarketDashboardReadModelContractError(f"{field} must be a positive integer")
    if value < 1:
        raise MarketDashboardReadModelContractError(f"{field} must be >= 1")
    return value


def require_aware_datetime(value: Any, *, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise MarketDashboardReadModelContractError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise MarketDashboardReadModelContractError(
            f"{field} must be timezone-aware (naive timestamps rejected)"
        )
    return value


def require_timestamp_order(
    earlier: datetime,
    later: datetime,
    *,
    earlier_field: str,
    later_field: str,
) -> None:
    if later < earlier:
        raise MarketDashboardReadModelContractError(f"{later_field} must be >= {earlier_field}")


def require_enum(value: Any, enum_cls: type[_E], *, field: str) -> _E:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError as exc:
            raise MarketDashboardReadModelContractError(
                f"{field} must be one of {[e.value for e in enum_cls]}, got {value!r}"
            ) from exc
    raise MarketDashboardReadModelContractError(
        f"{field} must be {enum_cls.__name__}, got {type(value).__name__}"
    )


def require_producer_module(value: Any, *, field: str = "producer_module") -> str:
    text = require_non_empty_str(value, field=field)
    if not PRODUCER_MODULE_PATTERN.fullmatch(text):
        raise MarketDashboardReadModelContractError(
            f"{field} must be a non-empty producer identity, got {text!r}"
        )
    return text


def require_optional_non_empty_str(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return require_non_empty_str(value, field=field)


def require_sha256_digest(value: Any, *, field: str) -> str:
    text = require_non_empty_str(value, field=field).lower()
    if not SHA256_HEX_PATTERN.fullmatch(text):
        raise MarketDashboardReadModelContractError(
            f"{field} must be a 64-char lowercase sha256 hex digest"
        )
    return text


def require_optional_sha256_digest(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return require_sha256_digest(value, field=field)


def require_finite_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MarketDashboardReadModelContractError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise MarketDashboardReadModelContractError(
            f"{field} must be finite (NaN/Infinity rejected)"
        )
    return number


def require_optional_finite_number(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    return require_finite_number(value, field=field)


def require_non_negative_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MarketDashboardReadModelContractError(f"{field} must be a non-negative integer")
    if value < 0:
        raise MarketDashboardReadModelContractError(f"{field} must be >= 0")
    return value


def require_non_negative_number(value: Any, *, field: str) -> float:
    number = require_finite_number(value, field=field)
    if number < 0:
        raise MarketDashboardReadModelContractError(f"{field} must be >= 0")
    return number


def require_optional_non_negative_number(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    return require_non_negative_number(value, field=field)


def normalize_reason_codes(values: Any, *, field: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise MarketDashboardReadModelContractError(f"{field} must be a list or tuple of strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        code = require_non_empty_str(item, field=f"{field}[{index}]")
        if code in seen:
            raise MarketDashboardReadModelContractError(f"{field} contains duplicate code {code!r}")
        seen.add(code)
        normalized.append(code)
    # Deterministic ordering for contract equality and serialization.
    return tuple(sorted(normalized))


def normalize_blockers(values: Any, *, field: str) -> tuple[str, ...]:
    return normalize_reason_codes(values, field=field)


def require_unique_sorted_keys(items: Iterable[str], *, field: str) -> tuple[str, ...]:
    ordered = tuple(items)
    if len(set(ordered)) != len(ordered):
        raise MarketDashboardReadModelContractError(f"{field} contains duplicate keys")
    if ordered != tuple(sorted(ordered)):
        raise MarketDashboardReadModelContractError(f"{field} must be deterministically sorted")
    return ordered


__all__ = [
    "MarketDashboardReadModelContractError",
    "normalize_blockers",
    "normalize_reason_codes",
    "require_aware_datetime",
    "require_enum",
    "require_finite_number",
    "require_non_empty_str",
    "require_non_negative_int",
    "require_non_negative_number",
    "require_optional_finite_number",
    "require_optional_non_empty_str",
    "require_optional_non_negative_number",
    "require_optional_sha256_digest",
    "require_producer_module",
    "require_schema_id",
    "require_schema_version",
    "require_sha256_digest",
    "require_timestamp_order",
    "require_unique_sorted_keys",
]
