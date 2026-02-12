"""
Auto-Apply Gate for Policy Critic integration.

This module provides the critical decision point for auto-apply workflows.
It enforces the fail-closed principle: if policy critic denies or is unavailable,
auto-apply MUST be blocked.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from src.governance.learning import (
    LearnableSurfacesViolation,
    assert_surfaces_allowed,
)

from .critic import PolicyCritic
from .models import PolicyCriticInput, PolicyCriticResult, RecommendedAction, ReviewContext

logger = logging.getLogger(__name__)


class ApplyMode(str, Enum):
    """Apply modes for changes."""

    AUTO = "auto"  # Automated apply allowed
    MANUAL_ONLY = "manual_only"  # Requires manual operator action
    BLOCKED = "blocked"  # Completely blocked (hard violation)


@dataclass
class AutoApplyDecision:
    """
    Decision on whether auto-apply is allowed.

    This is the output of the policy critic gate that controls
    whether automated changes can proceed.
    """

    allowed: bool
    mode: ApplyMode
    reason: str
    decided_at: str
    policy_critic_result: Optional[Dict[str, Any]] = None
    inputs_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "allowed": self.allowed,
            "mode": self.mode.value,
            "reason": self.reason,
            "decided_at": self.decided_at,
            "policy_critic_result": self.policy_critic_result,
            "inputs_summary": self.inputs_summary,
        }


def evaluate_policy_critic_before_apply(
    diff_text: str,
    changed_files: list[str],
    context: Optional[Dict[str, Any]] = None,
    fail_closed: bool = True,
) -> AutoApplyDecision:
    """
    Evaluate policy critic and determine if auto-apply is allowed.

    This is the PRIMARY INTEGRATION POINT for bounded_auto and promotion cycles.

    Critical invariants:
    1. If policy_critic returns AUTO_APPLY_DENY, auto-apply MUST be blocked
    2. If policy_critic is unavailable/errors, auto-apply MUST be blocked (fail-closed)
    3. If policy_critic returns ALLOW, auto-apply MAY proceed (hard gates still apply)

    Args:
        diff_text: Unified diff or patch text
        changed_files: List of changed file paths
        context: Optional context dict with:
            - run_id: str
            - source: str (e.g., "bounded_auto", "promotion_cycle")
            - justification: str (optional)
            - test_plan: str (optional)
            - environment: str (optional)
        fail_closed: If True (default), errors result in MANUAL_ONLY

    Returns:
        AutoApplyDecision with allowed flag, mode, and detailed reasoning

    Example:
        >>> decision = evaluate_policy_critic_before_apply(
        ...     diff_text=patch_content,
        ...     changed_files=["config.toml"],
        ...     context={"run_id": "promo-123", "source": "bounded_auto"}
        ... )
        >>> if not decision.allowed:
        ...     logger.warning(f"Auto-apply blocked: {decision.reason}")
        ...     return manual_review_required(decision)
    """
    decided_at = datetime.utcnow().isoformat() + "Z"
    context = context or {}

    # Build inputs summary (for audit trail)
    inputs_summary = {
        "changed_files_count": len(changed_files),
        "changed_files": changed_files[:10],  # Limit to first 10
        "diff_size_bytes": len(diff_text),
        "context_keys": list(context.keys()),
        "source": context.get("source", "unknown"),
        "run_id": context.get("run_id"),
    }

    # Learnable surfaces gate: when context signals learning (layer_id or
    # requested_surfaces present), deny unless both are explicit and fully allowed.
    # Missing surfaces list => treat as __unknown__ and deny. Skip gate when neither
    # is in context (backward compatible for non-learning auto-apply).
    if "layer_id" in context or "requested_surfaces" in context:
        layer_id = context.get("layer_id")
        requested_surfaces = context.get("requested_surfaces")
        if layer_id is None or requested_surfaces is None:
            layer_id = "L0"
            requested_surfaces = ["__unknown__"]  # Force deny when not explicit
        try:
            assert_surfaces_allowed(layer_id, list(requested_surfaces))
        except LearnableSurfacesViolation as e:
            logger.warning("Learnable surfaces gate: %s", e)
            return AutoApplyDecision(
                allowed=False,
                mode=ApplyMode.MANUAL_ONLY,
                reason=f"Learnable surfaces not allowed: {e}",
                decided_at=decided_at,
                policy_critic_result=None,
                inputs_summary={
                    **inputs_summary,
                    "learnable_surfaces_violation": str(e),
                    "layer_id": layer_id,
                    "requested_surfaces": list(requested_surfaces),
                },
            )
        except ValueError as e:
            logger.warning("Learnable surfaces gate (invalid layer): %s", e)
            return AutoApplyDecision(
                allowed=False,
                mode=ApplyMode.MANUAL_ONLY,
                reason=f"Learnable surfaces gate: {e}",
                decided_at=decided_at,
                policy_critic_result=None,
                inputs_summary={
                    **inputs_summary,
                    "learnable_surfaces_violation": str(e),
                },
            )

    try:
        # Build review context
        review_context = None
        if context:
            review_context = ReviewContext(
                justification=context.get("justification"),
                test_plan=context.get("test_plan"),
                author=context.get("author"),
                related_issue=context.get("related_issue"),
            )

        # Create input
        input_data = PolicyCriticInput(
            diff=diff_text,
            changed_files=changed_files,
            context=review_context,
        )

        # Run policy critic
        critic = PolicyCritic()
        result = critic.review(input_data)

        # Map result to decision
        return _map_critic_result_to_decision(
            result=result,
            decided_at=decided_at,
            inputs_summary=inputs_summary,
        )

    except Exception as e:
        logger.error(f"Policy critic evaluation failed: {e}", exc_info=True)

        if fail_closed:
            # FAIL-CLOSED: Error → MANUAL_ONLY
            return AutoApplyDecision(
                allowed=False,
                mode=ApplyMode.MANUAL_ONLY,
                reason=f"Policy critic evaluation failed (fail-closed): {str(e)}",
                decided_at=decided_at,
                policy_critic_result=None,
                inputs_summary=inputs_summary,
            )
        else:
            # Fail-open (NOT RECOMMENDED, only for testing)
            logger.warning("FAIL-OPEN mode: allowing auto-apply despite error")
            return AutoApplyDecision(
                allowed=True,
                mode=ApplyMode.AUTO,
                reason=f"Policy critic failed but fail-open mode enabled: {str(e)}",
                decided_at=decided_at,
                policy_critic_result=None,
                inputs_summary=inputs_summary,
            )


def _map_critic_result_to_decision(
    result: PolicyCriticResult,
    decided_at: str,
    inputs_summary: Dict[str, Any],
) -> AutoApplyDecision:
    """
    Map PolicyCriticResult to AutoApplyDecision.

    This enforces the core policy:
    - AUTO_APPLY_DENY → blocked
    - REVIEW_REQUIRED → manual only
    - ALLOW → may proceed (but hard gates still apply)
    """
    policy_critic_dict = result.to_canonical_dict()

    if result.recommended_action == RecommendedAction.AUTO_APPLY_DENY:
        return AutoApplyDecision(
            allowed=False,
            mode=ApplyMode.BLOCKED,
            reason=f"Policy critic DENIED auto-apply: {result.summary}",
            decided_at=decided_at,
            policy_critic_result=policy_critic_dict,
            inputs_summary=inputs_summary,
        )

    elif result.recommended_action == RecommendedAction.REVIEW_REQUIRED:
        return AutoApplyDecision(
            allowed=False,
            mode=ApplyMode.MANUAL_ONLY,
            reason=f"Policy critic requires manual review: {result.summary}",
            decided_at=decided_at,
            policy_critic_result=policy_critic_dict,
            inputs_summary=inputs_summary,
        )

    else:  # ALLOW
        return AutoApplyDecision(
            allowed=True,
            mode=ApplyMode.AUTO,
            reason=f"Policy critic allows auto-apply: {result.summary}",
            decided_at=decided_at,
            policy_critic_result=policy_critic_dict,
            inputs_summary=inputs_summary,
        )


def persist_decision_to_report(
    report_path: Path,
    decision: AutoApplyDecision,
) -> None:
    """
    Persist auto-apply decision to existing report JSON.

    Adds or updates the 'governance' section with:
    - policy_critic: full policy critic result
    - auto_apply_decision: decision metadata

    Args:
        report_path: Path to existing report JSON file
        decision: AutoApplyDecision to persist

    Raises:
        FileNotFoundError: If report doesn't exist
        ValueError: If report is not valid JSON
    """
    # Load existing report
    with open(report_path, "r") as f:
        report = json.load(f)

    # Ensure governance section exists
    if "governance" not in report:
        report["governance"] = {}

    # Add policy critic result
    if decision.policy_critic_result:
        report["governance"]["policy_critic"] = decision.policy_critic_result

    # Add auto-apply decision
    report["governance"]["auto_apply_decision"] = {
        "allowed": decision.allowed,
        "mode": decision.mode.value,
        "reason": decision.reason,
        "decided_at": decision.decided_at,
        "inputs_summary": decision.inputs_summary,
    }

    # Write back
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Persisted auto-apply decision to {report_path}")


def should_deny_auto_apply(decision: AutoApplyDecision) -> bool:
    """
    Check if auto-apply should be denied.

    Simple helper that returns True if auto-apply is not allowed.
    Use this in conditional logic to block automated changes.

    Args:
        decision: AutoApplyDecision from evaluate_policy_critic_before_apply

    Returns:
        True if auto-apply should be denied, False if it may proceed
    """
    return not decision.allowed
