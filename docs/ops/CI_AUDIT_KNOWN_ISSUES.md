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
## Cybersecurity owner-triage notes for retained CI/Ops risks v0

This note records the post-HOLD owner-triage outcome for retained cybersecurity findings R-001 through R-007. It is a documentation-only boundary note for CI/Ops known issues. It does not authorize implementation, workflow dispatches, runtime execution, scheduler or daemon control, testnet/live activity, broker/exchange/order activity, or any change to Master V2 / Double Play trading semantics.

### Source artifacts

- Owner-triage report: `/tmp/peak_trade_cybersecurity_post_hold_owner_triage_20260510T150908Z/CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md`
- Full lossless retained candidate inventory: `/tmp/peak_trade_full_lossless_risk_inventory_readonly_20260508T163523Z/FULL_LOSSLESS_RISK_CANDIDATES.jsonl`
- Top review queue: `/tmp/peak_trade_full_lossless_risk_clusters_readonly_20260508T163641Z/TOP_REVIEW_QUEUE.jsonl`

### Owner-triage outcome

The retained confirmed-risk candidates R-001 through R-007 remain accepted as cybersecurity follow-up items. They are retained for controlled follow-up, not discarded or downgraded by this note.

### Boundary

Allowed follow-up classes start with documentation-only or offline deterministic tests-only work that reuses existing CI/Ops/security surfaces.

This note explicitly does not authorize:

- scheduler, daemon, paper/shadow/testnet/live, broker, exchange, or order-submission execution
- workflow dispatches or CI-triggering changes as a side effect of triage
- runtime or hot-path changes
- Master V2 / Double Play logic changes
- Scope/Capital, Risk/KillSwitch, Execution/Live Gate, dashboard authority, AI authority, or strategy live-authority changes
- new parallel Evidence, Readiness, Map, Registry, Handoff, Package, or Pointer surfaces

### No-regression constraints

Any later mitigation for R-001 through R-007 must preserve:

- system capability
- trading logic
- Master V2 / Double Play semantics
- hot-path performance
- existing fail-closed safety posture
- traceability to the retained lossless inventory

### Recommended first slice from owner-triage

```text
Docs-only clarification in `docs/ops/CI_AUDIT_KNOWN_ISSUES.md`, adding a retained cybersecurity post-HOLD owner-triage note for R-001 through R-007. No workflow, script, runtime, testnet/live, broker/exchange/order, trading logic, Master V2, or Double Play changes.
```

### Proposed branch name (reference)

```text
`docs/cyber-post-hold-owner-triage-known-issues`
```

### Proposed files in scope (reference)

```text
- `docs/ops/CI_AUDIT_KNOWN_ISSUES.md`
```

### Proposed files out of scope (reference)

```text
- `.github/workflows/**`
- `scripts/ops/**`
- `src/**`
- `tests/**`
- `out/**`
- `reports/**`
- `docs/ops/registry/DOCS_TRUTH_MAP.md` unless an existing drift rule requires it
```

### Proposed validation commands (reference)

```text
Not executed in this turn:

- `git diff --check`
- `python3 scripts/ops/check_docs_drift_guard.py --base origin/main`
- No pytest for the docs-only first slice unless requested later.
```

### Stop conditions (reference)

```text
Stop if any action would run scheduler/daemon/paper/shadow/testnet/live commands, dispatch workflows, mutate evidence, access secrets, touch broker/exchange/order paths, alter risk/killswitch/execution semantics, or change trading/Master V2/Double Play behavior.
```

### Final verdict (reference)

```text
Proceed first with the docs-only known-issues clarification. It preserves every confirmed finding, maximizes no-regression safety, reuses an existing surface, and avoids runtime/hot-path changes.

RESULT=/tmp/peak_trade_cybersecurity_post_hold_owner_triage_20260510T150908Z/CYBERSECURITY_POST_HOLD_OWNER_TRIAGE.md
FIRST_SLICE=docs-only clarification in docs/ops/CI_AUDIT_KNOWN_ISSUES.md for retained R-001 through R-007 owner-triage boundaries
BRANCH=docs/cyber-post-hold-owner-triage-known-issues
IMPLEMENT_NOW=false
NO_LOGIC_CHANGE=true
NO_PERFORMANCE_REGRESSION=true
```
