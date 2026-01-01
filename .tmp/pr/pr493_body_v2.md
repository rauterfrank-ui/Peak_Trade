## Summary
Rescued documentation hardening focused on reference-target integrity and parity improvements across the docs verification workflow.

## Why
- Reduce "missing target" noise while keeping strictness where it matters (changed files / priority areas).
- Make the docs-reference-targets gate more operator-friendly and maintainable.

## What changed
- Reference-target verification parity improvements (changed-files mode / priority triage).
- Ignore-list support for known historical/worklog areas (documented, bounded).
- Priority fixes in ops/risk-related docs references.

## Verification
**Foundation**
- `uv run ruff format --check .`
- `uv run ruff check .`
- `pytest -q` (optional for docs-only, but recommended if scripts touched)
- `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`

**Governance**
- Policy Critic gates expected green (docs-only; no enable-flags, no policy-triggering literal patterns).
- Docs Diff Guard Policy Gate expected green.

**Shadow**
- N/A (docs-only). Confirm no text implies enabling live execution; keep docs phrasing "manual-only / shadow-only / blocked by default".

## Risk
Low.
- Docs-only changes with bounded verification logic.
- No runtime behavior change expected.

## Operator notes
- Use the docs reference targets verifier in `--changed` mode for routine PRs.
- Use the ignore list only for documented legacy/worklog zones; do not expand without a rationale.

## Rollback
Revert PR commit(s) if any unintended gate behavior occurs.
