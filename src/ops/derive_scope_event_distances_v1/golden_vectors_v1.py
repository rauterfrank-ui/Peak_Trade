"""Golden vectors for the full Dynamic Scope distance contract."""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.derive_scope_event_distances_v1.constants_v1 import (
    FAILURE_REASON_INVALID_INPUT,
)


@dataclass(frozen=True)
class GoldenValidVectorV1:
    current_hysteresis_band: float
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    note: str


@dataclass(frozen=True)
class GoldenInvalidVectorV1:
    current_hysteresis_band: object
    note: str


def _valid(band: float, note: str) -> GoldenValidVectorV1:
    return GoldenValidVectorV1(
        current_hysteresis_band=band,
        up_distance=band,
        adverse_exit_distance=band,
        reversal_distance=band,
        note=note,
    )


GOLDEN_VALID_VECTORS_V1: tuple[GoldenValidVectorV1, ...] = (
    _valid(25.0, "representative_small_band"),
    _valid(50.0, "representative_mid_band"),
    _valid(1.0, "representative_unit_band"),
    _valid(5.0, "full_scope_5"),
    _valid(12.5, "full_scope_12_5"),
    _valid(200.0, "full_scope_200"),
)

GOLDEN_INVALID_VECTORS_V1: tuple[GoldenInvalidVectorV1, ...] = (
    GoldenInvalidVectorV1(float("nan"), "nan"),
    GoldenInvalidVectorV1(float("inf"), "pos_inf"),
    GoldenInvalidVectorV1(float("-inf"), "neg_inf"),
    GoldenInvalidVectorV1(0.0, "zero"),
    GoldenInvalidVectorV1(-0.0, "negative_zero"),
    GoldenInvalidVectorV1(-1.0, "negative"),
    GoldenInvalidVectorV1(None, "none"),
    GoldenInvalidVectorV1(1, "int_no_coercion"),
    GoldenInvalidVectorV1(True, "bool_no_coercion"),
    GoldenInvalidVectorV1("25.0", "str_no_coercion"),
)

GOLDEN_INVALID_FAILURE_REASON = FAILURE_REASON_INVALID_INPUT
