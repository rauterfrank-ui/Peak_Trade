"""Governance module for feature approval, go/no-go decisions, sanity checks, and policy review.

P0 Guardrails Drill Test: CODEOWNERS enforcement
This comment verifies that changes to src/governance/ trigger required reviews.
"""

from .go_no_go import (
    GovernanceStatus,
    get_governance_status,
    is_feature_approved_for_year,
)
from .strategy_switch_sanity_check import (
    StrategySwitchSanityResult,
    StrategyMeta,
    run_strategy_switch_sanity_check,
    print_result as print_sanity_result,
)

# Policy Critic is available as a submodule: governance.policy_critic

__all__ = [
    # Go/No-Go
    "GovernanceStatus",
    "get_governance_status",
    "is_feature_approved_for_year",
    # Strategy-Switch Sanity
    "StrategySwitchSanityResult",
    "StrategyMeta",
    "run_strategy_switch_sanity_check",
    "print_sanity_result",
]
