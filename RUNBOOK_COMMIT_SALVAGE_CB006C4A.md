# Runbook: Commit Salvage cb006c4a → Feature Branch Workflow

**Objective:** Salvage local commit cb006c4a from main → feature branch, reset main, push branch, create PR, run CI snapshot, merge plan.

**Constraints:**
- ✅ No content deletion
- ✅ Docs gates must remain green
- ✅ No watch loops (snapshots only)
- ✅ Repo-conform workflow (feature branch → PR → CI → merge)

**Known State:**
- Local branch: `main` (tracking `origin&#47;main`)
- Local commit: `cb006c4a` ("docs(ops): Phase 9C closeout graph + ops README update")
- Files changed:
  - `docs/ops/README.md` (modified)
  - `docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md` (new)
- Commit stats: 2 files changed, 437 insertions(+)

---

## Roles & Responsibilities

### ORCHESTRATOR
- **Decision:** Sequence validation → salvage → reset → push → PR → CI → merge
- **Guardrails:** Each phase has explicit acceptance criteria; no parallel mutations on main

### IMPLEMENTER
- **Craft:** Terminal commands for each phase
- **Output:** PR body skeleton, merge log pointers

### CI_GUARDIAN
- **Checks:** Snapshot commands only (no `--watch`), expected CI contexts
- **Validation:** CI snapshot output review, gate status verification

### DOCS_GUARDIAN
- **Risk Scan:** Token policy violations, reference targets, illustrative path encoding
- **Gate Items:** `docs-token-policy-gate`, `docs-reference-targets-gate`, `docs-diff-guard-policy-gate`

### SCRIBE
- **Artifacts:** PR body template, merge log skeleton (if merge succeeds)

---

## Phase 0: State Validation & Truth Capture

**Purpose:** Verify current state matches known state, capture commit details for PR body.

### Commands

```bash
# Verify we're on main
git branch --show-current

# Verify commit exists locally
git log --oneline -1 cb006c4a

# Verify commit is on main (not pushed to origin/main yet)
git log origin/main..main --oneline

# Capture commit details for PR body
git show --stat cb006c4a > /tmp/salvage_commit_details.txt
git show --format=fuller cb006c4a | head -20 >> /tmp/salvage_commit_details.txt

# Verify no uncommitted changes
git status --short

# Verify docs gates would pass (dry-run)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

### Acceptance Criteria

- ✅ Current branch is `main`
- ✅ Commit `cb006c4a` exists and is ahead of `origin&#47;main`
- ✅ No uncommitted changes in working tree
- ✅ Docs gates snapshot shows GREEN or provides actionable fixes
- ✅ Commit details captured in `/tmp/salvage_commit_details.txt`

### Expected Output

```
main
cb006c4a docs(ops): Phase 9C closeout graph + ops README update
cb006c4a docs(ops): Phase 9C closeout graph + ops README update
(empty git status)
[docs gates output - all PASS or with fixable violations]
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| Not on main | `git checkout main` |
| Working tree dirty | Stash or commit changes first |
| Commit not found | Verify commit SHA, check `git reflog` |
| Docs gates FAIL | Fix violations before proceeding (see gate output) |

---

## Phase 1: Feature Branch Creation & Commit Salvage

**Purpose:** Create feature branch pointing to cb006c4a, preserving commit history.

### Commands

```bash
# Create feature branch FROM current HEAD (which is cb006c4a on main)
git checkout -b docs/phase9c-closeout-graph

# Verify branch points to correct commit
git log --oneline -1

# Verify branch tracks nothing yet (will set upstream on push)
git branch -vv | grep phase9c-closeout-graph
```

### Acceptance Criteria

- ✅ New branch `docs&#47;phase9c-closeout-graph` created
- ✅ Branch HEAD is `cb006c4a`
- ✅ Branch does not track remote yet
- ✅ Commit history intact (437 insertions, 2 files changed)

### Expected Output

```
Switched to a new branch 'docs/phase9c-closeout-graph'
cb006c4a docs(ops): Phase 9C closeout graph + ops README update
* docs/phase9c-closeout-graph cb006c4a docs(ops): Phase 9C closeout graph + ops README update
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| Branch already exists | Delete old branch: `git branch -D docs/phase9c-closeout-graph` |
| Wrong commit | `git reset --hard cb006c4a` |

---

## Phase 2: Reset Local Main to Origin/Main

**Purpose:** Reset local main to match origin/main (undo the local commit on main).

### Commands

```bash
# Switch back to main
git checkout main

# Verify we're ahead of origin/main by 1 commit
git log origin/main..main --oneline | wc -l

# Hard reset main to origin/main (DESTRUCTIVE: commit cb006c4a removed from main)
git reset --hard origin/main

# Verify main is now identical to origin/main
git log origin/main..main --oneline

# Verify feature branch still has the commit
git log docs/phase9c-closeout-graph --oneline -1
```

### Acceptance Criteria

- ✅ Local `main` reset to `origin&#47;main`
- ✅ No commits ahead of `origin&#47;main` on main
- ✅ Feature branch `docs&#47;phase9c-closeout-graph` still points to `cb006c4a`
- ✅ Working tree clean

### Expected Output

```
Switched to branch 'main'
1
HEAD is now at <origin_main_sha> <origin_main_commit_message>
(empty output - no commits ahead)
cb006c4a docs(ops): Phase 9C closeout graph + ops README update
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| Commit count != 1 | Verify state before reset, use `git log --graph` |
| Reset fails | Check for uncommitted changes, stash first |
| Feature branch lost | Recreate from reflog: `git branch docs/phase9c-closeout-graph cb006c4a` |

### ⚠️ Safety Note

**This step is DESTRUCTIVE for main branch.** Commit cb006c4a is only preserved on feature branch. Verify Phase 1 completed successfully before running `git reset --hard`.

---

## Phase 3: Push Feature Branch to Origin

**Purpose:** Push feature branch to remote, establishing tracking relationship.

### Commands

```bash
# Switch to feature branch
git checkout docs/phase9c-closeout-graph

# Push branch and set upstream
git push -u origin docs/phase9c-closeout-graph

# Verify push succeeded
git branch -vv | grep phase9c-closeout-graph

# Verify remote branch exists
gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'
gh api repos/rauterfrank-ui/Peak_Trade/branches/docs/phase9c-closeout-graph --jq '.name'
```

### Acceptance Criteria

- ✅ Branch pushed to `origin&#47;docs&#47;phase9c-closeout-graph`
- ✅ Local branch tracks remote branch
- ✅ Remote branch visible in GitHub UI
- ✅ Commit `cb006c4a` is the HEAD of remote branch

### Expected Output

```
Switched to branch 'docs/phase9c-closeout-graph'
Enumerating objects: X, done.
To github.com:rauterfrank-ui/Peak_Trade.git
 * [new branch]      docs/phase9c-closeout-graph -> docs/phase9c-closeout-graph
branch 'docs/phase9c-closeout-graph' set up to track 'origin/docs/phase9c-closeout-graph'.
* docs/phase9c-closeout-graph cb006c4a [origin/docs/phase9c-closeout-graph] docs(ops): Phase 9C closeout graph + ops README update
main
docs/phase9c-closeout-graph
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| Push rejected | Check remote state: `git fetch origin`, resolve conflicts if any |
| Branch exists remotely | Delete remote branch: `gh api -X DELETE repos/rauterfrank-ui/Peak_Trade/git/refs/heads/docs/phase9c-closeout-graph` |
| Auth failure | `gh auth refresh` |

---

## Phase 4: Create PR with Clean Body

**Purpose:** Open PR against main with structured PR body following Peak_Trade conventions.

### Commands

```bash
# Verify we're on feature branch
git branch --show-current

# Create PR body file
cat > /tmp/pr_body_phase9c.md <<'EOF'
## Summary

Phase 9C Closeout documentation:
- Adds comprehensive closeout graph for Docs Reference Remediation Waves 3–5
- Updates ops README with Phase 9C session reference
- Documents broken target reduction: 114 → 39 (−65.8%, goal achieved)

## Changes

**New:**
- `docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md` — Mermaid graph + wave metrics + evidence pointers

**Modified:**
- `docs/ops/README.md` — Added Phase 9C closeout link in session closeouts section (line 15)

## Why

Completes Phase 9C documentation cycle:
1. Waves 3–5 executed (PRs #712, #714, #716)
2. Each wave reduced broken targets incrementally
3. Final outcome: 114 → 39 broken targets (goal: <50 ✅)
4. Closeout graph provides visual timeline + operator quick reference

## Verification

```bash
# Docs gates (expected: PASS)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Verify new file structure
cat docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md | head -20

# Verify README link
grep -n "Phase 9C Closeout" docs/ops/README.md
```

## Risk

**LOW (docs-only)**
- No code changes
- No config changes
- Docs gates: token-policy ✅, reference-targets ✅, diff-guard ✅

## Related

- PR #716 (Wave 5: 58→39 broken targets, final wave)
- PR #714 (Wave 4: 87→65 broken targets)
- PR #712 (Wave 3: 114→89 broken targets)
- Phase 9C Goal: <50 broken targets ✅

## How to Review

1. Check closeout graph renders correctly (Mermaid syntax)
2. Verify README link points to correct file
3. Run docs gates snapshot (should pass)
4. Optional: Compare wave metrics against PR merge logs

EOF

# Create PR
gh pr create \
  --title "docs(ops): Phase 9C closeout graph + ops README integration" \
  --body-file /tmp/pr_body_phase9c.md \
  --base main \
  --head docs/phase9c-closeout-graph \
  --label documentation

# Capture PR number
PR_NUMBER=$(gh pr list --head docs/phase9c-closeout-graph --json number --jq '.[0].number')
echo "PR #${PR_NUMBER} created"

# Verify PR created
gh pr view ${PR_NUMBER} --json number,title,state,baseRefName,headRefName
```

### Acceptance Criteria

- ✅ PR created successfully
- ✅ PR title follows conventional commit format
- ✅ PR body contains all required sections (Summary, Changes, Why, Verification, Risk, Related, How to Review)
- ✅ PR base is `main`, head is `docs&#47;phase9c-closeout-graph`
- ✅ Label `documentation` applied
- ✅ PR number captured for Phase 5

### Expected Output

```
docs/phase9c-closeout-graph
Creating pull request for docs/phase9c-closeout-graph into main in rauterfrank-ui/Peak_Trade

https://github.com/rauterfrank-ui/Peak_Trade/pull/XXX
PR #XXX created
{
  "number": XXX,
  "title": "docs(ops): Phase 9C closeout graph + ops README integration",
  "state": "OPEN",
  "baseRefName": "main",
  "headRefName": "docs/phase9c-closeout-graph"
}
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| PR already exists | Update existing PR: `gh pr edit <NUM>` |
| Title too long | Shorten to <72 chars |
| Body validation fails | Check body file, ensure UTF-8 encoding |

---

## Phase 5: CI Snapshot (No Watch Loops)

**Purpose:** Trigger CI checks, capture snapshot of results (no blocking wait).

### Commands

```bash
# Wait for CI to start (GitHub Actions initialization delay)
sleep 10

# Snapshot 1: Initial CI state
gh pr checks ${PR_NUMBER} --interval 0 > /tmp/ci_snapshot_initial.txt
cat /tmp/ci_snapshot_initial.txt

# Wait for first round of checks (typical: 30-60s for docs-only PRs)
echo "Waiting 60s for CI checks to materialize..."
sleep 60

# Snapshot 2: After initialization
gh pr checks ${PR_NUMBER} --interval 0 > /tmp/ci_snapshot_60s.txt
cat /tmp/ci_snapshot_60s.txt

# Check specific docs gates (if available via API)
gh api repos/rauterfrank-ui/Peak_Trade/commits/$(git rev-parse docs/phase9c-closeout-graph)/check-runs \
  --jq '.check_runs[] | select(.name | contains("docs")) | {name: .name, status: .status, conclusion: .conclusion}' \
  > /tmp/ci_docs_gates_snapshot.json
cat /tmp/ci_docs_gates_snapshot.json

# Snapshot 3: Full PR view (includes mergeable status)
gh pr view ${PR_NUMBER} --json \
  number,title,state,mergeable,statusCheckRollup \
  > /tmp/pr_full_snapshot.json
cat /tmp/pr_full_snapshot.json | jq .

# Generate CI report
cat > /tmp/ci_snapshot_report.md <<EOF
# CI Snapshot Report: PR #${PR_NUMBER}

**Timestamp:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Branch:** docs/phase9c-closeout-graph
**Commit:** cb006c4a

## Initial State (T+10s)
\`\`\`
$(cat /tmp/ci_snapshot_initial.txt)
\`\`\`

## After Initialization (T+60s)
\`\`\`
$(cat /tmp/ci_snapshot_60s.txt)
\`\`\`

## Docs Gates Detail
\`\`\`json
$(cat /tmp/ci_docs_gates_snapshot.json)
\`\`\`

## Full PR State
\`\`\`json
$(cat /tmp/pr_full_snapshot.json)
\`\`\`

## Next Actions

- If all checks GREEN → proceed to Phase 6 (merge plan)
- If any checks RED/YELLOW → triage via snapshots, fix if needed
- If mergeable: UNKNOWN → wait for check materialization (typical: 2-5 min for docs PRs)

EOF

cat /tmp/ci_snapshot_report.md
```

### Acceptance Criteria

- ✅ At least 1 CI check visible in snapshot (not all "pending")
- ✅ Docs gates triggered (token-policy, reference-targets, diff-guard)
- ✅ No watch loops used (all snapshots via `--interval 0`)
- ✅ CI report generated in `/tmp/ci_snapshot_report.md`
- ✅ Mergeable status captured (may be UNKNOWN initially, expected)

### Expected Output (Snapshot)

```
# Expected docs gates in check-runs:
- "CI / Docs Token Policy Gate / docs-token-policy-gate" → status: completed, conclusion: success
- "CI / Docs Reference Targets Gate / docs-reference-targets-gate" → status: completed, conclusion: success
- "CI / Docs Diff Guard Policy Gate / docs-diff-guard-policy-gate" → status: completed, conclusion: success
- "CI Required Contexts Contract (matrix required checks)" → status: completed, conclusion: success

# Mergeable status:
- Initially: UNKNOWN (checks not materialized yet)
- After 2-5 min: MERGEABLE (if all required checks pass)
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| No checks visible after 60s | Check workflow triggers: `gh api repos/rauterfrank-ui/Peak_Trade/actions/runs?branch=docs/phase9c-closeout-graph` |
| Docs gate fails | Review snapshot, fix violations, push fix |
| Mergeable stays UNKNOWN | Wait up to 5 min, check required checks config |

### CI_GUARDIAN Notes

**Expected CI Contexts (docs-only PR):**
1. `docs-token-policy-gate` — Validates `&#47;` encoding for illustrative paths
2. `docs-reference-targets-gate` — Validates referenced paths exist
3. `docs-diff-guard-policy-gate` — No mass deletions (threshold: 200 lines/file)
4. `dispatch-guard` (always-run) — Validates workflow_dispatch contexts
5. `CI Required Contexts Contract` — Meta-check for required checks presence

**Snapshot-Only Strategy:**
- No `--watch` flags
- No blocking waits beyond initial materialization (60s)
- Capture state at T+10s, T+60s, then manual review
- Operator decides when to proceed to Phase 6 based on snapshot data

---

## Phase 6: Merge Plan & Cleanup

**Purpose:** Define merge strategy, execute merge (if CI green), cleanup branches.

### Commands

#### 6.1: Pre-Merge Validation

```bash
# Verify PR is mergeable (snapshot from Phase 5)
gh pr view ${PR_NUMBER} --json mergeable,statusCheckRollup | jq .

# Check for conflicts
gh pr view ${PR_NUMBER} --json mergeable | jq -r '.mergeable'

# Review approval status (if required reviews configured)
gh pr view ${PR_NUMBER} --json reviewDecision | jq -r '.reviewDecision'

# Final docs gates check (local, belt-and-suspenders)
git checkout docs/phase9c-closeout-graph
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
```

#### 6.2: Merge Execution (Auto-Merge Preferred)

```bash
# Option A: Enable auto-merge (preferred for docs-only PRs)
gh pr merge ${PR_NUMBER} --auto --squash --delete-branch

# Option B: Manual merge (if auto-merge not available or operator prefers)
# gh pr merge ${PR_NUMBER} --squash --delete-branch

# Capture merge result
MERGE_STATUS=$?
if [ $MERGE_STATUS -eq 0 ]; then
  echo "✅ PR #${PR_NUMBER} merge initiated"
else
  echo "❌ Merge failed with exit code $MERGE_STATUS"
  exit 1
fi

# Wait for auto-merge to complete (if enabled)
if gh pr view ${PR_NUMBER} --json autoMergeRequest | jq -e '.autoMergeRequest' > /dev/null; then
  echo "Auto-merge enabled, waiting for checks..."
  sleep 10
  gh pr view ${PR_NUMBER} --json state,mergedAt
fi
```

#### 6.3: Post-Merge Verification

```bash
# Update local main
git checkout main
git pull --ff-only origin main

# Verify commit is now in main
git log --oneline -5 | grep -i "phase 9c closeout"

# Verify files are present
ls -lh docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
grep -n "Phase 9C Closeout" docs/ops/README.md

# Verify remote branch deleted (if --delete-branch used)
gh api repos/rauterfrank-ui/Peak_Trade/branches/docs/phase9c-closeout-graph 2>&1 | grep -q "Not Found"
DELETE_CHECK=$?
if [ $DELETE_CHECK -eq 0 ]; then
  echo "✅ Remote branch deleted"
else
  echo "⚠️  Remote branch still exists (manual cleanup needed)"
fi
```

#### 6.4: Local Cleanup

```bash
# Delete local feature branch (if remote deleted)
git branch -d docs/phase9c-closeout-graph

# Verify cleanup
git branch -a | grep phase9c-closeout-graph
BRANCH_CHECK=$?
if [ $BRANCH_CHECK -ne 0 ]; then
  echo "✅ Local branch cleaned up"
else
  echo "⚠️  Local branch still exists"
fi

# Optional: Create merge log entry
cat > /tmp/merge_log_stub.md <<EOF
# PR #${PR_NUMBER} Merge Log Stub

**Title:** docs(ops): Phase 9C closeout graph + ops README integration
**Merged:** $(date -u +"%Y-%m-%d")
**Branch:** docs/phase9c-closeout-graph → main
**Commit:** cb006c4a

## Summary
Phase 9C closeout graph + ops README update successfully salvaged from main into feature branch workflow.

## Salvage Workflow
1. Commit created locally on main (oops)
2. Salvaged to feature branch: docs/phase9c-closeout-graph
3. Main reset to origin/main
4. Feature branch pushed, PR created
5. CI checks passed (docs gates green)
6. Auto-merge executed, branch deleted

## Files Changed
- docs/ops/README.md (437 insertions)
- docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md (new)

## Verification
\`\`\`bash
ls -lh docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
grep "Phase 9C Closeout" docs/ops/README.md
\`\`\`

## Related
- PR #712 (Wave 3)
- PR #714 (Wave 4)
- PR #716 (Wave 5)

EOF

echo "Merge log stub created at /tmp/merge_log_stub.md"
cat /tmp/merge_log_stub.md
```

### Acceptance Criteria

#### Pre-Merge
- ✅ PR mergeable status is `MERGEABLE`
- ✅ All required checks passed (green in CI snapshot)
- ✅ No merge conflicts
- ✅ Docs gates pass locally (belt-and-suspenders check)

#### Post-Merge
- ✅ PR state is `MERGED`
- ✅ Commit appears in `main` branch history
- ✅ Files present in `main` worktree
- ✅ Remote feature branch deleted
- ✅ Local feature branch deleted (or flagged for manual cleanup)
- ✅ Merge log stub created (optional, for audit trail)

### Expected Output

```
# Pre-Merge
{
  "mergeable": "MERGEABLE",
  "statusCheckRollup": [...]
}
MERGEABLE
APPROVED (or null if no reviews required)
[docs gates output - all PASS]

# Merge
✅ PR #XXX merge initiated
Auto-merge enabled, waiting for checks...
{
  "state": "MERGED",
  "mergedAt": "2026-01-14T..."
}

# Post-Merge
From github.com:rauterfrank-ui/Peak_Trade
 * branch            main       -> FETCH_HEAD
Already up to date.
cb006c4a docs(ops): Phase 9C closeout graph + ops README integration
-rw-r--r--  1 user  staff  12345 Jan 14 10:00 docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
15:- **[Phase 9C Closeout](graphs/PHASE9C_CLOSEOUT_2026-01-14.md)** — Docs Graph Remediation Waves 3–5 (114→39 broken targets, −65.8%, goal achieved)
✅ Remote branch deleted
Deleted branch docs/phase9c-closeout-graph (was cb006c4a).
✅ Local branch cleaned up
```

### Failure Modes

| Condition | Action |
|-----------|--------|
| Mergeable: CONFLICTING | Rebase feature branch on main, resolve conflicts, force-push |
| Mergeable: UNKNOWN | Wait for checks to materialize (up to 5 min), re-check |
| Required check failed | Triage failed check, push fix to feature branch, re-snapshot CI |
| Auto-merge fails | Manual merge via Web UI or `gh pr merge` without `--auto` |
| Branch deletion fails | Manual cleanup: `git push origin --delete docs/phase9c-closeout-graph` |

---

## ORCHESTRATOR Decision Log

### Go/No-Go Checkpoints

| Phase | Go Condition | No-Go Action |
|-------|-------------|--------------|
| 0 → 1 | Commit exists, docs gates pass | Fix violations first |
| 1 → 2 | Feature branch created with correct commit | Abort, review commit SHA |
| 2 → 3 | Main reset successfully | Do NOT proceed if feature branch missing |
| 3 → 4 | Feature branch pushed to origin | Check network/auth, retry |
| 4 → 5 | PR created | Cannot proceed without PR number |
| 5 → 6 | CI snapshot shows green/yellow (no red blockers) | Triage failures, push fixes |
| 6 → Cleanup | PR merged successfully | Manual cleanup if auto-merge failed |

### Risk Mitigation

1. **Commit Loss Risk:** Feature branch created in Phase 1 BEFORE main reset in Phase 2
2. **Docs Gate Risk:** Pre-flight check in Phase 0, belt-and-suspenders check in Phase 6.1
3. **CI Timeout Risk:** Snapshot-only approach (no watch loops), operator-driven progression
4. **Merge Conflict Risk:** Docs-only PR, low conflict probability; rebase plan in Phase 6 failure modes
5. **Branch Leak Risk:** Auto-delete flags in merge command, post-merge verification in Phase 6.3

---

## DOCS_GUARDIAN Risk Scan

### Token Policy Items

**Scope:** `docs/ops/README.md` (modified), `docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md` (new)

**Scan Results (Expected):**
- No illustrative paths requiring `&#47;` encoding (docs-only references)
- Real repo targets: `docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md` (self-referential, exempt)
- Links to existing files: PRs #712, #714, #716 merge logs (validated in Phase 0)

**Gate Status:** ✅ PASS (expected)

### Reference Targets Items

**Scope:** All markdown links in changed files

**Scan Results (Expected):**
- `graphs&#47;PHASE9C_CLOSEOUT_2026-01-14.md` — Exists (created in commit cb006c4a)
- PR references (e.g., `PR_712_MERGE_LOG.md`) — Exist in `docs/ops/` (verified in Phase 0)
- Relative links — Resolved from `docs/ops/` directory

**Gate Status:** ✅ PASS (expected)

### Diff Guard Items

**Scope:** Deletion threshold check (default: 200 lines/file)

**Scan Results (Expected):**
- `docs/ops/README.md`: +1 line (new link), 0 deletions
- `docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md`: +436 lines (new file), 0 deletions
- Total: 437 insertions, 0 deletions

**Gate Status:** ✅ PASS (no mass deletions)

---

## SCRIBE Artifacts

### PR Body Template

See Phase 4 commands section (inline PR body generation).

### Merge Log Skeleton

```markdown
# PR #${PR_NUMBER} Merge Log

**Title:** docs(ops): Phase 9C closeout graph + ops README integration
**Merged:** [DATE]
**Author:** [OPERATOR]
**Reviewers:** [TBD or "auto-merge"]

## Summary
Phase 9C closeout documentation: graph + ops README update. Salvaged from accidental commit on main.

## Changes
- New: docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
- Modified: docs/ops/README.md (line 15, closeout link)

## Why
Completes Phase 9C evidence chain: Waves 3-5 executed, goal achieved (114→39 broken targets).

## Verification
```bash
# Docs gates
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main
# Output: all PASS

# File verification
ls -lh docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
grep "Phase 9C Closeout" docs/ops/README.md
```

## Risk
LOW (docs-only, no code/config changes).

## Related
- PR #712 (Wave 3: 114→89)
- PR #714 (Wave 4: 87→65)
- PR #716 (Wave 5: 58→39, final)

## Workflow Notes
Salvage workflow executed:
1. Feature branch created from commit cb006c4a
2. Main reset to origin/main
3. PR workflow followed (no shortcuts)

## How to Use
Reference this closeout when documenting Phase 9C outcomes or auditing wave progression.
```

---

## Timeline Estimate

| Phase | Duration | Notes |
|-------|----------|-------|
| 0 | 2-3 min | Fast (local checks only) |
| 1 | <1 min | Local branch creation |
| 2 | <1 min | Local reset (instant) |
| 3 | 1-2 min | Network push time |
| 4 | 2-3 min | PR body creation + API call |
| 5 | 2-5 min | CI initialization + snapshots (no blocking) |
| 6 | 3-10 min | Merge wait (if auto-merge) + verification |
| **Total** | **15-25 min** | Operator-driven, no watch loops |

---

## Recovery Scenarios

### Scenario 1: Feature Branch Lost After Phase 2

**Symptom:** Main reset, but feature branch missing or points to wrong commit.

**Recovery:**
```bash
# Find commit in reflog
git reflog | grep cb006c4a

# Recreate branch
git branch docs/phase9c-closeout-graph cb006c4a

# Verify
git log docs/phase9c-closeout-graph --oneline -1
```

### Scenario 2: CI Gate Fails After PR Created

**Symptom:** Docs gate shows violations in Phase 5 snapshot.

**Recovery:**
```bash
# Checkout feature branch
git checkout docs/phase9c-closeout-graph

# Fix violations (example: token policy)
# Edit files, encode illustrative paths with &#47;

# Commit fix
git add docs/ops/README.md docs/ops/graphs/PHASE9C_CLOSEOUT_2026-01-14.md
git commit -m "fix: docs gate violations (token policy encoding)"

# Push fix
git push origin docs/phase9c-closeout-graph

# Re-snapshot CI (repeat Phase 5)
sleep 60
gh pr checks ${PR_NUMBER} --interval 0
```

### Scenario 3: Merge Fails (Conflict or Check Failure)

**Symptom:** Phase 6 merge command fails.

**Recovery:**
```bash
# Check conflict status
gh pr view ${PR_NUMBER} --json mergeable

# If CONFLICTING:
git checkout docs/phase9c-closeout-graph
git fetch origin main
git rebase origin/main
# Resolve conflicts
git rebase --continue
git push --force-with-lease origin docs/phase9c-closeout-graph

# If check failure:
# Review failed check in CI snapshot
# Push fix, re-run Phase 5 and 6.1
```

### Scenario 4: Auto-Merge Stuck

**Symptom:** Auto-merge enabled but PR not merging after 10+ min.

**Recovery:**
```bash
# Check PR state
gh pr view ${PR_NUMBER} --json state,mergeable,autoMergeRequest

# Disable auto-merge
gh pr merge ${PR_NUMBER} --disable-auto

# Manual merge via Web UI (if checks green)
# OR: gh pr merge ${PR_NUMBER} --squash --delete-branch
```

---

## Exit Criteria (Full Runbook)

✅ **Success Conditions:**
1. Commit cb006c4a salvaged to feature branch
2. Local main reset to origin/main
3. Feature branch pushed to origin
4. PR created with structured body
5. CI snapshot captured (docs gates green)
6. PR merged (auto or manual)
7. Branches cleaned up (local + remote)
8. Files visible in main branch

❌ **Abort Conditions:**
1. Commit cb006c4a not found or corrupted
2. Docs gates fail in Phase 0 (fix first)
3. Feature branch creation fails (disk/permission issue)
4. Push fails (network/auth issue, no retry after 3 attempts)
5. PR creation fails (API error, manual fallback required)
6. CI snapshot shows critical gate failures (red, not fixable in PR)
7. Merge blocked by required reviews (escalate to admin/reviewer)

---

## Appendix A: Quick Command Cheat Sheet

```bash
# Phase 0: Validate
git log origin/main..main --oneline
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Phase 1: Salvage
git checkout -b docs/phase9c-closeout-graph

# Phase 2: Reset
git checkout main
git reset --hard origin/main

# Phase 3: Push
git checkout docs/phase9c-closeout-graph
git push -u origin docs/phase9c-closeout-graph

# Phase 4: PR
gh pr create --title "docs(ops): Phase 9C closeout graph + ops README integration" --body-file /tmp/pr_body_phase9c.md --base main --head docs/phase9c-closeout-graph --label documentation
PR_NUMBER=$(gh pr list --head docs/phase9c-closeout-graph --json number --jq '.[0].number')

# Phase 5: CI Snapshot
sleep 60
gh pr checks ${PR_NUMBER} --interval 0

# Phase 6: Merge
gh pr merge ${PR_NUMBER} --auto --squash --delete-branch
git checkout main
git pull --ff-only origin main
git branch -d docs/phase9c-closeout-graph
```

---

## Appendix B: Docs Gates Quick Reference

### Token Policy Gate
- **Purpose:** Enforce `&#47;` encoding for illustrative paths
- **Trigger:** Any `*.md` file changes
- **Fix:** Replace `/` with `&#47;` in inline-code tokens (e.g., `docs&#47;ops&#47;example.md` shown as example)

### Reference Targets Gate
- **Purpose:** Validate referenced repo paths exist
- **Trigger:** Any `*.md` file changes
- **Fix:** Ensure linked files exist, fix typos, or use `&#47;` encoding for illustrative paths

### Diff Guard Policy Gate
- **Purpose:** Prevent mass deletions (>200 lines/file under `docs/`)
- **Trigger:** Any `docs&#47;**` file changes
- **Fix:** Review deletions, split into smaller PRs if intentional, or revert accidental deletions

---

**END OF RUNBOOK**

**Operator Notes:**
- This runbook is self-contained and can be executed sequentially without external dependencies (except `gh` CLI and git).
- All commands are copy-paste-safe (no placeholders except `${PR_NUMBER}`, which is captured in Phase 4).
- CI snapshots use `--interval 0` to avoid watch loops (cursor-safe).
- Auto-merge preferred for docs-only PRs to reduce manual wait time.
- Recovery scenarios cover common failure modes; escalate to senior operator if novel failure encountered.

**Version:** 1.0.0
**Last Updated:** 2026-01-14
**Maintainer:** Peak_Trade Ops
