# Operating Rhythm

This runbook defines the day-to-day and week-to-week operating cadence for the scheduled PR-J / PR-K / PR-O / PR-U stack.

## Daily (5–10 min)

1) Check PR-K artifacts (status + health):
- prj&#95;status&#95;latest.md / .json
- prj&#95;health&#95;summary.md / .json

Interpretation:
- **OK**: last successful schedule run is fresh.
- **STALE**: policy.action=NO_TRADE, reason PRJ&#95;STATUS&#95;STALE → investigate PR-J schedule health.
- **NO&#95;SUCCESS**: policy.action=NO_TRADE, reason PRJ&#95;STATUS&#95;NO&#95;SUCCESS → PR-J has no successful schedule run in sample.

Commands:
- scripts&#47;ops&#47;ops&#95;status.sh
- gh workflow run prk-prj-status-report.yml --ref main -f mock_mode=false
- gh run list --workflow prk-prj-status-report.yml --branch main --limit 5
- gh run download &lt;RUN_ID&gt;

2) If **STALE** or **NO&#95;SUCCESS**:
- Open the latest PR-J schedule runs and locate first failure point.
- Confirm: schedule is firing, artifacts are uploaded, validation passes.

## Weekly (15–30 min)

1) Drift detector (PR-U):
- Ensure required checks list stays aligned and no drift is reported.
- If drift: update .github&#47;required&#95;status&#95;checks&#95;main.txt or workflows producing contexts.

2) Nightly selfcheck (PR-O):
- Confirm schema validation stays green.
- If it fails: treat as contract regression; fix before relying on reports.

## Incident Playbooks

### A) PR-K reports STALE
Symptoms:
- PRJ&#95;BADGE: STALE
- policy.action=NO&#95;TRADE reason PRJ&#95;STATUS&#95;STALE

Actions:
- Inspect latest PR-J schedule run(s)
- Identify whether failure is infra (API/timeout), data freshness gate, or test regression
- Fix cause; re-run workflow&#95;dispatch if needed

### B) PR-K reports NO&#95;SUCCESS
Symptoms:
- PRJ&#95;BADGE: NO&#95;SUCCESS
- policy.action=NO&#95;TRADE reason PRJ&#95;STATUS&#95;NO&#95;SUCCESS

Actions:
- Validate PR-J schedule is enabled and cron is correct
- Look for repeated cancellations / permission issues
- Run PR-J workflow&#95;dispatch to validate end-to-end

### C) Schema validation fails (PR-O)
Actions:
- Treat as breaking contract: fix generator or schema
- Keep output_version stable or bump intentionally with migration notes

### D) Required checks deadlock (PR blocked, missing required contexts)
Use:
- scripts&#47;ops&#47;ci&#95;trigger&#95;required&#95;checks.sh

Notes:
- Never add tracked files under reports&#47;.
- Tool creates a reversible change (commit + revert) to trigger required checks without leaving markers.
