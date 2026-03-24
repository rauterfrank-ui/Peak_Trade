from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.ops.update_officer_schema import UpdateOfficerSchemaError, validate_notifier_payload

NOTIFIER_PAYLOAD_BASENAME = "notifier_payload.json"

EMPTY_UPDATE_OFFICER_UI_MESSAGE = (
    "Update Officer notifier payload is not available (no path resolved or file missing)."
)
INVALID_UPDATE_OFFICER_UI_MESSAGE = (
    "Update Officer notifier payload could not be loaded or validated."
)
UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE = (
    "Update Officer: provide only one of notifier path or run directory (both were given)."
)


def load_notifier_payload(path: str | Path) -> Dict[str, Any]:
    payload_path = Path(path)
    with payload_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    validate_notifier_payload(payload)
    return payload


def build_notifier_view_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    validate_notifier_payload(payload)

    queue: List[Dict[str, Any]] = list(payload.get("recommended_update_queue", []))
    next_topic = payload.get("next_recommended_topic", "none")
    reason = payload.get("top_priority_reason", "")
    next_action = payload.get("recommended_next_action", "")
    review_paths = list(payload.get("recommended_review_paths", []))
    severity = payload.get("severity", "info")
    reminder_class = payload.get("reminder_class", "none")
    requires_manual_review = bool(payload.get("requires_manual_review", False))

    if next_topic == "none":
        headline = "No update topic recommended."
        status = "idle"
    elif requires_manual_review:
        headline = f"Review next update topic: {next_topic}"
        status = "manual_review"
    else:
        headline = f"Next update topic: {next_topic}"
        status = "ready"

    queue_preview = [
        {
            "rank": item["rank"],
            "topic_id": item["topic_id"],
            "worst_priority": item["worst_priority"],
            "finding_count": item["finding_count"],
        }
        for item in queue
    ]

    return {
        "headline": headline,
        "status": status,
        "next_topic": next_topic,
        "why_now": reason,
        "next_action": next_action,
        "review_paths": review_paths,
        "queue_preview": queue_preview,
        "requires_manual_review": requires_manual_review,
        "severity": severity,
        "reminder_class": reminder_class,
    }


def render_notifier_text_summary(payload: Dict[str, Any]) -> str:
    view = build_notifier_view_model(payload)

    lines = [
        f"Headline: {view['headline']}",
        f"Status: {view['status']}",
        f"Next topic: {view['next_topic']}",
        f"Why now: {view['why_now']}",
        f"Next action: {view['next_action']}",
        f"Severity: {view['severity']}",
        f"Reminder class: {view['reminder_class']}",
        f"Requires manual review: {str(view['requires_manual_review']).lower()}",
    ]

    review_paths = view["review_paths"]
    lines.append("Review paths: " + (", ".join(review_paths) if review_paths else "none"))

    queue_preview = view["queue_preview"]
    if not queue_preview:
        lines.append("Queue preview: none")
    else:
        lines.append("Queue preview:")
        for item in queue_preview:
            lines.append(
                f"- #{item['rank']} {item['topic_id']} "
                f"[worst_priority={item['worst_priority']}, findings={item['finding_count']}]"
            )

    return "\n".join(lines)


def resolve_update_officer_notifier_payload_path(
    payload_path: str | Path | None = None,
    run_dir: str | Path | None = None,
) -> Path | None:
    """Resolve path to notifier_payload.json. Explicit payload_path wins; no directory scans."""
    if payload_path is not None:
        p = Path(payload_path)
        return p if p.is_file() else None
    if run_dir is not None:
        candidate = Path(run_dir) / NOTIFIER_PAYLOAD_BASENAME
        return candidate if candidate.is_file() else None
    return None


def build_update_officer_ui_route_conflict() -> Dict[str, Any]:
    """Deterministic empty-state when route supplies conflicting explicit sources."""
    return _empty_update_officer_ui_model(UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE)


def _empty_update_officer_ui_model(message: str) -> Dict[str, Any]:
    return {
        "available": False,
        "headline": "",
        "status": "unavailable",
        "next_topic": "",
        "why_now": "",
        "next_action": "",
        "review_paths": [],
        "queue_preview": [],
        "requires_manual_review": False,
        "severity": "info",
        "reminder_class": "none",
        "empty_state_message": message,
    }


def build_update_officer_ui_model(
    payload_path: str | Path | None = None,
    run_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """
    Read-only UI contract: load notifier payload from explicit path or run directory,
    or return a deterministic empty-state model.
    """
    resolved = resolve_update_officer_notifier_payload_path(
        payload_path=payload_path,
        run_dir=run_dir,
    )
    if resolved is None:
        return _empty_update_officer_ui_model(EMPTY_UPDATE_OFFICER_UI_MESSAGE)
    try:
        payload = load_notifier_payload(resolved)
        view = build_notifier_view_model(payload)
    except (OSError, json.JSONDecodeError, UpdateOfficerSchemaError, ValueError, KeyError):
        return _empty_update_officer_ui_model(INVALID_UPDATE_OFFICER_UI_MESSAGE)
    return {
        "available": True,
        "empty_state_message": "",
        **view,
    }
