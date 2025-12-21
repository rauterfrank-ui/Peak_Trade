#!/usr/bin/env python3
"""
G4 Telemetry Rollup Script - Analyze and summarize Policy Critic telemetry data.

This script parses the POLICY_CRITIC_TELEMETRY_G4.md file and generates
summary statistics including FP rate, total PRs, blocks, and rule frequencies.

Usage:
    python scripts/governance/g4_rollup_telemetry.py
    python scripts/governance/g4_rollup_telemetry.py --out docs/governance/POLICY_CRITIC_G4_ROLLUP.md
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple


class TelemetryEntry:
    """Represents a single PR telemetry entry."""

    def __init__(self):
        self.pr_number: int = 0
        self.date: str = ""
        self.title: str = ""
        self.result: str = ""
        self.severity: str = ""
        self.rules: List[str] = []
        self.classification: str = ""
        self.operator_action: List[str] = []
        self.notes: List[str] = []


def parse_telemetry_file(file_path: Path) -> List[TelemetryEntry]:
    """Parse the telemetry markdown file and extract entries.

    Args:
        file_path: Path to the telemetry markdown file

    Returns:
        List of TelemetryEntry objects
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return []

    content = file_path.read_text()
    entries = []

    # Split by PR entries (## PR #...)
    pr_sections = re.split(r"^## PR #", content, flags=re.MULTILINE)

    for section in pr_sections[1:]:  # Skip header
        entry = TelemetryEntry()

        # Extract PR number and date from header
        header_match = re.match(r"(\d+)\s*—\s*(\S+)", section)
        if header_match:
            entry.pr_number = int(header_match.group(1))
            entry.date = header_match.group(2)

        # Extract fields
        if title_match := re.search(r"\*\*Title:\*\*\s*(.+?)(?=\n|$)", section):
            entry.title = title_match.group(1).strip()

        if result_match := re.search(r"\*\*Result:\*\*\s*(\w+)", section):
            entry.result = result_match.group(1).strip()

        if severity_match := re.search(r"\*\*Severity:\*\*\s*(\w+)", section):
            entry.severity = severity_match.group(1).strip()

        if classification_match := re.search(r"\*\*Classification:\*\*\s*(\w+)", section):
            entry.classification = classification_match.group(1).strip()

        # Extract rules (lines starting with "- " under "Rules triggered:")
        rules_section = re.search(r"\*\*Rules triggered:\*\*\s*\n((?:\s*[-•]\s*.+\n?)*)", section)
        if rules_section:
            for line in rules_section.group(1).split("\n"):
                # Match lines like: "  - RULE_KEY (files: ...)"
                if rule_match := re.search(r"[-•]\s*([A-Z_0-9]+)\s*\(", line):
                    entry.rules.append(rule_match.group(1))

        entries.append(entry)

    return entries


def compute_statistics(entries: List[TelemetryEntry]) -> Dict:
    """Compute summary statistics from telemetry entries.

    Args:
        entries: List of TelemetryEntry objects

    Returns:
        Dictionary containing computed statistics
    """
    total_prs = len(entries)

    # Count classifications
    classifications = Counter(e.classification for e in entries if e.classification)

    # Count results
    results = Counter(e.result for e in entries if e.result)

    # Count severities
    severities = Counter(e.severity for e in entries if e.severity)

    # Count blocks (Result: BLOCK)
    blocks = sum(1 for e in entries if e.result == "BLOCK")

    # Count rules
    all_rules = []
    for entry in entries:
        all_rules.extend(entry.rules)
    rule_frequencies = Counter(all_rules)

    # Compute FP rates (two variants)
    false_positives = classifications.get("FALSE_POSITIVE", 0)
    mixed = classifications.get("MIXED", 0)
    needs_review = classifications.get("NEEDS_REVIEW", 0)

    # FP Rate Variant 1: Exclude NEEDS_REVIEW from denominator
    classified_count = total_prs - needs_review
    fp_rate_v1 = (false_positives / classified_count * 100) if classified_count > 0 else 0.0

    # FP Rate Variant 2: Include all PRs in denominator
    fp_rate_v2 = (false_positives / total_prs * 100) if total_prs > 0 else 0.0

    return {
        "total_prs": total_prs,
        "classifications": classifications,
        "results": results,
        "severities": severities,
        "blocks": blocks,
        "rule_frequencies": rule_frequencies,
        "false_positives": false_positives,
        "mixed": mixed,
        "needs_review": needs_review,
        "classified_count": classified_count,
        "fp_rate_v1": fp_rate_v1,
        "fp_rate_v2": fp_rate_v2,
    }


def format_summary(stats: Dict) -> str:
    """Format statistics as a markdown summary.

    Args:
        stats: Dictionary containing computed statistics

    Returns:
        Formatted markdown string
    """
    summary = """# Policy Critic G4 Telemetry Rollup

## Summary Statistics

"""

    summary += f"- **Total PRs logged:** {stats['total_prs']}\n"
    summary += f"- **Real BLOCKs observed:** {stats['blocks']}\n"
    summary += "\n"

    # FP Rate section
    summary += "### False Positive Rates\n\n"
    summary += f"- **FP Rate (exclude NEEDS_REVIEW):** {stats['fp_rate_v1']:.1f}% "
    summary += f"({stats['false_positives']} FP / {stats['classified_count']} classified PRs)\n"
    summary += f"- **FP Rate (include all PRs):** {stats['fp_rate_v2']:.1f}% "
    summary += f"({stats['false_positives']} FP / {stats['total_prs']} total PRs)\n"
    summary += "\n"

    # Results breakdown
    summary += "### Results Breakdown\n\n"
    if stats["results"]:
        for result, count in stats["results"].most_common():
            pct = (count / stats["total_prs"] * 100) if stats["total_prs"] > 0 else 0
            summary += f"- **{result}:** {count} ({pct:.1f}%)\n"
    else:
        summary += "- _(no results recorded)_\n"
    summary += "\n"

    # Classification breakdown
    summary += "### Classification Breakdown\n\n"
    if stats["classifications"]:
        for classification, count in stats["classifications"].most_common():
            pct = (count / stats["total_prs"] * 100) if stats["total_prs"] > 0 else 0
            summary += f"- **{classification}:** {count} ({pct:.1f}%)\n"
    else:
        summary += "- _(no classifications recorded)_\n"
    summary += "\n"

    # Severity breakdown
    summary += "### Severity Breakdown\n\n"
    if stats["severities"]:
        for severity, count in stats["severities"].most_common():
            pct = (count / stats["total_prs"] * 100) if stats["total_prs"] > 0 else 0
            summary += f"- **{severity}:** {count} ({pct:.1f}%)\n"
    else:
        summary += "- _(no severities recorded)_\n"
    summary += "\n"

    # Top rules
    summary += "### Top Triggered Rules\n\n"
    if stats["rule_frequencies"]:
        for rule, count in stats["rule_frequencies"].most_common(10):
            summary += f"- **{rule}:** {count} occurrences\n"
    else:
        summary += "- _(no rules recorded)_\n"
    summary += "\n"

    # G4 Exit Criteria
    summary += "## G4 Exit Criteria Progress\n\n"
    pr_status = "DONE" if stats["total_prs"] >= 10 else f"IN PROGRESS ({stats['total_prs']}/10)"
    summary += f"- ✅ **10-20 PRs logged:** {pr_status}\n"
    fp_status = "DONE" if stats["fp_rate_v1"] < 10.0 else f"NOT MET ({stats['fp_rate_v1']:.1f}%)"
    summary += f"- ✅ **FP Rate < 10%:** {fp_status}\n"
    block_status = "DONE" if stats["blocks"] >= 1 else "NOT MET (0 blocks)"
    summary += f"- ✅ **At least 1 real BLOCK:** {block_status}\n"
    summary += "- ✅ **Change Set 2 decision:** _(manual review required)_\n"
    summary += "\n"

    # Recommendations
    summary += "## Recommendations\n\n"

    if stats["total_prs"] < 10:
        summary += "- Continue logging PRs (target: 10-20 PRs)\n"

    if stats["fp_rate_v1"] >= 10.0:
        summary += f"- FP rate is {stats['fp_rate_v1']:.1f}% (above 10% target)\n"
        if stats["rule_frequencies"]:
            top_rule = stats["rule_frequencies"].most_common(1)[0]
            summary += (
                f"- Review top triggered rule: **{top_rule[0]}** ({top_rule[1]} occurrences)\n"
            )

    if stats["blocks"] == 0:
        summary += "- No real BLOCKs observed yet - continue monitoring\n"

    if stats["needs_review"] > 0:
        summary += f"- {stats['needs_review']} PRs marked NEEDS_REVIEW - review and classify\n"

    summary += "\n"
    summary += "---\n"
    summary += "\n"
    summary += "_Generated by scripts/governance/g4_rollup_telemetry.py_\n"

    return summary


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze and rollup Policy Critic G4 telemetry data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Display summary to stdout
  python scripts/governance/g4_rollup_telemetry.py

  # Write summary to file
  python scripts/governance/g4_rollup_telemetry.py --out docs/governance/POLICY_CRITIC_G4_ROLLUP.md
""",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/governance/POLICY_CRITIC_TELEMETRY_G4.md"),
        help="Input telemetry file (default: docs/governance/POLICY_CRITIC_TELEMETRY_G4.md)",
    )
    parser.add_argument("--out", type=Path, help="Output file path (default: print to stdout)")

    args = parser.parse_args()

    # Parse telemetry entries
    entries = parse_telemetry_file(args.input)

    if not entries:
        print(f"Warning: No telemetry entries found in {args.input}", file=sys.stderr)
        print("", file=sys.stderr)
        print("To record a PR:", file=sys.stderr)
        print(
            "  python scripts/governance/g4_record_pr_telemetry.py --pr <PR_NUMBER>",
            file=sys.stderr,
        )
        return 1

    # Compute statistics
    stats = compute_statistics(entries)

    # Format summary
    summary = format_summary(stats)

    # Output
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(summary)
        print(f"✓ Rollup summary written to {args.out}")
    else:
        print(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
