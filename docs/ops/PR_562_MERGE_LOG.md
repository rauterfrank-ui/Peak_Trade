# PR #562 — Merge Log

## Summary
AI-Ops Toolchain v1.1: standardized promptfoo eval execution via a robust runner, added non-blocking/path-filtered CI coverage, introduced an eval scoreboard, and expanded governance-critical eval testcases. This improves operator safety and auditability without touching trading logic.

## Why
- Provide a reproducible, operator-friendly eval runner with deterministic artifact handling.
- Add advisory CI signal for AI-Ops changes (rules/commands/docs/evals), without hard-blocking merges.
- Establish a baseline/scoreboard to detect policy drift and regressions in governance behavior.
- Extend eval coverage for "no autonomous live trading", "no trading-logic changes", and "audit-stable output contracts".

## Changes
### Evals Runner
- Added `scripts/aiops/run_promptfoo_eval.sh`
  - Robust pre-flight (repo checks, clear logging)
  - Graceful skip when `OPENAI_API_KEY` is missing (exit 0)
  - Writes logs/artifacts into `.artifacts/aiops/` (ignored)

### CI Workflow (Advisory)
- Added `.github/workflows/aiops-promptfoo-evals.yml`
  - Path-filtered triggers for: `.cursor/**`, `docs/ai/**`, `evals/aiops/**`, `scripts/aiops/**`
  - Non-blocking / advisory intent
  - Skips cleanly if `OPENAI_API_KEY` secret is not available

### Scoreboard
- Added `docs/ai/AI_EVALS_SCOREBOARD.md`
  - Baseline tracking guidance (date/sha/model/pass-rate)
  - Drift interpretation and operator decision workflow
- Linked from `docs/ai/AI_EVALS_RUNBOOK.md`

### Governance-Critical Testcases
- Added:
  - `evals/aiops/testcases/governance_lock_no_live_execution.yaml`
  - `evals/aiops/testcases/no_trading_logic_changes.yaml`
  - `evals/aiops/testcases/audit_stable_output_contract.yaml`
- Registered in `evals/aiops/promptfooconfig.yaml`

### Hygiene
- Updated `.gitignore` to ensure `.artifacts/` is untracked.

## Verification
### Local
- No API key (should skip successfully):
  - `bash scripts/aiops/run_promptfoo_eval.sh`
- With API key:
  - `export OPENAI_API_KEY="sk-..." && bash scripts/aiops/run_promptfoo_eval.sh`
- Confirm repo stays clean (artifacts ignored):
  - `git status -sb`

### CI
- Confirm workflow triggers only on relevant path changes (rules/docs/evals/scripts).
- Confirm job skips cleanly when `OPENAI_API_KEY` secret is not set.
- Confirm advisory behavior (signal only; not a hard governance gate).

## Risk
LOW — Tooling/docs/evals only. No changes to `src/`, no execution logic changes, no new runtime dependencies, and no live-execution automation introduced.

## Operator How-To
- Preferred local run:
  - `bash scripts/aiops/run_promptfoo_eval.sh`
- Cursor shortcut:
  - Use `/pt-eval` (delegates to the runner workflow as documented).
- Artifacts/logs:
  - Review `.artifacts/aiops/promptfoo_eval_*.log` for results and regressions.
- When adding new eval coverage:
  - Add a testcase under `evals/aiops/testcases/` and register it in `evals/aiops/promptfooconfig.yaml`.
- Governance note:
  - Evals inform operator decisions; they do not enable autonomous live trading.

## References
- PR: #562
- Related docs:
  - `docs/ai/AI_EVALS_RUNBOOK.md`
  - `docs/ai/AI_EVALS_SCOREBOARD.md`
  - `docs/ops/runbooks/CURSOR_MULTI_AGENT_INTEGRATION_RUNBOOK_V1.md`
