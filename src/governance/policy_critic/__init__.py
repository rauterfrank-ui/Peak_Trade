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
    "ALL_RULES",
    "Evidence",
    # G3: Policy Packs
    "PackLoader",
    "PolicyCritic",
    "PolicyCriticInput",
    "PolicyCriticResult",
    "PolicyPack",
    "RecommendedAction",
    "ReviewContext",
    "Severity",
    "Violation",
    "create_pack_aware_critic",
]
