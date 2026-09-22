"""Forensic Full-Core live-admission gap DAG. Offline only. No GET. No wire.

Durable FILEGATE is joined as typed admission evidence. Does not arm Live.
Does not wire canary as 29Q consumer. Canary observation modules are
classified REUSABLE_MECHANISM_ONLY.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
    FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED,
    FULL_CORE_OFFLINE_E2E_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    LIVE_ACCOUNT_BOUND_IMPLEMENTED,
    CAPITAL_ADMISSION_IMPLEMENTED,
    STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED,
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE,
    ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
    ADJUDICATION_RESULT,
    ARCHITECTURE_RATIFIED,
    OWNER_ASSIGNMENT_RATIFIED,
    C01_C16_REMAIN_REJECTED,
    C01_C16_REJECTION_STILL_BINDING,
    C01_C16_REVIVAL_ALLOWED,
    C17_CREATED,
    C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
    CANDIDATE_CENSUS_COMPLETE,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CHECKPOINT_CAN_MINT_EQUITY,
    CHECKPOINT_CONTRACT_SCHEMA_PRESENT,
    BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN,
    BOUND_ACCOUNT_IDENTITY_PROVEN,
    BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT,
    D4_CONCRETE_UID_CORROBORATED,
    D4_RUNTIME_BINDING_CONTRACT_PRESENT,
    D4_RUNTIME_BINDING_CREATED,
    D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT,
    GENESIS_REBASELINE_SELECTED_BY_OWNER,
    HISTORICAL_COMPLETENESS_CLAIMED,
    HISTORICAL_CONTINUITY_CLAIMED,
    LEGACY_D4_D5_RUNTIME_CHAIN_RECONSTRUCTED,
    BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
    CHECKPOINT_OBSERVATION_ACQUISITION_CREATED,
    CHECKPOINT_OBSERVATION_ACQUISITION_SCHEMA_PRESENT,
    CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED,
    CHECKPOINT_OBSERVATION_PROVEN,
    CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT,
    CHECKPOINT_OBSERVATION_WINDOW_RUNTIME_INSTANCE_PRESENT,
    D5_WINDOW_BINDING_CONTRACT_PRESENT,
    D5_WINDOW_BINDING_CREATED,
    D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT,
    OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT,
    OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED,
    DIMENSION_SPLIT_PERSISTED,
    EARLIEST_OPTION_D_DEPENDENCY,
    EQ_RECONCILIATION_TARGET_ONLY,
    EVENT_ACQUISITION_CREATED,
    EVENT_ACQUISITION_SCHEMA_PRESENT,
    EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    COMPLETE_EVENT_STREAM_PROVEN,
    KIND_SET_RESOLVED,
    KIND_SET_CLOSEOUT_CREATED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_EVIDENCE_PERSIST_CREATED,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
    OBSERVATION_BOUNDARY_CONTRACT_CREATED,
    OBSERVATION_BOUNDARY_CONTRACT_STATUS,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    ACCOUNT_COMPOSITION_OBSERVATION_DEFINED,
    LIABILITY_OBSERVATION_DEFINED,
    FEE_EMBEDDING_OBSERVATION_DEFINED,
    EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED,
    ACCOUNT_BILLS_ATLAS_AUTHORITY,
    CANDIDATE_SURFACE_SELECTION,
    PATH_A_ARCHIVE_OR_REPO_SEARCH,
    PATH_B_SCOPED_READ_ONLY_OBSERVATION,
    PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT,
    PATH_B_CLASS_C_PACKAGE_1_SELECTED,
    PACKAGE_1_PERSISTED,
    PATH_B_PREAUTHORIZATION_READY,
    EXECUTION_READY,
    PACKAGE_1_AUTHORITY_EFFECT,
    SELECTED_OBSERVATION_SURFACES,
    D4_RULE_PERSISTED,
    BALANCE_RULE_PERSISTED,
    BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01,
    EQ_ROLE,
    OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT,
    EMPTY_COVERAGE_RULE_PERSISTED,
    EMPTY_ROWS_PROVE_ZERO_EVENTS,
    EMPTY_ROWS_PROVE_KIND_ABSENCE,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    EMBEDDING_RULE_PERSISTED,
    EMBEDDING_OPTION,
    UNKNOWN_EMBEDDING_FACTS,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    RESIDUAL_COMPLETENESS_PROVEN,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_NO_REMAINDER_NORMALIZED,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    SOURCE_COVERAGE_COMPLETE,
    ORDERING_PROVEN,
    GAP_DETECTION_FAIL_CLOSED,
    IDEMPOTENCY_REPLAY_IDENTITY_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    EARLIEST_D6_COMPLETENESS_DEPENDENCY,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_TAXONOMY_SCHEMA_PRESENT,
    GENUINELY_NEW_CANDIDATE_COUNT,
    MAPPING_BOUNDARY_CURRENTLY_OPEN,
    MAPPING_REOPEN_MECHANISM_EXISTS,
    NEW_CANDIDATE_NAMESPACE_START,
    NEW_SOURCE_GENERATION_MECHANISM_RATIFIED,
    NEXT_EVIDENCE_GENERATION_BLOCKER,
    SOURCE_ACCEPTANCE_CONJUNCTION_RATIFIED,
    SOURCE_PROMOTION_STATE_MACHINE_RATIFIED,
    EQUITY_DIMENSION_BOUND,
    FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
    FUTURE_GOVERNED_SOURCE_OBJECT_CLASS,
    FUTURE_PRODUCER_CLASS,
    GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
    GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT,
    IMPLEMENTATION_OF_VALUE_BINDING,
    LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY,
    LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE,
    LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
    MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING,
    MAPPING_PROVEN,
    NUMERIC_EQUITY_TTL_SECONDS,
    OPTION_D_SELECTED,
    OPTION_D_SSOT_PERSISTED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESTART_PROVEN,
    UNCLASSIFIED_EVENT_FAIL_CLOSED,
    OBSERVATION_AUTHORITY_EFFECT,
    OBSERVATION_IS_NOT_AUTHORITY,
    P01_MAY_INCREASE_EQUITY,
    P01_STATUS,
    POLICY_SEMANTICS_COMPLETE,
    RAW_TO_WITNESS_PROVEN,
    RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN,
    RUNNING_EQUITY_POLICY_SEMANTICS_RATIFIED,
    RUNTIME_VALUE_BINDING_PRESENT,
    SEMANTIC_REQUIREMENTS_COMPLETE,
    SOURCE_CANDIDATE_COUNT,
    SOURCE_OBJECT_PRESENT,
    SOURCE_OBJECT_PRESENT_SEMANTICS,
    SOURCE_SELECTED,
    STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
    VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
    VENUE_WITNESS_SCHEMA_PRESENT,
    VENUE_WITNESS_SELECTED,
    WITNESS_CONTRACT_MISSING_CLOSED,
    NORMALIZATION_SCHEMA_PRESENT,
    NORMALIZATION_RUNTIME_INSTANCE_PRESENT,
    NORMALIZATION_CONTRACT_MISSING_CLOSED,
    NORMALIZATION_AUTHORITY_EFFECT,
    FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT,
    FIELD_TO_DIMENSION_MAPPING_PRESENT,
    SEMANTIC_MAPPING_PROVEN,
    INCLUSION_PROVEN,
    INTERNAL_RECONSTRUCTION_CREATED,
    INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
    INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT,
    INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED,
    INTERNAL_RECONSTRUCTION_PROVEN,
    INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT,
    RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT,
    P01_TERM_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT,
    P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT,
    P01_EMBEDDED_STATE_RESOLVED,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT,
    P01_HAIRCUT_SEMANTICS_RESOLVED,
    P01_RESERVE_SEMANTICS_RESOLVED,
    P01_DEPLETION_SEMANTICS_RESOLVED,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_EXACT_MEMBER_COUNT,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_VALUE_UNIT_CLASS,
    P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_VALUE_UNIT_CLASS_SELECTED_OPTION,
    P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_CLASS_RESOLVED,
    P01_APPLICABILITY_CLASS,
    P01_APPLICABILITY_STATE_MODEL,
    P01_APPLICABILITY_CLASS_SELECTED_OPTION,
    P01_APPLICATION_PREDICATE_RESOLVED,
    P01_APPLICATION_PREDICATE,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED,
    P01_APPLICATION_PREDICATE_MODEL,
    P01_APPLICATION_PREDICATE_IDENTITY_SELECTED_OPTION,
    P01_APPLICABILITY_DECISION_STATE_MODEL,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED,
    P01_APPLICATION_TRUE_RULE_RESOLVED,
    P01_APPLICATION_FALSE_RULE_RESOLVED,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION,
    P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED,
    P01_PREDICATE_INPUT_DOMAIN_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_TYPED,
    P01_PREDICATE_INPUT_DOMAIN_GOVERNED,
    P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS,
    P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD,
    P01_PREDICATE_INPUT_DOMAIN_DEFAULT,
    P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED,
    P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT,
    P01_PREDICATE_INPUT_MEMBER,
    P01_PREDICATE_INPUT_MEMBER_CLASS,
    P01_PRODUCT_SEMANTICS_COMPLETE,
    P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE,
    P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED,
    P01_INPUT_FRESHNESS_RULE_RESOLVED,
    P01_INPUT_READINESS_RULE_RESOLVED,
    P01_INPUT_NORMALIZATION_RULE_RESOLVED,
    P01_CLOSEOUT_MODEL,
    P01_OPERATOR,
    P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT,
    P01_SEMANTIC_DIMENSION,
    P01_PARENT_DIMENSION_COMPATIBILITY,
    P01_REQUIRES_DIMENSIONAL_TRANSFORMATION,
    P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    LIVE_RESTART_RECONSTRUCTED,
    RECONCILIATION_CONTRACT_CREATED,
    DIVERGENCE_POLICY_CREATED,
    U01_STATUS,
    U02_STATUS,
    U03_STATUS,
    U04_STATUS,
    U05_STATUS,
    U06_STATUS,
    U07_STATUS,
    U08_STATUS,
    U09_SAME_PRETRADE_EPOCH_REQUIRED,
    U09_STATUS,
    USD_EQUALS_USDC,
    RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION,
    RUNNING_EQUITY_SOURCE_OBJECT,
    RUNNING_EQUITY_SOURCE_SEMANTICS,
    LIVE_ARMED,
    LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_AUTHORIZED,
    LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_ENABLED,
    LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED,
    OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    EXTERNAL_EFFECT_AUTHORIZED,
    EXTERNAL_EFFECT_GATE_IMPLEMENTED,
    CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED,
    STANDING_LIVE_AUTHORIZATION,
    SUBMISSION_AUTHORIZED,
    SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    WIRE_SEND_PERMITTED,
    WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
)

GAP_DAG_VERSION = "v1"
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY = (
    "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
)
EARLIEST_DECOMPOSED_CONTRACT_GAP = "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE = (
    "NO_FURTHER_REPO_INTERNAL_SLICE_FRESH_TRUSTED_USDC_FREE_MARGIN_GET_AND_NUMERIC_BIND"
)
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE = False
NEXT_STEP_REQUIRES_OWNER_GO = True
HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG = True
LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN = False
CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT = (
    "SEND_CAPABLE_LIVE_AUTHORIZED_NOT_EXTERNAL_EFFECT"
)


@dataclass(frozen=True)
class LiveAdmissionGapNodeV1:
    component_id: str
    authority: str
    producer: str
    contract: str
    consumer: str
    implementation_status: str
    test_status: str
    repo_internal_solvable: bool
    fresh_external_evidence_required: bool
    productive_account_access_required: bool
    standing_live_gates_would_change: bool
    reusable_mechanism_only: bool
    wiring_authorized: bool
    layer: int
    dependencies: Tuple[str, ...]


def _node(**kwargs: Any) -> LiveAdmissionGapNodeV1:
    return LiveAdmissionGapNodeV1(**kwargs)


LIVE_ADMISSION_GAP_NODES: Tuple[LiveAdmissionGapNodeV1, ...] = (
    _node(
        component_id="PATH_IDENTITY",
        authority="full_core_live_path_authority_v1",
        producer="src.ops.full_core_live_path_composition_root_v1.path_identity_v1",
        contract="FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH",
        consumer="productive_live_next_pointer_authority_v1",
        implementation_status="BOUND_THIS_PERSIST",
        test_status="THIS_PACKAGE",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=0,
        dependencies=(),
    ),
    _node(
        component_id="ExecutionAdmissionDecisionV1",
        authority="halt_at_live_execution_boundary_v1",
        producer="evaluate_execution_admission_v1",
        contract="ExecutionAdmissionDecisionV1",
        consumer="halt_at_live_execution_boundary_v1",
        implementation_status="CONJUNCTION_ADMITTED_NOT_PORT_CONSTRUCTION",
        test_status="PROVEN_ADMITTED_HALTS_BEFORE_WIRE",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=0,
        dependencies=("PATH_IDENTITY",),
    ),
    _node(
        component_id="DURABLE_FILEGATE_RUNTIME_JOIN",
        authority="kill_switch_should_block_trading+KillSwitchState+StatePersistence",
        producer="src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1",
        contract="DurableKillSwitchEvidenceStatusV1",
        consumer="evaluate_execution_admission_v1",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="JOIN_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=1,
        dependencies=("PATH_IDENTITY", "ExecutionAdmissionDecisionV1"),
    ),
    _node(
        component_id="OWNER_ONE_SHOT_EXECUTION_PERMIT",
        authority="FullCoreLivePathInputV1.owner_go",
        producer="src.ops.full_core_live_path_composition_root_v1.owner_one_shot_permit_v1",
        contract="OwnerOneShotPermitEvidenceV1",
        consumer="evaluate_execution_admission_v1",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="TYPED_PERMIT_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=1,
        dependencies=("PATH_IDENTITY",),
    ),
    _node(
        component_id="LIVE_ACCOUNT_BOUND",
        authority="capital_risk_sizing_v1/STEP_29P",
        producer="src.ops.full_core_live_path_composition_root_v1.live_account_bound_v1",
        contract="LiveAccountBoundEvidenceV1",
        consumer="evaluate_execution_admission_v1",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="LIVE_ACCOUNT_BOUND_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=3,
        dependencies=("PRIVATE_AUTH_PREFLIGHT", "FRESH_GET_PER_PRETRADE_DECISION"),
    ),
    _node(
        component_id="CAPITAL_ADMISSION",
        authority="capital_admission_contract_v1",
        producer="src.ops.full_core_live_path_composition_root_v1.capital_admission_v1",
        contract="CapitalAdmissionEvidenceV1",
        consumer="evaluate_execution_admission_v1+capital_risk_sizing_v1/STEP_29P",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="CAPITAL_ADMISSION_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=3,
        dependencies=("LIVE_ACCOUNT_BOUND", "FRESH_GET_PER_PRETRADE_DECISION"),
    ),
    _node(
        component_id="STEP_29P_CAPITAL_RISK_ADMISSIBILITY",
        authority="capital_risk_sizing_v1/STEP_29P",
        producer="src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1",
        contract="Step29PCapitalRiskAdmissibilityV1",
        consumer="evaluate_execution_admission_v1+capital_risk_sizing_v1/STEP_29P",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="STEP_29P_RISK_ADMISSIBILITY_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=3,
        dependencies=("CAPITAL_ADMISSION", "FRESH_GET_PER_PRETRADE_DECISION"),
    ),
    _node(
        component_id="PRIVATE_AUTH_PREFLIGHT",
        authority="Full-Core private GET auth required fail-closed",
        producer="src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1",
        contract="PRIVATE_GET_AUTH_REQUIRED_FAIL_CLOSED",
        consumer="FRESH_GET_PER_PRETRADE_DECISION",
        implementation_status="PRIVATE_GET_AUTH_REQUIRED_FAIL_CLOSED",
        test_status="AUTH_FAILURE_DENIAL_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=2,
        dependencies=("PATH_IDENTITY",),
    ),
    _node(
        component_id="FRESH_GET_PER_PRETRADE_DECISION",
        authority="VENUE_PRETRADE_GATES",
        producer="src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1",
        contract="PRETRADE_SOURCE_FRESH_GET",
        consumer="evaluate_execution_admission_v1",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="FRESH_PRETRADE_RUNTIME_GET_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=2,
        dependencies=("PRIVATE_AUTH_PREFLIGHT",),
    ),
    _node(
        component_id="DATASAFETY_ADMISSION_JOIN",
        authority="evaluate_execution_admission_v1",
        producer="src.ops.full_core_live_path_composition_root_v1.datasafety_gate_join_into_execution_admission_v1",
        contract="DataSafetyAdmissionStatusV1",
        consumer="evaluate_execution_admission_v1",
        implementation_status="JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
        test_status="DATASAFETY_GATE_CONJUNCT_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=2,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="MAX_AVAILABLE",
        authority="Owner-adjudicated GET /api/v5/account/max-size",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1",
        contract="FrozenPretradeEvidenceV1.max_available",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="AVAILABLE_MARGIN",
        authority="Owner-adjudicated details[ccy=USDC].availEq",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1",
        contract="FrozenPretradeEvidenceV1.available_margin_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="PRICE_BAND",
        authority="Owner-adjudicated venue price-limit observation",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1",
        contract="FrozenPretradeEvidenceV1.price_band_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="LEVERAGE",
        authority="Owner-adjudicated leverage observation",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1",
        contract="FrozenPretradeEvidenceV1.leverage_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="POS_MODE",
        authority="Owner-adjudicated pos-mode observation",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1",
        contract="FrozenPretradeEvidenceV1.pos_mode_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="MARGIN_MODE",
        authority="Owner-adjudicated margin-mode observation",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.margin_mode_observation_v1",
        contract="FrozenPretradeEvidenceV1.margin_mode_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="INSTRUMENT_STATE",
        authority="Owner-adjudicated instrument state=live",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.instrument_state_observation_v1",
        contract="FrozenPretradeEvidenceV1.instrument_state_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="ACCOUNT_MODE",
        authority="Owner-adjudicated account-mode observation",
        producer="src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_mode_observation_v1",
        contract="FrozenPretradeEvidenceV1.account_mode_ok",
        consumer="evaluate_frozen_pretrade_conjunction_v1",
        implementation_status="FROZEN_OFFLINE_ON_FULL_CORE",
        test_status="FROZEN_CONJUNCTION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=3,
        dependencies=("FRESH_GET_PER_PRETRADE_DECISION",),
    ),
    _node(
        component_id="LiveExecutionPort",
        authority="CURRENT_PRODUCTIVE Cap-7.2 host-join to constructed port",
        producer="join_cap72_host_to_live_execution_port_v1",
        contract="LIVE_EXECUTION_PORT_ROLE",
        consumer="HostActivationBindingV1",
        implementation_status="SEND_CAPABLE_NOT_EXTERNAL_EFFECT",
        test_status="SEND_CAPABLE_SEAM_PROVEN_NOT_POST",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=5,
        dependencies=(
            "DURABLE_FILEGATE_RUNTIME_JOIN",
            "LIVE_ACCOUNT_BOUND",
            "CAPITAL_ADMISSION",
            "STEP_29P_CAPITAL_RISK_ADMISSIBILITY",
            "FRESH_GET_PER_PRETRADE_DECISION",
            "DATASAFETY_ADMISSION_JOIN",
            "LIVE_ENABLED",
            "LIVE_ARMED",
            "WIRE_SEND_PERMITTED",
        ),
    ),
    _node(
        component_id="LIVE_ENABLED",
        authority="standing Full-Core Live gate",
        producer="src.ops.full_core_live_path_composition_root_v1.constants_v1",
        contract="LIVE_ENABLED",
        consumer="evaluate_execution_admission_v1",
        implementation_status="STANDING_TRUE_NOT_AUTOMATIC_ADMISSION",
        test_status="STANDING_TRUE_PROVEN_NOT_ADMISSION",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=4,
        dependencies=(
            "DURABLE_FILEGATE_RUNTIME_JOIN",
            "OWNER_ONE_SHOT_EXECUTION_PERMIT",
            "CAPITAL_ADMISSION",
        ),
    ),
    _node(
        component_id="LIVE_ARMED",
        authority="standing Full-Core arming gate",
        producer="src.ops.full_core_live_path_composition_root_v1.constants_v1",
        contract="LIVE_ARMED",
        consumer="evaluate_execution_admission_v1",
        implementation_status="STANDING_TRUE_NOT_AUTOMATIC_ADMISSION",
        test_status="STANDING_TRUE_PROVEN_NOT_ADMISSION",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=4,
        dependencies=("LIVE_ENABLED",),
    ),
    _node(
        component_id="WIRE_SEND_PERMITTED",
        authority="LIVE_EXECUTION_BOUNDARY",
        producer="src.ops.full_core_live_path_composition_root_v1.constants_v1",
        contract="WIRE_SEND_PERMITTED",
        consumer="evaluate_execution_admission_v1",
        implementation_status="STANDING_TRUE_NOT_AUTOMATIC_SEND",
        test_status="STANDING_TRUE_PROVEN_NOT_SEND",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=4,
        dependencies=("LIVE_ARMED",),
    ),
    _node(
        component_id="SUBMISSION_AUTHORIZED",
        authority="CURRENT_PRODUCTIVE submission-capability admission",
        producer="evaluate_submission_authorized_v1",
        contract="SUBMISSION_AUTHORIZED",
        consumer="halt_at_live_execution_boundary_v1",
        implementation_status="STANDING_TRUE_NOT_AUTOMATIC_WIRE",
        test_status="STANDING_TRUE_PROVEN_NOT_WIRE",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=5,
        dependencies=("LiveExecutionPort", "WIRE_SEND_PERMITTED"),
    ),
    _node(
        component_id="LIVE_AUTHORIZED",
        authority="CURRENT_PRODUCTIVE live-execution authority predicate",
        producer="evaluate_live_authorized_v1",
        contract="LIVE_AUTHORIZED",
        consumer="halt_at_live_execution_boundary_v1",
        implementation_status="STANDING_TRUE_NOT_AUTOMATIC_SEND",
        test_status="STANDING_TRUE_PROVEN_NOT_EXTERNAL_EFFECT",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=5,
        dependencies=("SUBMISSION_AUTHORIZED", "LIVE_ARMED"),
    ),
    _node(
        component_id="EXTERNAL_EFFECT",
        authority="LIVE_EXECUTION_BOUNDARY external-effect gate",
        producer="attempt_envelope_bound_external_effect_send_v1",
        contract="ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM",
        consumer="halt_at_live_execution_boundary_v1",
        implementation_status="ENVELOPE_BOUND_SINGLE_USE_SEAM_IMPLEMENTED_STANDING_FALSE",
        test_status="ENVELOPE_BOUND_SINGLE_USE_SEAM_PROVEN_NOT_REAL_POST",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=6,
        dependencies=("LIVE_AUTHORIZED", "LiveExecutionPort"),
    ),
)


def live_admission_gap_dag_v1() -> dict[str, Any]:
    nodes = {node.component_id: node for node in LIVE_ADMISSION_GAP_NODES}
    reusable = tuple(
        node.component_id for node in LIVE_ADMISSION_GAP_NODES if node.reusable_mechanism_only
    )
    repo_internal = tuple(
        node.component_id
        for node in LIVE_ADMISSION_GAP_NODES
        if node.repo_internal_solvable
        and node.implementation_status
        not in {
            "BOUND_THIS_PERSIST",
            "IMPLEMENTED_FAIL_CLOSED",
            "JOINED_TYPED_EVIDENCE_FAIL_CLOSED",
            "PRIVATE_GET_AUTH_REQUIRED_FAIL_CLOSED",
            "STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE",
            "STANDING_TRUE_NOT_AUTOMATIC_ADMISSION",
            "STANDING_TRUE_NOT_AUTOMATIC_SEND",
            "CONJUNCTION_ADMITTED_NOT_PORT_CONSTRUCTION",
            "CONSTRUCTIBLE_NOT_HOST_JOINED_NOT_WIRE",
            "HOST_JOINED_NOT_SUBMISSION_AUTHORIZED_NOT_WIRE",
            "STANDING_TRUE_NOT_AUTOMATIC_WIRE",
            "SEND_CAPABLE_NOT_EXTERNAL_EFFECT",
            "ENVELOPE_BOUND_SINGLE_USE_SEAM_IMPLEMENTED_STANDING_FALSE",
        }
    )
    return {
        "GAP_DAG_VERSION": GAP_DAG_VERSION,
        "FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH": FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
        "FULL_CORE_SYSTEM_E2E_PROVEN": FULL_CORE_SYSTEM_E2E_PROVEN,
        "CURRENT_LIVE_CORE_PATH_PROVEN": CURRENT_LIVE_CORE_PATH_PROVEN,
        "STANDING_LIVE_AUTHORIZATION": STANDING_LIVE_AUTHORIZATION,
        "CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY": (
            CANARY_PATH_IS_PARALLEL_PRODUCTIVE_LIVE_AUTHORITY
        ),
        "LIVE_ENABLED": LIVE_ENABLED,
        "LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED": (
            LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED
        ),
        "LIVE_ARMED": LIVE_ARMED,
        "LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED": (
            LIVE_ARMED_STANDING_ADMISSION_SEAM_IMPLEMENTED
        ),
        "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED,
        "WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED": (
            WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED
        ),
        "SUBMISSION_AUTHORIZED": SUBMISSION_AUTHORIZED,
        "SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED": (
            SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED
        ),
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED": (
            LIVE_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED
        ),
        "CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED": CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
        "EXTERNAL_EFFECT_GATE_IMPLEMENTED": EXTERNAL_EFFECT_GATE_IMPLEMENTED,
        "FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED": (
            FULL_CORE_HOST_STANDING_PREDICATE_JOIN_IMPLEMENTED
        ),
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT": CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
        "LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED": (
            LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED
        ),
        "PRODUCTIVE_WIRE_SEND_REACHABLE": PRODUCTIVE_WIRE_SEND_REACHABLE,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
        "EARLIEST_DECOMPOSED_CONTRACT_GAP": EARLIEST_DECOMPOSED_CONTRACT_GAP,
        "HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG": HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG,
        "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN": (LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN),
        "CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT": (
            CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT
        ),
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE": MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
        "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED": DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
        "OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED": (
            OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED
        ),
        "FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED": FRESH_PRETRADE_RUNTIME_GET_IMPLEMENTED,
        "LIVE_ACCOUNT_BOUND_IMPLEMENTED": LIVE_ACCOUNT_BOUND_IMPLEMENTED,
        "CAPITAL_ADMISSION_IMPLEMENTED": CAPITAL_ADMISSION_IMPLEMENTED,
        "STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED": (
            STEP_29P_CAPITAL_RISK_ADMISSIBILITY_IMPLEMENTED
        ),
        "ACCOUNT_EQUITY_AUTHORITY_OWNER": ACCOUNT_EQUITY_AUTHORITY_OWNER,
        "ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE": ACCOUNT_EQUITY_AUTHORITY_OWNER_CANDIDATE,
        "ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS": ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS,
        "OWNER_ASSIGNMENT_RATIFIED": OWNER_ASSIGNMENT_RATIFIED,
        "RUNNING_EQUITY_SOURCE_OBJECT": RUNNING_EQUITY_SOURCE_OBJECT,
        "RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION": (RUNNING_EQUITY_SOURCE_FIELD_OR_DERIVATION),
        "RUNNING_EQUITY_SOURCE_SEMANTICS": RUNNING_EQUITY_SOURCE_SEMANTICS,
        "MAPPING_PROVEN": MAPPING_PROVEN,
        "IMPLEMENTATION_OF_VALUE_BINDING": IMPLEMENTATION_OF_VALUE_BINDING,
        "RUNTIME_VALUE_BINDING_PRESENT": RUNTIME_VALUE_BINDING_PRESENT,
        "SOURCE_SELECTED": SOURCE_SELECTED,
        "ARCHITECTURE_RATIFIED": ARCHITECTURE_RATIFIED,
        "FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS": (
            FUTURE_ACCOUNT_EQUITY_AUTHORITY_OWNER_CLASS
        ),
        "FUTURE_GOVERNED_SOURCE_OBJECT_CLASS": FUTURE_GOVERNED_SOURCE_OBJECT_CLASS,
        "FUTURE_PRODUCER_CLASS": FUTURE_PRODUCER_CLASS,
        "GOVERNED_PRODUCTIVE_SOURCE_PRESENT": GOVERNED_PRODUCTIVE_SOURCE_PRESENT,
        "GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT": (
            GOVERNED_RUNNING_ACCOUNT_EQUITY_SAMPLE_SCHEMA_PRESENT
        ),
        "VENUE_WITNESS_SCHEMA_PRESENT": VENUE_WITNESS_SCHEMA_PRESENT,
        "VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT": VENUE_WITNESS_RUNTIME_INSTANCE_PRESENT,
        "VENUE_WITNESS_SELECTED": VENUE_WITNESS_SELECTED,
        "WITNESS_CONTRACT_MISSING_CLOSED": WITNESS_CONTRACT_MISSING_CLOSED,
        "NORMALIZATION_SCHEMA_PRESENT": NORMALIZATION_SCHEMA_PRESENT,
        "NORMALIZATION_RUNTIME_INSTANCE_PRESENT": NORMALIZATION_RUNTIME_INSTANCE_PRESENT,
        "NORMALIZATION_CONTRACT_MISSING_CLOSED": NORMALIZATION_CONTRACT_MISSING_CLOSED,
        "NORMALIZATION_AUTHORITY_EFFECT": NORMALIZATION_AUTHORITY_EFFECT,
        "FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT": (FIELD_TO_DIMENSION_MAPPING_SCHEMA_PRESENT),
        "FIELD_TO_DIMENSION_MAPPING_PRESENT": FIELD_TO_DIMENSION_MAPPING_PRESENT,
        "SEMANTIC_MAPPING_PROVEN": SEMANTIC_MAPPING_PROVEN,
        "INCLUSION_PROVEN": INCLUSION_PROVEN,
        "INTERNAL_RECONSTRUCTION_CREATED": INTERNAL_RECONSTRUCTION_CREATED,
        "INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT": INTERNAL_RECONSTRUCTION_SCHEMA_PRESENT,
        "INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT": (
            INTERNAL_RECONSTRUCTION_RUNTIME_INSTANCE_PRESENT
        ),
        "INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED": (
            INTERNAL_RECONSTRUCTION_CONTRACT_MISSING_CLOSED
        ),
        "INTERNAL_RECONSTRUCTION_PROVEN": INTERNAL_RECONSTRUCTION_PROVEN,
        "INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT": (INTERNAL_RECONSTRUCTION_AUTHORITY_EFFECT),
        "RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT": RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT,
        "RECONSTRUCTION_ALGEBRA_COMPLETE": RECONSTRUCTION_ALGEBRA_COMPLETE,
        "RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT": RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT,
        "P01_TERM_CONTRACT_SCHEMA_PRESENT": P01_TERM_CONTRACT_SCHEMA_PRESENT,
        "P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT": (P01_TERM_CONTRACT_RUNTIME_INSTANCE_PRESENT),
        "P01_TERM_CONTRACT_AUTHORITY_EFFECT": P01_TERM_CONTRACT_AUTHORITY_EFFECT,
        "P01_TERM_SEMANTICS_RESOLVED": P01_TERM_SEMANTICS_RESOLVED,
        "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED": (
            P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED
        ),
        "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT": (
            P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT": (
            P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_TERM_SET_RESOLVED": P01_TERM_SET_RESOLVED,
        "P01_VALUE_UNIT_CLASS_RESOLVED": P01_VALUE_UNIT_CLASS_RESOLVED,
        "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT": (P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT),
        "P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT": (
            P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_APPLICABILITY_RESOLVED": P01_APPLICABILITY_RESOLVED,
        "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT": (
            P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT": (
            P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_EQUITY_BASE_INCLUSION_RESOLVED": P01_EQUITY_BASE_INCLUSION_RESOLVED,
        "P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT": (
            P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT": (
            P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_EMBEDDED_STATE_RESOLVED": P01_EMBEDDED_STATE_RESOLVED,
        "P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT": (
            P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT": (
            P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_U04_OVERLAP_RESOLVED": P01_U04_OVERLAP_RESOLVED,
        "P01_U05_OVERLAP_RESOLVED": P01_U05_OVERLAP_RESOLVED,
        "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT": (
            P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT": (
            P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED": P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
        "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT": (
            P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT": (
            P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED": (P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED),
        "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT": (
            P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT": (
            P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_HAIRCUT_SEMANTICS_RESOLVED": P01_HAIRCUT_SEMANTICS_RESOLVED,
        "P01_RESERVE_SEMANTICS_RESOLVED": P01_RESERVE_SEMANTICS_RESOLVED,
        "P01_DEPLETION_SEMANTICS_RESOLVED": P01_DEPLETION_SEMANTICS_RESOLVED,
        "P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT": (
            P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT": (
            P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_EXACT_MEMBER_COUNT": P01_EXACT_MEMBER_COUNT,
        "P01_EXACT_MEMBER_IDENTITY_SET": P01_EXACT_MEMBER_IDENTITY_SET,
        "P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT": (
            P01_VALUE_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_VALUE_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT": (
            P01_VALUE_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_VALUE_UNIT_CLASS": P01_VALUE_UNIT_CLASS,
        "P01_VALUE_UNIT_CLASS_SELECTED_OPTION": P01_VALUE_UNIT_CLASS_SELECTED_OPTION,
        "P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT": (
            P01_APPLICABILITY_CLASS_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_APPLICABILITY_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT": (
            P01_APPLICABILITY_CLASS_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_APPLICABILITY_CLASS_RESOLVED": P01_APPLICABILITY_CLASS_RESOLVED,
        "P01_APPLICABILITY_CLASS": P01_APPLICABILITY_CLASS,
        "P01_APPLICABILITY_STATE_MODEL": P01_APPLICABILITY_STATE_MODEL,
        "P01_APPLICABILITY_CLASS_SELECTED_OPTION": P01_APPLICABILITY_CLASS_SELECTED_OPTION,
        "P01_APPLICATION_PREDICATE_RESOLVED": P01_APPLICATION_PREDICATE_RESOLVED,
        "P01_APPLICATION_PREDICATE": P01_APPLICATION_PREDICATE,
        "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT": (
            P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT": (
            P01_APPLICATION_PREDICATE_IDENTITY_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED": (
            P01_APPLICATION_PREDICATE_IDENTITY_RESOLVED
        ),
        "P01_APPLICATION_PREDICATE_MODEL": P01_APPLICATION_PREDICATE_MODEL,
        "P01_APPLICATION_PREDICATE_IDENTITY_SELECTED_OPTION": (
            P01_APPLICATION_PREDICATE_IDENTITY_SELECTED_OPTION
        ),
        "P01_APPLICABILITY_DECISION_STATE_MODEL": P01_APPLICABILITY_DECISION_STATE_MODEL,
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED": (
            P01_APPLICATION_PREDICATE_INPUT_DOMAIN_RESOLVED
        ),
        "P01_APPLICATION_TRUE_RULE_RESOLVED": P01_APPLICATION_TRUE_RULE_RESOLVED,
        "P01_APPLICATION_FALSE_RULE_RESOLVED": P01_APPLICATION_FALSE_RULE_RESOLVED,
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT": (
            P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT": (
            P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT
        ),
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT": (
            P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_CONTRACT_AUTHORITY_EFFECT
        ),
        "P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION": (
            P01_APPLICATION_PREDICATE_INPUT_DOMAIN_IDENTITY_SELECTED_OPTION
        ),
        "P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED": (
            P01_PREDICATE_INPUT_DOMAIN_IDENTITY_RESOLVED
        ),
        "P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED": (
            P01_PREDICATE_INPUT_DOMAIN_BOUNDARY_RESOLVED
        ),
        "P01_PREDICATE_INPUT_DOMAIN_CLASS": P01_PREDICATE_INPUT_DOMAIN_CLASS,
        "P01_PREDICATE_INPUT_DOMAIN_TYPED": P01_PREDICATE_INPUT_DOMAIN_TYPED,
        "P01_PREDICATE_INPUT_DOMAIN_GOVERNED": P01_PREDICATE_INPUT_DOMAIN_GOVERNED,
        "P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS": (
            P01_PREDICATE_INPUT_DOMAIN_ALLOWED_INPUT_CLASS
        ),
        "P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD": P01_PREDICATE_INPUT_DOMAIN_IS_CLOSED_WORLD,
        "P01_PREDICATE_INPUT_DOMAIN_DEFAULT": P01_PREDICATE_INPUT_DOMAIN_DEFAULT,
        "P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED": (
            P01_PREDICATE_CONCRETE_INPUT_MEMBERS_RESOLVED
        ),
        "P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT": P01_PREDICATE_CONCRETE_INPUT_MEMBER_COUNT,
        "P01_PREDICATE_INPUT_MEMBER": P01_PREDICATE_INPUT_MEMBER,
        "P01_PREDICATE_INPUT_MEMBER_CLASS": P01_PREDICATE_INPUT_MEMBER_CLASS,
        "P01_PRODUCT_SEMANTICS_COMPLETE": P01_PRODUCT_SEMANTICS_COMPLETE,
        "P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE": (
            P01_RECONSTRUCTION_ALGEBRA_CONTRACT_COMPLETE
        ),
        "P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED": (
            P01_PRODUCTIVE_EXTERNAL_SOURCE_MAPPING_RESOLVED
        ),
        "P01_INPUT_FRESHNESS_RULE_RESOLVED": P01_INPUT_FRESHNESS_RULE_RESOLVED,
        "P01_INPUT_READINESS_RULE_RESOLVED": P01_INPUT_READINESS_RULE_RESOLVED,
        "P01_INPUT_NORMALIZATION_RULE_RESOLVED": P01_INPUT_NORMALIZATION_RULE_RESOLVED,
        "P01_CLOSEOUT_MODEL": P01_CLOSEOUT_MODEL,
        "P01_OPERATOR": P01_OPERATOR,
        "P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT": (
            P01_RECONSTRUCTION_SEMANTIC_AND_ALGEBRA_CLOSEOUT_CONTRACT_SCHEMA_PRESENT
        ),
        "P01_SEMANTIC_DIMENSION": P01_SEMANTIC_DIMENSION,
        "P01_PARENT_DIMENSION_COMPATIBILITY": P01_PARENT_DIMENSION_COMPATIBILITY,
        "P01_REQUIRES_DIMENSIONAL_TRANSFORMATION": P01_REQUIRES_DIMENSIONAL_TRANSFORMATION,
        "P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE": (P01_DIRECT_ADDITIVE_SUBTRACTION_COMPATIBLE),
        "P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED": P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
        "P01_ZERO_ABSENCE_NA_RESOLVED": P01_ZERO_ABSENCE_NA_RESOLVED,
        "P01_COMBINATION_PRECEDENCE_RESOLVED": P01_COMBINATION_PRECEDENCE_RESOLVED,
        "P01_RUNTIME_INSTANCE_PRESENT": P01_RUNTIME_INSTANCE_PRESENT,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "RECONCILIATION_CONTRACT_CREATED": RECONCILIATION_CONTRACT_CREATED,
        "DIVERGENCE_POLICY_CREATED": DIVERGENCE_POLICY_CREATED,
        "RAW_TO_WITNESS_PROVEN": RAW_TO_WITNESS_PROVEN,
        "OBSERVATION_AUTHORITY_EFFECT": OBSERVATION_AUTHORITY_EFFECT,
        "EQUITY_DIMENSION_BOUND": EQUITY_DIMENSION_BOUND,
        "MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING": (
            MAPPED_TO_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING
        ),
        "SOURCE_OBJECT_PRESENT": SOURCE_OBJECT_PRESENT,
        "SOURCE_OBJECT_PRESENT_SEMANTICS": SOURCE_OBJECT_PRESENT_SEMANTICS,
        "RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN": RAW_VENUE_FIELD_AUTHORITY_FORBIDDEN,
        "OBSERVATION_IS_NOT_AUTHORITY": OBSERVATION_IS_NOT_AUTHORITY,
        "STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER": STEP_29P_IS_NOT_EQUITY_AUTHORITY_OWNER,
        "LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY": (
            LIVE_ACCOUNT_BOUND_IDENTITY_IS_NOT_CAPITAL_AUTHORITY
        ),
        "LIVE_ACCOUNT_BOUND_JOIN_PRESENT": LIVE_ACCOUNT_BOUND_JOIN_PRESENT,
        "ADJUDICATION_RESULT": ADJUDICATION_RESULT,
        "SOURCE_CANDIDATE_COUNT": SOURCE_CANDIDATE_COUNT,
        "C01_C16_REMAIN_REJECTED": C01_C16_REMAIN_REJECTED,
        "C01_C16_REJECTION_STILL_BINDING": C01_C16_REJECTION_STILL_BINDING,
        "C01_C16_REVIVAL_ALLOWED": C01_C16_REVIVAL_ALLOWED,
        "NEW_CANDIDATE_NAMESPACE_START": NEW_CANDIDATE_NAMESPACE_START,
        "NEW_SOURCE_GENERATION_MECHANISM_RATIFIED": (NEW_SOURCE_GENERATION_MECHANISM_RATIFIED),
        "SOURCE_ACCEPTANCE_CONJUNCTION_RATIFIED": SOURCE_ACCEPTANCE_CONJUNCTION_RATIFIED,
        "SOURCE_PROMOTION_STATE_MACHINE_RATIFIED": (SOURCE_PROMOTION_STATE_MACHINE_RATIFIED),
        "MAPPING_REOPEN_MECHANISM_EXISTS": MAPPING_REOPEN_MECHANISM_EXISTS,
        "MAPPING_BOUNDARY_CURRENTLY_OPEN": MAPPING_BOUNDARY_CURRENTLY_OPEN,
        "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING": (
            CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING
        ),
        "CANDIDATE_CENSUS_COMPLETE": CANDIDATE_CENSUS_COMPLETE,
        "C17_CREATED": C17_CREATED,
        "C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN": C17_CREATION_FROZEN_UNTIL_D1_D9_PROVEN,
        "GENUINELY_NEW_CANDIDATE_COUNT": GENUINELY_NEW_CANDIDATE_COUNT,
        "NEXT_EVIDENCE_GENERATION_BLOCKER": NEXT_EVIDENCE_GENERATION_BLOCKER,
        "OPTION_D_SELECTED": OPTION_D_SELECTED,
        "OPTION_D_SSOT_PERSISTED": OPTION_D_SSOT_PERSISTED,
        "RAW_EQ_SOURCE_AUTHORITY": RAW_EQ_SOURCE_AUTHORITY,
        "EQ_RECONCILIATION_TARGET_ONLY": EQ_RECONCILIATION_TARGET_ONLY,
        "CHECKPOINT_CAN_MINT_EQUITY": CHECKPOINT_CAN_MINT_EQUITY,
        "CHECKPOINT_CONTRACT_SCHEMA_PRESENT": CHECKPOINT_CONTRACT_SCHEMA_PRESENT,
        "EVENT_TAXONOMY_SCHEMA_PRESENT": EVENT_TAXONOMY_SCHEMA_PRESENT,
        "UNCLASSIFIED_EVENT_FAIL_CLOSED": UNCLASSIFIED_EVENT_FAIL_CLOSED,
        "EVENT_ACQUISITION_CREATED": EVENT_ACQUISITION_CREATED,
        "EVENT_ACQUISITION_SCHEMA_PRESENT": EVENT_ACQUISITION_SCHEMA_PRESENT,
        "EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT": (EVENT_ACQUISITION_RUNTIME_INSTANCE_PRESENT),
        "EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED": (EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED),
        "COMPLETE_EVENT_STREAM_PROVEN": COMPLETE_EVENT_STREAM_PROVEN,
        "KIND_SET_RESOLVED": KIND_SET_RESOLVED,
        "KIND_SET_CLOSEOUT_CREATED": KIND_SET_CLOSEOUT_CREATED,
        "KIND_SET_CLOSEOUT_STATUS": KIND_SET_CLOSEOUT_STATUS,
        "KIND_SET_EVIDENCE_PERSIST_CREATED": KIND_SET_EVIDENCE_PERSIST_CREATED,
        "KIND_SET_EVIDENCE_PERSIST_STATUS": KIND_SET_EVIDENCE_PERSIST_STATUS,
        "OBSERVATION_BOUNDARY_CONTRACT_CREATED": (OBSERVATION_BOUNDARY_CONTRACT_CREATED),
        "OBSERVATION_BOUNDARY_CONTRACT_STATUS": (OBSERVATION_BOUNDARY_CONTRACT_STATUS),
        "OBSERVATION_EXECUTED": OBSERVATION_EXECUTED,
        "OBSERVATION_EXECUTION_AUTHORIZED": OBSERVATION_EXECUTION_AUTHORIZED,
        "OBSERVATION_NETWORK_GET_AUTHORIZED": OBSERVATION_NETWORK_GET_AUTHORIZED,
        "ACCOUNT_COMPOSITION_OBSERVATION_DEFINED": (ACCOUNT_COMPOSITION_OBSERVATION_DEFINED),
        "LIABILITY_OBSERVATION_DEFINED": LIABILITY_OBSERVATION_DEFINED,
        "FEE_EMBEDDING_OBSERVATION_DEFINED": FEE_EMBEDDING_OBSERVATION_DEFINED,
        "EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED": (
            EXOGENOUS_EVENT_COVERAGE_OBSERVATION_DEFINED
        ),
        "ACCOUNT_BILLS_ATLAS_AUTHORITY": ACCOUNT_BILLS_ATLAS_AUTHORITY,
        "CANDIDATE_SURFACE_SELECTION": CANDIDATE_SURFACE_SELECTION,
        "PATH_A_ARCHIVE_OR_REPO_SEARCH": PATH_A_ARCHIVE_OR_REPO_SEARCH,
        "PATH_B_SCOPED_READ_ONLY_OBSERVATION": (PATH_B_SCOPED_READ_ONLY_OBSERVATION),
        "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT": (PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT),
        "PATH_B_CLASS_C_PACKAGE_1_SELECTED": PATH_B_CLASS_C_PACKAGE_1_SELECTED,
        "PACKAGE_1_PERSISTED": PACKAGE_1_PERSISTED,
        "PATH_B_PREAUTHORIZATION_READY": PATH_B_PREAUTHORIZATION_READY,
        "EXECUTION_READY": EXECUTION_READY,
        "PACKAGE_1_AUTHORITY_EFFECT": PACKAGE_1_AUTHORITY_EFFECT,
        "SELECTED_OBSERVATION_SURFACES": SELECTED_OBSERVATION_SURFACES,
        "D4_RULE_PERSISTED": D4_RULE_PERSISTED,
        "BALANCE_RULE_PERSISTED": BALANCE_RULE_PERSISTED,
        "BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01": (
            BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01
        ),
        "EQ_ROLE": EQ_ROLE,
        "OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT": (
            OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT
        ),
        "EMPTY_COVERAGE_RULE_PERSISTED": EMPTY_COVERAGE_RULE_PERSISTED,
        "EMPTY_ROWS_PROVE_ZERO_EVENTS": EMPTY_ROWS_PROVE_ZERO_EVENTS,
        "EMPTY_ROWS_PROVE_KIND_ABSENCE": EMPTY_ROWS_PROVE_KIND_ABSENCE,
        "PAGINATION_EXHAUSTION_PROVES_COMPLETENESS": (PAGINATION_EXHAUSTION_PROVES_COMPLETENESS),
        "EMBEDDING_RULE_PERSISTED": EMBEDDING_RULE_PERSISTED,
        "EMBEDDING_OPTION": EMBEDDING_OPTION,
        "UNKNOWN_EMBEDDING_FACTS": UNKNOWN_EMBEDDING_FACTS,
        "UNKNOWN_NECESSARY_CLASS_REMAINS": UNKNOWN_NECESSARY_CLASS_REMAINS,
        "MS1_KIND_SET_FULLY_CLOSED": MS1_KIND_SET_FULLY_CLOSED,
        "MS2_AUTHORIZED": MS2_AUTHORIZED,
        "D6_FULLY_CLOSED": D6_FULLY_CLOSED,
        "D7_AUTHORIZED": D7_AUTHORIZED,
        "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES": (NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES),
        "HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES": (HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES),
        "RESIDUAL_COMPLETENESS_PROVEN": RESIDUAL_COMPLETENESS_PROVEN,
        "RESIDUAL_KIND_DECISION": RESIDUAL_KIND_DECISION,
        "RESIDUAL_NO_REMAINDER_NORMALIZED": RESIDUAL_NO_REMAINDER_NORMALIZED,
        "U05_KIND_DECISION": U05_KIND_DECISION,
        "U06_KIND_DECISION": U06_KIND_DECISION,
        "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT": (
            AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT
        ),
        "SOURCE_COVERAGE_COMPLETE": SOURCE_COVERAGE_COMPLETE,
        "ORDERING_PROVEN": ORDERING_PROVEN,
        "GAP_DETECTION_FAIL_CLOSED": GAP_DETECTION_FAIL_CLOSED,
        "IDEMPOTENCY_REPLAY_IDENTITY_PROVEN": IDEMPOTENCY_REPLAY_IDENTITY_PROVEN,
        "D6_COMPLETENESS_PRECONDITIONS_PROVEN": D6_COMPLETENESS_PRECONDITIONS_PROVEN,
        "EVENT_KIND_SOURCE_SEAM_SELECTED": EVENT_KIND_SOURCE_SEAM_SELECTED,
        "EARLIEST_D6_COMPLETENESS_DEPENDENCY": EARLIEST_D6_COMPLETENESS_DEPENDENCY,
        "EARLIEST_D6_KIND_SET_DEPENDENCY": EARLIEST_D6_KIND_SET_DEPENDENCY,
        "RECONSTRUCTION_ENGINE_CREATED": RECONSTRUCTION_ENGINE_CREATED,
        "RESTART_PROVEN": RESTART_PROVEN,
        "BOUND_ACCOUNT_IDENTITY_PROVEN": BOUND_ACCOUNT_IDENTITY_PROVEN,
        "BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT": (
            BOUND_ACCOUNT_IDENTITY_CONTRACT_SCHEMA_PRESENT
        ),
        "BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT": (
            BOUND_ACCOUNT_IDENTITY_RUNTIME_INSTANCE_PRESENT
        ),
        "D4_RUNTIME_BINDING_CONTRACT_PRESENT": D4_RUNTIME_BINDING_CONTRACT_PRESENT,
        "D4_RUNTIME_BINDING_CREATED": D4_RUNTIME_BINDING_CREATED,
        "D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT": D4_D5_GENESIS_REBASELINE_CONTRACT_PRESENT,
        "GENESIS_REBASELINE_SELECTED_BY_OWNER": GENESIS_REBASELINE_SELECTED_BY_OWNER,
        "HISTORICAL_CONTINUITY_CLAIMED": HISTORICAL_CONTINUITY_CLAIMED,
        "HISTORICAL_COMPLETENESS_CLAIMED": HISTORICAL_COMPLETENESS_CLAIMED,
        "LEGACY_D4_D5_RUNTIME_CHAIN_RECONSTRUCTED": LEGACY_D4_D5_RUNTIME_CHAIN_RECONSTRUCTED,
        "D4_CONCRETE_UID_CORROBORATED": D4_CONCRETE_UID_CORROBORATED,
        "BOUND_ACCOUNT_CONCRETE_UID_OBSERVED": BOUND_ACCOUNT_CONCRETE_UID_OBSERVED,
        "BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN": (BOUND_ACCOUNT_IDENTITY_FROM_ENV_FORBIDDEN),
        "BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN": (
            BOUND_ACCOUNT_IDENTITY_FROM_CREDENTIAL_FORBIDDEN
        ),
        "BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN": (
            BOUND_ACCOUNT_IDENTITY_IMPLICIT_DEFAULT_FORBIDDEN
        ),
        "CHECKPOINT_OBSERVATION_ACQUISITION_CREATED": (CHECKPOINT_OBSERVATION_ACQUISITION_CREATED),
        "CHECKPOINT_OBSERVATION_ACQUISITION_SCHEMA_PRESENT": (
            CHECKPOINT_OBSERVATION_ACQUISITION_SCHEMA_PRESENT
        ),
        "CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED": (
            CHECKPOINT_OBSERVATION_NETWORK_GET_AUTHORIZED
        ),
        "CHECKPOINT_OBSERVATION_PROVEN": CHECKPOINT_OBSERVATION_PROVEN,
        "CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT": (
            CHECKPOINT_OBSERVATION_RUNTIME_INSTANCE_PRESENT
        ),
        "CHECKPOINT_OBSERVATION_WINDOW_RUNTIME_INSTANCE_PRESENT": (
            CHECKPOINT_OBSERVATION_WINDOW_RUNTIME_INSTANCE_PRESENT
        ),
        "D5_WINDOW_BINDING_CONTRACT_PRESENT": D5_WINDOW_BINDING_CONTRACT_PRESENT,
        "D5_WINDOW_BINDING_CREATED": D5_WINDOW_BINDING_CREATED,
        "D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT": (
            D5_WINDOW_END_EQUALS_OBSERVED_AT_AS_OF_RELATION_AUTHORITY_PRESENT
        ),
        "OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED": (OBSERVATION_S0_STRUCTURAL_BLOCKERS_CLEARED),
        "OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT": OBSERVATION_S0_RUNTIME_PAYLOADS_PRESENT,
        "DIMENSION_SPLIT_PERSISTED": DIMENSION_SPLIT_PERSISTED,
        "EARLIEST_OPTION_D_DEPENDENCY": EARLIEST_OPTION_D_DEPENDENCY,
        "RUNNING_EQUITY_POLICY_SEMANTICS_RATIFIED": (RUNNING_EQUITY_POLICY_SEMANTICS_RATIFIED),
        "SEMANTIC_REQUIREMENTS_COMPLETE": SEMANTIC_REQUIREMENTS_COMPLETE,
        "POLICY_SEMANTICS_COMPLETE": POLICY_SEMANTICS_COMPLETE,
        "P01_STATUS": P01_STATUS,
        "U01_STATUS": U01_STATUS,
        "U02_STATUS": U02_STATUS,
        "U03_STATUS": U03_STATUS,
        "U04_STATUS": U04_STATUS,
        "U05_STATUS": U05_STATUS,
        "U06_STATUS": U06_STATUS,
        "U07_STATUS": U07_STATUS,
        "U08_STATUS": U08_STATUS,
        "U09_STATUS": U09_STATUS,
        "P01_MAY_INCREASE_EQUITY": P01_MAY_INCREASE_EQUITY,
        "USD_EQUALS_USDC": USD_EQUALS_USDC,
        "U09_SAME_PRETRADE_EPOCH_REQUIRED": U09_SAME_PRETRADE_EPOCH_REQUIRED,
        "NUMERIC_EQUITY_TTL_SECONDS": NUMERIC_EQUITY_TTL_SECONDS,
        "LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE": (
            LIVE_ACCOUNT_BOUND_JOIN_EXECUTED_THIS_SLICE
        ),
        "FULL_CORE_OFFLINE_E2E_PROVEN": FULL_CORE_OFFLINE_E2E_PROVEN,
        "FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE": (
            FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE
        ),
        "NEXT_STEP_REQUIRES_OWNER_GO": NEXT_STEP_REQUIRES_OWNER_GO,
        "CANARY_29Q_CONSUMER_WIRING_AUTHORIZED": False,
        "REUSABLE_MECHANISM_ONLY_COMPONENTS": reusable,
        "REPO_INTERNAL_UNRESOLVED_COMPONENTS": repo_internal,
        "nodes": {
            key: {
                "component_id": node.component_id,
                "authority": node.authority,
                "producer": node.producer,
                "contract": node.contract,
                "consumer": node.consumer,
                "implementation_status": node.implementation_status,
                "test_status": node.test_status,
                "repo_internal_solvable": node.repo_internal_solvable,
                "fresh_external_evidence_required": node.fresh_external_evidence_required,
                "productive_account_access_required": (node.productive_account_access_required),
                "standing_live_gates_would_change": node.standing_live_gates_would_change,
                "reusable_mechanism_only": node.reusable_mechanism_only,
                "wiring_authorized": node.wiring_authorized,
                "layer": node.layer,
                "dependencies": node.dependencies,
            }
            for key, node in nodes.items()
        },
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
    }


def gap_node_v1(component_id: str) -> LiveAdmissionGapNodeV1:
    for node in LIVE_ADMISSION_GAP_NODES:
        if node.component_id == component_id:
            return node
    raise KeyError(component_id)
