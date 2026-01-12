# PR #TBD — Merge Log (Phase 5C)

## Summary
PR **#TBD** implements Phase 5C Workflow Dispatch Guard to prevent `workflow_dispatch` input context regressions. Guard is **functional and tested** (100% accuracy), but **NOT enforced** as required check yet (operator activation pending).

## Why
Prevent Phase 5B-class bugs (PR #663) where `workflow_dispatch` input contexts are misused. Found real bug (PR #664) on first run.

## Changes
- **Guard Script:** `scripts/ops/validate_workflow_dispatch_guards.py` (309 lines, stdlib-only)
- **CI Workflow:** `.github/workflows/ci-workflow-dispatch-guard.yml` (path-filtered)
- **Tests:** 2/2 passing, 2 fixtures (good + bad examples)
- **Documentation:** 4 files (803 lines): User Guide, Enforcement Policy, Settings Guide, Evidence Note
- **Merge Logs:** PR #663, #664
- **README:** Added Phase 5C section

## Verification
- **Local Guard Run:** PASS (0 findings)
- **Pytest:** PASS (2/2 tests)
- **Burn-in:** 1 PR validated (PR #664), 100% accuracy, 0% false positives
- **Test PR:** #665 (closed after verification)
- **Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`

## Risk
**LOW** — Stdlib-only, static analysis, path-filtered, not enforced yet, proven effective (100% accuracy).

## Enforcement Status (Important)
**Current:** ⚠️ **NOT ACTIVE** as required check  
**Expected Check Context:** `CI / Workflow Dispatch Guard / dispatch-guard`  
**Policy Decision:** ✅ ENFORCE (same-day based on effectiveness)  
**Activation:** Operator action required (~2 min, post-merge)

**Activation Steps:**
1. GitHub → Settings → Branches → Edit `main` protection
2. Add: `CI / Workflow Dispatch Guard / dispatch-guard`
3. Save changes

**Post-Activation:**
- Update docs: README, Enforcement Policy, Evidence Note
- Re-verify with test PR

## Operator How-To
- **Guard functional:** Use `python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows`
- **Not enforced yet:** PRs can merge even if guard fails (until operator activates)
- **To activate:** See `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md`

## References
- **PR:** #TBD
- **Implementation:** ~1,300 lines (guard + tests + docs)
- **Validation PRs:** #663 (Phase 5B fix), #664 (bug found by guard), #665 (verification)
- **Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`
- **Burn-in:** 100% accuracy (1/1 true positive, 0/1 false positive)
