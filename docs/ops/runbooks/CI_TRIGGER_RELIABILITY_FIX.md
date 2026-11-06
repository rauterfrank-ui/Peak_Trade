# CI Trigger Reliability Fix

## Goal
Normalize pull request trigger behavior so PR checks start reliably on normal PR lifecycle events.

## Trigger contract
For PR-relevant workflows, use:
- `opened`
- `synchronize`
- `reopened`
- `ready_for_review`

## Why
GitHub default pull request types do not include `ready_for_review`. Draft-to-ready transitions can therefore miss expected PR runs unless this type is explicit.

## Scope
This fix is limited to workflow trigger reliability.
It does not change trading/runtime behavior and does not touch paper/shadow/evidence data.

## Exact-head Ready reuse (narrow optimization)

Draft PRs still execute the full fail-closed validation suite on `opened` / `synchronize` / `reopened`.

`ready_for_review` remains an **explicit reliability event** and stays declared on the producer workflows.
It does **not** require a second complete suite when all of the following are proven:

1. current PR head SHA is unchanged,
2. each relevant Required Context already has an authoritative `completed` + `success` check-run on that exact head,
3. the check-run is owned by GitHub Actions (`app_id=15368`),
4. the verifier can page the Checks API and fails closed on API/permission/malformed payloads.

Implementation owner: `scripts/ci/exact_head_ready_reuse.py`.
Canonical Required Context set: `config/ci/required_status_checks.json` (no second truth list).

### Behavior

| Event | Behavior |
|-------|----------|
| `opened` / `synchronize` / `reopened` | Full validation (unchanged). |
| `ready_for_review` + exact-head reuse proven | Lightweight verifier path; Required Context **job names** still conclude success (no job-level skip of required checks). Heavy work is short-circuited. |
| `ready_for_review` + unproven / missing / failed / pending / wrong SHA / wrong app / API error | Full validation runs (reuse=false). Fail-closed on the reuse claim. |
| `ready_for_review` + verifier/bootstrap failure | Probe emits `reuse=false` and exits 0; Required jobs still run full validation (no skip cascade). |

### Safe verifier bootstrap

The Ready-reuse probe does **not** rely on the verifier already existing on `pull_request.base.sha`, and does **not** use raw unauthenticated `git fetch` over HTTPS.

Instead, on `ready_for_review` an isolated `actions&#47;checkout@v4` sparse-checkout loads only the verifier (+ its SSOT config helper) from:

- `repository: github.event.pull_request.head.repo.full_name`
- `ref: github.event.pull_request.head.sha` (exact SHA, never branch/base/main)
- `path: .ready-reuse-head`
- `persist-credentials: false`

The probe then proves `git -C .ready-reuse-head rev-parse HEAD` equals the PR head SHA and executes only `.ready-reuse-head&#47;scripts&#47;ci&#47;exact_head_ready_reuse.py` with read-only permissions (`contents` / `checks` / `pull-requests` / `actions`: read). Any checkout/path/SHA/API/tooling failure normalizes to `reuse=false` and continues into full validation.

### Non-goals

- No Required Context renames.
- No branch-protection / ruleset edits.
- No Draft coverage reduction.
- No `pull_request_target`.
- No write permissions / secrets exposure for the reuse probe.
- No skip-cascade of Required Contexts when reuse cannot be proven.
- No automatic Ready / merge / admin bypass.
