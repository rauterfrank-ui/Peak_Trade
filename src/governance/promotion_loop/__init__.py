"""
Promotion Loop v1: Governance layer for promoting Learning Loop patches to live.

This package provides:
- PromotionCandidate and PromotionDecision models
- Governance filters for live eligibility
- Proposal generation and materialization
- Auto-apply policies with bounded constraints
- P0/P1 safety features (blacklist, bounds, audit logging)
"""

from .engine import (
    apply_proposals_to_live_overrides,
    build_promotion_candidates_from_patches,
    build_promotion_proposals,
    filter_candidates_for_live,
    materialize_promotion_proposals,
)
from .models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from .policy import AutoApplyBounds, AutoApplyPolicy
from .safety import (
    SafetyConfig,
    apply_safety_filters,
    check_blacklist,
    check_bounded_auto_guardrails,
    check_bounds,
    check_global_promotion_lock,
    has_p0_violations,
    load_safety_config_from_toml,
    write_audit_log_entry,
)

__all__ = [
    # Policy
    "AutoApplyBounds",
    "AutoApplyPolicy",
    # Models
    "DecisionStatus",
    "PromotionCandidate",
    "PromotionDecision",
    "PromotionProposal",
    # Safety (P0/P1)
    "SafetyConfig",
    # Engine functions
    "apply_proposals_to_live_overrides",
    "apply_safety_filters",
    "build_promotion_candidates_from_patches",
    "build_promotion_proposals",
    "check_blacklist",
    "check_bounded_auto_guardrails",
    "check_bounds",
    "check_global_promotion_lock",
    "filter_candidates_for_live",
    "has_p0_violations",
    "load_safety_config_from_toml",
    "materialize_promotion_proposals",
    "write_audit_log_entry",
]
