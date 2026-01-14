# RUNBOOK: Docs-Only Deliverable to PR Fast Path (Cursor Multi-Agent)

**Version:** 1.0  
**Status:** READY  
**Risk Level:** LOW  
**Audience:** Operators, Cursor Agent, Human-in-the-Loop  
**Use Case:** Fast path from completed local deliverable to merged PR

---

## Purpose

This runbook provides an **ultra-practical fast path** for committing and PR'ing a docs-only deliverable that is already complete locally. Use this when:
- You have finished creating/editing docs files
- Working tree contains only intended changes
- You're ready to: Stage → Commit → Local Gates → Push → PR → CI → Merge → Verify

**Not covered:** Initial branch creation, extensive edits, merge conflict resolution. For full lifecycle, see the comprehensive PR lifecycle runbook.

---

## Preconditions

Before starting this runbook, ensure:

- [ ] **Deliverable is complete** (docs files created/edited, content finalized)
- [ ] **Working tree contains only intended changes** (verify with git status)
- [ ] **No untracked files except intended deliverables** (or they are safe to ignore)
- [ ] **You are on the correct feature branch** (not main)
- [ ] **Terminal prompt is normal** (not in continuation mode: dquote, cmdsubst, heredoc)

**If any precondition is false:** STOP. Resolve issue first, then return to this runbook.

---

## Phase 0 — Preconditions Check

### What Must Be True

**Deliverable Status:**
- Docs files are finalized (content complete, no pending edits)
- If multiple files: all are ready

**Working Tree Status:**
- Only intended changes present
- No accidental edits to code files (src, scripts, config, .github)
- No dirty files on main (if you switched from main)

**Branch Status:**
- On a feature branch (not main)
- Branch name is meaningful (e.g. docs-ops-runbook-fastpath)

**Terminal Status:**
- Prompt is normal (not dquote>, cmdsubst>, heredoc>, >)
- If hung: Ctrl-C to exit continuation mode

---

## Phase 1 — Pre-Flight (Continuation-Guard + Repo-Verifikation)

### Continuation-Guard

**WICHTIG:** If your terminal prompt shows any of these continuation markers, press Ctrl-C first:
- dquote> (open double-quote)
- cmdsubst> (open command substitution)
- heredoc> (open heredoc)
- > (open continuation)

**Action:** Press Ctrl-C, verify prompt returns to normal.

### Repo Verification Commands

Execute these commands to verify repo state:

```bash
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
```

```bash
pwd
```

**Expected Output:**

```
/Users/frnkhrz/Peak_Trade
```

**If different:** STOP. Navigate to correct directory.

```bash
git rev-parse --show-toplevel
```

**Expected Output:**

```
/Users/frnkhrz/Peak_Trade
```

**If error:** STOP. Not in a git repository.

```bash
git status -sb
```

**Expected Output (example on feature branch):**

```
## docs-ops-runbook-fastpath
?? docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

or

```
## docs-ops-runbook-fastpath
 M docs/ops/existing-file.md
```

**Red Flags:**
- If on main branch: STOP. Create/switch to feature branch first.
- If shows modified files outside docs/: STOP. Investigate unintended changes.

### Checklist Phase 1

- [ ] Terminal prompt is normal (no continuation mode)
- [ ] pwd shows correct repo directory
- [ ] git rev-parse confirms git repo
- [ ] git status shows feature branch (not main)
- [ ] git status shows only intended changes (docs files)

---

## Phase 2 — Stage + Diff Sanity

### Purpose

Stage your docs-only changes and verify no unintended files are included.

### Commands

**Step 1: Inspect unstaged changes**

```bash
git diff --stat
```

**Expected Output (example):**

```
 docs/ops/runbooks/RUNBOOK_NEW.md | 300 ++++++++++++++++++++++
 1 file changed, 300 insertions(+)
```

**Red Flag:** If shows changes to src/, scripts/, config/, .github/ → STOP. Investigate.

**Step 2: Stage docs files**

**Option A: Stage specific file(s)**

```bash
git add docs/ops/runbooks/RUNBOOK_NEW.md
```

**Option B: Stage entire docs directory**

```bash
git add docs/
```

**Option C: Stage multiple specific files**

```bash
git add docs/ops/runbooks/FILE1.md docs/ops/runbooks/FILE2.md
```

**Choose based on what you changed. Prefer specific files for precision.**

**Step 3: Verify staged changes**

```bash
git diff --cached --stat
```

**Expected Output:**

```
 docs/ops/runbooks/RUNBOOK_NEW.md | 300 ++++++++++++++++++++++
 1 file changed, 300 insertions(+)
```

**This shows what will be committed. Verify it matches your intent.**

**Step 4: Verify status**

```bash
git status -sb
```

**Expected Output:**

```
## docs-ops-runbook-fastpath
A  docs/ops/runbooks/RUNBOOK_NEW.md
```

(A = Added, M = Modified)

### Stop Conditions

**STOP if:**
- git diff --cached shows files outside docs/, README, OPERATOR_, PHASE_ → **STOP**
- Unintended files are staged (config, code, CI workflows) → **STOP**

**How to unstage:**

```bash
git restore --staged <file>
```

Then re-stage only intended files.

### Checklist Phase 2

- [ ] git diff --stat reviewed (only docs files)
- [ ] git add executed for intended files
- [ ] git diff --cached --stat shows only intended files
- [ ] git status shows correct staged files (A or M)
- [ ] No code/config/CI files staged

---

## Phase 3 — Local Docs Gates Snapshot (changed, Snapshot-only)

### Purpose

Run local docs gates to catch policy violations before pushing. **Snapshot only** (no watch loops).

### Primary: Unified Snapshot Script (if available)

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

**Expected Output:**

```
[INFO] Running docs gates snapshot for changed files...
[PASS] Token-Policy Gate: 0 violations
[PASS] Reference-Targets Gate: 0 broken links
[PASS] Diff-Guard Gate: No unexpected changes
[INFO] All gates passed.
```

**If script doesn't exist:** Proceed to Fallback.

### Fallback: Individual Gate Checks

**Check 1: Token-Policy Gate**

```bash
python scripts/ops/validate_docs_token_policy.py --changed
```

**Expected Output:**

```
Validating token policy for changed files...
[PASS] No violations detected.
```

**Check 2: Reference-Targets Gate**

```bash
bash scripts/ops/verify_docs_reference_targets.sh --changed
```

**Expected Output:**

```
Checking changed files for broken reference targets...
[PASS] All reference targets valid.
```

### Failure Patterns + Minimal-Invasive Fix

**Failure Pattern 1: Token-Policy Violation**

**Symptom:**

```
[FAIL] docs/ops/runbooks/FILE.md:67
  Inline backtick with slash detected: `docs/ops/file.md`
```

**Cause:** Inline backtick with slash (e.g. `path&#47;to&#47;file.md`)

**Fix Pattern:**
1. Open file, go to line 67
2. Replace inline backtick with plain text (no backticks) or use HTML entity for slash: `path&#47;to&#47;file.md`
3. Or use fenced code block if it's a command/path snippet
4. Re-run check

**Failure Pattern 2: Broken Reference Target**

**Symptom:**

```
[FAIL] docs/ops/runbooks/FILE.md:45
  Link target does not exist: docs/non-existent.md
```

**Cause:** Markdown link points to non-existent file

**Fix Pattern:**
1. Open file, go to line 45
2. Options:
   - Fix path to correct target
   - Remove link, use plain text
   - Create target file (if sensible)
3. Re-run check

**Failure Pattern 3: Diff-Guard (large deletion)**

**Symptom:**

```
[WARN] Large deletion detected in FILE.md (100+ lines removed)
```

**Cause:** Accidentally removed content

**Fix Pattern:**
1. Review git diff for that file
2. If deletion was unintended: git restore, re-apply only intended changes
3. If deletion was intended: Document in commit message
4. Re-run check

### Checklist Phase 3

- [ ] Primary snapshot script executed (or fallback checks)
- [ ] Token-Policy Gate: PASS
- [ ] Reference-Targets Gate: PASS
- [ ] Diff-Guard Gate: PASS or N/A
- [ ] If FAIL: Fix applied, re-run, achieved PASS

---

## Phase 4 — Commit

### Purpose

Commit staged changes with clear, policy-compliant message.

### Commit Message Template

**Format:**

```
docs(ops): <short description max 72 chars>

<Body with details>
```

**Example 1 (new file):**

```
docs(ops): add docs-only deliverable fastpath runbook

- New file: docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
- Scope: Fast path from completed deliverable to merged PR
- Risk: LOW (docs-only, additive)
- Verification: Local docs gates passed (Token-Policy, Reference-Targets)
```

**Example 2 (update existing):**

```
docs(ops): update operator quickstart with salvage pattern

- Modified: docs/ops/OPERATOR_QUICKSTART.md
- Added: Section on reflog recovery
- Risk: LOW (docs-only, clarification)
- Verification: Local docs gates passed
```

### Commit Command

**Simple commit:**

```bash
git commit -m "docs(ops): add docs-only deliverable fastpath runbook" -m "- New file: docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
- Scope: Fast path from completed deliverable to merged PR
- Risk: LOW (docs-only, additive)
- Verification: Local docs gates passed (Token-Policy, Reference-Targets)"
```

**Expected Output:**

```
[docs-ops-runbook-fastpath abc1234] docs(ops): add docs-only deliverable fastpath runbook
 1 file changed, 300 insertions(+)
 create mode 100644 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

### Verify Commit

```bash
git log -1 --stat
```

**Expected Output:**

```
commit abc1234...
Author: ...
Date: ...

    docs(ops): add docs-only deliverable fastpath runbook

    - New file: docs/ops/runbooks/...
    - Scope: ...

 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md | 300 +++++++++
 1 file changed, 300 insertions(+)
```

### When Commit Hook Fails

**Symptom:**

```
error: pre-commit hook failed
```

**Triage Steps:**
1. Read hook output (shows what check failed)
2. Common causes:
   - Linter error (markdownlint, etc.)
   - Formatting issue
   - Policy violation missed by local gates
3. Fix issue, re-stage, re-commit
4. If hook is broken/flaky: Document and escalate (don't skip hook with --no-verify unless approved)

### Checklist Phase 4

- [ ] Commit message follows template (docs(scope): description)
- [ ] Commit message includes body with details
- [ ] git commit successful (no hook failures)
- [ ] git log -1 shows correct commit
- [ ] Commit stats match expectations (only docs files)

---

## Phase 5 — Push

### Purpose

Push committed changes to remote origin.

### Commands

**Push current branch to origin:**

```bash
git push -u origin HEAD
```

**Why HEAD?** It pushes current branch regardless of name. Safer than hardcoding branch name.

**Expected Output:**

```
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.23 KiB | 1.23 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
To https://github.com/USER/Peak_Trade.git
   abc1234..def5678  docs-ops-runbook-fastpath -> docs-ops-runbook-fastpath
Branch 'docs-ops-runbook-fastpath' set up to track remote branch 'docs-ops-runbook-fastpath' from 'origin'.
```

**If this is the first push for this branch:**

```
To https://github.com/USER/Peak_Trade.git
 * [new branch]      docs-ops-runbook-fastpath -> docs-ops-runbook-fastpath
Branch 'docs-ops-runbook-fastpath' set up to track remote branch 'docs-ops-runbook-fastpath' from 'origin'.
```

### Failure Modes

**Failure: Permission Denied**

**Symptom:**

```
remote: Permission to USER/Peak_Trade.git denied
fatal: unable to access 'https://github.com/USER/Peak_Trade.git/': The requested URL returned error: 403
```

**Cause:** GitHub auth expired or incorrect

**Fix:**

```bash
gh auth status
```

If expired:

```bash
gh auth login
```

Then retry push.

**Failure: Branch Diverged**

**Symptom:**

```
! [rejected]        docs-ops-runbook-fastpath -> docs-ops-runbook-fastpath (non-fast-forward)
```

**Cause:** Remote branch has commits not in your local branch

**Fix:**
1. Fetch and inspect:

```bash
git fetch origin
git log --oneline --graph origin/docs-ops-runbook-fastpath..HEAD
```

2. If safe to overwrite remote (you're sure local is correct):

```bash
git push --force-with-lease
```

3. If unsure: STOP. Investigate divergence cause.

### Checklist Phase 5

- [ ] git push successful (no permission errors)
- [ ] Branch now exists on origin
- [ ] Tracking set up (origin/branch-name)
- [ ] No divergence warnings

---

## Phase 6 — PR Create or PR Update

### Purpose

Create a new PR or update existing PR with current changes.

### Decision: Create or Update?

**Create:** If no PR exists yet for this branch  
**Update:** If PR already exists (e.g. you pushed more commits)

**Check if PR exists:**

```bash
gh pr list --head docs-ops-runbook-fastpath
```

**Expected Output (no PR):**

```
(empty output)
```

**Expected Output (PR exists):**

```
#123  docs(ops): add fastpath runbook  docs-ops-runbook-fastpath
```

### Option A: PR Create

**If no PR exists, create one:**

```bash
gh pr create \
  --base main \
  --head docs-ops-runbook-fastpath \
  --title "docs(ops): add docs-only deliverable fastpath runbook" \
  --body-file PR_BODY.md
```

**Or inline body:**

```bash
gh pr create \
  --base main \
  --head docs-ops-runbook-fastpath \
  --title "docs(ops): add docs-only deliverable fastpath runbook" \
  --body "## Summary

Fast path runbook for docs-only deliverables: from completed local work to merged PR.

## Changes

- New file: docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
- Scope: Docs-only, additive

## Verification

- [x] Local docs gates passed (Token-Policy, Reference-Targets)
- [x] No code changes (src, scripts, config, .github)
- [x] Clean git diff (only docs)

## Risk Assessment

- Code Risk: NONE (docs-only)
- Operational Risk: LOW (no live system impact)
- Gate Risk: LOW (passed local snapshot)

## Type

Documentation-only (additive)"
```

**Expected Output:**

```
Creating pull request for docs-ops-runbook-fastpath into main in USER/Peak_Trade

https://github.com/USER/Peak_Trade/pull/123
```

**Capture PR number (e.g. 123) for next phases.**

### Option B: PR Update

**If PR already exists and you pushed more commits:**

The PR auto-updates with new commits. But you may want to update title/body:

```bash
gh pr edit 123 \
  --title "docs(ops): add docs-only deliverable fastpath runbook (v2)" \
  --body "Updated with additional sections..."
```

### PR Body Template (for manual use or file)

If you prefer to use a file for PR body, create PR_BODY.md:

```markdown
## Summary

Fast path runbook for docs-only deliverables: from completed local work to merged PR.

## Why

Provides ultra-practical operator guidance for the most common docs-only workflow: you have a finished deliverable locally, now need to commit/PR/merge it efficiently.

## Changes

- **New File:** docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
- **Lines:** ~600 lines
- **Scope:** Docs-only, additive (no code changes)

## Verification

- [x] Local docs gates snapshot passed (Token-Policy, Reference-Targets)
- [x] No code changes (src, scripts, config, .github)
- [x] Clean git diff (only docs files)
- [x] Commit message follows template (docs(ops): ...)

## Risk Assessment

- **Code Risk:** NONE (docs-only)
- **Operational Risk:** LOW (no live system impact)
- **Gate Risk:** LOW (passed local snapshot)

## Type

**Documentation-only (additive)**

## Operator How-To

This runbook documents the fast path workflow itself. To use it:
1. Have a completed docs deliverable locally
2. Follow phases: Pre-Flight → Stage → Local Gates → Commit → Push → PR → CI → Merge → Verify
3. No watch loops; snapshot commands included
4. Stop conditions clearly marked

## References

- Related: RUNBOOK_DOCS_PR_LIFECYCLE_BRANCH_TO_POSTMERGE_CURSOR_MULTI_AGENT.md (comprehensive lifecycle)
- Policy: docs-only scope (no code changes)
- Compliance: Token-Policy, Reference-Targets gates passed
```

Then use:

```bash
gh pr create --base main --head docs-ops-runbook-fastpath --title "..." --body-file PR_BODY.md
```

### Checklist Phase 6

- [ ] PR created successfully (received PR URL and number)
- [ ] PR title follows convention (docs(scope): description)
- [ ] PR body includes Summary, Changes, Verification, Risk, Type
- [ ] PR body explicitly states "docs-only" and "no code changes"
- [ ] PR number captured (e.g. 123) for next phases

---

## Phase 7 — CI Snapshot (ohne Watch) + Merge

### Purpose

Monitor CI checks via snapshot commands (no watch loops), then merge when green.

### Snapshot Commands

**View PR metadata:**

```bash
gh pr view 123 --json number,state,mergeable,headRefName
```

**Expected Output:**

```json
{
  "number": 123,
  "state": "OPEN",
  "mergeable": "MERGEABLE",
  "headRefName": "docs-ops-runbook-fastpath"
}
```

**Red Flags:**
- mergeable: CONFLICTING → STOP. Merge conflict, needs resolution.
- state: CLOSED → STOP. PR was closed, investigate.

**View PR checks:**

```bash
gh pr checks 123
```

**Expected Output (all green):**

```
All checks passed
✓  CI / docs-gates       1m15s
✓  CI / lint-markdown    38s
✓  CI / reference-check  29s
```

**If checks pending:**

```
Some checks are still pending
○  CI / docs-gates       (pending)
○  CI / lint-markdown    (pending)
```

**Action:** Wait 1-2 minutes, then re-run gh pr checks 123 (snapshot, not watch).

**If checks failed:**

```
Some checks failed
✗  CI / docs-gates       1m23s
✓  CI / lint-markdown    45s
```

**Action:** See "Failure Modes" below.

### Merge Command (when all checks green)

**Auto-merge (recommended):**

```bash
gh pr merge 123 --squash --auto --delete-branch
```

**Expected Output:**

```
✓ Enabled auto-merge on pull request #123
✓ Pull request #123 will be automatically merged via squash when all requirements are met
✓ Pull request #123 will delete branch docs-ops-runbook-fastpath when merged
```

**What this does:**
- Enables auto-merge
- Will squash commits into one
- Will auto-delete branch after merge
- Merge happens when all required checks pass (you don't need to wait)

**Manual merge (if you prefer to wait and merge manually):**

Wait for checks to pass, then:

```bash
gh pr merge 123 --squash --delete-branch
```

**Expected Output:**

```
✓ Merged pull request #123 (docs(ops): add docs-only deliverable fastpath runbook)
✓ Deleted branch docs-ops-runbook-fastpath
```

### Failure Modes

**Mode 1: Required Check Missing**

**Symptom:** PR shows mergeable but no checks running

**Cause:** CI config may not be complete or branch protection not set up

**Action:**
1. Verify .github/workflows/ has docs-gates workflow
2. Check branch protection rules (gh repo view --json branchProtectionRules)
3. If missing: Escalate to admin

**Mode 2: Pending Checks (stuck)**

**Symptom:** Checks show pending for >5 minutes

**Cause:** CI infrastructure issue or queue backup

**Action:**
1. Check GitHub Status: https://www.githubstatus.com
2. Wait 5-10 minutes
3. If still stuck: Cancel and re-trigger (push empty commit or close/reopen PR)

**Mode 3: Docs Gates Fail**

**Symptom:**

```
✗  CI / docs-gates  failed
```

**Cause:** Token-Policy or Reference-Targets violation that local check missed

**Action:**
1. View CI logs:

```bash
gh pr view 123 --json statusCheckRollup
```

or open in browser:

```bash
gh pr view 123 --web
```

2. Identify violation (file, line, pattern)
3. Fix locally:

```bash
git switch docs-ops-runbook-fastpath
# Edit file to fix violation
git add <file>
git commit -m "docs: fix gate violation"
git push
```

4. CI will auto-rerun. Re-snapshot: gh pr checks 123

### Checklist Phase 7

- [ ] gh pr view shows mergeable: MERGEABLE
- [ ] gh pr checks shows all required checks passed (green checkmarks)
- [ ] gh pr merge executed (auto or manual)
- [ ] PR merged successfully (verify with gh pr view 123)

---

## Phase 8 — Post-Merge Verify (main)

### Purpose

Verify changes landed correctly on main branch.

### Commands

**Step 1: Switch to main**

```bash
git switch main
```

**Expected Output:**

```
Switched to branch 'main'
Your branch is behind 'origin/main' by 1 commit, and can be fast-forwarded.
```

**Step 2: Pull latest**

```bash
git pull --ff-only
```

**Expected Output:**

```
Updating abc1234..def5678
Fast-forward
 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md | 300 +++++++++
 1 file changed, 300 insertions(+)
 create mode 100644 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

**If error (non-fast-forward):** STOP. Main has diverged. Investigate with git log --graph.

**Step 3: Verify status**

```bash
git status -sb
```

**Expected Output:**

```
## main...origin/main
```

(Clean, up-to-date)

**Step 4: Verify file exists**

```bash
ls -la docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

**Expected Output:**

```
-rw-r--r--  1 user  staff  25000 Jan 14 10:30 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

**If file not found:** FAIL. Merge didn't work. Escalate.

**Step 5: Inspect content (optional)**

```bash
head -n 10 docs/ops/runbooks/RUNBOOK_DOCS_ONLY_DELIVERABLE_TO_PR_FASTPATH_CURSOR_MULTI_AGENT.md
```

**Expected Output:** First 10 lines showing header, title, version, etc.

### Optional: Local Snapshot on Main

For extra verification, run docs gates on main:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh
```

**Expected Output:**

```
[INFO] Running docs gates snapshot...
[PASS] Token-Policy Gate: 0 violations
[PASS] Reference-Targets Gate: 0 broken links
[INFO] All gates passed.
```

**Note:** This runs on entire docs directory, not just changed files. Should still be green.

### Checklist Phase 8

- [ ] git switch main successful
- [ ] git pull --ff-only successful (fast-forward)
- [ ] git status shows clean tree, up-to-date with origin
- [ ] ls shows new/modified file exists
- [ ] Optional: local snapshot on main passed

---

## Phase 9 — Cleanup

### Purpose

Clean up local feature branch and verify repository state.

### Commands

**Step 1: Fetch with prune (remove stale remote refs)**

```bash
git fetch --prune
```

**Expected Output:**

```
From https://github.com/USER/Peak_Trade
 - [deleted]         (none)     -> origin/docs-ops-runbook-fastpath
```

(Shows remote branch was deleted, which is expected after --delete-branch merge)

**Step 2: List local branches**

```bash
git branch -vv
```

**Expected Output:**

```
* main                         def5678 [origin/main] docs(ops): add docs-only deliverable fastpath runbook
  docs-ops-runbook-fastpath   abc1234 [origin/docs-ops-runbook-fastpath: gone] docs(ops): add docs-only deliverable fastpath runbook
```

**Note:** Feature branch shows [gone] because remote was deleted.

**Step 3: Delete local merged branch (optional)**

```bash
git branch -d docs-ops-runbook-fastpath
```

**Expected Output:**

```
Deleted branch docs-ops-runbook-fastpath (was abc1234).
```

**If refused (unmerged warning):**

The squash merge means local commits aren't technically "merged" in git's view. Force delete:

```bash
git branch -D docs-ops-runbook-fastpath
```

**Expected Output:**

```
Deleted branch docs-ops-runbook-fastpath (was abc1234).
```

**Step 4: Verify final state**

```bash
git branch -vv
```

**Expected Output:**

```
* main  def5678 [origin/main] docs(ops): add docs-only deliverable fastpath runbook
```

(Only main branch remains)

### Branch Recreation Guidance (if needed)

If you ever need to recreate a branch from a squashed/deleted branch:

**Find the commit hash from reflog:**

```bash
git reflog | grep "docs-ops-runbook-fastpath"
```

**Expected Output:**

```
abc1234 HEAD@{5}: commit: docs(ops): add docs-only deliverable fastpath runbook
```

**Recreate branch:**

```bash
git switch -c docs-ops-runbook-fastpath-v2 abc1234
```

This creates a new branch from the old commit. Useful for salvage scenarios.

### Checklist Phase 9

- [ ] git fetch --prune executed (stale refs removed)
- [ ] git branch -vv shows feature branch as [gone] (expected)
- [ ] Local feature branch deleted (git branch -d or -D)
- [ ] git branch -vv shows only main (or other long-lived branches)
- [ ] Repository is clean and ready for next task

---

## Operator Outcome Checklist

Use this checklist to verify successful completion of the fast path workflow:

- [ ] **Preconditions met:** Deliverable was complete, working tree had only intended changes
- [ ] **Pre-flight passed:** Terminal normal, repo verified, on feature branch
- [ ] **Staging clean:** Only docs files staged, no unintended code/config files
- [ ] **Local gates passed:** Token-Policy, Reference-Targets, Diff-Guard all green
- [ ] **Commit successful:** Clean commit with policy-compliant message
- [ ] **Push successful:** Branch pushed to origin, tracking set up
- [ ] **PR created:** PR opened with clear title/body, docs-only scope stated
- [ ] **CI checks passed:** All required checks green (docs-gates, lint, etc.)
- [ ] **Merge successful:** PR merged via squash, branch deleted on remote
- [ ] **Post-merge verify passed:** Changes visible on main, file exists, clean tree
- [ ] **Cleanup done:** Local feature branch deleted, repo ready for next task
- [ ] **No watch loops used:** All checks done via snapshot commands (no infinite waits)

**If all checked:** Workflow complete. Deliverable successfully merged to main.

**If any unchecked:** Review relevant phase, resolve issue, then continue.

---

## Risk Statement

**Overall Risk Level: LOW**

**Rationale:**
- Docs-only changes (no code, config, or infrastructure modifications)
- Additive workflow (minimal risk of breaking existing functionality)
- Multiple verification gates (local snapshot before push, CI checks before merge)
- Post-merge verification confirms successful landing
- Squash merge keeps commit history clean
- Branch auto-deletion prevents stale branch accumulation

**Residual Risks:**
- Typos or broken links in docs (LOW impact, easy to fix-forward)
- CI infrastructure failures (LOW likelihood, mitigated by manual checks)
- Merge conflicts if main changes rapidly (LOW likelihood for docs-only, mitigated by fast path approach)

**Mitigation:**
- Follow all phases in order
- Don't skip local gates
- Use snapshot commands (no watch loops) to maintain control
- Stop at any red flag, investigate before proceeding
- Leverage reflog for recovery if needed

---

## Recovery Notes

### Reflog Recovery Primer

If you lose commits (e.g. accidental reset, branch deletion before merge), use git reflog:

**View reflog:**

```bash
git reflog
```

**Expected Output:**

```
def5678 (HEAD -> main, origin/main) HEAD@{0}: pull --ff-only: Fast-forward
abc1234 HEAD@{1}: commit: docs(ops): add docs-only deliverable fastpath runbook
xyz9876 HEAD@{2}: switch: moving from docs-ops-runbook-fastpath to main
...
```

**Find lost commit hash (e.g. abc1234), then recover:**

**Option 1: Cherry-pick onto current branch**

```bash
git cherry-pick abc1234
```

**Option 2: Reset to lost commit (destructive, use with caution)**

```bash
git reset --hard abc1234
```

**Option 3: Create new branch from lost commit**

```bash
git switch -c recovered-branch abc1234
```

**Reflog retention:** Git keeps reflog entries for 30-90 days (default), so you have time to recover.

### Branch Recreation Snippet

If you need to recreate a deleted feature branch:

**Step 1: Find commit in reflog**

```bash
git reflog | grep "feature-branch-name"
```

**Step 2: Note commit hash (e.g. abc1234)**

**Step 3: Create new branch from that commit**

```bash
git switch -c feature-branch-name-v2 abc1234
```

**Step 4: Verify branch content**

```bash
git log -1 --stat
```

**You now have a new branch with the old commit's content.**

### Force-Push Recovery (if you force-pushed accidentally)

**If you force-pushed and lost commits:**

**Step 1: Check reflog for pre-force-push state**

```bash
git reflog
```

**Step 2: Find commit before force-push (e.g. xyz9876)**

**Step 3: Reset to that commit**

```bash
git reset --hard xyz9876
```

**Step 4: Force-push again (with caution) to restore remote**

```bash
git push --force-with-lease
```

**Note:** Force-push should be rare. If needed, coordinate with team to avoid conflicts.

---

## Revision History

| Version | Date       | Author        | Changes                              |
|---------|------------|---------------|--------------------------------------|
| 1.0     | 2026-01-14 | Cursor Agent  | Initial version (fast path workflow) |

---

**END OF RUNBOOK**
