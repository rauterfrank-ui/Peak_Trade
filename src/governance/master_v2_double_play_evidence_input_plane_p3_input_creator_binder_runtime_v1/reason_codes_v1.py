"""Fail-closed reason codes for P3 Component B binding intake."""

from __future__ import annotations

from enum import Enum


class LayerInputBindingIntakeFailureCodeV1(str, Enum):
    REQUEST_MISSING = "request_missing"
    BINDING_ID_MISSING = "binding_id_missing"
    ADJUDICATION_NOT_ADMIT = "adjudication_not_admit"
    ENVELOPE_MISSING = "envelope_missing"
    ENVELOPE_DIGEST_MISSING = "envelope_digest_missing"
    TARGET_LAYER_INVALID = "target_layer_invalid"
    TARGET_CONTRACT_VERSION_UNSUPPORTED = "target_contract_version_unsupported"
    INSTRUMENT_BINDING_MISMATCH = "instrument_binding_mismatch"
    EPOCH_BINDING_MISMATCH = "epoch_binding_mismatch"
    NULLEPOCH_INVALID = "nullline_provenance_epoch_invalid"
    DIRECT_PRODUCER_TO_B_FORBIDDEN = "direct_producer_to_b_forbidden"
    DUPLICATE_BINDING_DIVERGENT = "duplicate_binding_divergent"
    BINDING_CONTRACT_VALIDATION_FAILED = "binding_contract_validation_failed"
    TYPED_INPUT_VALIDATION_FAILED = "typed_input_validation_failed"
