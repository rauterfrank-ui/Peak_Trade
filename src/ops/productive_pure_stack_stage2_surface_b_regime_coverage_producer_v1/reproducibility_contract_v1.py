"""Reproducibility contract for Surface-B regime-coverage producer v1."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageProducerErrorV1,
    RegimeCoverageProducerResultV1,
)


def assert_reproducibility_invariants_v1(result: RegimeCoverageProducerResultV1) -> None:
    if result.versioned_producer_id != C.VERSIONED_PRODUCER_ID:
        raise RegimeCoverageProducerErrorV1("REPRO_VERSIONED_PRODUCER_ID_MISMATCH")
    if result.threshold_authority_ref != C.THRESHOLD_AUTHORITY_REF:
        raise RegimeCoverageProducerErrorV1("REPRO_THRESHOLD_AUTHORITY_MISMATCH")
    if result.lookback_window_authority_ref != C.LOOKBACK_WINDOW_AUTHORITY_REF:
        raise RegimeCoverageProducerErrorV1("REPRO_LOOKBACK_AUTHORITY_MISMATCH")
    if result.productive_emission is not False:
        raise RegimeCoverageProducerErrorV1("REPRO_PRODUCTIVE_EMISSION_MUST_BE_FALSE")
    if result.coverage_counts is not None:
        raise RegimeCoverageProducerErrorV1("REPRO_COVERAGE_COUNTS_MUST_REMAIN_NULL")
    if result.regime_coverage_instance is not None:
        raise RegimeCoverageProducerErrorV1("REPRO_INSTANCE_MUST_REMAIN_NULL")
    if tuple(result.taxonomy_sink_labels) != C.TAXONOMY_SINK_LABELS:
        raise RegimeCoverageProducerErrorV1("REPRO_TAXONOMY_MISMATCH")
    if not result.producer_digest or len(result.producer_digest) != 64:
        raise RegimeCoverageProducerErrorV1("REPRO_DIGEST_INVALID")


def reproducibility_record_v1(result: RegimeCoverageProducerResultV1) -> Mapping[str, Any]:
    assert_reproducibility_invariants_v1(result)
    return {
        "versioned_producer_id": result.versioned_producer_id,
        "producer_digest": result.producer_digest,
        "as_of_event_time_epoch_s": result.as_of_event_time_epoch_s,
        "instrument_id": result.instrument_id,
        "observation_count": len(result.observations),
        "productive_emission": False,
        "coverage_counts": None,
        "regime_coverage_instance": None,
        "input_authority": C.INPUT_AUTHORITY,
        "runtime_implemented": C.RUNTIME_IMPLEMENTED,
    }
