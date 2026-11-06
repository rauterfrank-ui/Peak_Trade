"""F1/M9 scoped Owner Threshold Value authority constants v1."""

from __future__ import annotations

from typing import Final

RUNTIME_THRESHOLD_VALUE_AUTHORITY: Final[str] = "F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORITY_V1"


def is_f1_m9_scoped_runtime_threshold_value_authority_v1(value: str | None) -> bool:
    return value == RUNTIME_THRESHOLD_VALUE_AUTHORITY


__all__ = [
    "RUNTIME_THRESHOLD_VALUE_AUTHORITY",
    "is_f1_m9_scoped_runtime_threshold_value_authority_v1",
]
