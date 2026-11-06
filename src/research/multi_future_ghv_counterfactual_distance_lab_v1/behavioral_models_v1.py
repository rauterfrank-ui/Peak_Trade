from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    LayerCEventDistancesBindingResultV1,
    resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
)

BEHAVIORAL_MODEL_IDS = (
    "MODEL_A_LEGACY_FIXED_80",
    "MODEL_B_CURRENT_LAYER_C",
    "MODEL_C_LEGACY_CLAMP_Dt",
    "MODEL_D_POLICY_HARD_MAX",
)

DIAGNOSTIC_INVARIANT_IDS = ("DIAGNOSTIC_CMC_VS_BAND_MISMATCH",)

LEGACY_CLAMP_MIN = 50.0
LEGACY_CLAMP_MAX = 500.0
LEGACY_FIXED_ADVERSE = 80.0
HARD_MAX_ADVERSE_DISTANCE = 500.0


@dataclass(frozen=True)
class BehavioralModelSpecV1:
    model_id: str
    formula: str
    unit: str
    inputs: Tuple[str, ...]
    provenance: str
    current_components_reused: Tuple[str, ...]
    new_semantics_required: bool
    price_scale_adaptive: bool
    volatility_adaptive: bool
    contract_aware: bool
    risk_aware: bool
    symbol_specific: bool


MODEL_MANIFEST: Mapping[str, BehavioralModelSpecV1] = {
    "MODEL_A_LEGACY_FIXED_80": BehavioralModelSpecV1(
        model_id="MODEL_A_LEGACY_FIXED_80",
        formula="adverse=80 absolute; up/reversal via derive_scope_event_distances_v1 ratios",
        unit="price",
        inputs=("fixed_adverse",),
        provenance="HISTORICAL Cap 6.3 negative control (200/80/120 family)",
        current_components_reused=("derive_scope_event_distances_v1",),
        new_semantics_required=False,
        price_scale_adaptive=False,
        volatility_adaptive=False,
        contract_aware=False,
        risk_aware=False,
        symbol_specific=False,
    ),
    "MODEL_B_CURRENT_LAYER_C": BehavioralModelSpecV1(
        model_id="MODEL_B_CURRENT_LAYER_C",
        formula="D_t=sigma×P; distances=derive_scope_event_distances_v1(D_t)",
        unit="price",
        inputs=("mark_price", "volatility_estimate"),
        provenance="PROVEN_CURRENT layer_c_scope_event_distance_binding_v1",
        current_components_reused=(
            "resolve_layer_c_event_distances_from_mark_and_volatility_v1",
            "derive_scope_event_distances_v1",
        ),
        new_semantics_required=False,
        price_scale_adaptive=True,
        volatility_adaptive=True,
        contract_aware=False,
        risk_aware=False,
        symbol_specific=False,
    ),
    "MODEL_C_LEGACY_CLAMP_Dt": BehavioralModelSpecV1(
        model_id="MODEL_C_LEGACY_CLAMP_Dt",
        formula="D_t=clamp(sigma×P,[50,500]); distances=derive_scope_event_distances_v1(D_t)",
        unit="price",
        inputs=("mark_price", "volatility_estimate", "min_scope_band", "max_scope_band"),
        provenance="HISTORICAL legacy scope init clamp (canonical_scope_initialization clamp_scope_band)",
        current_components_reused=("derive_scope_event_distances_v1", "clamp_scope_band"),
        new_semantics_required=False,
        price_scale_adaptive=True,
        volatility_adaptive=True,
        contract_aware=False,
        risk_aware=False,
        symbol_specific=False,
    ),
    "MODEL_D_POLICY_HARD_MAX": BehavioralModelSpecV1(
        model_id="MODEL_D_POLICY_HARD_MAX",
        formula="Layer-C distances then consumer min(adverse, hard_max_adverse_distance=500)",
        unit="price",
        inputs=("mark_price", "volatility_estimate", "hard_max_adverse_distance"),
        provenance="PROVEN_CURRENT ScopeEventGeneratorPolicyV1.hard_max_adverse_distance consumer",
        current_components_reused=(
            "resolve_layer_c_event_distances_from_mark_and_volatility_v1",
            "ScopeEventGeneratorPolicyV1.hard_max_adverse_distance",
        ),
        new_semantics_required=False,
        price_scale_adaptive=True,
        volatility_adaptive=True,
        contract_aware=False,
        risk_aware=True,
        symbol_specific=False,
    ),
}


def _derive_from_magnitude(magnitude: float) -> LayerCEventDistancesBindingResultV1:
    return resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(float(magnitude))


def resolve_behavioral_layer_c_distances_v1(
    *,
    model_id: str,
    mark_price: float,
    volatility_estimate: float,
) -> LayerCEventDistancesBindingResultV1:
    if model_id == "MODEL_B_CURRENT_LAYER_C":
        return resolve_layer_c_event_distances_from_mark_and_volatility_v1(
            mark_price=float(mark_price),
            volatility_estimate=float(volatility_estimate),
        )
    if model_id == "MODEL_A_LEGACY_FIXED_80":
        up = LEGACY_FIXED_ADVERSE / 0.4
        return _derive_from_magnitude(up)
    raw_dt = float(volatility_estimate) * float(mark_price)
    if model_id == "MODEL_C_LEGACY_CLAMP_Dt":
        from trading.master_v2.canonical_scope_initialization_v1 import clamp_scope_band

        magnitude = clamp_scope_band(raw_dt, LEGACY_CLAMP_MIN, LEGACY_CLAMP_MAX)
        return _derive_from_magnitude(magnitude)
    if model_id == "MODEL_D_POLICY_HARD_MAX":
        base = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
            mark_price=float(mark_price),
            volatility_estimate=float(volatility_estimate),
        )
        if not base.ok or base.adverse_exit_distance is None:
            return base
        adverse = min(float(base.adverse_exit_distance), HARD_MAX_ADVERSE_DISTANCE)
        if adverse <= 0:
            return LayerCEventDistancesBindingResultV1(
                ok=False,
                up_distance=None,
                adverse_exit_distance=None,
                reversal_distance=None,
                dynamic_scope_magnitude=base.dynamic_scope_magnitude,
                failure_codes=("policy_hard_max_non_positive_adverse",),
            )
        up = adverse / 0.4
        rev = adverse / 0.4 * 1.5
        return LayerCEventDistancesBindingResultV1(
            ok=True,
            up_distance=up,
            adverse_exit_distance=adverse,
            reversal_distance=rev,
            dynamic_scope_magnitude=base.dynamic_scope_magnitude,
            failure_codes=(),
        )
    raise ValueError(f"unknown_behavioral_model:{model_id}")


def diagnostic_cmc_vs_hysteresis_band_v1(
    *,
    mark_price: float,
    volatility_estimate: float,
    hysteresis_band: float,
) -> dict[str, object]:
    layer_c = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
        mark_price=float(mark_price),
        volatility_estimate=float(volatility_estimate),
    )
    cmc_dt = float(layer_c.dynamic_scope_magnitude or 0.0)
    band = float(hysteresis_band)
    abs_delta = abs(cmc_dt - band)
    rel = abs_delta / cmc_dt if cmc_dt > 0 else None
    return {
        "diagnostic_id": "DIAGNOSTIC_CMC_VS_BAND_MISMATCH",
        "CMC_Dt": cmc_dt,
        "HYSTERESIS_BAND": band,
        "ABS_DELTA": abs_delta,
        "RELATIVE_DELTA": rel,
        "SEMANTICALLY_EQUIVALENT": bool(cmc_dt > 0 and abs_delta <= max(1e-9, 1e-6 * cmc_dt)),
    }
