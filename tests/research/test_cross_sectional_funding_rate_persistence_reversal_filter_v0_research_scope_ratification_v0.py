"""Contract tests for CS funding-rate persistence reversal filter v0 research scope ratification."""

from __future__ import annotations

from pathlib import Path

from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0 import (
    OPERATOR_GO_SCOPE_RATIFICATION,
    RECOMMENDED_SCOPE_ID,
    STRATEGY_ID,
    STRATEGY_VERSION,
    TERMINALIZED_PARENT_STRATEGY,
    ValidationVerdictEnum,
    materialize_persistence_reversal_filter_research_scope_ratification_v0,
    validate_persistence_reversal_filter_research_scope_ratification_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/research/"
    "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_RESEARCH_SCOPE_RATIFICATION.md"
)
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0.json"
)


class TestCrossSectionalFundingRatePersistenceReversalFilterV0ResearchScopeRatification:
    def test_ratification_materializes_with_required_fields(self) -> None:
        ratification = materialize_persistence_reversal_filter_research_scope_ratification_v0(
            repo_root=REPO_ROOT,
        )
        validation = validate_persistence_reversal_filter_research_scope_ratification_v0(
            ratification
        )
        assert validation.verdict == ValidationVerdictEnum.ACCEPTED
        assert ratification["recommended_scope_id"] == RECOMMENDED_SCOPE_ID
        assert ratification["operator_go_token"] == OPERATOR_GO_SCOPE_RATIFICATION
        assert ratification["strategy_id"] == STRATEGY_ID
        assert ratification["strategy_version"] == STRATEGY_VERSION
        assert ratification["research_scope_definition_ratified"] is True
        assert ratification["binding_ratified"] is False
        assert ratification["all_required_bindings_ratified"] is False
        assert ratification["offline_economic_evaluation_scope_ratified"] is False
        assert ratification["economic_evaluation_executed"] is False
        assert ratification["next_scope_requires_separate_evaluation_go"] is True
        assert ratification["promotion_granted"] is False
        assert ratification["runtime_authority_touched"] is False
        assert ratification["promotion_admissible"] is False
        assert ratification["runtime_rewire_admissible"] is False
        assert ratification["material_difference_vs_rank_delta_v0_confirmed"] is True
        assert ratification["unchanged_retry"] is False
        assert ratification["unchanged_retry_allowed"] is False
        assert ratification["parameter_rescue"] is False
        assert ratification["threshold_relaxation"] is False
        assert ratification["unchanged_retry_of_failed_bindings_forbidden"] is True
        assert TERMINALIZED_PARENT_STRATEGY in ratification["terminal_failed_binding_exclusions"]
        assert ratification["core_system_mutation_allowed"] is False
        assert ratification["no_orders"] is True
        assert ratification["no_live"] is True

    def test_governance_doc_exists_and_states_no_eval(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert RECOMMENDED_SCOPE_ID in text
        assert "ECONOMIC_EVALUATION_EXECUTED" in text
        assert "PROMOTION_GRANTED" in text
        assert "false" in text
        assert "persistence" in text.lower()
        assert "reversal" in text.lower()
        assert "rank_delta" in text.lower()

    def test_no_runtime_authority_in_ratification(self) -> None:
        ratification = materialize_persistence_reversal_filter_research_scope_ratification_v0(
            repo_root=REPO_ROOT,
        )
        assert ratification["authority_effect"] == "NONE"
        assert ratification["runtime_effect"] == "NONE"
        assert ratification["order_effect"] == "NONE"
        assert ratification["no_credentials"] is True
        assert ratification["no_scheduler"] is True
        assert ratification["no_shadow"] is True
        assert ratification["no_paper"] is True
        assert ratification["no_testnet"] is True

    def test_scope_config_matches_materialized_ratification_when_present(self) -> None:
        if not SCOPE_CONFIG.is_file():
            return
        import json

        ratification = materialize_persistence_reversal_filter_research_scope_ratification_v0(
            repo_root=REPO_ROOT,
        )
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["ratification_digest"] == ratification["ratification_digest"]
        assert config["strategy_id"] == STRATEGY_ID
