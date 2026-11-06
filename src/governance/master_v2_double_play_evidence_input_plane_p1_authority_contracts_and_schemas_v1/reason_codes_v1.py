"""Fail-closed reason codes for P1 Evidence & Input Plane contracts."""

from __future__ import annotations

from enum import Enum


class EvidenceEnvelopeFailureCodeV1(str, Enum):
    ENVELOPE_MISSING = "envelope_missing"
    SCHEMA_VERSION_UNSUPPORTED = "schema_version_unsupported"
    ENVELOPE_ID_MISSING = "envelope_id_missing"
    PRODUCER_FAMILY_INVALID = "producer_family_invalid"
    EVIDENCE_KIND_INVALID = "evidence_kind_invalid"
    TRADING_AUTHORITY_NOT_NONE = "trading_authority_not_none"
    INSTRUMENT_ID_MISSING = "instrument_id_missing"
    VENUE_MISSING = "venue_missing"
    VENUE_INSTRUMENT_ID_MISSING = "venue_instrument_id_missing"
    EPOCH_MISSING = "epoch_missing"
    EPOCH_INVALID = "epoch_invalid"
    OBSERVED_AT_MISSING = "observed_at_unix_missing"
    OBSERVED_AT_INVALID = "observed_at_unix_invalid"
    FRESHNESS_HORIZON_MISSING = "freshness_horizon_seconds_missing"
    FRESHNESS_HORIZON_INVALID = "freshness_horizon_seconds_invalid"
    FRESHNESS_STALE = "freshness_stale"
    PROVENANCE_MISSING = "provenance_refs_missing"
    PROVENANCE_EMPTY = "provenance_refs_empty"
    SOURCE_EVIDENCE_DIGEST_MISSING = "source_evidence_digest_missing"
    SOURCE_EVIDENCE_DIGEST_INVALID = "source_evidence_digest_invalid"
    TYPED_PAYLOAD_DIGEST_MISSING = "typed_payload_digest_missing"
    TYPED_PAYLOAD_DIGEST_INVALID = "typed_payload_digest_invalid"
    DIRECT_PRODUCER_TO_B_FORBIDDEN = "direct_producer_to_b_forbidden"
    DIRECT_PRODUCER_TO_DP_FORBIDDEN = "direct_producer_to_dp_forbidden"


class DpLayerBindingFailureCodeV1(str, Enum):
    BINDING_MISSING = "binding_missing"
    SCHEMA_VERSION_UNSUPPORTED = "schema_version_unsupported"
    BINDING_ID_MISSING = "binding_id_missing"
    TARGET_LAYER_INVALID = "target_layer_invalid"
    ENVELOPE_DIGEST_MISSING = "envelope_digest_missing"
    ENVELOPE_DIGEST_INVALID = "envelope_digest_invalid"
    ENVELOPE_DIGEST_MISMATCH = "envelope_digest_mismatch"
    INSTRUMENT_BINDING_MISMATCH = "instrument_binding_mismatch"
    EPOCH_BINDING_MISMATCH = "epoch_binding_mismatch"
    TRADING_AUTHORITY_NOT_NONE = "trading_authority_not_none"
    DP_STATE_MUTATION_FORBIDDEN = "dp_state_mutation_forbidden"
    PROPOSED_D_T_FIELD_FORBIDDEN = "proposed_d_t_field_forbidden"
    D_T_FIELD_FORBIDDEN = "d_t_field_forbidden"
    FINAL_D_T_FIELD_FORBIDDEN = "final_d_t_field_forbidden"
    B_MAY_NOT_COMPUTE_FINAL_D_T = "b_may_not_compute_final_d_t"
    B_MAY_NOT_SELECT_D_T_FORMULA = "b_may_not_select_d_t_formula"
    COLLAPSE_TO_PROPOSED_D_T_FORBIDDEN = "collapse_to_proposed_d_t_forbidden"
    ENVELOPE_NOT_ADJUDICATED = "envelope_not_adjudicated"
    DIRECT_PRODUCER_TO_B_FORBIDDEN = "direct_producer_to_b_forbidden"


class L6TypedEvidenceInputFailureCodeV1(str, Enum):
    INPUT_MISSING = "input_missing"
    SCHEMA_VERSION_UNSUPPORTED = "schema_version_unsupported"
    LAYER_TARGET_INVALID = "layer_target_invalid"
    BINDING_DIGEST_MISMATCH = "binding_digest_mismatch"
    INTERPRETATION_AUTHORITY_NOT_L6 = "interpretation_authority_not_l6"
    NUMERIC_D_T_FIELD_FORBIDDEN = "numeric_d_t_field_forbidden"
    PROPOSED_D_T_FIELD_FORBIDDEN = "proposed_d_t_field_forbidden"


class AuthorityInvariantFailureCodeV1(str, Enum):
    RUNTIME_A_IMPLEMENTATION_FORBIDDEN = "runtime_a_implementation_forbidden"
    RUNTIME_B_IMPLEMENTATION_FORBIDDEN = "runtime_b_implementation_forbidden"
    PRODUCTIVE_BINDING_FORBIDDEN = "productive_binding_forbidden"
    OWNER_DECISION_DRIFT = "owner_decision_drift"
