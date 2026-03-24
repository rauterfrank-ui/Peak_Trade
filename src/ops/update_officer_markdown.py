from __future__ import annotations

from typing import Any


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"


def _sorted_item_names_for_topic(findings: list[dict[str, Any]], topic_id: str) -> list[str]:
    return sorted(
        str(f["item_name"]) for f in findings if str(f.get("category", "unknown")) == topic_id
    )


_PRIORITY_LABELS = {
    "p0": "Immediate",
    "p1": "Before merge / CI",
    "p2": "Before next tooling bump",
    "p3": "Routine hygiene",
}


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
    npp = report.get("notifier_payload_path")
    if npp:
        lines.append(f"- notifier_payload_path: `{npp}`")
    lines.append("")

    lines.append("## Notifier-ready output")
    lines.append("")
    if npp:
        lines.append(
            f"Machine-readable notifier contract (same run directory as `report.json`): `{npp}`."
        )
    else:
        lines.append("_Notifier payload path not present in this report._")
    lines.append("")

    lines.append("## Next best update topic")
    lines.append("")
    lines.append(f"- `{report.get('next_recommended_topic', 'none')}`")
    lines.append("")

    lines.append("## Why now")
    lines.append("")
    lines.append(report.get("top_priority_reason", ""))
    lines.append("")

    lines.append("## What to review first")
    lines.append("")
    queue = report.get("recommended_update_queue") or []
    if not queue:
        lines.append("- _(no queued topics)_")
        lines.append("")
    else:
        for entry in queue:
            tid = entry.get("topic_id", "")
            rk = entry.get("rank", 0)
            hl = entry.get("headline", "")
            lines.append(f"{rk}. **`{tid}`** — {hl}")
        lines.append("")
        top_tid = str(queue[0].get("topic_id", ""))
        first_items = _sorted_item_names_for_topic(findings, top_tid)
        lines.append(f"### Items to review first (topic: `{top_tid}`)")
        lines.append("")
        for name in first_items:
            lines.append(f"- `{name}`")
        lines.append("")

    lines.append("## Summary counts")
    lines.append("")
    lines.append(f"- total_findings: `{summary['total_findings']}`")
    lines.append(f"- safe_review: `{summary['safe_review']}`")
    lines.append(f"- manual_review: `{summary['manual_review']}`")
    lines.append(f"- blocked: `{summary['blocked']}`")
    lines.append("")

    lines.append("### By classification")
    lines.append("")
    lines.append(
        f"- `safe_review`: `{summary['safe_review']}` — routine dev-tooling or well-pinned refs"
    )
    lines.append(f"- `manual_review`: `{summary['manual_review']}` — needs human verification")
    lines.append(f"- `blocked`: `{summary['blocked']}` — runtime-adjacent or policy-blocked")
    lines.append("")

    prio = summary.get("priority_counts", {})
    if prio:
        lines.append("### Priority counts")
        lines.append("")
        for key in ["p0", "p1", "p2", "p3"]:
            label = _PRIORITY_LABELS.get(key, key)
            lines.append(f"- {key} ({label}): `{prio.get(key, 0)}`")
        lines.append("")

    cat_counts = summary.get("category_counts", {})
    if cat_counts:
        lines.append("### Category counts")
        lines.append("")
        for key in sorted(cat_counts.keys()):
            lines.append(f"- {key}: `{cat_counts[key]}`")
        lines.append("")

    lines.append("## By priority")
    lines.append("")
    for prio_key in ["p0", "p1", "p2", "p3"]:
        subset = sorted(
            [f for f in findings if f.get("recommended_priority") == prio_key],
            key=lambda x: (x["surface"], x["item_name"]),
        )
        label = _PRIORITY_LABELS.get(prio_key, prio_key)
        lines.append(f"### {prio_key} ({label})")
        lines.append("")
        if not subset:
            lines.append("- _(none)_")
        else:
            for f in subset:
                lines.append(
                    f"- `{f['item_name']}` — {f['surface']} / {f['classification']} — {f['reason']}"
                )
        lines.append("")

    lines.append("## By category")
    lines.append("")
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        by_cat.setdefault(str(f.get("category", "unknown")), []).append(f)
    for cat in sorted(by_cat.keys()):
        lines.append(f"### {cat}")
        lines.append("")
        for f in sorted(by_cat[cat], key=lambda x: (x["recommended_priority"], x["item_name"])):
            lines.append(
                f"- `{f['item_name']}` — priority `{f.get('recommended_priority', '')}` — "
                f"{f['classification']} — {f['surface']}"
            )
        lines.append("")

    lines.append("## Recommended next actions")
    lines.append("")
    lines.append("| item_name | priority | recommended_action |")
    lines.append("|---|---|---|")
    for f in sorted(
        findings,
        key=lambda x: (x.get("recommended_priority", ""), x["surface"], x["item_name"]),
    ):
        action = str(f.get("recommended_action", "")).replace("|", "\\|")
        lines.append(f"| `{f['item_name']}` | `{f.get('recommended_priority', '')}` | {action} |")
    lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append(
        "| surface | item_name | classification | priority | category | current_spec | reason |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for f in sorted(findings, key=lambda x: (x["surface"], x["item_name"])):
        lines.append(
            f"| {f['surface']} | {f['item_name']} | {f['classification']} | "
            f"{f.get('recommended_priority', '')} | {f.get('category', '')} | "
            f"{f['current_spec']} | {f['reason']} |"
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
        for item_name, item_notes in sorted(notes_entries, key=lambda x: x[0]):
            lines.append(f"### {item_name}")
            lines.append("")
            for note in item_notes:
                lines.append(f"- {note}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
