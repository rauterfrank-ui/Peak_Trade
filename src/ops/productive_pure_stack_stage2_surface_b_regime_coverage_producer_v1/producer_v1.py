"""Dedicated Surface-B regime-coverage producer v1.

Versioned, deterministic, PIT-safe producer scaffold under Authority Surface B.
Does not invent thresholds, lookbacks, or coverage counts. Does not flip
INPUT_AUTHORITY, start campaigns, create raw packs, or change trading logic.
"""

from __future__ import annotations

from typing import Sequence

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.boundary_guards_v1 import (
    assert_forbidden_effects_remain_false_v1,
    assert_source_not_forbidden_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.digest_contract_v1 import (
    compute_regime_coverage_producer_digest_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.label_semantics_v1 import (
    resolve_label_without_owner_thresholds_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
    RegimeCoverageLabelObservationV1,
    RegimeCoverageProducerErrorV1,
    RegimeCoverageProducerResultV1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.pit_rules_v1 import (
    assert_chronological_unique_buckets,
    assert_pit_no_lookahead_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.reproducibility_contract_v1 import (
    assert_reproducibility_invariants_v1,
)


def _assert_bar_sane(bar: RegimeCoverageBarInputV1) -> None:
    if not isinstance(bar.instrument_id, str) or not bar.instrument_id.strip():
        raise RegimeCoverageProducerErrorV1("INSTRUMENT_ID_REQUIRED")
    for name in ("open", "high", "low", "close", "mark_price", "volume"):
        value = getattr(bar, name)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise RegimeCoverageProducerErrorV1(f"BAR_FIELD_TYPE_INVALID:{name}")
        if name != "volume" and float(value) <= 0:
            raise RegimeCoverageProducerErrorV1(f"BAR_FIELD_NONPOSITIVE:{name}")
        if name == "volume" and float(value) < 0:
            raise RegimeCoverageProducerErrorV1("BAR_VOLUME_NEGATIVE")
    if float(bar.high) < float(bar.low):
        raise RegimeCoverageProducerErrorV1("BAR_HIGH_LT_LOW")
    if not (float(bar.low) <= float(bar.open) <= float(bar.high)):
        raise RegimeCoverageProducerErrorV1("BAR_OPEN_OUT_OF_RANGE")
    if not (float(bar.low) <= float(bar.close) <= float(bar.high)):
        raise RegimeCoverageProducerErrorV1("BAR_CLOSE_OUT_OF_RANGE")


def produce_regime_coverage_labels_v1(
    *,
    instrument_id: str,
    as_of_event_time_epoch_s: int,
    bars: Sequence[RegimeCoverageBarInputV1],
) -> RegimeCoverageProducerResultV1:
    """Produce taxonomy labels without inventing Owner numeric thresholds.

    While threshold/lookback authority remains UNSET, every complete bar is
    labeled ``missing``. Incomplete bars are labeled ``unknown``. Coverage
    counts and campaign instance fields remain null.
    """
    assert_forbidden_effects_remain_false_v1()
    assert_source_not_forbidden_v1(C.CANONICAL_PRODUCER_NAME)
    if not isinstance(instrument_id, str) or not instrument_id.strip():
        raise RegimeCoverageProducerErrorV1("INSTRUMENT_ID_REQUIRED")
    if not bars:
        raise RegimeCoverageProducerErrorV1("BARS_REQUIRED")

    assert_chronological_unique_buckets(bars)
    assert_pit_no_lookahead_v1(bars, as_of_event_time_epoch_s=as_of_event_time_epoch_s)

    observations: list[RegimeCoverageLabelObservationV1] = []
    for bar in bars:
        if bar.instrument_id != instrument_id:
            raise RegimeCoverageProducerErrorV1("MULTI_INSTRUMENT_FORBIDDEN")
        _assert_bar_sane(bar)
        input_complete = (
            bar.finalized
            and float(bar.mark_price) > 0
            and float(bar.close) > 0
            and float(bar.volume) >= 0
        )
        label, reason = resolve_label_without_owner_thresholds_v1(input_complete=input_complete)
        observations.append(
            RegimeCoverageLabelObservationV1(
                event_time_epoch_s=int(bar.event_time_epoch_s),
                label=label,
                reason=reason,
            )
        )

    digest = compute_regime_coverage_producer_digest_v1(
        instrument_id=instrument_id,
        as_of_event_time_epoch_s=as_of_event_time_epoch_s,
        bars=bars,
        observations=observations,
    )
    result = RegimeCoverageProducerResultV1(
        versioned_producer_id=C.VERSIONED_PRODUCER_ID,
        instrument_id=instrument_id,
        as_of_event_time_epoch_s=int(as_of_event_time_epoch_s),
        observations=tuple(observations),
        producer_digest=digest,
        taxonomy_sink_labels=C.TAXONOMY_SINK_LABELS,
        threshold_authority_ref=C.THRESHOLD_AUTHORITY_REF,
        lookback_window_authority_ref=C.LOOKBACK_WINDOW_AUTHORITY_REF,
        productive_emission=False,
        coverage_counts=None,
        regime_coverage_instance=None,
    )
    assert_reproducibility_invariants_v1(result)
    return result
