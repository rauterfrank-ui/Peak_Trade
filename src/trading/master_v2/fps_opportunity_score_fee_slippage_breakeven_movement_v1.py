"""Shadow Stage-1 opportunity score on unit interval.

FORMULA_ID=fps_opportunity_score.fee_slippage_breakeven_movement.v1
PRODUCTIVE_ACTIVATION=false
SHADOW_ONLY=true

Semantic: monotonic transform of recent absolute log-return movement relative to an
explicit fee+slippage breakeven band. Missing inputs → UNAVAILABLE (never default 0).
"""

from __future__ import annotations

import math
from typing import Optional

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    ShadowAvailabilityV1,
    ShadowFormulaObservationV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

FORMULA_ID = "fps_opportunity_score.fee_slippage_breakeven_movement.v1"
UNIT = "UNIT_INTERVAL_0_1"
PRODUCTIVE_ACTIVATION = False
PROVISIONAL = True


def compute_fps_opportunity_score_fee_slippage_breakeven_movement_v1(
    *,
    recent_abs_log_return: Optional[float],
    fee_bps: Optional[float],
    slippage_bps: Optional[float],
    event_time_epoch_s: Optional[int] = None,
) -> ShadowFormulaObservationV1:
    payload = {
        "formula_id": FORMULA_ID,
        "recent_abs_log_return": recent_abs_log_return,
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "event_time_epoch_s": event_time_epoch_s,
    }
    digest = digest_mapping(payload)

    def _out(status: ShadowAvailabilityV1, reason: Optional[str], value: Optional[float]):
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
            notes=("shadow_only", "not_trade_signal", "no_default_zero"),
        )

    if recent_abs_log_return is None or fee_bps is None or slippage_bps is None:
        return _out(ShadowAvailabilityV1.UNAVAILABLE, "unavailable_missing_inputs", None)
    if any(
        (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))
        for x in (recent_abs_log_return, fee_bps, slippage_bps)
    ):
        return _out(ShadowAvailabilityV1.REJECTED, "reject_non_finite_inputs", None)
    if recent_abs_log_return < 0 or fee_bps < 0 or slippage_bps < 0:
        return _out(ShadowAvailabilityV1.REJECTED, "reject_negative_inputs", None)

    breakeven = (fee_bps + slippage_bps) / 10_000.0
    if breakeven <= 0.0:
        return _out(ShadowAvailabilityV1.UNAVAILABLE, "unavailable_zero_breakeven_band", None)

    # Monotonic soft-sat in [0,1]: 1 - exp(-movement / breakeven).
    score = 1.0 - math.exp(-recent_abs_log_return / breakeven)
    if score < 0.0 or score > 1.0 or math.isnan(score):
        return _out(ShadowAvailabilityV1.REJECTED, "reject_score_out_of_unit_interval", None)
    return _out(ShadowAvailabilityV1.AVAILABLE, None, score)
