"""Determinism contract for Surface-B regime-coverage producer v1."""

from __future__ import annotations

from typing import Sequence

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageBarInputV1,
    RegimeCoverageProducerResultV1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.producer_v1 import (
    produce_regime_coverage_labels_v1,
)


def assert_deterministic_reproduction_v1(
    *,
    instrument_id: str,
    as_of_event_time_epoch_s: int,
    bars: Sequence[RegimeCoverageBarInputV1],
) -> RegimeCoverageProducerResultV1:
    """Same inputs must yield identical digests and observation sequences."""
    first = produce_regime_coverage_labels_v1(
        instrument_id=instrument_id,
        as_of_event_time_epoch_s=as_of_event_time_epoch_s,
        bars=bars,
    )
    second = produce_regime_coverage_labels_v1(
        instrument_id=instrument_id,
        as_of_event_time_epoch_s=as_of_event_time_epoch_s,
        bars=bars,
    )
    if first.producer_digest != second.producer_digest:
        raise AssertionError("DETERMINISM_DIGEST_MISMATCH")
    if first.to_dict() != second.to_dict():
        raise AssertionError("DETERMINISM_PAYLOAD_MISMATCH")
    return first
