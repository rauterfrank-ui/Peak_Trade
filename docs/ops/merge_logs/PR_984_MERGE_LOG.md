# PR #984 — Merge Log

## Summary
- Merged PR #984: docs(observability): make Grafana time picker explicit on provisioned dashboards

## Why
- Ensure the Grafana time range selector is visible across provisioned Peak_Trade dashboards (hardening via explicit dashboard JSON fields).

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/984
- state: MERGED
- mergedAt: 2026-01-24T16:36:54Z
- mergeCommit: `e04b7e7e3ad556d855e33582b2f9032274c421ab`

## Changes
- Grafana dashboard JSONs: add explicit `timepicker.hidden=false` across all provisioned dashboards; add default `time` only where missing.
- Ops note: `docs&#47;ops&#47;notes&#47;2026-01-24_grafana_timepicker_visible.md` (token-policy safe).

## Verification

```bash
python3 scripts/ops/check_merge_log_hygiene.py docs/ops/merge_logs/PR_984_MERGE_LOG.md
```

## Risk
LOW — docs-only (Grafana dashboards JSON + docs note).
