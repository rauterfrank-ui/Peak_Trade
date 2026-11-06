# PR #664 — Merge Log

## Summary
PR **#664** fixes a `workflow_dispatch` input-context bug in `.github/workflows/offline_suites.yml` by replacing `inputs.suite_type` with `github.event.inputs.suite_type` at two lines. Guard + tests are green.

## Why
Phase 5C Dispatch Guard detected incorrect context usage that prevented manual dispatch runs from reading `suite_type`.

## Changes
- `.github/workflows/offline_suites.yml`: 2-line substitution (`inputs.suite_type` → `github.event.inputs.suite_type`)

## Verification
- Workflow Dispatch Guard: **0 findings**
- Pytest ops guard tests: **pass**
- CI: (link/run-id after merge)

## Risk
LOW — CI workflow-only, minimal substitution. No runtime/trading logic affected.

## Operator How-To
No action required. Manual dispatch now uses correct input context.

## References
- PR #664
- Phase 5C Dispatch Guard
- Found by: `scripts/ops/validate_workflow_dispatch_guards.py`
- Commit: 77248c717ee17e900d7c7aad09cf3eceb17aac49
