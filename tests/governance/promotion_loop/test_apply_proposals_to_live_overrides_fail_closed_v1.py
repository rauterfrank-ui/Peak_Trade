"""Fail-closed contract: apply_proposals_to_live_overrides never writes."""

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


def _accepted_leverage_proposal() -> PromotionProposal:
    patch = ConfigPatch(
        id="patch-leverage-fail-closed-1",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.75,
        status=PatchStatus.APPLIED_OFFLINE,
    )
    candidate = PromotionCandidate(
        patch=patch,
        eligible_for_live=True,
        tags=["leverage"],
    )
    decision = PromotionDecision(
        candidate=candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=["accepted leverage proposal for fail-closed writer contract"],
    )
    return PromotionProposal(
        proposal_id="fail_closed_leverage_001",
        title="fail-closed leverage write",
        description="historically eligible bounded_auto leverage write",
        decisions=[decision],
        meta={},
    )


def test_bounded_auto_accepted_leverage_proposal_returns_none_and_does_not_write(
    tmp_path: Path,
) -> None:
    live_path = tmp_path / "config" / "live_overrides" / "auto.toml"
    policy = AutoApplyPolicy(
        mode="bounded_auto",
        leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=1.0),
    )
    result = apply_proposals_to_live_overrides(
        [_accepted_leverage_proposal()],
        policy=policy,
        live_override_path=live_path,
    )
    assert result is None
    assert not live_path.exists()
    assert not live_path.parent.exists()


def test_bounded_auto_does_not_mutate_existing_override_file(tmp_path: Path) -> None:
    live_path = tmp_path / "auto.toml"
    original = '[auto_applied]\n"portfolio.leverage" = 1.0\n'
    live_path.write_text(original, encoding="utf-8")
    policy = AutoApplyPolicy(
        mode="bounded_auto",
        leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=1.0),
    )
    result = apply_proposals_to_live_overrides(
        [_accepted_leverage_proposal()],
        policy=policy,
        live_override_path=live_path,
    )
    assert result is None
    assert live_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.backup"))
