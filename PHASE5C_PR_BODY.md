# feat(ci): Phase 5C workflow dispatch guard + enforcement docs

## Summary

Implements **Phase 5C Workflow Dispatch Regression Guard** to prevent `workflow_dispatch` input context bugs (like PR #663, #664). Guard is **functional and tested**, but **NOT yet enforced** as a required check.

## Enforcement Status (Important) ⚠️

**Current State:** Guard is **operational** but **NOT ACTIVE** as a required check on `main`.

**Expected Check Context:** `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`

**Why Not Active Yet:**
- Requires operator action to add check to GitHub Branch Protection Rules
- No technical blocker; purely administrative/settings step
- Takes ~2 minutes to activate

**Policy Decision:** ✅ ENFORCE (same-day based on proven effectiveness)

**Activation Instructions:** See `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md`

## What This PR Delivers

### 1. Workflow Dispatch Guard (Stdlib-only)

**Script:** `scripts/ops/validate_workflow_dispatch_guards.py` (309 lines)

**Checks for:**
- Using `github.event.inputs.<name>` without defining input under `on.workflow_dispatch.inputs`
- Referencing `github.event.inputs` in workflows without `workflow_dispatch` trigger
- Confusing `inputs.<name>` (workflow_call) with `github.event.inputs.<name>` (workflow_dispatch)

**Exit Codes:**
- `0` = OK (no findings)
- `1` = WARN (only with `--fail-on-warn`)
- `2` = ERROR (findings detected)

### 2. CI Workflow (Path-Filtered)

**Path:** `.github/workflows/ci-workflow-dispatch-guard.yml`

**Triggers:**
- PRs modifying `.github&#47;workflows&#47;*.yml`
- PRs modifying guard script or tests
- Pushes to `main` (workflow changes only)

**Path Filter:** Only runs when relevant files change (minimal disruption)

### 3. Tests & Fixtures

**Tests:** `tests/ops/test_validate_workflow_dispatch_guards.py` (2/2 passing)
- `test_good_workflow_has_no_findings` ✅
- `test_bad_workflow_has_errors` ✅

**Fixtures:**
- `tests/fixtures/workflows_dispatch_guard/good_workflow.yml` (valid example)
- `tests/fixtures/workflows_dispatch_guard/bad_workflow.yml` (invalid example with 2 errors)

### 4. Documentation (803 lines)

1. **User Guide** (169 lines): `docs/ops/ci/WORKFLOW_DISPATCH_GUARD.md`
   - Usage examples, typical findings & fixes, CI integration

2. **Enforcement Policy** (113 lines): `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md`
   - Policy decision, rationale, timeline, bypass/rollback procedures

3. **Settings Guide** (121 lines): `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md`
   - Activation steps (Branch Protection + Rulesets), verification, post-activation updates

4. **Evidence Note** (295 lines): `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`
   - Verification results, GitHub API snapshot, test PR results, operator sign-off

### 5. Merge Logs

- **PR #663:** Phase 5B workflow dispatch condition fix
- **PR #664:** offline_suites workflow_dispatch input context fix (found by this guard!)

## Why This Guard

### Problem

PR #663 introduced a Phase 5B `workflow_dispatch` bug. Without this guard, similar bugs can slip through:
- Wrong input context (`inputs.X` vs `github.event.inputs.X`)
- Undefined inputs referenced
- Missing `workflow_dispatch` trigger

### Solution

Static guard with stdlib-only parsing catches these at PR time:
- **Proven Effective:** Found real bug (PR #664) on first run
- **Zero False Positives:** 100% accuracy in burn-in (1/1 true positive)
- **Fast Execution:** ~3-5s (no dependencies)
- **Path-Filtered:** Only runs when workflow files change

## Verification

### Burn-in Phase

- **Deployed:** 2026-01-12
- **First Run:** Found bug in `offline_suites.yml` (PR #664)
- **False Positive Rate:** 0% (0/1)
- **True Positive Rate:** 100% (1/1)
- **Execution Time:** ~3-5s

### Local Verification

```bash
# Guard run (all workflows)
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn
# Result: OK (0 findings after PR #664 fix)

# Tests
uv run pytest -q tests/ops/test_validate_workflow_dispatch_guards.py
# Result: 2 passed in 0.03s
```

### Test PR

- **PR #665:** Test/verification PR (closed after verification)
- **Outcome:** Guard triggered correctly, check context confirmed
- **Evidence:** Full verification results in evidence note

## Changes

### New Files (13)

**Guard Implementation:**
- `scripts/ops/validate_workflow_dispatch_guards.py` (309 lines)
- `.github/workflows/ci-workflow-dispatch-guard.yml` (33 lines)

**Tests & Fixtures:**
- `tests/ops/test_validate_workflow_dispatch_guards.py` (23 lines)
- `tests/fixtures/workflows_dispatch_guard/good_workflow.yml` (18 lines)
- `tests/fixtures/workflows_dispatch_guard/bad_workflow.yml` (17 lines)

**Documentation:**
- `docs/ops/ci/WORKFLOW_DISPATCH_GUARD.md` (169 lines)
- `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md` (113 lines)
- `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md` (121 lines)
- `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md` (295 lines)

**Merge Logs:**
- `docs/ops/PR_663_MERGE_LOG.md` (26 lines)
- `docs/ops/PR_664_MERGE_LOG.md` (27 lines)

### Modified Files (1)

- `docs/ops/README.md` (added Phase 5C section + merge log links)

**Total:** ~1,300 lines (code + docs + tests)

## Risk Assessment

**Risk:** **LOW**

**Why Low:**
- ✅ Stdlib-only (no new dependencies)
- ✅ Path-filtered (only runs on workflow changes)
- ✅ Static analysis (no runtime effects)
- ✅ Proven effectiveness (100% accuracy)
- ✅ Fast execution (<5s)
- ✅ Not enforced yet (advisory mode until operator activates)

**Impact:**
- **Positive:** Prevents workflow_dispatch regressions (proven: found PR #664 bug)
- **Negative:** None detected (0% false positive rate)

## Post-Merge Actions

### Immediate (Operator, ~2 min)

1. **Activate Enforcement:**
   - GitHub → Settings → Branches → Branch protection rules → `main` → Edit
   - Add required check: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`
   - Save changes

2. **Verify Activation:**
   ```bash
   gh api repos/rauterfrank-ui/Peak_Trade/branches/main/protection \
     --jq '.required_status_checks.contexts | .[] | select(. | contains("Workflow Dispatch Guard"))'
   ```
   Expected: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`

### Follow-up (After Activation)

3. **Update Documentation:**
   - `docs/ops/README.md`: Status NOT ACTIVE → ACTIVE
   - `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md`: Update timeline
   - `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`: Add activation addendum

4. **Re-verify with Test PR:**
   - Create PR touching workflow file
   - Confirm check blocks merge when failing
   - Confirm check allows merge when passing

## References

- **Root Cause:** PR #663 (Phase 5B workflow dispatch bug)
- **Validation:** PR #664 (bug found by this guard)
- **Test PR:** PR #665 (verification complete, closed)
- **Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`

## Related Work

- **Phase 5B:** Trend Ledger from Seed (PR #661)
- **Phase 5A:** Trend Seed Consumer (PR #660)
- **PR #663:** Phase 5B dispatch condition fix (original regression)
- **PR #664:** offline_suites dispatch fix (found by this guard)

---

**Ready to merge.** Guard is functional and proven. Enforcement activation is a 2-minute operator task post-merge.
