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
    LIVE_ENABLED,
    LIVE_ENABLED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    LIVE_EXECUTION_PORT_CONSTRUCTION_ADMISSION_CONTRACT_IMPLEMENTED,
    OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT_IMPLEMENTED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
    WIRE_SEND_PERMITTED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
)

GAP_DAG_VERSION = "v1"
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY = "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
EARLIEST_DECOMPOSED_CONTRACT_GAP = "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE = (
    "NO_FURTHER_REPO_INTERNAL_SLICE_NO_CANONICALLY_VALID_EQUITY_MAPPING"
)
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE = False
NEXT_STEP_REQUIRES_OWNER_GO = True
HOST_JOIN_NOT_IN_LIVE_ADMISSION_GAP_DAG = True
LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN = True
CANONICAL_ORDER_HOST_JOIN_VS_LIVE_ARMED_VS_LIVE_EXECUTION_PORT = (
    "STANDING_GATES_BEFORE_CONSTRUCTION_CAP72_HOST_REMAINS_SIMULATED"
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
        authority="SECTION_11_2_1",
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
        implementation_status="IMPLEMENTED_FAIL_CLOSED",
        test_status="PROVEN_NOT_ADMITTED",
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
        authority="Cap 11.1 LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN",
        producer="FORBIDDEN_IN_CAP_11_1",
        contract="LIVE_EXECUTION_PORT_ROLE",
        consumer="later Full-Core transport boundary",
        implementation_status="CONSTRUCTION_FORBIDDEN",
        test_status="CONSTRUCTION_ADMISSION_CONTRACT_PROVEN_STILL_FORBIDDEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=5,
        dependencies=(
            "DURABLE_FILEGATE_RUNTIME_JOIN",
            "LIVE_ACCOUNT_BOUND",
            "CAPITAL_ADMISSION",
            "STEP_29P_CAPITAL_RISK_ADMISSIBILITY",
            "FRESH_GET_PER_PRETRADE_DECISION",
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
        implementation_status="STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE",
        test_status="STANDING_ADMISSION_SEAM_PROVEN",
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
        implementation_status="STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE",
        test_status="STANDING_ADMISSION_SEAM_PROVEN",
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
        implementation_status="STANDING_ADMISSION_SEAM_IMPLEMENTED_DEFAULT_FALSE",
        test_status="STANDING_ADMISSION_SEAM_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=True,
        layer=4,
        dependencies=("LIVE_ARMED",),
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
