"""Typed result contract for derive_scope_event_distances_v1.

DATA CONTRACT ONLY. AUTHORITY_EFFECT=NONE. Does not mint selection, formula,
policy, producer, runtime-bind, or trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.ops.derive_scope_event_distances_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    FAILURE_REASON_INVALID_INPUT,
)


@dataclass(frozen=True)
class DerivedScopeEventDistancesResultV1:
    """Fail-closed result record. Invalid results carry no usable distances."""

    ok: bool
    up_distance: float | None
    adverse_exit_distance: float | None
    reversal_distance: float | None
    failure_reason: str | None
    AUTHORITY_EFFECT: ClassVar[str] = AUTHORITY_EFFECT

    def __post_init__(self) -> None:
        if self.ok:
            if self.failure_reason is not None:
                raise ValueError("valid result must not carry a failure_reason")
            for name in ("up_distance", "adverse_exit_distance", "reversal_distance"):
                value = getattr(self, name)
                if type(value) is not float:
                    raise ValueError(f"valid result {name} must be float")
            return
        if self.failure_reason != FAILURE_REASON_INVALID_INPUT:
            raise ValueError("invalid result must use FAILURE_REASON_INVALID_INPUT")
        if (
            self.up_distance is not None
            or self.adverse_exit_distance is not None
            or self.reversal_distance is not None
        ):
            raise ValueError("invalid result must not carry usable distances")


def ok_result_v1(
    *,
    up_distance: float,
    adverse_exit_distance: float,
    reversal_distance: float,
) -> DerivedScopeEventDistancesResultV1:
    return DerivedScopeEventDistancesResultV1(
        ok=True,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        failure_reason=None,
    )


def invalid_result_v1() -> DerivedScopeEventDistancesResultV1:
    return DerivedScopeEventDistancesResultV1(
        ok=False,
        up_distance=None,
        adverse_exit_distance=None,
        reversal_distance=None,
        failure_reason=FAILURE_REASON_INVALID_INPUT,
    )
