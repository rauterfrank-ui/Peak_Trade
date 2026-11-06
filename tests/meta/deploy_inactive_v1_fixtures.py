"""Fixtures for deploy_inactive_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.deploy_inactive_v1 import (
    DeployedInactiveVerificationInput,
    DeploymentCandidateEvaluationInput,
    OfflineDeclarativeProjection,
    build_deployment_candidate_v1,
    default_deployed_inactive_verification_input,
    default_deployment_candidate_evaluation_input,
    default_offline_declarative_projection,
    produce_deployment_candidate_v1,
    produce_deployed_inactive_verification_v1,
)


@dataclass(frozen=True)
class DeployInactiveFixtureBundle:
    candidate_request: DeploymentCandidateEvaluationInput
    verification_request: DeployedInactiveVerificationInput


def build_valid_deployment_candidate_input(
    **overrides: object,
) -> DeploymentCandidateEvaluationInput:
    base = default_deployment_candidate_evaluation_input()
    if not overrides:
        return base

    data = {
        "contract_version": base.contract_version,
        "created_at": base.created_at,
        "builder_version": base.builder_version,
        "policy_version": base.policy_version,
        "deployment_candidate_id": base.deployment_candidate_id,
        "runtime_eligibility_ref": base.runtime_eligibility_ref,
        "runtime_eligibility_digest": base.runtime_eligibility_digest,
        "runtime_eligibility_status": base.runtime_eligibility_status,
        "runtime_eligibility_body": dict(base.runtime_eligibility_body),
        "runtime_eligibility_input": base.runtime_eligibility_input,
        "candidate_artifact_ref": base.candidate_artifact_ref,
        "candidate_artifact_body": dict(base.candidate_artifact_body),
        "candidate_artifact_digest": base.candidate_artifact_digest,
        "candidate_artifact_version": base.candidate_artifact_version,
        "strategy_id": base.strategy_id,
        "strategy_version": base.strategy_version,
        "model_version": base.model_version,
        "parameter_set_digest": base.parameter_set_digest,
        "feature_set_digest": base.feature_set_digest,
        "market_type": base.market_type,
        "promotion_decision_ref": base.promotion_decision_ref,
        "promotion_decision_body": dict(base.promotion_decision_body),
        "promotion_decision_digest": base.promotion_decision_digest,
        "promotion_status": base.promotion_status,
        "promotion_decision_outcome": base.promotion_decision_outcome,
        "trading_logic_compatibility_ref": base.trading_logic_compatibility_ref,
        "trading_logic_compatibility_digest": base.trading_logic_compatibility_digest,
        "trading_logic_compatibility_status": base.trading_logic_compatibility_status,
        "trading_logic_bypass_detected": base.trading_logic_bypass_detected,
        "parallel_trading_logic_ssot_detected": base.parallel_trading_logic_ssot_detected,
        "pre_trade_safety_ref": base.pre_trade_safety_ref,
        "pre_trade_safety_digest": base.pre_trade_safety_digest,
        "kill_switch_contract_ref": base.kill_switch_contract_ref,
        "kill_switch_contract_digest": base.kill_switch_contract_digest,
        "kill_switch_writer_fencing_ref": base.kill_switch_writer_fencing_ref,
        "kill_switch_writer_fencing_digest": base.kill_switch_writer_fencing_digest,
        "reconciliation_readiness_ref": base.reconciliation_readiness_ref,
        "reconciliation_readiness_digest": base.reconciliation_readiness_digest,
        "unknown_outcome_recovery_ref": base.unknown_outcome_recovery_ref,
        "unknown_outcome_recovery_digest": base.unknown_outcome_recovery_digest,
        "adapter_submission_contract_ref": base.adapter_submission_contract_ref,
        "adapter_submission_contract_digest": base.adapter_submission_contract_digest,
        "environment": base.environment,
        "venue_scope": base.venue_scope,
        "instrument_scope": base.instrument_scope,
        "venue_capability_snapshot_ref": base.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": base.venue_capability_snapshot_digest,
        "venue_capability_stale": base.venue_capability_stale,
        "venue_capability_venue_scope": base.venue_capability_venue_scope,
        "risk_policy_digest": base.risk_policy_digest,
        "sizing_profile_digest": base.sizing_profile_digest,
        "scope_capital_digest": base.scope_capital_digest,
        "package_ref": base.package_ref,
        "package_digest": base.package_digest,
        "deployment_layout_ref": base.deployment_layout_ref,
        "deployment_layout_digest": base.deployment_layout_digest,
        "deployment_policy_digest": base.deployment_policy_digest,
        "expected_loader_contract": base.expected_loader_contract,
        "expected_loader_contract_digest": base.expected_loader_contract_digest,
        "expected_runtime_contract": base.expected_runtime_contract,
        "expected_runtime_contract_digest": base.expected_runtime_contract_digest,
        "expected_configuration_digest": base.expected_configuration_digest,
        "rollback_parent_ref": base.rollback_parent_ref,
        "rollback_parent_digest": base.rollback_parent_digest,
        "rollback_artifact_ref": base.rollback_artifact_ref,
        "rollback_artifact_digest": base.rollback_artifact_digest,
        "rollback_readiness_status": base.rollback_readiness_status,
        "data_readiness_status": base.data_readiness_status,
        "budget_readiness_status": base.budget_readiness_status,
        "artifact_integrity_status": base.artifact_integrity_status,
        "loader_compatibility_status": base.loader_compatibility_status,
        "runtime_contract_compatibility_status": base.runtime_contract_compatibility_status,
        "deployment_layout_status": base.deployment_layout_status,
        "input_epoch": base.input_epoch,
        "bound_input_epoch": base.bound_input_epoch,
        "input_refs": base.input_refs,
        "input_digests": base.input_digests,
        "real_deployment_requested": base.real_deployment_requested,
        "file_transfer_requested": base.file_transfer_requested,
        "runtime_installation_requested": base.runtime_installation_requested,
        "runtime_registration_requested": base.runtime_registration_requested,
        "activation_requested": base.activation_requested,
        "authority_creation_requested": base.authority_creation_requested,
        "scheduler_enable_requested": base.scheduler_enable_requested,
        "execution_permission_requested": base.execution_permission_requested,
        "adapter_invocation_requested": base.adapter_invocation_requested,
        "order_submission_requested": base.order_submission_requested,
        "network_side_effect_requested": base.network_side_effect_requested,
    }
    data.update(overrides)
    return DeploymentCandidateEvaluationInput(**data)


def build_valid_verification_input(
    candidate: dict | None = None,
    **overrides: object,
) -> DeployedInactiveVerificationInput:
    candidate_contract = dict(
        candidate or build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    )
    base = default_deployed_inactive_verification_input(candidate_contract)
    if not overrides:
        return base

    data = {
        "contract_version": base.contract_version,
        "created_at": base.created_at,
        "builder_version": base.builder_version,
        "policy_version": base.policy_version,
        "verification_id": base.verification_id,
        "deployment_candidate_ref": base.deployment_candidate_ref,
        "deployment_candidate_digest": base.deployment_candidate_digest,
        "deployment_candidate_status": base.deployment_candidate_status,
        "deployment_candidate_body": dict(base.deployment_candidate_body),
        "projection": base.projection,
        "input_refs": base.input_refs,
        "input_digests": base.input_digests,
        "real_runtime_observation_requested": base.real_runtime_observation_requested,
    }
    data.update(overrides)
    return DeployedInactiveVerificationInput(**data)


def minimal_invalid_digest() -> str:
    return compute_content_sha256({"invalid": True})


def produce_deployment_candidate_fixture(
    tmp_path: Path, name: str = "deployment_candidate_out"
) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    out = root / name
    produce_deployment_candidate_v1(
        request=default_deployment_candidate_evaluation_input(),
        output_dir=out,
    )
    return out


def produce_verification_fixture(tmp_path: Path, name: str = "verification_out") -> Path:
    candidate = build_deployment_candidate_v1(default_deployment_candidate_evaluation_input())
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    out = root / name
    produce_deployed_inactive_verification_v1(
        request=default_deployed_inactive_verification_input(candidate),
        output_dir=out,
    )
    return out


def matching_projection(candidate: dict) -> OfflineDeclarativeProjection:
    return default_offline_declarative_projection(candidate)
