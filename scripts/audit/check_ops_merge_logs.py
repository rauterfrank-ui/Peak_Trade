#!/usr/bin/env python3
"""
Ops Merge Log Audit Tool
Prüft alle PR_*_MERGE_LOG.md Dateien auf Einhaltung des kompakten Standards.

Standard-Requirements (strikt für neue PRs):
- Dateiname: PR_<number>_MERGE_LOG.md
- Header: Title, PR, Merged, Merge Commit, Branch, Change Type
- Sections: Summary, Motivation, Changes, Files Changed, Verification, Risk Assessment
- Kompakt: < 200 Zeilen (Richtwert)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Tuple, Optional


class Violation:
    """Structured violation data."""

    def __init__(self, code: str, message: str, severity: str = "error"):
        self.code = code
        self.message = message
        self.severity = severity  # "error" or "warning"

    def __str__(self):
        icon = "❌" if self.severity == "error" else "⚠️ "
        return f"{icon} {self.message}"

    def to_dict(self):
        return {"code": self.code, "message": self.message, "severity": self.severity}


def check_required_sections(filepath: Path) -> List[str]:
    """
    Prüft, welche erforderlichen Sektionen in einem Merge Log fehlen.

    Args:
        filepath: Pfad zum Merge Log

    Returns:
        Liste der fehlenden Sektionen (Namen ohne "## " Präfix)
    """
    try:
        content = filepath.read_text()
    except Exception:
        return []

    # Deutsche Section-Namen für Tests
    required_sections = {
        "Zusammenfassung": "## Zusammenfassung",
        "Warum": "## Warum",
        "Änderungen": "## Änderungen",
        "Verifikation": "## Verifikation",
        "Risiko": "## Risiko",
        "Operator How-To": "## Operator How-To",
    }

    missing = []
    for name, section_header in required_sections.items():
        if section_header not in content:
            missing.append(name)

    return missing


def check_merge_log(filepath: Path) -> Tuple[bool, List[Violation]]:
    """
    Überprüft ein einzelnes Merge Log auf Compliance.
    Returns: (is_valid, violations)
    """
    violations = []

    # Lese Datei
    try:
        content = filepath.read_text()
        lines = content.splitlines()
    except Exception as e:
        violations.append(Violation("READ_ERROR", f"Fehler beim Lesen: {e}", "error"))
        return False, violations

    # Check: Dateiname Format
    if not re.match(r"PR_\d+_MERGE_LOG\.md", filepath.name):
        violations.append(
            Violation("INVALID_FILENAME", f"Ungültiger Dateiname: {filepath.name}", "error")
        )

    # Check: Header-Felder
    required_headers = [
        "**Title:**",
        "**PR:**",
        "**Merged:**",
        "**Merge Commit:**",
        "**Branch:**",
        "**Change Type:**",
    ]
    for header in required_headers:
        if header not in content:
            header_name = header.replace("**", "").replace(":", "").strip()
            violations.append(
                Violation("MISSING_HEADER", f"Fehlendes Header-Feld: {header}", "error")
            )

    # Check: Required Sections
    required_sections = [
        "## Summary",
        "## Motivation",
        "## Changes",
        "## Files Changed",
        "## Verification",
        "## Risk Assessment",
    ]
    for section in required_sections:
        if section not in content:
            section_name = section.replace("## ", "")
            violations.append(Violation("MISSING_SECTION", f"Fehlende Section: {section}", "error"))

    # Check: Länge (Kompaktheit)
    if len(lines) > 200:
        violations.append(
            Violation(
                "LENGTH_WARNING",
                f"Länge: {len(lines)} Zeilen (Richtwert: < 200 Zeilen)",
                "warning",
            )
        )

    # Check: PR Nummer Konsistenz
    pr_match = re.search(r"PR_(\d+)_MERGE_LOG\.md", filepath.name)
    if pr_match:
        pr_num = pr_match.group(1)
        # Prüfe ob **PR:** Feld mit Dateinamen übereinstimmt
        pr_field_match = re.search(r"\*\*PR:\*\*\s*#?(\d+)", content)
        if pr_field_match and pr_field_match.group(1) != pr_num:
            violations.append(
                Violation(
                    "PR_NUMBER_MISMATCH",
                    f"PR Nummer inkonsistent: Datei={pr_num}, Header={pr_field_match.group(1)}",
                    "error",
                )
            )

    return len(violations) == 0, violations


def generate_json_report(
    all_violations: Dict[str, List[Violation]],
    total_checked: int,
    total_passed: int,
    output_path: Path,
):
    """Generate JSON report of violations."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_checked": total_checked,
            "total_passed": total_passed,
            "total_failed": total_checked - total_passed,
        },
        "violations": {
            filename: [v.to_dict() for v in violations]
            for filename, violations in all_violations.items()
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        json.dump(report, f, indent=2)

    print(f"📄 JSON Report: {output_path}")


def generate_markdown_report(
    all_violations: Dict[str, List[Violation]],
    total_checked: int,
    total_passed: int,
    output_path: Path,
):
    """Generate Markdown report with violations table and checklist."""
    lines = [
        "# Ops Merge Log Violations Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Total Checked:** {total_checked}  ",
        f"**Passed:** {total_passed}  ",
        f"**Failed:** {total_checked - total_passed}",
        "",
        "## Summary",
        "",
    ]

    if not all_violations:
        lines.extend(
            [
                "✅ **All merge logs are compliant!**",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"⚠️ **{len(all_violations)} file(s) with violations**",
                "",
                "## Violations by File",
                "",
                "| File | Violations | Severity |",
                "| --- | --- | --- |",
            ]
        )

        # Sort by PR number (descending = newest first)
        def extract_pr_num(fname: str) -> int:
            match = re.search(r"PR_(\d+)_MERGE_LOG\.md", fname)
            return int(match.group(1)) if match else 0

        sorted_files = sorted(all_violations.keys(), key=extract_pr_num, reverse=True)

        for filename in sorted_files:
            violations = all_violations[filename]
            error_count = sum(1 for v in violations if v.severity == "error")
            warning_count = sum(1 for v in violations if v.severity == "warning")
            severity_str = (
                f"{error_count}E, {warning_count}W" if warning_count > 0 else f"{error_count}E"
            )
            lines.append(f"| `{filename}` | {len(violations)} | {severity_str} |")

        lines.extend(
            [
                "",
                "## Detailed Violations",
                "",
            ]
        )

        for filename in sorted_files:
            violations = all_violations[filename]
            pr_num = extract_pr_num(filename)
            lines.extend(
                [
                    f"### `{filename}` (PR #{pr_num})",
                    "",
                ]
            )

            # Group by code
            by_code: Dict[str, List[Violation]] = {}
            for v in violations:
                by_code.setdefault(v.code, []).append(v)

            for code, viols in sorted(by_code.items()):
                lines.append(f"- **{code}** ({len(viols)}x):")
                for v in viols:
                    lines.append(f"  - {v.message}")

            lines.append("")

        lines.extend(
            [
                "## Migration Checklist",
                "",
                "Priority: Newest PRs first (highest leverage)",
                "",
            ]
        )

        for filename in sorted_files:
            pr_num = extract_pr_num(filename)
            violation_count = len(all_violations[filename])
            lines.append(f"- [ ] **PR #{pr_num}** (`{filename}`) — {violation_count} violations")

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "1. **Forward-only policy:** All new PRs (from next PR onward) must be compliant",
            "2. **Use template:** `docs/ops/PR_206_MERGE_LOG.md` as reference",
            "3. **Migrate on-demand:** Legacy logs can be updated as needed",
            "4. **CI guard:** Currently non-blocking; can flip to blocking when ready",
            "",
            "## Standard Requirements",
            "",
            "### Required Headers",
            "- `**Title:**`",
            "- `**PR:**`",
            "- `**Merged:**`",
            "- `**Merge Commit:**`",
            "- `**Branch:**`",
            "- `**Change Type:**`",
            "",
            "### Required Sections",
            "- `## Summary`",
            "- `## Motivation`",
            "- `## Changes`",
            "- `## Files Changed`",
            "- `## Verification`",
            "- `## Risk Assessment`",
            "",
            "### Compactness",
            "- Target: < 200 lines",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))

    print(f"📝 Markdown Report: {output_path}")


def main():
    """Hauptfunktion: Überprüft alle Merge Logs."""
    parser = argparse.ArgumentParser(
        description="Audit ops merge logs for compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Console output only (default)
  python scripts/audit/check_ops_merge_logs.py

  # Generate reports
  python scripts/audit/check_ops_merge_logs.py \\
    --report-md reports/ops/violations.md \\
    --report-json reports/ops/violations.json

  # Generate reports without failing CI
  python scripts/audit/check_ops_merge_logs.py \\
    --report-md violations.md \\
    --no-exit-nonzero-on-violations
        """,
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        help="Write Markdown report to this path",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        help="Write JSON report to this path",
    )
    parser.add_argument(
        "--exit-nonzero-on-violations",
        dest="exit_nonzero",
        action="store_true",
        default=True,
        help="Exit with code 1 if violations found (default: True)",
    )
    parser.add_argument(
        "--no-exit-nonzero-on-violations",
        dest="exit_nonzero",
        action="store_false",
        help="Do not exit with code 1 if violations found",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    ops_dir = repo_root / "docs" / "ops"

    if not ops_dir.exists():
        print(f"❌ Ops-Verzeichnis nicht gefunden: {ops_dir}")
        sys.exit(1)

    # Finde alle Merge Logs
    merge_logs = sorted(ops_dir.glob("PR_*_MERGE_LOG.md"))

    if not merge_logs:
        print("⚠️  Keine Merge Logs gefunden.")
        sys.exit(0)

    print(f"🔍 Prüfe {len(merge_logs)} Merge Log(s)...\n")

    all_violations: Dict[str, List[Violation]] = {}
    total_checked = 0
    total_passed = 0

    for log_file in merge_logs:
        total_checked += 1
        is_valid, violations = check_merge_log(log_file)

        if is_valid:
            total_passed += 1
            print(f"✅ {log_file.name}")
        else:
            print(f"❌ {log_file.name}")
            all_violations[log_file.name] = violations
            for v in violations:
                print(f"   {v}")
            print()

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Ergebnis: {total_passed}/{total_checked} Logs bestehen den Standard")

    if all_violations:
        print(f"\n⚠️  {len(all_violations)} Datei(en) mit Violations (siehe oben)")
        print("\nTop Violations (nach Datei):")
        for fname in sorted(all_violations.keys()):
            print(f"  - {fname}: {len(all_violations[fname])} Violations")

        print("\n💡 Hinweis: Legacy-Logs können bei Bedarf migriert werden.")
        print("   Forward-only Policy: Neue Logs müssen dem Standard entsprechen.")

    # Generate reports if requested
    if args.report_json:
        generate_json_report(all_violations, total_checked, total_passed, args.report_json)

    if args.report_md:
        generate_markdown_report(all_violations, total_checked, total_passed, args.report_md)

    # Exit code
    if all_violations and args.exit_nonzero:
        sys.exit(1)
    else:
        if not all_violations:
            print("\n✅ Alle Logs entsprechen dem Standard!")
        sys.exit(0)


if __name__ == "__main__":
    main()
