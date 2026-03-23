from __future__ import annotations

from src.ops.update_officer_markdown import render_update_officer_summary


def _sample_report() -> dict:
    return {
        "officer_version": "v0-min",
        "profile": "dev_tooling_review",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/ops/update_officer/20260323T100000Z",
        "repo_root": "/tmp/repo",
        "success": True,
        "findings": [
            {
                "surface": "pyproject.toml",
                "item_name": "ruff",
                "current_spec": ">=0.1.0",
                "classification": "safe_review",
                "reason": "recognized dev tooling",
                "notes": [],
            },
            {
                "surface": "pyproject.toml",
                "item_name": "mystery-pkg",
                "current_spec": "(unpinned)",
                "classification": "manual_review",
                "reason": "not in known dev-tooling bucket",
                "notes": ["needs manual check"],
            },
        ],
        "summary": {
            "total_findings": 2,
            "safe_review": 1,
            "manual_review": 1,
            "blocked": 0,
        },
    }


def test_render_contains_core_sections() -> None:
    md = render_update_officer_summary(_sample_report())
    assert "# Update Officer Summary" in md
    assert "## Run" in md
    assert "## Summary Counts" in md
    assert "## Findings" in md
    assert "| surface | item_name | current_spec | classification | reason |" in md
    assert "ruff" in md
    assert "mystery-pkg" in md


def test_render_contains_notes_section() -> None:
    md = render_update_officer_summary(_sample_report())
    assert "## Notes" in md
    assert "needs manual check" in md


def test_render_no_notes_when_empty() -> None:
    report = _sample_report()
    for f in report["findings"]:
        f["notes"] = []
    md = render_update_officer_summary(report)
    assert "## Notes" not in md


def test_render_includes_metadata() -> None:
    md = render_update_officer_summary(_sample_report())
    assert "dev_tooling_review" in md
    assert "v0-min" in md
    assert "total_findings" in md
