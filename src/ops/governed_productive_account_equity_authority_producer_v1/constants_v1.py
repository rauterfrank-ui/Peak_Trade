"""Governed account-equity authority-owner slot.

Owner assignment plus typed sample schema, typed venue-witness
observation contract, typed normalization/inclusion adjudication schema,
and typed internal reconstruction contract schema, plus typed
reconstruction algebra contract schema, plus typed P01
haircut/reserve-depletion term contract schema, plus typed P01
term-set and unit-class adjudication contract schema, plus typed P01
applicability adjudication contract schema, plus typed P01
equity-base inclusion adjudication contract schema, plus typed P01
broader embedding-state adjudication contract schema. No producer
implementation. No runtime source object. No mapping. No value
binding. No Live-account-bound join. No wire.
"""

from __future__ import annotations

CAPABILITY_ID = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER_V1"
PACKAGE_MARKER = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER_V1=true"
OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
SCHEMA_VERSION = "governed_productive_account_equity_authority_producer.v1"
CONTRACT_VERSION = "v1"

ACCOUNT_EQUITY_AUTHORITY_OWNER = "ops.governed_productive_account_equity_authority_producer_v1"
ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS = "GOVERNED_PRODUCTIVE_ACCOUNT_EQUITY_AUTHORITY_PRODUCER"
OWNER_ASSIGNMENT_RATIFIED = True
SLOT_KIND = "EMPTY_GOVERNED_AUTHORITY_OWNER_SLOT"
SLOT_IS_EMPTY = True
C01_C16_NOT_ELEVATED = True
STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER = True
PRODUCER_IMPLEMENTATION_PRESENT = False
GOVERNED_PRODUCER_CREATED = False
GOVERNED_PRODUCTIVE_SOURCE_PRESENT = False
SOURCE_OBJECT_PRESENT = False
SOURCE_OBJECT_PRESENT_SEMANTICS = "RUNTIME_SAMPLE_INSTANCE_NOT_SCHEMA_DEFINITION"
SOURCE_SELECTED = False
GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT = True
VENUE_WITNESS_SCHEMA_PRESENT = True
VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT = False
VENUE_WITNESS_SELECTED = False
WITNESS_CONTRACT_MISSING_CLOSED = True
NORMALIZATION_SCHEMA_PRESENT = True
NORMALIZATION_RUNTIME_INSTANCE_PRESENT = False
NORMALIZATION_CONTRACT_MISSING_CLOSED = True
NORMALIZATION_AUTHORITY_EFFECT = "NONE"
FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT = True
FIELD_TO_DIMENSION_MAPPING_PRESENT = False
SEMANTIC_MAPPING_PROVEN = False
INCLUSION_PROVEN = False
INTERNAL_RECONSTRUCTION_CREATED = False
INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT = True
INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT = False
INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED = True
INTERNAL_RECONSTRUCTION_PROVEN = False
INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT = "NONE"
RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT = True
RECONSTRUCTION_ALGEBRA_COMPLETE = False
RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT = "NONE"
P01_TERM_CONTRACT_SCHEMA_PRESENT = True
P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_TERM_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_TERM_SEMANTICS_RESOLVED = False
P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED = False
P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT = True
P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_TERM_SET_RESOLVED = False
P01_VALUE_UNIT_CLASS_RESOLVED = False
P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT = True
P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_APPLICABILITY_RESOLVED = False
P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT = True
P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_EQUITY_BASE_INCLUSION_RESOLVED = False
P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT = True
P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_EMBEDDED_STATE_RESOLVED = False
LIVE_RESTART_RECONSTRUCTED = False
RECONCILIATION_CONTRACT_CREATED = False
DIVERGENCE_POLICY_CREATED = False
OBSERVATION_AUTHORITY_EFFECT = "NONE"
EQUITY_DIMENSION_BOUND = False
MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING = False
RAW_TO_WITNESS_PROVEN = False
RUNTIME_VALUE_PRESENT = False
SAMPLE_PRESENT = False
LIVE_ACCOUNT_BOUND_JOIN_PRESENT = False
CORE_LOGIC_CHANGE = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
NUMERIC_EQUITY_TTL_SECONDS = 5
SAMPLE_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "dimension_id",
    "bound_account_identity",
    "bound_venue_identity",
    "bound_td_mode",
    "settlement_currency",
    "value",
    "value_semantics",
    "producer_identity",
    "authority_contract_ref",
    "source_revision_or_digest",
    "input_set_digest",
    "decision_epoch",
    "observed_at/as_of",
    "freshness_max_age",
    "freshness_policy_status",
    "restart_reconciliation_status",
    "component_completeness",
    "component_provenance",
    "inclusion_vector",
    "component_term_vector",
    "double_count_guards",
    "currency_conversion_status",
    "witness_reconciliation_status",
    "policy_version",
    "semantic_digest",
    "sample_id",
    "observation_vs_authority_class",
)
WITNESS_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "witness_id",
    "bound_account_identity",
    "bound_venue_identity",
    "rest_host",
    "bound_td_mode",
    "account_mode",
    "currency_domain",
    "endpoint",
    "method",
    "request_identity",
    "decision_epoch",
    "observed_at/as_of",
    "response_received_at",
    "provider_timestamp",
    "raw_field_path",
    "observation_semantic_class",
    "raw_value_representation",
    "presence_state",
    "raw_payload_state",
    "payload_digest",
    "raw_payload",
    "request_provenance",
    "response_provenance",
    "observation_vs_authority_class",
    "observation_authority_effect",
    "equity_dimension_bound_status",
    "mapping_status",
    "freshness_evidence_status",
    "clock_source_status",
    "provenance_digest",
)
NORMALIZATION_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "adjudication_id",
    "source_witness_id",
    "bound_account_identity",
    "bound_venue_identity",
    "rest_host",
    "bound_td_mode",
    "account_mode",
    "currency_domain",
    "decision_epoch",
    "raw_field_path",
    "observation_semantic_class",
    "raw_value_representation",
    "presence_state",
    "requested_target_dimension_id",
    "field_to_dimension_mapping_status",
    "observation_participation_state",
    "normalizable_status",
    "semantic_mapping_status",
    "inclusion_status",
    "source_selection_status",
    "observation_vs_authority_class",
    "normalization_authority_effect",
    "exclusion_reason_codes",
    "account_scope_compatibility_status",
    "currency_domain_compatibility_status",
    "unit_compatibility_status",
    "freshness_evidence_status",
    "freshness_evidence_ref",
    "provenance_status",
    "ambiguity_status",
    "contradiction_status",
    "semantic_mapping_proven_status",
    "inclusion_proven_status",
    "source_selected_status",
    "provenance_digest",
)
RECONSTRUCTION_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "reconstruction_id",
    "source_normalization_adjudication_id",
    "bound_account_identity",
    "bound_venue_identity",
    "rest_host",
    "bound_td_mode",
    "account_mode",
    "currency_domain",
    "reconstruction_epoch",
    "target_semantic_dimension_id",
    "reconstruction_semantic_class",
    "reconstruction_semantic_class_version",
    "inclusion_vector",
    "component_term_vector",
    "component_completeness",
    "reconstruction_algebra_status",
    "reconstruction_algebra_representation",
    "reconstructed_value_state",
    "reconstructed_value_representation",
    "contradiction_status",
    "same_epoch_status",
    "freshness_status",
    "freshness_evidence_ref",
    "restart_invalidation_status",
    "restart_provenance_class",
    "reconstruction_eligibility",
    "reconstruction_proven_status",
    "observation_vs_authority_class",
    "internal_reconstruction_authority_effect",
    "provenance_digest",
)
ALGEBRA_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "algebra_contract_id",
    "algebra_contract_version",
    "reconstruction_contract_schema_class",
    "target_semantic_dimension_id",
    "algebra_representation",
    "algebra_completeness_status",
    "canonical_formula_status",
    "canonical_formula_representation",
    "unresolved_required_terms",
    "contradiction_status",
    "currency_unit_compatibility_status",
    "valuation_dependency_status",
    "reconstruction_algebra_authority_effect",
    "term_vector",
    "provenance_digest",
)
P01_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_term_contract_id",
    "p01_term_contract_version",
    "algebra_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "semantic_class",
    "algebraic_role",
    "economic_meaning",
    "value_unit_class",
    "currency_valuation_domain",
    "applicability_state",
    "provenance_requirements",
    "origin_class",
    "inclusion_state",
    "embedded_state",
    "overlap_state",
    "double_counting_guard",
    "sign_constraints",
    "negative_allowed",
    "zero_validity_semantics",
    "freshness_epoch_requirements",
    "completeness_resolution_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "p01_term_contract_authority_effect",
    "numeric_state",
    "provenance_digest",
)
P01_TERM_SET_AND_UNIT_CLASS_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_term_set_and_unit_class_contract_id",
    "p01_term_set_and_unit_class_contract_version",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "family_class_labels",
    "family_labels_are_not_exact_term_set",
    "p01_term_set",
    "p01_term_set_resolved_status",
    "p01_term_set_adjudication",
    "p01_value_unit_class",
    "p01_value_unit_class_resolved_status",
    "p01_value_unit_class_adjudication",
    "currency_valuation_domain",
    "algebraic_role",
    "sign_constraints",
    "negative_allowed",
    "rejected_term_set_inferences",
    "rejected_unit_class_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_term_set_and_unit_class_contract_authority_effect",
    "provenance_digest",
)
P01_APPLICABILITY_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_applicability_contract_id",
    "p01_applicability_contract_version",
    "parent_p01_term_set_and_unit_class_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_applicability_status",
    "p01_applicability_resolved_status",
    "p01_applicability_rule",
    "p01_applicability_adjudication",
    "typed_applicability_state",
    "unknown_is_not_not_applicable",
    "zero_is_not_not_applicable",
    "absence_is_not_not_applicable",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "term_set_unresolved_does_not_decide_applicability",
    "unit_unresolved_does_not_decide_applicability",
    "rejected_applicability_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_applicability_contract_authority_effect",
    "provenance_digest",
)
P01_EQUITY_BASE_INCLUSION_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_equity_base_inclusion_contract_id",
    "p01_equity_base_inclusion_contract_version",
    "parent_p01_applicability_contract_schema_class",
    "parent_p01_term_set_and_unit_class_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_equity_base_inclusion_status",
    "p01_equity_base_inclusion_resolved_status",
    "p01_equity_base_inclusion_rule",
    "p01_equity_base_inclusion_adjudication",
    "typed_inclusion_state",
    "unknown_is_not_excluded",
    "zero_is_not_embedded_or_excluded",
    "absence_is_not_not_embedded",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "term_set_unresolved_does_not_decide_inclusion",
    "applicability_unresolved_does_not_decide_inclusion",
    "unit_unresolved_does_not_decide_inclusion",
    "separate_schema_does_not_prove_independent_deduction",
    "unknown_inclusion_cannot_authorize_subtraction",
    "unknown_inclusion_cannot_authorize_omission",
    "no_double_counting_permission",
    "rejected_inclusion_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_equity_base_inclusion_contract_authority_effect",
    "provenance_digest",
)
P01_EMBEDDING_STATE_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_embedding_state_contract_id",
    "p01_embedding_state_contract_version",
    "parent_p01_equity_base_inclusion_contract_schema_class",
    "parent_p01_applicability_contract_schema_class",
    "parent_p01_term_set_and_unit_class_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_embedded_state",
    "p01_embedded_state_resolved_status",
    "p01_embedding_rule",
    "p01_embedding_adjudication",
    "typed_embedding_state",
    "family_level_embedding_state",
    "member_level_embedding_state",
    "economic_overlap_state",
    "representational_nesting_state",
    "arithmetic_inclusion_state",
    "semantic_equivalence_state",
    "p01_overlap_state",
    "unknown_is_not_not_embedded",
    "unknown_is_not_embedded",
    "zero_does_not_prove_embedding",
    "absence_does_not_prove_embedding",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "term_set_unresolved_does_not_decide_embedding",
    "applicability_unresolved_does_not_decide_embedding",
    "unit_unresolved_does_not_decide_embedding",
    "equity_base_inclusion_unresolved_does_not_decide_broader_embedding",
    "u04_u05_u06_labels_do_not_decide_embedding",
    "equal_values_do_not_prove_embedding",
    "shared_source_does_not_prove_embedding",
    "separate_schema_does_not_prove_independence",
    "unknown_embedding_cannot_authorize_subtraction",
    "unknown_embedding_cannot_authorize_omission",
    "unknown_embedding_cannot_authorize_netting",
    "no_double_counting_permission",
    "rejected_embedding_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_embedding_state_contract_authority_effect",
    "provenance_digest",
)
