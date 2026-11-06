# PR #295 — chore(ops): guard formatter policy CI enforcement (doctor)

## Summary
Adds a "Guard-the-Guardrail" check so `ops doctor` verifies that CI enforcement for the formatter policy drift guard is still present.

- PR: #295
- Merge commit: 91d396023f101185e039e018830d142ed50f4d20
- Branch: chore/guard-formatter-policy-ci-enforced → main

## Why
We enforce "no black enforcement" already, but now we also ensure the CI enforcement step itself can't quietly disappear.

## Changes
- `scripts/ops/check_formatter_policy_ci_enforced.sh` (new)
  - Verifies `.github/workflows/lint_gate.yml` still runs `scripts/ops/check_no_black_enforcement.sh`
  - Exit 0 when enforced; exit 1 if missing
- `scripts/ops/ops_center.sh`
  - Runs the new check in `ops doctor` right after `check_no_black_enforcement.sh`
- `docs/ops/README.md`
  - Notes that `ops doctor` also verifies CI enforcement presence

## Verification
- Local:
  - `bash scripts/ops/check_formatter_policy_ci_enforced.sh` → PASS
  - `bash scripts/ops/check_no_black_enforcement.sh` → PASS
  - `ops doctor` → PASS

## Risk
Low. Read-only grep check; fails only if CI enforcement disappears.

## Operator How-To
- Run locally:
  - `bash scripts/ops/check_formatter_policy_ci_enforced.sh`
  - `ops doctor`

## References
- PR #295
- `.github/workflows/lint_gate.yml`
- `scripts/ops/check_no_black_enforcement.sh`
