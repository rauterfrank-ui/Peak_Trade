#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – Ops Convenience Pack (Git/PR End-to-End) – Robust v2
# - Handles dirty working tree via auto-stash (keeps your local changes safe)
# - Creates/uses branch idempotently
# - Uses heredocs for commit + PR body (no escaping pain)
# - Detects PR number reliably for checks/merge
# ─────────────────────────────────────────────────────────────

set -euo pipefail

REPO="$HOME/Peak_Trade"
MAIN_BRANCH="main"
BR="chore/ops-merge-log-workflow-convenience"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Peak_Trade: Ops Merge-Log Workflow Convenience PR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$REPO"

# Sanity: must be a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "❌ Not a git repository: $REPO"
  exit 2
}

# Helpers
is_dirty() {
  # includes untracked
  [[ -n "$(git status --porcelain)" ]]
}

echo ""
echo "📋 Step 0: Preflight checks..."
git status

# Auto-stash if dirty (common when you just implemented changes)
STASH_REF=""
if is_dirty; then
  echo ""
  echo "🧳 Working tree is dirty → auto-stashing changes..."
  git stash push -u -m "ops-convenience-pack:auto-stash($(date +%F_%T))" >/dev/null
  STASH_REF="$(git stash list -1 --format='%gd' || true)"
  echo "   Stashed as: ${STASH_REF:-<unknown>}"
fi

echo ""
echo "⬇️  Updating ${MAIN_BRANCH}..."
git checkout "$MAIN_BRANCH"
git pull --ff-only

echo ""
echo "🌿 Step 1: Creating / switching to branch..."
if git show-ref --verify --quiet "refs/heads/$BR"; then
  git checkout "$BR"
else
  git checkout -b "$BR"
fi

# Restore stashed work if we stashed
if [[ -n "${STASH_REF}" ]]; then
  echo ""
  echo "🎒 Restoring stashed changes (${STASH_REF})..."
  # If conflicts occur, stash pop exits non-zero → script stops (good).
  git stash pop >/dev/null
fi

echo ""
echo "🔍 Step 2: Running quality checks..."
uv run ruff check .
uv run pytest -q

echo ""
echo "📊 Step 3: Review changes..."
git diff --stat

echo ""
echo "💾 Step 4: Committing changes..."

# Stage (explicit list; adjust if you added more files)
git add \
  Makefile \
  docs/ops/README.md \
  scripts/ops/run_merge_log_workflow_robust.sh \
  tests/test_ops_merge_log_workflow_wrapper.py

# Show what will be committed
echo ""
echo "🧾 Staged files:"
git diff --cached --name-only

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

# Commit message via heredoc (no quoting issues)
git commit -F - <<'EOF'
chore(ops): add merge-log workflow convenience + tests

- Add Makefile targets: mlog, mlog-auto, mlog-review, mlog-no-web, mlog-manual
- Add docs/ops/README.md section: Merge-Log PR Workflow (robust)
- Add PEAK_TRADE_TEST_MODE support to wrapper (additiv, no breaking changes)
- Add offline deterministic tests (7 tests, <1s runtime)
EOF

echo ""
echo "🚀 Step 5: Pushing branch..."
git push -u origin "$BR"

echo ""
echo "📬 Step 6: Creating PR..."

TITLE="chore(ops): merge-log workflow convenience + tests"

# Create PR (if it already exists, gh may error; we'll detect via gh pr view afterwards)
set +e
gh pr create --title "$TITLE" --body-file - --base "$MAIN_BRANCH" <<'EOF'
**Ziel**: Operator-Convenience für Merge-Log Workflows

**Änderungen**:
- ✅ Makefile targets: `make mlog-auto PR=207` usw.
- ✅ Docs: Usage + Beispiele in `docs/ops/README.md`
- ✅ Test-Mode: `PEAK_TRADE_TEST_MODE=1` für deterministisches Testen
- ✅ Tests: 7 offline tests (<1s, deterministisch)

**Quality**:
- `uv run pytest -q` ✅ grün
- `uv run ruff check .` ✅ grün
- Keine Breaking Changes (nur additive Erweiterungen)

**Beispiel**:
```bash
make mlog-auto PR=207
make mlog-review PR=207
```
EOF
PR_CREATE_EXIT=$?
set -e

echo ""
echo "🔎 Step 7: Detecting PR number..."

# Robust PR detection (works even if pr create failed because PR already exists)
PR_NUM=""
if PR_DATA=$(gh pr view "$BR" --json number 2>/dev/null); then
  PR_NUM=$(echo "$PR_DATA" | jq -r .number)
fi

if [[ -z "$PR_NUM" || "$PR_NUM" == "null" ]]; then
  echo "❌ Could not detect PR number for branch: $BR"
  echo "   Manual fallback: gh pr list --head $BR"
  gh pr list --head "$BR" --limit 5
  exit 2
fi

echo "✅ Detected PR #${PR_NUM}"

echo ""
echo "⏳ Step 8: Watching CI checks for PR #${PR_NUM}..."
gh pr checks "$PR_NUM" --watch

echo ""
echo "🔀 Step 9: Merging PR #${PR_NUM}..."
gh pr merge "$PR_NUM" --squash --delete-branch

echo ""
echo "🔄 Step 10: Updating local ${MAIN_BRANCH}..."
git checkout "$MAIN_BRANCH"
git pull --ff-only

echo ""
echo "📋 Latest commit on ${MAIN_BRANCH}:"
git log -1 --oneline

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DONE: PR #${PR_NUM} merged and ${MAIN_BRANCH} updated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  Branch:  $BR"
echo "  PR:      #${PR_NUM}"
echo "  Status:  Merged to ${MAIN_BRANCH}"
echo ""
