from __future__ import annotations

from typing import Any


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def render_workflow_officer_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    checks = report["checks"]

    lines: list[str] = []
    lines.append("# Workflow Officer Summary")
    lines.append("")
    lines.append("## Run")
    lines.append("")
    lines.append(f"- officer_version: `{report['officer_version']}`")
    lines.append(f"- mode: `{report['mode']}`")
    lines.append(f"- profile: `{report['profile']}`")
    lines.append(f"- success: `{_bool_text(report['success'])}`")
    lines.append(f"- started_at: `{report['started_at']}`")
    lines.append(f"- finished_at: `{report['finished_at']}`")
    lines.append(f"- output_dir: `{report['output_dir']}`")
    lines.append(f"- repo_root: `{report['repo_root']}`")
    lines.append("")

    lines.append("## Summary Counts")
    lines.append("")
    lines.append(f"- total_checks: `{summary['total_checks']}`")
    lines.append(f"- hard_failures: `{summary['hard_failures']}`")
    lines.append(f"- warnings: `{summary['warnings']}`")
    lines.append(f"- infos: `{summary['infos']}`")
    lines.append(f"- strict: `{_bool_text(summary['strict'])}`")
    lines.append("")

    lines.append("### Recommended priority counts")
    lines.append("")
    for key in ["p0", "p1", "p2", "p3"]:
        lines.append(f"- {key}: `{summary['recommended_priority_counts'][key]}`")
    lines.append("")

    lines.append("### Severity Counts")
    lines.append("")
    for key in ["hard_fail", "warn", "info"]:
        lines.append(f"- {key}: `{summary['severity_counts'][key]}`")
    lines.append("")

    lines.append("### Outcome Counts")
    lines.append("")
    for key in ["pass", "fail", "missing"]:
        lines.append(f"- {key}: `{summary['outcome_counts'][key]}`")
    lines.append("")

    lines.append("### Effective Level Counts")
    lines.append("")
    for key in ["ok", "warning", "error", "info"]:
        lines.append(f"- {key}: `{summary['effective_level_counts'][key]}`")
    lines.append("")

    # Lazy import: ``workflow_officer`` imports this module at load time.
    from src.ops.workflow_officer import (
        render_next_chat_preview_markdown,
        render_operator_report_markdown,
    )

    raw_op = summary.get("operator_report")
    op = raw_op if isinstance(raw_op, dict) else {}
    op_block = render_operator_report_markdown(op)
    if op_block:
        lines.append(op_block)

    raw_preview = summary.get("next_chat_preview")
    preview = raw_preview if isinstance(raw_preview, dict) else {}
    preview_block = render_next_chat_preview_markdown(preview)
    if preview_block:
        lines.append(preview_block)

    lines.append("## By priority")
    lines.append("")
    for prio in ["p0", "p1", "p2", "p3"]:
        subset = sorted(
            [c for c in checks if c["recommended_priority"] == prio],
            key=lambda x: x["check_id"],
        )
        lines.append(f"### {prio}")
        lines.append("")
        if not subset:
            lines.append("- _(none)_")
        else:
            for c in subset:
                lines.append(
                    f"- `{c['check_id']}` — {c['category']} / {c['surface']} — "
                    f"{c['effective_level']} / {c['outcome']}"
                )
        lines.append("")

    lines.append("## By category")
    lines.append("")
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for c in checks:
        by_cat.setdefault(c["category"], []).append(c)
    for cat in sorted(by_cat.keys()):
        lines.append(f"### {cat}")
        lines.append("")
        for c in sorted(by_cat[cat], key=lambda x: x["check_id"]):
            lines.append(
                f"- `{c['check_id']}` — priority `{c['recommended_priority']}` — "
                f"{c['effective_level']} / {c['outcome']}"
            )
        lines.append("")

    lines.append("## Recommended next actions")
    lines.append("")
    lines.append("| check_id | priority | recommended_action |")
    lines.append("|---|---|---|")
    for c in sorted(checks, key=lambda x: (x["recommended_priority"], x["check_id"])):
        action = c["recommended_action"].replace("|", "\\|")
        lines.append(f"| `{c['check_id']}` | `{c['recommended_priority']}` | {action} |")
    lines.append("")

    lines.append("## Checks")
    lines.append("")
    lines.append(
        "| check_id | surface | category | priority | severity | outcome | effective_level | status | returncode |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---:|")
    for check in sorted(checks, key=lambda x: x["check_id"]):
        lines.append(
            f"| {check['check_id']} | {check['surface']} | {check['category']} | "
            f"{check['recommended_priority']} | {check['severity']} | {check['outcome']} | "
            f"{check['effective_level']} | {check['status']} | {check['returncode']} |"
        )
    lines.append("")

    notes = []
    for check in checks:
        check_notes = check.get("notes") or []
        if check_notes:
            notes.append((check["check_id"], check_notes))

    if notes:
        lines.append("## Notes")
        lines.append("")
        for check_id, check_notes in sorted(notes, key=lambda x: x[0]):
            lines.append(f"### {check_id}")
            lines.append("")
            for note in check_notes:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
