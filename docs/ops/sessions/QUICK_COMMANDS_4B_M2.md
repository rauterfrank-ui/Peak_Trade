# Quick Commands — 4B M2

**Worktree:** `/Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2`  
**Branch:** `feat/4b-m2-cursor-multi-agent`

Quick reference for operator during 4B M2 session.

---

## Worktree Navigation

```bash
# Go to worktree
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Open in Cursor
code /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Check status
git status -sb
git log --oneline -5
```

---

## Local Gates (Quick Check)

```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# All gates in one command
uv run ruff format --check src/ && \
uv run ruff check src/ && \
uv run pytest -q tests/ && \
uv run pip-audit && \
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs/ops/sessions/ && \
echo "✅ All gates PASSED"
```

### Individual Gates

```bash
# Lint (format check)
uv run ruff format --check src/

# Lint (check rules)
uv run ruff check src/

# Auto-fix format issues
uv run ruff format src/

# Test (quick)
uv run pytest -q tests/

# Test (specific module)
uv run pytest -xvs tests/[module]/

# Audit
uv run pip-audit

# Docs reference targets (session docs only)
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs/ops/sessions/

# Docs reference targets (all docs)
bash scripts/ops/verify_docs_reference_targets.sh
```

---

## Session Artifacts

```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2/docs/ops/sessions

# Edit session log
code SESSION_4B_M2_20260109.md

# Edit taskboard
code SESSION_4B_M2_TASKBOARD.md

# Edit decisions
code SESSION_4B_M2_DECISIONS.md

# View PR body
code PR_BODY_4B_M2.md

# View audit baseline
code AUDIT_BASELINE_4B_M2.md
```

---

## Commit Workflow

```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Check what's changed
git status -sb
git diff

# Stage specific files
git add <file>

# Stage all
git add -A

# Commit (pre-commit hooks will run)
git commit -m "type(scope): message"

# View recent commits
git log --oneline -5
```

---

## Push to Remote (When Ready)

```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Push branch (first time)
git push -u origin feat/4b-m2-cursor-multi-agent

# Push subsequent changes
git push
```

---

## Worktree Cleanup (After Merge)

```bash
# List all worktrees
git worktree list

# Remove this worktree (from any git repo)
git worktree remove /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Or force remove if has uncommitted changes
git worktree remove --force /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Clean up stale references
git worktree prune
```

---

## PR Creation (GitHub CLI)

```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Create draft PR (if gh cli installed)
gh pr create --draft \
  --title "feat(ai): 4B M2 cursor multi-agent workflow" \
  --body-file docs/ops/sessions/PR_BODY_4B_M2.md

# Or manually: Push branch, then create PR in GitHub UI
git push -u origin feat/4b-m2-cursor-multi-agent
# Then open: https://github.com/[org]/Peak_Trade/pull/new/feat/4b-m2-cursor-multi-agent
```

---

## Emergency: Reset Worktree

```bash
# If worktree gets into bad state, reset to origin/main
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2
git fetch origin
git reset --hard origin/main
git clean -fdx  # CAUTION: removes all untracked files

# Or recreate worktree from scratch
cd /Users/frnkhrz/Peak_Trade
git worktree remove --force /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2
bash scripts/ops/setup_worktree_4b_m2.sh /Users/frnkhrz/Peak_Trade
```

---

## File Locations (Quick Reference)

```
Worktree Root:
  /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2/

Session Artifacts:
  docs/ops/sessions/SESSION_4B_M2_20260109.md
  docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md
  docs/ops/sessions/SESSION_4B_M2_DECISIONS.md
  docs/ops/sessions/PR_BODY_4B_M2.md
  docs/ops/sessions/AUDIT_BASELINE_4B_M2.md
  docs/ops/sessions/QUICK_COMMANDS_4B_M2.md (this file)

Templates:
  docs/ops/sessions/APPENDIX_A_SYSTEM_PROMPT.md
  docs/ops/sessions/APPENDIX_B_TASKBOARD_TEMPLATE.md
  docs/ops/sessions/APPENDIX_C_PR_TEMPLATE.md

Runbook:
  docs/runbooks/RUNBOOK_4B_M2_CURSOR_MULTI_AGENT.md

Setup Script:
  scripts/ops/setup_worktree_4b_m2.sh
```

---

**Tip:** Bookmark this file for quick access during M2 implementation phase!
