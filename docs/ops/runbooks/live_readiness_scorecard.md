# Live Readiness Scorecard (Go/No-Go)

This is an **operational readiness** checklist for progressing:
Research → Shadow → Testnet → Live

It is **not** financial advice and does not assert profitability. The goal is to reduce operational and safety risk.

## Inputs (artifacts)

- reports&#47;status&#47;stability&#95;gate.json
- reports&#47;status&#47;prj&#95;status&#95;latest.json
- reports&#47;status&#47;prj&#95;health&#95;summary.json

## Hard Blocks (NO-GO)

- Stability Gate overall&#95;ok != true
- PR-K health status is NO&#95;SUCCESS (no successful PR-J schedule in sample)
- Any missing required artifact inputs

## Soft Signals (Score)

- Age of latest PR-K schedule success (hours)
- Age of latest PR-J schedule success (hours)
- PR-K health status OK vs STALE
- Presence of badge lines (PRJ&#95;BADGE / PRJ&#95;HEALTH&#95;BADGE)

## Suggested thresholds

- GO (very small notional, strict risk): score >= 85 AND no hard blocks
- Shadow/Testnet continues: score 60–84 or any soft warnings
- NO-GO: any hard block OR score < 60

## Operations

Manual run (local):
- python3 scripts&#47;ci&#47;live&#95;readiness&#95;scorecard.py --out-dir reports&#47;status --stability reports&#47;status&#47;stability&#95;gate.json --status reports&#47;status&#47;prj&#95;status&#95;latest.json --health reports&#47;status&#47;prj&#95;health&#95;summary.json

Workflow:
- .github&#47;workflows&#47;prbd-live-readiness-scorecard.yml
