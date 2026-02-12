# Merge Evidence
- mergedAt: 2026-01-24T07:46:06Z
- mergeCommit: aea53bdda0e38106d97722d5e78707ec1abc1239

# PR #966 — MERGE LOG

## Summary
- Merged PR #966 (AI Live Ops: deterministic v1 rules mount + ops verify).
- Scope: observability/ops (docs/scripts/tests/compose); NO-LIVE unchanged.

## Why
- Make AI Live Ops Pack deterministic and reproducible on fresh local start (rules load without manual copy/restart), plus single-shot verifier.

## Changes
- Deterministic Prometheus rules loading for AI Live Ops Pack v1 (rules mount / startup path).
- Add single-shot verifier script for AI Live Ops expectations (rules + dashboard ops row + hardened queries).
- Targeted tests for ops pack + determinism; existing Grafana operator dashpack/provisioning sanity tests continue to pass.

## Verification
- Local: targeted tests green (per PR evidence).
- CI: required checks green prior to merge; Cursor Bugbot may report NEUTRAL (treated non-blocking for this merge).

## Risk
- LOW–MED (no src/** execution paths; watch-only/observability ops).
- Governance: NO-LIVE unchanged.

## Operator How-To
1. Start local stack (Prometheus-local + Grafana) via `scripts/obs/grafana_local_up.sh`.
2. Run verifier: `bash scripts/obs/ai_live_ops_verify.sh`.
3. Confirm rules loaded: curl http:&#47;&#47;127.0.0.1:9092&#47;api&#47;v1&#47;rules | head
4. Open Grafana dashboard: “Peak_Trade — Execution Watch Overview”; verify “AI Live — Ops Summary” row is populated.

## References
- PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;966
