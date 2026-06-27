"""Dedicated policy characterization tests for manifest-era offline promotion (GAP-007)."""

from __future__ import annotations

from pathlib import Path

from src.governance.promotion_loop.engine import apply_proposals_to_live_overrides
from src.governance.promotion_loop.models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from src.governance.promotion_loop.policy import AutoApplyBounds, AutoApplyPolicy
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


def _accepted_proposal(*, target: str = "research.offline.window_days") -> PromotionProposal:
    patch = ConfigPatch(
        id="patch-policy-1",
        target=target,
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    candidate = PromotionCandidate(patch=patch, eligible_for_live=True, tags=["research"])
    decision = PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=[],
    )
    return PromotionProposal(
        proposal_id="offline_policy_test_001",
        title="test",
        description="test",
        decisions=[decision],
        meta={},
    )


def test_auto_apply_policy_default_is_manual_only() -> None:
    policy = AutoApplyPolicy()
    assert policy.mode == "manual_only"
    assert policy.is_bounded_auto() is False


def test_is_bounded_auto_only_for_bounded_auto_mode() -> None:
    assert AutoApplyPolicy(mode="disabled").is_bounded_auto() is False
    assert AutoApplyPolicy(mode="manual_only").is_bounded_auto() is False
    assert AutoApplyPolicy(mode="bounded_auto").is_bounded_auto() is True


def test_apply_proposals_returns_none_for_manual_only(tmp_path: Path) -> None:
    proposal = _accepted_proposal()
    live_path = tmp_path / "config" / "live_overrides" / "auto.toml"
    result = apply_proposals_to_live_overrides(
        [proposal],
        policy=AutoApplyPolicy(mode="manual_only"),
        live_override_path=live_path,
    )
    assert result is None
    assert not live_path.exists()


def test_apply_proposals_returns_none_for_disabled_mode(tmp_path: Path) -> None:
    proposal = _accepted_proposal()
    live_path = tmp_path / "auto.toml"
    result = apply_proposals_to_live_overrides(
        [proposal],
        policy=AutoApplyPolicy(mode="disabled"),
        live_override_path=live_path,
    )
    assert result is None
    assert not live_path.exists()


def test_bounded_auto_policy_retains_existing_bounds_fields() -> None:
    policy = AutoApplyPolicy(
        mode="bounded_auto",
        leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=0.25),
        trigger_delay_bounds=AutoApplyBounds(min_value=3.0, max_value=15.0, max_step=2.0),
        macro_weight_bounds=AutoApplyBounds(min_value=0.0, max_value=0.8, max_step=0.1),
    )
    assert policy.leverage_bounds is not None
    assert policy.leverage_bounds.max_value == 2.0
