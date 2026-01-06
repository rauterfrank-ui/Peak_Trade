# Wave3 Restore Queue – Operator Briefing

**Date:** 2026-01-06  
**Prepared by:** Cursor Agent  
**Status:** ⚠️ READY FOR REVIEW & APPROVAL

---

## 🎯 Mission

Restore 47 valuable branches (docs, tests, features) and cleanup 26 obsolete branches.

---

## 📊 Situation Analysis

### Current State
- **Total unmerged branches:** 73
- **Open PRs:** 0 (all clean)
- **Main branch status:** ✅ Clean, CI green
- **Last activity:** Wave2 closeout completed

### Repository Health
```
Working directory: clean
CI status: passing
Test status: passing
Branch debt: HIGH (73 unmerged branches)
```

---

## 🗂️ Branch Inventory

| Tier | Count | Risk | Action Required |
|------|-------|------|-----------------|
| **A** | 27 | 🟢 LOW | Batch merge with auto-checks |
| **B** | 12 | 🟡 MEDIUM | Review + pytest per branch |
| **C** | 8 | 🔴 HIGH | Full review + operator signoff |
| **X** | 26 | ⚫ N/A | DELETE after verification |
| **TOTAL** | **73** | — | — |

---

## 🚦 Immediate Actions (Pre-Flight)

### ✅ ACTION 1: Delete Obsolete Conflict Branches (4 branches)

**Finding:** PR #70 is already in main → 4 conflict resolution branches are obsolete

```bash
# These can be safely deleted:
git push origin --delete condescending-rubin
git push origin --delete dazzling-gates
git push origin --delete sweet-kapitsa
git push origin --delete magical-tesla
```

**Impact:** Zero (branches are obsolete)  
**Verification:** `git log origin/main --oneline | grep "#70"` shows PR #70 commits

---

### ⚠️ ACTION 2: Review Duplicate Branches (5 branches)

**Finding:** 5 branches with identical commit message + date

```
beautiful-ritchie
busy-cerf
determined-matsumoto
keen-aryabhata
serene-elbakyan
```

**All have:** "docs(stability): mark Wave A+B stack complete, add deployment runbook" (2025-12-18)

**Decision Required:**
- Option A: Diff all 5 against main, merge the most complete ONE, delete the other 4
- Option B: Check if content already in main, if yes delete ALL 5

**Recommended Action:**
```bash
# Check if already merged (by content, not by commit):
git log origin/main --since="2025-12-18" --grep="Wave A+B" --oneline

# If found → DELETE all 5
# If not found → Diff first branch:
git diff origin/main..origin/beautiful-ritchie --stat

# If valuable → MERGE beautiful-ritchie, DELETE others
# If already in main → DELETE all
```

---

## 📋 Tier A: Safe Docs (27 branches)

### Categories

1. **Merge Log Backlog** (11 branches)  
   - Pure documentation, historical PR merge logs  
   - **Risk:** Zero  
   - **Action:** Auto-merge with conflict checks  
   - **Script:** `./scripts/ops/wave3_restore_batch.sh tier-a-merge-logs`

2. **Runbooks & Standards** (6 branches)  
   - Operational documentation  
   - **Risk:** Zero  
   - **Action:** Sequential merge  
   - **Script:** `./scripts/ops/wave3_restore_batch.sh tier-a-runbooks`

3. **Roadmaps & Housekeeping** (5 branches)  
   - Roadmap docs, finalization reports  
   - **Risk:** Zero  
   - **Action:** Review + merge  
   - **Script:** `./scripts/ops/wave3_restore_batch.sh tier-a-roadmaps`

4. **Tooling** (1 branch)  
   - `feat/ops-merge-log-tooling-v1` – Ops tooling  
   - **Risk:** Low (non-runtime)  
   - **Action:** Review + merge  
   - **Script:** `./scripts/ops/wave3_restore_batch.sh tier-a-tooling`

5. **Duplicates** (5 branches – see ACTION 2)

6. **Obsolete Conflicts** (4 branches – see ACTION 1)

### Execution Plan: Tier A

```bash
# Day 1: Pre-flight
./scripts/ops/wave3_restore_batch.sh check-dupes
./scripts/ops/wave3_restore_batch.sh check-conflicts
# → Execute ACTION 1 & 2

# Day 1-2: Batch merge
./scripts/ops/wave3_restore_batch.sh tier-a-merge-logs    # 11 branches
./scripts/ops/wave3_restore_batch.sh tier-a-runbooks      # 6 branches
./scripts/ops/wave3_restore_batch.sh tier-a-roadmaps      # 5 branches
./scripts/ops/wave3_restore_batch.sh tier-a-tooling       # 1 branch

# Verification
make docs-validate
git log --oneline --since="2 days" | wc -l  # expect ~23
```

**Expected Duration:** 2 days  
**Success Criteria:** 23 branches merged, 0 test failures

---

## 🧪 Tier B: Tests/CI (12 branches)

### High-Priority Branches

1. **`chore/tooling-uv-ruff`** (2025-12-17)  
   - Modernize Python tooling (uv + ruff)  
   - **Impact:** Dev environment, linting, dependencies  
   - **Question:** Is uv/ruff adoption approved?  
   - **Test:** `uv --version`, `ruff check .`

2. **`feat/execution-pipeline-fill-idempotency`** (2026-01-03)  
   - Harden CI required checks  
   - **Impact:** CI workflow behavior  
   - **Test:** Trigger CI on test branch

3. **`chore/github-guardrails-p0` + `-p0-only`** (2 branches)  
   - GitHub P0 guardrails setup  
   - **Impact:** Repository rules, PR policies  
   - **Test:** Check GitHub branch protection rules

### Execution Plan: Tier B

```bash
# Day 3-4: One by one with tests
./scripts/ops/wave3_restore_batch.sh tier-b

# This will:
# - Rebase each branch
# - Run 'make test' per branch
# - Report failures
# - Stop on errors

# Manual review for any failures
```

**Expected Duration:** 2 days  
**Success Criteria:** 11-12 branches merged, `make test-full` passes

---

## ⚠️ Tier C: Source Code (8 branches)

### 🔴 High Risk – Execution & Risk

| Branch | Date | Impact | Priority |
|--------|------|--------|----------|
| `pr-334-rebase` | 2026-01-03 | Canonical Order contract for risk gate | 🔴 CRITICAL |
| `feat/risk-liquidity-gate-v1` | 2025-12-25 | Liquidity gate config + logic | 🔴 HIGH |

**Required:**
- Full diff review
- Risk assessment document
- Extended test suite (`make test-backtests`)
- Paper trading smoke test
- **Explicit operator signoff**

### 🟡 Medium Risk – Strategy & Backtest

| Branch | Date | Impact | Priority |
|--------|------|--------|----------|
| `feat/phase-9b-rolling-backtests` | 2025-12-29 | Rolling backtest implementation | 🟡 MEDIUM |
| `feat/strategy-layer-vnext-tracking` | 2025-12-23 | Tracker hooks in BacktestEngine | 🟡 MEDIUM |

**Required:**
- Backtest regression tests
- Engine behavior validation
- Operator review

### 🟢 Low Risk – Infra & Observability

| Branch | Date | Impact | Priority |
|--------|------|--------|----------|
| `vigilant-thompson` | 2025-12-18 | Data lake with DuckDB (P2) | 🟢 LOW |
| `stupefied-montalcini` | 2025-12-18 | (Duplicate of vigilant-thompson?) | 🟢 LOW |
| `vibrant-antonelli` | 2025-12-19 | Suppress MLflow warnings | 🟢 LOW |
| `feat/phase-57-live-status-snapshot-builder-api` | 2025-12-16 | Live status API endpoints | 🟢 LOW |
| `feat/governance-g4-telemetry-automation` | 2025-12-15 | G4 telemetry automation | 🟢 LOW |

**Note:** Data lake branches – check if already merged via other PR

### Execution Plan: Tier C

```bash
# Day 5-7: Manual review per branch

# For each branch:
git checkout -b restore/wave3/<branch> origin/<branch>
git rebase origin/main
git diff origin/main --stat
make test-full

# Document decision in docs/ops/wave3_tier_c_decisions.md
# Only merge with explicit operator signoff
```

**Expected Duration:** 3 days  
**Success Criteria:** 8 branches reviewed, decisions documented, merges completed with signoff

---

## 🗑️ Tier X: Cleanup (26 branches)

### WIP Stash Archives (6 branches)
```
wip/stash-archive-20251227_010347_3
wip/stash-archive-20251227_010344_2
wip/stash-archive-20251227_010341_1
wip/stash-archive-20251227_010316_0
wip/untracked-salvage-20251224_081737
wip/salvage-code-tests-untracked-20251224_082521
```

**Action:** Check for valuable code, then DELETE

### Obsolete Branches (20+ branches)
- Copilot experiments
- Old CI fast-lane branches
- P2 features (defer to Wave4?)
- Old cleanup branches

**Action:** DELETE after quick verification

### Execution Plan: Tier X

```bash
# Day 8: Cleanup day
./scripts/ops/wave3_restore_batch.sh cleanup  # WIP stashes

# Manual cleanup for others (see WAVE3_QUICKSTART.md)
```

**Expected Duration:** 1 day  
**Success Criteria:** 26 branches deleted, final branch count ~20-25

---

## 📅 Recommended Timeline

| Days | Phase | Branches | Status |
|------|-------|----------|--------|
| **Day 0** | Pre-flight + Actions 1&2 | 9 (delete) | ⏸️ Pending approval |
| **Days 1-2** | Tier A docs | 23 | ⏸️ Pending approval |
| **Days 3-4** | Tier B tests/CI | 12 | ⏸️ Pending approval |
| **Days 5-7** | Tier C source review | 8 | ⏸️ Pending approval |
| **Day 8** | Tier X cleanup | 17 | ⏸️ Pending approval |
| **Day 9** | Verification + closeout | — | ⏸️ Pending approval |

**Total Duration:** ~9 days  
**Net Result:** +47 branches merged, -26 branches deleted

---

## ❓ Critical Questions for Operator

Before starting Wave3, please answer:

### Q1: Duplicate Branches (5 branches)
**Question:** Merge ONE or delete ALL 5 duplicate "Wave A+B deployment runbook" branches?  
**Your Decision:** [ ] Merge `beautiful-ritchie` only  |  [ ] Delete all 5  |  [ ] Other: _______

### Q2: Tooling Modernization
**Question:** Is uv + ruff adoption approved? (`chore/tooling-uv-ruff` branch)  
**Your Decision:** [ ] Yes, merge  |  [ ] No, reject  |  [ ] Defer to later

### Q3: Risk Gate Changes
**Question:** Priority for `pr-334-rebase` (canonical Order contract)?  
**Your Decision:** [ ] High priority, review now  |  [ ] Medium priority, defer  |  [ ] Low priority, reject

### Q4: Data Lake Branches
**Question:** Data lake branches (`vigilant-thompson`, `stupefied-montalcini`) – merge or defer to Wave4?  
**Your Decision:** [ ] Merge if tests pass  |  [ ] Defer to Wave4 (P2 priority)  |  [ ] Reject

### Q5: Batch Processing
**Question:** Preferred batch size for Tier A?  
**Your Decision:** [ ] Full blast (all 23 at once)  |  [ ] Conservative (5 branches per batch)  |  [ ] Other: _______

---

## ✅ Approval & Signoff

**Pre-Flight Checklist:**
- [ ] Reviewed this briefing document
- [ ] Reviewed full queue (`docs/ops/wave3_restore_queue.md`)
- [ ] Reviewed quickstart guide (`docs/ops/WAVE3_QUICKSTART.md`)
- [ ] Answered critical questions above
- [ ] Main branch is stable (CI green, tests pass)
- [ ] Backup/snapshot strategy understood
- [ ] Rollback procedures understood
- [ ] Available for Tier C signoffs (days 5-7)

**Approval:**
```
[ ] APPROVED – Proceed with Wave3 execution
[ ] CONDITIONAL – Address comments below first
[ ] REJECTED – Do not proceed (explain below)

Operator Name: _____________________
Date: _____________________
Signature: _____________________

Comments:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

## 📚 Supporting Documents

1. **Full Queue:** `docs/ops/wave3_restore_queue.md` (detailed analysis)
2. **Summary:** `docs/ops/wave3_restore_queue_summary.md` (executive summary)
3. **Quickstart:** `docs/ops/WAVE3_QUICKSTART.md` (execution guide)
4. **Batch Script:** `scripts/ops/wave3_restore_batch.sh` (automation)
5. **This Briefing:** `docs/ops/WAVE3_OPERATOR_BRIEFING.md` (you are here)

---

## 🚨 Risk Mitigation

### Red Lines (STOP execution if encountered)
- Tier A causes test failures → INVESTIGATE
- Tier B breaks CI → ROLLBACK
- Tier C shows unexpected runtime behavior → HALT

### Rollback Plan
```bash
# Per-branch rollback:
git revert <commit-hash>

# Nuclear option (with approval only):
git reset --hard <pre-wave3-commit-sha>
```

### Escalation Path
1. Document issue in `docs/ops/wave3_incidents.md`
2. STOP all merge activity
3. Ping operator for review
4. Execute rollback if needed
5. Postmortem and adjust plan

---

## 📞 Next Steps

1. **Operator:** Review this briefing + supporting docs
2. **Operator:** Answer critical questions above
3. **Operator:** Sign approval section
4. **Execute:** Start with Pre-Flight (ACTION 1 & 2)
5. **Execute:** Proceed with Tier A (days 1-2)
6. **Monitor:** Daily progress updates
7. **Complete:** Wave3 closeout document

---

## 📊 Success Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Tier A merged | 23/23 | `git log --grep="Wave3 Tier A" \| wc -l` |
| Tier B merged | 12/12 | `git log --grep="Wave3 Tier B" \| wc -l` |
| Tier C reviewed | 8/8 | `wave3_tier_c_decisions.md` exists |
| Tier C merged | ≥5/8 | Operator decisions |
| Branches deleted | 26/26 | `git branch -r \| grep origin \| wc -l` ≤25 |
| CI status | GREEN | `gh pr checks origin/main` |
| Tests | 100% pass | `make test-full` |
| Docs | Valid | `make docs-validate` |

---

**Status:** ⚠️ AWAITING OPERATOR APPROVAL

**Ready to execute upon signoff.** 🚀
