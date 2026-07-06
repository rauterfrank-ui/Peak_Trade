"""Contract tests for CS funding-rate delta momentum v0 scope binding ratification prep."""

from __future__ import annotations

from pathlib import Path

from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification_v0 import (
    OPERATOR_GO_RATIFICATION_PREP,
    RECOMMENDED_SCOPE_ID,
    STRATEGY_ID,
    STRATEGY_VERSION,
    ValidationVerdictEnum,
    materialize_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0,
    validate_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/research/"
    "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_BINDING_RATIFICATION_PREP.md"
)


class TestCrossSectionalFundingRateDeltaMomentumV0ScopeBindingRatificationPrep:
    def test_ratification_materializes_with_required_fields(self) -> None:
        binding = materialize_versioned_research_binding_v0()
        ratification = (
            materialize_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0(
                repo_root=REPO_ROOT,
                versioned_binding=binding,
            )
        )
        validation = (
            validate_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0(
                ratification,
                expected_binding=binding,
            )
        )
        assert validation.verdict == ValidationVerdictEnum.ACCEPTED
        assert ratification["recommended_scope_id"] == RECOMMENDED_SCOPE_ID
        assert ratification["operator_go_token"] == OPERATOR_GO_RATIFICATION_PREP
        assert ratification["strategy_id"] == STRATEGY_ID
        assert ratification["strategy_version"] == STRATEGY_VERSION
        assert ratification["all_required_bindings_ratified"] is True
        assert ratification["economic_evaluation_executed"] is False
        assert ratification["promotion_admissible"] is False
        assert ratification["runtime_rewire_admissible"] is False
        assert "trend_following/v2" in ratification["terminal_failed_binding_exclusions"]
        assert ratification["runner_binding"]
        assert ratification["harness_binding"]

    def test_governance_doc_exists_and_states_no_eval(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert RECOMMENDED_SCOPE_ID in text
        assert "ECONOMIC_EVALUATION_EXECUTED" in text
        assert "PROMOTION_ADMISSIBLE" in text
        assert "false" in text
