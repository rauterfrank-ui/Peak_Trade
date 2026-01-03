# PR #491 — ops(docs,scripts): deliver bg_job runner + fix bg_job truth

## Summary
Adds the repo-native background job runner (`scripts/ops/bg_job.sh`) and its operator runbook, and restores documentation integrity by ensuring the "bg_job availability" narrative matches what is actually present in `main`.

## Why
- Operator-facing documentation and merge logs referenced `scripts/ops/bg_job.sh` as if it were already available in `main`.
- PR #491 is the actual delivery point for the bg_job runner; the missing post-merge documentation leaves the "Verified Merge Logs" index incomplete.

## Changes
- **Added** `scripts/ops/bg_job.sh` (executable): background job runner for long-running commands.
- **Added** `docs/ops/RUNBOOK_BACKGROUND_JOBS.md`: operator runbook describing run/follow/status/stop patterns.
- **Corrected** downstream documentation and merge logs so they no longer imply bg_job shipped in a `.gitignore`-only change and instead reflect actual availility after this PR.

## Verification
Run from repo root:
- Script exists and is executable:
  - `ls -la scripts/ops/bg_job.sh`
- Help output:
  - `bash scripts/ops/bg_job.sh --help`
- Docs reference targets (changed files):
  - `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main` (if present)

## Risk
Low.
- Adds an operator convenience script and documentation only.
- No live enablement; no strategy logic changes.

## Operator How-To
- Primary documentation:
  - `docs/ops/RUNBOOK_BACKGROUND_JOBS.md`
- Quick entry:
  - `bash scripts/ops/bg_job.sh --help`

## References
- PR #491: bg_job delivery + truth corrections (this PR's subject).
