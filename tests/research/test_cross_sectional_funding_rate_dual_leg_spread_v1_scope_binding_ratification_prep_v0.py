"""Contract tests for CS funding-rate dual-leg spread v1 scope binding ratification prep."""

from __future__ import annotations

from pathlib import Path

from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_offline_economic_evaluation_scope_ratification_v0 import (
    OPERATOR_GO_RATIFICATION_PREP,
    RECOMMENDED_SCOPE_ID,
    STRATEGY_ID,
    STRATEGY_VERSION,
    ValidationVerdictEnum,
    materialize_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1,
    validate_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/research/"
    "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_OFFLINE_ECONOMIC_EVALUATION_BINDING_RATIFICATION_PREP.md"
)


class TestCrossSectionalFundingRateDualLegSpreadV1ScopeBindingRatificationPrep:
    def test_ratification_materializes_with_required_fields(self) -> None:
        binding = materialize_versioned_research_binding_v1()
        ratification = (
            materialize_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1(
                repo_root=REPO_ROOT,
                versioned_binding=binding,
            )
        )
        validation = validate_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1(
            ratification,
            expected_binding=binding,
        )
        assert validation.verdict == ValidationVerdictEnum.ACCEPTED
        assert ratification["recommended_scope_id"] == RECOMMENDED_SCOPE_ID
        assert ratification["operator_go_token"] == OPERATOR_GO_RATIFICATION_PREP
        assert ratification["strategy_id"] == STRATEGY_ID
        assert ratification["strategy_version"] == STRATEGY_VERSION
        assert ratification["all_required_bindings_ratified"] is True
        assert ratification["binding_ratified"] is True
        assert ratification["economic_evaluation_executed"] is False
        assert ratification["promotion_admissible"] is False
        assert ratification["runtime_rewire_admissible"] is False
        assert ratification["material_difference_vs_pr4925_confirmed"] is True
        assert ratification["unchanged_retry"] is False
        assert ratification["parameter_rescue"] is False
        assert ratification["threshold_relaxation"] is False
        assert (
            "cross_sectional_funding_rate_delta_momentum/v0"
            in ratification["terminal_failed_binding_exclusions"]
        )
        assert ratification["evaluation_infrastructure_ready"] is False

    def test_governance_doc_exists_and_states_no_eval(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert RECOMMENDED_SCOPE_ID in text
        assert "ECONOMIC_EVALUATION_EXECUTED" in text
        assert "PROMOTION_ADMISSIBLE" in text
        assert "false" in text
        assert "dual_leg_simultaneous" in text.lower() or "dual-leg" in text.lower()
