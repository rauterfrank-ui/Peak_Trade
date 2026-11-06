# PR #778 — MERGE LOG

## Summary
- PR: #778
- Title: docs(observability): keep overview readable when main prom missing
- State: MERGED
- Merged at: 2026-01-18T06:07:27Z
- Merge commit: c4e007bd35ddf7f6349d941d1ed1a567d154d191

## Why
- Keep the provisioned Overview dashboard readable when the main Prometheus datasource is missing/unavailable.

## Changes
- Scope: docs-only / observability dashboard JSON
- Files:
  - M `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;overview&#47;peaktrade-overview.json`

## Verification
- PR checks snapshot: `gh pr checks 778` showed PASS/SKIP only (no watch loops).

## Risk
- Low (docs-only / dashboard JSON)

## Operator Notes
- If the “main” Prometheus datasource is not present, the Overview dashboard remains readable (panels should degrade gracefully rather than break hard).

## References
- PR #778
- Merge commit c4e007bd35ddf7f6349d941d1ed1a567d154d191
