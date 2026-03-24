from __future__ import annotations

import json

import pytest

from src.ops.update_officer_schema import UpdateOfficerSchemaError
from src.ops.update_officer_consumer import (
    build_notifier_view_model,
    load_notifier_payload,
    render_notifier_text_summary,
)


def _qe(
    rank: int,
    topic_id: str,
    worst_priority: str,
    finding_count: int,
    *,
    blocked: int = 0,
    manual: int = 0,
    safe: int = 0,
) -> dict:
    return {
        "topic_id": topic_id,
        "rank": rank,
        "worst_priority": worst_priority,
        "finding_count": finding_count,
        "blocked_count": blocked,
        "manual_review_count": manual,
        "safe_review_count": safe,
        "headline": (
            f"{finding_count} finding(s); worst_priority={worst_priority}; "
            f"blocked={blocked}; manual_review={manual}; safe_review={safe}"
        ),
    }


def _payload(**overrides):
    payload = {
        "officer_version": "v3-min",
        "generated_at": "2026-03-24T10:25:52Z",
        "next_recommended_topic": "ci_integrations",
        "top_priority_reason": "Critical CI surface requires manual review.",
        "recommended_update_queue": [
            _qe(1, "ci_integrations", "p0", 2, blocked=1, manual=1, safe=0),
            _qe(2, "python_dependencies", "p2", 1, safe=1),
        ],
        "recommended_next_action": "Review CI-related updates first.",
        "recommended_review_paths": [".github/workflows"],
        "severity": "critical",
        "reminder_class": "blocked",
        "requires_manual_review": True,
    }
    payload.update(overrides)
    return payload


def test_build_notifier_view_model_manual_review():
    view = build_notifier_view_model(_payload())
    assert view["status"] == "manual_review"
    assert view["next_topic"] == "ci_integrations"
    assert view["severity"] == "critical"
    assert view["reminder_class"] == "blocked"
    assert view["queue_preview"][0]["rank"] == 1
    assert view["queue_preview"][0]["topic_id"] == "ci_integrations"


def test_build_notifier_view_model_empty_queue():
    view = build_notifier_view_model(
        _payload(
            next_recommended_topic="none",
            top_priority_reason="No update topic requires action.",
            recommended_update_queue=[],
            recommended_next_action="No action required.",
            recommended_review_paths=[],
            severity="info",
            reminder_class="none",
            requires_manual_review=False,
        )
    )
    assert view["status"] == "idle"
    assert view["headline"] == "No update topic recommended."
    assert view["queue_preview"] == []


def test_render_notifier_text_summary_is_deterministic():
    text = render_notifier_text_summary(_payload())
    assert "Headline: Review next update topic: ci_integrations" in text
    assert "Status: manual_review" in text
    assert "Review paths: .github/workflows" in text
    assert "- #1 ci_integrations [worst_priority=p0, findings=2]" in text
    assert "- #2 python_dependencies [worst_priority=p2, findings=1]" in text


def test_load_notifier_payload_validates(tmp_path):
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    payload = load_notifier_payload(path)
    assert payload["next_recommended_topic"] == "ci_integrations"


def test_load_notifier_payload_invalid_fails(tmp_path):
    path = tmp_path / "notifier_payload.json"
    invalid = _payload(severity="urgent")
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(UpdateOfficerSchemaError):
        load_notifier_payload(path)
