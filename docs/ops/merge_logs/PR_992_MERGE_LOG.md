# PR #992 — MERGE LOG

## Summary
- obs(ops): add AI Live local verify wrapper + runbook quickstart

## Why
- DRY: Single Source of Truth wrapper script; runbook bleibt script-first.
- Deterministic operator proof: one-command local verify producing file-backed evidence.

## Changes
- Add: `scripts/obs/ai_live_local_verify.sh` (snapshot-only, no pipes, Port Contract v1 :9110, file-backed evidence; exit=verify_rc).
- Update: `docs/ops/runbooks/RUNBOOK_AI_LIVE_OPS_LOCAL.md` (Quickstart: one-command wrapper; no script duplication).
- Update: `docs/ops/EVIDENCE_INDEX.md`
- Add: `docs/ops/evidence/EV_AI_LIVE_OPS_LOCAL_20260125T010948Z.md`

## Verification
- Pre-merge gate: mergeStateStatus=CLEAN; required checks PASS; approved_reviews=2; Head SHA matched guard.
- Merge exec: guarded squash merge with `--match-head-commit`.
- Evidence: `.local_tmp&#47;pr_992_merge_exec_20260126T224258Z` (pre/post snapshots, required checks snapshot, merge stdout/stderr, local main sync).

## Risk
- Low. NO-LIVE HARD; wrapper writes only `.local_tmp&#47;*` and (runtime) `logs&#47;ai&#47;ai_events.jsonl`; no broker/order/execution writes.

## Operator How-To
- Run (one command): `bash scripts/obs/ai_live_local_verify.sh`
- Evidence outputs:
  - Wrapper OUT: `.local_tmp&#47;ai_live_local_verify_<STAMP>` (`OPERATOR_NOTE.txt`, `MANIFEST_SHA256.txt`, `KEY_MATERIAL_SCAN.txt`, latest dirs pointer)
  - Verify evidence: `.local_tmp&#47;ai_live_ops_verify_<STAMP>`
  - Activity evidence: `.local_tmp&#47;ai_live_activity_demo_<STAMP>`

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/992
- mergedAt: 2026-01-26T22:43:01Z
- mergeCommit: 6d9e3e417bb544ac65b0b802d1897451575d2789
