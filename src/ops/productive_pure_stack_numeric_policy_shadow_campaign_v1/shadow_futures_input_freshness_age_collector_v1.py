"""Shadow futures-input freshness age collector (event-time only).

PRODUCTIVE_ACTIVATION=false
Does not assert productive freshness_state.
Does not apply OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS thresholds.
Does not reuse CMC numeric max-age alpha.
"""

from __future__ import annotations

from typing import Optional

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.models_v1 import (
    FinalizedBarV1,
    FreshnessAgeObservationV1,
    ShadowAvailabilityV1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    digest_mapping,
)

COLLECTOR_ID = "shadow_futures_input_freshness_age_collector.v1"
PRODUCTIVE_ACTIVATION = False
PROVISIONAL = True


def collect_shadow_futures_input_freshness_age_v1(
    *,
    bar: Optional[FinalizedBarV1],
    as_of_event_time_epoch_s: Optional[int],
) -> FreshnessAgeObservationV1:
    """Age = as_of_event_time - bar.event_time. Wallclock is never used as market time."""
    payload = {
        "collector_id": COLLECTOR_ID,
        "bar_event_time": None if bar is None else bar.event_time_epoch_s,
        "as_of_event_time_epoch_s": as_of_event_time_epoch_s,
        "finalized": None if bar is None else bar.finalized,
        "instrument_id": None if bar is None else bar.instrument_id,
    }
    digest = digest_mapping(payload)

    if bar is None or as_of_event_time_epoch_s is None:
        return FreshnessAgeObservationV1(
            instrument_id="" if bar is None else bar.instrument_id,
            status=ShadowAvailabilityV1.UNAVAILABLE,
            age_seconds=None,
            bar_event_time_epoch_s=None if bar is None else bar.event_time_epoch_s,
            as_of_event_time_epoch_s=as_of_event_time_epoch_s,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            rejection_reason="unavailable_missing_bar_or_as_of_event_time",
            input_digest=digest,
            notes=("shadow_only", "no_threshold_applied", "event_time_only"),
        )
    if not bar.finalized:
        return FreshnessAgeObservationV1(
            instrument_id=bar.instrument_id,
            status=ShadowAvailabilityV1.REJECTED,
            age_seconds=None,
            bar_event_time_epoch_s=bar.event_time_epoch_s,
            as_of_event_time_epoch_s=as_of_event_time_epoch_s,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            rejection_reason="reject_non_finalized_bars",
            input_digest=digest,
            notes=("shadow_only", "no_lookahead"),
        )
    if as_of_event_time_epoch_s < bar.event_time_epoch_s:
        return FreshnessAgeObservationV1(
            instrument_id=bar.instrument_id,
            status=ShadowAvailabilityV1.REJECTED,
            age_seconds=None,
            bar_event_time_epoch_s=bar.event_time_epoch_s,
            as_of_event_time_epoch_s=as_of_event_time_epoch_s,
            provisional=PROVISIONAL,
            productive_activation=PRODUCTIVE_ACTIVATION,
            rejection_reason="reject_lookahead_as_of_before_bar_event_time",
            input_digest=digest,
            notes=("shadow_only", "no_lookahead"),
        )

    age = int(as_of_event_time_epoch_s - bar.event_time_epoch_s)
    return FreshnessAgeObservationV1(
        instrument_id=bar.instrument_id,
        status=ShadowAvailabilityV1.AVAILABLE,
        age_seconds=age,
        bar_event_time_epoch_s=bar.event_time_epoch_s,
        as_of_event_time_epoch_s=as_of_event_time_epoch_s,
        provisional=PROVISIONAL,
        productive_activation=PRODUCTIVE_ACTIVATION,
        rejection_reason=None,
        input_digest=digest,
        notes=(
            "shadow_only",
            "provisional",
            "no_owner_threshold_applied",
            "not_cmc_numeric_max_age",
            "not_freshness_state_authority",
        ),
    )
