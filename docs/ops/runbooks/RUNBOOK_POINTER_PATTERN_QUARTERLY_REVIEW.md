---
title: Runbook – Pointer Pattern Quarterly Review
date: 2026-01-14
audience: ops, docs-maintainers
scope: Documentation Patterns / Drift Control / Orphan Prevention
status: active
---

# Runbook: Pointer Pattern Quarterly Review & Drift Prevention

**Status:** ACTIVE  
**Scope:** Documentation Patterns / Ops Workflows / Runbook Maintenance  
**Risk:** LOW (docs-only, snapshot-based review)  
**Last Updated:** 2026-01-14  
**Version:** v1.0

---

## 1. Purpose

This runbook standardizes the **quarterly review process** for the Pointer Pattern architecture to ensure:

- **Drift Control:** Root canonical runbooks and pointer documents remain synchronized
- **Orphan Prevention:** All pointer documents have valid root targets and index entries
- **Gate Compliance:** Token policy and reference targets gates remain GREEN
- **Navigation Integrity:** Index entries resolve correctly

**What This Is:**
- Snapshot-based periodic audit (quarterly or on-demand)
- Detection of pointer/root misalignment
- Fast fix workflow for discovered issues

**What This Is NOT:**
- Real-time monitoring or watch loops (use CI gates for that)
- Content duplication detection (use drift control runbook)
- New pointer creation (use RUNBOOK_POINTER_PATTERN_OPERATIONS.md)

---

## 2. Scope & Definitions

### 2.1 Key Terms

| Term | Definition | Location Example |
|------|-----------|------------------|
| **Root Canonical Runbook** | Source-of-truth operational runbook at repository root | `RUNBOOK_COMMIT_SALVAGE_CB006C4A.md` |
| **Pointer Document** | Minimal navigation stub in `docs&#47;ops&#47;runbooks&#47;` linking to root runbook | `docs&#47;ops&#47;runbooks&#47;RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md` |
| **Index Entry** | Single-line link in runbook index enabling discoverability | Line in `docs&#47;ops&#47;runbooks&#47;README.md` |
| **Drift** | Content divergence between pointer and root (violates single source of truth) | Pointer adds content beyond minimal stub |
| **Orphan** | Pointer document whose root target no longer exists | Root runbook deleted but pointer remains |

### 2.2 Review Scope

**In Scope:**
- ✅ Verify all pointer documents have valid root targets
- ✅ Verify all pointer documents have index entries
- ✅ Verify gate compliance (token policy, reference targets)
- ✅ Detect content drift (pointer forks root content)
- ✅ Detect root runbook renames/moves without pointer updates

**Out of Scope:**
- ❌ Real-time monitoring (CI handles this)
- ❌ Content quality review (separate editorial process)
- ❌ New pointer creation (use operations runbook)
- ❌ Mass refactoring (requires separate RFC)

---

## 3. Quarterly Review Checklist (Snapshot Mode)

### 3.1 Pre-Flight Checklist

**Before starting review, verify:**

```bash
# 1. Navigate to repo root
cd /Users/frnkhrz/Peak_Trade  # Adjust to your path
pwd && git rev-parse --show-toplevel

# 2. Ensure on main branch (or review branch)
git checkout main
git pull origin main

# 3. Working tree clean
git status -sb
# Expected: "## main...origin/main"

# 4. No active editing in pointer docs
ls -l docs/ops/runbooks/*_POINTER.md
# Review: No uncommitted changes
```

**Pre-Flight Exit Criteria:**
- [ ] On main branch (or dedicated review branch)
- [ ] Working tree clean (no uncommitted changes)
- [ ] Latest remote changes pulled
- [ ] Terminal not stuck (Ctrl-C aborts if needed)

### 3.2 Discovery Phase: Identify All Pointers

```bash
# List all pointer documents
find docs/ops/runbooks -name "*_POINTER.md" -type f
```

**Expected Output (example):**
```
docs/ops/runbooks/RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md
docs/ops/runbooks/RUNBOOK_INSTALLATION_2026_01_POINTER.md
```

**Store list for next steps:**
```bash
POINTERS=$(find docs/ops/runbooks -name "*_POINTER.md" -type f)
echo "$POINTERS" > /tmp/pointer_review_$(date +%Y%m%d).txt
```

### 3.3 Verification Phase: Check Each Pointer

For each pointer document, verify:

#### A) Root Target Exists

```bash
# Extract canonical location from pointer
POINTER="docs/ops/runbooks/RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md"
ROOT=$(grep -m1 "Canonical Location:" "$POINTER" | awk '{print $3}')

# Verify root exists
if [[ -f "$ROOT" ]]; then
  echo "✅ Root exists: $ROOT"
else
  echo "❌ ORPHAN: Root missing: $ROOT"
fi
```

**Expected:** `✅ Root exists` for all pointers.

**Failure Mode:** If `❌ ORPHAN` appears → see Section 7.3 (Orphaned Pointer Recovery).

#### B) Pointer Links Resolve

```bash
# Verify relative link in pointer document
cd "$(dirname "$POINTER")"
RELATIVE_LINK=$(grep -oP '\[.*?\]\(\K[^)]+' "$(basename "$POINTER")" | head -1)

if [[ -f "$RELATIVE_LINK" ]]; then
  echo "✅ Pointer link resolves: $RELATIVE_LINK"
else
  echo "❌ BROKEN LINK: $RELATIVE_LINK"
fi

cd "$OLDPWD"
```

**Expected:** `✅ Pointer link resolves` for all pointers.

**Failure Mode:** If `❌ BROKEN LINK` appears → see Section 7.2 (Reference Targets Violation).

#### C) Index Entry Exists

```bash
# Verify README index contains pointer
POINTER_BASENAME=$(basename "$POINTER")
if grep -q "$POINTER_BASENAME" docs/ops/runbooks/README.md; then
  echo "✅ Index entry exists for: $POINTER_BASENAME"
else
  echo "❌ MISSING INDEX: $POINTER_BASENAME"
fi
```

**Expected:** `✅ Index entry exists` for all pointers.

**Failure Mode:** If `❌ MISSING INDEX` appears → see Section 7.4 (README Entry Missing).

#### D) Content Drift Check

```bash
# Pointer should be minimal (< 50 lines typical)
LINE_COUNT=$(wc -l < "$POINTER")

if [[ "$LINE_COUNT" -lt 100 ]]; then
  echo "✅ Pointer minimal: $LINE_COUNT lines"
else
  echo "⚠️  REVIEW NEEDED: Pointer may have drifted ($LINE_COUNT lines)"
fi
```

**Expected:** `✅ Pointer minimal` (typically < 50 lines).

**Failure Mode:** If `⚠️ REVIEW NEEDED` appears → see Section 7.5 (Content Duplication/Drift).

### 3.4 Gate Compliance Phase

```bash
# Run all docs gates in snapshot mode
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Expected output:
# ✅ Docs Token Policy Gate: PASS
# ✅ Docs Reference Targets Gate: PASS
# ✅ Docs Diff Guard Policy Gate: PASS
```

**Expected:** All 3 gates PASS.

**Failure Modes:**
- `❌ Docs Token Policy Gate: FAIL` → see Section 7.1
- `❌ Docs Reference Targets Gate: FAIL` → see Section 7.2
- `❌ Docs Diff Guard Policy Gate: FAIL` → follow on-screen instructions

---

## 4. Operator Procedure (Fix Workflow)

If review detects issues, follow this workflow:

### 4.1 Branch Creation

```bash
# Create feature branch for fixes
git checkout -b docs/pointer-pattern-quarterly-review-$(date +%Y%m%d)

# Verify branch
git status -sb
# Expected: "## docs/pointer-pattern-quarterly-review-YYYYMMDD"
```

### 4.2 Apply Fixes

**Choose repair procedure based on failure mode (see Section 7):**

- **Orphaned pointer:** Remove pointer + index entry (Section 7.3)
- **Broken link:** Update relative path (Section 7.2)
- **Missing index:** Add index entry (Section 7.4)
- **Content drift:** Trim pointer to minimal stub (Section 7.5)
- **Token policy:** Escape illustrative paths (Section 7.1)

### 4.3 Local Verification

```bash
# Re-run gates after fixes
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Expected: All gates PASS
```

### 4.4 Commit

```bash
# Stage changes
git add docs/ops/runbooks/

# Commit with conventional message
git commit -m "docs(ops): pointer pattern quarterly review fixes YYYY-MM-DD

- Fix: [describe specific fix, e.g., 'removed orphaned pointer for deleted runbook']
- Verified: All docs gates PASS
- Scope: docs-only

Related: RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md"
```

### 4.5 Push & PR

```bash
# Push branch
git push -u origin docs/pointer-pattern-quarterly-review-$(date +%Y%m%d)

# Create PR (use GitHub CLI or web UI)
gh pr create \
  --title "docs(ops): pointer pattern quarterly review YYYY-MM-DD" \
  --body "$(cat <<'EOF'
## Summary
Quarterly review of Pointer Pattern architecture (root canonical runbooks + pointer documents).

## Changes
- [ ] Verified all pointer documents have valid root targets
- [ ] Verified all index entries resolve
- [ ] Fixed: [list specific fixes]
- [ ] All docs gates: PASS

## Risk
**LOW** (docs-only)

## Verification
- [x] Local gates: `./scripts/ops/pt_docs_gates_snapshot.sh --changed` → ALL PASS
- [x] Pre-commit hooks: PASS
- [x] Working tree: CLEAN

## Related Runbook
- docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md

## Reviewers
@ops-team
EOF
)"
```

### 4.6 CI & Merge

**Wait for CI checks:**
- ✅ docs-token-policy-gate
- ✅ docs-reference-targets-gate
- ✅ Docs Diff Guard Policy Gate
- ✅ lint-gate
- ✅ All required checks

**After approval:**
```bash
# Merge via GitHub UI (or CLI)
gh pr merge --squash

# Clean up local branch
git checkout main
git pull origin main
git branch -d docs/pointer-pattern-quarterly-review-YYYYMMDD
```

---

## 5. Failure Modes & Fast Fixes

### 5.1 Token Policy Violation

**Symptom:**
```
❌ Docs Token Policy Gate: FAIL
📄 docs/ops/runbooks/RUNBOOK_X_POINTER.md
  Line 15: `scripts/example.py` (ILLUSTRATIVE)
    → Illustrative path token must use &#47; encoding
```

**Root Cause:** Illustrative paths in pointer document not escaped.

**Fix:**
```bash
# Replace forward slashes in illustrative paths with &#47;
# Example: `scripts/example.py` → `scripts&#47;example.py`

# Use autofix tool (if available)
uv run python scripts/ops/autofix_docs_token_policy_inline_code_v2.py \
  --files docs/ops/runbooks/RUNBOOK_X_POINTER.md

# Or manual edit
# sed -i '' 's/`scripts\/example.py`/`scripts\&#47;example.py`/g' docs/ops/runbooks/RUNBOOK_X_POINTER.md
```

**Verify:**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
# Expected: ✅ Docs Token Policy Gate: PASS
```

**References:**
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md)
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md)

### 5.2 Reference Targets Violation

**Symptom:**
```
❌ Docs Reference Targets Gate: FAIL
📄 docs/ops/runbooks/RUNBOOK_X_POINTER.md
  Line 10: [RUNBOOK_OLD.md](../../RUNBOOK_OLD.md) → Target not found
```

**Root Cause:** Root runbook was renamed/moved without updating pointer.

**Fix:**

**Option A: Root runbook renamed (still exists)**
```bash
# Update pointer's relative link
# Example: If root moved from RUNBOOK_OLD.md to RUNBOOK_NEW_2026.md

# Edit pointer document
sed -i '' 's|../../RUNBOOK_OLD.md|../../RUNBOOK_NEW_2026.md|g' \
  docs/ops/runbooks/RUNBOOK_X_POINTER.md

# Verify new target exists
ls -l ../../RUNBOOK_NEW_2026.md  # (from docs/ops/runbooks/)
```

**Option B: Root runbook deleted (orphan)**
→ See Section 5.3 (Orphaned Pointer).

**Verify:**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
# Expected: ✅ Docs Reference Targets Gate: PASS
```

**References:**
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md)

### 5.3 Orphaned Pointer (Root Deleted)

**Symptom:**
```bash
❌ ORPHAN: Root missing: RUNBOOK_COMMIT_SALVAGE_OLD.md
```

**Root Cause:** Root canonical runbook was deleted but pointer document remains.

**Fix:**

**Step 1: Confirm root deletion**
```bash
# Search git history for root runbook
git log --all --oneline --follow -- RUNBOOK_COMMIT_SALVAGE_OLD.md

# If deleted in recent commit:
git show <commit-sha>:RUNBOOK_COMMIT_SALVAGE_OLD.md
```

**Step 2: Remove orphaned pointer**
```bash
# Remove pointer document
git rm docs/ops/runbooks/RUNBOOK_COMMIT_SALVAGE_OLD_POINTER.md
```

**Step 3: Remove index entry**
```bash
# Edit README.md to remove pointer's index entry
# Find line containing "RUNBOOK_COMMIT_SALVAGE_OLD_POINTER.md" and delete it

# Example:
# - [Commit Salvage Workflow](RUNBOOK_COMMIT_SALVAGE_OLD_POINTER.md) ← DELETE THIS LINE
```

**Step 4: Verify**
```bash
# Check no broken references remain
./scripts/ops/pt_docs_gates_snapshot.sh --changed
# Expected: ✅ All gates PASS
```

**Commit:**
```bash
git commit -m "docs(ops): remove orphaned pointer for deleted runbook

- Removed: docs/ops/runbooks/RUNBOOK_COMMIT_SALVAGE_OLD_POINTER.md
- Removed: Index entry in README.md
- Reason: Root canonical runbook was deleted in <commit-sha>
- Verified: All docs gates PASS"
```

### 5.4 README Entry Missing

**Symptom:**
```bash
❌ MISSING INDEX: RUNBOOK_EXAMPLE_POINTER.md
```

**Root Cause:** Pointer document created but index entry not added to README.

**Fix:**

**Step 1: Find correct section in README**
```bash
# Open docs/ops/runbooks/README.md
# Determine correct category (e.g., "CI & Operations", "Patterns", etc.)
```

**Step 2: Add index entry**
```markdown
# Example: Add to "CI & Operations" section

### CI & Operations
...
- [Example Workflow](RUNBOOK_EXAMPLE_POINTER.md) ⭐ — Description of workflow (pointer to root canonical)
```

**Template:**
```markdown
- [<Display Name>](<POINTER_FILENAME>) ⭐ — <Short description> (pointer to root canonical)
```

**Step 3: Verify alphabetical order (if section is sorted)**

**Step 4: Verify gate compliance**
```bash
./scripts/ops/pt_docs_gates_snapshot.sh --changed
# Expected: ✅ All gates PASS
```

**Commit:**
```bash
git add docs/ops/runbooks/README.md
git commit -m "docs(ops): add missing index entry for pointer document

- Added: Index entry for RUNBOOK_EXAMPLE_POINTER.md
- Location: CI & Operations section
- Verified: All docs gates PASS"
```

### 5.5 Content Duplication / Drift

**Symptom:**
```bash
⚠️  REVIEW NEEDED: Pointer may have drifted (150 lines)
```

**Root Cause:** Pointer document accumulated content beyond minimal navigation stub.

**Fix:**

**Step 1: Review pointer content**
```bash
# Check pointer document size
wc -l docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md

# Compare with template (should be ~30-50 lines)
```

**Step 2: Trim to minimal stub**

**Pointer should contain ONLY:**
```markdown
# [Runbook Title] (Pointer)

**Canonical Location:** [Link to root]

**Purpose:** [1-2 sentence summary]

**This is a pointer document.** The full operational runbook is maintained at the canonical location above.

## Quick Access

For the complete runbook, see:
- [Root Canonical Runbook](../../../RUNBOOK_EXAMPLE.md)

## Related Documentation
- [Link to related docs if needed]
```

**Step 3: Move extra content to root runbook**
```bash
# If pointer has operational content, move it to root canonical runbook
# Edit root runbook to incorporate content
# Then trim pointer back to minimal stub
```

**Step 4: Verify**
```bash
wc -l docs/ops/runbooks/RUNBOOK_EXAMPLE_POINTER.md
# Expected: < 50 lines

./scripts/ops/pt_docs_gates_snapshot.sh --changed
# Expected: ✅ All gates PASS
```

**Commit:**
```bash
git commit -m "docs(ops): trim pointer document to minimal stub

- Fixed: Content drift in RUNBOOK_EXAMPLE_POINTER.md
- Moved: Operational content to root canonical runbook
- Result: Pointer now minimal navigation stub
- Verified: All docs gates PASS"
```

---

## 6. Verification

### 6.1 Pre-Commit Verification (Local)

**Before committing fixes:**

```bash
# 1. All docs gates
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
# Expected: ✅ All 3 gates PASS

# 2. Pre-commit hooks (if enabled)
pre-commit run --files docs/ops/runbooks/*

# 3. File structure check
ls -lh docs/ops/runbooks/*_POINTER.md
# Verify: All pointer documents < 5KB (minimal stub size)

# 4. Link verification (manual spot check)
# Pick 2-3 pointer documents, verify relative links resolve
cd docs/ops/runbooks
ls -l $(grep -oP '\[.*?\]\(\K[^)]+' RUNBOOK_COMMIT_SALVAGE_CB006C4A_POINTER.md | head -1)
# Expected: File exists
```

**Exit Criteria:**
- [x] All docs gates: PASS
- [x] Pre-commit hooks: PASS (if applicable)
- [x] All pointer documents < 5KB
- [x] Spot-checked links: All resolve

### 6.2 Expected CI Checks

After PR creation, expect these CI checks:

| Check | Expected Status | Notes |
|-------|----------------|-------|
| docs-token-policy-gate | ✅ PASS | No illustrative path violations |
| docs-reference-targets-gate | ✅ PASS | All markdown links resolve |
| Docs Diff Guard Policy Gate | ✅ PASS | No mass deletions |
| lint-gate | ✅ PASS | Ruff + pre-commit pass |
| dispatch-guard | ✅ PASS | No workflow_dispatch changes |
| ci-required-contexts-control | ✅ PASS | Meta-check |
| Policy Critic Gate | ✅ PASS | No policy violations |
| Check Docs Link Debt Trend | ✅ PASS or ⏳ | Non-blocking informational |

**If any gate fails:**
1. Review CI logs for specific violation
2. Apply fix from Section 5 (Failure Modes)
3. Commit fix: `git commit --amend` or new commit
4. Force push: `git push --force-with-lease` (if amended) or `git push`

### 6.3 Post-Merge Verification

**After PR merge:**

```bash
# 1. Update local main
git checkout main
git pull origin main

# 2. Verify pointers still intact
find docs/ops/runbooks -name "*_POINTER.md" -type f

# 3. Spot-check index entries
grep -c "POINTER.md" docs/ops/runbooks/README.md
# Expected: Number matches pointer count

# 4. Full gate scan (optional, weekly)
./scripts/ops/pt_docs_gates_snapshot.sh --all
# Expected: ✅ All gates PASS
```

---

## 7. Templates

### 7.1 Quarterly Review Issue Template

**Use this template to create a tracking issue for quarterly reviews:**

```markdown
## Quarterly Pointer Pattern Review – [YYYY-QX]

**Due Date:** [Last week of quarter]  
**Assignee:** @ops-team  
**Runbook:** docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md

---

### Checklist

**Discovery Phase:**
- [ ] Identified all pointer documents (count: ___)
- [ ] Created snapshot list: `/tmp/pointer_review_YYYYMMDD.txt`

**Verification Phase:**
- [ ] All root targets exist (no orphans)
- [ ] All pointer links resolve
- [ ] All index entries present
- [ ] No content drift detected
- [ ] All docs gates: PASS

**Fix Phase (if needed):**
- [ ] Created feature branch: `docs/pointer-pattern-quarterly-review-YYYYMMDD`
- [ ] Applied fixes (list below)
- [ ] Local verification: All gates PASS
- [ ] PR created: #___
- [ ] CI checks: All PASS
- [ ] PR merged

**Fixes Applied:**
- [List any fixes, or "None – all checks passed"]

---

### Results

**Total Pointers Reviewed:** ___  
**Issues Found:** ___  
**Issues Fixed:** ___  
**Gate Status:** ✅ PASS / ❌ FAIL

**Notes:**
[Any observations, recommendations for next quarter]
```

### 7.2 PR Body Template

**Use this template for quarterly review PRs:**

```markdown
## Summary
Quarterly review of Pointer Pattern architecture (root canonical runbooks + pointer documents) per RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md.

## Review Date
[YYYY-MM-DD]

## Findings
- **Pointers Reviewed:** [count]
- **Orphans Detected:** [count or "None"]
- **Broken Links:** [count or "None"]
- **Missing Index Entries:** [count or "None"]
- **Content Drift:** [count or "None"]
- **Gate Violations:** [count or "None"]

## Changes
- [ ] Fixed: [specific fix, e.g., "removed orphaned pointer for deleted runbook X"]
- [ ] Fixed: [another fix if applicable]
- [ ] [Or "No fixes needed – all checks passed"]

## Risk
**LOW** (docs-only, snapshot-based review)

## Verification
- [x] Local gates: `./scripts/ops/pt_docs_gates_snapshot.sh --changed` → ALL PASS
- [x] Pre-commit hooks: PASS
- [x] Working tree: CLEAN
- [x] All pointer documents verified

## Related Runbook
- docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md
- docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_OPERATIONS.md

## Reviewers
@ops-team
```

### 7.3 Merge Log Reminder

**If quarterly review fixes are substantial, consider adding merge log entry:**

```bash
# Create merge log entry (optional, for significant fixes)
./scripts/ops/create_merge_log.py \
  --pr-number <PR_NUMBER> \
  --title "Pointer Pattern Quarterly Review YYYY-QX" \
  --summary "Quarterly maintenance of pointer pattern architecture" \
  --impact "LOW" \
  --risk "LOW" \
  --verification "All docs gates PASS, [N] pointers verified"

# Store in docs/ops/merge_logs/
```

---

## 8. Anti-Footgun Checklist

**Before finalizing quarterly review:**

- [ ] **No content duplication:** All pointers remain minimal stubs (< 50 lines typical)
- [ ] **No illusory links:** All markdown links resolve to real files
- [ ] **No token violations:** All illustrative paths use `&#47;` encoding
- [ ] **No broken index:** README.md contains all pointer documents
- [ ] **No orphans:** All pointer documents have valid root targets
- [ ] **No drift:** Pointer content matches minimal stub template
- [ ] **Branch naming:** `docs/pointer-pattern-quarterly-review-YYYYMMDD`
- [ ] **Commit message:** Follows conventional format `docs(ops): ...`
- [ ] **Working tree clean:** No uncommitted changes before starting
- [ ] **Gates GREEN:** All 3 docs gates PASS before and after fixes

---

## 9. Exit Criteria

**Quarterly review is COMPLETE when:**

✅ All pointer documents verified (existence + content)  
✅ All root targets verified (no orphans)  
✅ All index entries verified (no missing links)  
✅ All docs gates: PASS  
✅ No content drift detected (pointers remain minimal)  
✅ Fixes committed and merged (if any issues found)  
✅ Issue closed with summary (findings + fixes)  
✅ Next quarter's review scheduled (create follow-up issue)

---

## 10. Related Documentation

### Runbooks
- [RUNBOOK_POINTER_PATTERN_OPERATIONS.md](RUNBOOK_POINTER_PATTERN_OPERATIONS.md) — Creating and maintaining pointer pattern
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Token policy gate reference
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Reference targets gate operator guide
- [RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md](RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md) — Diff guard gate operator guide

### Scripts
- `scripts/ops/pt_docs_gates_snapshot.sh` — Local docs gates snapshot runner
- `scripts/ops/validate_docs_token_policy.py` — Token policy validator
- `scripts/ops/verify_docs_reference_targets.sh` — Reference targets verifier

### Navigation
- [README.md](README.md) — Ops runbook index
- [../README.md](../README.md) — Ops documentation overview

---

## 11. Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-14 | v1.0 | Initial runbook creation | Cursor AI Agent |

---

**Maintainer:** ops  
**Review Frequency:** Quarterly (or on-demand when pointer pattern changes detected)  
**Last Review:** 2026-01-14
