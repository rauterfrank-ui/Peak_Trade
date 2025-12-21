#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – Merge-Log PR Workflow (End-to-End, ultra-robust)
# ─────────────────────────────────────────────────────────────
# Vollständiger Workflow-Wrapper für Merge-Log Erstellung:
#   1. Preflight (main checkout, pull, auth check)
#   2. Ruft create_and_open_merge_log_pr.sh auf
#   3. Ultra-robuste PR-Detection via:
#      - Current branch (post-script)
#      - Head candidates (Branch-Namen)
#      - Title-Search Fallback
#   4. CI checks watch + merge (falls noch OPEN)
#   5. Lokal main updaten
#
# USAGE:
#   bash scripts/ops/run_merge_log_workflow_robust.sh <PR_NUMBER> [MODE]
#
# MODES:
#   auto       - Standard: auto-merge + Web (default)
#   review     - Kein Auto-Merge (manual review)
#   no-web     - Kein Browser öffnen
#   manual     - Kombiniert: kein Browser + kein Auto-Merge
#
# EXAMPLES:
#   bash scripts/ops/run_merge_log_workflow_robust.sh 207
#   bash scripts/ops/run_merge_log_workflow_robust.sh 207 review
#   bash scripts/ops/run_merge_log_workflow_robust.sh 207 manual
#
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Test Mode Detection (additiv, keine Breaking Changes)
# ─────────────────────────────────────────────────────────────
# Wenn PEAK_TRADE_TEST_MODE=1 gesetzt ist:
# - Keine destruktiven Git Aktionen
# - Kein echtes gh nötig
# - Zeigt nur resolved MODE + ARGS an
# - Exit 0 (valid input) / Exit 2 (invalid input)

TEST_MODE="${PEAK_TRADE_TEST_MODE:-0}"

# ─────────────────────────────────────────────────────────────
# Argument Parsing
# ─────────────────────────────────────────────────────────────

if [ $# -lt 1 ]; then
  echo "❌ Missing required argument: PR_NUMBER"
  echo "Usage: $0 <PR_NUMBER> [MODE]"
  echo "Modes: auto (default), review, no-web, manual"
  exit 2
fi

PR="$1"
MODE="${2:-auto}"

case "$MODE" in
  auto)
    MODE_ARGS=()
    ;;
  review)
    MODE_ARGS=(--no-merge)
    ;;
  no-web)
    MODE_ARGS=(--no-web)
    ;;
  manual)
    MODE_ARGS=(--no-web --no-merge)
    ;;
  *)
    echo "❌ Invalid mode: $MODE"
    echo "Valid modes: auto, review, no-web, manual"
    exit 2
    ;;
esac

# ─────────────────────────────────────────────────────────────
# Depth=1 Policy: Refuse to create merge-logs for merge-log PRs
# ─────────────────────────────────────────────────────────────

ALLOW_RECURSIVE="${ALLOW_RECURSIVE:-0}"

if [ "$ALLOW_RECURSIVE" != "1" ]; then
  echo "🔍 Checking Depth=1 policy: is PR #${PR} a merge-log PR?"

  # In TEST_MODE: use PEAK_TEST_PR_TITLE env var
  # In Normal mode: fetch via gh pr view
  if [ "$TEST_MODE" = "1" ]; then
    PR_TITLE="${PEAK_TEST_PR_TITLE:-}"
  else
    # Fetch PR title (suppress stderr, tolerate failures)
    PR_TITLE="$(gh pr view "$PR" --json title --jq .title 2>/dev/null || echo "")"
  fi

  if [ -n "$PR_TITLE" ]; then
    # Pattern: ^docs\(ops\): add PR #[0-9]+ merge log
    if echo "$PR_TITLE" | grep -Eq '^docs\(ops\): add PR #[0-9]+ merge log'; then
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "⛔ Depth=1 Policy Violation"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "Refusing to generate a merge log for a merge-log PR:"
      echo "  PR #${PR}: ${PR_TITLE}"
      echo ""
      echo "Why: This would create a recursive merge-log PR chain."
      echo "     Merge-log PRs are documentation-only and do not need their own logs."
      echo ""
      echo "Override (if you really need this):"
      echo "  ALLOW_RECURSIVE=1 make mlog-auto PR=${PR}"
      echo ""
      exit 2
    fi
  else
    # Only warn in normal mode (in test mode, empty title is expected if not set)
    if [ "$TEST_MODE" != "1" ]; then
      echo "⚠️  Could not fetch PR title (gh pr view failed). Proceeding anyway."
    fi
  fi

  echo "✅ Depth=1 check passed: PR #${PR} is not a merge-log PR"
fi

# ─────────────────────────────────────────────────────────────
# Test Mode: Output resolved values and exit
# ─────────────────────────────────────────────────────────────

if [ "$TEST_MODE" = "1" ]; then
  echo "TEST_MODE: Resolved configuration"
  echo "  PR: ${PR}"
  echo "  MODE: ${MODE}"
  # Handle empty array without triggering 'unbound variable' error
  if [ ${#MODE_ARGS[@]} -eq 0 ]; then
    echo "  ARGS:"
  else
    echo "  ARGS: ${MODE_ARGS[*]}"
  fi
  exit 0
fi

# ─────────────────────────────────────────────────────────────
# Normal Mode: Proceed with workflow
# ─────────────────────────────────────────────────────────────

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Peak_Trade: Merge-Log Workflow für PR #${PR}"
echo "Mode: ${MODE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────────────
# Preflight
# ─────────────────────────────────────────────────────────────

echo ""
echo "🔍 Preflight: Ensuring clean state..."
cd ~/Peak_Trade

# Show current status
git status -sb

# Checkout main and pull
echo "📥 Switching to main and pulling latest..."
git checkout main
git pull --ff-only

# Check gh auth
echo "🔐 Verifying GitHub CLI authentication..."
if ! gh auth status; then
  echo "❌ GitHub CLI not authenticated"
  exit 1
fi

# ─────────────────────────────────────────────────────────────
# Optional: Show target PR status
# ─────────────────────────────────────────────────────────────

echo ""
echo "📋 Target PR #${PR} Status:"
gh pr view "$PR" --json number,state,mergedAt,title,url | jq .

# ─────────────────────────────────────────────────────────────
# Run Core Script
# ─────────────────────────────────────────────────────────────

echo ""
echo "🚀 Running: create_and_open_merge_log_pr.sh for PR #${PR}..."
bash scripts/ops/create_and_open_merge_log_pr.sh --pr "$PR" ${MODE_ARGS[@]+"${MODE_ARGS[@]}"}

# ─────────────────────────────────────────────────────────────
# Ultra-Robust PR Detection
# ─────────────────────────────────────────────────────────────

echo ""
echo "🔎 Detecting newly created merge-log PR (ultra-robust)..."

# 1) Current branch (falls das Script auf dem Merge-Log Branch endet)
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Current branch: ${CURRENT_BRANCH}"

# 2) Kandidaten (verschiedene Branch-Naming Patterns)
HEAD_CANDIDATES=(
  "${CURRENT_BRANCH}"
  "docs/ops-pr${PR}-merge-log"
  "docs/ops-pr${PR}-mergelog"
  "docs/ops-pr${PR}-merge"
  "docs/ops-pr-${PR}-merge-log"
  "docs/ops-pr-${PR}"
)

NEW_PR=""
NEW_STATE=""
NEW_TITLE=""
NEW_URL=""
NEW_HEAD=""

# Helper: Versuche PR via head-Branch zu finden
try_by_head() {
  local HEAD="$1"
  [[ -z "$HEAD" ]] && return 1

  local INFO
  INFO="$(gh pr list --state all --head "$HEAD" --limit 1 --json number,state,title,url,headRefName \
    -q 'if length>0 then "FOUND\t\(.[]|.number)\t\(.[]|.state)\t\(.[]|.headRefName)\t\(.[]|.title)\t\(.[]|.url)" else "" end' 2>/dev/null || true)"

  if [[ -n "${INFO}" && "${INFO}" == FOUND* ]]; then
    IFS=$'\t' read -r _ NEW_PR NEW_STATE NEW_HEAD NEW_TITLE NEW_URL <<< "${INFO}"
    return 0
  fi
  return 1
}

# 3) Head-Branch Lookup (Current → candidates)
echo "Searching by branch name..."
for HEAD in "${HEAD_CANDIDATES[@]}"; do
  if try_by_head "${HEAD}"; then
    echo "✅ Found via branch: ${HEAD}"
    break
  fi
done

# 4) Fallback: Title-Search (wenn Branch-Naming komplett anders ist)
if [[ -z "${NEW_PR}" ]]; then
  echo "Branch lookup failed, trying title search..."

  SEARCH_PATTERNS=(
    "PR #${PR} merge log in:title"
    "add PR #${PR} merge log in:title"
    "docs(ops) PR #${PR} in:title"
    "PR_${PR}_MERGE_LOG in:title"
  )

  for SEARCH in "${SEARCH_PATTERNS[@]}"; do
    echo "  Searching: ${SEARCH}"
    INFO="$(gh pr list --state all --author "@me" --search "$SEARCH" --limit 1 --json number,state,title,url,headRefName \
      -q 'if length>0 then "FOUND\t\(.[]|.number)\t\(.[]|.state)\t\(.[]|.headRefName)\t\(.[]|.title)\t\(.[]|.url)" else "" end' 2>/dev/null || true)"

    if [[ -n "${INFO}" && "${INFO}" == FOUND* ]]; then
      IFS=$'\t' read -r _ NEW_PR NEW_STATE NEW_HEAD NEW_TITLE NEW_URL <<< "${INFO}"
      echo "✅ Found via title search: ${SEARCH}"
      break
    fi
  done
fi

# 5) Wenn immer noch nichts gefunden: Debug ausgabe + Exit
if [[ -z "${NEW_PR}" ]]; then
  echo ""
  echo "❌ Konnte den neu erstellten Merge-Log PR nicht eindeutig finden."
  echo ""
  echo "Debug-Info:"
  echo "  Kandidaten-Branches:"
  printf "    - %s\n" "${HEAD_CANDIDATES[@]}"
  echo ""
  echo "  Letzte offene PRs von dir (zur Orientierung):"
  gh pr list --author "@me" --state open --limit 15
  echo ""
  echo "  Alle PRs mit 'merge log' im Titel (letzte 10):"
  gh pr list --state all --search "merge log in:title" --limit 10
  exit 2
fi

# ─────────────────────────────────────────────────────────────
# PR Found - Show Info
# ─────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Detected Merge-Log PR #${NEW_PR}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "State:  ${NEW_STATE}"
echo "Head:   ${NEW_HEAD}"
echo "Title:  ${NEW_TITLE}"
echo "URL:    ${NEW_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────────────
# Watch Checks & Merge (nur wenn OPEN)
# ─────────────────────────────────────────────────────────────

if [[ "${NEW_STATE}" == "OPEN" ]]; then
  echo ""
  echo "⏳ Watching CI checks for PR #${NEW_PR}..."
  gh pr checks "${NEW_PR}" --watch

  echo ""
  echo "🔀 Merging PR #${NEW_PR} (squash + delete branch)..."
  # Tolerant falls schon gemerged (z.B. durch Auto-Merge im ersten Script)
  if gh pr merge "${NEW_PR}" --squash --delete-branch; then
    echo "✅ PR #${NEW_PR} successfully merged"
  else
    echo "⚠️  Merge command exited with non-zero (möglicherweise bereits gemerged)"
  fi
elif [[ "${NEW_STATE}" == "MERGED" ]]; then
  echo ""
  echo "✅ PR #${NEW_PR} ist bereits MERGED"
else
  echo ""
  echo "⚠️  PR #${NEW_PR} ist nicht OPEN (State=${NEW_STATE})"
  echo "    Skipping checks/merge step"
fi

# ─────────────────────────────────────────────────────────────
# Finalize: Update Local Main
# ─────────────────────────────────────────────────────────────

echo ""
echo "🔄 Finalizing: Updating local main..."
git checkout main
git pull --ff-only

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DONE: Merge-Log Workflow abgeschlossen"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  Original PR:   #${PR}"
echo "  Merge-Log PR:  #${NEW_PR}"
echo "  Status:        ${NEW_STATE}"
echo "  Mode:          ${MODE}"
echo ""
echo "📁 Merge log file: docs/ops/PR_${PR}_MERGE_LOG.md"
echo ""
