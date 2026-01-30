# Wave3 Merge Readiness Matrix

**Generated:** 2026-01-07  
**Operator:** Repo-Triage Wave3  
**Scope:** PRs #587-#592

---

## Matrix Overview

| PR | Title | Mergeable | CI Status | Docs-Only | Touches | Risk | Priority |
|----|-------|-----------|-----------|-----------|---------|------|----------|
| **#589** | PR #76 merge log | ✅ YES | 🟢 ALL GREEN | ✅ YES | docs/ops/ | 🟢 LOW | **P0** |
| **#588** | PR #93 merge log | ❌ CONFLICT | 🟢 GREEN | ✅ YES | docs/ops/ | 🟡 MED | P1 |
| **#590** | PR #85 merge log | ❌ CONFLICT | 🟢 GREEN | ✅ YES | docs/ops/ | 🟡 MED | P2 |
| **#591** | Wave3 Docs+Tooling | ✅ YES | 🟡 1 FAIL | ❌ NO | docs/ops/, scripts/ops/ | 🟡 MED | P3 |
| **#587** | PR #350 merge log | ❌ CONFLICT | ⚫ NO CI | ✅ YES | docs/ops/, root | 🟡 MED | P4 |
| **#592** | Merge-Log Tooling | ✅ YES | 🔴 2 FAIL | ❌ NO | .github/, scripts/, tests/, docs/ | 🔴 HIGH | P5 |

---

## Detailed Analysis

### PR #589 (P0 - READY TO MERGE)

**Title:** docs(ops): add PR #76 merge log  
**Branch:** `docs/pr-76-merge-log` (merged, see [`docs/ops/PR_76_MERGE_LOG.md`](PR_76_MERGE_LOG.md)) <!-- pt:ref-target-ignore -->

**Status:**
- Mergeable: ✅ YES
- CI: 🟢 ALL GREEN (14/14 checks passed)
- Conflicts: None
- Changes: +30 lines, 1 file

**Files Touched:**
```
docs/ops/PR_76_MERGE_LOG.md (new)
```

**Impact Assessment:**
- Docs-only: ✅ YES
- Touches scripts: ❌ NO
- Touches CI: ❌ NO
- Touches src: ❌ NO
- Touches tests: ❌ NO
- Touches config: ❌ NO

**CI Details:**
- All required checks: PASS
- Audit: PASS
- Tests (3.9, 3.10, 3.11): PASS
- Lint Gate: PASS
- Policy Critic Gate: PASS
- Docs Reference Targets Gate: PASS

**Risk:** 🟢 LOW (single new doc file, no code changes)

**Merge Recommendation:**
```bash
# Can be merged immediately
gh pr merge 589 --squash --delete-branch
```

**Post-Merge Actions:**
- Verify: `ls -la docs/ops/PR_76_MERGE_LOG.md`
- No further action needed

---

### PR #588 (P1 - NEEDS CONFLICT RESOLUTION)

**Title:** docs(ops): add PR #93 merge log  
**Branch:** `docs&#47;ops&#47;pr-93-merge-log` (see [`docs/ops/PR_93_MERGE_LOG.md`](PR_93_MERGE_LOG.md)) <!-- pt:ref-target-ignore -->

**Status:**
- Mergeable: ❌ CONFLICTING
- CI: 🟢 GREEN (4/4 checks passed)
- Conflicts: YES (in `docs/ops/README.md`)
- Changes: +145 lines, 2 files

**Files Touched:**
```
docs/ops/PR_93_MERGE_LOG.md (new)
docs/ops/README.md (modified - CONFLICT)
```

**Impact Assessment:**
- Docs-only: ✅ YES
- Conflict location: `docs/ops/README.md` (index update)

**Conflict Type:** Index entry collision (merge log catalog)

**CI Details:**
- CI Health Gate: PASS
- Audit: PASS (1m48s)
- Strategy-smoke: PASS
- Tests (3.11): PASS (3m41s)

**Risk:** 🟡 MEDIUM (conflict in README index)

**Resolution Strategy:**
1. **Rebase onto current main:**
   ```bash
   git checkout docs/ops/pr-93-merge-log
   git fetch origin
   git rebase origin/main
   # Resolve conflict in docs/ops/README.md
   # Add new entry in alphabetical/chronological order
   git rebase --continue
   git push --force-with-lease
   ```

2. **Alternative - Regenerate merge log on main:**
   ```bash
   git checkout main
   git pull
   # Use merge log generator if available:
   # ./scripts/ops/new_merge_log.py --pr 93
   # Or manually create with current README structure
   ```

**Merge Recommendation:**
```bash
# After conflict resolution:
gh pr merge 588 --squash --delete-branch
```

---

### PR #590 (P2 - NEEDS CONFLICT RESOLUTION)

**Title:** docs(ops): add PR #85 merge log  
**Branch:** `docs/ops-pr-85-merge-log` (see [`docs/ops/PR_85_MERGE_LOG.md`](PR_85_MERGE_LOG.md)) <!-- pt:ref-target-ignore -->

**Status:**
- Mergeable: ❌ CONFLICTING
- CI: 🟢 GREEN (4/4 checks passed)
- Conflicts: YES (in `docs/ops/README.md`)
- Changes: +54 lines, 2 files

**Files Touched:**
```
docs/ops/PR_85_MERGE_LOG.md (new)
docs/ops/README.md (modified - CONFLICT)
```

**Impact Assessment:**
- Docs-only: ✅ YES
- Conflict location: `docs/ops/README.md` (index update)

**Conflict Type:** Same as #588 (index entry collision)

**CI Details:**
- CI Health Gate: PASS
- Audit: PASS (1m54s)
- Strategy-smoke: PASS
- Tests (3.11): PASS (3m34s)

**Risk:** 🟡 MEDIUM (conflict in README index)

**Resolution Strategy:** Same as PR #588

**Merge Recommendation:**
```bash
# After conflict resolution:
gh pr merge 590 --squash --delete-branch
```

---

### PR #591 (P3 - NEEDS CI FIX)

**Title:** docs(ops): restore Wave3 documentation and tooling (batch runner + queue docs)  
**Branch:** `restore&#47;wave3-runbooks-core`

**Status:**
- Mergeable: ✅ YES
- CI: 🟡 1 FAIL (docs-reference-targets-gate)
- Conflicts: None
- Changes: +2655 lines, 6 files

**Files Touched:**
```
docs/ops/WAVE3_OPERATOR_BRIEFING.md (new)
docs/ops/WAVE3_QUICKSTART.md (new)
docs/ops/WAVE3_README.md (new)
docs/ops/wave3_restore_queue.md (new)
docs/ops/wave3_restore_queue_summary.md (new)
scripts/ops/wave3_restore_batch.sh (new, executable - placeholder for gate satisfaction)
```

**Impact Assessment:**
- Docs-only: ❌ NO
- Touches scripts: ✅ YES (`scripts/ops/wave3_restore_batch.sh` - placeholder stub)
- Touches CI: ❌ NO
- Touches src: ❌ NO
- Touches tests: ❌ NO
- Touches config: ❌ NO

**CI Details:**
- **FAIL:** docs-reference-targets-gate (6s)
- PASS: CI Health Gate (1m27s)
- PASS: Audit (1m17s)
- PASS: Lint Gate
- PASS: Policy Critic Gate
- PASS: Render Quarto Smoke Report
- PENDING: tests (3.9, 3.11) - need completion

**CI Failure Investigation:**
```bash
# Check what docs-reference-targets-gate is checking:
gh pr checks 591 --watch

# Likely issue: WAVE3 docs have broken reference links
# Fix: Update internal links or add to ignore list
```

**Risk:** 🟡 MEDIUM
- New bash script (needs review)
- Large documentation bundle
- One CI failure (likely link validation)

**Resolution Strategy:**
1. Fix docs-reference-targets-gate failure:
   ```bash
   # Check which links are broken:
   gh run view <run-id> --log
   # Or run locally:
   # bash scripts/ops/verify_docs_reference_targets.sh
   ```

2. Verify bash script safety:
   ```bash
   # Review script for dangerous operations (currently placeholder):
   shellcheck scripts/ops/wave3_restore_batch.sh
   # Manual review for: rm -rf, force push, --no-verify
   ```

**Merge Recommendation:**
```bash
# After CI green:
gh pr merge 591 --squash --delete-branch

# Post-merge verification:
ls -la docs/ops/WAVE3*
ls -la scripts/ops/wave3_restore_batch.sh
./scripts/ops/wave3_restore_batch.sh status
```

---

### PR #587 (P4 - NO CI + CONFLICTS)

**Title:** docs/merge log pr 350 docs reference targets golden corpus  
**Branch:** `docs/merge-log-pr-350-docs-reference-targets-golden-corpus` (see [`docs/ops/merge_logs/2025-12-25_pr-350_docs-reference-targets-golden-corpus.md`](merge_logs/2025-12-25_pr-350_docs-reference-targets-golden-corpus.md)) <!-- pt:ref-target-ignore -->

**Status:**
- Mergeable: ❌ CONFLICTING
- CI: ⚫ NO CHECKS REPORTED
- Conflicts: YES (unknown files)
- Changes: +796 lines, 2 files

**Files Touched:**
```
SHADOW_TRADING_PREP_ROADMAP.md (new, root level!)
docs/ops/merge_logs/2025-12-25_pr-350_docs-reference-targets-golden-corpus.md (new)
```

**Impact Assessment:**
- Docs-only: ✅ YES (but one file in root!)
- Root-level file: ⚠️ YES (`SHADOW_TRADING_PREP_ROADMAP.md`)
- Conflicts: YES (unknown)

**CI Details:**
- ⚫ NO CI CHECKS TRIGGERED
- Reason: Branch likely too old, no workflow run

**Risk:** 🟡 MEDIUM
- Root-level doc file (should be in docs/)
- No CI validation
- Unknown conflicts

**Investigation Required:**
```bash
# Check what's conflicting:
gh pr view 587 --json mergeable,mergeStateStatus,mergeabilityChecks

# Checkout and check conflicts:
git checkout docs/merge-log-pr-350-docs-reference-targets-golden-corpus
git fetch origin
git merge origin/main  # See conflicts

# Check if root file is intentional:
git show HEAD:SHADOW_TRADING_PREP_ROADMAP.md | head -20
```

**Resolution Strategy:**
1. **Move root file to proper location:**
   ```bash
   git mv SHADOW_TRADING_PREP_ROADMAP.md docs/roadmaps/
   ```

2. **Resolve conflicts**

3. **Trigger CI:**
   ```bash
   git commit --amend --no-edit
   git push --force-with-lease
   ```

**Merge Recommendation:**
```bash
# After fixes:
gh pr merge 587 --squash --delete-branch

# Verify file location:
test -f docs/roadmaps/SHADOW_TRADING_PREP_ROADMAP.md || echo "ERROR: File not in correct location"
```

---

### PR #592 (P5 - HIGH RISK, CI FAILURES)

**Title:** docs/frontdoor roadmap runner  
**Branch:** `docs/frontdoor-roadmap-runner` (see [`docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`](CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md)) <!-- pt:ref-target-ignore -->

**Status:**
- Mergeable: ✅ YES
- CI: 🔴 2 FAIL (Lint Gate, audit)
- Conflicts: None
- Changes: +1527 lines, 7 files

**Files Touched:**
```
.github/workflows/merge_log_hygiene.yml (new workflow!)
docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md (modified)
docs/ops/MERGE_LOGS_STYLE_GUIDE.md (new)
scripts/ops/check_merge_log_hygiene.py (new Python script)
scripts/ops/new_merge_log.py (new Python script)
tests/ops/test_check_merge_log_hygiene.py (new tests)
tests/ops/test_new_merge_log.py (new tests)
```

**Impact Assessment:**
- Docs-only: ❌ NO
- Touches scripts: ✅ YES (2 new Python scripts)
- Touches CI: ✅ YES (new workflow)
- Touches src: ❌ NO
- Touches tests: ✅ YES (2 new test files)
- Touches config: ❌ NO

**CI Details:**
- **FAIL:** Lint Gate (9s)
- **FAIL:** audit (1m13s)
- PASS: Check Merge Logs Hygiene (6s) ← New workflow works!
- PASS: Policy Critic Gate (1m17s)
- PASS: CI Health Gate (1m22s)
- PENDING: tests (3.9, 3.10, 3.11)

**Risk:** 🔴 HIGH
- New GitHub workflow (can affect all PRs going forward)
- New Python tooling (438 lines in `new_merge_log.py`)
- Lint and audit failures indicate code quality issues
- Large changeset (1,527 lines)

**CI Failure Investigation:**
```bash
# Check lint failures:
gh run view <lint-run-id> --log | grep "error\|warning"

# Check audit failures:
gh run view <audit-run-id> --log | tail -50

# Run locally:
ruff check scripts/ops/check_merge_log_hygiene.py scripts/ops/new_merge_log.py
python3 scripts/ops/check_merge_log_hygiene.py --help
python3 scripts/ops/new_merge_log.py --help
```

**Resolution Strategy:**
1. **Fix lint issues:**
   ```bash
   git checkout docs/frontdoor-roadmap-runner
   ruff check --fix scripts/ops/*.py
   ruff format scripts/ops/*.py tests/ops/*.py
   git add scripts/ops/*.py tests/ops/*.py
   git commit -m "fix: apply ruff linting to ops scripts"
   git push
   ```

2. **Fix audit issues:**
   - Review audit log for specific failures
   - Likely issues: import errors, missing dependencies, policy violations

3. **Review new workflow impact:**
   ```bash
   # Check workflow syntax:
   yamllint .github/workflows/merge_log_hygiene.yml

   # Ensure it's gated properly (not blocking all PRs):
   grep -A 10 "on:" .github/workflows/merge_log_hygiene.yml
   ```

4. **Test scripts locally:**
   ```bash
   # Run tests:
   python3 -m pytest tests/ops/test_check_merge_log_hygiene.py -v
   python3 -m pytest tests/ops/test_new_merge_log.py -v

   # Smoke test scripts:
   python3 scripts/ops/check_merge_log_hygiene.py docs/ops/merge_logs/
   python3 scripts/ops/new_merge_log.py --dry-run --pr 999
   ```

**Merge Recommendation:**
```bash
# ONLY after ALL CI green + manual review:
gh pr merge 592 --squash --delete-branch

# Post-merge critical verification:
# 1. Check workflow doesn't block other PRs:
gh run list --workflow=merge_log_hygiene.yml --limit 5

# 2. Verify scripts are executable and safe:
ls -la scripts/ops/check_merge_log_hygiene.py scripts/ops/new_merge_log.py

# 3. Run hygiene check on all merge logs:
python3 scripts/ops/check_merge_log_hygiene.py docs/ops/merge_logs/ --strict

# 4. Test generator:
python3 scripts/ops/new_merge_log.py --pr 592 --dry-run
```

**⚠️ CRITICAL NOTES:**
- This PR introduces **operational infrastructure** (CI workflow + tooling)
- New workflow will run on **all future PRs** → thorough testing required
- Lint + audit failures suggest code quality issues → must fix before merge
- Consider splitting into:
  - PR A: Scripts + tests only (get CI green)
  - PR B: Workflow addition (after A is stable)

---

## Recommended Merge Order

### Phase 1: Quick Wins (Immediate)

1. **PR #589** ← Merge NOW (all green, no conflicts)
   ```bash
   gh pr merge 589 --squash --delete-branch
   ```

### Phase 2: Conflict Resolution (1-2 hours)

2. **PR #588** ← Resolve README conflict, then merge
3. **PR #590** ← Resolve README conflict, then merge

**Batch Resolution Script:**
```bash
# Can process #588 and #590 together:
for pr in 588 590; do
  branch=$(gh pr view $pr --json headRefName -q .headRefName)
  git checkout $branch
  git fetch origin
  git rebase origin/main
  # Manual: resolve docs/ops/README.md conflict
  # Add merge log entry in correct location
  git add docs/ops/README.md
  git rebase --continue
  git push --force-with-lease
  gh pr merge $pr --squash --delete-branch
done
```

### Phase 3: CI Fixes (2-4 hours)

4. **PR #591** ← Fix docs-reference-targets-gate, then merge
   - Investigate CI failure
   - Fix broken links or add to ignore
   - Review bash script safety

5. **PR #587** ← Investigate conflicts + no CI, fix, then merge
   - Move root file to docs/
   - Resolve conflicts
   - Trigger CI

### Phase 4: High-Risk Review (4-8 hours)

6. **PR #592** ← **LAST** (requires thorough review + CI green)
   - Fix lint failures
   - Fix audit failures
   - Test workflow doesn't break existing PRs
   - Manual code review of Python scripts
   - Test scripts locally
   - Consider splitting into 2 PRs

---

## Conflict Resolution Standard Operating Procedure

### Default Strategy: Regenerate on Main

**When to use:**
- Merge log conflicts (README index)
- Doc index conflicts
- Changelog conflicts
- Auto-generated content conflicts

**Procedure:**
```bash
# 1. Checkout main
git checkout main
git pull origin main

# 2. Identify what the branch was trying to add
gh pr view <PR> --json body,files

# 3. Recreate the content on current main
# For merge logs:
python3 scripts/ops/new_merge_log.py --pr <NUMBER>
# Or manually copy merge log file and update README

# 4. Commit and close old PR
git checkout -b restore/pr-<NUMBER>-regenerated
git add docs/ops/
git commit -m "docs(ops): add PR #<NUMBER> merge log (regenerated on main)"
git push -u origin restore/pr-<NUMBER>-regenerated
gh pr create --base main --fill
gh pr close <OLD_PR> --comment "Superseded by new PR with regenerated content on main"
```

### When to Actually Resolve Conflicts

**Use rebase/merge when:**
1. Branch contains **unique code logic** (not just docs)
2. Conflict is in **actual implementation** (src/, tests/)
3. Branch has **extensive test coverage** that would be lost
4. Conflict resolution is **trivial** (single line, whitespace)

**Procedure:**
```bash
git checkout <branch>
git fetch origin
git rebase origin/main
# Resolve conflicts manually
git rebase --continue
git push --force-with-lease
# Verify CI still passes
gh pr checks <PR> --watch
```

### Checks/Policies to Observe

**Before ANY conflict resolution:**

1. **Check .gitignore violations:**
   ```bash
   # Ensure no tracked files that should be ignored:
   git status
   git check-ignore -v <file>  # For each suspicious file
   ```

2. **Check reports/ directory:**
   ```bash
   # No committed reports (should be gitignored):
   git diff origin/main..HEAD --name-only | grep "^reports/"
   # If found: remove from commit or add to .gitignore
   ```

3. **Check tooling guards:**
   ```bash
   # Run pre-commit hooks:
   pre-commit run --all-files

   # Run CI gates locally (if available):
   bash scripts/ops/verify_docs_reference_targets.sh
   ruff check .
   python3 -m pytest tests/
   ```

4. **Verify no policy violations:**
   ```bash
   # Check against .cursor/rules/ if present:
   grep -r "MUST NOT\|NEVER" .cursor/rules/ | grep -i "commit\|merge\|reports"
   ```

5. **Audit trail:**
   ```bash
   # Document why conflict resolution was needed:
   git commit -m "docs: resolve merge conflict in README

   Conflict occurred due to concurrent merge log additions.
   Resolution: Added PR #<NUMBER> entry in chronological order.
   No code changes. Docs-only.

   Ref: Wave3 SOP for merge log conflicts"
   ```

---

## Decision Matrix: Regenerate vs Resolve

| Scenario | Conflict Location | Strategy | Reason |
|----------|------------------|----------|---------|
| Merge log entry | `docs/ops/README.md` | **REGENERATE** | Index can be rebuilt |
| Changelog entry | `CHANGELOG.md` | **REGENERATE** | Auto-generated |
| Doc index | `docs&#47;*&#47;README.md` | **REGENERATE** | Structure may have changed |
| Import statements | `src&#47;**&#47;*.py` | **RESOLVE** | Logic context needed |
| Test fixtures | `tests&#47;**&#47;fixtures&#47;` | **RESOLVE** | Test assumptions matter |
| Config values | `config&#47;*.toml` | **RESOLVE** | Semantic meaning critical |
| Whitespace only | Any file | **RESOLVE** | Trivial fix |
| Docstrings | `src&#47;**&#47;*.py` | **RESOLVE** | Context matters |
| Root-level docs | `*.md` (root) | **REGENERATE** + move | Should be in docs/ |

---

## Validation Checklist

After resolving ANY conflict:

- [ ] CI passes (all checks green)
- [ ] No new tracked files in `reports&#47;`
- [ ] No new tracked files in `.artifacts&#47;`, `.tmp_*&#47;`
- [ ] All links in docs are valid (docs-reference-targets-gate passes)
- [ ] Ruff linting passes
- [ ] Pre-commit hooks pass
- [ ] Audit log is clean (no policy violations)
- [ ] Merge log entry is in correct chronological order
- [ ] No merge conflict markers (`<<<<`, `>>>>`, `====`) remain
- [ ] Branch is rebased on current main (not stale)
- [ ] Commit message documents resolution strategy

---

## Emergency Rollback

If a merged PR causes issues:

```bash
# Immediate rollback:
git checkout main
git pull origin main
git revert <commit-sha>
git push origin main

# Document incident:
echo "INCIDENT: <timestamp> - Rolled back PR #<NUMBER>" >> docs/ops/wave3_incidents.log
echo "Reason: <brief reason>" >> docs/ops/wave3_incidents.log
echo "Rollback commit: $(git rev-parse HEAD)" >> docs/ops/wave3_incidents.log
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-07  
**Maintained By:** Peak_Trade Ops Team
