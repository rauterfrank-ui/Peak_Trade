"""Tests für Ops Merge Log Generator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


@pytest.fixture
def test_repo_structure(tmp_path: Path) -> Path:
    """
    Erstellt minimale Repo-Struktur für Tests.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path zum Mock-Repo-Root
    """
    repo_root = tmp_path / "peak_trade"
    repo_root.mkdir()

    # docs/ops/ Verzeichnis
    ops_dir = repo_root / "docs" / "ops"
    ops_dir.mkdir(parents=True)

    # Minimale README mit Merge Logs Section
    readme_content = """# Operations Guide

Quick reference for Peak_Trade operational tasks.

---

## Merge Logs

Post-merge documentation logs for operational PRs.

- [PR #100](PR_100_MERGE_LOG.md) — test(ops): existing entry (merged 2025-01-01) <!-- PR-100-MERGE-LOG -->

"""
    (ops_dir / "README.md").write_text(readme_content, encoding="utf-8")

    # Template
    template_content = """# MERGE LOG — PR #{{PR_NUMBER}} — {{TYPE}}({{SCOPE}}): {{TITLE}}

**PR:** {{PR_URL}}
**Merged:** {{MERGE_DATE_YYYY_MM_DD}}
**Merge Commit:** {{MERGE_COMMIT_SHA}}
**Branch:** {{BRANCH_NAME}} ({{BRANCH_STATUS}})

---

## Zusammenfassung
- TODO

## Warum
- TODO

## Änderungen
**Geändert**
- TODO

## Verifikation
**CI**
- TODO

## Risiko
**Risk:** 🟢 Minimal
**Begründung**
- TODO

## Operator How-To
- TODO

## Referenzen
- PR: {{PR_URL}}
- Commit: {{MERGE_COMMIT_SHA}}

---
"""
    (ops_dir / "MERGE_LOG_TEMPLATE_COMPACT.md").write_text(template_content, encoding="utf-8")

    return repo_root


def test_generate_merge_log_creates_file(test_repo_structure: Path, monkeypatch):
    """Test: Generator erstellt Merge Log Datei mit allen Pflicht-Sektionen."""
    # Importiere Generator Modul (mock __file__ auf test repo)
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "ops")

    import create_merge_log

    # Mock __file__ für repo_root discovery
    monkeypatch.setattr(
        create_merge_log,
        "__file__",
        str(test_repo_structure / "scripts" / "ops" / "create_merge_log.py"),
    )

    # Generiere Merge Log Content
    content = create_merge_log.generate_merge_log_content(
        pr_number=226,
        title="feat(ops): test feature",
        date="2025-12-21",
        commit="abc1234",
        pr_url="https://github.com/user/repo/pull/226",
        branch="feat/test",
        branch_status="deleted",
    )

    # Prüfe, dass Content alle Pflicht-Sektionen enthält
    required_sections = [
        "## Zusammenfassung",
        "## Warum",
        "## Änderungen",
        "## Verifikation",
        "## Risiko",
        "## Operator How-To",
        "## Referenzen",
    ]

    for section in required_sections:
        assert section in content, f"Pflicht-Sektion fehlt: {section}"

    # Prüfe Platzhalter-Ersetzungen
    assert "PR #226" in content
    assert "feat(ops): test feature" in content
    assert "2025-12-21" in content
    assert "abc1234" in content
    assert "https://github.com/user/repo/pull/226" in content
    assert "feat/test" in content
    assert "deleted" in content


def test_write_merge_log_creates_file(test_repo_structure: Path, monkeypatch):
    """Test: write_merge_log schreibt Datei korrekt."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "ops")

    import create_merge_log

    content = "# Test Merge Log\n\n## Zusammenfassung\nTest content"

    merge_log_path = create_merge_log.write_merge_log(
        repo_root=test_repo_structure,
        pr_number=226,
        content=content,
        dry_run=False,
    )

    assert merge_log_path.exists()
    assert merge_log_path.name == "PR_226_MERGE_LOG.md"
    assert merge_log_path.read_text(encoding="utf-8") == content


def test_update_readme_adds_entry(test_repo_structure: Path, monkeypatch):
    """Test: update_readme fügt neuen Entry hinzu."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "ops")

    import create_merge_log

    create_merge_log.update_readme(
        repo_root=test_repo_structure,
        pr_number=226,
        title="feat(ops): test feature",
        date="2025-12-21",
        dry_run=False,
    )

    readme_path = test_repo_structure / "docs" / "ops" / "README.md"
    readme_content = readme_path.read_text(encoding="utf-8")

    # Prüfe, dass neuer Entry vorhanden ist
    assert "[PR #226](PR_226_MERGE_LOG.md)" in readme_content
    assert "feat(ops): test feature" in readme_content
    assert "merged 2025-12-21" in readme_content
    assert "PR-226-MERGE-LOG" in readme_content  # Signature


def test_update_readme_idempotent(test_repo_structure: Path, monkeypatch):
    """Test: update_readme ist idempotent (keine Duplikate)."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "ops")

    import create_merge_log

    # Erste Einfügung
    create_merge_log.update_readme(
        repo_root=test_repo_structure,
        pr_number=226,
        title="feat(ops): test feature",
        date="2025-12-21",
        dry_run=False,
    )

    readme_path = test_repo_structure / "docs" / "ops" / "README.md"
    content_after_first = readme_path.read_text(encoding="utf-8")

    # Zweite Einfügung (sollte nichts tun)
    create_merge_log.update_readme(
        repo_root=test_repo_structure,
        pr_number=226,
        title="feat(ops): test feature",
        date="2025-12-21",
        dry_run=False,
    )

    content_after_second = readme_path.read_text(encoding="utf-8")

    # Content sollte identisch sein
    assert content_after_first == content_after_second

    # Prüfe, dass Entry nur einmal vorkommt
    count = content_after_second.count("[PR #226](PR_226_MERGE_LOG.md)")
    assert count == 1, f"Entry sollte nur einmal vorkommen, gefunden: {count}"


def test_guard_detects_missing_sections(test_repo_structure: Path, monkeypatch):
    """Test: Guard erkennt fehlende Pflicht-Sektionen."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "audit")

    import check_ops_merge_logs

    # Erstelle Merge Log mit fehlenden Sektionen
    incomplete_log = """# MERGE LOG — PR #227 — test

## Zusammenfassung
- Test

## Warum
- Test

## Referenzen
- Test
"""

    merge_log_path = test_repo_structure / "docs" / "ops" / "PR_227_MERGE_LOG.md"
    merge_log_path.write_text(incomplete_log, encoding="utf-8")

    # Mock __file__ für repo_root discovery
    monkeypatch.setattr(
        check_ops_merge_logs,
        "__file__",
        str(test_repo_structure / "scripts" / "audit" / "check_ops_merge_logs.py"),
    )

    missing = check_ops_merge_logs.check_required_sections(merge_log_path)

    # Erwarte fehlende Sektionen
    expected_missing = ["Änderungen", "Verifikation", "Risiko", "Operator How-To"]
    assert sorted(missing) == sorted(expected_missing)


def test_guard_accepts_complete_log(test_repo_structure: Path, monkeypatch):
    """Test: Guard akzeptiert vollständiges Merge Log."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "audit")

    import check_ops_merge_logs

    # Erstelle vollständiges Merge Log
    complete_log = """# MERGE LOG — PR #228 — test

## Zusammenfassung
- Test

## Warum
- Test

## Änderungen
- Test

## Verifikation
- Test

## Risiko
- Test

## Operator How-To
- Test

## Referenzen
- Test
"""

    merge_log_path = test_repo_structure / "docs" / "ops" / "PR_228_MERGE_LOG.md"
    merge_log_path.write_text(complete_log, encoding="utf-8")

    # Mock __file__
    monkeypatch.setattr(
        check_ops_merge_logs,
        "__file__",
        str(test_repo_structure / "scripts" / "audit" / "check_ops_merge_logs.py"),
    )

    missing = check_ops_merge_logs.check_required_sections(merge_log_path)

    # Keine fehlenden Sektionen
    assert missing == []


def test_dry_run_does_not_write(test_repo_structure: Path, monkeypatch):
    """Test: dry_run schreibt keine Dateien."""
    monkeypatch.syspath_prepend(Path(__file__).parent.parent / "scripts" / "ops")

    import create_merge_log

    content = "# Test Merge Log"

    merge_log_path = create_merge_log.write_merge_log(
        repo_root=test_repo_structure,
        pr_number=229,
        content=content,
        dry_run=True,
    )

    # Datei sollte NICHT existieren
    assert not merge_log_path.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
