"""Shadow Stage-1 path-survival ratio: pre-arm path fraction above barrier.

FORMULA_ID=fps_sequence_path_survival_ratio.prearm_path_fraction.v1
PRODUCTIVE_ACTIVATION=false
SHADOW_ONLY=true
PROVISIONAL=true  # metric functional authorized as definition ID; producer is shadow-only
"""

from __future__ import annotations

from typing import Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ShadowAvailabilityV1,
    ShadowFormulaObservationV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

FORMULA_ID = "fps_sequence_path_survival_ratio.prearm_path_fraction.v1"
UNIT = "RATIO_UNIT_INTERVAL"
PRODUCTIVE_ACTIVATION = False
PROVISIONAL = True


def compute_fps_sequence_path_survival_ratio_prearm_path_fraction_v1(
    path_above_barrier: Sequence[bool] | None,
    *,
    event_time_epoch_s: int | None = None,
) -> ShadowFormulaObservationV1:
    payload = {
        "formula_id": FORMULA_ID,
        "path_above_barrier": None
        if path_above_barrier is None
        else [bool(x) for x in path_above_barrier],
        "event_time_epoch_s": event_time_epoch_s,
    }
    digest = digest_mapping(payload)

    def _out(status: ShadowAvailabilityV1, reason: str | None, value: float | None):
        return ShadowFormulaObservationV1(
            formula_id=FORMULA_ID,
            status=status,
            value=value,
            unit=UNIT,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            rejection_reason=reason,
            input_digest=digest,
            observation_event_time_epoch_s=event_time_epoch_s,
            notes=(
                "shadow_only",
                "provisional_formula",
                "definition_id_bound",
                "no_hot_path_recompute_claim",
            ),
        )

    if path_above_barrier is None:
        return _out(ShadowAvailabilityV1.UNAVAILABLE, "unavailable_missing_path_ensemble", None)
    if len(path_above_barrier) == 0:
        return _out(ShadowAvailabilityV1.UNAVAILABLE, "unavailable_empty_path_ensemble", None)
    if any(not isinstance(x, bool) for x in path_above_barrier):
        return _out(ShadowAvailabilityV1.REJECTED, "reject_non_boolean_path_flags", None)

    survived = sum(1 for x in path_above_barrier if x)
    ratio = survived / float(len(path_above_barrier))
    return _out(ShadowAvailabilityV1.AVAILABLE, None, ratio)
