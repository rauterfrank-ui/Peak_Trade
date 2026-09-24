"""Constants for F1/M9 scoped Owner Apply authority (import-safe, no cycle)."""

from __future__ import annotations

from typing import Final

RUNTIME_APPLY_AUTHORITY_VALUE: Final[str] = "F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_V1"


def is_f1_m9_scoped_runtime_apply_authority_v1(value: str | None) -> bool:
    return value == RUNTIME_APPLY_AUTHORITY_VALUE


__all__ = ["RUNTIME_APPLY_AUTHORITY_VALUE", "is_f1_m9_scoped_runtime_apply_authority_v1"]
