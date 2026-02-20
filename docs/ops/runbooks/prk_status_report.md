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
