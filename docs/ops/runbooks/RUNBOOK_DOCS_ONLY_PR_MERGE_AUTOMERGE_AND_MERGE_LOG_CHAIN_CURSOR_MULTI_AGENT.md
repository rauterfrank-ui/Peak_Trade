# RUNBOOK — Docs-Only PR Merge (Auto-Merge/Squash) + CI Snapshot + Merge-Log Chain

**Status:** OPERATOR-READY  
**Owner:** ops / docs-integrity  
**Risk:** LOW-MEDIUM (merge operations; branch cleanup; protected main)  
**Last Updated:** 2026-01-14

---

## OPERATOR QUICKSTART

**Use Cases:**
- CI is green → merge PR (squash) → cleanup branch → post-merge verify
- CI not green → snapshot → fix-forward → re-check
- After merge → create merge-log as separate docs-only PR

**Golden Path (Fast Track):**
1. Pre-flight: pwd, git status, continuation guard
2. CI snapshot: gh pr checks (no watch)
3. Merge: auto-merge squash + delete branch
4. Post-merge verify: sync main, confirm merge commit
5. Branch cleanup: local + remote
6. Merge log chain: new branch, create log file, separate PR

**Stop Conditions:**
- Required checks missing or failed
- Working tree dirty without reason
- Protected main violation
- Shell in continuation mode (prompt shows `>` or `dquote>`)

---

## 1. Purpose & Scope

This runbook provides a standardized operator procedure for merging docs-only PRs with:
- Automated CI status snapshot (no watch loops)
- Auto-merge + squash + branch deletion (preferred path)
- Manual fallback if auto-merge unavailable
- Post-merge verification
- Local and remote branch cleanup
- Merge-log chain as separate PR

**In Scope:**
- Docs-only PRs where CI checks are green or fixable
- Squash-merge strategy (default for this repo)
- Protected main branch workflows

**Out of Scope:**
- Code PRs (may require different merge strategies)
- Emergency hotfixes (use dedicated runbook)
- Rebases or history rewrites

---

## 2. Preconditions / Assumptions

**Operator Prerequisites:**
- Local clone of Peak_Trade repository
- GitHub CLI (`gh`) installed and authenticated
- Write access to repository
- PR number available

**PR Prerequisites:**
- PR targets `main` branch
- PR is docs-only (no code changes)
- All required checks configured
- No merge conflicts

**System Prerequisites:**
- Protected main branch rules active
- Required checks defined (typically 10 checks for this repo)
- Auto-merge enabled for repository

---

## 3. Roles & Responsibilities

**Operator:**
- Execute pre-flight checks
- Capture CI status snapshot
- Initiate merge (auto or manual)
- Verify post-merge state
- Clean up branches
- Create merge-log PR

**Reviewer:**
- Approve PR before merge (if required by branch protection)
- Validate docs-only scope

**CI System:**
- Execute required checks
- Block merge if checks fail
- Report status via GitHub API

---

## 4. Inputs & Artifacts

**Required Inputs:**
- PR number (e.g., 731)
- PR branch name (e.g., docs/ops-runbook-post-merge-verify-snapshot)
- Target branch (typically `main`)

**Artifacts to Capture:**
- CI status snapshot (timestamp + check names + results)
- Merge commit SHA
- Pre-merge HEAD SHA
- Post-merge HEAD SHA
- Branch cleanup confirmation

**Optional Inputs:**
- Merge commit message (if customizing)
- Merge log template

---

## 5. Safety / Governance

**Protected Main:**
- Direct push to main is blocked
- All changes via PR only
- Required checks must pass

**Docs-Only Scope:**
- This runbook assumes docs-only changes
- Code changes may require additional review

**Required Checks:**
- Typically 10 checks for this repo
- Check names may vary by PR
- Path-filtered checks may show "neutral" (acceptable if not required)

**No-Watch Policy:**
- All CI snapshots are point-in-time
- No continuous polling or watch loops
- Manual refresh if status needs update

**Branch Protection:**
- Auto-merge respects all protection rules
- Manual merge only after all checks green

---

## 6. Procedure — Phase 0: Pre-Flight (Repo + Continuation Guard)

**Goal:** Confirm clean repo state and shell not in continuation mode.

**Step 6.1: Continuation Guard**

Check your terminal prompt. If you see any of these continuation indicators:
- `>` (general continuation)
- `dquote>` (double-quote continuation)
- `heredoc>` (heredoc continuation)

**Action:** Press Ctrl-C once to exit continuation mode, then verify prompt returns to normal.

**Step 6.2: Repo Check**

Run these commands to confirm you are in the correct repository:

```bash
pwd
git rev-parse --show-toplevel
git status -sb
```

**Expected Output:**
- Current directory is inside Peak_Trade repository
- `git rev-parse` shows repo root path
- `git status -sb` shows current branch and clean or expected working tree state

**Evidence to Capture:**
- Output of `git status -sb`
- Confirm no unexpected dirty state

**Stop Conditions:**
- Shell shows continuation prompt and Ctrl-C does not resolve it → escalate
- Working tree dirty with unexpected changes → investigate before proceeding
- Not in correct repository → navigate to correct location

---

## 7. Procedure — Phase 1: CI Checks Snapshot (GitHub UI + gh)

**Goal:** Capture point-in-time CI status without watch loops.

**Step 7.1: Snapshot via GitHub CLI**

Run this command to get current CI status:

```bash
gh pr checks <PR_NUMBER>
```

Replace `<PR_NUMBER>` with actual PR number (e.g., 731).

**Step 7.2: Interpret Results**

Check output for:
- All required checks present
- All required checks show "pass" or "success"
- Path-filtered checks may show "neutral" (acceptable if not in required set)

**Step 7.3: GitHub UI Snapshot (Alternative)**

If CLI not available:
1. Open PR page in browser
2. Scroll to "Checks" section at bottom
3. Note timestamp and status of all checks
4. Screenshot if needed for evidence

**Evidence to Capture:**
- Full output of `gh pr checks` command
- Timestamp of snapshot
- List of failed checks (if any)

**Decision Point:**

**If all required checks green:**
- Proceed to Phase 2 (Merge Execution)

**If any required check failed:**
- STOP: Do not merge
- Consult Section 12 (Failure Modes)
- Fix-forward or request changes

**If checks still running:**
- Wait for completion
- Re-run snapshot command
- Do NOT use watch mode; manual refresh only

---

## 8. Procedure — Phase 2: Merge Execution (Auto-Merge Squash)

**Goal:** Execute merge with squash strategy and branch deletion.

**Preferred Path: Auto-Merge via GitHub CLI**

**Step 8.1: Enable Auto-Merge**

```bash
gh pr merge <PR_NUMBER> --auto --squash --delete-branch
```

This command:
- Enables auto-merge on the PR
- Uses squash merge strategy
- Deletes branch after merge
- Waits for required checks (if not already green)

**Step 8.2: Monitor Merge Completion**

Auto-merge will complete automatically when:
- All required checks pass
- All required reviews approved

**To check if merge completed:**

```bash
gh pr view <PR_NUMBER>
```

Look for "State: MERGED" in output.

**Alternative Path: Manual Merge (if auto-merge not available)**

**Step 8.3: Manual Squash Merge**

Only if auto-merge is not enabled for repo or PR:

```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

This will merge immediately (checks must already be green).

**Step 8.4: Capture Merge Commit SHA**

After merge completes:

```bash
gh pr view <PR_NUMBER> --json mergeCommit --jq '.mergeCommit.oid'
```

**Evidence to Capture:**
- Merge commit SHA
- Merge completion timestamp
- Branch deletion confirmation

---

## 9. Procedure — Phase 3: Post-Merge Verify (main)

**Goal:** Confirm local main is synced with origin/main and merge commit is present.

**Step 9.1: Sync Local Main**

```bash
git fetch --prune
git switch main
git pull --ff-only
git status -sb
```

**Expected:**
- `main...origin&#47;main` shows no ahead/behind
- Working tree clean
- Fast-forward pull succeeded

**Step 9.2: Verify Merge Commit**

```bash
git log -1 --oneline
git show --stat HEAD
```

**Expected:**
- HEAD matches merge commit SHA from Phase 2
- Commit message matches PR title
- Changed files match PR scope

**Step 9.3: Optional Docs Gates Snapshot**

For comprehensive verification, refer to existing post-merge verify runbook:

See: [RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md](RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md)

This is optional; use if you need to verify docs gates on merged changes.

**Evidence to Capture:**
- `git status -sb` output
- `git log -1 --oneline` output
- Merge commit SHA verification (matches Phase 2)

---

## 10. Procedure — Phase 4: Branch Cleanup (local + remote)

**Goal:** Remove merged branch from local and remote (if not auto-deleted).

**Step 10.1: Verify Remote Branch Deleted**

Check if branch was auto-deleted during merge:

```bash
git fetch --prune
git branch -r | grep <BRANCH_NAME>
```

If no output, remote branch is deleted (expected if `--delete-branch` was used).

**Step 10.2: Delete Local Branch**

Switch to main if not already there:

```bash
git switch main
```

Delete local branch:

```bash
git branch -d <BRANCH_NAME>
```

If branch was not merged (error about unmerged changes):

```bash
git branch -D <BRANCH_NAME>
```

Use `-D` only if you are certain merge completed successfully.

**Step 10.3: Verify Cleanup**

List local branches:

```bash
git branch
```

Ensure merged branch is no longer listed.

**Evidence to Capture:**
- Confirmation that remote branch deleted
- Confirmation that local branch deleted
- Output of `git branch` showing clean state

---

## 11. Procedure — Phase 5: Merge Log Chain (separate PR)

**Goal:** Create merge-log documentation as separate docs-only PR.

**Step 11.1: Create Merge-Log Branch**

From clean main:

```bash
git switch main
git pull --ff-only
git switch -c merge-log/pr-<PR_NUMBER>-<SHORT_DESCRIPTION>
```

Example:

```bash
git switch -c merge-log/pr-731-post-merge-verify-runbook
```

**Step 11.2: Create Merge-Log File**

Create new file in merge-logs directory:

```bash
touch docs/ops/merge_logs/PR_<PR_NUMBER>_MERGE_LOG.md
```

**Step 11.3: Populate Merge-Log (Template)**

Open file and add content using this template:

```markdown
# PR #<PR_NUMBER> Merge Log

**Status:** MERGED  
**Merge Date:** YYYY-MM-DD (UTC)  
**Merge Commit:** <MERGE_SHA>  
**Branch:** <BRANCH_NAME>  
**Operator:** <YOUR_NAME>

---

## Summary
<Brief description of what was merged>

## Pre-Merge Checks
- CI Status: <all checks green / summary>
- Required Reviews: <approved / count>
- Docs Gates: <pass/fail if verified>

## Merge Execution
- Method: <auto-merge / manual squash>
- Merge Commit SHA: <MERGE_SHA>
- Branch Deleted: <yes/no>

## Post-Merge Verification
- Local main synced: <yes/no>
- Merge commit verified: <yes/no>
- Expected files present: <yes/no>

## Files Changed
- List of files from PR

## Notes
<Any anomalies, special considerations, or follow-up items>

---

**Evidence Capture:** <timestamp>  
**Runbook Used:** RUNBOOK_DOCS_ONLY_PR_MERGE_AUTOMERGE_AND_MERGE_LOG_CHAIN_CURSOR_MULTI_AGENT.md
```

**Step 11.4: Optional Index Update**

If merge-logs directory has a README or index, consider adding entry (optional).

**Step 11.5: Commit and Push**

```bash
git add docs/ops/merge_logs/PR_<PR_NUMBER>_MERGE_LOG.md
git commit -m "docs(ops): add merge log for PR #<PR_NUMBER>"
git push -u origin merge-log/pr-<PR_NUMBER>-<SHORT_DESCRIPTION>
```

**Step 11.6: Create PR for Merge Log**

```bash
gh pr create --base main \
  --head merge-log/pr-<PR_NUMBER>-<SHORT_DESCRIPTION> \
  --title "docs(ops): add merge log for PR #<PR_NUMBER>" \
  --body "Merge log documentation for PR #<PR_NUMBER>. Docs-only."
```

**Evidence to Capture:**
- Merge-log PR number
- Merge-log file path
- Commit SHA for merge-log

---

## 12. Failure Modes / Troubleshooting

**Issue: Required Checks Missing**

**Symptoms:**
- CI shows fewer checks than expected
- Required check not triggered

**Resolution:**
- Check if PR changes trigger path filters
- Verify required checks configuration
- If check legitimately not needed (path-filtered), proceed with available checks
- If check should run but did not, retrigger CI or investigate configuration

**Issue: Required Check Failed**

**Symptoms:**
- One or more required checks show red/failed

**Resolution:**
- Identify which check failed
- Review check logs (click check name in PR or use `gh pr checks <PR_NUMBER>`)
- Common failures:
  - Docs Token Policy: unescaped slashes in inline-code
  - Docs Reference Targets: broken links
  - Docs Diff Guard: renames or deletions in docs
- Fix-forward: make changes, push to same branch, checks re-run automatically
- Do NOT merge until all required checks green

**Issue: Auto-Merge Not Available**

**Symptoms:**
- `gh pr merge --auto` returns error about auto-merge not enabled

**Resolution:**
- Use manual merge: `gh pr merge <PR_NUMBER> --squash --delete-branch`
- Only proceed if all checks already green

**Issue: Merge Conflict**

**Symptoms:**
- PR shows "This branch has conflicts that must be resolved"

**Resolution:**
- Do NOT merge
- Resolve conflicts on PR branch
- Push resolution, wait for checks to re-run
- Return to Phase 1 (CI snapshot)

**Issue: Protected Main Violation**

**Symptoms:**
- Merge blocked with "Protected branch update failed"
- Required reviews not satisfied

**Resolution:**
- Ensure all required reviews obtained
- Wait for reviewers if needed
- Do NOT bypass protection rules

**Issue: Branch Not Auto-Deleted**

**Symptoms:**
- After merge, branch still exists on remote

**Resolution:**
- Manually delete remote branch:

```bash
git push origin --delete <BRANCH_NAME>
```

- Then clean up local branch as per Phase 4

**Issue: Local Main Diverged from origin/main**

**Symptoms:**
- `git status -sb` shows `main...origin&#47;main [ahead N]` or `[behind N]`

**Resolution:**
- If behind: `git pull --ff-only`
- If ahead with unexpected commits: investigate
- If you accidentally committed to main: use reflog to recover and move commits to feature branch

---

## 13. Verification Checklist

After completing all phases, verify:

- [ ] PR merged successfully (state: MERGED on GitHub)
- [ ] Merge commit SHA captured and verified
- [ ] Local main synced with origin/main (no ahead/behind)
- [ ] Merge commit present at HEAD on main
- [ ] PR branch deleted on remote
- [ ] PR branch deleted locally
- [ ] Working tree clean
- [ ] (Optional) Merge-log PR created
- [ ] (Optional) Docs gates snapshot verified (if required)

If all checks pass, merge operation complete.

---

## 14. References

**Related Runbooks:**
- [RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md](RUNBOOK_POST_MERGE_VERIFY_MAIN_AND_DOCS_GATES_SNAPSHOT_CURSOR_MULTI_AGENT.md) — Post-merge verification with docs gates snapshot
- [README.md](README.md) — Runbooks index

**Related Docs:**
- Protected branch rules (GitHub repository settings)
- Required checks configuration (GitHub Actions workflows)
- Squash merge strategy (GitHub merge options)

**Tools:**
- GitHub CLI (`gh`): https://cli.github.com/
- Git: https://git-scm.com/

---

**END OF RUNBOOK**
