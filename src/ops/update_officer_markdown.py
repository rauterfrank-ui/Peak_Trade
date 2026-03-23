from __future__ import annotations

from typing import Any


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def render_update_officer_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    findings = report["findings"]

    lines: list[str] = []
    lines.append("# Update Officer Summary")
    lines.append("")
    lines.append("## Run")
    lines.append("")
    lines.append(f"- officer_version: `{report['officer_version']}`")
    lines.append(f"- profile: `{report['profile']}`")
    lines.append(f"- success: `{_bool_text(report['success'])}`")
    lines.append(f"- started_at: `{report['started_at']}`")
    lines.append(f"- finished_at: `{report['finished_at']}`")
    lines.append(f"- output_dir: `{report['output_dir']}`")
    lines.append(f"- repo_root: `{report['repo_root']}`")
    lines.append("")

    lines.append("## Summary Counts")
    lines.append("")
    lines.append(f"- total_findings: `{summary['total_findings']}`")
    lines.append(f"- safe_review: `{summary['safe_review']}`")
    lines.append(f"- manual_review: `{summary['manual_review']}`")
    lines.append(f"- blocked: `{summary['blocked']}`")
    lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| surface | item_name | current_spec | classification | reason |")
    lines.append("|---|---|---|---|---|")
    for f in findings:
        lines.append(
            f"| {f['surface']} | {f['item_name']} | {f['current_spec']} "
            f"| {f['classification']} | {f['reason']} |"
        )
    lines.append("")

    notes_entries = []
    for f in findings:
        finding_notes = f.get("notes") or []
        if finding_notes:
            notes_entries.append((f["item_name"], finding_notes))

    if notes_entries:
        lines.append("## Notes")
        lines.append("")
        for item_name, item_notes in notes_entries:
            lines.append(f"### {item_name}")
            lines.append("")
            for note in item_notes:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
