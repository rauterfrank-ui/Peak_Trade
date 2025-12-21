#!/usr/bin/env python3
"""Guard für Ops Merge Log Format-Compliance (Pflichtsektionen Check)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


# Pflicht-Sektionen (H2) für Merge Logs
REQUIRED_SECTIONS = [
    "Zusammenfassung",
    "Warum",
    "Änderungen",
    "Verifikation",
    "Risiko",
    "Operator How-To",
    "Referenzen",
]


def find_merge_logs(repo_root: Path) -> list[Path]:
    """
    Findet alle Merge Log Dateien im ops Directory.

    Args:
        repo_root: Repository root directory

    Returns:
        Liste von Merge Log Pfaden (sortiert)
    """
    ops_dir = repo_root / "docs" / "ops"
    if not ops_dir.exists():
        return []

    # Pattern: PR_<N>_MERGE_LOG.md
    merge_logs = list(ops_dir.glob("PR_*_MERGE_LOG.md"))
    return sorted(merge_logs)


def check_required_sections(merge_log_path: Path) -> list[str]:
    """
    Prüft, ob alle Pflicht-Sektionen in einem Merge Log vorhanden sind.

    Args:
        merge_log_path: Pfad zum Merge Log

    Returns:
        Liste der fehlenden Sektionen (leer wenn alles ok)
    """
    content = merge_log_path.read_text(encoding="utf-8")

    # Finde alle H2 Sektionen (## Sektionsname)
    h2_pattern = re.compile(r"^##\s+(.+?)$", re.MULTILINE)
    found_sections = set(h2_pattern.findall(content))

    # Prüfe, welche Pflicht-Sektionen fehlen
    missing = []
    for required in REQUIRED_SECTIONS:
        if required not in found_sections:
            missing.append(required)

    return missing


def main() -> int:
    """
    Main entry point.

    Exit codes:
        0 - Alle Merge Logs compliant
        1 - Violations gefunden (fehlende Sektionen)
        2 - Unerwarteter Fehler
    """
    try:
        repo_root = Path(__file__).parent.parent.parent
        merge_logs = find_merge_logs(repo_root)

        if not merge_logs:
            print("✅ Keine Merge Logs gefunden (docs/ops/PR_*_MERGE_LOG.md)")
            return 0

        print(f"🔍 Prüfe {len(merge_logs)} Merge Log(s) auf Pflicht-Sektionen...")
        print()

        violations = []

        for merge_log_path in merge_logs:
            missing = check_required_sections(merge_log_path)
            if missing:
                violations.append((merge_log_path, missing))

        if violations:
            print("❌ VIOLATIONS GEFUNDEN:")
            print()
            for path, missing in violations:
                print(f"  {path.relative_to(repo_root)}")
                for section in missing:
                    print(f"    ⚠️  Fehlende Sektion: ## {section}")
                print()

            print(f"❌ {len(violations)} Merge Log(s) mit fehlenden Sektionen")
            print()
            print("Pflicht-Sektionen (H2):")
            for section in REQUIRED_SECTIONS:
                print(f"  - ## {section}")

            return 1

        print(f"✅ Alle {len(merge_logs)} Merge Log(s) sind compliant")
        print()
        print("Geprüfte Pflicht-Sektionen:")
        for section in REQUIRED_SECTIONS:
            print(f"  ✓ ## {section}")

        return 0

    except Exception as exc:
        print(f"❌ Unerwarteter Fehler: {exc}")
        import traceback

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
