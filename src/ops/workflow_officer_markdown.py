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

    lines.append("## Checks")
    lines.append("")
    lines.append("| check_id | severity | outcome | effective_level | status | returncode |")
    lines.append("|---|---|---|---|---|---:|")
    for check in checks:
        lines.append(
            f"| {check['check_id']} | {check['severity']} | {check['outcome']} | "
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
        for check_id, check_notes in notes:
            lines.append(f"### {check_id}")
            lines.append("")
            for note in check_notes:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
