---
title: Runbook – PR Merge (Squash) → Post-Merge Verify → Docs Gates → Merge Log
owner: ops
maintainer: ops, cursor-multi-agent
review_frequency: quarterly
last_review: 2026-01-14
version: v1.0
status: active
audience: ops, docs-maintainers, cursor-multi-agent
scope: PR Merge Workflows / Docs-Only / Squash Merge / Post-Merge Verification / Merge Log
---

# Runbook: PR Merge (Squash) → Post-Merge Verify → Docs Gates → Merge Log

**Status:** ACTIVE  
**Owner:** ops  
**Maintainer:** ops, cursor-multi-agent  
**Version:** v1.0  
**Last Review:** 2026-01-14  
**Review Frequency:** Quarterly

---

## Purpose & Scope

This runbook operationalizes the standard workflow for a **docs-only** Pull Request that is **merge-ready** (all required checks green) and should be merged using **squash merge**, followed by **post-merge verification** on `main`, **local docs gates snapshot**, and **merge log creation**.

**In-Scope:**
- Docs-only PR merge via `gh pr merge --squash`
- Post-merge verification and sync hygiene on `main`
- Local docs gates snapshot using `scripts/ops/pt_docs_gates_snapshot.sh`
- Merge log creation following repo conventions (`docs/ops/merge_logs/PR_<NUM>_MERGE_LOG.md`)
- Evidence/index updates (minimal, only if required by repo conventions)

**Out-of-Scope:**
- Code-change PR workflows (requires separate testing/validation)
- Modifying branch protection or required checks policies
- Watch/polling loops (explicitly disallowed—snapshots only)
- Emergency hotfixes (use incident response procedures)

---

## Preconditions & Safety

### Operational Constraints

- **No watch loops:** Use snapshots only (single execution, no polling)
- **KEEP EVERYTHING:** Do not remove or shorten existing documentation; apply additive changes only
- **Use verified links only:** All markdown links must resolve to existing files (see "Related Documentation")
- **Token Policy:** Inline code with `/` that is NOT a real repo path, URL, or command → escape with `&#47;`

### Token Policy (Inline Code With Slashes)

**RULE:** If inline code contains `/` and is **not** a real repo path, URL, or command → escape using `&#47;`.

| Type | Example | Safe? | Fix |
|------|---------|-------|-----|
| Real repo path | `docs/ops/runbooks/RUNBOOK_X.md` | ✅ YES | (no escape needed) |
| Command | `git checkout main` | ✅ YES | (auto-exempted) |
| URL | `https://github.com/user/repo` | ✅ YES | (auto-exempted) |
| Illustrative path | `docs/example/file.md` | ❌ NO | `docs&#47;example&#47;file.md` |
| Illustrative branch | `feature/my-branch` | ❌ NO | `feature&#47;my-branch` |

### Reference Targets Gate

**RULE:** Every markdown link `[text](target)` must resolve to an existing file. No phantom targets.

---

## Agent Roles (Cursor Multi-Agent)

### ORCHESTRATOR
- Selects correct workflow path (docs-only + merge-ready)
- Ensures constraints followed (no watch loops, KEEP EVERYTHING)
- Delegates to CI_GUARDIAN / DOCS_SCRIBE / RISK_OFFICER

### CI_GUARDIAN
- Confirms PR is merge-ready (all required checks green)
- Confirms post-merge `main` is clean and synced
- Triggers local docs gates snapshot

### DOCS_SCRIBE
- Creates merge log following repo conventions
- Ensures token-policy-safe inline code and valid reference targets
- Updates evidence index if required

### RISK_OFFICER
- Confirms "docs-only" scope and low risk assumptions
- Reviews failure modes, rollback steps, stop conditions
- Ensures merge log contains clear risk statement

---

## Workflow Phases

### Phase 0: Intake & Context

**Purpose:** Identify PR number, verify merge-ready state, confirm docs-only scope.

**Inputs:**
- PR number (e.g., 723)
- PR state (should be OPEN, not draft)
- CI status (all required checks PASS)

**Terminal Block:**

```bash
# Continuation Guard: If stuck in >, dquote>, heredoc> prompts: press Ctrl-C

cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

# Set PR number
PR_NUMBER=723

# Verify PR is merge-ready
gh pr view ${PR_NUMBER} --json state,title,statusCheckRollup

# Expected: state="OPEN", all checks "conclusion"="SUCCESS"
```

**Verification:**
- [ ] PR state is OPEN
- [ ] All required checks PASS
- [ ] PR is docs-only (verify in GitHub UI or `gh pr diff`)

---

### Phase 1: Pre-Flight (Repo + Continuation Guard)

**Purpose:** Ensure clean working tree, on correct branch, repo verified.

**Terminal Block:**

```bash
# Continuation Guard
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb

# Verify working tree clean
git status

# Expected: "nothing to commit, working tree clean"
# If dirty: stash or commit changes before proceeding
```

**Verification:**
- [ ] Working tree clean (no uncommitted changes)
- [ ] On expected branch (will switch to main after merge)

---

### Phase 2: Execute Merge (Squash)

**Purpose:** Merge PR using squash merge via GitHub CLI.

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

PR_NUMBER=723

# Execute squash merge
echo "🔀 Merging PR #${PR_NUMBER} (squash)..."
gh pr merge ${PR_NUMBER} --squash

# Expected output:
# ✓ Merged pull request #723 (Title...)
# ✓ Deleted branch <branch-name>

# Verify merge succeeded
gh pr view ${PR_NUMBER} --json state,mergedAt,mergeCommit

# Expected: state="MERGED", mergedAt has timestamp
```

**Verification:**
- [ ] PR state changed to "MERGED"
- [ ] `mergedAt` timestamp present
- [ ] Feature branch deleted (GitHub auto-deletes)

**If FAIL:** Do not proceed. Investigate merge failure in GitHub UI.

---

### Phase 3: Post-Merge Verify (main)

**Purpose:** Switch to main, pull merge commit, verify clean state.

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

PR_NUMBER=723

# Switch to main
echo "🔄 Switching to main..."
git checkout main

# Pull merge commit
echo "⬇️  Pulling from origin/main..."
git pull origin main

# Verify pull succeeded
git status -sb
# Expected: ## main...origin/main [clean]

# Find merge commit
echo "🔍 Finding merge commit..."
git log --oneline --grep="#${PR_NUMBER}" -n 1

# Show merge commit details
MERGE_COMMIT=$(git log --oneline --grep="#${PR_NUMBER}" -n 1 | awk '{print $1}')
echo "Merge commit: ${MERGE_COMMIT}"
git show --stat ${MERGE_COMMIT}

# Verify working tree clean
git status

# Expected: "nothing to commit, working tree clean"
```

**Verification:**
- [ ] On main branch
- [ ] Synced with origin/main (no divergence)
- [ ] Merge commit present in log
- [ ] Working tree clean

**If FAIL:** STOP. Investigate:
- If local main has extra commits → see Appendix C (diverged main)
- If merge commit missing → verify merge in GitHub UI

---

### Phase 4: Local Docs Gates Snapshot

**Purpose:** Run local docs gates to verify no regressions.

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

# Run docs gates (changed files only — fast)
echo "🔍 Running docs gates snapshot..."
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base HEAD~1

# Expected output:
# ✅ Docs Token Policy Gate: PASS
# ✅ Docs Reference Targets Gate: PASS
# ✅ Docs Diff Guard Policy Gate: PASS
# 🎉 All gates passed!

# Alternative: Full scan (comprehensive, slower)
# ./scripts/ops/pt_docs_gates_snapshot.sh --all
```

**Verification:**
- [ ] All 3 gates PASS (token policy, reference targets, diff guard)
- [ ] No new violations introduced
- [ ] Exit code 0 (success)

**If FAIL (Gate Regression):**
- STOP. Do NOT fix on main directly.
- Create hotfix branch: `git checkout -b hotfix&#47;docs-gate-regression-pr-${PR_NUMBER}`
- Apply minimal fix following gate error instructions
- Verify fix: `./scripts/ops/pt_docs_gates_snapshot.sh --changed --base main`
- Commit and create hotfix PR
- See Appendix C for detailed recovery

---

### Phase 5: Merge Log Creation

**Purpose:** Create merge log for audit trail.

**When to Create Merge Log:**
- PR introduces new runbooks, patterns, or significant docs changes
- PR fixes critical bugs or gate violations
- PR is part of auditable workflow (governance requirements)
- Evidence trail needed for quarterly reviews

**Skip if:**
- Trivial typo fixes (< 5 lines, no semantic impact)
- Automated formatting-only changes
- Already documented in higher-level issue

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

PR_NUMBER=723
MERGE_COMMIT=$(git log --oneline --grep="#${PR_NUMBER}" -n 1 | awk '{print $1}')
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M UTC")

# Create merge log
cat > docs/ops/merge_logs/PR_${PR_NUMBER}_MERGE_LOG.md <<'EOFMERGE'
# Merge Log: PR #723 – fix(docs): fix token policy violations

**Date:** 2026-01-14  
**PR:** #723  
**Branch:** docs&#47;runbook-pointer-pattern-quarterly-review → main  
**Merge Commit:** 96babd20  
**Risk:** LOW  
**Scope:** docs-only

---

## Summary

Fixed token policy violations in existing Pointer Pattern Quarterly Review runbook. No new content added; only illustrative paths escaped with &#47; encoding per token policy.

## Changes

- Modified: `docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md`
  - 5 insertions(+), 5 deletions(-)
  - Escaped illustrative paths: lines 331, 340, 661, 671, 764

## Verification

- [x] All CI checks: PASS (27/27)
- [x] Docs gates: PASS
  - [x] Token policy: PASS (0 violations)
  - [x] Reference targets: PASS (all links resolve)
  - [x] Diff guard: PASS (no mass deletions)
- [x] Post-merge verify: CLEAN
- [x] Working tree: CLEAN

## Risk Assessment

**Risk Level:** LOW

**Rationale:**
Docs-only changes, token escaping only, no semantic changes, all gates pass.

## Related Documentation

- PR: #723 (https://github.com/rauterfrank-ui/Peak_Trade/pull/723)
- Runbook: docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md
- Related: docs/ops/runbooks/RUNBOOK_POINTER_PATTERN_OPERATIONS.md

---

**Operator:** Cursor AI Agent  
**Verified:** 2026-01-14 16:30 UTC
EOFMERGE

# Verify merge log created
ls -lh docs/ops/merge_logs/PR_${PR_NUMBER}_MERGE_LOG.md

# Add and commit
git add docs/ops/merge_logs/PR_${PR_NUMBER}_MERGE_LOG.md
git commit -m "docs(ops): add merge log for PR #${PR_NUMBER}

- Merge log: PR_${PR_NUMBER}_MERGE_LOG.md
- Risk: LOW
- Scope: docs-only"

# Push to main
git push origin main
```

**Verification:**
- [ ] Merge log created in `docs/ops/merge_logs/`
- [ ] Merge log follows repo template
- [ ] All required fields present
- [ ] Merge log committed to main

---

### Phase 6: Evidence & Index Updates (Optional)

**Purpose:** Update evidence index or runbook index if required by repo conventions.

**When to Update:**
- New runbook created (add to `docs/ops/runbooks/README.md`)
- New pattern introduced (document in frontdoor)
- Governance requires audit trail

**Skip if:**
- Runbook already indexed
- No new discoverable artifacts
- Trivial fixes

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

# Check if runbook index needs update
# (Manual verification — no automatic changes)

echo "ℹ️  Verify runbook index if new runbook was created:"
echo "   File: docs/ops/runbooks/README.md"
echo "   Check: Does new runbook appear in index?"

# If update needed: edit README.md manually, then:
# git add docs/ops/runbooks/README.md
# git commit -m "docs(ops): update runbook index for PR #NNN"
# git push origin main
```

**Verification:**
- [ ] Runbook index updated (if new runbook)
- [ ] All links in index resolve
- [ ] No orphan docs created

---

### Phase 7: Closeout

**Purpose:** Final verification, clean working tree.

**Terminal Block:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

# Final verification
git status

# Expected: "nothing to commit, working tree clean"

# Verify on main
git branch --show-current
# Expected: main

# Verify synced
git status -sb
# Expected: ## main...origin/main

echo "✅ Workflow complete!"
echo "   PR #${PR_NUMBER} merged"
echo "   Merge log created"
echo "   Docs gates: PASS"
echo "   Working tree: CLEAN"
```

**Verification:**
- [ ] Working tree clean
- [ ] On main branch
- [ ] Synced with origin/main
- [ ] No pending changes

---

## Stop Conditions (Abort Criteria)

**STOP workflow immediately if ANY of these occur:**

1. ❌ **CI Status Regression:** Required checks fail after merge
2. ❌ **Main Branch Diverged:** Local main ≠ origin/main unexpectedly
3. ❌ **Docs Gates Regress:** Gates fail post-merge (CI passed but local fails)
4. ❌ **Merge Conflict:** PR shows "CONFLICTING" state
5. ❌ **Policy Violation:** Policy critic gate fails
6. ❌ **Working Tree Dirty:** Uncommitted changes prevent verification
7. ❌ **Required Check Missing:** Checks still pending
8. ❌ **Manual Hold Flag:** PR has "DO NOT MERGE" label

**When stopped:**
- Document stop reason
- Preserve current state (no destructive operations)
- Notify operator
- Wait for explicit "continue" or "abort" decision

---

## Appendix A: Terminal Pre-Flight + Continuation Guard

**Use this pattern before ALL terminal blocks:**

```bash
# Continuation Guard: If stuck in >, dquote>, heredoc> prompts: press Ctrl-C

cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb
```

**Why:**
- Prevents runaway heredocs or unclosed quotes
- Ensures correct working directory
- Verifies git repo state
- No hard exit (allows operator to fix manually)

---

## Appendix B: Troubleshooting Matrix

### Token Policy Violations

**Symptom:** `❌ Docs Token Policy Gate: FAIL`

**Fix:**
```bash
# Escape illustrative paths with &#47;
# Example: `docs/example/file.md` → `docs&#47;example&#47;file.md`

# Use autofix tool
uv run python scripts/ops/autofix_docs_token_policy_inline_code_v2.py \
  --files <file>

# Verify
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base main
```

### Reference Targets Violations

**Symptom:** `❌ Docs Reference Targets Gate: FAIL`

**Fix:**
```bash
# Option A: Create missing target file
# Option B: Remove broken link
# Option C: Fix relative path

# Verify
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base main
```

### Main Branch Diverged

**Symptom:** `git pull` shows divergence

**Fix:**
```bash
# Inspect divergence
git log --oneline --graph --all -10

# If safe to rebase (only merge log commit local):
git fetch origin
git rebase origin/main

# Verify
git status -sb

# Push (only if rebase clean)
git push origin main

# If rebase fails:
git rebase --abort
echo "❌ Manual intervention required"
```

---

## Appendix C: Minimal Follow-Up PR Workflow

**If additional docs fixes needed after merge:**

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git status -sb

# Create hotfix branch
git checkout -b docs&#47;hotfix-pr-NNN-followup

# Apply minimal fix

# Verify locally
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base main

# Commit
git add <files>
git commit -m "fix(docs): follow-up fix for PR #NNN

- Fixed: [describe fix]
- Verified: All docs gates PASS"

# Push and create PR
git push -u origin docs&#47;hotfix-pr-NNN-followup
gh pr create --title "fix(docs): follow-up fix for PR #NNN" --base main

# Merge using this runbook (repeat workflow)
```

---

## Appendix D: Snapshot Templates

### Post-Merge Verify Snapshot

```markdown
## Post-Merge Verify Snapshot — PR #NNN

**Date:** YYYY-MM-DD HH:MM UTC  
**Merge Commit:** <SHA>  
**Branch:** main

### Git Status
- [x] On main branch
- [x] Synced with origin/main
- [x] Working tree clean

### Merge Commit Verification
```
git log --oneline --grep="#NNN" -n 1
# Output: <SHA> <commit message> (#NNN)
```

### Files Changed
```
gh pr view NNN --json files --jq '.files[].path'
# Output: [list of files]
```
```

### Docs Gates Snapshot

```markdown
## Docs Gates Snapshot — PR #NNN

**Date:** YYYY-MM-DD HH:MM UTC  
**Mode:** changed files (--changed --base HEAD~1)

### Results
```
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base HEAD~1

✅ Docs Token Policy Gate: PASS (N files scanned)
✅ Docs Reference Targets Gate: PASS (M references found)
✅ Docs Diff Guard Policy Gate: PASS
🎉 All gates passed!
```

### Violations (if any)
- None
```

---

## Related Documentation

### Runbooks
- [RUNBOOK_POINTER_PATTERN_OPERATIONS.md](RUNBOOK_POINTER_PATTERN_OPERATIONS.md) — Pointer pattern operations
- [RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md](RUNBOOK_POINTER_PATTERN_QUARTERLY_REVIEW.md) — Quarterly review
- [RUNBOOK_DOCS_TOKEN_POLICY_GATE.md](RUNBOOK_DOCS_TOKEN_POLICY_GATE.md) — Token policy gate
- [RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md](RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md) — Reference targets gate

### Scripts
- `scripts/ops/pt_docs_gates_snapshot.sh` — Docs gates snapshot runner
- `scripts/ops/check_merge_log_hygiene.py` — Merge log hygiene checker

### Navigation
- [README.md](README.md) — Ops runbook index
- [../README.md](../README.md) — Ops documentation overview

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-14 | v1.0 | Initial runbook creation | Cursor AI Agent |

---

**Maintainer:** ops, cursor-multi-agent  
**Review Frequency:** Quarterly  
**Last Review:** 2026-01-14  
**Status:** ACTIVE
