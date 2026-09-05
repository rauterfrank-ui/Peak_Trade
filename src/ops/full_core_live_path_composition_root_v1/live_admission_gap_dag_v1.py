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
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY = "LIVE_VENUE_CAPITAL_NOT_ADMITTED_TO_STEP_29P"
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE = "NO_FURTHER_REPO_INTERNAL_SLICE_PRE_WIRE_BOUNDARY_REACHED"
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE = True
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
