"""Golden vectors for derive_scope_event_distances_v1.

Expected valid distances are the OQ-C1/OQ-C2 formula results, not CURRENT
Cap 6.3 Dual Envelope values used as authority. The 200.0 vector is a
formula coincidence check only.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.derive_scope_event_distances_v1.constants_v1 import (
    FAILURE_REASON_INVALID_INPUT,
    OQ_C2_ADVERSE_NUMERATOR,
    OQ_C2_RATIO_DENOMINATOR,
    OQ_C2_REVERSAL_NUMERATOR,
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


def _formula_triplet(band: float) -> tuple[float, float, float]:
    up_distance = band
    adverse_exit_distance = band * (OQ_C2_ADVERSE_NUMERATOR / OQ_C2_RATIO_DENOMINATOR)
    reversal_distance = band * (OQ_C2_REVERSAL_NUMERATOR / OQ_C2_RATIO_DENOMINATOR)
    return up_distance, adverse_exit_distance, reversal_distance


def _valid(band: float, note: str) -> GoldenValidVectorV1:
    up_distance, adverse_exit_distance, reversal_distance = _formula_triplet(band)
    return GoldenValidVectorV1(
        current_hysteresis_band=band,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        note=note,
    )


GOLDEN_VALID_VECTORS_V1: tuple[GoldenValidVectorV1, ...] = (
    _valid(25.0, "representative_small_band"),
    _valid(50.0, "representative_mid_band"),
    _valid(1.0, "representative_unit_band"),
    _valid(5.0, "exact_ratio_geometry_5"),
    _valid(12.5, "exact_ratio_geometry_12_5"),
    _valid(200.0, "formula_coincidence_with_model_b_not_authority"),
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
