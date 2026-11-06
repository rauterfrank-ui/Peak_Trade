#!/usr/bin/env python3
"""
G4 Telemetry Recording Script - Record PR telemetry data for Policy Critic tracking.

This script automates the process of recording PR telemetry entries in the
POLICY_CRITIC_TELEMETRY_G4.md file. It fetches PR metadata from GitHub CLI
and appends a structured markdown template for the operator to fill in.

Usage:
    python scripts/governance/g4_record_pr_telemetry.py --pr 123
    python scripts/governance/g4_record_pr_telemetry.py --pr 123 --open
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Optional


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def fetch_pr_metadata(pr_number: int) -> Optional[Dict]:
    """Fetch PR metadata from GitHub CLI.

    Args:
        pr_number: The pull request number

    Returns:
        Dictionary containing PR metadata, or None if fetch failed
    """
    fields = [
        "number",
        "title",
        "url",
        "author",
        "baseRefName",
        "headRefName",
        "changedFiles",
        "additions",
        "deletions",
    ]

    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "--json", ",".join(fields)],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to fetch PR #{pr_number}", file=sys.stderr)
        print(f"gh CLI output: {e.stderr}", file=sys.stderr)
        return None
    except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"Error: Failed to parse gh CLI response: {e}", file=sys.stderr)
        return None


def fetch_pr_checks(pr_number: int) -> str:
    """Fetch PR checks summary from GitHub CLI.

    Args:
        pr_number: The pull request number

    Returns:
        String summary of checks, or error message
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "checks", str(pr_number)], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"(checks not available: {result.stderr.strip()})"
    except subprocess.TimeoutExpired:
        return "(checks fetch timed out)"


def format_telemetry_entry(pr_metadata: Dict, checks_summary: str, entry_date: str) -> str:
    """Format a telemetry entry markdown block.

    Args:
        pr_metadata: Dictionary containing PR metadata from gh CLI
        checks_summary: String summary of PR checks
        entry_date: Date string in YYYY-MM-DD format

    Returns:
        Formatted markdown string
    """
    pr_num = pr_metadata["number"]
    title = pr_metadata["title"]
    author = pr_metadata.get("author", {}).get("login", "unknown")
    url = pr_metadata["url"]
    changed_files = pr_metadata.get("changedFiles", 0)
    additions = pr_metadata.get("additions", 0)
    deletions = pr_metadata.get("deletions", 0)

    # Truncate checks summary if too long
    checks_lines = checks_summary.split("\n")
    if len(checks_lines) > 10:
        checks_summary = "\n".join(checks_lines[:10]) + "\n... (truncated)"

    entry = f"""
## PR #{pr_num} — {entry_date}
- **Title:** {title}
- **Author:** {author}
- **URL:** {url}
- **Changed files:** {changed_files} (+{additions} -{deletions})
- **Result:** _FILL IN: PASS | WARN | BLOCK_
- **Severity:** _FILL IN: LOW | MED | HIGH | BLOCK_
- **Rules triggered:**
  - _FILL IN: RULE_KEY_1 (files: path/to/file.py)_
  - _FILL IN: RULE_KEY_2 (files: path/to/other.py)_
- **Classification:** _FILL IN: TRUE_POSITIVE | FALSE_POSITIVE | MIXED | NEEDS_REVIEW_
- **Operator action:**
  - _FILL IN: e.g., "added justification", "excluded path", "no change"_
- **Notes:**
  - _FILL IN: 1-2 bullets describing what was learned_
- **Checks summary:**
```
{checks_summary}
```

---
"""
    return entry


def append_telemetry_entry(output_file: Path, entry: str) -> None:
    """Append telemetry entry to the output file.

    Args:
        output_file: Path to the telemetry markdown file
        entry: Formatted markdown entry to append
    """
    # Create parent directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not output_file.exists():
        header = """# Policy Critic G4 Telemetry Log

Track 10-20 real PRs → False Positive Rate < 10% → Change Set 2 decision.

Each entry documents a PR's interaction with Policy Critic for ongoing tuning.

---
"""
        output_file.write_text(header)

    # Append the entry
    with output_file.open("a") as f:
        f.write(entry)


def open_pr_in_browser(pr_number: int) -> None:
    """Open PR in browser using gh CLI.

    Args:
        pr_number: The pull request number
    """
    try:
        subprocess.run(["gh", "pr", "view", str(pr_number), "--web"], timeout=5, check=False)
    except subprocess.TimeoutExpired:
        print("Warning: Opening PR in browser timed out", file=sys.stderr)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Record PR telemetry for Policy Critic G4 tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record PR #123 telemetry
  python scripts/governance/g4_record_pr_telemetry.py --pr 123

  # Record PR and open in browser
  python scripts/governance/g4_record_pr_telemetry.py --pr 123 --open

  # Use custom date
  python scripts/governance/g4_record_pr_telemetry.py --pr 123 --date 2025-12-01
""",
    )

    parser.add_argument("--pr", type=int, required=True, help="Pull request number to record")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/governance/POLICY_CRITIC_TELEMETRY_G4.md"),
        help="Output file path (default: docs/governance/POLICY_CRITIC_TELEMETRY_G4.md)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().isoformat(),
        help="Entry date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument("--open", action="store_true", help="Open PR in browser after recording")

    args = parser.parse_args()

    # Validate gh CLI
    if not check_gh_cli():
        print("Error: GitHub CLI (gh) is not installed or not authenticated", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install: https://cli.github.com/", file=sys.stderr)
        print("Authenticate: gh auth login", file=sys.stderr)
        return 1

    print(f"Fetching metadata for PR #{args.pr}...")
    pr_metadata = fetch_pr_metadata(args.pr)

    if not pr_metadata:
        return 1

    print(f"Fetching checks for PR #{args.pr}...")
    checks_summary = fetch_pr_checks(args.pr)

    print(f"Formatting telemetry entry...")
    entry = format_telemetry_entry(pr_metadata, checks_summary, args.date)

    print(f"Appending to {args.out}...")
    append_telemetry_entry(args.out, entry)

    print("")
    print("✓ Telemetry entry recorded successfully!")
    print("")
    print(f"Next steps:")
    print(f"  1. Edit {args.out}")
    print(
        f"  2. Fill in: Result, Severity, Rules triggered, Classification, Operator action, Notes"
    )
    print(
        f"  3. Commit: git add {args.out} && git commit -m 'docs(governance): add G4 telemetry for PR #{args.pr}'"
    )
    print("")

    if args.open:
        print(f"Opening PR #{args.pr} in browser...")
        open_pr_in_browser(args.pr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
