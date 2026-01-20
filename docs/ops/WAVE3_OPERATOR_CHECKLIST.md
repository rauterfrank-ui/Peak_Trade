# Wave3 Operator Checklist

**Version:** 1.0  
**Date:** 2026-01-07  
**Purpose:** Pre/Post-Merge validation for Wave3 PRs

---

## Before Merge (ANY PR)

### 1. CI Status
- [ ] All required checks are **GREEN**
- [ ] No "pending" checks remaining
- [ ] No skipped checks that should run

**Verify:** `gh pr checks <PR> | grep -E "fail|pending"`

### 2. Conflict Status
- [ ] PR shows **MERGEABLE** (not CONFLICTING)
- [ ] No merge conflict markers in diff

**Verify:** `gh pr view <PR> --json mergeable -q .mergeable`

### 3. File Scope Review
- [ ] No files in `reports/` committed
- [ ] No files in `.artifacts/`, `.tmp_*&#47;` committed
- [ ] No root-level docs (should be in `docs/`)
- [ ] No committed secrets/credentials

**Verify:** `gh pr view <PR> --json files | jq -r '.files[].path' | grep -E "^reports&#47;|^\.tmp|^\.artifacts|^[A-Z_]+\.md$"`

### 4. Code Quality (if touches code)
- [ ] Ruff linting passes
- [ ] Pre-commit hooks pass
- [ ] No `TODO`, `FIXME`, `XXX` in new code (without issue link)

**Verify:** `gh pr diff <PR> | grep -E "TODO|FIXME|XXX"`

### 5. Docs Quality (if touches docs)
- [ ] docs-reference-targets-gate passes
- [ ] No broken internal links
- [ ] Markdown formatting consistent

**Verify:** `gh pr checks <PR> | grep docs-reference-targets-gate`

### 6. Risk Assessment
- [ ] Docs-only PR? → Low risk
- [ ] Touches `.github/workflows/`? → Review workflow impact
- [ ] Touches `scripts/`? → Review for safety (`rm -rf`, force operations)
- [ ] Touches `src/`? → Requires extended testing

**Verify:** `gh pr view <PR> --json files | jq -r '.files[].path' | cut -d&#47; -f1 | sort -u`

---

## After Merge (ANY PR)

### 7. Merge Confirmation
- [ ] PR is merged (state = MERGED)
- [ ] Branch is deleted
- [ ] Squash commit appears in main

**Verify:** `gh pr view <PR> --json state,headRefName`

### 8. File Verification
- [ ] New files exist at expected paths
- [ ] No unexpected files added to main

**Verify:** `git log -1 --name-status | grep ^A`

### 9. CI on Main
- [ ] Main branch CI is green after merge
- [ ] No new workflow failures introduced

**Verify:** `gh run list --branch main --limit 1 --json conclusion`

### 10. Audit Trail
- [ ] Merge appears in `git log`
- [ ] Commit message references PR number
- [ ] No policy violations in audit log (if applicable)

**Verify:** `git log --oneline -1 | grep "#<PR>"`

### 11. Functionality Smoke Test (for code PRs)
- [ ] Run affected scripts manually (if applicable)
- [ ] Run affected tests manually (if applicable)
- [ ] Check for runtime errors

**Verify:** `python scripts&#47;<new_script>.py --help` or `pytest tests&#47;<new_test>.py -v`

### 12. Documentation Update (if needed)
- [ ] README updated (if new feature)
- [ ] Wave3 Control Center updated
- [ ] Wave3 audit log updated

**Verify:** Check `docs/ops/WAVE3_CONTROL_CENTER.md`

---

## Emergency Rollback Checklist

If ANY issue detected post-merge:

- [ ] Document issue immediately
- [ ] Assess impact (production/dev/docs)
- [ ] Execute rollback: `git revert <commit>`
- [ ] Push rollback to main
- [ ] Update Wave3 incident log
- [ ] Re-open original PR with notes

**Command:** `git revert <commit> && git push origin main`

---

## Quick Reference Commands

```bash
# Check PR status:
gh pr view <PR> --json mergeable,state,isDraft,additions,deletions

# Check CI:
gh pr checks <PR>

# Check files:
gh pr view <PR> --json files | jq -r '.files[].path'

# Merge PR:
gh pr merge <PR> --squash --delete-branch

# Verify merge on main:
git checkout main && git pull && git log --oneline -1

# Rollback:
git revert <commit> && git push origin main
```

---

**Checklist Version:** 1.0  
**Last Updated:** 2026-01-07  
**Maintained By:** Peak_Trade Ops
