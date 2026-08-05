"""Label semantics for Surface-B regime-coverage taxonomy sink.

Exclusive sink: low | mid | high | unknown | missing

Without Owner-ratified threshold/lookback authority, productive low/mid/high
classification is forbidden. The producer emits ``missing`` (thresholds unset)
or ``unknown`` (inputs present but not classifiable under ratified rules).
"""

from __future__ import annotations

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_producer_v1.models_v1 import (
    RegimeCoverageProducerErrorV1,
)

LABEL_MISSING = "missing"
LABEL_UNKNOWN = "unknown"
LABEL_LOW = "low"
LABEL_MID = "mid"
LABEL_HIGH = "high"

MISSING_REASON_THRESHOLDS_UNSET = "OWNER_NUMERIC_THRESHOLD_AND_LOOKBACK_UNSET"
UNKNOWN_REASON_INPUT_INCOMPLETE = "INPUT_PRESENT_BUT_NOT_CLASSIFIABLE_UNDER_RATIFIED_RULES"


def assert_label_in_taxonomy(label: str) -> None:
    if label not in C.TAXONOMY_SINK_LABELS:
        raise RegimeCoverageProducerErrorV1(f"FOREIGN_TAXONOMY_LABEL_FORBIDDEN:{label}")


def assert_no_foreign_taxonomy_derivation(label: str) -> None:
    assert_label_in_taxonomy(label)


def resolve_label_without_owner_thresholds_v1(*, input_complete: bool) -> tuple[str, str]:
    """Fail-closed label resolution when Owner thresholds/lookbacks remain unset.

    Never invents low/mid/high magnitudes.
    """
    if C.THRESHOLD_AUTHORITY_REF != "OWNER_NUMERIC_THRESHOLD_AUTHORITY_UNSET_V1":
        raise RegimeCoverageProducerErrorV1("THRESHOLD_AUTHORITY_UNEXPECTED")
    if C.LOOKBACK_WINDOW_AUTHORITY_REF != "OWNER_NUMERIC_LOOKBACK_AUTHORITY_UNSET_V1":
        raise RegimeCoverageProducerErrorV1("LOOKBACK_AUTHORITY_UNEXPECTED")
    if C.CLASSIFY_LOW_MID_HIGH_WITHOUT_OWNER_THRESHOLDS:
        raise RegimeCoverageProducerErrorV1("LOW_MID_HIGH_WITHOUT_OWNER_THRESHOLDS_FORBIDDEN")
    if input_complete:
        label = LABEL_MISSING
        reason = MISSING_REASON_THRESHOLDS_UNSET
    else:
        label = LABEL_UNKNOWN
        reason = UNKNOWN_REASON_INPUT_INCOMPLETE
    assert_no_foreign_taxonomy_derivation(label)
    return label, reason
