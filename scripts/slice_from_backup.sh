#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/Users/frnkhrz/Peak_Trade}"
REMOTE="${REMOTE:-origin}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"
BACKUP_BRANCH="${BACKUP_BRANCH:-backup/wip-stash-restore-2025-12-12}"

AUTO_COMMIT="${AUTO_COMMIT:-0}"
AUTO_PUSH="${AUTO_PUSH:-0}"
AUTO_PR="${AUTO_PR:-0}"

log() { printf "%s\n" "$*"; }
die() { log "❌ $*"; exit 1; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || die "Command not found: $1"; }
in_git_repo() { git rev-parse --is-inside-work-tree >/dev/null 2>&1; }

ensure_clean_tree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    log "❌ Working tree is not clean. Bitte commit/stash, bevor du slicest."
    git status --short
    exit 1
  fi
}

fetch_all() {
  log "🔄 git fetch --all --prune"
  git fetch --all --prune
}

resolve_backup_ref() {
  if git show-ref --verify --quiet "refs/remotes/${REMOTE}/${BACKUP_BRANCH}"; then
    echo "${REMOTE}/${BACKUP_BRANCH}"; return
  fi
  if git show-ref --verify --quiet "refs/heads/${BACKUP_BRANCH}"; then
    echo "${BACKUP_BRANCH}"; return
  fi
  die "Backup branch nicht gefunden: ${BACKUP_BRANCH} (weder ${REMOTE}/${BACKUP_BRANCH} noch lokal)."
}

update_main() {
  log "🏁 Checkout ${MAIN_BRANCH} + Pull"
  git checkout "${MAIN_BRANCH}"
  git pull --ff-only "${REMOTE}" "${MAIN_BRANCH}"
}

path_exists_in_ref() {
  local ref="$1" path="$2"
  git ls-tree -r --name-only "$ref" -- "$path" | head -n 1 | grep -q .
}

checkout_paths_from_ref() {
  local ref="$1"; shift
  local -a paths=("$@")
  local -a missing=()
  local p

  for p in "${paths[@]}"; do
    if path_exists_in_ref "$ref" "$p"; then
      log "  ✅ import: $p"
      git checkout "$ref" -- "$p"
    else
      log "  ⚠️  missing in backup: $p"
      missing+=("$p")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    log "  📌 Missing paths summary:"
    for p in "${missing[@]}"; do log "     - $p"; done
  fi
}

confirm() {
  local prompt="$1" default="${2:-N}" ans=""
  if [[ "$default" == "Y" ]]; then
    read -r -p "${prompt} [Y/n] " ans || true
    ans="${ans:-Y}"
  else
    read -r -p "${prompt} [y/N] " ans || true
    ans="${ans:-N}"
  fi
  [[ "$ans" =~ ^[Yy]$ ]]
}

maybe_commit() {
  local msg="$1" do_commit="0"
  if [[ "$AUTO_COMMIT" == "1" ]]; then
    do_commit="1"
  else
    confirm "Commit erstellen? (${msg})" "Y" && do_commit="1"
  fi

  if [[ "$do_commit" == "1" ]]; then
    git add -A
    if git diff --cached --quiet; then
      log "  ℹ️  Nichts zu committen (Index leer). Überspringe Commit."
      return 0
    fi
    git commit -m "$msg"
  else
    log "  ⏭️  Commit übersprungen."
  fi
}

maybe_push() {
  local branch="$1" do_push="0"
  if [[ "$AUTO_PUSH" == "1" ]]; then
    do_push="1"
  else
    confirm "Push nach ${REMOTE}/${branch}?" "Y" && do_push="1"
  fi

  if [[ "$do_push" == "1" ]]; then
    git push -u "$REMOTE" "$branch"
  else
    log "  ⏭️  Push übersprungen."
  fi
}

maybe_create_pr() {
  local branch="$1" title="$2" body="$3" do_pr="0"

  if ! command -v gh >/dev/null 2>&1; then
    log "  ℹ️  gh nicht gefunden → PR-Erstellung übersprungen."
    return 0
  fi

  if [[ "$AUTO_PR" == "1" ]]; then
    do_pr="1"
  else
    confirm "Draft PR via gh erstellen?" "N" && do_pr="1"
  fi

  if [[ "$do_pr" == "1" ]]; then
    gh pr create --draft --base "$MAIN_BRANCH" --head "$branch" --title "$title" --body "$body" || \
      log "  ⚠️  gh pr create failed (evtl. nicht eingeloggt)."
  else
    log "  ⏭️  PR-Erstellung übersprungen."
  fi
}

run_smoke() {
  local label="$1"; shift
  local -a cmds=("$@")
  log "🧪 Smoke: ${label}"
  local c
  for c in "${cmds[@]}"; do
    log "  $ $c"
    bash -lc "$c" || true
  done
}

run_slice() {
  local ref="$1" branch="$2" commit_msg="$3" pr_title="$4" pr_body="$5"
  shift 5
  local -a paths=("$@")

  log ""
  log "=============================="
  log "🚧 SLICE: ${branch}"
  log "=============================="

  ensure_clean_tree
  update_main
  git checkout -B "$branch"

  checkout_paths_from_ref "$ref" "${paths[@]}"

  log ""
  log "📌 Diff-Stat:"
  git diff --stat || true

  run_smoke "$branch" \
    "python3 -m compileall -q src scripts 2>/dev/null || true" \
    "python3 -m pytest -q --collect-only 2>/dev/null | head -n 30 || true"

  maybe_commit "$commit_msg"
  maybe_push "$branch"
  maybe_create_pr "$branch" "$pr_title" "$pr_body"

  log "✅ Done: ${branch}"
  ensure_clean_tree
}

need_cmd git
need_cmd python3

cd "$REPO_DIR"
in_git_repo || die "Nicht in einem Git-Repo: $REPO_DIR"

log "📁 Repo: $REPO_DIR"
fetch_all
ensure_clean_tree

BACKUP_REF="$(resolve_backup_ref)"
log "🧷 Using backup ref: $BACKUP_REF"
log "⚠️  Backup-Branch NICHT löschen, bis alles gemerged ist!"

# PR #1 TODO Board
run_slice "$BACKUP_REF" \
  "feat/todo-board-system-v1" \
  "feat(docs): add TODO board system (config + generator + docs)" \
  "TODO board system (v1)" \
  "Imports TODO board generator + config + docs from backup branch." \
  "config/todo_board.yaml" \
  "scripts/build_todo_board_html.py" \
  "docs/00_overview" \
  "docs/ops/todo"

# PR #2 Promotion Loop
run_slice "$BACKUP_REF" \
  "feat/promotion-loop-v1" \
  "feat(governance): add promotion loop system (config + runner + docs)" \
  "Promotion loop system (v1)" \
  "Imports promotion loop system + runner + docs from backup branch." \
  "config/promotion_loop_config.toml" \
  "src/governance/promotion_loop" \
  "scripts/run_promotion_proposal_cycle.py" \
  "docs/learning_promotion_loop"

# PR #3 Meta / InfoStream (guard file included)
run_slice "$BACKUP_REF" \
  "feat/meta-infostream-v1" \
  "feat(meta): add meta/infostream modules + smoke tests" \
  "Meta / InfoStream (v1)" \
  "Imports src/meta + related scripts/tests from backup branch." \
  "src/meta/__init__.py" \
  "src/meta" \
  "scripts/infostream" \
  "tests/meta"

# PR #4 Macro Regimes
run_slice "$BACKUP_REF" \
  "feat/macro-regimes-v1" \
  "feat(macro): add macro regimes module + configs + tests" \
  "Macro regimes (v1)" \
  "Imports macro regimes module + config + tests from backup branch." \
  "src/macro_regimes" \
  "config/macro_regimes" \
  "scripts/macro_events" \
  "tests/macro_regimes"

# PR #5 Market Sentinel / Outlook
run_slice "$BACKUP_REF" \
  "feat/market-sentinel-v1" \
  "feat(market): add market sentinel + market outlook pipeline" \
  "Market sentinel + outlook (v1)" \
  "Imports market sentinel + outlook config/scripts/tests from backup branch." \
  "src/market_sentinel" \
  "config/market_outlook" \
  "scripts/market_outlook" \
  "tests/market_sentinel"

# PR #6 Workflows
run_slice "$BACKUP_REF" \
  "feat/workflows-automation-v1" \
  "ci(workflows): add automations (infostream/market_outlook/test-health)" \
  "CI workflows automation (v1)" \
  "Imports GitHub workflow automations from backup branch." \
  ".github/workflows"

# PR #7a Docs-only
run_slice "$BACKUP_REF" \
  "feat/docs-pack-v1" \
  "docs: add WIP docs pack (promotion/infostream/macro/ops)" \
  "Docs pack (WIP)" \
  "Imports docs-only pack from backup branch." \
  "docs"

log ""
log "⚠️  PR #7b ist sehr groß und sollte zuletzt kommen."
if confirm "PR #7b (src + tests) jetzt schon als Branch/PR erstellen?" "N"; then
  run_slice "$BACKUP_REF" \
    "feat/code-pack-v1" \
    "feat: import WIP code pack (src + tests) from backup" \
    "Code pack (WIP, large)" \
    "Imports remaining WIP code (src + tests) from backup branch. Recommended to merge last." \
    "src" \
    "tests"
else
  log "⏭️  PR #7b übersprungen."
fi

log ""
log "🎉 Fertig. Merge-Reihenfolge empfohlen: #2 → (#3-#6 beliebig) → #7a → #7b"
