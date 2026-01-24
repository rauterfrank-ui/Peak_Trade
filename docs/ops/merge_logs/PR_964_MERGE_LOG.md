# PR #964 — MERGE LOG

## Summary
- PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;964
- Title: obs(ops): add AI Live Ops Pack v1 (alerts + dashboard ops summary)
- Risk: LOW (watch-only; NO-LIVE; no src/** changes)
- Merge mode: SQUASH (delete-branch + match-head-commit)

## Why
- Make AI Live observability operational (alerts + compact ops summary) without changing live execution posture.
- Provide at-a-glance answers: up/scraped, freshness, parse/drops spikes, latency degradation, and active alerts.

## Changes
- Added Prometheus alert rules (stable alert names) + local rule loading wiring.
- Extended Grafana execution overview with a top “AI Live — Ops Summary” row (Up/Freshness/Errors/Drops/Latency + active alerts indicator).
- Added operator runbook section for alert meaning + remediation steps.

## Verification
- CI required checks: PASS (mergeStateStatus=CLEAN; all checks SUCCESS/SKIPPED at merge time)
- Local (pre-merge):

```bash
python3 -m pytest -q tests/obs/test_grafana_operator_dashpacks_v1.py tests/obs/test_grafana_provisioning_sanity.py tests/obs/test_ai_live_ops_pack_v1.py
```

## Risk
- LOW
  - watch-only / NO-LIVE (observability + docs/tests only)
  - no src/** changes; no execution enablement; no governance bypass

## Operator How-To (watch-only)
- Exporter Port Contract v1: AI Live Exporter läuft lokal auf Port 9110 (job=ai_live wird von prometheus-local gescrapt).
- Smoke: bash scripts/obs/ai_live_smoke_test.sh
- Verify: bash scripts/obs/ai_live_verify.sh
- Grafana: Dashboard “Peak_Trade — Execution Watch Overview” öffnen → Top-Row “AI Live — Ops Summary” (Up/Freshness/Errors/Drops/Latency + active alerts).
- Alerts: Regeln in docs/webui/observability/prometheus/rules/ai_live_alerts_v1.yml (ExporterDown, StaleEvents, ParseErrorsSpike, DroppedEventsSpike, LatencyP95High [+ optional P99]).

## References
- PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;964

## Merge Evidence
```text
state: MERGED
mergedAt: 2026-01-24T06:40:33Z
mergeCommit (main): fcf3f524f357c0fa76912bd573e59690266c6ae5
headRefOid (pre-merge): f3cec7a7d8fcb5af2c75f9e482b293f736aea60e
approval_exact_comment_id: 3793977320
mergeMethod: squash
deleteBranch: yes
matchHeadCommit: yes
```
