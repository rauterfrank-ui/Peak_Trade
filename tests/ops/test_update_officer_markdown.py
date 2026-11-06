from __future__ import annotations

from src.ops.update_officer_markdown import render_update_officer_summary


def _sample_report() -> dict:
    return {
        "officer_version": "v3-min",
        "profile": "dev_tooling_review",
        "started_at": "2026-03-23T10:00:00+00:00",
        "finished_at": "2026-03-23T10:00:01+00:00",
        "output_dir": "out/ops/update_officer/20260323T100000Z",
        "repo_root": "/tmp/repo",
        "success": True,
        "notifier_payload_path": "notifier_payload.json",
        "next_recommended_topic": "ci_integrations",
        "top_priority_reason": (
            "Topic `ci_integrations` ranks first in the deterministic queue: "
            "worst per-finding priority is `p1` across 1 finding(s) (blocked=0)."
        ),
        "recommended_update_queue": [
            {
                "topic_id": "ci_integrations",
                "rank": 1,
                "worst_priority": "p1",
                "finding_count": 1,
                "blocked_count": 0,
                "manual_review_count": 1,
                "safe_review_count": 0,
                "headline": (
                    "1 finding(s); worst_priority=p1; blocked=0; manual_review=1; safe_review=0"
                ),
            },
            {
                "topic_id": "python_dependencies",
                "rank": 2,
                "worst_priority": "p3",
                "finding_count": 1,
                "blocked_count": 0,
                "manual_review_count": 0,
                "safe_review_count": 1,
                "headline": (
                    "1 finding(s); worst_priority=p3; blocked=0; manual_review=0; safe_review=1"
                ),
            },
        ],
        "findings": [
            {
                "surface": "pyproject.toml",
                "item_name": "ruff",
                "current_spec": ">=0.1.0",
                "classification": "safe_review",
                "reason": "recognized dev tooling",
                "category": "python_dependencies",
                "description": "Dev dependency ruff in pyproject.toml.",
                "recommended_action": "No immediate action; include in routine dev-tooling hygiene.",
                "recommended_priority": "p3",
                "notes": [],
            },
            {
                "surface": "github_actions",
                "item_name": "actions/checkout@v3",
                "current_spec": "v3",
                "classification": "manual_review",
                "reason": "non-standard version ref",
                "category": "ci_integrations",
                "description": "GitHub Actions reference.",
                "recommended_action": "Pin or verify GitHub Actions references before relying on this workflow.",
                "recommended_priority": "p1",
                "notes": ["needs manual check"],
            },
        ],
        "summary": {
            "total_findings": 2,
            "safe_review": 1,
            "manual_review": 1,
            "blocked": 0,
            "priority_counts": {"p0": 0, "p1": 1, "p2": 0, "p3": 1},
            "category_counts": {"python_dependencies": 1, "ci_integrations": 1},
        },
    }


def test_render_contains_core_sections() -> None:
    md = render_update_officer_summary(_sample_report())
    assert "# Update Officer Summary" in md
    assert "## Run" in md
    assert "## Notifier-ready output" in md
    assert "notifier_payload.json" in md
    assert "notifier_payload_path" in md
    assert "## Next best update topic" in md
    assert "## Why now" in md
    assert "## What to review first" in md
    assert "## Summary counts" in md
    assert "## By priority" in md
    assert "## By category" in md
    assert "## Recommended next actions" in md
    assert "## Findings" in md
    assert (
        "| surface | item_name | classification | priority | category | current_spec | reason |"
        in md
    )
    assert "ruff" in md
    assert "actions/checkout@v3" in md


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
    assert "v3-min" in md
    assert "total_findings" in md
    assert "### Priority counts" in md
    assert "### Category counts" in md
    assert "`ci_integrations`" in md
    assert "### Items to review first (topic: `ci_integrations`)" in md
