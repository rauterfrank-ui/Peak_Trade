# CI Audit — Known Issues

## Current status
- Historical context: GitHub [Issue #252](https://github.com/rauterfrank-ui/Peak_Trade/issues/252) tracked an older formatter drift described as a Black formatting/configuration issue.
- Current CI policy is Ruff-oriented. `scripts/ops/run_audit.sh` runs `ruff check .` and `ruff format --check .`; `scripts/ops/check_no_black_enforcement.sh` guards against `black --check` enforcement in workflows/scripts.
- `audit` findings are not all hard failures in every workflow path. In `.github/workflows/audit.yml`, `pip-audit` is blocking only for dependency-relevant changes and non-blocking for docs-only scope. The `run_audit.sh` step is currently wrapped so findings are surfaced but do not by themselves fail that workflow step.
- `lint_gate.yml` remains a separate enforcement surface: it always creates a check run, fails on Black-enforcement drift, and runs Ruff lint/format checks when Python files changed.

## What to check
- Confirm `strategy-smoke`, `tests`, and health gates are green for merge readiness.
- If `audit` or lint/format checks report findings, cross-check the workflow, trigger, and changed-file scope before treating the finding as merge-blocking.
- Distinguish technically enforced gates from advisory audit output or policy-language documentation.

## Tracking
- Historical formatter drift / Black wording: [Issue #252](https://github.com/rauterfrank-ui/Peak_Trade/issues/252)
- Current formatter source of truth: Ruff format checks, not Black enforcement.

## Local reproduction
```bash
ruff check .
ruff format --check .
bash scripts/ops/check_no_black_enforcement.sh
```

## Blocking model
- Technically enforced:
  - `pip-audit` in `.github/workflows/audit.yml` when dependency-relevant files changed.
  - `lint_gate.yml` Ruff lint/format checks when Python files changed.
  - `lint_gate.yml` Black-enforcement drift guard.
- Advisory / surfaced but not hard-failing in the current `audit.yml` wrapper:
  - `run_audit.sh` findings emitted by the `Run audit script (full checks)` step.
  - `pip-audit` findings for docs-only scope.
- Policy-language only:
  - Any historical reference to Black or Issue #252 unless a workflow/script actually enforces Black.

## Next steps
1. Clarify policy/docs if CI enforcement changes.
2. Keep future wording aligned with Ruff format/check surfaces and workflow-specific blocking behavior.
3. Do not perform a broad Black formatting sweep from this historical issue alone.
