"""
Risk Runtime Package (WP0B - Phase 0 Foundation)

Runtime risk evaluation system with pluggable policies.

Public API:
- RiskDecision: Extended decision enum (ALLOW/REJECT/MODIFY/HALT)
- RiskDirective: Risk evaluation result with reason and optional modifications
- RiskContextSnapshot: Snapshot of system state for risk evaluation
- RiskPolicy: Protocol for risk policies
- RiskRuntime: Main orchestrator for risk evaluation
- RuntimeRiskHook: Adapter implementing RiskHook protocol
"""

from src.execution.risk_runtime.decisions import (
    RiskDecision,
    RiskDirective,
)

from src.execution.risk_runtime.context import (
    RiskContextSnapshot,
    build_context_snapshot,
    build_empty_snapshot,
)

from src.execution.risk_runtime.policies import (
    RiskPolicy,
    NoopPolicy,
    MaxOpenOrdersPolicy,
    MaxPositionSizePolicy,
    MinCashBalancePolicy,
)

from src.execution.risk_runtime.runtime import (
    RiskRuntime,
)

__all__ = [
    # Decisions
    "RiskDecision",
    "RiskDirective",
    # Context
    "RiskContextSnapshot",
    "build_context_snapshot",
    "build_empty_snapshot",
    # Policies
    "RiskPolicy",
    "NoopPolicy",
    "MaxOpenOrdersPolicy",
    "MaxPositionSizePolicy",
    "MinCashBalancePolicy",
    # Runtime
    "RiskRuntime",
]
