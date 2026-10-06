"""Productive Layer-C event distance binding from Dynamic Scope magnitude (stateful or fresh GGE).

Fresh base geometry for CMC bridges uses Golden Geometry Engine V1. Stateful paths use
``current_hysteresis_band`` via resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1.
Owner-authorized cutover: derive_scope_event_distances_v1 ratios 1.0 / 0.4 / 0.6 × D_t.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Tuple

from src.ops.derive_scope_event_distances_v1.derive_v1 import derive_scope_event_distances_v1

LAYER_C_SCOPE_EVENT_DISTANCE_BINDING_OWNER = (
    "trading.master_v2.layer_c_scope_event_distance_binding_v1"
)
LAYER_C_EVENT_DISTANCE_DERIVATION_ID = "derive_scope_event_distances_v1"
_LAYER_C_DERIVED_CAP62_DIGEST_MATERIAL = (
    "cap62-layer-c-event-distance-authority:derive_scope_event_distances_v1:1.0/0.4/0.6"
)
_LAYER_C_DERIVED_CAP65_ADVERSE_DIGEST_MATERIAL = (
    "cap65-adverse-exit-from-layer-c-derived:derive_scope_event_distances_v1:0.4"
)


def layer_c_derived_dynamic_scope_persistence_config_digest_v1() -> str:
    """Cap 6.2 session digest: derivation-mode + ratio contract (CONFIGURATION SEMANTICS).

    Identifies authorized Layer-C binding (derive_scope_event_distances_v1 at 1.0/0.4/0.6),
    not instantaneous D_t numeric values (those change each market tick at runtime).
    """
    return hashlib.sha256(_LAYER_C_DERIVED_CAP62_DIGEST_MATERIAL.encode("utf-8")).hexdigest()


def layer_c_derived_exit_policy_adverse_config_digest_v1(
    *,
    profit_protection_distance: float,
) -> str:
    """Stable Cap 6.5 session digest for derived adverse exit; profit protection unchanged."""
    material = (
        f"{_LAYER_C_DERIVED_CAP65_ADVERSE_DIGEST_MATERIAL}:"
        f"profit={float(profit_protection_distance)}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LayerCEventDistancesBindingResultV1:
    ok: bool
    up_distance: float | None
    adverse_exit_distance: float | None
    reversal_distance: float | None
    dynamic_scope_magnitude: float | None
    failure_codes: Tuple[str, ...]


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(
    dynamic_scope_magnitude: float,
) -> LayerCEventDistancesBindingResultV1:
    """Map authoritative D_t to Layer-C distances via derive_scope_event_distances_v1."""
    if not _positive_finite(dynamic_scope_magnitude):
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=("dynamic_scope_magnitude_non_positive",),
        )
    magnitude = float(dynamic_scope_magnitude)
    derived = derive_scope_event_distances_v1(magnitude)
    if not derived.ok:
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=magnitude,
            failure_codes=("layer_c_event_distance_derive_failed",),
        )
    return LayerCEventDistancesBindingResultV1(
        ok=True,
        up_distance=float(derived.up_distance),
        adverse_exit_distance=float(derived.adverse_exit_distance),
        reversal_distance=float(derived.reversal_distance),
        dynamic_scope_magnitude=magnitude,
        failure_codes=(),
    )


def resolve_layer_c_event_distances_from_mark_and_volatility_v1(
    *,
    mark_price: float,
    volatility_estimate: float,
    instrument_id: str = "",
) -> LayerCEventDistancesBindingResultV1:
    """Fresh base geometry via GGE V1, then Layer-C derive (productive exit/CMC path)."""
    from trading.master_v2.golden_geometry_engine_v1 import (
        compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
    )

    gge = compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id=instrument_id or "unknown",
        mark_price=float(mark_price),
        volatility_estimate=float(volatility_estimate),
    )
    if not gge.ok or gge.output is None:
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=gge.failure_codes or ("base_geometry_unavailable",),
        )
    return resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(
        float(gge.output.magnitude)
    )


def resolve_layer_c_event_distances_from_canonical_market_context_v1(
    market_context: object,
) -> LayerCEventDistancesBindingResultV1:
    """Fresh base geometry from finalized CMC via GGE V1 (FRESH_BASE_GEOMETRY exit path)."""
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
    from trading.master_v2.golden_geometry_engine_v1 import (
        compute_canonical_base_geometry_magnitude_from_market_context_v1,
    )

    if not isinstance(market_context, CanonicalMarketContextV1):
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=("market_context_invalid",),
        )
    gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(market_context)
    if not gge.ok or gge.output is None:
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=gge.failure_codes or ("base_geometry_unavailable",),
        )
    return resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(
        float(gge.output.magnitude)
    )
