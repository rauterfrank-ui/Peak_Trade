"""
Tests for Promotion Loop P0/P1 safety features.

Tests cover:
- P0: Blacklist checking
- P0: Bounds validation
- P0: bounded_auto guardrails
- P1: Audit logging
- P1: Global promotion lock
"""

from pathlib import Path
from datetime import datetime
import json
import tempfile

import pytest

from src.governance.promotion_loop.models import PromotionCandidate, PromotionDecision, DecisionStatus
from src.governance.promotion_loop.policy import AutoApplyBounds
from src.governance.promotion_loop.safety import (
    SafetyConfig,
    check_blacklist,
    check_bounds,
    check_bounded_auto_guardrails,
    check_global_promotion_lock,
    apply_safety_filters,
    has_p0_violations,
    write_audit_log_entry,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


@pytest.fixture
def sample_patch():
    """Create a sample ConfigPatch for testing."""
    return ConfigPatch(
        id="test_patch_001",
        target="portfolio.leverage",
        old_value=1.0,
        new_value=1.5,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=datetime.utcnow(),
        confidence_score=0.85,
        meta={"is_live_ready": True},
    )


@pytest.fixture
def sample_candidate(sample_patch):
    """Create a sample PromotionCandidate for testing."""
    return PromotionCandidate(
        patch=sample_patch,
        tags=["leverage"],
        eligible_for_live=True,
        notes="Test candidate",
        safety_flags=[],
    )


@pytest.fixture
def safety_config():
    """Create a sample SafetyConfig for testing."""
    return SafetyConfig(
        blacklist_targets=["live.api_keys", "risk.stop_loss"],
        blacklist_tags=["r_and_d", "experimental"],
        bounds={
            "leverage": AutoApplyBounds(
                min_value=1.0,
                max_value=2.0,
                max_step=0.25,
            ),
            "trigger": AutoApplyBounds(
                min_value=3.0,
                max_value=15.0,
                max_step=2.0,
            ),
        },
        global_promotion_lock=False,
        min_confidence_for_auto_apply=0.80,
    )


# =============================================================================
# P0: Blacklist Tests
# =============================================================================

def test_blacklist_rejects_exact_match(sample_candidate, safety_config):
    """Test that blacklist rejects exact target matches."""
    sample_candidate.patch.target = "live.api_keys"
    
    violations = check_blacklist(sample_candidate, safety_config)
    
    assert len(violations) == 1
    assert "P0_BLACKLIST" in violations[0]
    assert "live.api_keys" in violations[0]


def test_blacklist_rejects_prefix_match(sample_candidate, safety_config):
    """Test that blacklist rejects prefix matches (e.g., live.api_keys.binance)."""
    sample_candidate.patch.target = "live.api_keys.binance"
    
    violations = check_blacklist(sample_candidate, safety_config)
    
    assert len(violations) == 1
    assert "P0_BLACKLIST" in violations[0]


def test_blacklist_rejects_blacklisted_tags(sample_candidate, safety_config):
    """Test that blacklist rejects candidates with blacklisted tags."""
    sample_candidate.tags = ["leverage", "r_and_d"]
    
    violations = check_blacklist(sample_candidate, safety_config)
    
    assert len(violations) == 1
    assert "P0_BLACKLIST" in violations[0]
    assert "r_and_d" in violations[0]


def test_blacklist_allows_safe_targets(sample_candidate, safety_config):
    """Test that blacklist allows non-blacklisted targets."""
    sample_candidate.patch.target = "portfolio.leverage"
    sample_candidate.tags = ["leverage"]
    
    violations = check_blacklist(sample_candidate, safety_config)
    
    assert len(violations) == 0


# =============================================================================
# P0: Bounds Tests
# =============================================================================

def test_bounds_rejects_value_below_min(sample_candidate, safety_config):
    """Test that bounds reject values below min_value."""
    sample_candidate.patch.new_value = 0.5  # Below min_value (1.0)
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) >= 1
    assert any("P0_BOUNDS" in v and "min_value" in v for v in violations)


def test_bounds_rejects_value_above_max(sample_candidate, safety_config):
    """Test that bounds reject values above max_value."""
    sample_candidate.patch.new_value = 2.5  # Above max_value (2.0)
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) >= 1
    assert any("P0_BOUNDS" in v and "max_value" in v for v in violations)


def test_bounds_rejects_step_too_large(sample_candidate, safety_config):
    """Test that bounds reject steps larger than max_step."""
    sample_candidate.patch.old_value = 1.0
    sample_candidate.patch.new_value = 1.5  # Step = 0.5 > max_step (0.25)
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) == 1
    assert "P0_BOUNDS" in violations[0]
    assert "max_step" in violations[0]


def test_bounds_allows_valid_changes(sample_candidate, safety_config):
    """Test that bounds allow valid changes within limits."""
    sample_candidate.patch.old_value = 1.0
    sample_candidate.patch.new_value = 1.2  # Step = 0.2 <= max_step (0.25)
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) == 0


def test_bounds_skips_non_numeric_values(sample_candidate, safety_config):
    """Test that bounds checking skips non-numeric values."""
    sample_candidate.patch.new_value = "weekly"  # String value
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) == 0


def test_bounds_skips_unconfigured_tags(sample_candidate, safety_config):
    """Test that bounds checking skips tags without configured bounds."""
    sample_candidate.tags = ["unknown_tag"]
    sample_candidate.patch.new_value = 999.0  # Would violate bounds if checked
    
    violations = check_bounds(sample_candidate, safety_config)
    
    assert len(violations) == 0


# =============================================================================
# P0: bounded_auto Guardrails Tests
# =============================================================================

def test_guardrails_reject_when_global_lock_active(sample_candidate, safety_config):
    """Test that guardrails reject when global promotion lock is active."""
    safety_config.global_promotion_lock = True
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "bounded_auto")
    
    assert len(violations) == 1
    assert "P0_GUARDRAIL" in violations[0]
    assert "Global promotion lock" in violations[0]


def test_guardrails_reject_when_p0_flags_present(sample_candidate, safety_config):
    """Test that guardrails reject candidates with existing P0 violations."""
    sample_candidate.safety_flags = ["P0_BLACKLIST: Some violation"]
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "bounded_auto")
    
    assert len(violations) == 1
    assert "P0_GUARDRAIL" in violations[0]
    assert "P0 violations" in violations[0]


def test_guardrails_reject_low_confidence(sample_candidate, safety_config):
    """Test that guardrails reject low confidence patches."""
    sample_candidate.patch.confidence_score = 0.70  # Below min_threshold (0.80)
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "bounded_auto")
    
    assert len(violations) == 1
    assert "P0_GUARDRAIL" in violations[0]
    assert "Confidence" in violations[0]


def test_guardrails_reject_r_and_d_tier(sample_candidate, safety_config):
    """Test that guardrails reject R&D tier candidates."""
    sample_candidate.tags = ["leverage", "r_and_d"]
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "bounded_auto")
    
    assert len(violations) == 1
    assert "P0_GUARDRAIL" in violations[0]
    assert "R&D" in violations[0]


def test_guardrails_reject_not_live_ready(sample_candidate, safety_config):
    """Test that guardrails reject patches not marked as live-ready."""
    sample_candidate.patch.meta["is_live_ready"] = False
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "bounded_auto")
    
    assert len(violations) == 1
    assert "P0_GUARDRAIL" in violations[0]
    assert "not live-ready" in violations[0]


def test_guardrails_skip_for_manual_only(sample_candidate, safety_config):
    """Test that guardrails are not enforced for manual_only mode."""
    safety_config.global_promotion_lock = True  # Would fail in bounded_auto
    
    violations = check_bounded_auto_guardrails(sample_candidate, safety_config, "manual_only")
    
    assert len(violations) == 0


# =============================================================================
# P0: Integration Tests
# =============================================================================

def test_apply_safety_filters_updates_safety_flags(sample_candidate, safety_config):
    """Test that apply_safety_filters correctly updates safety_flags."""
    sample_candidate.patch.target = "live.api_keys.binance"  # Blacklisted
    
    apply_safety_filters(sample_candidate, safety_config, "manual_only")
    
    assert len(sample_candidate.safety_flags) > 0
    assert any("P0_BLACKLIST" in f for f in sample_candidate.safety_flags)


def test_has_p0_violations_detects_p0_flags(sample_candidate):
    """Test that has_p0_violations correctly detects P0 flags."""
    assert not has_p0_violations(sample_candidate)
    
    sample_candidate.safety_flags = ["P0_BLACKLIST: Test violation"]
    
    assert has_p0_violations(sample_candidate)


def test_has_p0_violations_ignores_p1_flags(sample_candidate):
    """Test that has_p0_violations ignores P1 flags."""
    sample_candidate.safety_flags = ["P1_AUDIT: Some info"]
    
    assert not has_p0_violations(sample_candidate)


# =============================================================================
# P1: Audit Logging Tests
# =============================================================================

def test_write_audit_log_entry_creates_file(sample_candidate, safety_config):
    """Test that audit log entry is written to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = Path(tmpdir) / "audit.jsonl"
        safety_config.audit_log_path = audit_path
        
        decision = PromotionDecision(
            candidate=sample_candidate,
            status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
            reasons=[],
        )
        
        write_audit_log_entry(sample_candidate, decision, "manual_only", safety_config)
        
        assert audit_path.exists()
        
        # Verify content
        with audit_path.open("r") as f:
            line = f.readline()
            entry = json.loads(line)
            
            assert entry["mode"] == "manual_only"
            assert entry["patch_id"] == "test_patch_001"
            assert entry["target"] == "portfolio.leverage"
            assert entry["decision_status"] == "ACCEPTED_FOR_PROPOSAL"


def test_write_audit_log_entry_appends_to_existing(sample_candidate, safety_config):
    """Test that audit log entries are appended to existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = Path(tmpdir) / "audit.jsonl"
        safety_config.audit_log_path = audit_path
        
        decision = PromotionDecision(
            candidate=sample_candidate,
            status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
            reasons=[],
        )
        
        # Write first entry
        write_audit_log_entry(sample_candidate, decision, "manual_only", safety_config)
        
        # Write second entry
        write_audit_log_entry(sample_candidate, decision, "manual_only", safety_config)
        
        # Verify both entries exist
        with audit_path.open("r") as f:
            lines = f.readlines()
            assert len(lines) == 2


def test_write_audit_log_entry_handles_errors_gracefully(sample_candidate, safety_config):
    """Test that audit logging errors don't crash the system."""
    safety_config.audit_log_path = Path("/invalid/path/audit.jsonl")
    
    decision = PromotionDecision(
        candidate=sample_candidate,
        status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
        reasons=[],
    )
    
    # Should not raise exception
    write_audit_log_entry(sample_candidate, decision, "manual_only", safety_config)


# =============================================================================
# P1: Global Promotion Lock Tests
# =============================================================================

def test_global_lock_returns_warning_when_active(safety_config):
    """Test that check_global_promotion_lock returns warning when lock is active."""
    safety_config.global_promotion_lock = True
    
    warning = check_global_promotion_lock(safety_config)
    
    assert warning is not None
    assert "Global promotion lock" in warning
    assert "bounded_auto is disabled" in warning


def test_global_lock_returns_none_when_inactive(safety_config):
    """Test that check_global_promotion_lock returns None when lock is inactive."""
    safety_config.global_promotion_lock = False
    
    warning = check_global_promotion_lock(safety_config)
    
    assert warning is None


# =============================================================================
# Edge Cases & Robustness Tests
# =============================================================================

def test_safety_filters_are_idempotent(sample_candidate, safety_config):
    """Test that applying safety filters multiple times doesn't duplicate flags."""
    sample_candidate.patch.target = "live.api_keys"
    
    apply_safety_filters(sample_candidate, safety_config, "manual_only")
    initial_flags = len(sample_candidate.safety_flags)
    
    apply_safety_filters(sample_candidate, safety_config, "manual_only")
    final_flags = len(sample_candidate.safety_flags)
    
    assert initial_flags == final_flags


def test_multiple_violations_are_all_recorded(sample_candidate, safety_config):
    """Test that multiple violations are all recorded in safety_flags."""
    # Set up candidate to violate both blacklist and bounds
    sample_candidate.patch.target = "live.api_keys"  # Blacklisted
    sample_candidate.patch.new_value = 2.5  # Above bounds
    
    apply_safety_filters(sample_candidate, safety_config, "manual_only")
    
    assert len(sample_candidate.safety_flags) >= 2
    assert any("BLACKLIST" in f for f in sample_candidate.safety_flags)
    assert any("BOUNDS" in f for f in sample_candidate.safety_flags)


