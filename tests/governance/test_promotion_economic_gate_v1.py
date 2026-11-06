"""RUNBOOK STEP 29N — promotion economic gate binding v1 tests."""

from __future__ import annotations

from typing import Any

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate

EVAL_TS = "2026-07-01T12:00:00Z"


def _policy() -> gate.PromotionEconomicGatePolicyV1:
    return gate.canonical_promotion_economic_gate_policy_v1()


def _economic_policy_digest() -> str:
    return canonical_economic_validity_policy_v1().policy_digest()


def _valid_input(**overrides: Any) -> gate.PromotionEconomicGateInputV1:
    base = {
        "strategy_id": "mv2_offline_research",
        "strategy_version": "v1",
        "candidate_id": "candidate-001",
        "economic_viability_evidence_ref": "evidence://admissible/futures/v1/bundle-001",
        "economic_validity_status": gate.PASS_STATUS,
        "economic_validity_proven": True,
        "profitability_claim_allowed": True,
        "robustness_status": gate.PASS_STATUS,
        "data_admissibility_status": gate.PASS_STATUS,
        "evidence_admissibility_status": gate.PASS_STATUS,
        "policy_threshold_status": gate.PASS_STATUS,
        "walk_forward_status": gate.PASS_STATUS,
        "out_of_sample_status": gate.PASS_STATUS,
        "monte_carlo_status": gate.PASS_STATUS,
        "stress_status": gate.PASS_STATUS,
        "parameter_sensitivity_status": gate.PASS_STATUS,
        "reproducibility_status": gate.PASS_STATUS,
        "digest_binding_status": gate.PASS_STATUS,
        "manifest_binding_status": gate.PASS_STATUS,
        "safety_policy_status": gate.PASS_STATUS,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "config_digest": "a" * 64,
        "implementation_digest": "b" * 64,
        "policy_digest": _economic_policy_digest(),
        "evidence_manifest_digest": "c" * 64,
        "dataset_digest": "d" * 64,
        "robustness_result_digests": ("wf:" + "e" * 61,),
        "safety_policy_digest": "f" * 64,
        "evidence_admissible": True,
    }
    base.update(overrides)
    return gate.PromotionEconomicGateInputV1(**base)


def _evaluate(**overrides: Any) -> gate.PromotionEconomicGateResultV1:
    return gate.evaluate_promotion_economic_gate_v1(
        policy=_policy(),
        input_data=_valid_input(**overrides),
        evaluation_timestamp=EVAL_TS,
    )


class TestPromotionGatePolicyContract:
    def test_policy_version_bound(self) -> None:
        policy = _policy()
        assert policy.is_version_bound() is True
        assert policy.policy_id == gate.PROMOTION_ECONOMIC_GATE_POLICY_ID

    def test_policy_digest_deterministic(self) -> None:
        assert _policy().policy_digest() == _policy().policy_digest()

    def test_no_authority_effects(self) -> None:
        policy = _policy()
        assert policy.authority_effect == gate.AUTHORITY_EFFECT_NONE
        assert policy.runtime_effect == gate.RUNTIME_EFFECT_NONE
        assert policy.deployment_effect == gate.DEPLOYMENT_EFFECT_NONE
        assert policy.activation_effect == gate.ACTIVATION_EFFECT_NONE


class TestPromotionGateEvaluation:
    def test_all_hard_gates_pass_eligible(self) -> None:
        result = _evaluate()
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.ELIGIBLE
        assert result.eligible_for_promotion_candidate is True
        assert result.reason_codes == ()
        assert result.authority_effect == gate.AUTHORITY_EFFECT_NONE
        assert result.runtime_effect == gate.RUNTIME_EFFECT_NONE

    def test_economic_validity_false_ineligible(self) -> None:
        result = _evaluate(
            economic_validity_status=gate.FAIL_STATUS,
            economic_validity_proven=False,
        )
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_ECONOMIC_VALIDITY_NOT_PROVEN in result.reason_codes

    def test_economic_validity_missing_blocked(self) -> None:
        result = _evaluate(economic_validity_status="")
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert any(
            code.startswith(gate.REASON_REQUIRED_INPUT_MISSING) for code in result.reason_codes
        )

    def test_profitability_claim_false_ineligible(self) -> None:
        result = _evaluate(profitability_claim_allowed=False)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_PROFITABILITY_CLAIM_NOT_ALLOWED in result.reason_codes

    def test_economic_evidence_missing_blocked(self) -> None:
        result = _evaluate(economic_viability_evidence_ref="")
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert gate.REASON_ECONOMIC_EVIDENCE_MISSING in result.reason_codes

    def test_economic_evidence_inadmissible_ineligible(self) -> None:
        result = _evaluate(
            evidence_admissible=False,
            evidence_admissibility_status=gate.FAIL_STATUS,
        )
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_ECONOMIC_EVIDENCE_INADMISSIBLE in result.reason_codes

    def test_data_admissibility_fail_ineligible(self) -> None:
        result = _evaluate(data_admissibility_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_DATA_ADMISSIBILITY_FAILED in result.reason_codes

    def test_policy_threshold_fail_ineligible(self) -> None:
        result = _evaluate(policy_threshold_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_POLICY_THRESHOLD_FAILED in result.reason_codes

    def test_walk_forward_fail_ineligible(self) -> None:
        result = _evaluate(walk_forward_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_WALK_FORWARD_FAILED in result.reason_codes

    def test_oos_fail_ineligible(self) -> None:
        result = _evaluate(out_of_sample_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_OUT_OF_SAMPLE_FAILED in result.reason_codes

    def test_monte_carlo_fail_ineligible(self) -> None:
        result = _evaluate(monte_carlo_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_MONTE_CARLO_FAILED in result.reason_codes

    def test_stress_fail_ineligible(self) -> None:
        result = _evaluate(stress_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_STRESS_FAILED in result.reason_codes

    def test_parameter_sensitivity_fail_ineligible(self) -> None:
        result = _evaluate(parameter_sensitivity_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_PARAMETER_SENSITIVITY_FAILED in result.reason_codes

    def test_reproducibility_fail_ineligible(self) -> None:
        result = _evaluate(reproducibility_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_REPRODUCIBILITY_FAILED in result.reason_codes

    def test_digest_binding_fail_blocked(self) -> None:
        result = _evaluate(digest_binding_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert gate.REASON_DIGEST_BINDING_FAILED in result.reason_codes

    def test_manifest_binding_fail_blocked(self) -> None:
        result = _evaluate(manifest_binding_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert gate.REASON_MANIFEST_BINDING_FAILED in result.reason_codes

    def test_safety_policy_fail_ineligible(self) -> None:
        result = _evaluate(safety_policy_status=gate.FAIL_STATUS)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_SAFETY_POLICY_FAILED in result.reason_codes

    def test_non_futures_candidate_ineligible(self) -> None:
        result = _evaluate(futures_only=False)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_NON_FUTURES_CANDIDATE in result.reason_codes

    def test_bitcoin_direction_forbidden_ineligible(self) -> None:
        result = _evaluate(bitcoin_direction_allowed=True)
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.INELIGIBLE
        assert gate.REASON_BITCOIN_DIRECTION_FORBIDDEN in result.reason_codes

    def test_missing_required_input_blocked(self) -> None:
        result = _evaluate(candidate_id="")
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert any(
            code.startswith(gate.REASON_REQUIRED_INPUT_MISSING) for code in result.reason_codes
        )

    def test_non_finite_metric_blocked(self) -> None:
        result = _evaluate(required_metrics={"net_expectancy": float("nan")})
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert any(code.startswith(gate.REASON_NON_FINITE_METRIC) for code in result.reason_codes)

    def test_policy_digest_mismatch_blocked(self) -> None:
        result = gate.evaluate_promotion_economic_gate_v1(
            policy=_policy(),
            input_data=_valid_input(),
            evaluation_timestamp=EVAL_TS,
            expected_policy_digest="deadbeef" * 8,
        )
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert gate.REASON_POLICY_DIGEST_MISMATCH in result.reason_codes

    def test_evidence_digest_mismatch_blocked(self) -> None:
        result = gate.evaluate_promotion_economic_gate_v1(
            policy=_policy(),
            input_data=_valid_input(),
            evaluation_timestamp=EVAL_TS,
            expected_evidence_manifest_digest="feedface" * 8,
        )
        assert result.promotion_candidate_status is gate.PromotionCandidateStatus.BLOCKED
        assert gate.REASON_EVIDENCE_DIGEST_MISMATCH in result.reason_codes

    def test_hard_fail_not_compensated_by_other_passes(self) -> None:
        result = _evaluate(
            economic_validity_status=gate.FAIL_STATUS,
            economic_validity_proven=False,
            walk_forward_status=gate.PASS_STATUS,
            out_of_sample_status=gate.PASS_STATUS,
            monte_carlo_status=gate.PASS_STATUS,
        )
        assert result.eligible_for_promotion_candidate is False
        assert gate.REASON_ECONOMIC_VALIDITY_NOT_PROVEN in result.reason_codes

    def test_input_order_does_not_change_result(self) -> None:
        kwargs_a = {
            "strategy_id": "mv2_offline_research",
            "candidate_id": "candidate-001",
            "strategy_version": "v1",
        }
        kwargs_b = {
            "candidate_id": "candidate-001",
            "strategy_version": "v1",
            "strategy_id": "mv2_offline_research",
        }
        result_a = _evaluate(**kwargs_a)
        result_b = _evaluate(**kwargs_b)
        assert result_a.evaluation_digest == result_b.evaluation_digest
        assert result_a.promotion_candidate_status == result_b.promotion_candidate_status

    def test_identical_inputs_identical_evaluation_digest(self) -> None:
        first = _evaluate()
        second = _evaluate()
        assert first.evaluation_digest == second.evaluation_digest

    def test_input_mutation_changes_evaluation_digest(self) -> None:
        first = _evaluate()
        second = _evaluate(strategy_version="v2")
        assert first.evaluation_digest != second.evaluation_digest

    def test_eligible_does_not_imply_deployment(self) -> None:
        result = _evaluate()
        assert result.eligible_for_promotion_candidate is True
        assert result.deployment_eligible is False
        assert result.deployment_effect == gate.DEPLOYMENT_EFFECT_NONE

    def test_eligible_does_not_imply_runtime(self) -> None:
        result = _evaluate()
        assert result.runtime_eligible is False
        assert result.runtime_effect == gate.RUNTIME_EFFECT_NONE

    def test_eligible_does_not_imply_activation(self) -> None:
        result = _evaluate()
        assert result.activation_allowed is False
        assert result.activation_effect == gate.ACTIVATION_EFFECT_NONE

    def test_eligible_does_not_imply_execution(self) -> None:
        result = _evaluate()
        assert result.execution_allowed is False

    def test_current_repo_state_fail_closed(self) -> None:
        result = gate.evaluate_current_repo_promotion_gate_v1(evaluation_timestamp=EVAL_TS)
        assert result.eligible_for_promotion_candidate is False
        assert result.promotion_candidate_status is not gate.PromotionCandidateStatus.ELIGIBLE
        assert gate.REASON_ECONOMIC_VALIDITY_NOT_PROVEN in result.reason_codes
        assert gate.REASON_PROFITABILITY_CLAIM_NOT_ALLOWED in result.reason_codes

    def test_futures_only_preserved(self) -> None:
        policy = _policy()
        result = _evaluate()
        assert policy.futures_only is True
        assert result.eligible_for_promotion_candidate is True

    def test_bitcoin_direction_forbidden_preserved(self) -> None:
        policy = _policy()
        assert policy.bitcoin_direction_allowed is False
        result = gate.evaluate_current_repo_promotion_gate_v1(evaluation_timestamp=EVAL_TS)
        assert result.eligible_for_promotion_candidate is False


class TestPromotionGateRegistryBoundaries:
    def test_runtime_authority_request_forbidden(self) -> None:
        result = _evaluate(request_runtime_authority=True)
        assert gate.REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN in result.reason_codes

    def test_deployment_activation_request_forbidden(self) -> None:
        result = _evaluate(request_deployment_activation=True)
        assert gate.REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN in result.reason_codes

    def test_schema_contract(self) -> None:
        schema = gate.promotion_economic_gate_schema_v1()
        assert schema["policy_version"] == gate.PROMOTION_ECONOMIC_GATE_POLICY_VERSION
        assert gate.REASON_ECONOMIC_VALIDITY_NOT_PROVEN in schema["reason_codes"]
