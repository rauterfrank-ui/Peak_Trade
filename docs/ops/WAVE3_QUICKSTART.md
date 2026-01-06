# Wave3 Restore Queue – Quick Start Guide

**Start Date:** 2026-01-06  
**Status:** Ready for Execution  
**Estimated Duration:** 7-8 days

---

## 🎯 Goal

Merge 47 unmerged branches (Tier A+B+C), delete 26 obsolete branches (Tier X).

---

## 📋 Pre-Flight Checklist

Before starting Wave3, verify:

```bash
cd /Users/frnkhrz/Peak_Trade

# 1. On main branch, clean working tree
git status
# Should show: "On branch main, nothing to commit, working tree clean"

# 2. Fetch latest
git fetch --prune origin

# 3. CI is green
gh pr checks origin/main
# Or check GitHub Actions manually

# 4. Tests pass
make test
# Should pass

# 5. Docs validate (if applicable)
make docs-validate || true

# 6. Check unmerged branch count
git branch -r | grep -v "origin/main\|origin/HEAD" | wc -l
# Should show ~70-75
```

✅ **All checks pass?** → Proceed to Phase 1

---

## 🚀 Phase 1: Tier A Docs (Days 1-2)

**Target:** Merge 27 doc branches  
**Risk:** LOW

### Step 1.1: Check Duplicates & Conflicts FIRST

```bash
# Check duplicate branches (5 branches with same message)
./scripts/ops/wave3_restore_batch.sh check-dupes

# Decision: Merge ONE or delete ALL?
# If merge: pick beautiful-ritchie, delete the rest
# If delete: skip this group

# Check conflict resolution branches (4 branches)
./scripts/ops/wave3_restore_batch.sh check-conflicts

# Decision: If PR #70 in main → delete all 4
# Check: git log origin/main --oneline | grep "#70"
```

**Action Items:**
- [ ] Reviewed duplicate branches
- [ ] Decided: merge/delete duplicates
- [ ] Reviewed conflict branches  
- [ ] Decided: merge/delete conflicts

---

### Step 1.2: Batch Process Merge Logs (11 branches)

```bash
# Process all merge log branches
./scripts/ops/wave3_restore_batch.sh tier-a-merge-logs

# This will:
# - Rebase each branch onto main
# - Show diff stats
# - Validate docs (if make target exists)
# - Report success/fail

# Review output, check for failures
```

**Expected:** 11 success, 0 failures

---

### Step 1.3: Process Runbooks (6 branches)

```bash
./scripts/ops/wave3_restore_batch.sh tier-a-runbooks
```

**Expected:** 6 success, 0 failures

---

### Step 1.4: Process Roadmaps (5 branches)

```bash
./scripts/ops/wave3_restore_batch.sh tier-a-roadmaps
```

**Expected:** 5 success, 0 failures

---

### Step 1.5: Process Tooling (1 branch)

```bash
./scripts/ops/wave3_restore_batch.sh tier-a-tooling
```

**Expected:** 1 success, 0 failures

---

### Step 1.6: Create PRs for Tier A

```bash
# Get list of restore branches
git branch | grep "restore/wave3/docs"

# For each restore branch:
git checkout restore/wave3/docs/add-pr569-readme-link
gh pr create \
  --title "Wave3 Tier A: restore docs/add-pr569-readme-link" \
  --body "Tier A docs restore from Wave3 queue. Safe auto-merge candidate." \
  --base main

# Or use a loop:
for branch in $(git branch | grep "restore/wave3/docs"); do
  git checkout "$branch"
  branch_name=$(echo "$branch" | sed 's/restore\/wave3\///')
  gh pr create \
    --title "Wave3 Tier A: restore $branch_name" \
    --body "Tier A docs restore. Auto-merge safe." \
    --base main
done

# Return to main
git checkout main
```

---

### Step 1.7: Verify Tier A

```bash
# After all PRs merged:
cd /Users/frnkhrz/Peak_Trade

# 1. Docs structure intact?
ls -la docs/ops/
# Should see merge logs, runbooks, etc.

# 2. Recent commits count
git log --oneline --since="2 days ago" | wc -l
# Should be ~27

# 3. No test failures
make test

# 4. CI green
gh pr checks origin/main
```

✅ **Tier A Complete**

---

## 🧪 Phase 2: Tier B Tests/CI (Days 3-4)

**Target:** Merge 12 test/CI branches  
**Risk:** MEDIUM (can affect CI behavior)

### Step 2.1: Process Tier B (one by one)

```bash
# Tier B requires tests to pass
./scripts/ops/wave3_restore_batch.sh tier-b

# This will:
# - Rebase each branch
# - Run 'make test'
# - Show test results
# - Report success/fail

# Script will stop on failures
# Review each failure manually
```

**Expected:** 10-12 success, 0-2 failures (investigate failures)

---

### Step 2.2: Manual Review for Failures

If any Tier B branch fails:

```bash
# Check out the branch manually
git checkout -b restore/wave3/<branch> origin/<branch>

# Rebase
git rebase origin/main

# Run tests with verbose output
make test-verbose

# Check test logs
cat tests.log

# Fix if needed, or skip branch
```

---

### Step 2.3: Create PRs for Tier B

```bash
# Similar to Tier A:
for branch in $(git branch | grep "restore/wave3" | grep -E "chore|feat|fix|test"); do
  git checkout "$branch"
  branch_name=$(echo "$branch" | sed 's/restore\/wave3\///')
  gh pr create \
    --title "Wave3 Tier B: restore $branch_name" \
    --body "Tier B test/CI restore. Tests passed." \
    --base main
done

git checkout main
```

---

### Step 2.4: Verify Tier B

```bash
# After all merged:

# 1. Full test suite
make test-full

# 2. CI workflows intact
ls -la .github/workflows/

# 3. Tooling works (if uv/ruff merged)
uv --version
ruff --version

# 4. requirements.txt sync (if fix merged)
diff <(uv pip compile pyproject.toml --quiet) requirements.txt
```

✅ **Tier B Complete**

---

## ⚠️ Phase 3: Tier C Source Review (Days 5-7)

**Target:** Review 8 src/risk branches  
**Risk:** HIGH – requires operator signoff

### Step 3.1: Review Each Branch Individually

**DO NOT USE BATCH SCRIPT FOR TIER C**

For each Tier C branch:

```bash
# 1. Checkout and rebase
git checkout -b restore/wave3/<branch> origin/<branch>
git rebase origin/main

# 2. Full diff review
git diff origin/main --stat
git diff origin/main src/ config/

# 3. Read commit messages
git log origin/main..HEAD --oneline

# 4. Risk assessment
# - Does it touch risk gates?
# - Does it modify execution logic?
# - Does it change config schemas?
# - Does it add new dependencies?

# 5. Run extended tests
make test-full
make test-backtests  # if backtest changes

# 6. Integration test (if applicable)
# Example: paper trading smoke test for risk gate changes

# 7. Document decision
echo "Branch: <branch>" >> docs/ops/wave3_tier_c_decisions.md
echo "Decision: MERGE/DEFER/REJECT" >> docs/ops/wave3_tier_c_decisions.md
echo "Reason: ..." >> docs/ops/wave3_tier_c_decisions.md
echo "---" >> docs/ops/wave3_tier_c_decisions.md

# 8. If MERGE:
gh pr create \
  --title "Wave3 Tier C: restore <branch>" \
  --body "Tier C source restore. Full review + tests passed. Operator signoff: [YOUR NAME]" \
  --base main
```

---

### Step 3.2: Priority Order for Tier C

Review in this order:

1. **DEFER (check if already merged):**
   - `vigilant-thompson` (data lake)
   - `stupefied-montalcini` (data lake dupe)
   - `vibrant-antonelli` (MLflow warnings)

2. **LOW-MEDIUM (tooling/infra):**
   - `feat/governance-g4-telemetry-automation`
   - `feat/phase-57-live-status-snapshot-builder-api`

3. **MEDIUM (strategy/backtest):**
   - `feat/strategy-layer-vnext-tracking`
   - `feat/phase-9b-rolling-backtests`

4. **HIGH (risk/execution) – LAST:**
   - `feat/risk-liquidity-gate-v1`
   - `pr-334-rebase` (canonical Order contract)

---

### Step 3.3: Tier C Test Matrix

For each branch, run:

```bash
# Unit tests
make test

# Integration tests
make test-integration || true

# Backtest suite (if strategy/backtest changes)
make test-backtests || pytest tests/backtests/

# Risk gate validation (if risk changes)
pytest tests/risk/ -v

# Config validation (if config changes)
python -c "import tomli; tomli.load(open('config/live_policies.toml', 'rb'))"

# Smoke test (if execution changes)
# Example: run paper trading for 1 minute
# python scripts/run_live.py --mode paper --duration 60 --strategy minimal
```

---

### Step 3.4: Document Tier C Decisions

Create decision log:

```bash
cat > docs/ops/wave3_tier_c_decisions.md << 'EOF'
# Wave3 Tier C Decisions Log

## Branch: pr-334-rebase
- **Date Reviewed:** YYYY-MM-DD
- **Reviewer:** [NAME]
- **Decision:** MERGE / DEFER / REJECT
- **Reason:** [Detailed reason]
- **Tests Run:** [List of tests]
- **Test Results:** PASS / FAIL / PARTIAL
- **Risk Assessment:** [Notes]
- **Merge Date:** YYYY-MM-DD (if merged)

---

## Branch: feat/risk-liquidity-gate-v1
...

EOF
```

---

## 🗑️ Phase 4: Tier X Cleanup (Day 8)

**Target:** Delete 26 obsolete branches

### Step 4.1: Review WIP Stashes

```bash
# Check if any stash contains needed code
for branch in wip/stash-archive-20251227_010347_3 \
              wip/stash-archive-20251227_010344_2 \
              wip/stash-archive-20251227_010341_1 \
              wip/stash-archive-20251227_010316_0 \
              wip/untracked-salvage-20251224_081737 \
              wip/salvage-code-tests-untracked-20251224_082521; do
  echo "=== $branch ==="
  git log -1 --stat origin/$branch | head -20
  echo ""
done
```

**Decision:**
- [ ] Code needed? → Extract to new branch
- [ ] Code obsolete? → Proceed with delete

---

### Step 4.2: Run Cleanup

```bash
# This will DELETE remote branches permanently!
./scripts/ops/wave3_restore_batch.sh cleanup

# Confirms with "YES" prompt

# Verify deletion
git branch -r | grep "wip/stash\|wip/salvage"
# Should return empty
```

---

### Step 4.3: Manual Cleanup (remaining Tier X)

```bash
# Delete other obsolete branches manually
# (copilot experiments, old CI branches, etc.)

git push origin --delete copilot/add-health-check-system-again
git push origin --delete laughing-shockley
git push origin --delete laughing-hawking
git push origin --delete hotfix/policy-critic-ci-gate
git push origin --delete ci-fastlane-impl
git push origin --delete ci/fast-lane-matrix
git push origin --delete chore/folder-cleanup
git push origin --delete docs/ops-index-pr-61-63

# P2 features (if defer to Wave4):
git push origin --delete loving-gauss
git push origin --delete feat/p2-otel-minimal
git push origin --delete competent-hawking

# Document in cleanup log
git branch -r | grep "origin/" > docs/ops/wave3_remaining_branches.txt
```

---

## ✅ Wave3 Completion Checklist

After all phases complete:

```bash
cd /Users/frnkhrz/Peak_Trade

# 1. Branch count reduced
git branch -r | grep "origin/" | wc -l
# Should be ~20-25 (down from ~70)

# 2. All Tier A merged
git log --oneline --grep="Wave3 Tier A" | wc -l
# Should be ~27

# 3. All Tier B merged
git log --oneline --grep="Wave3 Tier B" | wc -l
# Should be ~12

# 4. Tier C decisions documented
test -f docs/ops/wave3_tier_c_decisions.md
# Should exist

# 5. CI green
gh pr checks origin/main

# 6. Tests pass
make test-full

# 7. Docs valid
make docs-validate || true

# 8. No dangling restore branches
git branch | grep "restore/wave3"
# Should be empty (clean up local branches)
```

**Create closeout document:**

```bash
cat > docs/ops/wave3_closeout.md << 'EOF'
# Wave3 Restore Queue – Closeout Report

## Summary
- Start Date: 2026-01-06
- End Date: YYYY-MM-DD
- Duration: X days

## Results
- Tier A merged: X/27
- Tier B merged: X/12
- Tier C merged: X/8 (Y deferred, Z rejected)
- Tier X deleted: X/26

## Metrics
- Total commits: X
- CI success rate: X%
- Test pass rate: X%
- Rollbacks: X

## Issues Encountered
[List any issues]

## Lessons Learned
[Document learnings]

## Next Steps
- Wave4 planning
- Deferred branch review
- Policy updates based on learnings

EOF
```

---

## 🚨 Troubleshooting

### Issue: Rebase Conflict

```bash
# If rebase fails:
git rebase --abort
git checkout main
git branch -D restore/wave3/<branch>

# Manually resolve:
git checkout -b restore/wave3/<branch> origin/<branch>
git rebase -i origin/main
# Resolve conflicts, git rebase --continue
```

---

### Issue: Test Failure

```bash
# Debug test failure:
make test-verbose
# Or:
pytest -vv -s tests/

# Check logs:
cat tests.log

# If persistent failure:
# Document in wave3_issues.md
# Skip branch or defer to later
```

---

### Issue: CI Breakage

```bash
# If CI breaks after merge:
# 1. Identify breaking commit
git log --oneline -10

# 2. Revert if needed
git revert <commit-hash>
git push origin main

# 3. Document incident
echo "Incident: CI breakage from <commit>" >> docs/ops/wave3_incidents.md

# 4. Fix in separate PR
```

---

## 📞 Escalation

**Stop execution if:**
- Multiple Tier A branches cause test failures
- Tier B breaks CI in unexpected ways
- Tier C shows unexpected runtime behavior
- Any merge causes production-like issues

**Action:**
1. STOP all merge activity
2. Document current state
3. Rollback if necessary
4. Ping operator for review
5. Update wave3_incidents.md

---

## 📚 Reference Documents

- **Full Queue:** `docs/ops/wave3_restore_queue.md`
- **Summary:** `docs/ops/wave3_restore_queue_summary.md`
- **This Guide:** `docs/ops/WAVE3_QUICKSTART.md`
- **Batch Script:** `scripts/ops/wave3_restore_batch.sh`

---

## 🎯 Daily Progress Template

Copy to track progress:

```markdown
## Day 1 (YYYY-MM-DD)
- [ ] Pre-flight checks complete
- [ ] Duplicates reviewed: [decision]
- [ ] Conflicts reviewed: [decision]
- [ ] Tier A merge logs: X/11 merged
- [ ] Issues: [list or none]

## Day 2 (YYYY-MM-DD)
- [ ] Tier A runbooks: X/6 merged
- [ ] Tier A roadmaps: X/5 merged
- [ ] Tier A tooling: X/1 merged
- [ ] Tier A verification complete
- [ ] Issues: [list or none]

## Day 3 (YYYY-MM-DD)
- [ ] Tier B batch 1: X/6 merged
- [ ] Issues: [list or none]

## Day 4 (YYYY-MM-DD)
- [ ] Tier B batch 2: X/6 merged
- [ ] Tier B verification complete
- [ ] Issues: [list or none]

## Days 5-7
- [ ] Tier C reviews: X/8 complete
- [ ] Tier C merges: X merged, Y deferred, Z rejected
- [ ] Issues: [list or none]

## Day 8
- [ ] Tier X cleanup: X/26 deleted
- [ ] Final verification complete
- [ ] Closeout document created
- [ ] Wave3 COMPLETE ✅
```

---

**Ready to start?** → Begin with Pre-Flight Checklist above!

**Questions?** → Document in `docs/ops/wave3_issues.md`

**Good luck!** 🚀
