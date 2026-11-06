"""Policy Critic - Governance gate for automated proposals."""

from .critic import PolicyCritic
from .models import (
    Evidence,
    PolicyCriticInput,
    PolicyCriticResult,
    RecommendedAction,
    ReviewContext,
    Severity,
    Violation,
)
from .packs import PackLoader, PolicyPack, create_pack_aware_critic
from .rules import ALL_RULES

__all__ = [
    "PolicyCritic",
    "PolicyCriticInput",
    "PolicyCriticResult",
    "RecommendedAction",
    "ReviewContext",
    "Severity",
    "Violation",
    "Evidence",
    "ALL_RULES",
    # G3: Policy Packs
    "PackLoader",
    "PolicyPack",
    "create_pack_aware_critic",
]
