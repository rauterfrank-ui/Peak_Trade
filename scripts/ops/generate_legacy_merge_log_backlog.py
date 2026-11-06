#!/usr/bin/env python3
"""
Generate/Update Legacy Merge Log Violations Backlog

Reads violations from JSON report (or runs audit internally) and generates
a structured, prioritized backlog document.

Strategy:
- Highest leverage first: newest PRs (likely more relevant)
- Deterministic/idempotent: re-running produces same output
- No auto-migration of content, only backlog management
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run_audit_internally(repo_root: Path) -> Dict:
    """Run check_ops_merge_logs.py internally and capture JSON."""
    audit_script = repo_root / "scripts" / "audit" / "check_ops_merge_logs.py"
    json_tmp = repo_root / ".tmp_violations.json"

    try:
        # Run audit with JSON output, don't fail on violations
        result = subprocess.run(
            [
                sys.executable,
                str(audit_script),
                "--report-json",
                str(json_tmp),
                "--no-exit-nonzero-on-violations",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if not json_tmp.exists():
            print("❌ Audit failed to generate JSON report")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)

        data = json.loads(json_tmp.read_text())
        json_tmp.unlink()  # Cleanup
        return data

    except Exception as e:
        print(f"❌ Error running audit: {e}")
        sys.exit(1)


def load_json_report(json_path: Path) -> Dict:
    """Load existing JSON report."""
    if not json_path.exists():
        print(f"❌ JSON report not found: {json_path}")
        sys.exit(1)

    return json.loads(json_path.read_text())


def generate_backlog_document(violations_data: Dict, output_path: Path, repo_root: Path):
    """Generate prioritized backlog Markdown document."""
    summary = violations_data["summary"]
    violations = violations_data["violations"]

    lines = [
        "# Legacy Merge Log Violations Backlog",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Status:** Forward-only policy active (CI guard non-blocking)  ",
        f"**Total Logs:** {summary['total_checked']}  ",
        f"**Compliant:** {summary['total_passed']}  ",
        f"**With Violations:** {summary['total_failed']}",
        "",
        "## Goal",
        "",
        "- **Forward-only Policy:** New merge logs must comply with compact standard",
        "- Legacy logs are migrated on-demand, prioritized by leverage",
        "- CI guard is non-blocking to avoid workflow disruption",
        "",
        "## Standard Requirements",
        "",
        "All new `PR_*_MERGE_LOG.md` files must include:",
        "",
        "### Required Headers",
        "- `**Title:**` — PR title",
        "- `**PR:**` — PR number (#XXX)",
        "- `**Merged:**` — Merge date (YYYY-MM-DD)",
        "- `**Merge Commit:**` — Commit hash (short)",
        "- `**Branch:**` — Branch name (deleted/active)",
        "- `**Change Type:**` — Change type (additive, breaking, etc.)",
        "",
        "### Required Sections",
        "- `## Summary` — Brief summary (2-3 sentences)",
        "- `## Motivation` — Why this change?",
        "- `## Changes` — What changed? (structured)",
        "- `## Files Changed` — File list with checksums",
        "- `## Verification` — CI checks, local tests",
        "- `## Risk Assessment` — Risk evaluation",
        "",
        "### Compactness",
        "- **< 200 lines** (guideline)",
        "- Focus on essentials, avoid verbose details",
        "",
        "## Reference Implementation",
        "",
        "✅ **`docs/ops/PR_206_MERGE_LOG.md`** — Use as template for new logs",
        "",
        "## Prioritized Backlog",
        "",
        "**Strategy:** Newest PRs first (highest leverage, likely more relevant)",
        "",
    ]

    if not violations:
        lines.extend(
            [
                "✅ **All logs are compliant!** No backlog items.",
                "",
            ]
        )
    else:
        # Extract PR numbers and sort descending (newest first)
        import re

        items = []
        for filename, viols in violations.items():
            match = re.search(r"PR_(\d+)_MERGE_LOG\.md", filename)
            if match:
                pr_num = int(match.group(1))
                error_count = sum(1 for v in viols if v.get("severity") == "error")
                warning_count = sum(1 for v in viols if v.get("severity") == "warning")
                items.append(
                    {
                        "pr": pr_num,
                        "filename": filename,
                        "total": len(viols),
                        "errors": error_count,
                        "warnings": warning_count,
                    }
                )

        items.sort(key=lambda x: x["pr"], reverse=True)

        # Categorize by severity
        high_priority = [i for i in items if i["total"] >= 10]
        medium_priority = [i for i in items if 5 <= i["total"] < 10]
        low_priority = [i for i in items if i["total"] < 5]

        if high_priority:
            lines.extend(
                [
                    "### High Priority (≥10 violations)",
                    "",
                ]
            )
            for item in high_priority:
                lines.append(
                    f"- [ ] **PR #{item['pr']}** — `{item['filename']}` "
                    f"({item['errors']}E, {item['warnings']}W)"
                )
            lines.append("")

        if medium_priority:
            lines.extend(
                [
                    "### Medium Priority (5-9 violations)",
                    "",
                ]
            )
            for item in medium_priority:
                lines.append(
                    f"- [ ] **PR #{item['pr']}** — `{item['filename']}` "
                    f"({item['errors']}E, {item['warnings']}W)"
                )
            lines.append("")

        if low_priority:
            lines.extend(
                [
                    "### Low Priority (<5 violations)",
                    "",
                ]
            )
            for item in low_priority:
                lines.append(
                    f"- [ ] **PR #{item['pr']}** — `{item['filename']}` "
                    f"({item['errors']}E, {item['warnings']}W)"
                )
            lines.append("")

    lines.extend(
        [
            "## Tools & Resources",
            "",
            "### Audit Tool",
            "```bash",
            "# Check all logs",
            "python scripts/audit/check_ops_merge_logs.py",
            "",
            "# Generate reports",
            "python scripts/audit/check_ops_merge_logs.py \\",
            "  --report-md reports/ops/violations.md \\",
            "  --report-json reports/ops/violations.json",
            "```",
            "",
            "### Regenerate This Backlog",
            "```bash",
            "python scripts/ops/generate_legacy_merge_log_backlog.py",
            "```",
            "",
            "### CI Integration",
            "- **Workflow:** `.github/workflows/audit.yml`",
            "- **Status:** Non-blocking guard active",
            "- **Future:** Can flip to blocking when legacy backlog is cleared",
            "",
            "## Migration Strategy",
            "",
            "1. **Forward-only:** All new PRs must be compliant (enforced by review)",
            "2. **Legacy:** Migrate on-demand, starting with high-priority items",
            "3. **Template:** Use `PR_206_MERGE_LOG.md` as reference",
            "4. **Review:** Update this backlog after migrations",
            "",
            "## Next Steps",
            "",
            "1. New PRs: Use compliant format (see reference implementation)",
            "2. Legacy: Pick items from backlog as needed/prioritized",
            "3. CI Guard: Keep non-blocking until backlog is significantly reduced",
            "4. Documentation: Keep this backlog up-to-date by re-running generator",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))

    print(f"✅ Backlog updated: {output_path}")
    print(f"   Total violations: {summary['total_failed']}/{summary['total_checked']}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate/update legacy merge log violations backlog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        help="Path to existing JSON report (if not provided, runs audit internally)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for backlog document (default: docs/ops/LEGACY_MERGE_LOG_VIOLATIONS_BACKLOG.md)",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent

    # Default output path
    if args.output is None:
        args.output = repo_root / "docs" / "ops" / "LEGACY_MERGE_LOG_VIOLATIONS_BACKLOG.md"

    # Load or generate violations data
    if args.json_report:
        print(f"📖 Loading JSON report: {args.json_report}")
        violations_data = load_json_report(args.json_report)
    else:
        print("🔍 Running audit internally...")
        violations_data = run_audit_internally(repo_root)

    # Generate backlog document
    generate_backlog_document(violations_data, args.output, repo_root)


if __name__ == "__main__":
    main()
