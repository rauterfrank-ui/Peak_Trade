# DRILL RUN — dispatch-guard no-op proof — 2026-01-12

**Date:** 2026-01-12  
**Drill Type:** Regression Proof / Verification Test  
**Phase:** 5C (Workflow Dispatch Guard Reliability)  
**Owner:** ops  
**Status:** IN PROGRESS → PASS (pending CI)

---

## 1. Purpose

**Objective:** Prove that the `dispatch-guard` required check is always present on docs-only PRs and executes fast no-op behavior after PR #668 fix.

**Context:**
- **Issue:** PR #667 was blocked because `dispatch-guard` was path-filtered and "absent" on docs-only PRs
- **Fix:** PR #668 removed PR-level path filtering, added internal change detection
- **Expected:** `dispatch-guard` now always runs but executes fast no-op (~5-7s) when no workflow files changed

**This PR:** Docs-only change (adds this drill run document) → should trigger dispatch-guard no-op pass

---

## 2. Change Scope

**Modified Files:**
- `docs/ops/drills/runs/DRILL_RUN_20260112_dispatch_guard_noop_proof.md` (NEW)

**Changed Areas:**
- Documentation only (ops drill runs)

**No Changes To:**
- ❌ Workflows (`.github/workflows/**`)
- ❌ CI config
- ❌ Source code (`src/**`)
- ❌ Tests
- ❌ Scripts

**Classification:** Docs-only PR

---

## 3. Expected Behavior

### dispatch-guard Check

**Expected Check Run:**
```
✓ CI / Workflow Dispatch Guard (5-7s)
  ✓ Checkout
  ✓ Detect workflow changes (workflows: false)
  ✓ No-op pass (no workflow changes detected)
```

**Expected Log Output:**
```
✅ No workflow changes detected; dispatch-guard no-op pass.
This check is required on main but only validates workflow files.
PR does not modify workflows → fast success.
```

**Expected Duration:** ~5-7 seconds (vs. ~8-10s for full validation)

**Expected Conclusion:** SUCCESS

---

## 4. Verification Commands

### Check if dispatch-guard runs
```bash
gh pr checks <PR_NUMBER> | grep dispatch-guard
# Expected: dispatch-guard present and passing
```

### View detailed check status
```bash
gh pr view <PR_NUMBER> --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.name == "dispatch-guard") | {name, conclusion, status, completedAt}'
# Expected:
# {
#   "name": "dispatch-guard",
#   "conclusion": "SUCCESS",
#   "status": "COMPLETED",
#   "completedAt": "2026-01-12T..."
# }
```

### View check logs (optional)
```bash
# Get latest workflow run for this branch
gh run list --branch docs/dispatch-guard-noop-proof-20260112 --limit 1 --json databaseId --jq '.[0].databaseId' | xargs gh run view --log | grep -A 3 "No-op pass"
# Expected output:
# ✅ No workflow changes detected; dispatch-guard no-op pass.
# This check is required on main but only validates workflow files.
# PR does not modify workflows → fast success.
```

---

## 5. Observed Result

### Check Status

**PR Number:** TBD (will be filled after PR creation)

**Check Run:**
```
# To be filled after CI completes:
# ✓ CI / Workflow Dispatch Guard (<duration>s)
```

**Duration:** TBD seconds

**GitHub Actions Run Link:** TBD

**Conclusion:** TBD (expected: SUCCESS)

### Log Output

```
# To be filled after CI completes:
# (Expected: No-op pass message from workflow logs)
```

---

## 6. Conclusion

**Status:** TBD (pending CI completion)

**Expected Outcome:** PASS

**Success Criteria:**
- ✅ dispatch-guard check is present (not "absent" like in PR #667)
- ✅ Check completes in ~5-7 seconds (fast no-op, not full validation)
- ✅ Log shows "No workflow changes detected; dispatch-guard no-op pass."
- ✅ Check conclusion: SUCCESS
- ✅ No "BLOCKED" status (issue from PR #667 resolved)

**Proof:**
If all criteria met, this proves:
1. PR #668 fix works correctly
2. dispatch-guard reliably produces check-runs on docs-only PRs
3. Internal change detection correctly identifies no workflow changes
4. Fast no-op execution (~5-7s) vs. full validation (~8-10s)
5. Required check "absent" issue permanently resolved

---

## References

- **PR #666:** dispatch-guard implementation (merged 2026-01-12, commit 930d16e7)
- **PR #667:** Phase 5C closeout (discovered "absent check" issue, merged 2026-01-12, commit f2826d0a)
- **PR #668:** dispatch-guard reliability fix (always-run + internal change detection, merged 2026-01-12, commit 878aa35b)
- **This PR:** Regression proof for PR #668 fix
- **Workflow:** `.github/workflows/ci-workflow-dispatch-guard.yml`
- **Closeout:** `docs/ops/PHASE5C_WORKFLOW_DISPATCH_GUARD_ENFORCEMENT_CLOSEOUT.md`

---

## Operator Notes

**Post-Merge Actions:**
- Update this document with actual check run results
- Confirm duration and log output match expectations
- File as evidence of dispatch-guard reliability

**If Check Fails:**
- Review workflow logs for error messages
- Check if dorny/paths-filter action failed
- Verify workflow file syntax (YAML valid)
- Escalate to ops team if unexpected failure

**If Check is Absent:**
- **CRITICAL:** This would indicate PR #668 fix did not work
- Immediately investigate workflow trigger configuration
- Verify PR-level path filter was removed
- Check GitHub Actions UI for workflow run status

---

**Drill Status:** ⏳ **IN PROGRESS** (awaiting CI results)
