"""Shadow Stage-1 formula: Wilder ATR over 14 finalized PT1M OHLCV bars.

FORMULA_ID=fps_atr_or_range.wilder_atr_finalized_ohlcv.v1
PRODUCTIVE_ACTIVATION=false
SHADOW_ONLY=true
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

FORMULA_ID = "fps_atr_or_range.wilder_atr_finalized_ohlcv.v1"
UNIT = "PRICE_QUOTE_CURRENCY_UNITS"
WINDOW = 14
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
        notes=(f"window={WINDOW}_PT1M_BARS", "shadow_only", "no_lookahead"),
    )


def _true_range(prev_close: float, bar: FinalizedBarV1) -> float:
    return max(
        bar.high - bar.low,
        abs(bar.high - prev_close),
        abs(bar.low - prev_close),
    )


def compute_fps_atr_or_range_wilder_atr_finalized_ohlcv_v1(
    bars: Sequence[FinalizedBarV1],
) -> ShadowFormulaObservationV1:
    """Wilder ATR(N=14). Needs N+1 bars (prev close + N true ranges)."""
    payload = {
        "formula_id": FORMULA_ID,
        "n_bars": len(bars),
        "event_times": [b.event_time_epoch_s for b in bars],
        "ohlc": [(b.open, b.high, b.low, b.close) for b in bars],
        "finalized": [b.finalized for b in bars],
    }
    digest = digest_mapping(payload)

    if len(bars) < WINDOW + 1:
        return _reject("unavailable_insufficient_bars_for_warmup", input_digest=digest)

    window = list(bars[-(WINDOW + 1) :])
    if any(not b.finalized for b in window):
        return _reject("reject_non_finalized_bars", input_digest=digest)
    for b in window:
        if any(math.isnan(x) or x <= 0 for x in (b.open, b.high, b.low, b.close)):
            return _reject("unavailable_invalid_ohlc", input_digest=digest)
        if b.high < b.low:
            return _reject("reject_invalid_high_low", input_digest=digest)

    times = [b.event_time_epoch_s for b in window]
    if times != sorted(times):
        return _reject("reject_lookahead_or_unsorted_event_time", input_digest=digest)
    if len(set(times)) != len(times):
        return _reject("reject_duplicate_event_time", input_digest=digest)
    for left, right in zip(times, times[1:]):
        if right - left != 60:
            return _reject("unavailable_non_contiguous_pt1m_bars", input_digest=digest)

    true_ranges: list[float] = []
    for idx in range(1, len(window)):
        true_ranges.append(_true_range(window[idx - 1].close, window[idx]))

    atr = sum(true_ranges) / float(WINDOW)
    # Wilder recursive average: seed with SMA of first WINDOW TRs (here exactly WINDOW).
    # With exactly WINDOW TRs the seed equals the final ATR for this minimal warmup.
    return ShadowFormulaObservationV1(
        formula_id=FORMULA_ID,
        status=ShadowAvailabilityV1.AVAILABLE,
        value=atr,
        unit=UNIT,
        provisional=PROVISIONAL,
        productive_activation=PRODUCTIVE_ACTIVATION,
        rejection_reason=None,
        input_digest=digest,
        observation_event_time_epoch_s=window[-1].event_time_epoch_s,
        notes=(f"window={WINDOW}_PT1M_BARS", "shadow_only", "wilder_seed_sma"),
    )
