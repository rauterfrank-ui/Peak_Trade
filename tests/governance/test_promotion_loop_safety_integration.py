"""
Integration tests for Promotion Loop with P0/P1 safety features.

Tests the full promotion cycle with realistic scenarios:
- Valid candidate passes all filters
- Blacklisted candidate is rejected
- Out-of-bounds candidate is rejected
- Multiple candidates with mixed safety statuses
"""

from datetime import datetime
from pathlib import Path
import tempfile

import pytest

from src.governance.promotion_loop import (
    build_promotion_candidates_from_patches,
    filter_candidates_for_live,
    build_promotion_proposals,
)
from src.governance.promotion_loop.safety import SafetyConfig
from src.governance.promotion_loop.policy import AutoApplyBounds
from src.governance.promotion_loop.models import DecisionStatus
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


@pytest.fixture
def safety_config():
    """Create a realistic SafetyConfig for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield SafetyConfig(
            blacklist_targets=["live.api_keys", "risk.stop_loss"],
            blacklist_tags=["r_and_d", "experimental"],
            bounds={
                "leverage": AutoApplyBounds(
                    min_value=1.0,
                    max_value=2.0,
                    max_step=0.25,
                ),
            },
            global_promotion_lock=False,
            audit_log_path=Path(tmpdir) / "audit.jsonl",
            min_confidence_for_auto_apply=0.80,
        )


def test_full_cycle_with_valid_candidate(safety_config):
    """Test full promotion cycle with a valid candidate."""
    # Create valid patch
    patch = ConfigPatch(
        id="valid_patch_001",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.2,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.85,
    )
    
    # Build candidate
    candidates = build_promotion_candidates_from_patches([patch])
    assert len(candidates) == 1
    
    # Mark as eligible
    candidates[0].eligible_for_live = True
    
    # Filter with safety checks
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Should be accepted
    assert len(decisions) == 1
    assert decisions[0].status == DecisionStatus.ACCEPTED_FOR_PROPOSAL
    assert len(decisions[0].candidate.safety_flags) == 0
    
    # Build proposals
    proposals = build_promotion_proposals(decisions)
    assert len(proposals) == 1
    assert len(proposals[0].decisions) == 1


def test_full_cycle_with_blacklisted_candidate(safety_config):
    """Test full promotion cycle with a blacklisted candidate."""
    # Create blacklisted patch
    patch = ConfigPatch(
        id="blacklisted_patch_001",
        target="live.api_keys.binance",  # Blacklisted!
        old_value="old_key",
        new_value="new_key",
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.99,  # High confidence, but still rejected
    )
    
    # Build candidate
    candidates = build_promotion_candidates_from_patches([patch])
    candidates[0].eligible_for_live = True
    
    # Filter with safety checks
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Should be rejected due to P0 violation
    assert len(decisions) == 1
    assert decisions[0].status == DecisionStatus.REJECTED_BY_POLICY
    assert len(decisions[0].candidate.safety_flags) > 0
    assert any("P0_BLACKLIST" in f for f in decisions[0].candidate.safety_flags)
    
    # No proposals should be generated
    proposals = build_promotion_proposals(decisions)
    assert len(proposals) == 0


def test_full_cycle_with_out_of_bounds_candidate(safety_config):
    """Test full promotion cycle with an out-of-bounds candidate."""
    # Create out-of-bounds patch
    patch = ConfigPatch(
        id="oob_patch_001",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=2.5,  # Above max_value (2.0)
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.85,
    )
    
    # Build candidate
    candidates = build_promotion_candidates_from_patches([patch])
    candidates[0].eligible_for_live = True
    
    # Filter with safety checks
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Should be rejected due to P0 violation
    assert len(decisions) == 1
    assert decisions[0].status == DecisionStatus.REJECTED_BY_POLICY
    assert len(decisions[0].candidate.safety_flags) > 0
    assert any("P0_BOUNDS" in f for f in decisions[0].candidate.safety_flags)


def test_full_cycle_with_mixed_candidates(safety_config):
    """Test full promotion cycle with multiple candidates (valid and invalid)."""
    # Create mix of patches
    patches = [
        # Valid patch
        ConfigPatch(
            id="valid_patch",
            target="portfolio.leverage",
            old_value=1.0,
            new_value=1.2,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.85,
        ),
        # Blacklisted patch
        ConfigPatch(
            id="blacklisted_patch",
            target="live.api_keys.exchange",
            old_value="old",
            new_value="new",
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.90,
        ),
        # Out-of-bounds patch
        ConfigPatch(
            id="oob_patch",
            target="portfolio.leverage",
            old_value=1.0,
            new_value=3.0,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.80,
        ),
        # Low confidence patch
        ConfigPatch(
            id="low_conf_patch",
            target="strategy.trigger_delay",
            old_value=10.0,
            new_value=8.0,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.60,
        ),
    ]
    
    # Build candidates
    candidates = build_promotion_candidates_from_patches(patches)
    assert len(candidates) == 4
    
    # Mark first 3 as eligible (4th has low confidence)
    for i in range(3):
        candidates[i].eligible_for_live = True
    
    # Filter with safety checks
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Should have 4 decisions
    assert len(decisions) == 4
    
    # Check results
    accepted = [d for d in decisions if d.status == DecisionStatus.ACCEPTED_FOR_PROPOSAL]
    rejected = [d for d in decisions if d.status == DecisionStatus.REJECTED_BY_POLICY]
    
    # Only valid patch should be accepted
    assert len(accepted) == 1
    assert accepted[0].candidate.patch.id == "valid_patch"
    
    # Others should be rejected
    assert len(rejected) == 3
    
    # Build proposals (should only include valid patch)
    proposals = build_promotion_proposals(decisions)
    assert len(proposals) == 1
    assert len(proposals[0].decisions) == 1
    assert proposals[0].decisions[0].candidate.patch.id == "valid_patch"


def test_bounded_auto_mode_enforces_stricter_rules(safety_config):
    """Test that bounded_auto mode enforces stricter guardrails."""
    # Create patch with confidence = 0.75 (below bounded_auto threshold of 0.80)
    patch = ConfigPatch(
        id="borderline_patch",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.2,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.75,  # OK for manual_only, not OK for bounded_auto
    )
    
    # Build candidate
    candidates = build_promotion_candidates_from_patches([patch])
    candidates[0].eligible_for_live = True
    
    # Test manual_only mode (should pass)
    decisions_manual = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Should be accepted in manual_only
    assert len([d for d in decisions_manual if d.status == DecisionStatus.ACCEPTED_FOR_PROPOSAL]) == 1
    
    # Test bounded_auto mode (should fail due to low confidence)
    decisions_auto = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="bounded_auto",
    )
    
    # Should be rejected in bounded_auto
    rejected_auto = [d for d in decisions_auto if d.status == DecisionStatus.REJECTED_BY_POLICY]
    assert len(rejected_auto) == 1
    assert any("P0_GUARDRAIL" in f for f in rejected_auto[0].candidate.safety_flags)


def test_global_lock_prevents_bounded_auto_candidates(safety_config):
    """Test that global lock prevents bounded_auto promotion."""
    safety_config.global_promotion_lock = True
    
    # Create valid patch
    patch = ConfigPatch(
        id="valid_patch",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.2,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.90,
    )
    
    # Build candidate
    candidates = build_promotion_candidates_from_patches([patch])
    candidates[0].eligible_for_live = True
    
    # Filter in bounded_auto mode with lock active
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="bounded_auto",
    )
    
    # Should be rejected due to global lock
    assert len(decisions) == 1
    assert decisions[0].status == DecisionStatus.REJECTED_BY_POLICY
    assert any("Global promotion lock" in f for f in decisions[0].candidate.safety_flags)


def test_audit_log_records_all_decisions(safety_config):
    """Test that audit log records all decisions (accepted and rejected)."""
    # Create mix of patches
    patches = [
        ConfigPatch(
            id="valid",
            target="portfolio.leverage",
            old_value=1.0,
            new_value=1.2,
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.85,
        ),
        ConfigPatch(
            id="blacklisted",
            target="live.api_keys",
            old_value="old",
            new_value="new",
            status=PatchStatus.APPLIED_OFFLINE,
            generated_at=datetime.utcnow(),
            confidence_score=0.90,
        ),
    ]
    
    # Build and filter
    candidates = build_promotion_candidates_from_patches(patches)
    for c in candidates:
        c.eligible_for_live = True
    
    decisions = filter_candidates_for_live(
        candidates,
        safety_config=safety_config,
        mode="manual_only",
    )
    
    # Check audit log
    audit_path = safety_config.audit_log_path
    assert audit_path.exists()
    
    with audit_path.open("r") as f:
        lines = f.readlines()
        assert len(lines) == 2  # Both decisions logged
        
        # Verify content
        import json
        entries = [json.loads(line) for line in lines]
        
        # Check that both patches are in audit log
        patch_ids = [e["patch_id"] for e in entries]
        assert "valid" in patch_ids
        assert "blacklisted" in patch_ids


