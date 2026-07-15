"""Contract tests for cross_sectional_futures_pairwise_lead_lag_spillover v1 score-and-ranking."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION as LEAD_LAG_V0_SCORE_FORMULA,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    CONFIG_REL_PATH,
    CONFIRM_GO,
    GOVERNANCE_REL_PATH,
    INSTRUMENT_DETERMINISTIC_TIE_BREAK,
    INSTRUMENT_RANKING_FORMULA,
    PAIR_DETERMINISTIC_TIE_BREAK,
    PAIR_RANKING_FORMULA,
    PENDING_SELECTION_POLICY_STATUS,
    RATIFIED_HYPOTHESIS_BINDING_DIGEST,
    RESEARCH_SCOPE,
    SCORE_FAMILY_POLICY,
    ContractMaterializationVerdict,
    ContractValidationVerdict,
    materialize_and_validate_score_and_ranking_contract_v0,
    materialize_score_and_ranking_contract_v0,
    materializer_to_binder_roundtrip_v0,
    validate_contract_rejections_v0,
    validate_lead_lag_v0_score_family_not_reused_v0,
    validate_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0 import (
    DEFAULT_FORWARD_LAG_BARS,
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
    compute_directed_pair_spillover_score_v0,
    compute_instrument_net_spillover_scores_v0,
    compute_panel_pairwise_spillover_scores_v0,
    rank_instrument_net_spillover_scores_deterministic_v0,
    rank_pair_scores_deterministic_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


@pytest.fixture
def complete_contract() -> dict:
    return materialize_score_and_ranking_contract_v0()


class TestContractMaterialization:
    def test_materialization_complete(self) -> None:
        result = materialize_and_validate_score_and_ranking_contract_v0()
        assert result.verdict == ContractMaterializationVerdict.COMPLETE
        assert result.validation_verdict == ContractValidationVerdict.ACCEPTED_COMPLETE
        assert result.fail_reasons == ()

    def test_deterministic_double_materialization(self) -> None:
        first = materialize_score_and_ranking_contract_v0()
        second = materialize_score_and_ranking_contract_v0()
        assert first == second

    def test_materializer_to_binder_roundtrip_pass(self) -> None:
        envelope = materialize_score_and_ranking_contract_v0()
        roundtrip = materializer_to_binder_roundtrip_v0(envelope)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


class TestHypothesisBindingReference:
    def test_hypothesis_binding_digest_unchanged(self, complete_contract: dict) -> None:
        hypothesis_binding = materialize_versioned_hypothesis_binding_v0()
        assert (
            complete_contract["hypothesis_binding_digest"] == hypothesis_binding["binding_digest"]
        )
        assert complete_contract["hypothesis_binding_digest"] == RATIFIED_HYPOTHESIS_BINDING_DIGEST
        assert (
            complete_contract["hypothesis_binding_reference"]["hypothesis_binding_mutated"] is False
        )

    def test_lead_lag_v0_score_family_not_reused(self, complete_contract: dict) -> None:
        ok, reasons = validate_lead_lag_v0_score_family_not_reused_v0(complete_contract)
        assert ok, reasons
        assert (
            complete_contract["score_contract"]["score_formula_version"]
            != LEAD_LAG_V0_SCORE_FORMULA
        )


class TestScoreContract:
    def test_score_formula_version(self, complete_contract: dict) -> None:
        score = complete_contract["score_contract"]
        assert score["score_formula_version"] == SCORE_FORMULA_VERSION
        assert score["score_family_policy"] == SCORE_FAMILY_POLICY
        assert score["panel_median_benchmark_semantics_forbidden"] is True
        assert score["self_pair_i_equals_j_forbidden"] is True

    def test_pit_ordering_required(self, complete_contract: dict) -> None:
        score = complete_contract["score_contract"]
        assert score["feature_time_lt_decision_time_required"] is True
        assert score["target_time_gt_decision_time_required"] is True
        assert score["contemporaneous_target_leakage_forbidden"] is True


class TestRankingContract:
    def test_ranking_formulas_and_tie_breaks(self, complete_contract: dict) -> None:
        ranking = complete_contract["ranking_contract"]
        assert ranking["pair_ranking_formula"] == PAIR_RANKING_FORMULA
        assert ranking["instrument_ranking_formula"] == INSTRUMENT_RANKING_FORMULA
        assert ranking["pair_deterministic_tie_break"] == PAIR_DETERMINISTIC_TIE_BREAK
        assert ranking["instrument_deterministic_tie_break"] == INSTRUMENT_DETERMINISTIC_TIE_BREAK
        assert ranking["tie_break_score_source"] == "unrounded_internal_score"

    def test_selection_policies_deferred(self, complete_contract: dict) -> None:
        ranking = complete_contract["ranking_contract"]
        for field in (
            "selection_policy_binding_status",
            "aggregation_policy_binding_status",
            "holding_policy_binding_status",
            "exit_policy_binding_status",
            "portfolio_weighting_policy_binding_status",
        ):
            assert ranking[field] == PENDING_SELECTION_POLICY_STATUS


class TestContractRejections:
    def test_panel_median_not_forbidden_rejected(self, complete_contract: dict) -> None:
        rejected, reasons = validate_contract_rejections_v0(
            complete_contract,
            mutated_field="score.panel_median_benchmark_semantics_forbidden",
            mutated_value=False,
        )
        assert rejected
        assert "PANEL_MEDIAN_BENCHMARK_NOT_FORBIDDEN" in reasons

    def test_pair_tie_break_mismatch_rejected(self, complete_contract: dict) -> None:
        rejected, reasons = validate_contract_rejections_v0(
            complete_contract,
            mutated_field="ranking.pair_deterministic_tie_break",
            mutated_value="invalid_tie_break",
        )
        assert rejected
        assert "PAIR_TIE_BREAK_MISMATCH" in reasons


class TestScoreComputation:
    def _sample_closes(self, *, trend: float, count: int = 20) -> list[float]:
        return [100.0 + index * trend for index in range(count)]

    def test_directed_pair_score_positive_spillover(self) -> None:
        leader_closes = self._sample_closes(trend=1.0)
        follower_closes = self._sample_closes(trend=0.5)
        epoch_index = len(leader_closes) - 1 - DEFAULT_FORWARD_LAG_BARS
        result = compute_directed_pair_spillover_score_v0(
            "inst-leader",
            "inst-follower",
            leader_closes,
            follower_closes,
            lag_window_l=DEFAULT_LAG_WINDOW_L,
            signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
            forward_lag_bars=DEFAULT_FORWARD_LAG_BARS,
            epoch_index=epoch_index,
        )
        assert result is not None
        assert result.leader_id == "inst-leader"
        assert result.follower_id == "inst-follower"
        assert result.score == pytest.approx(
            result.leader_lagged_return * result.follower_future_return
        )

    def test_self_pair_forbidden(self) -> None:
        closes = self._sample_closes(trend=0.5)
        epoch_index = len(closes) - 1 - DEFAULT_FORWARD_LAG_BARS
        assert (
            compute_directed_pair_spillover_score_v0(
                "inst-a",
                "inst-a",
                closes,
                closes,
                lag_window_l=DEFAULT_LAG_WINDOW_L,
                signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
                forward_lag_bars=DEFAULT_FORWARD_LAG_BARS,
                epoch_index=epoch_index,
            )
            is None
        )

    def test_pair_ranking_tie_break_deterministic(self) -> None:
        closes = self._sample_closes(trend=0.2)
        instrument_closes = {
            f"inst-{label}": closes for label in ("alpha", "beta", "gamma", "delta", "epsilon")
        }
        epoch_index = len(closes) - 1 - DEFAULT_FORWARD_LAG_BARS
        pair_scores = compute_panel_pairwise_spillover_scores_v0(
            instrument_closes,
            lag_window_l=DEFAULT_LAG_WINDOW_L,
            signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
            forward_lag_bars=DEFAULT_FORWARD_LAG_BARS,
            epoch_index=epoch_index,
        )
        assert pair_scores is not None
        ranked_once = rank_pair_scores_deterministic_v0(pair_scores)
        ranked_twice = rank_pair_scores_deterministic_v0(list(reversed(pair_scores)))
        assert ranked_once == ranked_twice

    def test_instrument_net_spillover_ranking_tie_break(self) -> None:
        closes = self._sample_closes(trend=0.3)
        instrument_closes = {
            f"inst-{label}": closes for label in ("alpha", "beta", "gamma", "delta", "epsilon")
        }
        epoch_index = len(closes) - 1 - DEFAULT_FORWARD_LAG_BARS
        pair_scores = compute_panel_pairwise_spillover_scores_v0(
            instrument_closes,
            lag_window_l=DEFAULT_LAG_WINDOW_L,
            signal_lag_bars=DEFAULT_SIGNAL_LAG_BARS,
            forward_lag_bars=DEFAULT_FORWARD_LAG_BARS,
            epoch_index=epoch_index,
        )
        assert pair_scores is not None
        net_scores = compute_instrument_net_spillover_scores_v0(pair_scores)
        ranked = rank_instrument_net_spillover_scores_deterministic_v0(net_scores)
        assert len(ranked) == len(net_scores)
        assert ranked == rank_instrument_net_spillover_scores_deterministic_v0(
            list(reversed(net_scores))
        )


class TestScopeIdentity:
    def test_research_scope_and_go_token(self, complete_contract: dict) -> None:
        assert complete_contract["research_scope"] == RESEARCH_SCOPE
        assert CONFIRM_GO.endswith("IMPLEMENTATION_V0")

    def test_no_economic_evaluation(self, complete_contract: dict) -> None:
        assert complete_contract["economic_evaluation_executed"] is False
        assert complete_contract["runtime_effect"] == "NONE"
        assert complete_contract["authority_effect"] == "NONE"


class TestGovernanceAndPaths:
    def test_governance_doc_exists(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "pairwise_spillover_graph_v1" in text

    def test_materializer_script_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_config_rel_path_defined(self) -> None:
        assert CONFIG_REL_PATH.endswith(".json")

    def test_no_forbidden_runtime_imports_in_contract_modules(self) -> None:
        contract_module = (
            REPO_ROOT / "src/research/"
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py"
        )
        score_module = (
            REPO_ROOT / "src/research/"
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0.py"
        )
        for module_path in (contract_module, score_module):
            text = module_path.read_text(encoding="utf-8")
            for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
                assert prefix not in text
