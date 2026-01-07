# Evidence Entry: CI Required Checks Matrix Naming Contract - Deterministic Test Discovery

**Evidence ID:** EV-20260107-CI-MATRIX-CONTRACT
**Date:** 2026-01-07
**Category:** Ci/Workflow
**Owner:** ops
**Status:** DRAFT

---

## Scope
CI Required Checks Matrix Naming Contract: Deterministic test discovery and auto-merge compatibility for GitHub Actions matrix jobs. Solves "BLOCKED" status on docs-only PRs by ensuring matrix checks (e.g., `tests (3.11)`) are always created, even when skipped.

---

## Claims
- Matrix jobs always create check runs (no job-level `if:` conditions)
- Explicit naming contract: `tests (${{ matrix.python-version }})` → `tests (3.9)`, `tests (3.10)`, `tests (3.11)`
- Docs-only PRs skip via step-level guards (not job-level), ensuring all required checks report SUCCESS
- Automated contract verification via `check_required_ci_contexts_present.sh` (5 validations)
- Fix deployed: PR #362 (2025-12-26), solves PR #361 BLOCKED issue

---

## Evidence / Source Links
- [Matrix Naming Contract Doc](../ci_required_checks_matrix_naming_contract.md)
- [CI Workflow: .github/workflows/ci.yml](../../../.github/workflows/ci.yml)
- [Contract Guard Script](../../../scripts/ops/check_required_ci_contexts_present.sh)
- [PR #362: Matrix naming fix](https://github.com/rauterfrank-ui/Peak_Trade/pull/362)
- [PR #512: Fail-open + concurrency hardening](https://github.com/rauterfrank-ui/Peak_Trade/pull/512)

---

## Verification Steps
1. Check contract doc: `cat docs/ops/ci_required_checks_matrix_naming_contract.md | grep -A 5 "Contract"`
2. Verify guard script: `../../../scripts/ops/check_required_ci_contexts_present.sh`
3. Inspect CI workflow: `grep -A 10 'name: tests' .github/workflows/ci.yml`
4. Test docs-only PR: Create PR with only markdown changes, verify `tests (3.11)` check appears
5. Expected: Guard script exits 0, matrix checks always created, auto-merge works on docs-only PRs

---

## Risk Notes
- Contract requires manual adherence when adding new required checks (checklist in doc)
- Guard script uses grep/regex (no YAML parser) — may miss complex edge cases
- Matrix jobs still run (consume CI minutes) even when skipped via step-level guards
- Breaking contract causes auto-merge failures (PRs stuck in BLOCKED state)
- Docs-only detection relies on `changes` job output (must be accurate)

---

## Related PRs / Commits
- PR #362: Matrix naming fix (merged 2025-12-26, commit 42a7d07)
- PR #361: Original BLOCKED issue (docs-only PR, missing `tests (3.11)` check)
- PR #512: Fail-open changes + concurrency hardening + contract guard deployment
- Contract guard: scripts/ops/check_required_ci_contexts_present.sh (5 validations)

---

## Owner / Responsibility
**Owner:** ops
**Contact:** [TBD]

---

**Entry Created:** 2026-01-07
**Last Updated:** 2026-01-07
**Template Version:** v0.2
