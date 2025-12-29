"""Governance module for feature approval, go/no-go decisions, sanity checks, and policy review."""

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
from .live_mode_gate import (
    ExecutionEnvironment,
    LiveModeStatus,
    LiveModeGate,
    LiveModeGateState,
    ValidationResult,
    create_gate,
    is_live_allowed,
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
    # Live Mode Gate (Phase 0 WP0C)
    "ExecutionEnvironment",
    "LiveModeStatus",
    "LiveModeGate",
    "LiveModeGateState",
    "ValidationResult",
    "create_gate",
    "is_live_allowed",
]
