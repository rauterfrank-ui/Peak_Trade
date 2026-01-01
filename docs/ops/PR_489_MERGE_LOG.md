# PR #489 — docs(ops): standardize bg_job execution pattern in Cursor multi-agent workflows

## Summary
Standardizes the bg_job execution pattern as operator tooling across Cursor multi-agent runbooks and roadmap docs.

## Why
- Establish a consistent, operator-friendly background job workflow across runbooks.
- Maintain gate compliance (no raw token patterns; no docs reference target pitfalls).

## Changes
- Documented bg_job execution pattern in the Cursor phases runbook
- Added quick-reference entry in the frontdoor runbook
- Updated the live execution roadmap docs with a bg_job toolbox/section
- Included/updated merge-log documentation related to the bg_job integration chain

## Verification
Local (recommended):
- Raw token check (expected: no matches)
  - rg -n "scripts/ops/bg_job\.sh" docs/ || true
- Docs reference targets gate (changed-files mode)
  - ./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

CI (PR #489):
- 14 succsful, 4 skipped, 0 failing
- Key gates: Docs Reference Targets, Policy Critic, Docs Diff Guard, Lint, Tests (3.9/3.10/3.11), Audit, Quarto Smoke, Test Health, Required Contexts

## Risk
Low (docs-only).

## Operator How-To
- Use the updated Cursor runbooks as the canonical reference for bg_job execution in multi-agent workflows.
- Prefer the standardized pattern as documented; avoid embedding raw script-token strings in docs.

## References
- PR #489 (merged, squash via auto-merge)
- PR #486 (gitignore-only prep for bg_job)
- PR #487 (initial integration)
- bg_job runner actual delivery: PR #PR_TBD
