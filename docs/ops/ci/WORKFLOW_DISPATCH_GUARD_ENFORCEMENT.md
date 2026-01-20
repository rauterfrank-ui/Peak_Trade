# Workflow Dispatch Guard — Enforcement Policy

## Activation Status (Operational)

**Policy Decision:** ✅ ENFORCE (same-day, based on burn-in)  
**Activation State:** ⚠️ NOT ACTIVE as a required check on `main` (operator action pending)  
**Expected Required Check Context:** `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`  
**Verification Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`

**What this means:**
- The guard is implemented and functional.
- Enforcement is **not** effective until GitHub branch protection/ruleset includes the required check context above.

**Operator Action Required (Summary):**
- Add `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard` to `main` required checks
- Re-verify with a workflow-touching PR and append evidence addendum

## Status

**Target:** ACTIVE as Required Check (after operator activation)

## Check Details

- **Workflow Name:** `CI &#47; Workflow Dispatch Guard`
- **Job Name:** `dispatch-guard`
- **Required Check Context:** `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`
- **Path:** `.github/workflows/ci-workflow-dispatch-guard.yml`

## Timeline

| Date | Event | Details |
|------|-------|---------|
| 2026-01-12 | Guard Deployed | Phase 5C implementation + PR #663 merge log |
| 2026-01-12 | First True Positive | PR #664: Found bug in `offline_suites.yml` |
| 2026-01-12 | Burn-in Complete | 1 PR validated (no false positives) |
| 2026-01-12 | Policy Decision | ✅ ENFORCE (same-day based on proven effectiveness) |
| 2026-01-12 | Verification | Evidence captured, activation procedure documented |
| TBD | Enforcement Activation | **PENDING**: Operator to add to required checks for `main` |

## Rationale

**Why Required (Policy Decision):**
- **Proven Effectiveness:** Found real bug (PR #664) on first run
- **Low False Positive Rate:** 100% true positive in burn-in (1/1)
- **Prevent Regressions:** Guards against Phase 5B-class bugs (workflow_dispatch input context errors)
- **Minimal Disruption:** Path-filtered (only runs on workflow changes)
- **Fast Execution:** Stdlib-only, no dependencies, <5s runtime

**Why Not Yet Active (Operational):**
- Operator action required to add check to GitHub branch protection settings
- No technical blocker; purely an administrative/settings step

**What It Prevents:**
1. Using `github.event.inputs.<name>` without defining input under `on.workflow_dispatch.inputs`
2. Referencing `github.event.inputs` in workflows without `workflow_dispatch` trigger
3. Confusing `inputs.<name>` (workflow_call) with `github.event.inputs.<name>` (workflow_dispatch)

## Enforcement Configuration

**Current Status:** ⚠️ NOT CONFIGURED (awaiting operator action)

### GitHub Settings → Branches → Branch Protection Rules

**Branch:** `main`

**Required Status Checks (TO BE ADDED):**
- Enable: ✅ Require status checks to pass before merging
- Check: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard` ← **ADD THIS**

**Alternative (Rulesets - Modern):**
- GitHub → Settings → Rules → Rulesets
- Target: `main` branch
- Required checks: Add `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard` ← **ADD THIS**

## Bypass/Override Policy

**When to Bypass:**
- ❌ **NEVER** for actual workflow changes
- ⚠️ **RARE EXCEPTION:** Documentation-only PRs that don't touch workflows (check auto-skips anyway via path filter)

**How to Bypass (Admin-only):**
- Requires admin privileges
- Use `gh pr merge <PR> --admin` OR GitHub UI admin override
- **Audit Requirement:** Document reason in PR comment before override

## Rollback Plan

**If False Positives Detected:**

1. **Immediate Action:**
   - Open GitHub Issue documenting false positive (workflow file, line, context)
   - Label issue: `bug&#47;false-positive`, `ci/guard`

2. **Temporary Mitigation:**
   - Remove check from required list (Settings → Branch Protection)
   - Guard still runs but doesn't block merge
   - Document decision in issue

3. **Fix & Re-enable:**
   - Fix guard logic in `scripts/ops/validate_workflow_dispatch_guards.py`
   - Add regression test to `tests/ops/test_validate_workflow_dispatch_guards.py`
   - Re-validate with 2-3 PRs
   - Re-add to required checks

## Owner & Contacts

- **Owner:** Ops Team
- **Technical Owner:** CI/CD Automation
- **Policy Owner:** Engineering Lead
- **Escalation:** GitHub Admin / DevOps Lead

## References

- **Guard Script:** `scripts/ops/validate_workflow_dispatch_guards.py`
- **CI Workflow:** `.github/workflows/ci-workflow-dispatch-guard.yml`
- **Documentation:** `docs/ops/ci/WORKFLOW_DISPATCH_GUARD.md`
- **Tests:** `tests/ops/test_validate_workflow_dispatch_guards.py`
- **Validation PRs:**
  - PR #663: Phase 5B fix (original regression this guards against)
  - PR #664: First true positive (offline_suites.yml bug)

## Metrics & KPIs

**Target:**
- False Positive Rate: <5%
- True Positive Rate: >90%
- Execution Time: <10s

**Burn-in Phase Results (as of 2026-01-12):**
- False Positive Rate: 0% (0/1 PRs)
- True Positive Rate: 100% (1/1 bugs found)
- Execution Time: ~3s (stdlib-only)

**Post-Enforcement Metrics:**
- ⚠️ N/A (enforcement not yet active)
- Will be tracked after operator activation

## Version

- **v1.0** (2026-01-12) — Initial enforcement policy
