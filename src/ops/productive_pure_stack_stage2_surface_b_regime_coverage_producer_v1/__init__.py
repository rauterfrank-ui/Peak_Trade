"""Dedicated Surface-B regime-coverage producer v1 package."""

from __future__ import annotations

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.constants_v1 import (
    AUTHORIZE_DETAIL_FIELD_VALUES,
    CANONICAL_PRODUCER_NAME,
    CANONICAL_PRODUCER_VERSION,
    PACKAGE_MARKER,
    VERSIONED_PRODUCER_ID,
)

__all__ = [
    "AUTHORIZE_DETAIL_FIELD_VALUES",
    "CANONICAL_PRODUCER_NAME",
    "CANONICAL_PRODUCER_VERSION",
    "PACKAGE_MARKER",
    "VERSIONED_PRODUCER_ID",
    "RegimeCoverageBarInputV1",
    "RegimeCoverageLabelObservationV1",
    "RegimeCoverageProducerErrorV1",
    "RegimeCoverageProducerResultV1",
    "produce_regime_coverage_labels_v1",
]


def __getattr__(name: str):
    if name in {
        "RegimeCoverageBarInputV1",
        "RegimeCoverageLabelObservationV1",
        "RegimeCoverageProducerErrorV1",
        "RegimeCoverageProducerResultV1",
    }:
        from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
            models_v1,
        )

        return getattr(models_v1, name)
    if name == "produce_regime_coverage_labels_v1":
        from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.producer_v1 import (
            produce_regime_coverage_labels_v1,
        )

        return produce_regime_coverage_labels_v1
    raise AttributeError(name)
