# Workflow Dispatch Guard — GitHub Settings Configuration

## Current State (as of 2026-01-12)

**Guard Functional:** ✅ Yes  
**Required Check Active:** ❌ No (not present in `main` required checks list)  
**Expected Context:** `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`  
**Evidence:** `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`

**Once the settings are applied, update:**
- `docs/ops/README.md` status line (NOT ACTIVE → ACTIVE)
- `docs/ops/ci/WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md` status and timeline
- Append a short "Activation Completed" addendum in the evidence note

---

## Required Check Context

**Full Context String:** `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`

## Configuration Steps

### Option 1: Branch Protection Rules (Legacy)

1. Navigate to: **GitHub → Settings → Branches**
2. Find: **Branch protection rule for `main`**
3. Edit Rule
4. Section: **Require status checks to pass before merging**
   - ✅ Enable: "Require status checks to pass before merging"
   - ✅ Enable: "Require branches to be up to date before merging" (recommended)
5. Search for status check: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`
6. Click to add check to required list
7. **Save changes**

### Option 2: Rulesets (Modern)

1. Navigate to: **GitHub → Settings → Rules → Rulesets**
2. Find or Create: Ruleset for `main` branch
3. Section: **Status checks**
   - ✅ Enable: "Require status checks to pass"
4. Add status check: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard`
5. **Save ruleset**

## Verification

### Check Configuration

```bash
# Via gh CLI (if available)
gh api repos/:owner/:repo/branches/main/protection

# Look for "required_status_checks" section containing:
# "CI / Workflow Dispatch Guard / dispatch-guard"
```

### Test PR

1. Create test PR that modifies a workflow file
2. Observe: Check appears in PR checks list
3. Verify: PR cannot be merged if check fails
4. Verify: Check auto-skips if no workflow files modified (path filter)

## Expected Behavior

**When Check Runs:**
- PR modifies files under `.github&#47;workflows&#47;*.yml` or `.github&#47;workflows&#47;*.yaml`
- PR modifies guard script: `scripts/ops/validate_workflow_dispatch_guards.py`
- PR modifies tests: `tests/ops/test_validate_workflow_dispatch_guards.py`

**When Check Skips:**
- PR only modifies non-workflow files (docs, src, config)
- Path filter prevents unnecessary runs

**Merge Blocking:**
- ✅ Check PASS → Merge allowed (with other required checks)
- ❌ Check FAIL → Merge blocked
- ⏭️ Check SKIPPED → Does not block (path-filtered, not applicable)

## Admin Override

**When Needed:**
- False positive detected (should be rare)
- Emergency hotfix (with audit justification)

**How:**
```bash
# GitHub CLI (requires admin token)
gh pr merge <PR_NUMBER> --admin --squash

# OR: GitHub UI
# - Navigate to PR
# - Click "Merge pull request" (admin bypass enabled)
# - Confirm with justification comment
```

**Audit Requirement:**
- **MUST** comment on PR explaining override reason
- **MUST** link to issue tracking false positive (if applicable)
- **MUST** notify Ops team

## Rollback

**To Remove Enforcement:**

1. Navigate to: **GitHub → Settings → Branches** (or Rulesets)
2. Edit protection rule for `main`
3. Remove check: `CI &#47; Workflow Dispatch Guard &#47; dispatch-guard` from required list
4. **Save changes**
5. **Document reason** in: GitHub Issue or Ops runbook

**Note:** Guard will continue to run and report results, but won't block merges.

## Settings Snapshot

### Current State (2026-01-12)

**Status:** ⚠️ Check **NOT** in required list

See evidence note for full API output: `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`

### Target State (After Activation)

```yaml
Branch: main
Protection:
  Required checks:
    - "CI / Workflow Dispatch Guard / dispatch-guard"  # ← TO BE ADDED
    - (... other existing required checks ...)
  Enforce admins: false (admin override allowed)
  Require PR reviews: (per repository policy)
```

## Post-Activation Documentation Updates

**After adding the check to required list, update these files:**

1. **README.md**
   - Change status: `⚠️ NOT ACTIVE` → `✅ ACTIVE`
   - Update date in "Current State" line

2. **WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md**
   - Update "Activation Status (Operational)" section
   - Update Timeline table: Add actual activation date for "Enforcement Activation" row
   - Change "Status" from "Target" to "ACTIVE"

3. **Evidence Note (Addendum)**
   - File: `docs/ops/ci/evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md`
   - Add "## Activation Completed" section with:
     - Activation date/time
     - Operator who performed activation
     - Re-verification PR (if any)
     - Updated GitHub API output showing check in required list

4. **This File (WORKFLOW_DISPATCH_GUARD_GITHUB_SETTINGS.md)**
   - Update "Current State" → "Activation Complete"
   - Update "Last Updated" date below

---

## Owner

- **Technical Owner:** CI/CD Automation Team
- **Policy Owner:** Engineering Lead
- **Last Updated:** 2026-01-12 (pre-activation)

## References

- **Enforcement Policy:** [WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md](WORKFLOW_DISPATCH_GUARD_ENFORCEMENT.md)
- **User Guide:** [WORKFLOW_DISPATCH_GUARD.md](WORKFLOW_DISPATCH_GUARD.md)
- **Evidence Note:** [evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md](evidence/PHASE5C_DISPATCH_GUARD_ENFORCEMENT_VERIFICATION_2026-01-12.md)
- **Validation PRs:** #663, #664
