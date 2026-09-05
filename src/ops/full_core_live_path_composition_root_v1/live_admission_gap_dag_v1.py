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
    CURRENT_LIVE_CORE_PATH_PROVEN,
    DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    FUTURE_PRODUCTIVE_LIVE_EXECUTION_PATH,
    LIVE_ARMED,
    LIVE_ENABLED,
    STANDING_LIVE_AUTHORIZATION,
    WIRE_SEND_PERMITTED,
)

GAP_DAG_VERSION = "v1"
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY = "OWNER_ONE_SHOT_TYPED_LIVE_EXECUTION_PERMIT"
MAX_SAFE_REPO_INTERNAL_NEXT_SLICE = (
    "FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_WITHOUT_LIVE_ARMING_OR_GET"
)
FRESH_EXTERNAL_EVIDENCE_REQUIRED_FOR_NEXT_SLICE = False
NEXT_STEP_REQUIRES_OWNER_GO = True


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
        authority="Owner one-shot execution permit",
        producer="ABSENT_TYPED_LIVE_PERMIT",
        contract="owner_authorization_present",
        consumer="evaluate_execution_admission_v1",
        implementation_status="OFFLINE_OWNER_GO_STRING_ONLY",
        test_status="MISSING_OWNER_AUTHORIZATION_DENIAL_PROVEN",
        repo_internal_solvable=True,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=1,
        dependencies=("PATH_IDENTITY",),
    ),
    _node(
        component_id="LIVE_ACCOUNT_BOUND",
        authority="capital_risk_sizing_v1/STEP_29P",
        producer="TYPED_ONLY_OFFLINE_ALGEBRA_EMITTED",
        contract="CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND",
        consumer="evaluate_execution_admission_v1",
        implementation_status="TYPED_NOT_IMPLEMENTED",
        test_status="OFFLINE_ALGEBRA_LIVE_ADMISSION_DENIED_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=3,
        dependencies=("PRIVATE_AUTH_PREFLIGHT", "FRESH_GET_PER_PRETRADE_DECISION"),
    ),
    _node(
        component_id="PRIVATE_AUTH_PREFLIGHT",
        authority="Full-Core private auth preflight (not canary HTTP as Full-Core transport)",
        producer="CANARY_VENUE_PROOF_ADAPTER_NOT_FULL_CORE",
        contract="PRIVATE_AUTH_PREFLIGHT_NOT_BOUND_ON_FULL_CORE",
        consumer="FRESH_GET_PER_PRETRADE_DECISION",
        implementation_status="NOT_BOUND_ON_FULL_CORE",
        test_status="CANARY_TRANSPORT_ISOLATION_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=True,
        wiring_authorized=False,
        layer=2,
        dependencies=("PATH_IDENTITY",),
    ),
    _node(
        component_id="FRESH_GET_PER_PRETRADE_DECISION",
        authority="VENUE_PRETRADE_GATES",
        producer="ABSENT_ON_FULL_CORE",
        contract="PRETRADE_SOURCE_FRESH_GET",
        consumer="evaluate_execution_admission_v1",
        implementation_status="NOT_IMPLEMENTED_ON_FULL_CORE",
        test_status="FRESH_PRETRADE_GET_NOT_IMPLEMENTED_DENIAL_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=True,
        productive_account_access_required=True,
        standing_live_gates_would_change=False,
        reusable_mechanism_only=False,
        wiring_authorized=False,
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
        test_status="CONSTRUCTION_FORBIDDEN_PROVEN",
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
        implementation_status="STANDING_FALSE",
        test_status="STANDING_FALSE_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=True,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=4,
        dependencies=("DURABLE_FILEGATE_RUNTIME_JOIN", "OWNER_ONE_SHOT_EXECUTION_PERMIT"),
    ),
    _node(
        component_id="LIVE_ARMED",
        authority="standing Full-Core arming gate",
        producer="src.ops.full_core_live_path_composition_root_v1.constants_v1",
        contract="LIVE_ARMED",
        consumer="evaluate_execution_admission_v1",
        implementation_status="STANDING_FALSE",
        test_status="STANDING_FALSE_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=True,
        reusable_mechanism_only=False,
        wiring_authorized=False,
        layer=4,
        dependencies=("LIVE_ENABLED",),
    ),
    _node(
        component_id="WIRE_SEND_PERMITTED",
        authority="LIVE_EXECUTION_BOUNDARY",
        producer="src.ops.full_core_live_path_composition_root_v1.constants_v1",
        contract="WIRE_SEND_PERMITTED",
        consumer="halt_at_live_execution_boundary_v1",
        implementation_status="STANDING_FALSE",
        test_status="STANDING_FALSE_PROVEN",
        repo_internal_solvable=False,
        fresh_external_evidence_required=False,
        productive_account_access_required=False,
        standing_live_gates_would_change=True,
        reusable_mechanism_only=False,
        wiring_authorized=False,
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
        "LIVE_ARMED": LIVE_ARMED,
        "WIRE_SEND_PERMITTED": WIRE_SEND_PERMITTED,
        "EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY": EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE": MAX_SAFE_REPO_INTERNAL_NEXT_SLICE,
        "DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED": DURABLE_FILEGATE_RUNTIME_JOIN_IMPLEMENTED,
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
