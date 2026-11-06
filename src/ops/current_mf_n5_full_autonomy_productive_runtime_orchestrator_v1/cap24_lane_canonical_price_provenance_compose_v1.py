"""Derive per-lane canonical price provenance from Cap24 bind + mark sidecar.

Composition-only. Does not mint price authority or alter Full-Core semantics.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
    MARK_SOURCE_CAP24_MARK_SIDECAR,
    ProductiveCanonicalPriceProvenanceError,
    ProductiveCycleCanonicalPriceProvenanceV1,
    build_provenance_from_resolved_cmc_mark_and_index_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class Cap24LaneCanonicalPriceProvenanceComposeError(ValueError):
    """Fail-closed Cap24 lane provenance compose violation."""


def _parse_positive_mark_v1(raw: Any, *, venue_native_id: str) -> float:
    text = str(raw or "").strip()
    if not text:
        raise Cap24LaneCanonicalPriceProvenanceComposeError(
            f"CAP24_MARK_PRICE_MISSING:{venue_native_id}"
        )
    try:
        value = float(Decimal(text))
    except (InvalidOperation, ValueError) as exc:
        raise Cap24LaneCanonicalPriceProvenanceComposeError(
            f"CAP24_MARK_PRICE_MALFORMED:{venue_native_id}"
        ) from exc
    if value <= 0:
        raise Cap24LaneCanonicalPriceProvenanceComposeError(
            f"CAP24_MARK_PRICE_NONPOSITIVE:{venue_native_id}"
        )
    return value


def build_n5_lane_canonical_price_provenance_from_cap24_v1(
    selected_pairs: Mapping[str, tuple[Any, BoundInstrumentV1]],
    mark_price_by_native_id: Mapping[str, Any],
    *,
    index_px: float,
    index_source: str = INDEX_SOURCE_EXPLICIT_TEST_FIXTURE,
) -> dict[str, ProductiveCycleCanonicalPriceProvenanceV1]:
    """One provenance object per occupied lane, keyed by lane_id."""

    if float(index_px) <= 0:
        raise Cap24LaneCanonicalPriceProvenanceComposeError("INDEX_PX_NONPOSITIVE")
    marks = dict(mark_price_by_native_id or {})
    out: dict[str, ProductiveCycleCanonicalPriceProvenanceV1] = {}
    for lane_id, pair in selected_pairs.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise Cap24LaneCanonicalPriceProvenanceComposeError(f"LANE_PAIR_MALFORMED:{lane_id}")
        _slot, bound = pair
        if not isinstance(bound, BoundInstrumentV1):
            raise Cap24LaneCanonicalPriceProvenanceComposeError(f"BOUND_TYPE:{lane_id}")
        native = str(bound.venue_native_id or "").strip()
        if not native:
            raise Cap24LaneCanonicalPriceProvenanceComposeError(
                f"VENUE_NATIVE_ID_MISSING:{lane_id}"
            )
        if native not in marks:
            raise Cap24LaneCanonicalPriceProvenanceComposeError(
                f"CAP24_MARK_PRICE_SIDEcar_MISSING:{native}"
            )
        mark_px = _parse_positive_mark_v1(marks[native], venue_native_id=native)
        try:
            provenance = build_provenance_from_resolved_cmc_mark_and_index_v1(
                venue_native_id=native,
                mark_px=mark_px,
                index_px=float(index_px),
                mark_source=MARK_SOURCE_CAP24_MARK_SIDECAR,
                index_source=str(index_source),
            )
        except ProductiveCanonicalPriceProvenanceError as exc:
            raise Cap24LaneCanonicalPriceProvenanceComposeError(
                f"CAP24_PROVENANCE_BUILD_FAIL_CLOSED:{lane_id}:{exc}"
            ) from exc
        provenance.validate_against_cycle_inputs_v1(
            mark_px=mark_px,
            index_px=float(index_px),
            venue_native_id=native,
        )
        out[str(lane_id)] = provenance
    if not out:
        raise Cap24LaneCanonicalPriceProvenanceComposeError("NO_OCCUPIED_LANES")
    return out


__all__ = [
    "Cap24LaneCanonicalPriceProvenanceComposeError",
    "build_n5_lane_canonical_price_provenance_from_cap24_v1",
]
