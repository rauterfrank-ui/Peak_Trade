# PR-K — PR-J Status Report (Daily)

## Goal
Generate a daily status snapshot of the PR-J smoke workflow:
- last N runs (schedule + workflow_dispatch)
- counts by conclusion
- links to latest successful schedule run
- quick metadata (createdAt, updatedAt, duration)

## Outputs
Uploaded as GitHub Actions artifacts:
- `reports&#47;status&#47;prj_status_latest.json`
- `reports&#47;status&#47;prj_status_latest.md`

No repo writes, no secrets, read-only permissions.

## Staleness Policy (Informational)
When the last successful schedule run is older than a configurable threshold (default 36h), the report includes:
- **JSON:** `policy: {"action":"NO_TRADE","reason_codes":["PRJ_STATUS_STALE"]}`
- **MD:** A prominent `⚠️ STALE — NO_TRADE` banner

This is a pure safety signal: no trading recommendation when status data is stale. Use `--stale-hours` and `--now` (ISO8601) for tuning or deterministic tests.

<!-- CI-TRIGGER: workflow-yaml-fix 20260222T171500Z -->
<!-- CI-TRIGGER: pr1556 20260222T180000Z -->

<!-- CI-TRIGGER: 20260222T180542Z PR-1557 -->
