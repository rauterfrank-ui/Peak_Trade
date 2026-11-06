"""Offline RUNBOOK_STEP_25 deploy-inactive contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.meta.learning_loop.runtime_eligibility_v1 import (
    AUTHORITY_CONTRACT_DIGEST,
    AUTHORITY_CONTRACT_REF,
    BEAR_COMPONENT_REF,
    BULL_BEAR_SEMANTIC_DIGEST,
    BULL_COMPONENT_REF,
    CANONICAL_ORDER_INTENT_CONTRACT_DIGEST,
    CANONICAL_ORDER_INTENT_CONTRACT_REF,
    CONTRACT_VERSION as RUNTIME_ELIGIBILITY_CONTRACT_VERSION,
    DOUBLE_PLAY_CONTRACT_DIGEST,
    DOUBLE_PLAY_OWNER_REF,
    DYNAMIC_SCOPE_OWNER_REF,
    DYNAMIC_SCOPE_POLICY_DIGEST,
    MASTER_V2_CONTRACT_DIGEST,
    MASTER_V2_OWNER_REF,
    REVOCATION_CONTRACT_DIGEST,
    REVOCATION_CONTRACT_REF,
    RISK_OWNER_REF,
    RuntimeEligibilityEvaluationInput,
    SCOPE_CAPITAL_OWNER_REF,
    SIZING_OWNER_REF,
    build_runtime_eligibility_v1,
    compute_candidate_artifact_digest,
    compute_promotion_decision_digest,
    default_candidate_artifact_body,
    default_promotion_decision_body,
    default_runtime_eligibility_evaluation_input,
    evaluate_runtime_eligibility_v1,
)

DEPLOYMENT_CANDIDATE_CONTRACT_NAME = "deployment_candidate_v1"
DEPLOYMENT_CANDIDATE_CONTRACT_VERSION = "v1"
DEPLOYMENT_CANDIDATE_BUILDER_VERSION = "deployment_candidate_builder_v1"
DEPLOYMENT_CANDIDATE_POLICY_VERSION = "deployment_candidate_policy_v1"
DEPLOYMENT_CANDIDATE_PRODUCER_VERSION = "deployment_candidate_v1"
DEPLOYMENT_CANDIDATE_ARTIFACT_REL = "deployment_candidate_v1.json"
DEPLOYMENT_CANDIDATE_STAGING_PREFIX = ".deployment_candidate_staging_"

VERIFICATION_CONTRACT_NAME = "deployed_inactive_verification_v1"
VERIFICATION_CONTRACT_VERSION = "v1"
VERIFICATION_BUILDER_VERSION = "deployed_inactive_verification_builder_v1"
VERIFICATION_POLICY_VERSION = "deployed_inactive_verification_policy_v1"
VERIFICATION_PRODUCER_VERSION = "deployed_inactive_verification_v1"
VERIFICATION_ARTIFACT_REL = "deployed_inactive_verification_v1.json"
VERIFICATION_STAGING_PREFIX = ".deployed_inactive_verification_staging_"

SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_CANDIDATE_VERSION = "v1"
SUPPORTED_CANDIDATE_VERSIONS = frozenset({"v1"})
OBSERVED_STATE_SOURCE = "OFFLINE_DECLARATIVE_PROJECTION"

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_READINESS_STATUSES = frozenset({"PROVEN", "NOT_PROVEN", "UNKNOWN"})
_VALID_RUNTIME_ELIGIBILITY_STATUSES = frozenset({"ELIGIBLE", "INELIGIBLE"})
_VALID_DEPLOYMENT_CANDIDATE_STATUSES = frozenset({"DEPLOYABLE", "NOT_DEPLOYABLE"})
_VALID_VERIFICATION_STATUSES = frozenset({"VERIFIED_INACTIVE_PROJECTION", "VERIFICATION_FAILED"})

_DEPLOYMENT_CANDIDATE_FAIL_CLOSED_DECISION_CODES: tuple[str, ...] = (
    "MISSING_RUNTIME_ELIGIBILITY",
    "RUNTIME_ELIGIBILITY_DIGEST_MISMATCH",
    "RUNTIME_ELIGIBILITY_STATUS_NOT_ELIGIBLE",
    "RUNTIME_ELIGIBILITY_EVIDENCE_INVALID",
    "MISSING_CANDIDATE_ARTIFACT",
    "CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
    "UNSUPPORTED_CANDIDATE_VERSION",
    "MISSING_PROMOTION_DECISION",
    "PROMOTION_DECISION_DIGEST_MISMATCH",
    "PROMOTION_STATUS_NOT_APPROVED",
    "MISSING_TRADING_LOGIC_COMPATIBILITY",
    "TRADING_LOGIC_COMPATIBILITY_DIGEST_MISMATCH",
    "TRADING_LOGIC_OWNER_BINDING_INVALID",
    "TRADING_LOGIC_BYPASS_DETECTED",
    "PARALLEL_TRADING_LOGIC_SSOT_DETECTED",
    "MISSING_RISK_POLICY_DIGEST",
    "RISK_POLICY_DIGEST_MISMATCH",
    "MISSING_SIZING_PROFILE",
    "SIZING_PROFILE_DIGEST_MISMATCH",
    "MISSING_SCOPE_CAPITAL_BINDING",
    "SCOPE_CAPITAL_DIGEST_MISMATCH",
    "ENVIRONMENT_BINDING_MISSING",
    "ENVIRONMENT_BINDING_MISMATCH",
    "VENUE_SCOPE_MISSING",
    "VENUE_SCOPE_MISMATCH",
    "INSTRUMENT_SCOPE_MISSING",
    "INSTRUMENT_SCOPE_MISMATCH",
    "SPOT_MARKET_TYPE_REJECTED",
    "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
    "UNKNOWN_MARKET_TYPE_REJECTED",
    "MISSING_MARKET_TYPE_REJECTED",
    "MISSING_VENUE_CAPABILITY_SNAPSHOT",
    "VENUE_CAPABILITY_DIGEST_MISMATCH",
    "VENUE_CAPABILITY_SCOPE_MISMATCH",
    "VENUE_CAPABILITY_STALE",
    "MISSING_PRE_TRADE_SAFETY_EVIDENCE",
    "PRE_TRADE_SAFETY_EVIDENCE_INVALID",
    "MISSING_KILLSWITCH_CONTRACT",
    "KILLSWITCH_CONTRACT_DIGEST_MISMATCH",
    "MISSING_KILLSWITCH_WRITER_FENCING_EVIDENCE",
    "KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
    "MISSING_RECONCILIATION_READINESS",
    "RECONCILIATION_READINESS_INVALID",
    "MISSING_UNKNOWN_OUTCOME_RECOVERY",
    "UNKNOWN_OUTCOME_RECOVERY_INVALID",
    "MISSING_ADAPTER_SUBMISSION_CONTRACT",
    "ADAPTER_SUBMISSION_CONTRACT_INVALID",
    "MISSING_AUTHORITY_CONTRACT",
    "AUTHORITY_CONTRACT_INVALID",
    "MISSING_REVOCATION_CONTRACT",
    "REVOCATION_CONTRACT_INVALID",
    "MISSING_PACKAGE",
    "PACKAGE_DIGEST_MISMATCH",
    "MISSING_DEPLOYMENT_LAYOUT",
    "DEPLOYMENT_LAYOUT_DIGEST_MISMATCH",
    "MISSING_DEPLOYMENT_POLICY",
    "DEPLOYMENT_POLICY_DIGEST_MISMATCH",
    "MISSING_LOADER_CONTRACT",
    "LOADER_CONTRACT_DIGEST_MISMATCH",
    "LOADER_COMPATIBILITY_NOT_PROVEN",
    "MISSING_RUNTIME_CONTRACT",
    "RUNTIME_CONTRACT_DIGEST_MISMATCH",
    "RUNTIME_CONTRACT_COMPATIBILITY_NOT_PROVEN",
    "CONFIGURATION_DIGEST_MISMATCH",
    "ROLLBACK_PARENT_MISSING",
    "ROLLBACK_ARTIFACT_MISSING",
    "ROLLBACK_ARTIFACT_DIGEST_MISMATCH",
    "ROLLBACK_READINESS_NOT_PROVEN",
    "DATA_READINESS_NOT_PROVEN",
    "BUDGET_READINESS_NOT_PROVEN",
    "ARTIFACT_INTEGRITY_NOT_PROVEN",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "INPUT_EPOCH_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "UNKNOWN_DECISION_CODE",
    "MISSING_REQUIRED_INPUT",
    "REAL_DEPLOYMENT_REQUESTED",
    "FILE_TRANSFER_REQUESTED",
    "RUNTIME_INSTALLATION_REQUESTED",
    "RUNTIME_REGISTRATION_REQUESTED",
    "ACTIVATION_REQUESTED",
    "AUTHORITY_REQUESTED",
    "SCHEDULER_ENABLE_REQUESTED",
    "EXECUTION_PERMISSION_REQUESTED",
    "ADAPTER_INVOCATION_REQUESTED",
    "ORDER_SUBMISSION_REQUESTED",
    "NETWORK_SIDE_EFFECT_REQUESTED",
)

_VERIFICATION_FAIL_CLOSED_DECISION_CODES: tuple[str, ...] = (
    "MISSING_DEPLOYMENT_CANDIDATE",
    "DEPLOYMENT_CANDIDATE_DIGEST_MISMATCH",
    "DEPLOYMENT_CANDIDATE_NOT_DEPLOYABLE",
    "OBSERVED_STATE_SOURCE_NOT_OFFLINE_PROJECTION",
    "REAL_RUNTIME_OBSERVATION_REQUESTED",
    "OBSERVED_ARTIFACT_DIGEST_MISMATCH",
    "OBSERVED_CONFIGURATION_DIGEST_MISMATCH",
    "OBSERVED_DEPLOYMENT_LAYOUT_DIGEST_MISMATCH",
    "OBSERVED_LOADER_CONTRACT_DIGEST_MISMATCH",
    "OBSERVED_RUNTIME_CONTRACT_DIGEST_MISMATCH",
    "DEPLOYMENT_STATE_NOT_INACTIVE",
    "ACTIVATION_STATE_NOT_DISABLED",
    "SCHEDULER_STATE_NOT_DISABLED",
    "AUTHORITY_STATE_NOT_ABSENT",
    "EXECUTION_PERMISSION_STATE_NOT_ABSENT",
    "ORDER_CAPABILITY_STATE_NOT_DISABLED",
    "ACTIVATION_PRESENT",
    "SCHEDULER_ENABLED",
    "AUTHORITY_PRESENT",
    "EXECUTION_PERMISSION_PRESENT",
    "ORDERS_ENABLED",
    "NETWORK_SIDE_EFFECT_PRESENT",
    "RUNTIME_SIDE_EFFECT_PRESENT",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "UNKNOWN_DECISION_CODE",
    "MISSING_REQUIRED_INPUT",
)

DEPLOY_INACTIVE_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "deploy_inactive_contract_complete": False,
    "deploy_inactive_offline_only": True,
    "deployment_candidate_is_evidence": True,
    "deployed_inactive_verification_is_evidence": True,
    "deployable_does_not_mean_deployed": True,
    "deployable_does_not_mean_deployed_inactive": True,
    "deployable_does_not_mean_activated": True,
    "deployable_does_not_mean_runtime_ready": True,
    "deployable_does_not_create_deployment": True,
    "deployable_does_not_create_authority": True,
    "deployable_does_not_create_execution_permission": True,
    "deployable_does_not_allow_scheduler": True,
    "deployable_does_not_allow_orders": True,
    "deployable_does_not_mutate_runtime": True,
    "verified_inactive_projection_does_not_prove_real_deployment": True,
    "verified_inactive_projection_does_not_create_deployment": True,
    "verified_inactive_projection_does_not_activate": True,
    "verified_inactive_projection_does_not_create_authority": True,
    "verified_inactive_projection_does_not_allow_orders": True,
    "verified_inactive_projection_does_not_mutate_runtime": True,
    "generic_futures_market_type_guard": True,
    "spot_rejected_fail_closed": True,
    "synthetic_spot_rejected_fail_closed": True,
    "unknown_market_type_rejected_fail_closed": True,
    "missing_market_type_rejected_fail_closed": True,
}

_DEPLOYMENT_CANDIDATE_NON_MUTATION_FLAGS: dict[str, bool] = {
    "real_deployment_performed": False,
    "file_transfer_to_runtime_performed": False,
    "runtime_installation_performed": False,
    "runtime_registration_performed": False,
    "deployment_created": False,
    "deployment_mutated": False,
    "deployment_activated": False,
    "runtime_activated": False,
    "runtime_state_mutated": False,
    "trading_session_created": False,
    "trading_epoch_created": False,
    "executor_epoch_created": False,
    "authority_created": False,
    "authority_activated": False,
    "authority_revoked": False,
    "lease_created": False,
    "lease_activated": False,
    "execution_permission_created": False,
    "execution_permission_consumed": False,
    "submission_authorized": False,
    "submission_claim_executed": False,
    "scheduler_enabled": False,
    "scheduler_invoked": False,
    "adapter_invoked": False,
    "venue_capability_discovery_executed": False,
    "venue_capability_refresh_executed": False,
    "reconciliation_executed": False,
    "killswitch_state_mutated": False,
    "killswitch_trip_executed": False,
    "killswitch_reset_executed": False,
    "order_created": False,
    "order_submitted": False,
    "order_cancel_requested": False,
    "order_amend_requested": False,
    "position_state_mutated": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "network_side_effect_created": False,
    "exchange_request_sent": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "offline_only": True,
    "does_not_transfer_file": True,
    "does_not_install_runtime": True,
    "does_not_register_runtime": True,
    "does_not_create_deployment": True,
    "does_not_mutate_deployment": True,
    "does_not_activate_deployment": True,
    "does_not_create_authority": True,
    "does_not_create_execution_permission": True,
    "does_not_invoke_scheduler": True,
    "does_not_invoke_adapter": True,
    "does_not_send_network_request": True,
    "does_not_submit_order": True,
    "does_not_mutate_runtime": True,
}

_VERIFICATION_NON_MUTATION_FLAGS: dict[str, bool] = {
    **_DEPLOYMENT_CANDIDATE_NON_MUTATION_FLAGS,
    "offline_only": True,
    "verification_does_not_prove_real_deployment": True,
    "verification_does_not_activate": True,
    "verification_does_not_create_authority": True,
    "verification_does_not_create_execution_permission": True,
    "verification_does_not_allow_orders": True,
    "verification_does_not_mutate_runtime": True,
    "real_runtime_observation": False,
    "real_deployment_confirmed": False,
    "observed_state_source": OBSERVED_STATE_SOURCE,
}


class DeployInactiveError(ValueError):
    """Fail-closed deploy-inactive contract error."""


@dataclass(frozen=True)
class DeploymentCandidateEvaluationInput:
    contract_version: str = DEPLOYMENT_CANDIDATE_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = DEPLOYMENT_CANDIDATE_BUILDER_VERSION
    policy_version: str = DEPLOYMENT_CANDIDATE_POLICY_VERSION
    deployment_candidate_id: str = ""
    runtime_eligibility_ref: str = ""
    runtime_eligibility_digest: str = ""
    runtime_eligibility_status: str = "ELIGIBLE"
    runtime_eligibility_body: dict[str, Any] = field(default_factory=dict)
    runtime_eligibility_input: RuntimeEligibilityEvaluationInput | None = None
    candidate_artifact_ref: str = ""
    candidate_artifact_body: dict[str, Any] = field(default_factory=dict)
    candidate_artifact_digest: str = ""
    candidate_artifact_version: str = DEFAULT_CANDIDATE_VERSION
    strategy_id: str = ""
    strategy_version: str = ""
    model_version: str = ""
    parameter_set_digest: str = ""
    feature_set_digest: str = ""
    market_type: str = "FUTURES"
    promotion_decision_ref: str = ""
    promotion_decision_body: dict[str, Any] = field(default_factory=dict)
    promotion_decision_digest: str = ""
    promotion_status: str = "PASS"
    promotion_decision_outcome: str = "APPROVE"
    trading_logic_compatibility_ref: str = ""
    trading_logic_compatibility_digest: str = ""
    trading_logic_compatibility_status: str = "TRADING_LOGIC_COMPATIBLE"
    trading_logic_bypass_detected: bool = False
    parallel_trading_logic_ssot_detected: bool = False
    master_v2_owner_ref: str = MASTER_V2_OWNER_REF
    master_v2_contract_digest: str = MASTER_V2_CONTRACT_DIGEST
    double_play_owner_ref: str = DOUBLE_PLAY_OWNER_REF
    double_play_contract_digest: str = DOUBLE_PLAY_CONTRACT_DIGEST
    bull_component_ref: str = BULL_COMPONENT_REF
    bear_component_ref: str = BEAR_COMPONENT_REF
    bull_bear_semantic_digest: str = BULL_BEAR_SEMANTIC_DIGEST
    dynamic_scope_owner_ref: str = DYNAMIC_SCOPE_OWNER_REF
    dynamic_scope_policy_digest: str = DYNAMIC_SCOPE_POLICY_DIGEST
    risk_owner_ref: str = RISK_OWNER_REF
    sizing_owner_ref: str = SIZING_OWNER_REF
    scope_capital_owner_ref: str = SCOPE_CAPITAL_OWNER_REF
    canonical_order_intent_contract_ref: str = CANONICAL_ORDER_INTENT_CONTRACT_REF
    canonical_order_intent_contract_digest: str = CANONICAL_ORDER_INTENT_CONTRACT_DIGEST
    pre_trade_safety_ref: str = ""
    pre_trade_safety_digest: str = ""
    kill_switch_contract_ref: str = ""
    kill_switch_contract_digest: str = ""
    kill_switch_writer_fencing_ref: str = ""
    kill_switch_writer_fencing_digest: str = ""
    reconciliation_readiness_ref: str = ""
    reconciliation_readiness_digest: str = ""
    unknown_outcome_recovery_ref: str = ""
    unknown_outcome_recovery_digest: str = ""
    adapter_submission_contract_ref: str = ""
    adapter_submission_contract_digest: str = ""
    authority_contract_ref: str = AUTHORITY_CONTRACT_REF
    authority_contract_digest: str = AUTHORITY_CONTRACT_DIGEST
    revocation_contract_ref: str = REVOCATION_CONTRACT_REF
    revocation_contract_digest: str = REVOCATION_CONTRACT_DIGEST
    environment: str = ""
    venue_scope: str = ""
    instrument_scope: str = ""
    venue_capability_snapshot_ref: str = ""
    venue_capability_snapshot_digest: str = ""
    venue_capability_stale: bool = False
    venue_capability_venue_scope: str = ""
    risk_policy_digest: str = ""
    sizing_profile_digest: str = ""
    scope_capital_digest: str = ""
    package_ref: str = ""
    package_digest: str = ""
    deployment_layout_ref: str = ""
    deployment_layout_digest: str = ""
    deployment_policy_digest: str = ""
    expected_loader_contract: str = ""
    expected_loader_contract_digest: str = ""
    expected_runtime_contract: str = ""
    expected_runtime_contract_digest: str = ""
    expected_configuration_digest: str = ""
    rollback_parent_ref: str = ""
    rollback_parent_digest: str = ""
    rollback_artifact_ref: str = ""
    rollback_artifact_digest: str = ""
    rollback_readiness_status: str = "PROVEN"
    data_readiness_status: str = "PROVEN"
    budget_readiness_status: str = "PROVEN"
    artifact_integrity_status: str = "PROVEN"
    loader_compatibility_status: str = "PROVEN"
    runtime_contract_compatibility_status: str = "PROVEN"
    deployment_layout_status: str = "PROVEN"
    input_epoch: int = 1
    bound_input_epoch: int = 1
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    real_deployment_requested: bool = False
    file_transfer_requested: bool = False
    runtime_installation_requested: bool = False
    runtime_registration_requested: bool = False
    activation_requested: bool = False
    authority_creation_requested: bool = False
    scheduler_enable_requested: bool = False
    execution_permission_requested: bool = False
    adapter_invocation_requested: bool = False
    order_submission_requested: bool = False
    network_side_effect_requested: bool = False


@dataclass(frozen=True)
class DeploymentCandidateEvaluationResult:
    deployment_candidate_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    fail_closed_gates: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class DeploymentCandidateResult:
    output_dir: Path
    deployment_candidate_id: str
    deployment_candidate_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class OfflineDeclarativeProjection:
    observed_state_source: str = OBSERVED_STATE_SOURCE
    real_runtime_observation: bool = False
    observed_artifact_digest: str = ""
    observed_configuration_digest: str = ""
    observed_deployment_layout_digest: str = ""
    observed_loader_contract_digest: str = ""
    observed_runtime_contract_digest: str = ""
    deployment_state: str = "INACTIVE"
    activation_state: str = "DISABLED"
    scheduler_state: str = "DISABLED"
    authority_state: str = "ABSENT"
    execution_permission_state: str = "ABSENT"
    order_capability_state: str = "DISABLED"
    network_side_effect_present: bool = False
    runtime_side_effect_present: bool = False


@dataclass(frozen=True)
class DeployedInactiveVerificationInput:
    contract_version: str = VERIFICATION_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = VERIFICATION_BUILDER_VERSION
    policy_version: str = VERIFICATION_POLICY_VERSION
    verification_id: str = ""
    deployment_candidate_ref: str = ""
    deployment_candidate_digest: str = ""
    deployment_candidate_status: str = "DEPLOYABLE"
    deployment_candidate_body: dict[str, Any] = field(default_factory=dict)
    projection: OfflineDeclarativeProjection = field(default_factory=OfflineDeclarativeProjection)
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    real_runtime_observation_requested: bool = False


@dataclass(frozen=True)
class DeployedInactiveVerificationResult:
    verification_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    fail_closed_gates: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class DeployedInactiveVerificationProduceResult:
    output_dir: Path
    verification_id: str
    verification_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


def _append_rejection(
    reasons: list[str],
    gates: list[str],
    *,
    decision_code: str,
    gate_id: str,
) -> None:
    if decision_code not in reasons:
        reasons.append(decision_code)
    gates.append(gate_id)


def _validate_digest_field(
    reasons: list[str],
    gates: list[str],
    *,
    value: str,
    expected: str,
    missing_code: str,
    mismatch_code: str,
    gate_id: str,
) -> None:
    if not value or not is_valid_sha256_hex(value):
        _append_rejection(reasons, gates, decision_code=missing_code, gate_id=gate_id)
    elif expected and value != expected:
        _append_rejection(reasons, gates, decision_code=mismatch_code, gate_id=gate_id)


def _validate_readiness(
    reasons: list[str],
    gates: list[str],
    *,
    status: str,
    not_proven_code: str,
    gate_id: str,
) -> None:
    if status not in _VALID_READINESS_STATUSES or status != "PROVEN":
        _append_rejection(reasons, gates, decision_code=not_proven_code, gate_id=gate_id)


def _as_runtime_eligibility_input(
    request: DeploymentCandidateEvaluationInput,
) -> RuntimeEligibilityEvaluationInput:
    if request.runtime_eligibility_input is None:
        raise DeployInactiveError("runtime_eligibility_input is required for revalidation")
    return request.runtime_eligibility_input


def _runtime_eligibility_failure_code(runtime_code: str) -> str:
    mapping = {
        "MISSING_CANDIDATE_ARTIFACT": "MISSING_CANDIDATE_ARTIFACT",
        "CANDIDATE_ARTIFACT_DIGEST_MISMATCH": "CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
        "MISSING_PRE_TRADE_SAFETY_KERNEL_EVIDENCE": "MISSING_PRE_TRADE_SAFETY_EVIDENCE",
        "PRE_TRADE_SAFETY_KERNEL_EVIDENCE_INVALID": "PRE_TRADE_SAFETY_EVIDENCE_INVALID",
        "MISSING_RECONCILIATION_EVIDENCE": "MISSING_RECONCILIATION_READINESS",
        "RECONCILIATION_READINESS_NOT_PROVEN": "RECONCILIATION_READINESS_INVALID",
        "MISSING_UNKNOWN_OUTCOME_RECOVERY_EVIDENCE": "MISSING_UNKNOWN_OUTCOME_RECOVERY",
        "UNKNOWN_OUTCOME_RECOVERY_NOT_FAIL_CLOSED": "UNKNOWN_OUTCOME_RECOVERY_INVALID",
        "SIZING_PROFILE_BINDING_MISSING": "MISSING_SIZING_PROFILE",
        "SCOPE_CAPITAL_BINDING_MISSING": "MISSING_SCOPE_CAPITAL_BINDING",
        "ROLLBACK_CAPABILITY_MISSING": "ROLLBACK_PARENT_MISSING",
    }
    return mapping.get(runtime_code, runtime_code)


def evaluate_deployment_candidate_v1(
    request: DeploymentCandidateEvaluationInput,
) -> DeploymentCandidateEvaluationResult:
    blocking_reasons: list[str] = []
    fail_closed_gates: list[str] = []

    forbidden_requests = (
        (request.real_deployment_requested, "REAL_DEPLOYMENT_REQUESTED", "real_deployment"),
        (request.file_transfer_requested, "FILE_TRANSFER_REQUESTED", "file_transfer"),
        (
            request.runtime_installation_requested,
            "RUNTIME_INSTALLATION_REQUESTED",
            "runtime_installation",
        ),
        (
            request.runtime_registration_requested,
            "RUNTIME_REGISTRATION_REQUESTED",
            "runtime_registration",
        ),
        (request.activation_requested, "ACTIVATION_REQUESTED", "activation"),
        (request.authority_creation_requested, "AUTHORITY_REQUESTED", "authority_creation"),
        (request.scheduler_enable_requested, "SCHEDULER_ENABLE_REQUESTED", "scheduler_enable"),
        (
            request.execution_permission_requested,
            "EXECUTION_PERMISSION_REQUESTED",
            "execution_permission",
        ),
        (
            request.adapter_invocation_requested,
            "ADAPTER_INVOCATION_REQUESTED",
            "adapter_invocation",
        ),
        (request.order_submission_requested, "ORDER_SUBMISSION_REQUESTED", "order_submission"),
        (
            request.network_side_effect_requested,
            "NETWORK_SIDE_EFFECT_REQUESTED",
            "network_side_effect",
        ),
    )
    for flag, code, gate_id in forbidden_requests:
        if flag:
            _append_rejection(
                blocking_reasons, fail_closed_gates, decision_code=code, gate_id=gate_id
            )

    if request.contract_version != DEPLOYMENT_CANDIDATE_CONTRACT_VERSION:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_CONTRACT_VERSION",
            gate_id="contract_version",
        )

    if not request.runtime_eligibility_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_RUNTIME_ELIGIBILITY",
            gate_id="runtime_eligibility_ref",
        )
    elif request.runtime_eligibility_status not in _VALID_RUNTIME_ELIGIBILITY_STATUSES:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RUNTIME_ELIGIBILITY_EVIDENCE_INVALID",
            gate_id="runtime_eligibility_status",
        )
    elif request.runtime_eligibility_status != "ELIGIBLE":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RUNTIME_ELIGIBILITY_STATUS_NOT_ELIGIBLE",
            gate_id="runtime_eligibility_status",
        )

    expected_runtime_eligibility_digest = ""
    if request.runtime_eligibility_body:
        expected_runtime_eligibility_digest = str(
            request.runtime_eligibility_body.get("output_digest", "")
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.runtime_eligibility_digest,
        expected=expected_runtime_eligibility_digest,
        missing_code="MISSING_RUNTIME_ELIGIBILITY",
        mismatch_code="RUNTIME_ELIGIBILITY_DIGEST_MISMATCH",
        gate_id="runtime_eligibility_digest",
    )

    runtime_result = evaluate_runtime_eligibility_v1(_as_runtime_eligibility_input(request))
    if runtime_result.eligibility_status != "ELIGIBLE":
        mapped = _runtime_eligibility_failure_code(runtime_result.decision_code)
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code=mapped,
            gate_id="runtime_eligibility_revalidation",
        )

    if request.candidate_artifact_version not in SUPPORTED_CANDIDATE_VERSIONS:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNSUPPORTED_CANDIDATE_VERSION",
            gate_id="candidate_artifact_version",
        )

    if not request.candidate_artifact_ref.strip() or not request.candidate_artifact_body:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_CANDIDATE_ARTIFACT",
            gate_id="candidate_artifact_ref",
        )

    expected_candidate_digest = compute_candidate_artifact_digest(request.candidate_artifact_body)
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.candidate_artifact_digest,
        expected=expected_candidate_digest,
        missing_code="MISSING_CANDIDATE_ARTIFACT",
        mismatch_code="CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
        gate_id="candidate_artifact_digest",
    )

    if not request.promotion_decision_ref.strip() or not request.promotion_decision_body:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_PROMOTION_DECISION",
            gate_id="promotion_decision_ref",
        )

    expected_promotion_digest = compute_promotion_decision_digest(request.promotion_decision_body)
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.promotion_decision_digest,
        expected=expected_promotion_digest,
        missing_code="MISSING_PROMOTION_DECISION",
        mismatch_code="PROMOTION_DECISION_DIGEST_MISMATCH",
        gate_id="promotion_decision_digest",
    )
    if request.promotion_decision_outcome != "APPROVE":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="PROMOTION_STATUS_NOT_APPROVED",
            gate_id="promotion_decision_outcome",
        )

    market_type = request.market_type.strip().upper()
    if not market_type:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_MARKET_TYPE_REJECTED",
            gate_id="market_type",
        )
    elif market_type in _FORBIDDEN_MARKET_TYPES:
        code = (
            "SPOT_MARKET_TYPE_REJECTED"
            if market_type == "SPOT"
            else "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"
        )
        _append_rejection(
            blocking_reasons, fail_closed_gates, decision_code=code, gate_id="market_type"
        )
    elif market_type not in _VALID_MARKET_TYPES:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_MARKET_TYPE_REJECTED",
            gate_id="market_type",
        )

    if not request.strategy_id.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_REQUIRED_INPUT",
            gate_id="strategy_id",
        )

    if not request.package_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_PACKAGE",
            gate_id="package_ref",
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.package_digest,
        expected=compute_content_sha256({"package_ref": request.package_ref})
        if request.package_ref
        else "",
        missing_code="MISSING_PACKAGE",
        mismatch_code="PACKAGE_DIGEST_MISMATCH",
        gate_id="package_digest",
    )
    if not request.deployment_layout_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_DEPLOYMENT_LAYOUT",
            gate_id="deployment_layout_ref",
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.deployment_layout_digest,
        expected=compute_content_sha256({"deployment_layout_ref": request.deployment_layout_ref})
        if request.deployment_layout_ref
        else "",
        missing_code="MISSING_DEPLOYMENT_LAYOUT",
        mismatch_code="DEPLOYMENT_LAYOUT_DIGEST_MISMATCH",
        gate_id="deployment_layout_digest",
    )
    if not request.deployment_policy_digest or not is_valid_sha256_hex(
        request.deployment_policy_digest
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_DEPLOYMENT_POLICY",
            gate_id="deployment_policy_digest",
        )

    if not request.expected_loader_contract.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_LOADER_CONTRACT",
            gate_id="expected_loader_contract",
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.expected_loader_contract_digest,
        expected=compute_content_sha256({"loader_contract": request.expected_loader_contract})
        if request.expected_loader_contract
        else "",
        missing_code="MISSING_LOADER_CONTRACT",
        mismatch_code="LOADER_CONTRACT_DIGEST_MISMATCH",
        gate_id="expected_loader_contract_digest",
    )
    if not request.expected_runtime_contract.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_RUNTIME_CONTRACT",
            gate_id="expected_runtime_contract",
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.expected_runtime_contract_digest,
        expected=compute_content_sha256({"runtime_contract": request.expected_runtime_contract})
        if request.expected_runtime_contract
        else "",
        missing_code="MISSING_RUNTIME_CONTRACT",
        mismatch_code="RUNTIME_CONTRACT_DIGEST_MISMATCH",
        gate_id="expected_runtime_contract_digest",
    )
    if not request.expected_configuration_digest or not is_valid_sha256_hex(
        request.expected_configuration_digest
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="CONFIGURATION_DIGEST_MISMATCH",
            gate_id="expected_configuration_digest",
        )

    if not request.rollback_parent_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ROLLBACK_PARENT_MISSING",
            gate_id="rollback_parent_ref",
        )
    if not request.rollback_artifact_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ROLLBACK_ARTIFACT_MISSING",
            gate_id="rollback_artifact_ref",
        )
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.rollback_artifact_digest,
        expected=compute_content_sha256({"rollback_artifact_ref": request.rollback_artifact_ref})
        if request.rollback_artifact_ref
        else "",
        missing_code="ROLLBACK_ARTIFACT_MISSING",
        mismatch_code="ROLLBACK_ARTIFACT_DIGEST_MISMATCH",
        gate_id="rollback_artifact_digest",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.rollback_readiness_status,
        not_proven_code="ROLLBACK_READINESS_NOT_PROVEN",
        gate_id="rollback_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.artifact_integrity_status,
        not_proven_code="ARTIFACT_INTEGRITY_NOT_PROVEN",
        gate_id="artifact_integrity_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.loader_compatibility_status,
        not_proven_code="LOADER_COMPATIBILITY_NOT_PROVEN",
        gate_id="loader_compatibility_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.runtime_contract_compatibility_status,
        not_proven_code="RUNTIME_CONTRACT_COMPATIBILITY_NOT_PROVEN",
        gate_id="runtime_contract_compatibility_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.deployment_layout_status,
        not_proven_code="MISSING_DEPLOYMENT_LAYOUT",
        gate_id="deployment_layout_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.data_readiness_status,
        not_proven_code="DATA_READINESS_NOT_PROVEN",
        gate_id="data_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.budget_readiness_status,
        not_proven_code="BUDGET_READINESS_NOT_PROVEN",
        gate_id="budget_readiness_status",
    )

    if not request.input_refs or not request.input_digests:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_REQUIRED_INPUT",
            gate_id="input_refs",
        )
    elif len(request.input_refs) != len(request.input_digests):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="INPUT_LINEAGE_GAP",
            gate_id="input_lineage",
        )
    elif request.input_epoch != request.bound_input_epoch:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="INPUT_EPOCH_MISMATCH",
            gate_id="input_epoch",
        )

    if blocking_reasons:
        deployment_candidate_status = "NOT_DEPLOYABLE"
        decision_code = blocking_reasons[0]
    else:
        deployment_candidate_status = "DEPLOYABLE"
        decision_code = "DEPLOYABLE"

    deployment_candidate_id = compute_content_sha256(
        {
            "deployment_candidate_id": request.deployment_candidate_id,
            "runtime_eligibility_digest": request.runtime_eligibility_digest,
            "decision_code": decision_code,
        }
    )

    contract_body: dict[str, Any] = {
        "contract_name": DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
        "contract_version": DEPLOYMENT_CANDIDATE_CONTRACT_VERSION,
        "deployment_candidate_id": deployment_candidate_id,
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": DEPLOYMENT_CANDIDATE_PRODUCER_VERSION,
        "runtime_eligibility_ref": request.runtime_eligibility_ref,
        "runtime_eligibility_digest": request.runtime_eligibility_digest,
        "runtime_eligibility_status": request.runtime_eligibility_status,
        "candidate_artifact_ref": request.candidate_artifact_ref,
        "candidate_artifact_digest": request.candidate_artifact_digest,
        "candidate_artifact_version": request.candidate_artifact_version,
        "strategy_id": request.strategy_id,
        "strategy_version": request.strategy_version,
        "model_version": request.model_version,
        "parameter_set_digest": request.parameter_set_digest,
        "feature_set_digest": request.feature_set_digest,
        "promotion_decision_ref": request.promotion_decision_ref,
        "promotion_decision_digest": request.promotion_decision_digest,
        "trading_logic_compatibility_ref": request.trading_logic_compatibility_ref,
        "trading_logic_compatibility_digest": request.trading_logic_compatibility_digest,
        "risk_policy_digest": request.risk_policy_digest,
        "sizing_profile_digest": request.sizing_profile_digest,
        "scope_capital_digest": request.scope_capital_digest,
        "environment": request.environment,
        "venue_scope": request.venue_scope,
        "instrument_scope": request.instrument_scope,
        "market_type": market_type or request.market_type,
        "venue_capability_snapshot_ref": request.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": request.venue_capability_snapshot_digest,
        "pre_trade_safety_ref": request.pre_trade_safety_ref,
        "pre_trade_safety_digest": request.pre_trade_safety_digest,
        "kill_switch_contract_ref": request.kill_switch_contract_ref,
        "kill_switch_contract_digest": request.kill_switch_contract_digest,
        "kill_switch_writer_fencing_ref": request.kill_switch_writer_fencing_ref,
        "kill_switch_writer_fencing_digest": request.kill_switch_writer_fencing_digest,
        "reconciliation_readiness_ref": request.reconciliation_readiness_ref,
        "reconciliation_readiness_digest": request.reconciliation_readiness_digest,
        "unknown_outcome_recovery_ref": request.unknown_outcome_recovery_ref,
        "unknown_outcome_recovery_digest": request.unknown_outcome_recovery_digest,
        "adapter_submission_contract_ref": request.adapter_submission_contract_ref,
        "adapter_submission_contract_digest": request.adapter_submission_contract_digest,
        "authority_contract_ref": request.authority_contract_ref,
        "authority_contract_digest": request.authority_contract_digest,
        "revocation_contract_ref": request.revocation_contract_ref,
        "revocation_contract_digest": request.revocation_contract_digest,
        "package_ref": request.package_ref,
        "package_digest": request.package_digest,
        "deployment_layout_ref": request.deployment_layout_ref,
        "deployment_layout_digest": request.deployment_layout_digest,
        "deployment_policy_digest": request.deployment_policy_digest,
        "expected_loader_contract": request.expected_loader_contract,
        "expected_loader_contract_digest": request.expected_loader_contract_digest,
        "expected_runtime_contract": request.expected_runtime_contract,
        "expected_runtime_contract_digest": request.expected_runtime_contract_digest,
        "expected_configuration_digest": request.expected_configuration_digest,
        "rollback_parent_ref": request.rollback_parent_ref,
        "rollback_parent_digest": request.rollback_parent_digest,
        "rollback_artifact_ref": request.rollback_artifact_ref,
        "rollback_artifact_digest": request.rollback_artifact_digest,
        "rollback_readiness_status": request.rollback_readiness_status,
        "data_readiness_status": request.data_readiness_status,
        "budget_readiness_status": request.budget_readiness_status,
        "artifact_integrity_status": request.artifact_integrity_status,
        "loader_compatibility_status": request.loader_compatibility_status,
        "runtime_contract_compatibility_status": request.runtime_contract_compatibility_status,
        "deployment_layout_status": request.deployment_layout_status,
        "fail_closed_gates": list(dict.fromkeys(fail_closed_gates)),
        "deployment_candidate_status": deployment_candidate_status,
        "decision_code": decision_code,
        "blocking_reasons": blocking_reasons,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_DEPLOYMENT_CANDIDATE_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return DeploymentCandidateEvaluationResult(
        deployment_candidate_status=deployment_candidate_status,
        decision_code=decision_code,
        blocking_reasons=tuple(blocking_reasons),
        fail_closed_gates=tuple(dict.fromkeys(fail_closed_gates)),
        contract_body=contract_body,
    )


def default_deployment_candidate_evaluation_input() -> DeploymentCandidateEvaluationInput:
    re_input = default_runtime_eligibility_evaluation_input()
    re_contract = build_runtime_eligibility_v1(re_input)
    candidate_id = re_input.candidate_id
    strategy_id = "generic-futures-strategy-001"
    package_ref = f"offline/{candidate_id}/package"
    package_digest = compute_content_sha256({"package_ref": package_ref})
    deployment_layout_ref = f"offline/{candidate_id}/deployment-layout"
    deployment_layout_digest = compute_content_sha256(
        {"deployment_layout_ref": deployment_layout_ref}
    )
    deployment_policy_digest = compute_content_sha256(
        {"deployment_policy_id": "generic-futures-deploy-policy-001"}
    )
    loader_contract = "generic-futures-loader-contract-v1"
    loader_digest = compute_content_sha256({"loader_contract": loader_contract})
    runtime_contract = "generic-futures-runtime-contract-v1"
    runtime_digest = compute_content_sha256({"runtime_contract": runtime_contract})
    configuration_digest = compute_content_sha256(
        {"configuration_id": "generic-futures-config-001"}
    )
    rollback_artifact_ref = f"offline/{candidate_id}/rollback-artifact"
    rollback_artifact_digest = compute_content_sha256(
        {"rollback_artifact_ref": rollback_artifact_ref}
    )
    rollback_parent_digest = compute_content_sha256(
        {"rollback_parent_ref": re_input.rollback_parent_ref}
    )
    parameter_set_digest = compute_content_sha256(
        {"parameter_set_id": "generic-futures-params-001"}
    )
    feature_set_digest = compute_content_sha256({"feature_set_id": "generic-futures-features-001"})
    input_refs = tuple(re_input.input_refs) + (
        re_contract["output_digest"],
        package_digest,
        deployment_layout_digest,
        loader_digest,
        runtime_digest,
        configuration_digest,
    )
    return DeploymentCandidateEvaluationInput(
        deployment_candidate_id=f"deployment-candidate-{candidate_id}",
        runtime_eligibility_ref=f"offline/{candidate_id}/runtime-eligibility-evidence",
        runtime_eligibility_digest=re_contract["output_digest"],
        runtime_eligibility_status="ELIGIBLE",
        runtime_eligibility_body=re_contract,
        runtime_eligibility_input=re_input,
        candidate_artifact_ref=re_input.candidate_artifact_ref,
        candidate_artifact_body=dict(re_input.candidate_artifact_body),
        candidate_artifact_digest=re_input.candidate_artifact_digest,
        candidate_artifact_version=re_input.candidate_version,
        strategy_id=strategy_id,
        strategy_version="v1",
        model_version="v1",
        parameter_set_digest=parameter_set_digest,
        feature_set_digest=feature_set_digest,
        market_type=re_input.market_type,
        promotion_decision_ref=re_input.promotion_decision_ref,
        promotion_decision_body=dict(re_input.promotion_decision_body),
        promotion_decision_digest=re_input.promotion_decision_digest,
        trading_logic_compatibility_ref=re_input.trading_logic_compatibility_ref,
        trading_logic_compatibility_digest=re_input.trading_logic_compatibility_digest,
        pre_trade_safety_ref=re_input.pre_trade_safety_kernel_evidence_ref,
        pre_trade_safety_digest=re_input.pre_trade_safety_kernel_evidence_digest,
        kill_switch_contract_ref=re_input.kill_switch_owner_ref,
        kill_switch_contract_digest=re_input.kill_switch_contract_digest,
        kill_switch_writer_fencing_ref=re_input.kill_switch_writer_fencing_evidence_ref,
        kill_switch_writer_fencing_digest=re_input.kill_switch_writer_fencing_evidence_digest,
        reconciliation_readiness_ref=re_input.reconciliation_evidence_ref,
        reconciliation_readiness_digest=re_input.reconciliation_evidence_digest,
        unknown_outcome_recovery_ref=re_input.unknown_outcome_recovery_evidence_ref,
        unknown_outcome_recovery_digest=re_input.unknown_outcome_recovery_evidence_digest,
        adapter_submission_contract_ref=re_input.adapter_submission_contract_ref,
        adapter_submission_contract_digest=re_input.adapter_submission_contract_digest,
        environment=re_input.environment,
        venue_scope=re_input.venue_scope,
        instrument_scope=re_input.instrument_scope,
        venue_capability_snapshot_ref=re_input.venue_capability_snapshot_ref,
        venue_capability_snapshot_digest=re_input.venue_capability_snapshot_digest,
        venue_capability_venue_scope=re_input.venue_capability_venue_scope,
        risk_policy_digest=re_input.risk_policy_digest,
        sizing_profile_digest=re_input.sizing_profile_digest,
        scope_capital_digest=re_input.scope_capital_digest,
        package_ref=package_ref,
        package_digest=package_digest,
        deployment_layout_ref=deployment_layout_ref,
        deployment_layout_digest=deployment_layout_digest,
        deployment_policy_digest=deployment_policy_digest,
        expected_loader_contract=loader_contract,
        expected_loader_contract_digest=loader_digest,
        expected_runtime_contract=runtime_contract,
        expected_runtime_contract_digest=runtime_digest,
        expected_configuration_digest=configuration_digest,
        rollback_parent_ref=re_input.rollback_parent_ref,
        rollback_parent_digest=rollback_parent_digest,
        rollback_artifact_ref=rollback_artifact_ref,
        rollback_artifact_digest=rollback_artifact_digest,
        input_refs=input_refs,
        input_digests=input_refs,
    )


def build_deployment_candidate_v1(
    request: DeploymentCandidateEvaluationInput,
) -> dict[str, Any]:
    return evaluate_deployment_candidate_v1(request).contract_body


def default_offline_declarative_projection(
    candidate: Mapping[str, Any],
) -> OfflineDeclarativeProjection:
    return OfflineDeclarativeProjection(
        observed_artifact_digest=str(candidate["candidate_artifact_digest"]),
        observed_configuration_digest=str(candidate["expected_configuration_digest"]),
        observed_deployment_layout_digest=str(candidate["deployment_layout_digest"]),
        observed_loader_contract_digest=str(candidate["expected_loader_contract_digest"]),
        observed_runtime_contract_digest=str(candidate["expected_runtime_contract_digest"]),
    )


def default_deployed_inactive_verification_input(
    candidate: Mapping[str, Any] | None = None,
) -> DeployedInactiveVerificationInput:
    candidate_contract = dict(
        candidate or build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    )
    projection = default_offline_declarative_projection(candidate_contract)
    candidate_digest = str(candidate_contract["output_digest"])
    return DeployedInactiveVerificationInput(
        verification_id=f"verification-{candidate_contract['deployment_candidate_id']}",
        deployment_candidate_ref=f"offline/{candidate_contract['deployment_candidate_id']}/deployment-candidate",
        deployment_candidate_digest=candidate_digest,
        deployment_candidate_status=str(candidate_contract["deployment_candidate_status"]),
        deployment_candidate_body=candidate_contract,
        projection=projection,
        input_refs=(candidate_digest,),
        input_digests=(candidate_digest,),
    )


def evaluate_deployed_inactive_verification_v1(
    request: DeployedInactiveVerificationInput,
) -> DeployedInactiveVerificationResult:
    blocking_reasons: list[str] = []
    fail_closed_gates: list[str] = []
    projection = request.projection

    if request.contract_version != VERIFICATION_CONTRACT_VERSION:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_CONTRACT_VERSION",
            gate_id="contract_version",
        )

    if request.real_runtime_observation_requested:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="REAL_RUNTIME_OBSERVATION_REQUESTED",
            gate_id="real_runtime_observation_requested",
        )

    if not request.deployment_candidate_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_DEPLOYMENT_CANDIDATE",
            gate_id="deployment_candidate_ref",
        )

    expected_candidate_digest = ""
    if request.deployment_candidate_body:
        expected_candidate_digest = str(request.deployment_candidate_body.get("output_digest", ""))
    _validate_digest_field(
        blocking_reasons,
        fail_closed_gates,
        value=request.deployment_candidate_digest,
        expected=expected_candidate_digest,
        missing_code="MISSING_DEPLOYMENT_CANDIDATE",
        mismatch_code="DEPLOYMENT_CANDIDATE_DIGEST_MISMATCH",
        gate_id="deployment_candidate_digest",
    )

    if request.deployment_candidate_status != "DEPLOYABLE":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="DEPLOYMENT_CANDIDATE_NOT_DEPLOYABLE",
            gate_id="deployment_candidate_status",
        )

    if projection.observed_state_source != OBSERVED_STATE_SOURCE:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="OBSERVED_STATE_SOURCE_NOT_OFFLINE_PROJECTION",
            gate_id="observed_state_source",
        )
    if projection.real_runtime_observation:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="REAL_RUNTIME_OBSERVATION_REQUESTED",
            gate_id="real_runtime_observation",
        )

    candidate = request.deployment_candidate_body
    if candidate:
        digest_checks = (
            (
                "expected_artifact_digest",
                "candidate_artifact_digest",
                "observed_artifact_digest",
                "OBSERVED_ARTIFACT_DIGEST_MISMATCH",
            ),
            (
                "expected_configuration_digest",
                "expected_configuration_digest",
                "observed_configuration_digest",
                "OBSERVED_CONFIGURATION_DIGEST_MISMATCH",
            ),
            (
                "expected_deployment_layout_digest",
                "deployment_layout_digest",
                "observed_deployment_layout_digest",
                "OBSERVED_DEPLOYMENT_LAYOUT_DIGEST_MISMATCH",
            ),
            (
                "expected_loader_contract_digest",
                "expected_loader_contract_digest",
                "observed_loader_contract_digest",
                "OBSERVED_LOADER_CONTRACT_DIGEST_MISMATCH",
            ),
            (
                "expected_runtime_contract_digest",
                "expected_runtime_contract_digest",
                "observed_runtime_contract_digest",
                "OBSERVED_RUNTIME_CONTRACT_DIGEST_MISMATCH",
            ),
        )
        for _label, candidate_key, observed_attr, mismatch_code in digest_checks:
            expected = str(candidate.get(candidate_key, ""))
            observed = getattr(projection, observed_attr)
            if expected != observed:
                _append_rejection(
                    blocking_reasons,
                    fail_closed_gates,
                    decision_code=mismatch_code,
                    gate_id=observed_attr,
                )

    state_checks = (
        (projection.deployment_state, "INACTIVE", "DEPLOYMENT_STATE_NOT_INACTIVE"),
        (projection.activation_state, "DISABLED", "ACTIVATION_STATE_NOT_DISABLED"),
        (projection.scheduler_state, "DISABLED", "SCHEDULER_STATE_NOT_DISABLED"),
        (projection.authority_state, "ABSENT", "AUTHORITY_STATE_NOT_ABSENT"),
        (projection.execution_permission_state, "ABSENT", "EXECUTION_PERMISSION_STATE_NOT_ABSENT"),
        (projection.order_capability_state, "DISABLED", "ORDER_CAPABILITY_STATE_NOT_DISABLED"),
    )
    for observed, expected, code in state_checks:
        if observed != expected:
            _append_rejection(
                blocking_reasons,
                fail_closed_gates,
                decision_code=code,
                gate_id=f"state_{expected.lower()}",
            )

    if projection.activation_state != "DISABLED":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ACTIVATION_PRESENT",
            gate_id="activation_present",
        )
    if projection.scheduler_state != "DISABLED":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="SCHEDULER_ENABLED",
            gate_id="scheduler_enabled",
        )
    if projection.authority_state != "ABSENT":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="AUTHORITY_PRESENT",
            gate_id="authority_present",
        )
    if projection.execution_permission_state != "ABSENT":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="EXECUTION_PERMISSION_PRESENT",
            gate_id="execution_permission_present",
        )
    if projection.order_capability_state != "DISABLED":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ORDERS_ENABLED",
            gate_id="orders_enabled",
        )
    if projection.network_side_effect_present:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="NETWORK_SIDE_EFFECT_PRESENT",
            gate_id="network_side_effect_present",
        )
    if projection.runtime_side_effect_present:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RUNTIME_SIDE_EFFECT_PRESENT",
            gate_id="runtime_side_effect_present",
        )

    if not request.input_refs or not request.input_digests:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_REQUIRED_INPUT",
            gate_id="input_refs",
        )
    elif len(request.input_refs) != len(request.input_digests):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="INPUT_LINEAGE_GAP",
            gate_id="input_lineage",
        )

    if blocking_reasons:
        verification_status = "VERIFICATION_FAILED"
        decision_code = blocking_reasons[0]
    else:
        verification_status = "VERIFIED_INACTIVE_PROJECTION"
        decision_code = "VERIFIED_INACTIVE_PROJECTION"

    verification_id = compute_content_sha256(
        {
            "verification_id": request.verification_id,
            "deployment_candidate_digest": request.deployment_candidate_digest,
            "decision_code": decision_code,
        }
    )

    contract_body: dict[str, Any] = {
        "contract_name": VERIFICATION_CONTRACT_NAME,
        "contract_version": VERIFICATION_CONTRACT_VERSION,
        "verification_id": verification_id,
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": VERIFICATION_PRODUCER_VERSION,
        "deployment_candidate_ref": request.deployment_candidate_ref,
        "deployment_candidate_digest": request.deployment_candidate_digest,
        "deployment_candidate_status": request.deployment_candidate_status,
        "expected_artifact_digest": str(candidate.get("candidate_artifact_digest", ""))
        if candidate
        else "",
        "observed_artifact_digest": projection.observed_artifact_digest,
        "expected_configuration_digest": str(candidate.get("expected_configuration_digest", ""))
        if candidate
        else "",
        "observed_configuration_digest": projection.observed_configuration_digest,
        "expected_deployment_layout_digest": str(candidate.get("deployment_layout_digest", ""))
        if candidate
        else "",
        "observed_deployment_layout_digest": projection.observed_deployment_layout_digest,
        "expected_loader_contract_digest": str(candidate.get("expected_loader_contract_digest", ""))
        if candidate
        else "",
        "observed_loader_contract_digest": projection.observed_loader_contract_digest,
        "expected_runtime_contract_digest": str(
            candidate.get("expected_runtime_contract_digest", "")
        )
        if candidate
        else "",
        "observed_runtime_contract_digest": projection.observed_runtime_contract_digest,
        "deployment_state": projection.deployment_state,
        "activation_state": projection.activation_state,
        "scheduler_state": projection.scheduler_state,
        "authority_state": projection.authority_state,
        "execution_permission_state": projection.execution_permission_state,
        "order_capability_state": projection.order_capability_state,
        "artifact_digest_match": projection.observed_artifact_digest
        == str(candidate.get("candidate_artifact_digest", ""))
        if candidate
        else False,
        "configuration_digest_match": projection.observed_configuration_digest
        == str(candidate.get("expected_configuration_digest", ""))
        if candidate
        else False,
        "deployment_layout_digest_match": projection.observed_deployment_layout_digest
        == str(candidate.get("deployment_layout_digest", ""))
        if candidate
        else False,
        "loader_contract_match": projection.observed_loader_contract_digest
        == str(candidate.get("expected_loader_contract_digest", ""))
        if candidate
        else False,
        "runtime_contract_match": projection.observed_runtime_contract_digest
        == str(candidate.get("expected_runtime_contract_digest", ""))
        if candidate
        else False,
        "activation_absent": projection.activation_state == "DISABLED",
        "scheduler_disabled": projection.scheduler_state == "DISABLED",
        "authority_absent": projection.authority_state == "ABSENT",
        "execution_permission_absent": projection.execution_permission_state == "ABSENT",
        "orders_disabled": projection.order_capability_state == "DISABLED",
        "network_side_effect_absent": not projection.network_side_effect_present,
        "runtime_side_effect_absent": not projection.runtime_side_effect_present,
        "verification_status": verification_status,
        "decision_code": decision_code,
        "blocking_reasons": blocking_reasons,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_VERIFICATION_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return DeployedInactiveVerificationResult(
        verification_status=verification_status,
        decision_code=decision_code,
        blocking_reasons=tuple(blocking_reasons),
        fail_closed_gates=tuple(dict.fromkeys(fail_closed_gates)),
        contract_body=contract_body,
    )


def build_deployed_inactive_verification_v1(
    request: DeployedInactiveVerificationInput,
) -> dict[str, Any]:
    return evaluate_deployed_inactive_verification_v1(request).contract_body


def serialize_deployment_candidate_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def serialize_deployed_inactive_verification_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise DeployInactiveError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise DeployInactiveError("output directory must not be under /tmp")


def _artifact_bytes_for_manifest_digest(
    contract: Mapping[str, Any],
    *,
    serialize: Any,
) -> bytes:
    body = {
        key: value for key, value in contract.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize(body).encode("utf-8")


def _compute_output_manifest_digest(
    contract: Mapping[str, Any],
    *,
    serialize: Any,
) -> str:
    return hashlib.sha256(
        _artifact_bytes_for_manifest_digest(contract, serialize=serialize)
    ).hexdigest()


def _build_self_verification(
    *,
    contract_name: str,
    contract_version: str,
    schema_version: str,
    artifact_rel: str,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {
            "check_id": "manifest_digest",
            "status": "PASS" if manifest_digest else "FAIL",
        },
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": schema_version,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "overall_status": overall,
        "checks": checks,
        "verified_artifact_rel": artifact_rel,
        "manifest_digest": manifest_digest,
    }


def _validate_deployment_candidate_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != DEPLOYMENT_CANDIDATE_CONTRACT_NAME:
        raise DeployInactiveError("contract_name mismatch")
    if contract.get("contract_version") != DEPLOYMENT_CANDIDATE_CONTRACT_VERSION:
        raise DeployInactiveError("contract_version mismatch")
    status = contract.get("deployment_candidate_status")
    if status not in _VALID_DEPLOYMENT_CANDIDATE_STATUSES:
        raise DeployInactiveError("deployment_candidate_status invalid")
    decision_code = str(contract.get("decision_code", ""))
    if status == "DEPLOYABLE" and decision_code != "DEPLOYABLE":
        raise DeployInactiveError("DEPLOYABLE status requires decision_code DEPLOYABLE")
    if (
        status == "NOT_DEPLOYABLE"
        and decision_code not in _DEPLOYMENT_CANDIDATE_FAIL_CLOSED_DECISION_CODES
    ):
        raise DeployInactiveError("unknown NOT_DEPLOYABLE decision_code")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise DeployInactiveError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise DeployInactiveError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise DeployInactiveError("output_digest mismatch")
    for key, expected_value in _DEPLOYMENT_CANDIDATE_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected_value:
            raise DeployInactiveError(f"{key} must remain {expected_value!r}")


def _validate_verification_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != VERIFICATION_CONTRACT_NAME:
        raise DeployInactiveError("contract_name mismatch")
    if contract.get("contract_version") != VERIFICATION_CONTRACT_VERSION:
        raise DeployInactiveError("contract_version mismatch")
    status = contract.get("verification_status")
    if status not in _VALID_VERIFICATION_STATUSES:
        raise DeployInactiveError("verification_status invalid")
    decision_code = str(contract.get("decision_code", ""))
    if status == "VERIFIED_INACTIVE_PROJECTION" and decision_code != "VERIFIED_INACTIVE_PROJECTION":
        raise DeployInactiveError("VERIFIED status requires matching decision_code")
    if (
        status == "VERIFICATION_FAILED"
        and decision_code not in _VERIFICATION_FAIL_CLOSED_DECISION_CODES
    ):
        raise DeployInactiveError("unknown VERIFICATION_FAILED decision_code")
    if contract.get("observed_state_source") != OBSERVED_STATE_SOURCE:
        raise DeployInactiveError("observed_state_source must be OFFLINE_DECLARATIVE_PROJECTION")
    if contract.get("real_runtime_observation") is not False:
        raise DeployInactiveError("real_runtime_observation must remain false")
    if contract.get("real_deployment_confirmed") is not False:
        raise DeployInactiveError("real_deployment_confirmed must remain false")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise DeployInactiveError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise DeployInactiveError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise DeployInactiveError("output_digest mismatch")


def reverify_deployment_candidate_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / DEPLOYMENT_CANDIDATE_ARTIFACT_REL
    if not artifact_path.is_file():
        raise DeployInactiveError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise DeployInactiveError("artifact must be a JSON object")
    _validate_deployment_candidate_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_deployment_candidate_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise DeployInactiveError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise DeployInactiveError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def reverify_deployed_inactive_verification_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / VERIFICATION_ARTIFACT_REL
    if not artifact_path.is_file():
        raise DeployInactiveError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise DeployInactiveError("artifact must be a JSON object")
    _validate_verification_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_deployed_inactive_verification_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise DeployInactiveError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise DeployInactiveError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def _produce_contract_bundle(
    *,
    contract_body: dict[str, Any],
    output_dir: Path | str,
    artifact_rel: str,
    staging_prefix: str,
    serialize: Any,
    reverify: Any,
    validate_integrity: Any,
    contract_name: str,
    contract_version: str,
    schema_version: str,
) -> tuple[Path, str, str]:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    staging = final_dir.parent / f"{staging_prefix}{uuid.uuid4().hex}"
    if staging.exists():
        raise DeployInactiveError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / artifact_rel
        self_path = staging / SELF_VERIFICATION_REL
        manifest_digest = _compute_output_manifest_digest(contract_body, serialize=serialize)
        contract_body["manifest_digest"] = manifest_digest
        artifact_path.write_text(serialize(contract_body), encoding="utf-8")
        self_payload = _build_self_verification(
            contract_name=contract_name,
            contract_version=contract_version,
            schema_version=schema_version,
            artifact_rel=artifact_rel,
            contract=contract_body,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise DeployInactiveError(f"MANIFEST.sha256 verification failed before publish: {msg}")
        validate_integrity(read_manifest(artifact_path))
        reverify(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise DeployInactiveError(f"MANIFEST.sha256 verification failed after publish: {msg}")
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return final_dir, str(contract_body["output_digest"]), manifest_digest


def produce_deployment_candidate_v1(
    *,
    request: DeploymentCandidateEvaluationInput,
    output_dir: Path | str,
) -> DeploymentCandidateResult:
    evaluation = evaluate_deployment_candidate_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=DEPLOYMENT_CANDIDATE_ARTIFACT_REL,
        staging_prefix=DEPLOYMENT_CANDIDATE_STAGING_PREFIX,
        serialize=serialize_deployment_candidate_v1,
        reverify=reverify_deployment_candidate_v1,
        validate_integrity=_validate_deployment_candidate_integrity,
        contract_name=DEPLOYMENT_CANDIDATE_CONTRACT_NAME,
        contract_version=DEPLOYMENT_CANDIDATE_CONTRACT_VERSION,
        schema_version="deployment_candidate_self_verification_v1",
    )
    return DeploymentCandidateResult(
        output_dir=final_dir,
        deployment_candidate_id=str(contract_body["deployment_candidate_id"]),
        deployment_candidate_status=str(contract_body["deployment_candidate_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def produce_deployed_inactive_verification_v1(
    *,
    request: DeployedInactiveVerificationInput,
    output_dir: Path | str,
) -> DeployedInactiveVerificationProduceResult:
    evaluation = evaluate_deployed_inactive_verification_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=VERIFICATION_ARTIFACT_REL,
        staging_prefix=VERIFICATION_STAGING_PREFIX,
        serialize=serialize_deployed_inactive_verification_v1,
        reverify=reverify_deployed_inactive_verification_v1,
        validate_integrity=_validate_verification_integrity,
        contract_name=VERIFICATION_CONTRACT_NAME,
        contract_version=VERIFICATION_CONTRACT_VERSION,
        schema_version="deployed_inactive_verification_self_verification_v1",
    )
    return DeployedInactiveVerificationProduceResult(
        output_dir=final_dir,
        verification_id=str(contract_body["verification_id"]),
        verification_status=str(contract_body["verification_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


__all__ = [
    "DEPLOYMENT_CANDIDATE_ARTIFACT_REL",
    "DEPLOYMENT_CANDIDATE_CONTRACT_NAME",
    "DEPLOY_INACTIVE_AUTHORITY_INVARIANTS",
    "DeployInactiveError",
    "DeployedInactiveVerificationInput",
    "DeployedInactiveVerificationProduceResult",
    "DeployedInactiveVerificationResult",
    "DeploymentCandidateEvaluationInput",
    "DeploymentCandidateEvaluationResult",
    "DeploymentCandidateResult",
    "OBSERVED_STATE_SOURCE",
    "OfflineDeclarativeProjection",
    "VERIFICATION_ARTIFACT_REL",
    "VERIFICATION_CONTRACT_NAME",
    "build_deployed_inactive_verification_v1",
    "build_deployment_candidate_v1",
    "default_deployed_inactive_verification_input",
    "default_deployment_candidate_evaluation_input",
    "default_offline_declarative_projection",
    "evaluate_deployed_inactive_verification_v1",
    "evaluate_deployment_candidate_v1",
    "produce_deployed_inactive_verification_v1",
    "produce_deployment_candidate_v1",
    "reverify_deployed_inactive_verification_v1",
    "reverify_deployment_candidate_v1",
    "serialize_deployed_inactive_verification_v1",
    "serialize_deployment_candidate_v1",
]
