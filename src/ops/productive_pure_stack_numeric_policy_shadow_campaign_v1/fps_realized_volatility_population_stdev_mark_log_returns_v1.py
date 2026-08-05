"""Shadow Stage-1 formula: population stdev of mark log returns (PT60M / 60 returns).

FORMULA_ID=fps_realized_volatility.population_stdev_mark_log_returns.v1
PRODUCTIVE_ACTIVATION=false
SHADOW_ONLY=true
No CMC.volatility_estimate alias. No invented defaults.
"""

from __future__ import annotations

import math
from typing import Sequence

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    FinalizedBarV1,
    ShadowAvailabilityV1,
    ShadowFormulaObservationV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

FORMULA_ID = "fps_realized_volatility.population_stdev_mark_log_returns.v1"
UNIT = "PER_BAR_DECIMAL_RETURN_VOLATILITY"
HORIZON = "PT60M"
REQUIRED_RETURNS = 60
PRODUCTIVE_ACTIVATION = False
PROVISIONAL = True


def _reject(reason: str, *, input_digest: str) -> ShadowFormulaObservationV1:
    return ShadowFormulaObservationV1(
        formula_id=FORMULA_ID,
        status=ShadowAvailabilityV1.REJECTED
        if reason.startswith("reject_")
        else ShadowAvailabilityV1.UNAVAILABLE,
        value=None,
        unit=UNIT,
        provisional=PROVISIONAL,
        productive_activation=PRODUCTIVE_ACTIVATION,
        rejection_reason=reason,
        input_digest=input_digest,
        observation_event_time_epoch_s=None,
        notes=(f"horizon={HORIZON}", "shadow_only", "no_lookahead"),
    )


def compute_fps_realized_volatility_population_stdev_mark_log_returns_v1(
    bars: Sequence[FinalizedBarV1],
) -> ShadowFormulaObservationV1:
    """Require finalized PIT bars only; last 60 contiguous mark log returns ending at t."""
    payload = {
        "formula_id": FORMULA_ID,
        "n_bars": len(bars),
        "event_times": [b.event_time_epoch_s for b in bars],
        "marks": [b.mark_price for b in bars],
        "finalized": [b.finalized for b in bars],
    }
    digest = digest_mapping(payload)

    if len(bars) < REQUIRED_RETURNS + 1:
        return _reject("unavailable_insufficient_bars_for_warmup", input_digest=digest)

    window = list(bars[-(REQUIRED_RETURNS + 1) :])
    if any(not b.finalized for b in window):
        return _reject("reject_non_finalized_bars", input_digest=digest)
    if any(b.mark_price <= 0 or math.isnan(b.mark_price) for b in window):
        return _reject("unavailable_invalid_mark_price", input_digest=digest)

    times = [b.event_time_epoch_s for b in window]
    if times != sorted(times):
        return _reject("reject_lookahead_or_unsorted_event_time", input_digest=digest)
    if len(set(times)) != len(times):
        return _reject("reject_duplicate_event_time", input_digest=digest)

    # Contiguity for PT1M: exactly 60 seconds between adjacent finalized bars.
    for left, right in zip(times, times[1:]):
        if right - left != 60:
            return _reject("unavailable_non_contiguous_pt1m_bars", input_digest=digest)

    returns: list[float] = []
    for prev, cur in zip(window, window[1:]):
        returns.append(math.log(cur.mark_price / prev.mark_price))

    mean = sum(returns) / float(REQUIRED_RETURNS)
    var = sum((r - mean) ** 2 for r in returns) / float(REQUIRED_RETURNS)  # ddof=0
    value = math.sqrt(var)
    return ShadowFormulaObservationV1(
        formula_id=FORMULA_ID,
        status=ShadowAvailabilityV1.AVAILABLE,
        value=value,
        unit=UNIT,
        provisional=PROVISIONAL,
        productive_activation=PRODUCTIVE_ACTIVATION,
        rejection_reason=None,
        input_digest=digest,
        observation_event_time_epoch_s=window[-1].event_time_epoch_s,
        notes=(f"horizon={HORIZON}", "shadow_only", "ddof=0", "not_cmc_volatility_estimate"),
    )
