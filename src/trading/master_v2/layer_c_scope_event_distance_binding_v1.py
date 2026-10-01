"""Productive Layer-C event distance binding from authoritative Dynamic Scope magnitude (σ×P).

Owner-authorized cutover: derive_scope_event_distances_v1 ratios 1.0 / 0.4 / 0.6 × D_t.
Cap 6.3 fixed 200/80/120 are not CURRENT productive event-distance authority.
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
) -> LayerCEventDistancesBindingResultV1:
    """σ×P at current canonical mark, then Layer-C derive (same magnitude SSOT as scope init)."""
    if not _positive_finite(mark_price):
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=("mark_price_non_positive",),
        )
    if not _positive_finite(volatility_estimate):
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=("volatility_non_positive",),
        )
    magnitude = float(volatility_estimate) * float(mark_price)
    return resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(magnitude)


def resolve_layer_c_event_distances_from_canonical_market_context_v1(
    market_context: object,
) -> LayerCEventDistancesBindingResultV1:
    """Authoritative σ×P from finalized CMC, then Layer-C derive (all productive bridges)."""
    from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        resolve_legacy_volatility_float_for_consumer_v1,
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
    try:
        vol = float(resolve_legacy_volatility_float_for_consumer_v1(market_context))
    except Exception:
        return LayerCEventDistancesBindingResultV1(
            ok=False,
            up_distance=None,
            adverse_exit_distance=None,
            reversal_distance=None,
            dynamic_scope_magnitude=None,
            failure_codes=("volatility_unavailable",),
        )
    return resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=float(market_context.mark_price),
        volatility_estimate=vol,
    )
