# Update Officer v3 – Notifier-ready contract

## Goal

Extend **Update Officer v2** with a **deterministic, machine-readable** artifact suitable for
downstream notifiers, **without** adding notification transport or changing read-only posture.

## Added in v3

| Artifact / field | Purpose |
|------------------|---------|
| `notifier_payload.json` | Sidecar JSON next to `report.json`, `summary.md`, `events.jsonl`, `manifest.json` |
| `notifier_payload_path` | Basename in `report.json` linking the report to the notifier artifact |
| `validate_notifier_payload()` | Schema checks for notifier keys and enums |

**Notifier payload (top level):**

- `officer_version` — e.g. `v3-min`
- `generated_at` — ISO-8601 (same run completion instant as report `finished_at`)
- `next_recommended_topic`, `top_priority_reason`, `recommended_update_queue` — aligned with v2 prioritization
- `recommended_next_action` — deterministic string (empty queue vs. queued topics)
- `recommended_review_paths` — e.g. `pyproject.toml` for `python_dependencies`, `.github/workflows` for `ci_integrations`, `[]` for `none`
- `severity` — `info` when no findings; else mapped from worst finding priority (`critical` / `high` / `medium` / `low`)
- `reminder_class` — `none` | `blocked` | `manual_review` | `hygiene`
- `requires_manual_review` — boolean derived from severity and classifications

**Manifest:** `manifest.json` lists all files in the run directory, including `notifier_payload.json`.

**Markdown:** `summary.md` includes **Notifier-ready output** and references `notifier_payload_path`.

## Guardrails

- Read-only; no dependency bumps, lockfile writes, or installs
- No paper/shadow/evidence mutation (beyond designated Update Officer output roots)
- No runtime/live authority; **no** external notification transport in this slice

## Deliverables (code)

- `src&#47;ops&#47;update_officer.py` — build + write notifier payload; report field
- `src&#47;ops&#47;update_officer_schema.py` — notifier + report validation
- `src&#47;ops&#47;update_officer_markdown.py` — notifier section
- Tests under `tests&#47;ops&#47;test_update_officer*.py`
- This runbook

## Version

- `officer_version`: **`v3-min`**
