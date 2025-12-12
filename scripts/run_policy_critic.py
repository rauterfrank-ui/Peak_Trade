#!/usr/bin/env python3
"""
Policy Critic CLI - Review changes against governance policies.

Usage:
    python scripts/run_policy_critic.py --diff-file changes.diff --changed-files "a.py,b.py"
    git diff | python scripts/run_policy_critic.py --diff-stdin --changed-files "$(git diff --name-only)"
    python scripts/run_policy_critic.py --diff-file changes.diff --changed-files "a.py" --context-json context.json

Exit codes:
    0: No blocking violations (ALLOW or REVIEW_REQUIRED)
    2: Blocking violations (AUTO_APPLY_DENY)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from governance.policy_critic.critic import PolicyCritic
from governance.policy_critic.models import PolicyCriticInput, ReviewContext


def load_diff(diff_file: Optional[str], diff_stdin: bool) -> str:
    """Load diff from file or stdin."""
    if diff_stdin:
        return sys.stdin.read()
    elif diff_file:
        with open(diff_file, "r") as f:
            return f.read()
    else:
        raise ValueError("Must provide either --diff-file or --diff-stdin")


def load_context(context_json: Optional[str]) -> Optional[ReviewContext]:
    """Load context from JSON file."""
    if not context_json:
        return None

    with open(context_json, "r") as f:
        data = json.load(f)

    return ReviewContext(
        justification=data.get("justification"),
        test_plan=data.get("test_plan"),
        author=data.get("author"),
        related_issue=data.get("related_issue"),
    )


def print_human_summary(result):
    """Print human-readable summary to stderr."""
    print("=" * 60, file=sys.stderr)
    print("POLICY CRITIC REVIEW", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Max Severity: {result.max_severity.value}", file=sys.stderr)
    print(f"Recommended Action: {result.recommended_action.value}", file=sys.stderr)
    print(f"Violations: {len(result.violations)}", file=sys.stderr)
    print(file=sys.stderr)

    if result.violations:
        print("VIOLATIONS:", file=sys.stderr)
        for v in result.violations:
            print(f"  [{v.severity.value}] {v.rule_id}: {v.message}", file=sys.stderr)
            if v.evidence:
                for e in v.evidence[:2]:  # Limit to first 2 evidence items
                    print(f"    → {e.file_path}", file=sys.stderr)
        print(file=sys.stderr)

    if result.minimum_test_plan:
        print("MINIMUM TEST PLAN:", file=sys.stderr)
        for item in result.minimum_test_plan:
            print(f"  • {item}", file=sys.stderr)
        print(file=sys.stderr)

    if result.operator_questions:
        print("OPERATOR QUESTIONS:", file=sys.stderr)
        for q in result.operator_questions:
            print(f"  ? {q}", file=sys.stderr)
        print(file=sys.stderr)

    print("SUMMARY:", file=sys.stderr)
    print(f"  {result.summary}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Review changes against governance policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Diff input
    diff_group = parser.add_mutually_exclusive_group(required=True)
    diff_group.add_argument("--diff-file", help="Path to diff file")
    diff_group.add_argument("--diff-stdin", action="store_true", help="Read diff from stdin")

    # Changed files
    parser.add_argument(
        "--changed-files",
        required=True,
        help="Comma-separated list of changed files",
    )

    # Optional context
    parser.add_argument(
        "--context-json",
        help="Path to JSON file with review context (justification, test_plan, etc.)",
    )

    # Output format
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output only JSON (no human summary to stderr)",
    )

    args = parser.parse_args()

    # Load inputs
    try:
        diff = load_diff(args.diff_file, args.diff_stdin)
        changed_files = [f.strip() for f in args.changed_files.split(",") if f.strip()]
        context = load_context(args.context_json)
    except Exception as e:
        print(f"Error loading input: {e}", file=sys.stderr)
        return 1

    # Create input
    input_data = PolicyCriticInput(
        diff=diff,
        changed_files=changed_files,
        context=context,
    )

    # Run critic
    critic = PolicyCritic()
    result = critic.review(input_data)

    # Output JSON to stdout
    print(json.dumps(result.to_dict(), indent=2))

    # Output human summary to stderr (unless --json-only)
    if not args.json_only:
        print_human_summary(result)

    # Exit with appropriate code
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
