"""Fixtures for runtime_eligibility_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.runtime_eligibility_v1 import (
    BULL_BEAR_SEMANTIC_DIGEST,
    BULL_COMPONENT_REF,
    BEAR_COMPONENT_REF,
    CANONICAL_ORDER_INTENT_CONTRACT_DIGEST,
    CANONICAL_ORDER_INTENT_CONTRACT_REF,
    DOUBLE_PLAY_CONTRACT_DIGEST,
    DOUBLE_PLAY_OWNER_REF,
    DYNAMIC_SCOPE_OWNER_REF,
    DYNAMIC_SCOPE_POLICY_DIGEST,
    MASTER_V2_CONTRACT_DIGEST,
    MASTER_V2_OWNER_REF,
    RISK_OWNER_REF,
    SCOPE_CAPITAL_OWNER_REF,
    SIZING_OWNER_REF,
    RuntimeEligibilityEvaluationInput,
    compute_candidate_artifact_digest,
    compute_promotion_decision_digest,
    default_candidate_artifact_body,
    default_promotion_decision_body,
    default_runtime_eligibility_evaluation_input,
    produce_runtime_eligibility_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


@dataclass(frozen=True)
class RuntimeEligibilityFixtureBundle:
    request: RuntimeEligibilityEvaluationInput
    bundle_dir: Path | None = None


def build_valid_runtime_eligibility_input(
    **overrides: object,
) -> RuntimeEligibilityEvaluationInput:
    base = default_runtime_eligibility_evaluation_input()
    if not overrides:
        return base

    data = {
        "contract_version": base.contract_version,
        "created_at": base.created_at,
        "builder_version": base.builder_version,
        "policy_version": base.policy_version,
        "candidate_id": base.candidate_id,
        "candidate_artifact_ref": base.candidate_artifact_ref,
        "candidate_artifact_body": dict(base.candidate_artifact_body),
        "candidate_artifact_digest": base.candidate_artifact_digest,
        "candidate_version": base.candidate_version,
        "market_type": base.market_type,
        "promotion_decision_ref": base.promotion_decision_ref,
        "promotion_decision_body": dict(base.promotion_decision_body),
        "promotion_decision_digest": base.promotion_decision_digest,
        "promotion_status": base.promotion_status,
        "promotion_decision_outcome": base.promotion_decision_outcome,
        "promotion_authorized_by_canonical_owner": base.promotion_authorized_by_canonical_owner,
        "completion_evidence_ref": base.completion_evidence_ref,
        "completion_evidence_digest": base.completion_evidence_digest,
        "research_validity_ref": base.research_validity_ref,
        "research_validity_digest": base.research_validity_digest,
        "research_validity_status": base.research_validity_status,
        "trading_logic_compatibility_ref": base.trading_logic_compatibility_ref,
        "trading_logic_compatibility_digest": base.trading_logic_compatibility_digest,
        "trading_logic_compatibility_status": base.trading_logic_compatibility_status,
        "trading_logic_bypass_detected": base.trading_logic_bypass_detected,
        "parallel_trading_logic_ssot_detected": base.parallel_trading_logic_ssot_detected,
        "master_v2_owner_ref": base.master_v2_owner_ref,
        "master_v2_contract_digest": base.master_v2_contract_digest,
        "double_play_owner_ref": base.double_play_owner_ref,
        "double_play_contract_digest": base.double_play_contract_digest,
        "bull_component_ref": base.bull_component_ref,
        "bear_component_ref": base.bear_component_ref,
        "bull_bear_semantic_digest": base.bull_bear_semantic_digest,
        "dynamic_scope_owner_ref": base.dynamic_scope_owner_ref,
        "dynamic_scope_policy_digest": base.dynamic_scope_policy_digest,
        "risk_owner_ref": base.risk_owner_ref,
        "sizing_owner_ref": base.sizing_owner_ref,
        "scope_capital_owner_ref": base.scope_capital_owner_ref,
        "canonical_order_intent_contract_ref": base.canonical_order_intent_contract_ref,
        "canonical_order_intent_contract_digest": base.canonical_order_intent_contract_digest,
        "kill_switch_owner_ref": base.kill_switch_owner_ref,
        "kill_switch_contract_digest": base.kill_switch_contract_digest,
        "kill_switch_policy_digest": base.kill_switch_policy_digest,
        "kill_switch_state_machine_digest": base.kill_switch_state_machine_digest,
        "kill_switch_writer_fencing_evidence_ref": base.kill_switch_writer_fencing_evidence_ref,
        "kill_switch_writer_fencing_evidence_digest": base.kill_switch_writer_fencing_evidence_digest,
        "kill_switch_writer_fencing_decision": base.kill_switch_writer_fencing_decision,
        "kill_switch_independent_read_paths_proven": base.kill_switch_independent_read_paths_proven,
        "pre_trade_safety_kernel_evidence_ref": base.pre_trade_safety_kernel_evidence_ref,
        "pre_trade_safety_kernel_evidence_digest": base.pre_trade_safety_kernel_evidence_digest,
        "pre_trade_safety_kernel_status": base.pre_trade_safety_kernel_status,
        "pre_trade_safety_fail_closed": base.pre_trade_safety_fail_closed,
        "adapter_submission_contract_ref": base.adapter_submission_contract_ref,
        "adapter_submission_contract_digest": base.adapter_submission_contract_digest,
        "adapter_submission_contract_status": base.adapter_submission_contract_status,
        "adapter_semantic_mutation_allowed": base.adapter_semantic_mutation_allowed,
        "venue_capability_snapshot_ref": base.venue_capability_snapshot_ref,
        "venue_capability_snapshot_digest": base.venue_capability_snapshot_digest,
        "venue_capability_snapshot_status": base.venue_capability_snapshot_status,
        "venue_capability_stale": base.venue_capability_stale,
        "venue_capability_venue_scope": base.venue_capability_venue_scope,
        "reconciliation_evidence_ref": base.reconciliation_evidence_ref,
        "reconciliation_evidence_digest": base.reconciliation_evidence_digest,
        "reconciliation_contract_status": base.reconciliation_contract_status,
        "unknown_outcome_recovery_evidence_ref": base.unknown_outcome_recovery_evidence_ref,
        "unknown_outcome_recovery_evidence_digest": base.unknown_outcome_recovery_evidence_digest,
        "unknown_outcome_recovery_contract_status": base.unknown_outcome_recovery_contract_status,
        "unknown_outcome_recovery_fail_closed": base.unknown_outcome_recovery_fail_closed,
        "authority_contract_ref": base.authority_contract_ref,
        "authority_contract_digest": base.authority_contract_digest,
        "revocation_contract_ref": base.revocation_contract_ref,
        "revocation_contract_digest": base.revocation_contract_digest,
        "environment": base.environment,
        "venue_scope": base.venue_scope,
        "instrument_scope": base.instrument_scope,
        "risk_policy_digest": base.risk_policy_digest,
        "sizing_profile_digest": base.sizing_profile_digest,
        "scope_capital_digest": base.scope_capital_digest,
        "rollback_parent_ref": base.rollback_parent_ref,
        "rollback_capability_proven": base.rollback_capability_proven,
        "deployment_compatibility_binding_digest": base.deployment_compatibility_binding_digest,
        "runtime_budget_binding_digest": base.runtime_budget_binding_digest,
        "input_epoch": base.input_epoch,
        "bound_input_epoch": base.bound_input_epoch,
        "data_readiness_status": base.data_readiness_status,
        "adapter_readiness_status": base.adapter_readiness_status,
        "reconciliation_readiness_status": base.reconciliation_readiness_status,
        "kill_switch_readiness_status": base.kill_switch_readiness_status,
        "rollback_readiness_status": base.rollback_readiness_status,
        "budget_readiness_status": base.budget_readiness_status,
        "trading_logic_readiness_status": base.trading_logic_readiness_status,
        "safety_readiness_status": base.safety_readiness_status,
        "authority_contract_readiness_status": base.authority_contract_readiness_status,
        "venue_capability_readiness_status": base.venue_capability_readiness_status,
        "input_refs": base.input_refs,
        "input_digests": base.input_digests,
    }
    data.update(overrides)

    if "candidate_artifact_body" in overrides and "candidate_artifact_digest" not in overrides:
        body = dict(data["candidate_artifact_body"])
        data["candidate_artifact_body"] = body
        data["candidate_artifact_digest"] = compute_candidate_artifact_digest(body)
    if "promotion_decision_body" in overrides and "promotion_decision_digest" not in overrides:
        body = dict(data["promotion_decision_body"])
        data["promotion_decision_body"] = body
        data["promotion_decision_digest"] = compute_promotion_decision_digest(body)

    return RuntimeEligibilityEvaluationInput(**data)


def produce_runtime_eligibility_fixture(
    tmp_path: Path, name: str = "runtime_eligibility_out"
) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    out = root / name
    produce_runtime_eligibility_v1(
        request=default_runtime_eligibility_evaluation_input(),
        output_dir=out,
    )
    return out


def trading_logic_owner_refs() -> dict[str, str]:
    return {
        "master_v2_owner_ref": MASTER_V2_OWNER_REF,
        "master_v2_contract_digest": MASTER_V2_CONTRACT_DIGEST,
        "double_play_owner_ref": DOUBLE_PLAY_OWNER_REF,
        "double_play_contract_digest": DOUBLE_PLAY_CONTRACT_DIGEST,
        "bull_component_ref": BULL_COMPONENT_REF,
        "bear_component_ref": BEAR_COMPONENT_REF,
        "bull_bear_semantic_digest": BULL_BEAR_SEMANTIC_DIGEST,
        "dynamic_scope_owner_ref": DYNAMIC_SCOPE_OWNER_REF,
        "dynamic_scope_policy_digest": DYNAMIC_SCOPE_POLICY_DIGEST,
        "risk_owner_ref": RISK_OWNER_REF,
        "sizing_owner_ref": SIZING_OWNER_REF,
        "scope_capital_owner_ref": SCOPE_CAPITAL_OWNER_REF,
        "canonical_order_intent_contract_ref": CANONICAL_ORDER_INTENT_CONTRACT_REF,
        "canonical_order_intent_contract_digest": CANONICAL_ORDER_INTENT_CONTRACT_DIGEST,
    }


def minimal_invalid_digest() -> str:
    return compute_content_sha256({"invalid": True})
