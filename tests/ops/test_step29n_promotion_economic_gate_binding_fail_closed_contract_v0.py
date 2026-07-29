"""STEP 29N fail-closed governance binding contract tests (post PR #4760)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop import promotion_economic_gate_v1 as gate

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
EVAL_TS = "2026-07-02T22:30:00Z"


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
        "economic_validity_offline_gate_pass": True,
        "integrated_economic_evidence_bundle_verified": True,
        "offline_economic_evidence_complete": True,
        "integrated_paper_shadow_evidence_complete": True,
    }
    base.update(overrides)
    return gate.PromotionEconomicGateInputV1(**base)


def _evaluate(**overrides: Any) -> gate.PromotionEconomicGateResultV1:
    return gate.evaluate_promotion_economic_gate_v1(
        policy=_policy(),
        input_data=_valid_input(**overrides),
        evaluation_timestamp=EVAL_TS,
    )


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


class TestSyntheticPassContract:
    def test_full_valid_input_promotion_eligible_true(self) -> None:
        result = _evaluate()
        assert result.promotion_eligible is True
        assert result.eligible_for_promotion_candidate is True
        assert result.economic_validity_pass is True
        assert result.robustness_pass is True
        assert result.evidence_admissible is True
        assert result.safety_policy_pass is True
        assert result.governance_hold_active is False
        assert result.authority_effect == gate.AUTHORITY_EFFECT_NONE
        assert result.runtime_effect == gate.RUNTIME_EFFECT_NONE


class TestFailClosedBlocks:
    def test_economic_validity_false_blocks(self) -> None:
        result = _evaluate(
            economic_validity_status=gate.FAIL_STATUS,
            economic_validity_proven=False,
            economic_validity_offline_gate_pass=False,
        )
        assert result.promotion_eligible is False
        assert gate.REASON_ECONOMIC_VALIDITY_NOT_PROVEN in result.reason_codes

    def test_economic_validity_unknown_blocks(self) -> None:
        result = _evaluate(economic_validity_status="MAYBE")
        assert result.promotion_eligible is False
        assert any(
            code.startswith(gate.REASON_REQUIRED_STATUS_UNKNOWN) for code in result.reason_codes
        )

    def test_walk_forward_fail_blocks(self) -> None:
        result = _evaluate(walk_forward_status=gate.FAIL_STATUS)
        assert result.promotion_eligible is False
        assert gate.REASON_WALK_FORWARD_FAILED in result.reason_codes

    def test_monte_carlo_fail_blocks(self) -> None:
        result = _evaluate(monte_carlo_status=gate.FAIL_STATUS)
        assert gate.REASON_MONTE_CARLO_FAILED in result.reason_codes

    def test_stress_fail_blocks(self) -> None:
        result = _evaluate(stress_status=gate.FAIL_STATUS)
        assert gate.REASON_STRESS_FAILED in result.reason_codes

    def test_parameter_robustness_fail_blocks(self) -> None:
        result = _evaluate(parameter_sensitivity_status=gate.FAIL_STATUS)
        assert gate.REASON_PARAMETER_SENSITIVITY_FAILED in result.reason_codes

    def test_evidence_inadmissible_blocks(self) -> None:
        result = _evaluate(
            evidence_admissible=False,
            evidence_admissibility_status=gate.FAIL_STATUS,
        )
        assert gate.REASON_ECONOMIC_EVIDENCE_INADMISSIBLE in result.reason_codes

    def test_missing_manifest_blocks(self) -> None:
        result = _evaluate(manifest_binding_status=gate.FAIL_STATUS)
        assert gate.REASON_MANIFEST_BINDING_FAILED in result.reason_codes

    def test_manifest_digest_mismatch_blocks(self) -> None:
        result = gate.evaluate_promotion_economic_gate_v1(
            policy=_policy(),
            input_data=_valid_input(),
            evaluation_timestamp=EVAL_TS,
            expected_evidence_manifest_digest="feedface" * 8,
        )
        assert gate.REASON_EVIDENCE_DIGEST_MISMATCH in result.reason_codes

    def test_safety_policy_fail_blocks(self) -> None:
        result = _evaluate(safety_policy_status=gate.FAIL_STATUS)
        assert gate.REASON_SAFETY_POLICY_FAILED in result.reason_codes

    def test_no_new_candidate_hold_blocks(self) -> None:
        result = _evaluate(no_new_candidate_hold_active=True)
        assert gate.REASON_NO_NEW_CANDIDATE_HOLD in result.reason_codes
        assert result.governance_hold_active is True

    def test_complete_no_pass_blocks(self) -> None:
        result = _evaluate(step29m_fleet_status=gate.STEP29M_FLEET_STATUS_COMPLETE_NO_PASS)
        assert gate.REASON_STEP29M_FLEET_COMPLETE_NO_PASS in result.reason_codes

    def test_terminal_disposition_blocks(self) -> None:
        result = _evaluate(candidate_terminal_disposition="REJECTED_CLOSED")
        assert gate.REASON_TERMINAL_CANDIDATE_DISPOSITION in result.reason_codes

    def test_confidence_score_only_blocks(self) -> None:
        result = _evaluate(promotion_basis_confidence_only=True)
        assert gate.REASON_CONFIDENCE_SCORE_ONLY in result.reason_codes

    def test_in_sample_profit_only_blocks(self) -> None:
        result = _evaluate(promotion_basis_in_sample_profit_only=True)
        assert gate.REASON_IN_SAMPLE_PROFIT_ONLY in result.reason_codes

    def test_zero_cost_evidence_blocks(self) -> None:
        result = _evaluate(zero_cost_evidence=True)
        assert gate.REASON_ZERO_COST_EVIDENCE in result.reason_codes

    def test_robustness_failure_blocks(self) -> None:
        result = _evaluate(robustness_status=gate.FAIL_STATUS, walk_forward_status=gate.FAIL_STATUS)
        assert gate.REASON_ROBUSTNESS_FAILED in result.reason_codes


class TestAuthorityAndRuntimeEffects:
    def test_authority_effect_none_on_pass(self) -> None:
        assert _evaluate().authority_effect == gate.AUTHORITY_EFFECT_NONE

    def test_runtime_effect_none_on_fail(self) -> None:
        result = gate.evaluate_post_pr4760_governance_bound_promotion_gate_v1(
            evaluation_timestamp=EVAL_TS,
        )
        assert result.runtime_effect == gate.RUNTIME_EFFECT_NONE
        assert result.shadow_candidate_eligible is False
        assert result.paper_candidate_eligible is False
        assert result.testnet_candidate_eligible is False


class TestDeterminism:
    def test_reason_codes_sorted(self) -> None:
        result = _evaluate(
            no_new_candidate_hold_active=True,
            economic_validity_status=gate.FAIL_STATUS,
            economic_validity_proven=False,
            economic_validity_offline_gate_pass=False,
        )
        assert list(result.reason_codes) == sorted(result.reason_codes)

    def test_serialization_roundtrip(self) -> None:
        result = _evaluate()
        payload = result.to_dict()
        encoded = json.dumps(payload, sort_keys=True)
        decoded = json.loads(encoded)
        assert decoded["promotion_eligible"] is True
        assert decoded["authority_effect"] == gate.AUTHORITY_EFFECT_NONE


class TestNegativeResearchCandidates:
    @staticmethod
    def _candidate_ids() -> set[str]:
        return {
            binding["candidate_id"]
            for binding in gate.canonical_negative_research_candidate_bindings_v0()
        }

    def test_negative_inventory_covers_required_candidates(self) -> None:
        required = {
            "macd_v1",
            "breakout_donchian_v1",
            "ma_crossover_v1",
            "rsi_reversion_v1",
            "breakout_donchian_v1_lookback_55",
            "composite_vol_gated_breakout_donchian_v1",
            "composite_breakout_confirmation_vol_gated_donchian_v1",
        }
        assert self._candidate_ids() == required

    def test_all_negative_candidates_not_promotion_eligible(self) -> None:
        for binding in gate.canonical_negative_research_candidate_bindings_v0():
            result = gate.evaluate_negative_research_candidate_promotion_gate_v1(
                binding,
                evaluation_timestamp=EVAL_TS,
            )
            assert result.promotion_eligible is False
            assert result.authority_effect == gate.AUTHORITY_EFFECT_NONE

    def test_composite_confirmation_rejected_closed(self) -> None:
        bindings = gate.canonical_negative_research_candidate_bindings_v0()
        composite = next(
            b
            for b in bindings
            if b["candidate_id"] == "composite_breakout_confirmation_vol_gated_donchian_v1"
        )
        result = gate.evaluate_negative_research_candidate_promotion_gate_v1(
            composite,
            evaluation_timestamp=EVAL_TS,
        )
        assert result.candidate_terminal_disposition == "REJECTED_CLOSED"
        assert gate.REASON_TERMINAL_CANDIDATE_DISPOSITION in result.reason_codes


class TestPostPr4760CurrentState:
    def test_repo_current_state_fail_closed(self) -> None:
        result = gate.evaluate_post_pr4760_governance_bound_promotion_gate_v1(
            evaluation_timestamp=EVAL_TS,
        )
        assert result.promotion_eligible is False
        assert result.economic_validity_pass is False
        assert result.governance_hold_active is True
        assert gate.REASON_NO_NEW_CANDIDATE_HOLD in result.reason_codes
        assert gate.REASON_STEP29M_FLEET_COMPLETE_NO_PASS in result.reason_codes


class TestFuturesOnlyPolicy:
    def test_non_futures_blocked(self) -> None:
        result = _evaluate(futures_only=False)
        assert gate.REASON_NON_FUTURES_CANDIDATE in result.reason_codes

    def test_bitcoin_direction_forbidden(self) -> None:
        result = _evaluate(bitcoin_direction_allowed=True)
        assert gate.REASON_BITCOIN_DIRECTION_FORBIDDEN in result.reason_codes


class TestProgressRegistryBinding:
    def test_operator_policy_maintain_hold_historical_step29m_snapshot(self) -> None:
        text = PROGRESS_REGISTRY.read_text(encoding="utf-8")
        # Historical STEP29M snapshot remains present; registry is prepend-ordered so
        # first-match helpers are not authoritative for historical rows.
        assert "| `STEP29M_OPERATOR_POLICY_DECISION` | `NO_NEW_CANDIDATE_HOLD` |" in text
        assert "| `STEP29M_FLEET_STATUS` | `COMPLETE_NO_PASS` |" in text

    def test_step29n_fail_closed_binding_fields(self) -> None:
        text = PROGRESS_REGISTRY.read_text(encoding="utf-8")
        assert _field_value(text, "STEP29N_GOVERNANCE_FAIL_CLOSED_BINDING") == "true"
        assert (
            _field_value(text, "STEP29N_OPERATOR_POLICY_DECISION")
            == gate.OPERATOR_POLICY_MAINTAIN_NO_NEW_CANDIDATE_HOLD
        )
        assert _field_value(text, "STEP29N_PROMOTION_GATE_STATUS") == "FAIL_CLOSED_BLOCKED"
