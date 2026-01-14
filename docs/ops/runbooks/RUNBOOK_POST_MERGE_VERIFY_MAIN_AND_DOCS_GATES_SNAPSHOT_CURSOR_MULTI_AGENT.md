# RUNBOOK — Post-Merge Verify (main) + Local Docs Gates Snapshot (No-Watch)
Status: DRAFT (Operator-Ready)  
Owner: Ops / Docs Integrity  
Risk: LOW (verification-only; no destructive operations by default)

## 1) Executive Summary
This runbook defines a safe, repeatable, snapshot-based procedure to:
- verify that `main` is synced with `origin/main` after a merge, and
- run a local "Docs Gates" snapshot (no watch loops) to detect token-policy or documentation integrity regressions.

It is optimized for docs-heavy PRs and governance workflows where evidence capture matters.

## 2) When to Use
Use after:
- Squash-merge or auto-merge completed successfully
- You need to confirm local repo state, merge commit, file presence, and docs gate status
- You want a local verification snapshot that matches the governance posture of CI

Not intended for:
- fixing violations (use the dedicated remediation runbooks)
- rebases or history rewrites

## 3) Preconditions
- You have local access to the Peak_Trade repo
- You can run git commands locally
- Optional: you have the docs gates scripts available in the repo (common in this codebase)

## 4) Safety Principles
- Snapshot-first: inventory before any action
- No watch loops: always produce a point-in-time status
- No destructive steps by default
- Stop on ambiguity: if state is unclear, capture evidence and halt

## 5) Stop Conditions (Hard Stops)
STOP immediately if any is true:
- Working tree is dirty and you did not explicitly intend to verify dirty state
- You are in detached HEAD and do not know why
- You see prompt continuations such as `>` or `dquote>` in your shell
- `main` diverges from `origin/main` unexpectedly
- The merge commit cannot be verified against expected SHA (if you have one)

## 6) Phase 1 — Pre-Flight (Repo + Continuation Guard)
Goal: Confirm you are in the correct repo and shell is not in continuation mode.

Operator actions:
- If your terminal shows `>` or `dquote>`: press Ctrl-C once to exit continuation mode.
- Ensure you are in the repo root (example location may vary by machine).

Snapshot commands (example):
- `pwd`
- `git rev-parse --show-toplevel`
- `git status -sb`

Evidence to capture:
- output of `git status -sb`
- the resolved repo root path

## 7) Phase 2 — Verify main vs origin/main
Goal: Confirm local `main` matches remote `origin/main` with fast-forward-only posture.

Snapshot commands:
- `git fetch --prune`
- `git switch main`
- `git pull --ff-only`
- `git status -sb`

Expected:
- `main...origin/main` is aligned
- working tree is clean (unless you explicitly intended otherwise)

## 8) Phase 3 — Confirm Merge Commit and File Presence
Goal: Confirm the merge commit is at HEAD and required deliverables exist.

Snapshot commands:
- `git log -1 --oneline`
- `git show --name-only --oneline --no-patch HEAD`
- Verify the expected file(s) exist (example):  
  - `test -f docs/ops/merge_logs/PR_729_MERGE_LOG.md && echo "OK: merge log exists" || echo "MISSING"`

Notes:
- Avoid adding illustrative inline-code paths with slashes; keep examples plain text unless you confirm they are real.

## 9) Phase 4 — Local Docs Gates Snapshot (No-Watch)
Goal: Run a local point-in-time docs gates snapshot for changed files (or the last commit range) without any watch loops.

### 9.1 Preferred: Use the consolidated snapshot runner (if present)
Try to locate a snapshot script in scripts/ops.

Snapshot commands (examples):
- `ls scripts/ops | grep -E "docs.*gates.*snapshot|pt_.*docs.*snapshot" || true`

If present, run it in a range-based way (examples; exact flags may vary by repo):
- `bash scripts/ops/pt_docs_gates_snapshot.sh --help || true`
- Then run a snapshot for the last commit or merge range, for example:  
  - `bash scripts/ops/pt_docs_gates_snapshot.sh --changed "HEAD~1..HEAD"`

### 9.2 Fallback: Run individual validators (if present)
If no consolidated runner exists, discover available validators:
- `ls scripts/ops | grep -E "token|reference|diff|gate" || true`

Then run what is available (examples; names may vary):
- Token policy validator (changed range):
  - `python scripts/ops/validate_docs_token_policy.py --changed "HEAD~1..HEAD"`
- Reference targets verifier:
  - `bash scripts/ops/verify_docs_reference_targets.sh --changed "HEAD~1..HEAD"`
- Diff guard / policy gate checks:
  - run the repo's documented diff-guard script for the same range, if available

### 9.3 Interpret Results
Record:
- PASS/FAIL per gate
- counts (violations, broken targets) if reported
- whether failures are pre-existing or introduced (if the tool outputs this)

Hard stop:
- If any gate fails, do not attempt "quick fixes" inside this runbook. Capture evidence and switch to the remediation runbook.

## 10) Phase 5 — Evidence Capture (Minimal Template)
Copy/paste and fill:

```
EVIDENCE — POST-MERGE VERIFY + DOCS GATES SNAPSHOT
- Date (UTC):
- Repo root:
- Branch:
- HEAD SHA:
- origin/main SHA:
- Working tree clean (Y/N):
- Merge commit verified (Y/N):
- Key file existence checks:
  - (list)
- Docs Gates Snapshot:
  - Token Policy: PASS/FAIL (notes)
  - Reference Targets: PASS/FAIL (notes)
  - Diff Guard / Policy: PASS/FAIL (notes)
- Notes / anomalies:
- Stop conditions triggered (if any):
```

## 11) Rollback / Recovery (If Something Looks Wrong)
- If you accidentally changed branches or lost context:
  - `git reflog` to locate prior HEAD
- If you pulled unexpected commits:
  - stop and capture evidence first (do not reset without governance context)

## 12) Operator Quickstart (Minimal)
1) Pre-flight:
   - pwd, git rev-parse --show-toplevel, git status -sb
2) Sync:
   - git fetch --prune, git switch main, git pull --ff-only
3) Verify:
   - git log -1 --oneline, git show --name-only --no-patch HEAD
4) Docs gates snapshot (no watch):
   - try consolidated snapshot runner, else fallback validators
5) Fill evidence template

End.
