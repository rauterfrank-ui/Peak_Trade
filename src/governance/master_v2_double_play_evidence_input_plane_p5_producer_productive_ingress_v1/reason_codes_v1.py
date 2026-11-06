"""P5 producer ingress failure reason codes."""

from __future__ import annotations

from enum import Enum


class ProducerIngressFailureCodeV1(str, Enum):
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_MALFORMED = "artifact_malformed"
    PRODUCER_CLASS_UNSUPPORTED = "producer_class_unsupported"
    PROMOTION_ADMISSION_ABSENT = "promotion_admission_absent"
    PROMOTION_DIGEST_MISMATCH = "promotion_digest_mismatch"
    PROMOTION_SCHEMA_UNSUPPORTED = "promotion_schema_unsupported"
    CONDITIONED_BINDING_REQUIRED = "conditioned_binding_required"
    TERMINATION_CONTEXT_MISSING = "termination_context_missing"
    INSTRUMENT_BINDING_DERIVATION_FAILED = "instrument_binding_derivation_failed"
    OBSERVED_AT_DERIVATION_FAILED = "observed_at_derivation_failed"
    CURRENT_PRODUCTIVE_PRODUCER_ABSENT = "current_productive_producer_absent"
