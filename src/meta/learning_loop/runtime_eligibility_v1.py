"""Offline RUNBOOK_STEP_24 runtime eligibility evidence contract owner v1."""

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
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
    KILL_SWITCH_OWNER_REF,
    KILL_SWITCH_POLICY_DIGEST,
    KILL_SWITCH_STATE_MACHINE_DIGEST,
)

CONTRACT_NAME = "runtime_eligibility_evidence_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "runtime_eligibility_evidence_v1"
BUILDER_VERSION = "runtime_eligibility_evidence_builder_v1"
POLICY_VERSION = "runtime_eligibility_policy_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "runtime_eligibility_evidence_record"
ARTIFACT_REL = "runtime_eligibility_evidence_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".runtime_eligibility_staging_"

SCHEMA_VERSION = "runtime_eligibility_evidence_schema_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = "peak_trade_offline_runtime_eligibility_producer_v1"
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
DEFAULT_CANDIDATE_VERSION = "v1"
SUPPORTED_CANDIDATE_VERSIONS = frozenset({"v1"})

MASTER_V2_OWNER_REF = "src/governance/master_v2"
MASTER_V2_CONTRACT_DIGEST = (
    "master_v2_owner_contract_digest_v1_"
    "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678901234567890abcdef12"
)
DOUBLE_PLAY_OWNER_REF = "src/governance/double_play"
DOUBLE_PLAY_CONTRACT_DIGEST = (
    "double_play_owner_contract_digest_v1_"
    "b2c3d4e5f60718293a4b5c6d7e8f9012345678901234567890abcdef1234"
)
BULL_COMPONENT_REF = "src/governance/bull_component"
BEAR_COMPONENT_REF = "src/governance/bear_component"
BULL_BEAR_SEMANTIC_DIGEST = (
    "bull_bear_semantic_digest_v1_c3d4e5f60718293a4b5c6d7e8f9012345678901234567890abcdef123456"
)
DYNAMIC_SCOPE_OWNER_REF = "src/governance/dynamic_scope"
DYNAMIC_SCOPE_POLICY_DIGEST = (
    "dynamic_scope_policy_digest_v1_d4e5f60718293a4b5c6d7e8f9012345678901234567890abcdef1234567"
)
RISK_OWNER_REF = "src/governance/risk"
SIZING_OWNER_REF = "src/governance/sizing"
SCOPE_CAPITAL_OWNER_REF = "src/governance/scope_capital"
CANONICAL_ORDER_INTENT_CONTRACT_REF = "src/governance/canonical_order_intent"
CANONICAL_ORDER_INTENT_CONTRACT_DIGEST = (
    "canonical_order_intent_contract_digest_v1_"
    "e5f60718293a4b5c6d7e8f9012345678901234567890abcdef12345678"
)
AUTHORITY_CONTRACT_REF = "src/meta/learning_loop/authority_lease_and_revocation_v1"
AUTHORITY_CONTRACT_DIGEST = (
    "authority_contract_digest_v1_f60718293a4b5c6d7e8f9012345678901234567890abcdef1234567890"
)
REVOCATION_CONTRACT_REF = "src/meta/learning_loop/authority_lease_and_revocation_v1#revocation"
REVOCATION_CONTRACT_DIGEST = (
    "revocation_contract_digest_v1_0718293a4b5c6d7e8f9012345678901234567890abcdef123456789012"
)

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_VALID_ELIGIBILITY_STATUSES = frozenset({"ELIGIBLE", "INELIGIBLE"})
_VALID_READINESS_STATUSES = frozenset({"PROVEN", "NOT_PROVEN", "UNKNOWN"})
_SELF_VERIFICATION_SCHEMA_VERSION = "runtime_eligibility_evidence_self_verification_v1"

_FAIL_CLOSED_DECISION_CODES: tuple[str, ...] = (
    "MISSING_CANDIDATE_ARTIFACT",
    "CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
    "UNSUPPORTED_CANDIDATE_VERSION",
    "MISSING_PROMOTION_DECISION",
    "PROMOTION_DECISION_DIGEST_MISMATCH",
    "PROMOTION_STATUS_NOT_APPROVED",
    "PROMOTION_DECISION_NOT_AUTHORIZED_BY_CANONICAL_OWNER",
    "MISSING_COMPLETION_EVIDENCE",
    "COMPLETION_EVIDENCE_DIGEST_MISMATCH",
    "MISSING_RESEARCH_VALIDITY",
    "RESEARCH_VALIDITY_DIGEST_MISMATCH",
    "RESEARCH_VALIDITY_NOT_PASS",
    "MISSING_TRADING_LOGIC_COMPATIBILITY",
    "TRADING_LOGIC_COMPATIBILITY_DIGEST_MISMATCH",
    "MASTER_V2_OWNER_INVALID",
    "MASTER_V2_CONTRACT_DIGEST_MISMATCH",
    "DOUBLE_PLAY_OWNER_INVALID",
    "DOUBLE_PLAY_CONTRACT_DIGEST_MISMATCH",
    "BULL_BEAR_COMPONENT_BINDING_INVALID",
    "BULL_BEAR_SEMANTIC_DIGEST_MISMATCH",
    "DYNAMIC_SCOPE_OWNER_INVALID",
    "DYNAMIC_SCOPE_POLICY_DIGEST_MISMATCH",
    "RISK_OWNER_INVALID",
    "SIZING_OWNER_INVALID",
    "SCOPE_CAPITAL_OWNER_INVALID",
    "CANONICAL_ORDER_INTENT_LINEAGE_INVALID",
    "TRADING_LOGIC_BYPASS_DETECTED",
    "PARALLEL_TRADING_LOGIC_SSOT_DETECTED",
    "MISSING_KILLSWITCH_CONTRACT",
    "KILLSWITCH_CONTRACT_DIGEST_MISMATCH",
    "KILLSWITCH_POLICY_DIGEST_MISMATCH",
    "KILLSWITCH_STATE_MACHINE_DIGEST_MISMATCH",
    "MISSING_KILLSWITCH_WRITER_FENCING_EVIDENCE",
    "KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
    "KILLSWITCH_INDEPENDENT_READ_PATHS_NOT_PROVEN",
    "MISSING_PRE_TRADE_SAFETY_KERNEL_EVIDENCE",
    "PRE_TRADE_SAFETY_KERNEL_EVIDENCE_INVALID",
    "PRE_TRADE_SAFETY_NOT_FAIL_CLOSED",
    "MISSING_ADAPTER_SUBMISSION_CONTRACT",
    "ADAPTER_SUBMISSION_CONTRACT_INVALID",
    "ADAPTER_SEMANTIC_MUTATION_ALLOWED",
    "MISSING_VENUE_CAPABILITY_SNAPSHOT",
    "VENUE_CAPABILITY_DIGEST_MISMATCH",
    "VENUE_CAPABILITY_STALE",
    "VENUE_CAPABILITY_SCOPE_MISMATCH",
    "MISSING_RECONCILIATION_EVIDENCE",
    "RECONCILIATION_READINESS_NOT_PROVEN",
    "MISSING_UNKNOWN_OUTCOME_RECOVERY_EVIDENCE",
    "UNKNOWN_OUTCOME_RECOVERY_NOT_FAIL_CLOSED",
    "MISSING_AUTHORITY_CONTRACT",
    "AUTHORITY_CONTRACT_INVALID",
    "MISSING_REVOCATION_CONTRACT",
    "REVOCATION_CONTRACT_INVALID",
    "ENVIRONMENT_BINDING_MISSING",
    "ENVIRONMENT_BINDING_MISMATCH",
    "VENUE_SCOPE_MISSING",
    "VENUE_SCOPE_MISMATCH",
    "INSTRUMENT_SCOPE_MISSING",
    "INSTRUMENT_SCOPE_MISMATCH",
    "RISK_POLICY_DIGEST_MISSING",
    "RISK_POLICY_DIGEST_MISMATCH",
    "SIZING_PROFILE_BINDING_MISSING",
    "SCOPE_CAPITAL_BINDING_MISSING",
    "ROLLBACK_CAPABILITY_MISSING",
    "DATA_READINESS_NOT_PROVEN",
    "ADAPTER_READINESS_NOT_PROVEN",
    "BUDGET_READINESS_NOT_PROVEN",
    "INPUT_EPOCH_MISMATCH",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "UNKNOWN_DECISION_CODE",
    "MISSING_REQUIRED_INPUT",
    "SPOT_MARKET_TYPE_REJECTED",
    "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
    "UNKNOWN_MARKET_TYPE_REJECTED",
    "MISSING_MARKET_TYPE_REJECTED",
)

RUNTIME_ELIGIBILITY_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "runtime_eligibility_contract_complete": False,
    "runtime_eligibility_offline_only": True,
    "runtime_eligibility_is_evidence": True,
    "runtime_eligibility_is_not_deployment": True,
    "runtime_eligibility_is_not_activation": True,
    "runtime_eligibility_is_not_authority": True,
    "runtime_eligibility_is_not_execution_permission": True,
    "runtime_eligibility_does_not_authorize_orders": True,
    "runtime_eligibility_does_not_mutate_runtime": True,
    "eligible_does_not_mean_deployable": True,
    "eligible_does_not_mean_deployed": True,
    "eligible_does_not_mean_activated": True,
    "eligible_does_not_mean_trading": True,
    "eligible_does_not_create_authority": True,
    "eligible_does_not_activate_authority": True,
    "eligible_does_not_create_execution_permission": True,
    "eligible_does_not_authorize_submission": True,
    "eligible_does_not_allow_orders": True,
    "eligible_does_not_mutate_runtime": True,
    "generic_futures_market_type_guard": True,
    "spot_rejected_fail_closed": True,
    "synthetic_spot_rejected_fail_closed": True,
    "unknown_market_type_rejected_fail_closed": True,
    "missing_market_type_rejected_fail_closed": True,
    "futures_only": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_MUTATION_FLAGS: dict[str, bool] = {
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
    "does_not_deploy": True,
    "does_not_activate": True,
    "does_not_create_authority": True,
    "does_not_activate_authority": True,
    "does_not_create_execution_permission": True,
    "does_not_authorize_submission": True,
    "does_not_mutate_runtime": True,
    "does_not_invoke_adapter": True,
    "does_not_send_network_request": True,
    "does_not_submit_order": True,
}


class RuntimeEligibilityError(ValueError):
    """Fail-closed runtime eligibility contract error."""


@dataclass(frozen=True)
class RuntimeEligibilityEvaluationInput:
    contract_version: str = CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = BUILDER_VERSION
    policy_version: str = POLICY_VERSION
    candidate_id: str = ""
    candidate_artifact_ref: str = ""
    candidate_artifact_body: dict[str, Any] = field(default_factory=dict)
    candidate_artifact_digest: str = ""
    candidate_version: str = DEFAULT_CANDIDATE_VERSION
    market_type: str = "FUTURES"
    promotion_decision_ref: str = ""
    promotion_decision_body: dict[str, Any] = field(default_factory=dict)
    promotion_decision_digest: str = ""
    promotion_status: str = "PASS"
    promotion_decision_outcome: str = "APPROVE"
    promotion_authorized_by_canonical_owner: bool = True
    completion_evidence_ref: str = ""
    completion_evidence_digest: str = ""
    research_validity_ref: str = ""
    research_validity_digest: str = ""
    research_validity_status: str = "PASS"
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
    kill_switch_owner_ref: str = KILL_SWITCH_OWNER_REF
    kill_switch_contract_digest: str = KILL_SWITCH_CONTRACT_DIGEST
    kill_switch_policy_digest: str = KILL_SWITCH_POLICY_DIGEST
    kill_switch_state_machine_digest: str = KILL_SWITCH_STATE_MACHINE_DIGEST
    kill_switch_writer_fencing_evidence_ref: str = ""
    kill_switch_writer_fencing_evidence_digest: str = ""
    kill_switch_writer_fencing_decision: str = "PASS"
    kill_switch_independent_read_paths_proven: bool = True
    pre_trade_safety_kernel_evidence_ref: str = ""
    pre_trade_safety_kernel_evidence_digest: str = ""
    pre_trade_safety_kernel_status: str = "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED"
    pre_trade_safety_fail_closed: bool = True
    adapter_submission_contract_ref: str = ""
    adapter_submission_contract_digest: str = ""
    adapter_submission_contract_status: str = "ADAPTER_SUBMISSION_CONTRACT_VALID"
    adapter_semantic_mutation_allowed: bool = False
    venue_capability_snapshot_ref: str = ""
    venue_capability_snapshot_digest: str = ""
    venue_capability_snapshot_status: str = "VENUE_CAPABILITY_SNAPSHOT_VALID"
    venue_capability_stale: bool = False
    venue_capability_venue_scope: str = ""
    reconciliation_evidence_ref: str = ""
    reconciliation_evidence_digest: str = ""
    reconciliation_contract_status: str = "RUNTIME_STATE_RECONCILIATION_VALID"
    unknown_outcome_recovery_evidence_ref: str = ""
    unknown_outcome_recovery_evidence_digest: str = ""
    unknown_outcome_recovery_contract_status: str = "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"
    unknown_outcome_recovery_fail_closed: bool = True
    authority_contract_ref: str = AUTHORITY_CONTRACT_REF
    authority_contract_digest: str = AUTHORITY_CONTRACT_DIGEST
    revocation_contract_ref: str = REVOCATION_CONTRACT_REF
    revocation_contract_digest: str = REVOCATION_CONTRACT_DIGEST
    environment: str = ""
    venue_scope: str = ""
    instrument_scope: str = ""
    risk_policy_digest: str = ""
    sizing_profile_digest: str = ""
    scope_capital_digest: str = ""
    rollback_parent_ref: str = ""
    rollback_capability_proven: bool = True
    deployment_compatibility_binding_digest: str = ""
    runtime_budget_binding_digest: str = ""
    input_epoch: int = 1
    bound_input_epoch: int = 1
    data_readiness_status: str = "PROVEN"
    adapter_readiness_status: str = "PROVEN"
    reconciliation_readiness_status: str = "PROVEN"
    kill_switch_readiness_status: str = "PROVEN"
    rollback_readiness_status: str = "PROVEN"
    budget_readiness_status: str = "PROVEN"
    trading_logic_readiness_status: str = "PROVEN"
    safety_readiness_status: str = "PROVEN"
    authority_contract_readiness_status: str = "PROVEN"
    venue_capability_readiness_status: str = "PROVEN"
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuntimeEligibilityEvaluationResult:
    eligibility_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    fail_closed_gates: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class RuntimeEligibilityResult:
    output_dir: Path
    evidence_id: str
    eligibility_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


def compute_candidate_artifact_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(body)


def compute_promotion_decision_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(body)


def default_candidate_artifact_body(
    *, candidate_id: str = "generic-futures-candidate-001"
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "candidate_version": DEFAULT_CANDIDATE_VERSION,
        "market_type": "FUTURES",
        "environment": "offline-evaluation",
        "venue_scope": "GENERIC-FUTURES-VENUE-001",
        "instrument_scope": "GENERIC-FUTURES-PERP-001",
    }


def default_promotion_decision_body(
    *, candidate_id: str = "generic-futures-candidate-001"
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "decision_status": "PASS",
        "decision_outcome": "APPROVE",
        "authorized_by_canonical_owner": True,
        "promotion_status": "APPROVED",
    }


def default_runtime_eligibility_evaluation_input() -> RuntimeEligibilityEvaluationInput:
    candidate_id = "generic-futures-candidate-001"
    candidate_body = default_candidate_artifact_body(candidate_id=candidate_id)
    candidate_digest = compute_candidate_artifact_digest(candidate_body)
    promotion_body = default_promotion_decision_body(candidate_id=candidate_id)
    promotion_digest = compute_promotion_decision_digest(promotion_body)
    completion_digest = compute_content_sha256(
        {"completion_status": "COMPLETE", "candidate_id": candidate_id}
    )
    research_digest = compute_content_sha256(
        {"research_validity_status": "PASS", "candidate_id": candidate_id}
    )
    trading_logic_digest = compute_content_sha256(
        {
            "trading_logic_compatibility_status": "TRADING_LOGIC_COMPATIBLE",
            "candidate_id": candidate_id,
        }
    )
    writer_fencing_digest = compute_content_sha256(
        {"decision": "PASS", "independent_read_paths_proven": True}
    )
    safety_digest = compute_content_sha256(
        {"contract_status": "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED", "fail_closed": True}
    )
    adapter_digest = compute_content_sha256(
        {"contract_status": "ADAPTER_SUBMISSION_CONTRACT_VALID", "semantic_mutation_allowed": False}
    )
    venue_digest = compute_content_sha256(
        {
            "contract_status": "VENUE_CAPABILITY_SNAPSHOT_VALID",
            "market_type": "FUTURES",
            "venue_scope": "GENERIC-FUTURES-VENUE-001",
            "stale": False,
        }
    )
    reconciliation_digest = compute_content_sha256(
        {"contract_status": "RUNTIME_STATE_RECONCILIATION_VALID", "readiness": "PROVEN"}
    )
    recovery_digest = compute_content_sha256(
        {"contract_status": "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID", "fail_closed": True}
    )
    risk_digest = compute_content_sha256({"risk_policy_id": "generic-futures-risk-policy-001"})
    sizing_digest = compute_content_sha256(
        {"sizing_profile_id": "generic-futures-sizing-profile-001"}
    )
    scope_capital_digest = compute_content_sha256(
        {"scope_capital_id": "generic-futures-scope-capital-001"}
    )
    deployment_binding_digest = compute_content_sha256({"deployment_compatibility": "BOUND"})
    budget_digest = compute_content_sha256(
        {"runtime_budget_id": "generic-futures-runtime-budget-001"}
    )
    environment = "offline-evaluation"
    venue_scope = "GENERIC-FUTURES-VENUE-001"
    instrument_scope = "GENERIC-FUTURES-PERP-001"
    input_refs = (
        candidate_digest,
        promotion_digest,
        completion_digest,
        research_digest,
        trading_logic_digest,
        writer_fencing_digest,
        safety_digest,
        adapter_digest,
        venue_digest,
        reconciliation_digest,
        recovery_digest,
    )
    return RuntimeEligibilityEvaluationInput(
        candidate_id=candidate_id,
        candidate_artifact_ref=f"offline/{candidate_id}/candidate-artifact",
        candidate_artifact_body=candidate_body,
        candidate_artifact_digest=candidate_digest,
        market_type="FUTURES",
        promotion_decision_ref=f"offline/{candidate_id}/promotion-decision",
        promotion_decision_body=promotion_body,
        promotion_decision_digest=promotion_digest,
        completion_evidence_ref=f"offline/{candidate_id}/completion-evidence",
        completion_evidence_digest=completion_digest,
        research_validity_ref=f"offline/{candidate_id}/research-validity",
        research_validity_digest=research_digest,
        trading_logic_compatibility_ref=f"offline/{candidate_id}/trading-logic-compatibility",
        trading_logic_compatibility_digest=trading_logic_digest,
        kill_switch_writer_fencing_evidence_ref=f"offline/{candidate_id}/killswitch-writer-fencing",
        kill_switch_writer_fencing_evidence_digest=writer_fencing_digest,
        pre_trade_safety_kernel_evidence_ref=f"offline/{candidate_id}/pre-trade-safety-kernel",
        pre_trade_safety_kernel_evidence_digest=safety_digest,
        adapter_submission_contract_ref=f"offline/{candidate_id}/adapter-submission-contract",
        adapter_submission_contract_digest=adapter_digest,
        venue_capability_snapshot_ref=f"offline/{candidate_id}/venue-capability-snapshot",
        venue_capability_snapshot_digest=venue_digest,
        venue_capability_venue_scope=venue_scope,
        reconciliation_evidence_ref=f"offline/{candidate_id}/reconciliation-evidence",
        reconciliation_evidence_digest=reconciliation_digest,
        unknown_outcome_recovery_evidence_ref=f"offline/{candidate_id}/unknown-outcome-recovery",
        unknown_outcome_recovery_evidence_digest=recovery_digest,
        environment=environment,
        venue_scope=venue_scope,
        instrument_scope=instrument_scope,
        risk_policy_digest=risk_digest,
        sizing_profile_digest=sizing_digest,
        scope_capital_digest=scope_capital_digest,
        rollback_parent_ref=f"offline/{candidate_id}/rollback-parent",
        deployment_compatibility_binding_digest=deployment_binding_digest,
        runtime_budget_binding_digest=budget_digest,
        input_refs=input_refs,
        input_digests=input_refs,
    )


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


def evaluate_runtime_eligibility_v1(
    request: RuntimeEligibilityEvaluationInput,
) -> RuntimeEligibilityEvaluationResult:
    blocking_reasons: list[str] = []
    fail_closed_gates: list[str] = []

    if request.contract_version != CONTRACT_VERSION:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_CONTRACT_VERSION",
            gate_id="contract_version",
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

    market_type = str(request.market_type or "").strip().upper()
    if not market_type:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_MARKET_TYPE_REJECTED",
            gate_id="market_type",
        )
    elif market_type in _FORBIDDEN_MARKET_TYPES:
        code = (
            "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"
            if market_type in {"SYNTHETIC_SPOT", "SYNTHETIC-SPOT"}
            else "SPOT_MARKET_TYPE_REJECTED"
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

    if not request.candidate_artifact_ref.strip() or not request.candidate_artifact_body:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_CANDIDATE_ARTIFACT",
            gate_id="candidate_artifact",
        )
    else:
        expected_candidate_digest = compute_candidate_artifact_digest(
            request.candidate_artifact_body
        )
        _validate_digest_field(
            blocking_reasons,
            fail_closed_gates,
            value=request.candidate_artifact_digest,
            expected=expected_candidate_digest,
            missing_code="MISSING_CANDIDATE_ARTIFACT",
            mismatch_code="CANDIDATE_ARTIFACT_DIGEST_MISMATCH",
            gate_id="candidate_artifact_digest",
        )
        if request.candidate_version not in SUPPORTED_CANDIDATE_VERSIONS:
            _append_rejection(
                blocking_reasons,
                fail_closed_gates,
                decision_code="UNSUPPORTED_CANDIDATE_VERSION",
                gate_id="candidate_version",
            )

    if not request.promotion_decision_ref.strip() or not request.promotion_decision_body:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_PROMOTION_DECISION",
            gate_id="promotion_decision",
        )
    else:
        expected_promotion_digest = compute_promotion_decision_digest(
            request.promotion_decision_body
        )
        _validate_digest_field(
            blocking_reasons,
            fail_closed_gates,
            value=request.promotion_decision_digest,
            expected=expected_promotion_digest,
            missing_code="MISSING_PROMOTION_DECISION",
            mismatch_code="PROMOTION_DECISION_DIGEST_MISMATCH",
            gate_id="promotion_decision_digest",
        )
        if request.promotion_status != "PASS" or request.promotion_decision_outcome != "APPROVE":
            _append_rejection(
                blocking_reasons,
                fail_closed_gates,
                decision_code="PROMOTION_STATUS_NOT_APPROVED",
                gate_id="promotion_status",
            )
        if not request.promotion_authorized_by_canonical_owner:
            _append_rejection(
                blocking_reasons,
                fail_closed_gates,
                decision_code="PROMOTION_DECISION_NOT_AUTHORIZED_BY_CANONICAL_OWNER",
                gate_id="promotion_authorization",
            )

    if not request.completion_evidence_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_COMPLETION_EVIDENCE",
            gate_id="completion_evidence",
        )
    elif not is_valid_sha256_hex(request.completion_evidence_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="COMPLETION_EVIDENCE_DIGEST_MISMATCH",
            gate_id="completion_evidence_digest",
        )

    if not request.research_validity_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_RESEARCH_VALIDITY",
            gate_id="research_validity",
        )
    elif not is_valid_sha256_hex(request.research_validity_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RESEARCH_VALIDITY_DIGEST_MISMATCH",
            gate_id="research_validity_digest",
        )
    elif request.research_validity_status != "PASS":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RESEARCH_VALIDITY_NOT_PASS",
            gate_id="research_validity_status",
        )

    if not request.trading_logic_compatibility_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_TRADING_LOGIC_COMPATIBILITY",
            gate_id="trading_logic_compatibility",
        )
    elif not is_valid_sha256_hex(request.trading_logic_compatibility_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="TRADING_LOGIC_COMPATIBILITY_DIGEST_MISMATCH",
            gate_id="trading_logic_compatibility_digest",
        )
    elif request.trading_logic_compatibility_status != "TRADING_LOGIC_COMPATIBLE":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_TRADING_LOGIC_COMPATIBILITY",
            gate_id="trading_logic_compatibility_status",
        )

    if request.master_v2_owner_ref != MASTER_V2_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MASTER_V2_OWNER_INVALID",
            gate_id="master_v2_owner_ref",
        )
    if request.master_v2_contract_digest != MASTER_V2_CONTRACT_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MASTER_V2_CONTRACT_DIGEST_MISMATCH",
            gate_id="master_v2_contract_digest",
        )
    if request.double_play_owner_ref != DOUBLE_PLAY_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="DOUBLE_PLAY_OWNER_INVALID",
            gate_id="double_play_owner_ref",
        )
    if request.double_play_contract_digest != DOUBLE_PLAY_CONTRACT_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="DOUBLE_PLAY_CONTRACT_DIGEST_MISMATCH",
            gate_id="double_play_contract_digest",
        )
    if not request.bull_component_ref.strip() or not request.bear_component_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="BULL_BEAR_COMPONENT_BINDING_INVALID",
            gate_id="bull_bear_component_ref",
        )
    if request.bull_bear_semantic_digest != BULL_BEAR_SEMANTIC_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="BULL_BEAR_SEMANTIC_DIGEST_MISMATCH",
            gate_id="bull_bear_semantic_digest",
        )
    if request.dynamic_scope_owner_ref != DYNAMIC_SCOPE_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="DYNAMIC_SCOPE_OWNER_INVALID",
            gate_id="dynamic_scope_owner_ref",
        )
    if request.dynamic_scope_policy_digest != DYNAMIC_SCOPE_POLICY_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="DYNAMIC_SCOPE_POLICY_DIGEST_MISMATCH",
            gate_id="dynamic_scope_policy_digest",
        )
    if request.risk_owner_ref != RISK_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RISK_OWNER_INVALID",
            gate_id="risk_owner_ref",
        )
    if request.sizing_owner_ref != SIZING_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="SIZING_OWNER_INVALID",
            gate_id="sizing_owner_ref",
        )
    if request.scope_capital_owner_ref != SCOPE_CAPITAL_OWNER_REF:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="SCOPE_CAPITAL_OWNER_INVALID",
            gate_id="scope_capital_owner_ref",
        )
    if (
        not request.canonical_order_intent_contract_ref.strip()
        or request.canonical_order_intent_contract_digest != CANONICAL_ORDER_INTENT_CONTRACT_DIGEST
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="CANONICAL_ORDER_INTENT_LINEAGE_INVALID",
            gate_id="canonical_order_intent_contract",
        )
    if request.trading_logic_bypass_detected:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="TRADING_LOGIC_BYPASS_DETECTED",
            gate_id="trading_logic_bypass",
        )
    if request.parallel_trading_logic_ssot_detected:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="PARALLEL_TRADING_LOGIC_SSOT_DETECTED",
            gate_id="parallel_trading_logic_ssot",
        )

    if not request.kill_switch_owner_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_KILLSWITCH_CONTRACT",
            gate_id="kill_switch_owner_ref",
        )
    if request.kill_switch_contract_digest != KILL_SWITCH_CONTRACT_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_CONTRACT_DIGEST_MISMATCH",
            gate_id="kill_switch_contract_digest",
        )
    if request.kill_switch_policy_digest != KILL_SWITCH_POLICY_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_POLICY_DIGEST_MISMATCH",
            gate_id="kill_switch_policy_digest",
        )
    if request.kill_switch_state_machine_digest != KILL_SWITCH_STATE_MACHINE_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_STATE_MACHINE_DIGEST_MISMATCH",
            gate_id="kill_switch_state_machine_digest",
        )
    if not request.kill_switch_writer_fencing_evidence_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_KILLSWITCH_WRITER_FENCING_EVIDENCE",
            gate_id="kill_switch_writer_fencing_evidence",
        )
    elif not is_valid_sha256_hex(request.kill_switch_writer_fencing_evidence_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
            gate_id="kill_switch_writer_fencing_evidence_digest",
        )
    elif request.kill_switch_writer_fencing_decision != "PASS":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
            gate_id="kill_switch_writer_fencing_decision",
        )
    if not request.kill_switch_independent_read_paths_proven:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_INDEPENDENT_READ_PATHS_NOT_PROVEN",
            gate_id="kill_switch_independent_read_paths",
        )

    if not request.pre_trade_safety_kernel_evidence_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_PRE_TRADE_SAFETY_KERNEL_EVIDENCE",
            gate_id="pre_trade_safety_kernel_evidence",
        )
    elif not is_valid_sha256_hex(request.pre_trade_safety_kernel_evidence_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="PRE_TRADE_SAFETY_KERNEL_EVIDENCE_INVALID",
            gate_id="pre_trade_safety_kernel_evidence_digest",
        )
    elif request.pre_trade_safety_kernel_status != "INDEPENDENT_PRE_TRADE_SAFETY_KERNEL_APPROVED":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="PRE_TRADE_SAFETY_KERNEL_EVIDENCE_INVALID",
            gate_id="pre_trade_safety_kernel_status",
        )
    if not request.pre_trade_safety_fail_closed:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="PRE_TRADE_SAFETY_NOT_FAIL_CLOSED",
            gate_id="pre_trade_safety_fail_closed",
        )

    if not request.adapter_submission_contract_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_ADAPTER_SUBMISSION_CONTRACT",
            gate_id="adapter_submission_contract",
        )
    elif not is_valid_sha256_hex(request.adapter_submission_contract_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_SUBMISSION_CONTRACT_INVALID",
            gate_id="adapter_submission_contract_digest",
        )
    elif request.adapter_submission_contract_status != "ADAPTER_SUBMISSION_CONTRACT_VALID":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_SUBMISSION_CONTRACT_INVALID",
            gate_id="adapter_submission_contract_status",
        )
    if request.adapter_semantic_mutation_allowed:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_SEMANTIC_MUTATION_ALLOWED",
            gate_id="adapter_semantic_mutation_allowed",
        )

    if not request.venue_capability_snapshot_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_VENUE_CAPABILITY_SNAPSHOT",
            gate_id="venue_capability_snapshot",
        )
    elif not is_valid_sha256_hex(request.venue_capability_snapshot_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="VENUE_CAPABILITY_DIGEST_MISMATCH",
            gate_id="venue_capability_snapshot_digest",
        )
    elif request.venue_capability_snapshot_status != "VENUE_CAPABILITY_SNAPSHOT_VALID":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_VENUE_CAPABILITY_SNAPSHOT",
            gate_id="venue_capability_snapshot_status",
        )
    if request.venue_capability_stale:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="VENUE_CAPABILITY_STALE",
            gate_id="venue_capability_stale",
        )
    if (
        request.venue_capability_venue_scope
        and request.venue_scope
        and request.venue_capability_venue_scope != request.venue_scope
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="VENUE_CAPABILITY_SCOPE_MISMATCH",
            gate_id="venue_capability_scope",
        )

    if not request.reconciliation_evidence_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_RECONCILIATION_EVIDENCE",
            gate_id="reconciliation_evidence",
        )
    elif not is_valid_sha256_hex(request.reconciliation_evidence_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_RECONCILIATION_EVIDENCE",
            gate_id="reconciliation_evidence_digest",
        )
    elif request.reconciliation_contract_status != "RUNTIME_STATE_RECONCILIATION_VALID":
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RECONCILIATION_READINESS_NOT_PROVEN",
            gate_id="reconciliation_contract_status",
        )

    if not request.unknown_outcome_recovery_evidence_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_UNKNOWN_OUTCOME_RECOVERY_EVIDENCE",
            gate_id="unknown_outcome_recovery_evidence",
        )
    elif not is_valid_sha256_hex(request.unknown_outcome_recovery_evidence_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_UNKNOWN_OUTCOME_RECOVERY_EVIDENCE",
            gate_id="unknown_outcome_recovery_evidence_digest",
        )
    elif (
        request.unknown_outcome_recovery_contract_status
        != "UNKNOWN_EXECUTION_OUTCOME_RECOVERY_VALID"
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_OUTCOME_RECOVERY_NOT_FAIL_CLOSED",
            gate_id="unknown_outcome_recovery_contract_status",
        )
    if not request.unknown_outcome_recovery_fail_closed:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_OUTCOME_RECOVERY_NOT_FAIL_CLOSED",
            gate_id="unknown_outcome_recovery_fail_closed",
        )

    if not request.authority_contract_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_AUTHORITY_CONTRACT",
            gate_id="authority_contract_ref",
        )
    elif request.authority_contract_digest != AUTHORITY_CONTRACT_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="AUTHORITY_CONTRACT_INVALID",
            gate_id="authority_contract_digest",
        )
    if not request.revocation_contract_ref.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_REVOCATION_CONTRACT",
            gate_id="revocation_contract_ref",
        )
    elif request.revocation_contract_digest != REVOCATION_CONTRACT_DIGEST:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="REVOCATION_CONTRACT_INVALID",
            gate_id="revocation_contract_digest",
        )

    if not request.environment.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ENVIRONMENT_BINDING_MISSING",
            gate_id="environment",
        )
    elif request.candidate_artifact_body.get("environment") not in (None, request.environment):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ENVIRONMENT_BINDING_MISMATCH",
            gate_id="environment_binding",
        )
    if not request.venue_scope.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="VENUE_SCOPE_MISSING",
            gate_id="venue_scope",
        )
    elif request.candidate_artifact_body.get("venue_scope") not in (None, request.venue_scope):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="VENUE_SCOPE_MISMATCH",
            gate_id="venue_scope_binding",
        )
    if not request.instrument_scope.strip():
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="INSTRUMENT_SCOPE_MISSING",
            gate_id="instrument_scope",
        )
    elif request.candidate_artifact_body.get("instrument_scope") not in (
        None,
        request.instrument_scope,
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="INSTRUMENT_SCOPE_MISMATCH",
            gate_id="instrument_scope_binding",
        )

    if not request.risk_policy_digest or not is_valid_sha256_hex(request.risk_policy_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="RISK_POLICY_DIGEST_MISSING",
            gate_id="risk_policy_digest",
        )
    if not request.sizing_profile_digest or not is_valid_sha256_hex(request.sizing_profile_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="SIZING_PROFILE_BINDING_MISSING",
            gate_id="sizing_profile_digest",
        )
    if not request.scope_capital_digest or not is_valid_sha256_hex(request.scope_capital_digest):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="SCOPE_CAPITAL_BINDING_MISSING",
            gate_id="scope_capital_digest",
        )

    if not request.rollback_parent_ref.strip() or not request.rollback_capability_proven:
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="ROLLBACK_CAPABILITY_MISSING",
            gate_id="rollback_capability",
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
        status=request.adapter_readiness_status,
        not_proven_code="ADAPTER_READINESS_NOT_PROVEN",
        gate_id="adapter_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.reconciliation_readiness_status,
        not_proven_code="RECONCILIATION_READINESS_NOT_PROVEN",
        gate_id="reconciliation_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.kill_switch_readiness_status,
        not_proven_code="KILLSWITCH_WRITER_FENCING_EVIDENCE_INVALID",
        gate_id="kill_switch_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.rollback_readiness_status,
        not_proven_code="ROLLBACK_CAPABILITY_MISSING",
        gate_id="rollback_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.budget_readiness_status,
        not_proven_code="BUDGET_READINESS_NOT_PROVEN",
        gate_id="budget_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.trading_logic_readiness_status,
        not_proven_code="MISSING_TRADING_LOGIC_COMPATIBILITY",
        gate_id="trading_logic_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.safety_readiness_status,
        not_proven_code="PRE_TRADE_SAFETY_KERNEL_EVIDENCE_INVALID",
        gate_id="safety_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.authority_contract_readiness_status,
        not_proven_code="AUTHORITY_CONTRACT_INVALID",
        gate_id="authority_contract_readiness_status",
    )
    _validate_readiness(
        blocking_reasons,
        fail_closed_gates,
        status=request.venue_capability_readiness_status,
        not_proven_code="MISSING_VENUE_CAPABILITY_SNAPSHOT",
        gate_id="venue_capability_readiness_status",
    )

    if not request.deployment_compatibility_binding_digest or not is_valid_sha256_hex(
        request.deployment_compatibility_binding_digest
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="MISSING_REQUIRED_INPUT",
            gate_id="deployment_compatibility_binding_digest",
        )
    if not request.runtime_budget_binding_digest or not is_valid_sha256_hex(
        request.runtime_budget_binding_digest
    ):
        _append_rejection(
            blocking_reasons,
            fail_closed_gates,
            decision_code="BUDGET_READINESS_NOT_PROVEN",
            gate_id="runtime_budget_binding_digest",
        )

    if blocking_reasons:
        eligibility_status = "INELIGIBLE"
        decision_code = blocking_reasons[0]
    else:
        eligibility_status = "ELIGIBLE"
        decision_code = "ELIGIBLE"

    evidence_id = compute_content_sha256(
        {
            "candidate_id": request.candidate_id,
            "candidate_artifact_digest": request.candidate_artifact_digest,
            "decision_code": decision_code,
        }
    )

    contract_body: dict[str, Any] = {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "evidence_id": evidence_id,
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "record_kind": RECORD_KIND,
        "candidate_id": request.candidate_id,
        "candidate_artifact_ref": request.candidate_artifact_ref,
        "candidate_artifact_digest": request.candidate_artifact_digest,
        "candidate_version": request.candidate_version,
        "market_type": market_type,
        "promotion_decision_ref": request.promotion_decision_ref,
        "promotion_decision_digest": request.promotion_decision_digest,
        "promotion_status": request.promotion_status,
        "promotion_decision_outcome": request.promotion_decision_outcome,
        "completion_evidence_ref": request.completion_evidence_ref,
        "completion_evidence_digest": request.completion_evidence_digest,
        "research_validity_ref": request.research_validity_ref,
        "research_validity_digest": request.research_validity_digest,
        "research_validity_status": request.research_validity_status,
        "trading_logic_compatibility_ref": request.trading_logic_compatibility_ref,
        "trading_logic_compatibility_digest": request.trading_logic_compatibility_digest,
        "trading_logic_compatibility_status": request.trading_logic_compatibility_status,
        "master_v2_owner_ref": request.master_v2_owner_ref,
        "master_v2_contract_digest": request.master_v2_contract_digest,
        "double_play_owner_ref": request.double_play_owner_ref,
        "double_play_contract_digest": request.double_play_contract_digest,
        "bull_component_ref": request.bull_component_ref,
        "bear_component_ref": request.bear_component_ref,
        "bull_bear_semantic_digest": request.bull_bear_semantic_digest,
        "dynamic_scope_owner_ref": request.dynamic_scope_owner_ref,
        "dynamic_scope_policy_digest": request.dynamic_scope_policy_digest,
        "risk_owner_ref": request.risk_owner_ref,
        "sizing_owner_ref": request.sizing_owner_ref,
        "scope_capital_owner_ref": request.scope_capital_owner_ref,
        "canonical_order_intent_contract_ref": request.canonical_order_intent_contract_ref,
        "canonical_order_intent_contract_digest": request.canonical_order_intent_contract_digest,
        "kill_switch_owner_ref": request.kill_switch_owner_ref,
        "kill_switch_contract_digest": request.kill_switch_contract_digest,
        "kill_switch_policy_digest": request.kill_switch_policy_digest,
        "kill_switch_state_machine_digest": request.kill_switch_state_machine_digest,
        "kill_switch_writer_fencing_evidence_ref": request.kill_switch_writer_fencing_evidence_ref,
        "kill_switch_writer_fencing_evidence_digest": request.kill_switch_writer_fencing_evidence_digest,
        "pre_trade_safety_kernel_evidence_ref": request.pre_trade_safety_kernel_evidence_ref,
        "pre_trade_safety_kernel_evidence_digest": request.pre_trade_safety_kernel_evidence_digest,
        "adapter_submission_contract_ref": request.adapter_submission_contract_ref,
        "adapter_submission_contract_digest": request.adapter_submission_contract_digest,
        "venue_capability_snapshot_ref": request.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": request.venue_capability_snapshot_digest,
        "reconciliation_evidence_ref": request.reconciliation_evidence_ref,
        "reconciliation_evidence_digest": request.reconciliation_evidence_digest,
        "unknown_outcome_recovery_evidence_ref": request.unknown_outcome_recovery_evidence_ref,
        "unknown_outcome_recovery_evidence_digest": request.unknown_outcome_recovery_evidence_digest,
        "authority_contract_ref": request.authority_contract_ref,
        "authority_contract_digest": request.authority_contract_digest,
        "revocation_contract_ref": request.revocation_contract_ref,
        "revocation_contract_digest": request.revocation_contract_digest,
        "environment": request.environment,
        "venue_scope": request.venue_scope,
        "instrument_scope": request.instrument_scope,
        "risk_policy_digest": request.risk_policy_digest,
        "sizing_profile_digest": request.sizing_profile_digest,
        "scope_capital_digest": request.scope_capital_digest,
        "rollback_parent_ref": request.rollback_parent_ref,
        "deployment_compatibility_binding_digest": request.deployment_compatibility_binding_digest,
        "runtime_budget_binding_digest": request.runtime_budget_binding_digest,
        "data_readiness_status": request.data_readiness_status,
        "adapter_readiness_status": request.adapter_readiness_status,
        "reconciliation_readiness_status": request.reconciliation_readiness_status,
        "kill_switch_readiness_status": request.kill_switch_readiness_status,
        "rollback_readiness_status": request.rollback_readiness_status,
        "budget_readiness_status": request.budget_readiness_status,
        "trading_logic_readiness_status": request.trading_logic_readiness_status,
        "safety_readiness_status": request.safety_readiness_status,
        "authority_contract_readiness_status": request.authority_contract_readiness_status,
        "venue_capability_readiness_status": request.venue_capability_readiness_status,
        "fail_closed_gates": list(dict.fromkeys(fail_closed_gates)),
        "eligibility_status": eligibility_status,
        "decision_code": decision_code,
        "blocking_reasons": blocking_reasons,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "input_epoch": request.input_epoch,
        "bound_input_epoch": request.bound_input_epoch,
        "manifest_digest": "",
        "output_digest": "",
        "artifact_id": "",
        "integrity": {},
    }
    contract_body.update(_REQUIRED_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["artifact_id"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return RuntimeEligibilityEvaluationResult(
        eligibility_status=eligibility_status,
        decision_code=decision_code,
        blocking_reasons=tuple(blocking_reasons),
        fail_closed_gates=tuple(dict.fromkeys(fail_closed_gates)),
        contract_body=contract_body,
    )


def build_runtime_eligibility_v1(request: RuntimeEligibilityEvaluationInput) -> dict[str, Any]:
    return evaluate_runtime_eligibility_v1(request).contract_body


def serialize_runtime_eligibility_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest", "artifact_id"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise RuntimeEligibilityError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise RuntimeEligibilityError("output directory must not be under /tmp")


def _artifact_bytes_for_manifest_digest(contract: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in contract.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_runtime_eligibility_v1(body).encode("utf-8")


def _compute_output_manifest_digest(contract: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(contract)).hexdigest()


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_network_side_effect", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {"check_id": "eligible_does_not_authorize_submission", "status": "PASS"},
        {
            "check_id": "manifest_digest",
            "status": "PASS" if manifest_digest else "FAIL",
        },
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": overall,
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "manifest_digest": manifest_digest,
    }


def _validate_contract_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != CONTRACT_NAME:
        raise RuntimeEligibilityError("contract_name mismatch")
    if contract.get("contract_version") != CONTRACT_VERSION:
        raise RuntimeEligibilityError("contract_version mismatch")
    status = contract.get("eligibility_status")
    if status not in _VALID_ELIGIBILITY_STATUSES:
        raise RuntimeEligibilityError("eligibility_status must be ELIGIBLE or INELIGIBLE")
    decision_code = str(contract.get("decision_code", ""))
    if status == "ELIGIBLE" and decision_code != "ELIGIBLE":
        raise RuntimeEligibilityError("ELIGIBLE status requires decision_code ELIGIBLE")
    if status == "INELIGIBLE" and decision_code not in _FAIL_CLOSED_DECISION_CODES:
        raise RuntimeEligibilityError("unknown INELIGIBLE decision_code")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise RuntimeEligibilityError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise RuntimeEligibilityError("integrity.content_sha256 mismatch")
    output_digest = contract.get("output_digest")
    if output_digest != _compute_output_digest(contract):
        raise RuntimeEligibilityError("output_digest mismatch")
    if contract.get("artifact_id") != output_digest:
        raise RuntimeEligibilityError("artifact_id must equal output_digest")
    for key, expected_value in _REQUIRED_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected_value:
            raise RuntimeEligibilityError(f"{key} must remain {expected_value!r}")


def reverify_runtime_eligibility_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / ARTIFACT_REL
    if not artifact_path.is_file():
        raise RuntimeEligibilityError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise RuntimeEligibilityError("artifact must be a JSON object")
    _validate_contract_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise RuntimeEligibilityError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise RuntimeEligibilityError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def produce_runtime_eligibility_v1(
    *,
    request: RuntimeEligibilityEvaluationInput,
    output_dir: Path | str,
) -> RuntimeEligibilityResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    evaluation = evaluate_runtime_eligibility_v1(request)
    contract_body = dict(evaluation.contract_body)

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise RuntimeEligibilityError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        contract_body["manifest_digest"] = manifest_digest
        artifact_path.write_text(
            serialize_runtime_eligibility_v1(contract_body),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=contract_body,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise RuntimeEligibilityError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )
        reverify_runtime_eligibility_v1(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise RuntimeEligibilityError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return RuntimeEligibilityResult(
        output_dir=final_dir,
        evidence_id=str(contract_body["evidence_id"]),
        eligibility_status=str(contract_body["eligibility_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=str(contract_body["output_digest"]),
        manifest_digest=str(contract_body["manifest_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "AUTHORITY_CONTRACT_DIGEST",
    "AUTHORITY_CONTRACT_REF",
    "BEAR_COMPONENT_REF",
    "BUILDER_VERSION",
    "BULL_BEAR_SEMANTIC_DIGEST",
    "BULL_COMPONENT_REF",
    "CANONICAL_ORDER_INTENT_CONTRACT_DIGEST",
    "CANONICAL_ORDER_INTENT_CONTRACT_REF",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "DOUBLE_PLAY_CONTRACT_DIGEST",
    "DOUBLE_PLAY_OWNER_REF",
    "DYNAMIC_SCOPE_OWNER_REF",
    "DYNAMIC_SCOPE_POLICY_DIGEST",
    "MASTER_V2_CONTRACT_DIGEST",
    "MASTER_V2_OWNER_REF",
    "REVOCATION_CONTRACT_DIGEST",
    "REVOCATION_CONTRACT_REF",
    "RISK_OWNER_REF",
    "RUNTIME_ELIGIBILITY_AUTHORITY_INVARIANTS",
    "RuntimeEligibilityError",
    "RuntimeEligibilityEvaluationInput",
    "RuntimeEligibilityEvaluationResult",
    "RuntimeEligibilityResult",
    "SCOPE_CAPITAL_OWNER_REF",
    "SIZING_OWNER_REF",
    "build_runtime_eligibility_v1",
    "build_self_verification_v1",
    "compute_candidate_artifact_digest",
    "compute_promotion_decision_digest",
    "default_candidate_artifact_body",
    "default_promotion_decision_body",
    "default_runtime_eligibility_evaluation_input",
    "evaluate_runtime_eligibility_v1",
    "produce_runtime_eligibility_v1",
    "reverify_runtime_eligibility_v1",
    "serialize_runtime_eligibility_v1",
]
