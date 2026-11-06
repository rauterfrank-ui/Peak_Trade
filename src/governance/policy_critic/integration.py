"""
Integration helpers for Policy Critic in bounded_auto / auto-apply workflows.

This module provides helper functions for integrating the Policy Critic
into automated change approval workflows (future bounded_auto system).
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

from .models import PolicyCriticResult, RecommendedAction, Severity


def run_policy_critic_subprocess(
    diff_file: Path,
    changed_files: list[str],
    context_json: Optional[Path] = None,
) -> Tuple[PolicyCriticResult, int]:
    """
    Run policy critic as subprocess and parse results.

    Args:
        diff_file: Path to diff file
        changed_files: List of changed file paths
        context_json: Optional path to context JSON file

    Returns:
        Tuple of (PolicyCriticResult parsed from JSON, exit_code)

    Raises:
        RuntimeError: If policy critic script fails to run
        ValueError: If output cannot be parsed
    """
    import sys

    cmd = [
        sys.executable,
        "scripts/run_policy_critic.py",
        "--diff-file",
        str(diff_file),
        "--changed-files",
        ",".join(changed_files),
        "--json-only",
    ]

    if context_json:
        cmd.extend(["--context-json", str(context_json)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit
            cwd=Path(__file__).parent.parent.parent.parent,  # repo root
        )

        # Parse JSON output
        output = json.loads(result.stdout)

        # Reconstruct PolicyCriticResult from dict
        # (This is a simplified reconstruction; full reconstruction would need all nested objects)
        parsed_result = _dict_to_result(output)

        return parsed_result, result.returncode

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse policy critic output: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to run policy critic: {e}") from e


def _dict_to_result(data: Dict) -> PolicyCriticResult:
    """Convert dict back to PolicyCriticResult (simplified)."""
    from .models import Evidence, PolicyCriticResult, Violation

    violations = []
    for v_data in data.get("violations", []):
        evidence = [
            Evidence(
                file_path=e["file_path"],
                line_range=e.get("line_range"),
                snippet=e.get("snippet"),
                pattern=e.get("pattern"),
            )
            for e in v_data.get("evidence", [])
        ]

        violations.append(
            Violation(
                rule_id=v_data["rule_id"],
                severity=Severity(v_data["severity"]),
                message=v_data["message"],
                evidence=evidence,
                suggested_fix=v_data.get("suggested_fix"),
            )
        )

    return PolicyCriticResult(
        max_severity=Severity(data["max_severity"]),
        recommended_action=RecommendedAction(data["recommended_action"]),
        violations=violations,
        minimum_test_plan=data.get("minimum_test_plan", []),
        operator_questions=data.get("operator_questions", []),
        summary=data.get("summary", ""),
    )


def should_deny_auto_apply(result: PolicyCriticResult) -> bool:
    """
    Determine if auto-apply should be denied based on policy critic result.

    This is the key integration point for bounded_auto:
    - If recommended_action is AUTO_APPLY_DENY, auto-apply MUST be blocked
    - This function enforces the "can only brake, not accelerate" principle

    Args:
        result: Policy critic result

    Returns:
        True if auto-apply must be denied, False otherwise
    """
    return result.recommended_action == RecommendedAction.AUTO_APPLY_DENY


def merge_policy_result_into_report(
    existing_report: Dict, policy_result: PolicyCriticResult
) -> Dict:
    """
    Merge policy critic result into existing promotion/bounded_auto report.

    Args:
        existing_report: Existing report dict (e.g., from bounded_auto)
        policy_result: Policy critic result

    Returns:
        Updated report with policy_critic section added
    """
    existing_report["policy_critic"] = policy_result.to_dict()

    # Add top-level auto_apply_allowed field (conservative: deny if critic says so)
    if "auto_apply_allowed" in existing_report:
        # If it was already False, keep it False
        # If it was True, update based on policy critic
        if existing_report["auto_apply_allowed"]:
            existing_report["auto_apply_allowed"] = not should_deny_auto_apply(policy_result)
    else:
        # Set initial value
        existing_report["auto_apply_allowed"] = not should_deny_auto_apply(policy_result)

    return existing_report


# Example usage for future bounded_auto integration:
"""
# In bounded_auto promotion workflow:

from src.governance.policy_critic.integration import (
    run_policy_critic_subprocess,
    should_deny_auto_apply,
    merge_policy_result_into_report,
)

# Generate diff for proposed change
diff_file = Path("/tmp/proposed_change.diff")
changed_files = ["config.toml", "src/strategies/new_strategy.py"]

# Run policy critic
policy_result, exit_code = run_policy_critic_subprocess(diff_file, changed_files)

# Check if auto-apply should be denied
if should_deny_auto_apply(policy_result):
    logger.warning("Auto-apply denied by policy critic")
    # Force manual review
    require_manual_review = True
else:
    logger.info("Policy critic allows auto-apply to proceed")

# Merge into promotion report
promotion_report = {...}  # Existing report
promotion_report = merge_policy_result_into_report(promotion_report, policy_result)

# Save report with policy critic results
save_report(promotion_report)
"""
