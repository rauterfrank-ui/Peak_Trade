# Workflow Dispatch Guard — Enforcement Policy

## Activation Status (Operational)

**Policy Decision:** ✅ ENFORCE (same-day, based on burn-in)  
**Activation State:** ✅ ACTIVE as a required check on `main` (Phase 5C activation complete)  
**Required Check Context (job name):** `dispatch-guard`  
**JSON SSOT:** `config/ci/required_status_checks.json` — `dispatch-guard` in `required_contexts`  
**Verification Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`  
**Closeout:** `docs/ops/PHASE5C_WORKFLOW_DISPATCH_GUARD_ENFORCEMENT_CLOSEOUT.md`

**What this means:**
- The guard is implemented, functional, and listed in the repo JSON required-check SSOT.
- Phase 5C branch-protection activation is **complete** (2026-01-12); merge to `main` requires a passing `dispatch-guard` check.
- This policy doc describes CI governance only — **not** live, testnet, runtime, arming, or gate-lift authority.

## Status

**Current:** ACTIVE as Required Check (aligned with JSON SSOT and Phase 5C closeout)

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
| 2026-01-12 | Enforcement Activated | `dispatch-guard` added to `main` required checks (Phase 5C closeout) |

## Rationale

**Why Required (Policy Decision):**
- **Proven Effectiveness:** Found real bug (PR #664) on first run
- **Low False Positive Rate:** 100% true positive in burn-in (1/1)
- **Prevent Regressions:** Guards against Phase 5B-class bugs (workflow_dispatch input context errors)
- **Minimal Disruption:** Always-on PR check with internal change detection; no-op pass when no workflow files change
- **Fast Execution:** Stdlib-only, no dependencies, <5s runtime

**What It Prevents:**
1. Using `github.event.inputs.<name>` without defining input under `on.workflow_dispatch.inputs`
2. Referencing `github.event.inputs` in workflows without `workflow_dispatch` trigger
3. Confusing `inputs.<name>` (workflow_call) with `github.event.inputs.<name>` (workflow_dispatch)

## Enforcement Configuration

**Current Status:** ✅ CONFIGURED — `dispatch-guard` in `config/ci/required_status_checks.json` and Phase 5C branch protection (see closeout).

### GitHub Settings → Branches → Branch Protection Rules

**Branch:** `main`

**Required Status Checks (active since Phase 5C):**
- Enable: ✅ Require status checks to pass before merging
- Check: `dispatch-guard` (job name; workflow display: `CI / Workflow Dispatch Guard`)

**Alternative (Rulesets - Modern):**
- GitHub → Settings → Rules → Rulesets
- Target: `main` branch
- Required checks: include `dispatch-guard` per JSON SSOT

**Reconciliation:** `scripts/ops/reconcile_required_checks_branch_protection.py --check` with `--required-config config/ci/required_status_checks.json`

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
- Tracked post Phase 5C activation; see closeout and merge-log evidence for historical runs
- Validator: `python scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn`
- Hygiene: `python scripts/ci/validate_required_checks_hygiene.py --config config/ci/required_status_checks.json --workflows .github/workflows --strict`

## Non-authority boundary (docs sync)

- Updating this enforcement policy **does not** authorize live, testnet, paper/shadow, scheduler, or runtime activity.
- **No** workflow YAML change is implied by enforcement-status documentation alone.
- Guard failure blocks merge of workflow changes — it does **not** grant execution or arming authority.

## Version

- **v1.0** (2026-01-12) — Initial enforcement policy
- **v1.1** (2026-06-07) — Status sync: ACTIVE aligned with JSON SSOT + Phase 5C closeout (docs-only; `GO_REPO_DOCS_TESTS_WORKFLOW_DISPATCH_GUARD_ENFORCEMENT_STATUS_SYNC_V0`)
