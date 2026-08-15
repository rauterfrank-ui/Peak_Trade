"""I37 / I74 / I85 forensic rows for R6 S2 (read-only).

I37 and I74 must not form two independent VaR authorities.
I85 must not become a parallel portfolio-risk owner beside the
canonical risk chain.
"""

from __future__ import annotations

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.models_v1 import (
    IntentForensicRowV1,
    R6S2PortfolioRiskError,
)

REQUIRED_INTENT_IDS = ("I37", "I74", "I85")

I37_I74_I85_ROWS: tuple[IntentForensicRowV1, ...] = (
    IntentForensicRowV1(
        intent_id="I37",
        current_state="IMPLEMENTED_NOT_PROVEN_SUPPORTING_LIBRARY",
        current_runtime_reachability=(
            "src/risk/var.py historical/parametric/EWMA/Cornish-Fisher VaR+CVaR; "
            "monte_carlo.py; stress.py; not imported by Cap7.2 productive no-order host"
        ),
        current_authority_effect="NONE",
        current_callers=(
            "RiskLayerManager (research orchestration); scripts/risk/*; "
            "backtest/research; no productive Cap2.4/7.2 caller as authority"
        ),
        current_config="config/risk_layer_v1_example.toml example-only; not productive MF grant",
        current_tests="tests/risk/test_var_core.py and related risk-layer unit tests",
        current_evidence="library unit tests; no productive portfolio-VaR evidence pack",
        canonical_owner="src.risk.var as GOVERNED_SUPPORTING_METHOD_LIBRARY",
        duplicate_authority_risk=(
            "MUST_NOT_BE_SECOND_VAR_AUTHORITY_BESIDE_I74_OR_CAPITAL_RISK_SIZING"
        ),
        long_term_role="CANONICAL_AUTHORITY_TARGET_AS_METHOD_CONSUMED_BY_RISK_CHAIN",
        s2_requirement="bind as supporting library; reuse later; no authority promotion",
        s2_gap="NONE_FOR_S2_STRUCTURAL_CONTRACT",
        implementation_required_later="S3 consume behind flags; S4 evidence; R7 live risk write",
        safe_to_bind_read_only=True,
    ),
    IntentForensicRowV1(
        intent_id="I74",
        current_state="PLANNED_ONLY_ROADMAP_NON_RUNTIME",
        current_runtime_reachability="docs/risk/roadmaps/* only; no runtime module",
        current_authority_effect="NONE",
        current_callers="none_runtime",
        current_config="none_runtime",
        current_tests="none_as_engine",
        current_evidence="roadmap documents; not implementation evidence",
        canonical_owner="docs.risk.roadmaps as CANONICAL_REQUIREMENT_IDENTITY",
        duplicate_authority_risk=("MUST_NOT_BE_INTERPRETED_AS_A_SECOND_VAR_ENGINE_BESIDE_I37"),
        long_term_role="REQUIREMENT_AND_ROADMAP_SURFACE_NON_RUNTIME",
        s2_requirement="bind as non-runtime requirement identity feeding I85/I37 reuse",
        s2_gap="NONE_FOR_S2_STRUCTURAL_CONTRACT",
        implementation_required_later="implementation remains I37 methods + canonical chain, not a new engine",
        safe_to_bind_read_only=True,
    ),
    IntentForensicRowV1(
        intent_id="I85",
        current_state="CLOSED_BOUNDARY_CONTRACT_IDENTITY_G13_GATED",
        current_runtime_reachability=(
            "no productive MF portfolio/component VaR owner; helpers in "
            "src/risk/component_var.py and portfolio_var.py are non-authority"
        ),
        current_authority_effect="NONE",
        current_callers="scripts/run_component_var_report.py research; RiskLayerManager optional feature",
        current_config="risk.portfolio_var.* example keys in portfolio_var config builder; unused as grant",
        current_tests="tests/risk/test_portfolio_var_phase1.py and component-var tests",
        current_evidence="helper unit tests; G13 still INTENTIONAL_SAFETY_BARRIER",
        canonical_owner="I85_CONTRACT_IDENTITY_CONSUMED_BY_CANONICAL_RISK_CHAIN",
        duplicate_authority_risk=(
            "MUST_NOT_BECOME_PARALLEL_PORTFOLIO_RISK_OWNER_BESIDE_CAPITAL_RISK_SIZING"
        ),
        long_term_role="CANONICAL_AUTHORITY_PLUS_TRANSITIONAL_GATE_G13",
        s2_requirement="bind structural ownership; numerics deferred; G13 unchanged",
        s2_gap="NONE_FOR_S2_STRUCTURAL_CONTRACT",
        implementation_required_later="S3 unauthorized runtime behind flags; S5 unlock needs live proof+GO",
        safe_to_bind_read_only=True,
    ),
)


def require_intent(intent_id: str) -> IntentForensicRowV1:
    for row in I37_I74_I85_ROWS:
        if row.intent_id == intent_id:
            return row
    raise R6S2PortfolioRiskError(f"unknown_s2_intent:{intent_id}")
