# PR #921 — Merge Log
## Summary
Execution Watch v0.4: health endpoint + health panel (read-only, deterministic).

## Why
Expose deterministic health/meta surface for watch-only UI without impacting tail mode; keep NO-LIVE posture.

## Changes
- API: v0.4 meta enrichments + new health endpoint (deterministic; runtime metrics opt-in).
- UI: Health panel + "Ping Health" (no auto polling; tail mode unchanged).
- Docs/Evidence: runbook v0.4 update + evidence template + stamped PASS evidence.
- Tests: extended pytest for v0.4 meta/health/stats/last_event + runtime-metrics opt-in “does not crash”.

## Verification
Pre-merge required checks PASS (snapshot-only via `gh pr checks 921 --watch=false`).
Pre-merge Gate: mergeable=MERGEABLE, mergeStateStatus=CLEAN, headRefOid=e6251004d91c30c22a9d2265be8daf183146d2f8.

## Risk
LOW (watch-only/read-only; NO-LIVE; no mutating endpoints).

## Operator How-To
UI: use Health panel; "Ping Health" triggers a single-shot read.
Endpoint (code-fence only):
```text
/api/execution/health
```
