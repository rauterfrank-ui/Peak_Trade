"""
Safety filters and validation for the Promotion Loop.

This module implements P0 (critical) and P1 (important) safety features:
- P0: Blacklist checking, bounds validation, bounded_auto guardrails
- P1: Audit logging, global promotion lock

P0 violations prevent auto-promotion in bounded_auto mode.
P1 features add governance layers but don't block manual_only reviews.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import DecisionStatus, PromotionCandidate, PromotionDecision
from .policy import AutoApplyBounds


class SafetyConfig:
    """
    Configuration for safety features loaded from promotion_loop_config.toml.
    """
    
    def __init__(
        self,
        blacklist_targets: Optional[List[str]] = None,
        blacklist_tags: Optional[List[str]] = None,
        bounds: Optional[Dict[str, AutoApplyBounds]] = None,
        global_promotion_lock: bool = False,
        audit_log_path: Optional[Path] = None,
        min_confidence_for_auto_apply: float = 0.80,
    ):
        self.blacklist_targets = blacklist_targets or []
        self.blacklist_tags = blacklist_tags or []
        self.bounds = bounds or {}
        self.global_promotion_lock = global_promotion_lock
        self.audit_log_path = audit_log_path or Path("reports/promotion_audit/promotion_audit.jsonl")
        self.min_confidence_for_auto_apply = min_confidence_for_auto_apply


# =============================================================================
# P0: Critical Safety Features
# =============================================================================

def check_blacklist(candidate: PromotionCandidate, config: SafetyConfig) -> List[str]:
    """
    P0: Check if candidate violates blacklist rules.
    
    Blacklist checks:
    1. Target matches blacklist patterns (e.g., live.api_keys*)
    2. Tags intersect with blacklist tags (e.g., r_and_d, experimental)
    
    Returns:
        List of violation reasons (empty if no violations)
    """
    violations = []
    
    # Check target against blacklist patterns
    target = candidate.patch.target
    for blacklist_pattern in config.blacklist_targets:
        # Support prefix matching (e.g., "live.api_keys" matches "live.api_keys.binance")
        if target.startswith(blacklist_pattern):
            violations.append(f"P0_BLACKLIST: Target '{target}' matches blacklisted pattern '{blacklist_pattern}'")
            break
    
    # Check tags against blacklist
    if config.blacklist_tags:
        blacklisted_tags = set(candidate.tags) & set(config.blacklist_tags)
        if blacklisted_tags:
            violations.append(f"P0_BLACKLIST: Tags {blacklisted_tags} are blacklisted")
    
    return violations


def check_bounds(candidate: PromotionCandidate, config: SafetyConfig) -> List[str]:
    """
    P0: Check if candidate violates bounds (min/max/max_step).
    
    Bounds checks for numeric patches:
    1. Value is within [min_value, max_value] range
    2. Step size <= max_step (if old_value is numeric)
    
    Returns:
        List of violation reasons (empty if no violations)
    """
    violations = []
    
    # Only check numeric patches
    if not isinstance(candidate.patch.new_value, (int, float)):
        return violations
    
    new_val = float(candidate.patch.new_value)
    old_val = candidate.patch.old_value
    
    # Find applicable bounds based on tags
    bounds: Optional[AutoApplyBounds] = None
    for tag in candidate.tags:
        if tag in config.bounds:
            bounds = config.bounds[tag]
            break
    
    if bounds is None:
        # No bounds configured for this parameter type
        return violations
    
    # Check min/max range
    if new_val < bounds.min_value:
        violations.append(
            f"P0_BOUNDS: New value {new_val} < min_value {bounds.min_value} (tag: {tag})"
        )
    elif new_val > bounds.max_value:
        violations.append(
            f"P0_BOUNDS: New value {new_val} > max_value {bounds.max_value} (tag: {tag})"
        )
    
    # Check max_step
    if isinstance(old_val, (int, float)):
        step = abs(new_val - float(old_val))
        if step > bounds.max_step:
            violations.append(
                f"P0_BOUNDS: Step {step:.3f} > max_step {bounds.max_step} (tag: {tag})"
            )
    
    return violations


def check_bounded_auto_guardrails(
    candidate: PromotionCandidate,
    config: SafetyConfig,
    mode: str,
) -> List[str]:
    """
    P0: Check bounded_auto specific guardrails.
    
    Guardrails for bounded_auto mode:
    1. Global promotion lock must be OFF
    2. No P0 safety_flags present
    3. Confidence >= min_confidence_for_auto_apply
    4. Not marked as R&D tier (if such field exists)
    
    Returns:
        List of violation reasons (empty if no violations)
    """
    violations = []
    
    # Only enforce for bounded_auto mode
    if mode != "bounded_auto":
        return violations
    
    # Check global lock
    if config.global_promotion_lock:
        violations.append("P0_GUARDRAIL: Global promotion lock is active")
    
    # Check for existing P0 violations
    p0_flags = [f for f in candidate.safety_flags if f.startswith("P0_")]
    if p0_flags:
        violations.append(f"P0_GUARDRAIL: Candidate has P0 violations: {p0_flags}")
    
    # Check confidence threshold
    confidence = candidate.patch.confidence_score
    if confidence is None or confidence < config.min_confidence_for_auto_apply:
        conf_str = f"{confidence:.3f}" if confidence is not None else "None"
        violations.append(
            f"P0_GUARDRAIL: Confidence {conf_str} < min_threshold {config.min_confidence_for_auto_apply}"
        )
    
    # Check R&D tier (check tags for r_and_d or experimental)
    if "r_and_d" in candidate.tags or "experimental" in candidate.tags:
        violations.append("P0_GUARDRAIL: Candidate is R&D/experimental tier")
    
    # Check if patch metadata indicates not live-ready
    if candidate.patch.meta.get("is_live_ready") is False:
        violations.append("P0_GUARDRAIL: Patch metadata indicates not live-ready")
    
    return violations


def apply_safety_filters(
    candidate: PromotionCandidate,
    config: SafetyConfig,
    mode: str = "manual_only",
) -> PromotionCandidate:
    """
    Apply all P0 safety filters to a candidate and update safety_flags.
    
    This function is idempotent - can be called multiple times.
    
    Args:
        candidate: Promotion candidate to check
        config: Safety configuration
        mode: Promotion mode (manual_only, bounded_auto, disabled)
    
    Returns:
        Modified candidate with safety_flags updated
    """
    # Collect all violations
    violations = []
    
    violations.extend(check_blacklist(candidate, config))
    violations.extend(check_bounds(candidate, config))
    violations.extend(check_bounded_auto_guardrails(candidate, config, mode))
    
    # Update safety_flags (append only new violations)
    for violation in violations:
        if violation not in candidate.safety_flags:
            candidate.safety_flags.append(violation)
    
    return candidate


def has_p0_violations(candidate: PromotionCandidate) -> bool:
    """
    Check if candidate has any P0 violations.
    
    Returns:
        True if candidate has P0 flags, False otherwise
    """
    return any(f.startswith("P0_") for f in candidate.safety_flags)


# =============================================================================
# P1: Important Safety Features
# =============================================================================

def write_audit_log_entry(
    candidate: PromotionCandidate,
    decision: PromotionDecision,
    mode: str,
    config: SafetyConfig,
) -> None:
    """
    P1: Write audit log entry for a promotion decision.
    
    Logs all promotion decisions (accepted and rejected) with full context.
    
    Args:
        candidate: Promotion candidate
        decision: Final promotion decision
        mode: Promotion mode (manual_only, bounded_auto, disabled)
        config: Safety configuration
    """
    try:
        # Ensure audit log directory exists
        config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build audit entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": mode,
            "patch_id": candidate.patch.id,
            "target": candidate.patch.target,
            "old_value": candidate.patch.old_value,
            "new_value": candidate.patch.new_value,
            "confidence_score": candidate.patch.confidence_score,
            "source_experiment_id": candidate.patch.source_experiment_id,
            "decision_status": decision.status.value,
            "decision_reasons": decision.reasons,
            "safety_flags": candidate.safety_flags,
            "tags": candidate.tags,
            "eligible_for_live": candidate.eligible_for_live,
            "meta": candidate.patch.meta,
        }
        
        # Append to JSONL file (one JSON object per line)
        with config.audit_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    except Exception as e:
        # Audit logging failures should not crash the promotion loop
        # Log warning but continue
        print(f"[safety] WARNING: Failed to write audit log entry: {e}")


def check_global_promotion_lock(config: SafetyConfig) -> Optional[str]:
    """
    P1: Check if global promotion lock is active.
    
    Returns:
        Warning message if lock is active, None otherwise
    """
    if config.global_promotion_lock:
        return (
            "WARNING: Global promotion lock is active. "
            "bounded_auto is disabled. Only manual changes are allowed."
        )
    return None


# =============================================================================
# Utility Functions
# =============================================================================

def load_safety_config_from_toml(config_path: Path) -> SafetyConfig:
    """
    Load SafetyConfig from TOML file.
    
    Args:
        config_path: Path to promotion_loop_config.toml
    
    Returns:
        SafetyConfig instance
    """
    import toml
    
    try:
        data = toml.load(config_path)
    except Exception as e:
        print(f"[safety] WARNING: Failed to load config from {config_path}: {e}")
        print("[safety] Using default safety config")
        return SafetyConfig()
    
    # Extract safety section
    safety_section = data.get("promotion_loop", {}).get("safety", {})
    bounds_section = data.get("promotion_loop", {}).get("bounds", {})
    governance_section = data.get("promotion_loop", {}).get("governance", {})
    
    # Build bounds dict
    bounds = {}
    if "leverage_min" in bounds_section:
        bounds["leverage"] = AutoApplyBounds(
            min_value=bounds_section.get("leverage_min", 1.0),
            max_value=bounds_section.get("leverage_max", 2.0),
            max_step=bounds_section.get("leverage_max_step", 0.25),
        )
    if "trigger_delay_min" in bounds_section:
        bounds["trigger"] = AutoApplyBounds(
            min_value=bounds_section.get("trigger_delay_min", 3.0),
            max_value=bounds_section.get("trigger_delay_max", 15.0),
            max_step=bounds_section.get("trigger_delay_max_step", 2.0),
        )
    if "macro_weight_min" in bounds_section:
        bounds["macro"] = AutoApplyBounds(
            min_value=bounds_section.get("macro_weight_min", 0.0),
            max_value=bounds_section.get("macro_weight_max", 0.8),
            max_step=bounds_section.get("macro_weight_max_step", 0.1),
        )
    
    return SafetyConfig(
        blacklist_targets=safety_section.get("auto_apply_blacklist", []),
        blacklist_tags=safety_section.get("blacklist_tags", []),
        bounds=bounds,
        global_promotion_lock=governance_section.get("global_promotion_lock", False),
        min_confidence_for_auto_apply=safety_section.get("min_confidence_for_auto_apply", 0.80),
    )
