# RUNBOOK: Docs Gates Fix-Forward CI Triage (Token Policy + Reference Targets) — Cursor Multi-Agent

**Scope:** docs-only PRs  
**Risk:** Low (typical), escalate on Stop Conditions  
**Audience:** Operator (Frank) + CI Guardian + Evidence Scribe  
**Version:** 1.0  
**Last Updated:** 2026-01-14

---

## Executive Summary

**Problem Class:**  
CI Gate Failures occur despite local PASS verdicts. Root causes include:
- **Base-Ref Drift:** Local `main` vs `origin&#47;main` not synchronized; changed-detection runs against stale references
- **Coverage Gaps:** New or staged files slip through local gate execution (e.g., `--changed` flag misses uncommitted or newly added files)
- **Meta-Compliance:** Runbook examples themselves must be gate-conformant (Token Policy: illustrative "/" paths, Reference Targets: no links to missing files)

**Solution:**  
Deterministic fix-forward workflow organized in phases: local snapshot → PR creation → CI snapshot → targeted remediation → re-check → auto-merge. No watch-loops, no git rewrites.

**Output:**  
Repeatable operator flow with evidence trail, minimizing iteration cycles and ensuring gate convergence.

---

## Terminology / Definitions

| Term | Definition |
|------|------------|
| **Local Snapshot** | Executing docs gates locally against the current working tree / branch state |
| **CI Snapshot** | GitHub Checks status captured at a specific commit SHA (one-time capture, no polling) |
| **Fix-Forward** | Additional commit on the same PR branch (no rebase, no force-push) to remediate gate failures |
| **Base Ref Drift** | Mismatch between local `main` and `origin&#47;main` causing incorrect changed-file detection |
| **Changed Detection Gap** | Scenario where `--changed` or diff commands miss files due to wrong comparison base or unstaged/uncommitted state |
| **Token Policy Violation** | Inline code (backticks) containing "/" in illustrative paths without proper encoding (`&#47;`) |
| **Reference Targets Violation** | Markdown links pointing to non-existent files or anchors |

---

## Phase 0 — Preconditions (Repo + Branch Hygiene)

**Goal:** Ensure local comparison base matches remote, preventing stale-ref issues.

### Snapshot Commands

Run these commands to verify repo state (no watch-loops):

```bash
git status -sb
git rev-parse --show-toplevel
git fetch --prune
git log -1 --oneline
```

### Decision Tree

**If `origin&#47;main` is ahead of local `main`:**

- **Option A (safe):** Reset local `main` to `origin&#47;main`:

```bash
git checkout main
git reset --hard origin/main
```

- **Option B (investigate):** If local `main` has unpushed commits, investigate before proceeding.

**If working branch is not up-to-date with `origin&#47;main`:**

- Consider rebasing or merging `origin&#47;main` into feature branch (only if required; otherwise defer to CI merge preview).

### Expected Outputs

- `git status -sb` shows feature branch ahead of `origin&#47;main` by N commits (no untracked/unstaged surprises)
- Local `main` exactly matches `origin&#47;main` commit SHA

### Stop Condition

- Unexpected dirty state (uncommitted changes not part of intended PR scope) → Triage separately before proceeding.

---

## Phase 1 — Local Gates: "Coverage-First" Snapshot

**Goal:** Run local gates in a way that ensures new, staged, or committed files are included in gate evaluation.

### Why Local PASS ≠ CI PASS

**Common Coverage Gaps:**

1. **New files not staged:** Gate runs against committed files only; new file exists but is untracked
2. **Staged but not committed:** `--changed` flag may compare against wrong base
3. **Wrong diff base:** Comparing against local `main` instead of `origin&#47;main`

### Execution Variants

#### Variant A: Pre-Commit (Staged Diff)

Use when changes are staged but not yet committed:

```bash
git diff --cached --name-only
```

Verify that new/modified docs files are listed. Then run gates:

```bash
make docs-gates
```

(or equivalent gate command that respects staged state)

#### Variant B: Post-Commit (Origin Diff)

Use after committing changes to feature branch:

```bash
git diff --name-only origin&#47;main...HEAD
```

Ensure output includes all new/modified files. Then run gates:

```bash
make docs-gates
```

### Coverage Check: Files Under Consideration

Capture the list of files the gate evaluated:

```bash
git diff --name-only origin&#47;main...HEAD > /tmp/gate_coverage.txt
cat /tmp/gate_coverage.txt
```

Store this as evidence (timestamp + file list).

### Expected Outputs

- **Gate Verdict:** PASS or FAIL
- **Files Evaluated:** List of changed docs files (non-empty if changes exist)
- **Timestamp:** Local execution time for audit trail

### Stop Condition

- If file list is empty but you know you added/modified files → Coverage gap detected; revisit Phase 0 or variant selection.

---

## Phase 2 — PR Creation / Auto-Merge Preparation

**Goal:** Create PR with clear scope and evidence from local snapshot; prepare for CI evaluation.

### Minimal PR Body Pattern

```markdown
**Scope:** docs-only

**Gates:** Local snapshot executed at YYYY-MM-DD HH:MM:SS UTC
- Token Policy: PASS
- Reference Targets: PASS
- Diff Guard: PASS

**Fix-Forward Policy:** Enabled (no rebase/force-push)

**Changed Files:**
- docs&#47;ops&#47;runbooks&#47;EXAMPLE.md

**Next:** Awaiting CI snapshot before enabling auto-merge.
```

### Decision: Auto-Merge Timing

**Recommended:** Enable auto-merge **after** first CI snapshot shows all required checks passing. This avoids premature merge if CI detects issues missed locally.

### Expected Outputs

- PR created with descriptive title (e.g., `docs(ops): add CI triage runbook`)
- PR body includes local snapshot evidence
- Branch protection requires all checks before merge

---

## Phase 3 — CI Snapshot (Without Watch)

**Goal:** Capture CI gate results at the current commit SHA, one-time check.

### Snapshot Commands

**Option A: GitHub CLI**

```bash
gh pr checks <PR_NUMBER>
```

**Option B: GitHub UI**

Navigate to PR → Checks tab → Capture screenshot or note status per check.

### Result Handling

| CI Result | Next Phase |
|-----------|------------|
| All checks PASS | → Phase 7 (Auto-Merge) |
| Token Policy FAIL | → Phase 4 (Token Policy Remediation) |
| Reference Targets FAIL | → Phase 5 (Reference Targets Remediation) |
| Diff Guard FAIL | → STOP (manual investigation required) |

### Expected Outputs

- Timestamped snapshot of check statuses
- Specific gate failure messages (if any)

### Stop Condition

- Diff Guard FAIL → Not additive; escalate for manual review before proceeding.

---

## Phase 4 — Token Policy Gate Failure: Triage + Remediation

**Goal:** Identify and fix Token Policy violations (illustrative "/" in inline code).

### Diagnosis

**Common Violation Patterns:**

1. **Illustrative Paths in Backticks:**

```markdown
Example: `src/utils/helper.py` (if "src/utils/helper.py" is illustrative and not a real repo path)
```

2. **Branch Names in Inline Code:**

```markdown
Example: `feature/add-docs` (branch names with "/" trigger policy)
```

3. **URLs in Inline Code:**

```markdown
Example: `https://github.com/user/repo` (URLs with "//" may trigger depending on policy config)
```

### Remediation Rules

#### Rule 1: Illustrative Paths → Encode Slash

**Before:**

```markdown
See `docs/ops/runbooks/EXAMPLE.md` for details.
```

**After:**

```markdown
See `docs&#47;ops&#47;runbooks&#47;EXAMPLE.md` for details.
```

(Use HTML entity `&#47;` to encode "/" in illustrative inline code)

#### Rule 2: Real Repo Paths → Keep As-Is (If File Exists)

**If the file actually exists in the repo:**

```markdown
See `docs/ops/runbooks/RUNBOOK_DOCS_GATES_OPERATOR_PACK_QUICKSTART.md` for details.
```

(No encoding needed; gate recognizes real paths)

#### Rule 3: URLs → Move Outside Backticks or Encode

**Before:**

```markdown
Clone from `https://github.com/user/repo`.
```

**After (Option A: Remove Backticks):**

```markdown
Clone from https://github.com/user/repo.
```

**After (Option B: Encode):**

```markdown
Clone from `https:&#47;&#47;github.com&#47;user&#47;repo`.
```

### Minimal-Invasive Fix Pattern

- **Target:** Only the specific line(s) flagged by gate
- **Scope:** Change only the encoding, not the surrounding content
- **Verification:** Re-run token policy gate locally before committing

### Evidence Template

| Violation | File | Line | Fix Applied |
|-----------|------|------|-------------|
| Illustrative path "/" | `RUNBOOK_X.md` | 42 | Encoded as `&#47;` |

---

## Phase 5 — Reference-Targets Gate Failure: Missing Targets / Broken Links

**Goal:** Resolve links pointing to non-existent files or anchors.

### Diagnosis Classification

#### Type A: Real Target Missing (Bug)

**Symptom:** Link points to a file that should exist but doesn't (e.g., typo, wrong path, file renamed).

**Example:**

```
Link points to: docs&#47;ops&#47;runbooks&#47;OPERATOR_GUIDE.md
```

(File `docs&#47;ops&#47;runbooks&#47;OPERATOR_GUIDE.md` does not exist as this is an illustrative example)

**Decision:**

- Does the file exist under a different name? → Fix link to correct path
- Should the file exist? → Either create it (if in scope) or remove the link

#### Type B: Illustrative Target (Example in Docs)

**Symptom:** Link is an example in a runbook/guide, not meant to resolve to a real file.

**Example:**

```markdown
For custom runbooks, create a file like [MY_CUSTOM_RUNBOOK.md](docs&#47;ops&#47;runbooks&#47;MY_CUSTOM_RUNBOOK.md).
```

(This is illustrative; no such file exists)

**Decision:**

- Convert link to plain text (no Markdown link syntax)
- Or encode with `&#47;` so gate doesn't interpret as target

### Remediation Patterns

#### Pattern 1: Convert Link to Plain Text

**Before:**

```markdown
[MY_CUSTOM_RUNBOOK.md](docs&#47;ops&#47;runbooks&#47;MY_CUSTOM_RUNBOOK.md)
```

**After:**

```markdown
MY_CUSTOM_RUNBOOK.md (example path: docs&#47;ops&#47;runbooks&#47;...)
```

#### Pattern 2: Gate-Safe Encoding in Inline Code

**Before:**

```markdown
Create `docs/ops/runbooks/MY_RUNBOOK.md`
```

**After:**

```markdown
Create `docs&#47;ops&#47;runbooks&#47;MY_RUNBOOK.md`
```

(Encoding prevents gate from treating it as a reference target)

#### Pattern 3: Fix Broken Link to Real Target

**Before:**

```markdown
[Operator Guide](docs&#47;ops&#47;OPERATOR_GUIDE.md)
```

**After (correct path):**

```markdown
[Operator Guide](docs&#47;ops&#47;runbooks&#47;OPERATOR_GUIDE.md)
```

(Only if file truly exists at corrected path)

### Evidence Template

| Missing Target | Classification | Remediation Applied |
|----------------|----------------|---------------------|
| `docs&#47;ops&#47;runbooks&#47;EXAMPLE.md` | Illustrative | Converted to plain text |
| `docs&#47;ops&#47;OPERATOR_GUIDE.md` | Real (typo) | Corrected path to `runbooks&#47;OPERATOR_GUIDE.md` |

---

## Phase 6 — Fix-Forward Commit (No Rewrite)

**Goal:** Apply remediation changes as a new commit on the same branch (no rebase/force-push).

### Steps

1. **Stage Changes:**

```bash
git add docs/ops/runbooks/RUNBOOK_X.md
```

2. **Commit with Descriptive Message:**

```bash
git commit -m "docs(ops): fix-forward token-policy violations in RUNBOOK_X"
```

(or)

```bash
git commit -m "docs(ops): fix-forward reference-targets in RUNBOOK_Y"
```

3. **Push:**

```bash
git push origin feature-branch-name
```

### Why No Rewrite?

- **Determinism:** Each iteration is auditable; commit history shows progression
- **Safety:** No risk of losing work or creating conflicts with remote
- **Auditability:** Evidence chain intact (before/after diff visible in PR)

### Expected Outputs

- New commit SHA on PR branch
- PR updated automatically (GitHub reflects new commit)
- CI triggers re-check automatically

---

## Phase 7 — CI Re-Snapshot (One-Time) + Auto-Merge

**Goal:** Verify that fix-forward commit resolved gate failures; enable auto-merge if all checks pass.

### Snapshot Commands

```bash
gh pr checks <PR_NUMBER>
```

Or refresh GitHub UI Checks tab.

### Decision Tree

| CI Result | Action |
|-----------|--------|
| All checks PASS | → Enable auto-merge |
| Failures persist | → Iterate (back to Phase 4/5) or escalate if > 2 iterations |
| New failures introduced | → STOP, investigate scope creep or unintended side effects |

### Auto-Merge Activation

**GitHub UI:**

- PR page → Enable auto-merge (squash/merge/rebase per repo policy)

**GitHub CLI:**

```bash
gh pr merge <PR_NUMBER> --auto --squash
```

### Expected Outputs

- Auto-merge enabled
- PR merges automatically once all required checks pass (no further operator action needed)

---

## Phase 8 — Post-Merge Verify (main)

**Goal:** Confirm merged changes are present on `main` and functional.

### Verification Steps

1. **Sync Local `main`:**

```bash
git checkout main
git pull origin main
```

2. **Verify File Exists:**

```bash
ls -l docs/ops/runbooks/RUNBOOK_X.md
```

3. **Spot-Check Links (Optional):**

If runbook includes links, manually verify a few key links resolve:

```bash
cat docs/ops/runbooks/RUNBOOK_X.md | grep -E '\[.*\]\(.*\)'
```

(Visual inspection or use link checker tool if available)

4. **Branch Cleanup:**

```bash
git branch -d feature-branch-name
git push origin --delete feature-branch-name
```

### Expected Outputs

- File present on `main`
- No orphaned branches
- Local workspace clean

---

## Stop Conditions (Hard Abort Criteria)

Abort workflow and escalate if any of the following occur:

| Condition | Reason | Escalation Path |
|-----------|--------|-----------------|
| **Diff-Guard FAIL** | Changes not additive; risk of breaking existing docs | Manual review required; create diagnosis report |
| **Unclear Gate Interpretation** | Gate failure message ambiguous or contradictory | Consult gate maintainer; document edge case |
| **> 2 Fix-Forward Iterations Without Convergence** | Remediation not effective; potential tooling bug or scope issue | Escalate to gate owner; consider alternative approach |
| **Unintended Side Effects** | Fix-forward introduces new failures in unrelated files | Revert commit; re-scope remediation |
| **Token Policy + Reference Targets Both Fail (Intertwined)** | Complex remediation requiring simultaneous fixes | Split into two PRs or manual fix with extended review |

---

## Risk Matrix

| Risk Level | Scenario | Mitigation |
|------------|----------|------------|
| **LOW** | Single runbook addition, no index/crosslink changes | Standard fix-forward workflow |
| **LOW-MED** | Runbook with examples referencing real repo paths | Verify paths exist; use gate-safe encoding for illustrative paths |
| **MED** | Runbook modifying index (e.g., README.md in runbooks/) | Ensure additive-only; verify no orphaned links |
| **HIGH** | Runbook with complex anchor links or multi-file refactor | Consider splitting into smaller PRs; extended verification phase |

---

## Appendix A — Quick Reference (Operator Checklist)

### Pre-Flight

```bash
git fetch --prune
git status -sb
```

### Local Coverage Snapshot

```bash
git diff --name-only origin/main...HEAD > /tmp/gate_coverage.txt
make docs-gates
```

### PR Creation

- Title: `docs(ops): <brief description>`
- Body: Include local snapshot evidence + fix-forward policy

### CI Snapshot

```bash
gh pr checks <PR_NUMBER>
```

### Fix-Forward Commit

```bash
git add <file>
git commit -m "docs(ops): fix-forward <gate-name>"
git push origin <branch>
```

### Auto-Merge

```bash
gh pr merge <PR_NUMBER> --auto --squash
```

### Post-Merge Verify

```bash
git checkout main
git pull origin main
ls -l docs/ops/runbooks/<FILE>.md
git branch -d <branch>
git push origin --delete <branch>
```

---

## Appendix B — Expected Outputs (Examples)

### Example: Local Coverage Snapshot

```
docs/ops/runbooks/RUNBOOK_DOCS_GATES_FIX_FORWARD_CI_TRIAGE_CURSOR_MULTI_AGENT.md
docs/ops/runbooks/README.md
```

(Output of `git diff --name-only origin/main...HEAD`)

### Example: Token Policy Violation (CI Log Excerpt)

```
ERROR: Token Policy Gate
File: docs/ops/runbooks/RUNBOOK_X.md
Line 42: Inline code contains unescaped "/" in illustrative path
Suggestion: Use &#47; encoding for illustrative paths
```

### Example: Reference Targets Violation (CI Log Excerpt)

```
ERROR: Reference Targets Gate
Missing target: docs/ops/runbooks/EXAMPLE.md
Referenced in: docs/ops/runbooks/RUNBOOK_Y.md:87
```

### Example: Fix-Forward Commit Message

```
docs(ops): fix-forward token-policy violations in CI triage runbook

- Encode illustrative "/" in inline code examples
- Remove backticks from branch name references
```

---

## Appendix C — Evidence Pack Mini-Template

Use this template to document fix-forward iterations:

### Evidence Pack: Fix-Forward CI Triage

**PR Number:** #XXX  
**Branch:** `feature/add-ci-triage-runbook`  
**Operator:** Frank  
**Date:** YYYY-MM-DD

#### Iteration 1

**Local Snapshot:**  
- Timestamp: YYYY-MM-DD HH:MM:SS UTC  
- Verdict: PASS (all gates)  
- Files Evaluated: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_X.md`

**CI Snapshot (Commit SHA: abc1234):**  
- Timestamp: YYYY-MM-DD HH:MM:SS UTC  
- Token Policy: FAIL (3 violations)  
- Reference Targets: PASS

**Failure → Fix Mapping:**

| Violation | File | Line | Fix Applied | Commit |
|-----------|------|------|-------------|--------|
| Illustrative "/" in `src&#47;utils&#47;...` | RUNBOOK_X.md | 42 | Encoded as `&#47;` | def5678 |
| Branch name `feature&#47;x` in backticks | RUNBOOK_X.md | 87 | Removed backticks | def5678 |

**Fix-Forward Commit:**  
- SHA: def5678  
- Message: `docs(ops): fix-forward token-policy violations in RUNBOOK_X`

#### Iteration 2

**CI Re-Snapshot (Commit SHA: def5678):**  
- Timestamp: YYYY-MM-DD HH:MM:SS UTC  
- Token Policy: PASS  
- Reference Targets: PASS  
- Diff Guard: PASS

**Result:** All checks PASS → Auto-merge enabled

**Post-Merge Verify:**  
- Merged to `main` at commit SHA: 123abcd  
- File verified present: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_X.md`  
- Branch cleanup: `feature&#47;add-ci-triage-runbook` deleted

---

**End of Runbook**
