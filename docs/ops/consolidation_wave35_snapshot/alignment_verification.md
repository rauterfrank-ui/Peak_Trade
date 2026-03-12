# Alignment Verification — Config vs GitHub

**Timestamp:** 2026-03-12  
**Scope:** Post-Wave 34 + Wave 33 retry

---

## Comparison

| Source | Required Contexts Count | Contexts |
|--------|-------------------------|----------|
| **Config** (`config/ci/required_status_checks.json`) | 9 | Guard tracked files in reports directories, audit, tests (3.11), strategy-smoke, Policy Critic Gate, Lint Gate, dispatch-guard, docs-token-policy-gate, docs-reference-targets-gate |
| **GitHub** (branch protection API) | 9 | Same list, identical order |

---

## Verification Result

**Status: ✅ ALIGNED**

- Config `required_contexts` and GitHub `required_status_checks.contexts` match **exactly**.
- No remaining mismatch.
- No ambiguity.

---

## Operational Meaning

1. **Branch protection:** PRs to `main` must pass all 9 required checks.
2. **Validator:** `validate_required_checks_hygiene.py` (with matrix expansion from Wave 34) correctly recognizes `tests (3.11)` as produced by CI matrix job.
3. **Hygiene gate:** `required-checks-hygiene-gate` validates that all 9 required contexts are producible by always-on PR workflows.
4. **Docs:** CI.md and GATES_OVERVIEW.md state alignment; wording is accurate post-Wave 33 retry.

---

## Ignored Contexts (Not Required by GitHub)

- `CI Health Gate (weekly_core)` — scheduled/informational
- `Docs Diff Guard Policy Gate` — informational

These remain in config `ignored_contexts` and are correctly excluded from required-check validation.
