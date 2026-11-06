# Labeling Guide

## Canonical taxonomy
We use a small, stable set of labels to avoid taxonomy drift.

### Type / Stream
- `documentation` — docs-only changes, runbooks, guides
- `enhancement` — feature work (user-visible or functional improvement)
- `stream:G` — CI/CD & Quality (pipelines, tooling, lint/test infra, build system)
- `chore` — repo hygiene / maintenance (non-functional upkeep)

### Priority
- `priority:low`
- `priority:medium`
- `priority:high`

## Rules (Guardrails)
- Prefer existing canonical labels over introducing new `type:*` labels.
- Only add new labels if they represent a stable long-term category.
- Every PR should have exactly:
  - 1× Type/Stream label (documentation/enhancement/stream:G/chore)
  - 1× Priority label (low/medium/high)

## Examples
- Docs update to a runbook → `documentation` + `priority:medium`
- New strategy feature → `enhancement` + `priority:high`
- CI workflow fix / tooling → `stream:G` + `priority:medium`
- Formatting / small repo maintenance → `chore` + `priority:low`

## Notes
- `chore` exists to cover maintenance without creating additional `type:*` labels.
