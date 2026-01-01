# PR #486 — ops(scripts): add bg_job runner (exitcode capture)

## Summary
Adds a repository-native background job runner to avoid Cursor/terminal timeouts for long-running commands, with PID/log/exitcode tracking and macOS sleep prevention via `caffeinate`. Also ignores runtime job artifacts via `.gitignore`.

## Why
Cursor and interactive terminals can time out or hang on long-running commands (full docs scans, long pytest runs, watch commands). A standardized background runner improves operator reliability and provides stable logs and exitcode capture.

## Changes
- Added `scripts/ops/bg_job.sh`: background job runner supporting `run`, `follow`, `status`, `stop`, `latest`, `list`.
- Ensured exitcode capture via a per-job `.exit` marker file (generated at runtime).
- Ignored runtime job artifacts via `.gitignore` to prevent accidental tracking.

## Verification
Commands (local):
- `bash scripts/ops/bg_job.sh --help | head -20`
- `bash scripts/ops/bg_job.sh run smoke_exit -- echo "ok"`
- `sleep 1 && bash scripts/ops/bg_job.sh status smoke_exit`
- `cat "$(bash scripts/ops/bg_job.sh latest smoke_exit)"`

Expected:
- Status shows NOT RUNNING and EXITCODE 0.
- Latest log contains "ok".

## Risk
Low. Adds an ops helper script and ignores `.logs/`. No production execution logic changed.

## Operator How-To
Typical usage:
- Start long job: `bash scripts/ops/bg_job.sh run <label> -- <command...>`
- Follow logs: `bash scripts/ops/bg_job.sh follow <label>`
- Check status/exit: `bash scripts/ops/bg_job.sh status <label>`
- Stop job: `bash scripts/ops/bg_job.sh stop <label>`

Examples:
- Docs full scan: `bash scripts/ops/bg_job.sh run docs_refs_full -- ./scripts/ops/verify_docs_reference_targets.sh`
- Pytest: `bash scripts/ops/bg_job.sh run pytest_full -- pytest tests/ -v`
- PR watch: `bash scripts/ops/bg_job.sh run pr_checks_watch_486 -- gh pr checks 486 --watch`

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/486
- Merged at: 2026-01-01T11:04:15Z
- Merge SHA (main tip at time of log creation): 11f0233
