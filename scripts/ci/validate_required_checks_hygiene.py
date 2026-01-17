#!/usr/bin/env python3
"""
Required Checks Hygiene Validator

Purpose:
  Validates that all required status checks are reliably produced by
  always-on PR workflows (no PR-level path filtering).

Problem Context (Phase 5C):
  Branch protection "required status checks" can block PRs if the
  workflow is path-filtered at the `on.pull_request.paths` level.
  When a PR doesn't match the paths filter, no check-run is created,
  and GitHub blocks the merge (even with admin override).

Solution:
  This validator ensures that:
  1) Every required context is producible by at least one PR workflow
  2) No required context relies exclusively on path-filtered workflows
  3) Findings are audit-stable with clear remediation guidance

Usage:
  python scripts/ci/validate_required_checks_hygiene.py \\
    --config config/ci/required_status_checks.json \\
    --workflows .github/workflows \\
    --strict

Exit Codes:
  0: All required checks are hygiene-compliant
  2: Hygiene violations found (required checks unreliable)

Phase: 5D
Date: 2026-01-12
Owner: ops
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


class WorkflowAnalyzer:
    """Analyzes GitHub Actions workflows for check context generation."""

    def __init__(self, workflow_dir: Path):
        self.workflow_dir = workflow_dir
        self.workflows: List[Dict[str, Any]] = []

    def load_workflows(self) -> None:
        """Load and parse all workflow YAML files."""
        patterns = ["*.yml", "*.yaml"]
        workflow_files = []
        for pattern in patterns:
            workflow_files.extend(self.workflow_dir.glob(pattern))

        for wf_file in sorted(workflow_files):
            try:
                with open(wf_file, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if content:
                        self.workflows.append(
                            {
                                "file": wf_file.name,
                                "path": wf_file,
                                "content": content,
                            }
                        )
            except Exception as e:
                print(f"WARNING: Failed to parse {wf_file.name}: {e}", file=sys.stderr)

    def extract_pr_workflows(self) -> List[Dict[str, Any]]:
        """Extract workflows that trigger on pull_request events."""
        pr_workflows = []

        for wf in self.workflows:
            content = wf["content"]

            # PyYAML quirk: 'on' is a reserved word and may be parsed as boolean True
            # Check both 'on' and True keys
            on_config = content.get("on") or content.get(True) or {}

            # Normalize 'on' to dict (can be string, list, or dict)
            if isinstance(on_config, str):
                on_config = {on_config: True}
            elif isinstance(on_config, list):
                on_config = {k: True for k in on_config}

            if not isinstance(on_config, dict):
                continue

            # Check if pull_request trigger exists
            if "pull_request" not in on_config:
                continue

            pr_config = on_config["pull_request"]

            # Determine if PR-level paths filtering is present
            has_pr_paths = False
            if isinstance(pr_config, dict):
                has_pr_paths = "paths" in pr_config or "paths-ignore" in pr_config

            # Extract workflow name
            workflow_name = content.get("name", wf["file"].replace(".yml", "").replace(".yaml", ""))

            # Extract jobs
            jobs = content.get("jobs", {})
            job_list = []
            for job_id, job_config in jobs.items():
                if isinstance(job_config, dict):
                    job_display = job_config.get("name", job_id)
                    job_list.append(
                        {
                            "job_id": job_id,
                            "job_display": job_display,
                        }
                    )

            pr_workflows.append(
                {
                    "file": wf["file"],
                    "workflow_name": workflow_name,
                    "has_pr_paths": has_pr_paths,
                    "jobs": job_list,
                }
            )

        return pr_workflows

    def generate_check_candidates(self, workflow: Dict[str, Any], job: Dict[str, Any]) -> List[str]:
        """
        Generate possible check context strings for a workflow/job combination.

        GitHub Actions check contexts can appear as:
        - job_display (e.g., "tests (3.11)")
        - workflow_name (e.g., "CI")
        - "workflow_name / job_display" (e.g., "CI / tests (3.11)")
        """
        workflow_name = workflow["workflow_name"]
        job_display = job["job_display"]

        candidates = [
            job_display,
            workflow_name,
            f"{workflow_name} / {job_display}",
        ]

        # Deduplicate
        return list(dict.fromkeys(candidates))


class RequiredChecksValidator:
    """Validates required checks hygiene against workflow definitions."""

    def __init__(self, config_path: Path, workflow_dir: Path, strict: bool = False):
        self.config_path = config_path
        self.workflow_dir = workflow_dir
        self.strict = strict
        self.config: Dict[str, Any] = {}
        self.analyzer = WorkflowAnalyzer(workflow_dir)
        self.findings: List[Dict[str, str]] = []

    def load_config(self) -> None:
        """Load required status checks configuration."""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def validate(self) -> bool:
        """
        Validate all required checks.

        Returns:
          True if all checks pass, False if hygiene violations found.
        """
        self.load_config()
        self.analyzer.load_workflows()
        pr_workflows = self.analyzer.extract_pr_workflows()

        required_contexts = self.config.get("required_contexts", [])
        ignored_contexts = set(self.config.get("ignored_contexts", []))

        for context in required_contexts:
            if context in ignored_contexts:
                continue

            self._validate_context(context, pr_workflows)

        return len(self.findings) == 0

    def _validate_context(self, context: str, pr_workflows: List[Dict[str, Any]]) -> None:
        """Validate a single required context."""
        # Find all matching workflows/jobs
        matches = []
        for wf in pr_workflows:
            for job in wf["jobs"]:
                candidates = self.analyzer.generate_check_candidates(wf, job)
                if context in candidates:
                    matches.append(
                        {
                            "workflow_file": wf["file"],
                            "workflow_name": wf["workflow_name"],
                            "job_display": job["job_display"],
                            "has_pr_paths": wf["has_pr_paths"],
                        }
                    )

        if not matches:
            # FAIL: Required context not produced by any PR workflow
            self.findings.append(
                {
                    "context": context,
                    "status": "FAIL",
                    "reason": "Required context not produced by any PR workflow",
                    "remediation": f"Add a PR-triggered workflow/job that produces '{context}' check",
                }
            )
            return

        # Check if all matches are path-filtered
        always_on_matches = [m for m in matches if not m["has_pr_paths"]]

        if not always_on_matches:
            # FAIL: Context only produced by path-filtered workflows
            example = matches[0]
            self.findings.append(
                {
                    "context": context,
                    "status": "FAIL",
                    "reason": "Required context only produced by path-filtered workflows",
                    "remediation": f"Remove PR-level 'paths' filter from workflow '{example['workflow_file']}' "
                    f"and use internal change detection (dorny/paths-filter) instead",
                }
            )
            return

        # PASS: Context is produced by at least one always-on workflow
        # (No findings added for passing checks)

    def print_report(self) -> None:
        """Print validation report."""
        print("=" * 80)
        print("Required Checks Hygiene Validation")
        print("=" * 80)
        print()
        print(f"Config:    {self.config_path}")
        print(f"Workflows: {self.workflow_dir}")
        print(f"Mode:      {'STRICT' if self.strict else 'NORMAL'}")
        print()

        required_count = len(self.config.get("required_contexts", []))
        findings_count = len(self.findings)

        if findings_count == 0:
            print(f"✅ SUCCESS: All {required_count} required checks are hygiene-compliant")
            print()
            print("All required status checks are produced by always-on PR workflows.")
            print("No path-filtering detected on required checks.")
            return

        print(f"❌ FAILURE: {findings_count} hygiene violation(s) found")
        print()
        print("Findings:")
        print("-" * 80)
        print(f"{'Context':<40} {'Status':<10} {'Issue':<30}")
        print("-" * 80)

        for finding in self.findings:
            context = finding["context"]
            status = finding["status"]
            reason = finding["reason"]
            print(f"{context:<40} {status:<10} {reason:<30}")

        print("-" * 80)
        print()
        print("Remediation:")
        print()
        for i, finding in enumerate(self.findings, 1):
            print(f"{i}. Context: {finding['context']}")
            print(f"   Issue:  {finding['reason']}")
            print(f"   Fix:    {finding['remediation']}")
            print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate required status checks hygiene (Phase 5D)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate with default config
  python scripts/ci/validate_required_checks_hygiene.py

  # Strict mode (fail on warnings)
  python scripts/ci/validate_required_checks_hygiene.py --strict

  # Custom config location
  python scripts/ci/validate_required_checks_hygiene.py \\
    --config config/ci/required_status_checks.json \\
    --workflows .github/workflows
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/ci/required_status_checks.json"),
        help="Path to required status checks config (default: config/ci/required_status_checks.json)",
    )

    parser.add_argument(
        "--workflows",
        type=Path,
        default=Path(".github/workflows"),
        help="Path to workflows directory (default: .github/workflows)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode (treat warnings as failures)",
    )

    args = parser.parse_args()

    # Validate paths
    if not args.config.exists():
        print(f"ERROR: Config file not found: {args.config}", file=sys.stderr)
        return 2

    if not args.workflows.exists() or not args.workflows.is_dir():
        print(f"ERROR: Workflows directory not found: {args.workflows}", file=sys.stderr)
        return 2

    # Run validation
    validator = RequiredChecksValidator(
        config_path=args.config,
        workflow_dir=args.workflows,
        strict=args.strict,
    )

    try:
        success = validator.validate()
        validator.print_report()

        return 0 if success else 2

    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
