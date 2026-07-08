"""Docs-contract guard: stale Kraken docs must not claim current target venue SSOT."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

POSITIVE_CLAIM_PHRASES = (
    "Kraken is the current canonical target venue",
    "Kraken is the current target venue",
    "CURRENT_CANONICAL_VENUE_SSOT=kraken",
    'default_exchange = "kraken"',
    'default_exchange="kraken"',
)

CLARIFIED_DOC_PATHS = (
    REPO_ROOT / "docs" / "project_docs" / "FINAL_SUMMARY.md",
    REPO_ROOT / "docs" / "project_docs" / "IMPLEMENTATION_SUMMARY.md",
    REPO_ROOT / "docs" / "project_docs" / "NEXT_STEPS.md",
    REPO_ROOT / "docs" / "project_docs" / "CONFIG_IMPORT_GUIDE.md",
    REPO_ROOT / "WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md",
)


def test_venue_kraken_legacy_clarification_audit_note_present_v0() -> None:
    text = (REPO_ROOT / "docs" / "audit" / "VENUE_KRAKEN_LEGACY_CLARIFICATION_V0.md").read_text(
        encoding="utf-8"
    )
    assert "KRAKEN_CURRENT_TARGET_VENUE=false" in text
    assert "KRAKEN_REFERENCES_ARE_LEGACY_OR_GUARDED_INFRASTRUCTURE=true" in text
    assert "NO_RUNTIME_AUTHORITY_FROM_VENUE_REFERENCES=true" in text
    assert "okx_europe_eea" in text


def _normalized_doc_text(text: str) -> str:
    return text.lower().replace("*", "")


def test_clarified_kraken_docs_do_not_claim_current_target_venue_ssot_v0() -> None:
    for path in CLARIFIED_DOC_PATHS:
        text = path.read_text(encoding="utf-8")
        for phrase in POSITIVE_CLAIM_PHRASES:
            assert phrase not in text, (
                f"{path.relative_to(REPO_ROOT)} contains forbidden phrase: {phrase!r}"
            )
        normalized = _normalized_doc_text(text)
        assert "not the current canonical target venue" in normalized
        assert "okx_europe_eea" in normalized


def test_legacy_kraken_demo_script_docstring_marks_non_canonical_v0() -> None:
    text = (REPO_ROOT / "scripts" / "demo_kraken_simple.py").read_text(encoding="utf-8")
    assert "legacy" in text.lower()
    assert "not the current canonical target venue" in text.lower()
    for phrase in POSITIVE_CLAIM_PHRASES:
        assert phrase not in text
