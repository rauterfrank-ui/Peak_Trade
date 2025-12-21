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

import sys
from pathlib import Path
import re
from typing import List, Dict, Tuple


def check_merge_log(filepath: Path) -> Tuple[bool, List[str]]:
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
        violations.append(f"❌ Fehler beim Lesen: {e}")
        return False, violations

    # Check: Dateiname Format
    if not re.match(r"PR_\d+_MERGE_LOG\.md", filepath.name):
        violations.append(f"❌ Ungültiger Dateiname: {filepath.name}")

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
            violations.append(f"❌ Fehlendes Header-Feld: {header}")

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
            violations.append(f"❌ Fehlende Section: {section}")

    # Check: Länge (Kompaktheit)
    if len(lines) > 200:
        violations.append(f"⚠️  Länge: {len(lines)} Zeilen (Richtwert: < 200 Zeilen)")

    # Check: PR Nummer Konsistenz
    pr_match = re.search(r"PR_(\d+)_MERGE_LOG\.md", filepath.name)
    if pr_match:
        pr_num = pr_match.group(1)
        # Prüfe ob **PR:** Feld mit Dateinamen übereinstimmt
        pr_field_match = re.search(r"\*\*PR:\*\*\s*#?(\d+)", content)
        if pr_field_match and pr_field_match.group(1) != pr_num:
            violations.append(
                f"❌ PR Nummer inkonsistent: Datei={pr_num}, Header={pr_field_match.group(1)}"
            )

    return len(violations) == 0, violations


def main():
    """Hauptfunktion: Überprüft alle Merge Logs."""
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

    all_violations: Dict[str, List[str]] = {}
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
        sys.exit(1)
    else:
        print("\n✅ Alle Logs entsprechen dem Standard!")
        sys.exit(0)


if __name__ == "__main__":
    main()
