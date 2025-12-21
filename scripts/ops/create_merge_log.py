#!/usr/bin/env python3
"""Generator für Ops Merge Logs im standardisierten Format."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path


def load_template(repo_root: Path) -> str:
    """
    Lädt das Merge Log Template.

    Args:
        repo_root: Repository root directory

    Returns:
        Template als String

    Raises:
        FileNotFoundError: Wenn Template nicht gefunden wurde
    """
    template_path = repo_root / "docs" / "ops" / "MERGE_LOG_TEMPLATE_COMPACT.md"
    if not template_path.exists():
        msg = f"Template nicht gefunden: {template_path}"
        raise FileNotFoundError(msg)
    return template_path.read_text(encoding="utf-8")


def generate_merge_log_content(
    pr_number: int,
    title: str,
    date: str,
    commit: str,
    pr_url: str,
    branch: str,
    branch_status: str = "deleted",
) -> str:
    """
    Generiert Merge Log Inhalt aus Template.

    Args:
        pr_number: PR Nummer
        title: PR Titel (format: "type(scope): description")
        date: Merge Datum (YYYY-MM-DD)
        commit: Merge Commit SHA
        pr_url: PR URL
        branch: Branch Name
        branch_status: Branch Status (default: "deleted")

    Returns:
        Gefülltes Merge Log Template als String
    """
    # Template-Ersetzungen
    replacements = {
        "{{PR_NUMBER}}": str(pr_number),
        "{{TYPE}}({{SCOPE}}): {{TITLE}}": title,
        "{{PR_URL}}": pr_url,
        "{{MERGE_DATE_YYYY_MM_DD}}": date,
        "{{MERGE_COMMIT_SHA}}": commit,
        "{{BRANCH_NAME}}": branch,
        "{{BRANCH_STATUS}}": branch_status,
    }

    # Versuche Template zu laden, ansonsten generiere Minimal-Template
    try:
        repo_root = Path(__file__).parent.parent.parent
        content = load_template(repo_root)
    except FileNotFoundError:
        # Fallback: Minimales Template
        content = _generate_minimal_template()

    # Ersetze Platzhalter
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return content


def _generate_minimal_template() -> str:
    """Generiert minimales Merge Log Template als Fallback."""
    return """# MERGE LOG — PR #{{PR_NUMBER}} — {{TYPE}}({{SCOPE}}): {{TITLE}}

**PR:** {{PR_URL}}
**Merged:** {{MERGE_DATE_YYYY_MM_DD}}
**Merge Commit:** {{MERGE_COMMIT_SHA}}
**Branch:** {{BRANCH_NAME}} ({{BRANCH_STATUS}})

---

## Zusammenfassung
- _TODO: Was wurde geändert?_
- _TODO: Welchen Impact/Wert bringt es?_

## Warum
- _TODO: Root Cause oder Kontext_
- _TODO: Warum jetzt?_

## Änderungen
**Geändert**
- `path/to/file` — _TODO: Beschreibung_

**Neu**
- `path/to/file` — _TODO: Beschreibung_

## Verifikation
**CI**
- _TODO: Check Name_ — PASS/FAIL

**Lokal**
- _TODO: Durchgeführte Tests_

## Risiko
**Risk:** 🟢 Minimal / 🟡 Medium / 🔴 High
**Begründung**
- _TODO: Warum dieses Risk Level?_

## Operator How-To
- _TODO: Schritt 1_
- _TODO: Schritt 2_

## Referenzen
- PR: {{PR_URL}}
- Commit: {{MERGE_COMMIT_SHA}}

---
"""


def write_merge_log(
    repo_root: Path,
    pr_number: int,
    content: str,
    dry_run: bool = False,
) -> Path:
    """
    Schreibt Merge Log Datei.

    Args:
        repo_root: Repository root directory
        pr_number: PR Nummer
        content: Merge Log Inhalt
        dry_run: Wenn True, nur Ausgabe ohne Schreiben

    Returns:
        Path zum geschriebenen Merge Log
    """
    merge_log_path = repo_root / "docs" / "ops" / f"PR_{pr_number}_MERGE_LOG.md"

    if dry_run:
        print(f"[DRY-RUN] Würde schreiben: {merge_log_path}")
        print(content)
        return merge_log_path

    merge_log_path.parent.mkdir(parents=True, exist_ok=True)
    merge_log_path.write_text(content, encoding="utf-8")
    print(f"[created] {merge_log_path}")

    return merge_log_path


def update_readme(
    repo_root: Path,
    pr_number: int,
    title: str,
    date: str,
    dry_run: bool = False,
) -> None:
    """
    Aktualisiert docs/ops/README.md mit neuem Merge Log Link (idempotent).

    Args:
        repo_root: Repository root directory
        pr_number: PR Nummer
        title: PR Titel
        date: Merge Datum (YYYY-MM-DD)
        dry_run: Wenn True, nur Ausgabe ohne Schreiben
    """
    readme_path = repo_root / "docs" / "ops" / "README.md"

    # Signature für Duplikat-Schutz
    signature = f"PR-{pr_number}-MERGE-LOG"

    if not readme_path.exists():
        if dry_run:
            print(f"[DRY-RUN] README nicht gefunden: {readme_path}")
            return
        # Erstelle minimale README
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        initial_content = """# Operations Guide

Quick reference for Peak_Trade operational tasks.

---

## Merge Logs

Post-merge documentation logs for operational PRs.

"""
        readme_path.write_text(initial_content, encoding="utf-8")
        print(f"[created] {readme_path}")

    text = readme_path.read_text(encoding="utf-8")

    # Prüfe auf Duplikat (via signature oder PR-Link)
    pr_link = f"[PR #{pr_number}](PR_{pr_number}_MERGE_LOG.md)"
    if signature in text or pr_link in text:
        print(f"[skip] PR #{pr_number} bereits in README vorhanden")
        return

    # Entry erstellen
    entry = f"- {pr_link} — {title} (merged {date}) <!-- {signature} -->\n"

    # Finde "## Merge Logs" Section
    section_header = "## Merge Logs"
    if section_header not in text:
        # Section existiert nicht, füge sie hinzu
        if dry_run:
            print(f"[DRY-RUN] Würde Section '{section_header}' hinzufügen")
            return

        if not text.endswith("\n\n"):
            text += "\n\n"
        text += f"{section_header}\n\n"
        text += "Post-merge documentation logs for operational PRs.\n\n"
        text += entry
        readme_path.write_text(text, encoding="utf-8")
        print(f"[add] Section + Entry in {readme_path}")
        return

    if dry_run:
        print(f"[DRY-RUN] Würde Entry hinzufügen: {entry.strip()}")
        return

    # Insert nach dem Section Header (top insertion)
    before, after = text.split(section_header, 1)

    # Finde erste Zeile nach Header (könnte leer sein oder Text)
    lines_after = after.split("\n")
    # Überspringe Leerzeilen und einleitenden Text bis zur ersten Liste
    insert_idx = 0
    for i, line in enumerate(lines_after):
        if line.strip() and not line.startswith("-") and not line.startswith("#"):
            # Einleitungstext, überspringe
            insert_idx = i + 1
        elif line.startswith("-"):
            # Erste Liste gefunden
            insert_idx = i
            break
        elif line.strip() == "":
            # Leerzeile
            continue
        else:
            # Nächster Header oder anderer Content
            insert_idx = i
            break

    # Baue neuen Content zusammen
    lines_after.insert(insert_idx, entry.rstrip())
    new_after = "\n".join(lines_after)
    new_text = before + section_header + new_after

    readme_path.write_text(new_text, encoding="utf-8")
    print(f"[insert] Entry in {readme_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generiert Ops Merge Log im standardisierten Format"
    )
    parser.add_argument("--pr", type=int, required=True, help="PR Nummer")
    parser.add_argument("--title", type=str, required=True, help="PR Titel")
    parser.add_argument("--date", type=str, required=True, help="Merge Datum (YYYY-MM-DD)")
    parser.add_argument("--commit", type=str, required=True, help="Merge Commit SHA")
    parser.add_argument("--pr-url", type=str, required=True, help="PR URL")
    parser.add_argument("--branch", type=str, required=True, help="Branch Name")
    parser.add_argument(
        "--branch-status",
        type=str,
        default="deleted",
        help="Branch Status (default: deleted)",
    )
    parser.add_argument(
        "--update-readme",
        action="store_true",
        default=True,
        help="README aktualisieren (default: true)",
    )
    parser.add_argument(
        "--no-update-readme",
        dest="update_readme",
        action="store_false",
        help="README nicht aktualisieren",
    )
    parser.add_argument("--dry-run", action="store_true", help="Nur Ausgabe, keine Änderungen")

    args = parser.parse_args()

    # Validiere Datum
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError as exc:
        print(f"[error] Ungültiges Datumsformat: {args.date} (erwartet: YYYY-MM-DD)")
        return 2

    try:
        repo_root = Path(__file__).parent.parent.parent

        # Generiere Merge Log Content
        content = generate_merge_log_content(
            pr_number=args.pr,
            title=args.title,
            date=args.date,
            commit=args.commit,
            pr_url=args.pr_url,
            branch=args.branch,
            branch_status=args.branch_status,
        )

        # Schreibe Merge Log
        write_merge_log(
            repo_root=repo_root,
            pr_number=args.pr,
            content=content,
            dry_run=args.dry_run,
        )

        # Update README (optional)
        if args.update_readme:
            update_readme(
                repo_root=repo_root,
                pr_number=args.pr,
                title=args.title,
                date=args.date,
                dry_run=args.dry_run,
            )

        if args.dry_run:
            print("\n[DRY-RUN] Keine Änderungen vorgenommen")
        else:
            print(f"\n✅ Merge Log für PR #{args.pr} erfolgreich erstellt")

        return 0

    except Exception as exc:
        print(f"[error] Unerwarteter Fehler: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
