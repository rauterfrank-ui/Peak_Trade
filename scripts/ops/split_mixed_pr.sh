#!/usr/bin/env bash
set -euo pipefail

# =========================
# Peak_Trade: split mixed changes into 2 PRs (DOCS + FEATURE)
# Includes PAUSE hooks to manually run: git add -p ...
# =========================

# >>>> EDIT DEFAULTS (or override via env) <<<<
DOCS_BRANCH="${DOCS_BRANCH:-docs/split-pr-x2}"
FEAT_BRANCH="${FEAT_BRANCH:-feat/split-pr-x2}"

DOCS_TITLE="${DOCS_TITLE:-docs(ops): split docs/ops changes from mixed set}"
FEAT_TITLE="${FEAT_TITLE:-feat: split feature/code changes from mixed set}"

# If you have PR body files, script will use them, else fallback to short bodies.
DOCS_BODY_FILE="${DOCS_BODY_FILE:-docs/ops/pr_bodies/PR_BODY_DOCS.md}"
FEAT_BODY_FILE="${FEAT_BODY_FILE:-docs/ops/pr_bodies/PR_BODY_FEATURE.md}"

# Patterns (path-based heuristic)
is_docs_path() {
  local f="$1"
  [[ "$f" == docs/* ]] && return 0
  [[ "$f" == scripts/ops/* ]] && return 0
  [[ "$f" == *.md ]] && return 0
  return 1
}
is_feat_path() {
  local f="$1"
  [[ "$f" == src/* ]] && return 0
  [[ "$f" == config/* ]] && return 0
  [[ "$f" == tests/* ]] && return 0
  return 1
}

pause() {
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "PAUSE: $1"
  echo "Tip: nutze jetzt z.B. 'git status' und 'git add -p <file>'"
  echo "Weiter mit ENTER…"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  read -r </dev/tty || true
}

die() { echo "ERROR: $*" >&2; exit 1; }

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

orig_branch="$(git branch --show-current || true)"
echo "Repo: $repo_root"
echo "Start branch: ${orig_branch:-<detached>}"
echo

# Collect changed files (staged + unstaged + untracked via git status)
mapfile -t changed < <(
  { git diff --name-only; git diff --cached --name-only; } | awk 'NF' | sort -u
)

# Include untracked files too (important!)
mapfile -t untracked < <(git ls-files --others --exclude-standard | awk 'NF' | sort -u)
if ((${#untracked[@]})); then
  changed+=( "${untracked[@]}" )
  mapfile -t changed < <(printf "%s\n" "${changed[@]}" | awk 'NF' | sort -u)
fi

((${#changed[@]})) || die "Keine Änderungen gefunden (staged/unstaged/untracked)."

docs_files=()
feat_files=()
other_files=()

for f in "${changed[@]}"; do
  if is_docs_path "$f"; then
    docs_files+=( "$f" )
  elif is_feat_path "$f"; then
    feat_files+=( "$f" )
  else
    other_files+=( "$f" )
  fi
done

echo "Detected change buckets:"
echo "  DOCS candidates:   ${#docs_files[@]}"
echo "  FEATURE candidates:${#feat_files[@]}"
echo "  OTHER (mixed?):    ${#other_files[@]}"
echo

if ((${#other_files[@]})); then
  echo "OTHER / mixed-candidates (manuell zuordnen, ggf. via git add -p):"
  printf "  - %s\n" "${other_files[@]}"
  echo
fi

pause "Wenn du willst: prüfe jetzt 'git diff --stat' / 'git status' bevor wir stashen."

# 1) Stash everything, so we can branch from fresh main
stash_name="split-mixed-$(date +%Y%m%d_%H%M%S)"
git stash push -u -m "$stash_name" >/dev/null
echo "Stashed: $stash_name"
echo

# 2) Update main and create docs branch
git checkout main >/dev/null
git pull --ff-only
git checkout -b "$DOCS_BRANCH" >/dev/null
git stash pop >/dev/null || die "stash pop failed on docs branch"

echo "==> On DOCS branch: $DOCS_BRANCH"
git status --porcelain=v1
echo

# Stage obvious docs files
if ((${#docs_files[@]})); then
  git add -- "${docs_files[@]}" || true
fi

# Let user manually stage hunks for mixed files
if ((${#other_files[@]})); then
  echo
  echo "Mixed candidates exist. Entscheide jetzt: was gehört in DOCS PR?"
  echo "Empfohlen: nutze 'git add -p <file>' für einzelne Hunks."
  pause "Jetzt manuell patch-stagen für DOCS (z.B. git add -p .github/workflows/x.yml)."
fi

echo "==> Staged for DOCS:"
git diff --cached --stat || true
echo

git diff --cached --quiet && die "DOCS branch: Nichts staged. Stage files/hunks und starte erneut oder passe Patterns an."

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

git commit -m "docs(ops): split docs/ops changes from mixed set"
git push -u origin HEAD

# Create docs PR
if [[ -f "$DOCS_BODY_FILE" ]]; then
  gh pr create --base main --title "$DOCS_TITLE" --body-file "$DOCS_BODY_FILE"
else
  gh pr create --base main --title "$DOCS_TITLE" --body "Split docs/ops changes out of a mixed set."
fi

# 3) Stash remaining changes and create feature branch
git stash push -u -m "${stash_name}-remaining" >/dev/null

git checkout main >/dev/null
git pull --ff-only
git checkout -b "$FEAT_BRANCH" >/dev/null
git stash pop >/dev/null || die "stash pop failed on feature branch"

echo
echo "==> On FEATURE branch: $FEAT_BRANCH"
git status --porcelain=v1
echo

# Stage obvious feature files
if ((${#feat_files[@]})); then
  git add -- "${feat_files[@]}" || true
fi

# Remaining other files: let user decide/stage via patch
# (Some OTHER may have been intentionally left for feature PR, e.g. .github/ or tooling)
echo
echo "If there are remaining mixed/other files, patch-stage them now for FEATURE:"
pause "Jetzt manuell patch-stagen für FEATURE (git add -p <file>)."

echo "==> Staged for FEATURE:"
git diff --cached --stat || true
echo

git diff --cached --quiet && die "FEATURE branch: Nichts staged. Stage files/hunks und starte erneut oder passe Patterns an."

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

git commit -m "feat: split feature/code changes from mixed set"
git push -u origin HEAD

# Create feature PR
if [[ -f "$FEAT_BODY_FILE" ]]; then
  gh pr create --base main --title "$FEAT_TITLE" --body-file "$FEAT_BODY_FILE"
else
  gh pr create --base main --title "$FEAT_TITLE" --body "Split feature/code changes out of a mixed set."
fi

echo
echo "✅ Done."
echo "DOCS branch:   $DOCS_BRANCH"
echo "FEATURE branch:$FEAT_BRANCH"
