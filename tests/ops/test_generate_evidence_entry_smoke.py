"""Smoke tests for scripts/ops/generate_evidence_entry.py (NO-LIVE, local files only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import generate_evidence_entry as ge  # noqa: E402


def test_main_rejects_whitespace_only_tag() -> None:
    """Auto-ID requires a non-empty --tag (whitespace-only is invalid)."""
    code = ge.main(
        [
            "--category",
            "Test/Refactor",
            "--title",
            "t",
            "--tag",
            "   ",
            "--date",
            "2026-01-15",
        ]
    )
    assert code == 1


def test_main_rejects_out_dir_that_is_existing_file(tmp_path: Path) -> None:
    bad = tmp_path / "not_a_dir.txt"
    bad.write_text("x", encoding="utf-8")
    code = ge.main(
        [
            "--category",
            "Test/Refactor",
            "--title",
            "t",
            "--id",
            "EV-20260115-X",
            "--out-dir",
            str(bad),
        ]
    )
    assert code == 1


def test_main_writes_evidence_markdown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "evidence_out"
    code = ge.main(
        [
            "--category",
            "Test/Refactor",
            "--title",
            "Slice smoke",
            "--tag",
            "SMOKE",
            "--date",
            "2026-01-15",
            "--out-dir",
            str(out),
        ]
    )
    assert code == 0
    md = out / "EV-20260115-SMOKE.md"
    assert md.is_file()
    text = md.read_text(encoding="utf-8")
    assert "**Evidence ID:** EV-20260115-SMOKE" in text
    assert "Slice smoke" in text
