# PR #292 — chore(ci): enforce formatter policy drift guard in gate workflow

## Summary
PR #292 enforces the formatter policy drift guard in CI by running `scripts/ops/check_no_black_enforcement.sh`
in the always-run Lint Gate workflow. This prevents reintroduction of `black --check` enforcement in workflows/scripts.

- PR: #292
- Merge commit: MERGE_COMMIT_SHA
- Branch: chore/ci-enforce-formatter-policy-guard → main

## Why
Local enforcement via `ops doctor` is great, but CI enforcement makes drift prevention automatic and PR-blocking when violations are introduced.

## Changes
- `.github/workflows/lint_gate.yml`
  - Added step: **Formatter policy drift guard (no black enforcement)**
  - Runs immediately after checkout and before Python-file detection
  - Always runs (including docs-only PRs) and fails only on policy violation
- `docs/ops/README.md`
  - Documented enforcement points: local (`ops doctor`) + CI (Lint Gate)

## Verification
CI checks:
- ✅ Lint Gate — PASS
- ✅ Guard tracked files — PASS
- ✅ Policy Critic Gate — PASS
- ✅ audit — PASS (or ALLOWED FAIL if configured)
- ✅ tests (3.11) — PASS

Local sanity:
- `bash scripts/ops/check_no_black_enforcement.sh` → PASS

## Risk
Low. The new CI step is a fast grep-based guard (<1s) and should not block docs-only PRs because it exits 0 when compliant.

## Operator How-To
- Local check:
  - `bash scripts/ops/check_no_black_enforcement.sh`
  - `ops doctor` (Formatter Policy Health)
- CI behavior:
  - Any PR introducing `black --check` enforcement in workflows/scripts will fail the Lint Gate and block merge.

## References
- PR #292
- Guard script: `scripts/ops/check_no_black_enforcement.sh`
- Workflow: `.github/workflows/lint_gate.yml`
