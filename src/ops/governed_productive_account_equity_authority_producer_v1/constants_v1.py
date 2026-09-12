"""Governed account-equity authority-owner slot.

Owner assignment plus typed sample schema, typed venue-witness
observation contract, typed normalization/inclusion adjudication schema,
and typed internal reconstruction contract schema, plus typed
reconstruction algebra contract schema, plus typed P01
haircut/reserve-depletion term contract schema, plus typed P01
term-set and unit-class adjudication contract schema, plus typed P01
applicability adjudication contract schema, plus typed P01
equity-base inclusion adjudication contract schema, plus typed P01
broader embedding-state adjudication contract schema, plus typed P01
overlap/equivalence adjudication versus U04 and U05, plus typed P01
numeric value provenance adjudication, plus typed P01 member freshness
inheritance adjudication, plus typed P01 haircut/reserve/depletion
semantics adjudication, plus typed P01 exact member identity
ratification, plus typed P01 value unit class ratification.
No producer implementation. No
runtime source object. No mapping. No value binding. No
Live-account-bound join. No wire.
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
P01_TERM_SET_RESOLVED = True
P01_VALUE_UNIT_CLASS_RESOLVED = True
P01_VALUE_UNIT_CLASS = "ABSOLUTE_MONETARY_REDUCTION_AMOUNT"
P01_SEMANTIC_DIMENSION = "PARENT_EQUITY_DIMENSION_REDUCTION_AMOUNT"
P01_PARENT_DIMENSION_COMPATIBILITY = (
    "SAME_DIMENSION_CLASS_AS_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
)
P01_REQUIRES_DIMENSIONAL_TRANSFORMATION = False
P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE = True
P01_UNIT_IDENTITY_IS_DISTINCT_FROM_AUTHORITY_IDENTITY = True
P01_UNIT_IDENTITY_IS_DISTINCT_FROM_MEMBER_IDENTITY = True
P01_SETTLEMENT_CURRENCY_IS_NOT_UNIT_IDENTITY = True
P01_PARENT_DIMENSION_IS_NOT_AUTHORITY_SOURCE = True
P01_VALUE_UNIT_CLASS_SELECTED_OPTION = "P01_OP_VU_ABSOLUTE_MONETARY_REDUCTION_V1"
P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT = True
P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_EXACT_MEMBER_IDENTITY_SET = "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION"
P01_EXACT_MEMBER_COUNT = 1
P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT = True
P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED = False
P01_ZERO_ABSENCE_NA_RESOLVED = False
P01_COMBINATION_PRECEDENCE_RESOLVED = False
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
P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT = True
P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_U04_OVERLAP_RESOLVED = False
P01_U05_OVERLAP_RESOLVED = False
P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT = True
P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_NUMERIC_VALUE_PROVENANCE_RESOLVED = False
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT = True
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED = False
P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT = True
P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT = False
P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT = "NONE"
P01_HAIRCUT_SEMANTICS_RESOLVED = False
P01_RESERVE_SEMANTICS_RESOLVED = False
P01_DEPLETION_SEMANTICS_RESOLVED = False
P01_RUNTIME_INSTANCE_PRESENT = False
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
P01_OVERLAP_WITH_U04_U05_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_overlap_with_u04_u05_contract_id",
    "p01_overlap_with_u04_u05_contract_version",
    "parent_p01_embedding_state_contract_schema_class",
    "parent_p01_equity_base_inclusion_contract_schema_class",
    "parent_p01_applicability_contract_schema_class",
    "parent_p01_term_set_and_unit_class_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_u04_overlap_state",
    "p01_u04_overlap_resolved_status",
    "p01_u04_overlap_adjudication",
    "typed_u04_overlap_state",
    "p01_u05_overlap_state",
    "p01_u05_overlap_resolved_status",
    "p01_u05_overlap_adjudication",
    "typed_u05_overlap_state",
    "semantic_equivalence_state",
    "economic_overlap_state",
    "representational_nesting_state",
    "shared_provenance_state",
    "shared_numeric_value_state",
    "shared_unit_state",
    "simultaneous_applicability_state",
    "arithmetic_interaction_state",
    "p01_overlap_state",
    "u06_accrued_fees_distinct_pin",
    "unknown_is_not_disjoint",
    "unknown_is_not_equivalent",
    "unknown_is_not_non_overlapping",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "zero_does_not_prove_non_overlap",
    "absence_does_not_prove_disjoint",
    "equal_values_do_not_prove_equivalence",
    "shared_source_does_not_prove_equivalence",
    "shared_unit_does_not_prove_equivalence",
    "term_set_unresolved_does_not_decide_overlap",
    "applicability_unresolved_does_not_decide_overlap",
    "embedding_unresolved_does_not_decide_overlap",
    "u04_u05_labels_do_not_decide_overlap",
    "u06_distinctness_does_not_decide_p01_u06",
    "unknown_overlap_cannot_authorize_summation",
    "unknown_overlap_cannot_authorize_deduplication",
    "unknown_overlap_cannot_authorize_netting",
    "unknown_overlap_cannot_authorize_subtraction",
    "unknown_overlap_cannot_authorize_omission",
    "no_double_counting_permission",
    "rejected_overlap_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_overlap_with_u04_u05_contract_authority_effect",
    "provenance_digest",
)
P01_NUMERIC_VALUE_PROVENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_numeric_value_provenance_contract_id",
    "p01_numeric_value_provenance_contract_version",
    "parent_p01_overlap_with_u04_u05_contract_schema_class",
    "parent_p01_embedding_state_contract_schema_class",
    "parent_p01_equity_base_inclusion_contract_schema_class",
    "parent_p01_applicability_contract_schema_class",
    "parent_p01_term_set_and_unit_class_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_numeric_value_provenance_resolved_status",
    "p01_numeric_value_provenance_status",
    "p01_numeric_value_source",
    "p01_numeric_value_transformation",
    "typed_provenance_class",
    "producer_state",
    "source_object_id",
    "source_field_id",
    "source_contract_id",
    "transformation_chain_state",
    "time_semantics_state",
    "unit_dimension_transform_state",
    "missing_value_treatment",
    "stale_value_treatment",
    "unavailable_value_treatment",
    "contradictory_value_treatment",
    "partial_evidence_treatment",
    "multiple_candidate_treatment",
    "fallback_source_state",
    "numeric_computation_rule_state",
    "haircut_reserve_depletion_construction_state",
    "unknown_is_not_numeric_authorization",
    "unspecified_is_not_numeric_authorization",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "zero_is_not_p01_value",
    "absence_is_not_p01_value",
    "venue_field_is_not_p01_value",
    "name_similarity_does_not_prove_source",
    "numeric_equality_does_not_prove_source",
    "policy_slot_is_not_numeric_source",
    "algebra_slot_is_not_numeric_source",
    "unspecified_haircut_cannot_construct_p01",
    "unspecified_cannot_authorize_subtraction",
    "unspecified_cannot_authorize_addition",
    "unspecified_cannot_authorize_netting",
    "unspecified_cannot_authorize_omission",
    "unspecified_cannot_authorize_ignore",
    "rejected_provenance_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "candidate_sources_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_numeric_value_provenance_contract_authority_effect",
    "provenance_digest",
)
P01_MEMBER_FRESHNESS_INHERITANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_member_freshness_inheritance_contract_id",
    "p01_member_freshness_inheritance_contract_version",
    "parent_p01_numeric_value_provenance_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "p01_member_freshness_inheritance_resolved_status",
    "p01_member_freshness_status",
    "p01_member_freshness_rule",
    "p01_u09_freshness_relation",
    "p01_freshness_dimension_state",
    "p01_timestamp_state",
    "p01_level_freshness_metadata_state",
    "member_level_freshness_metadata_state",
    "inheritance_rule_state",
    "u09_comparison_evidence_only",
    "u09_is_not_p01_freshness_authority",
    "p01_freshness_does_not_inherit_u09",
    "p01_freshness_not_equivalent_to_u09",
    "unknown_is_not_freshness_authority",
    "unproven_is_not_freshness_authority",
    "unspecified_is_not_freshness_authority",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "oldest_member_wins_unproven",
    "newest_member_wins_unproven",
    "min_freshness_unproven",
    "max_freshness_unproven",
    "all_members_same_epoch_unproven",
    "weighted_composite_unproven",
    "source_specific_freshness_unproven",
    "independent_p01_timestamp_unproven",
    "producer_timestamp_unproven",
    "reconstruction_epoch_unproven",
    "valuation_epoch_unproven",
    "accounting_epoch_unproven",
    "current_time_is_not_p01_freshness",
    "missing_freshness_is_not_fresh",
    "stale_p01_is_not_admissible",
    "unproven_cannot_authorize_ignore",
    "unproven_cannot_authorize_fallback",
    "unproven_cannot_authorize_stale_filter",
    "fallback_freshness_state",
    "numeric_provenance_unspecified_does_not_decide_freshness",
    "term_set_unresolved_does_not_decide_freshness",
    "parent_time_semantics_state",
    "parent_freshness_epoch_requirements",
    "u09_freshness_class_comparison",
    "rejected_freshness_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "candidate_freshness_rules_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_member_freshness_inheritance_contract_authority_effect",
    "provenance_digest",
)
P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_haircut_reserve_depletion_semantics_contract_id",
    "p01_haircut_reserve_depletion_semantics_contract_version",
    "parent_p01_member_freshness_inheritance_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "family_class_labels",
    "family_labels_are_not_exact_term_set",
    "family_labels_are_not_independent_members",
    "family_reduction_only",
    "family_must_not_increase_equity",
    "family_negative_allowed",
    "family_zero_only_by_explicit_policy",
    "family_reduction_only_is_not_per_term_role",
    "family_sign_constraint_is_not_per_term_sign",
    "venue_raw_haircuts_forbidden",
    "future_fees_permission_is_not_reserve_definition",
    "u06_accrued_distinct_is_not_p01_definition",
    "terms_insufficiently_defined_for_algebraic_role",
    "p01_haircut_semantics_resolved_status",
    "p01_haircut_identity_class",
    "p01_haircut_role",
    "p01_haircut_sign_semantics",
    "p01_haircut_unit_class",
    "p01_haircut_applicability",
    "p01_haircut_positive_definition_state",
    "p01_reserve_semantics_resolved_status",
    "p01_reserve_identity_class",
    "p01_reserve_role",
    "p01_reserve_sign_semantics",
    "p01_reserve_unit_class",
    "p01_reserve_applicability",
    "p01_reserve_positive_definition_state",
    "p01_depletion_semantics_resolved_status",
    "p01_depletion_identity_class",
    "p01_depletion_role",
    "p01_depletion_sign_semantics",
    "p01_depletion_unit_class",
    "p01_depletion_applicability",
    "p01_depletion_positive_definition_state",
    "p01_zero_absence_na_rule",
    "p01_haircut_reserve_depletion_combination_rule",
    "p01_precedence_rule",
    "unknown_is_not_zero",
    "unspecified_is_not_zero",
    "missing_is_not_zero",
    "not_applicable_is_not_zero",
    "absent_is_not_zero",
    "unavailable_is_not_zero",
    "embedded_is_not_omit",
    "overlap_is_not_deduplicate",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "unspecified_cannot_authorize_subtraction",
    "unspecified_cannot_authorize_multiplication",
    "unspecified_cannot_authorize_addition",
    "unspecified_cannot_authorize_netting",
    "unspecified_cannot_authorize_omission",
    "unspecified_cannot_authorize_ignore",
    "naming_does_not_prove_algebra",
    "separate_labels_do_not_prove_separate_numeric_effect",
    "same_source_does_not_prove_shared_semantics",
    "missing_implementation_is_not_zero",
    "missing_implementation_is_not_not_applicable",
    "u04_u05_u06_u09_are_not_p01_term_authority",
    "rejected_role_inferences",
    "rejected_formula_inferences",
    "rejected_combination_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "candidate_roles_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_runtime_instance_present",
    "p01_authority_effect",
    "p01_haircut_reserve_depletion_semantics_contract_authority_effect",
    "provenance_digest",
)
P01_EXACT_MEMBER_IDENTITY_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_exact_member_identity_contract_id",
    "p01_exact_member_identity_contract_version",
    "parent_p01_haircut_reserve_depletion_semantics_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "ratification_scope",
    "p01_term_set_resolved_status",
    "p01_exact_member_identity_set",
    "p01_exact_member_count",
    "member_id",
    "identity_level_meaning",
    "identity_is_not_numeric_value",
    "identity_is_not_operator",
    "identity_is_not_formula",
    "identity_is_not_sign",
    "identity_is_not_unit",
    "identity_is_not_applicability",
    "identity_is_not_source",
    "identity_is_not_producer",
    "identity_is_not_freshness",
    "identity_is_not_equity_base_inclusion",
    "identity_is_not_embedding",
    "identity_is_not_u04_u05_u06_overlap",
    "identity_is_not_zero_absence_na",
    "identity_is_not_combination",
    "identity_is_not_precedence",
    "identity_is_not_runtime_binding",
    "identity_is_not_execution_effect",
    "p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_reserve_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_depletion_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_u04",
    "p01m_governed_deployability_conservatism_reduction_is_not_u05",
    "p01m_governed_deployability_conservatism_reduction_is_not_u06",
    "p01m_governed_deployability_conservatism_reduction_is_not_venue_raw",
    "p01m_governed_deployability_conservatism_reduction_is_not_availeq",
    "p01m_governed_deployability_conservatism_reduction_is_not_eq",
    "p01m_governed_deployability_conservatism_reduction_is_not_totaleq",
    "p01m_governed_deployability_conservatism_reduction_is_not_canary_envelope",
    "p01m_governed_deployability_conservatism_reduction_is_not_margin_reserve_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission",
    "p01_member_role_sign_unit_resolved_status",
    "p01_zero_absence_na_resolved_status",
    "p01_combination_precedence_resolved_status",
    "p01_value_unit_class_resolved_status",
    "p01_applicability_resolved_status",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "identity_does_not_authorize_arithmetic",
    "identity_does_not_close_p01_term_semantics",
    "identity_does_not_close_haircut_reserve_depletion_unspecified",
    "rejected_member_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_runtime_instance_present",
    "p01_authority_effect",
    "p01_exact_member_identity_contract_authority_effect",
    "provenance_digest",
)
P01_VALUE_UNIT_CLASS_REQUIRED_FIELDS: tuple[str, ...] = (
    "p01_value_unit_class_contract_id",
    "p01_value_unit_class_contract_version",
    "parent_p01_exact_member_identity_contract_schema_class",
    "parent_p01_term_contract_schema_class",
    "target_semantic_dimension_id",
    "policy_id",
    "term_id",
    "member_id",
    "ratification_scope",
    "selected_option",
    "p01_term_set_resolved_status",
    "p01_value_unit_class_resolved_status",
    "p01_value_unit_class",
    "p01_semantic_dimension",
    "p01_parent_dimension_compatibility",
    "p01_requires_dimensional_transformation",
    "p01_direct_additive_subtraction_compatible",
    "p01_unit_identity_is_distinct_from_authority_identity",
    "p01_unit_identity_is_distinct_from_member_identity",
    "p01_settlement_currency_is_not_unit_identity",
    "p01_parent_dimension_is_not_authority_source",
    "unit_does_not_ratify_formula",
    "unit_does_not_ratify_operator",
    "unit_does_not_ratify_sign",
    "unit_does_not_ratify_applicability",
    "unit_does_not_ratify_source_mapping",
    "unit_does_not_close_p01_term_semantics",
    "unit_does_not_close_haircut_reserve_depletion_unspecified",
    "p01_value_unit_class_is_not_ratio",
    "p01_value_unit_class_is_not_percentage",
    "p01_value_unit_class_is_not_bps",
    "p01_value_unit_class_is_not_contracts_qty",
    "p01_value_unit_class_is_not_python_numeric_type",
    "p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_reserve_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_depletion_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_u04",
    "p01m_governed_deployability_conservatism_reduction_is_not_u05",
    "p01m_governed_deployability_conservatism_reduction_is_not_u06",
    "p01m_governed_deployability_conservatism_reduction_is_not_venue_raw",
    "p01m_governed_deployability_conservatism_reduction_is_not_availeq",
    "p01m_governed_deployability_conservatism_reduction_is_not_eq",
    "p01m_governed_deployability_conservatism_reduction_is_not_totaleq",
    "p01m_governed_deployability_conservatism_reduction_is_not_canary_envelope",
    "p01m_governed_deployability_conservatism_reduction_is_not_margin_reserve_alias",
    "p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission",
    "p01_applicability_resolved_status",
    "p01_member_role_sign_unit_resolved_status",
    "missing_input_fail_closed",
    "malformed_input_fail_closed",
    "rejected_unit_class_inferences",
    "remaining_unresolved_semantics",
    "evidence_classification",
    "contradiction_state",
    "term_semantics_resolved_status",
    "unspecified_closed_status",
    "p01_runtime_instance_present",
    "p01_authority_effect",
    "p01_value_unit_class_contract_authority_effect",
    "provenance_digest",
)
