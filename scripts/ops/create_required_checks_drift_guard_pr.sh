#!/usr/bin/env bash
#
# create_required_checks_drift_guard_pr.sh
#
# Creates a PR with the required checks drift guard feature
#
# Usage:
#   create_required_checks_drift_guard_pr.sh
#
# Environment Variables (optional):
#   REPO_DIR     Repository directory (default: $HOME/Peak_Trade)
#   BRANCH       Feature branch name (default: feat/required-checks-drift-guard-v1)
#   BASE         Base branch (default: main)
#   COMMIT_MSG   Commit message (default: feat(ops): add required checks drift guard)
#   PR_TITLE     PR title (default: feat(ops): add required checks drift guard)
#   LABELS_CSV   Labels to add (default: ops,ci)

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG (bei Bedarf anpassen)
# ──────────────────────────────────────────────────────────────────────────────
REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
BASE="${BASE:-main}"
COMMIT_MSG="${COMMIT_MSG:-feat(ops): add required checks drift guard}"
PR_TITLE="${PR_TITLE:-feat(ops): add required checks drift guard}"
PR_BODY_FILE="${PR_BODY_FILE:-/tmp/pr_body_required_checks_drift_guard.md}"
LABELS_CSV="${LABELS_CSV:-ops,ci}"  # optional: kommasepariert, leer lassen falls keine Labels

# ──────────────────────────────────────────────────────────────────────────────
# 0) Repo + Branch
# ──────────────────────────────────────────────────────────────────────────────
cd "$REPO_DIR"
git fetch origin "$BASE" --prune

git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"
git rebase "origin/$BASE"

# ──────────────────────────────────────────────────────────────────────────────
# 1) Offline checks (Smoke / Doctor / Script)
# ──────────────────────────────────────────────────────────────────────────────
echo "== 1) Offline checks =="

test -f scripts/ops/verify_required_checks_drift.sh
chmod +x scripts/ops/verify_required_checks_drift.sh

# a) Script selbst (offline)
if ./scripts/ops/verify_required_checks_drift.sh --help 2>/dev/null | grep -q -- '--offline'; then
  ./scripts/ops/verify_required_checks_drift.sh --offline
else
  ./scripts/ops/verify_required_checks_drift.sh
fi

# b) Ops doctor (falls vorhanden)
if [ -x scripts/ops/ops_center.sh ]; then
  scripts/ops/ops_center.sh doctor || true
fi

# c) Pytests (falls vorhanden; läuft nur, wenn Tests existieren)
if [ -d tests ]; then
  if command -v uv >/dev/null 2>&1; then
    uv run pytest -q || true
  elif command -v pytest >/dev/null 2>&1; then
    pytest -q || true
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# 2) Optional live drift check (gh auth + jq)
# Exit Codes:
#   0 = ✅ Match (Doc == Live)
#   2 = ⚠️ Drift (warn-only) -> Review drift, update doc oder Branch Protection
#   1 = ❌ Error (Preflight failed: gh/jq/auth Problem)
# ──────────────────────────────────────────────────────────────────────────────
echo "== 2) Optional live drift check (requires gh auth + jq) =="

LIVE_SUPPORTED=0
if ./scripts/ops/verify_required_checks_drift.sh --help 2>/dev/null | grep -q -- '--live'; then
  LIVE_SUPPORTED=1
fi

if [ "$LIVE_SUPPORTED" -eq 1 ]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "❌ gh fehlt. Installiere GitHub CLI oder skippe Live-Check." >&2
    exit 1
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "❌ jq fehlt. Installiere jq oder skippe Live-Check." >&2
    exit 1
  fi
  if ! gh auth status >/dev/null 2>&1; then
    echo "❌ gh nicht authentifiziert. Führe 'gh auth login' aus." >&2
    exit 1
  fi

  set +e
  ./scripts/ops/verify_required_checks_drift.sh --live --warn-only
  LIVE_RC=$?
  set -e

  if [ "$LIVE_RC" -eq 0 ]; then
    echo "✅ Required Checks: No Drift (ok)"
  elif [ "$LIVE_RC" -eq 2 ]; then
    echo "⚠️ Required Checks: Drift detected (warn-only)."
    echo "   → Action: Drift reviewen und entweder Docs aktualisieren ODER Branch Protection / Required Checks Liste anpassen."
  else
    echo "❌ Live drift check error (exit=$LIVE_RC)."
    exit 1
  fi
else
  echo "ℹ️ Live-Check nicht unterstützt (kein --live). Überspringe Schritt 2."
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3) Commit + push + PR
# ──────────────────────────────────────────────────────────────────────────────
echo "== 3) Commit + push + PR =="

git add -A

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

git commit -m "$COMMIT_MSG"

git push -u origin HEAD

# PR Body (kurz & sauber)
cat > "$PR_BODY_FILE" <<'EOF'
## What
- Add required checks drift guard (offline) + optional live drift verification (gh+jq)
- Integrate into Ops Center / docs + smoke coverage

## Why
- Prevent silent drift between documented required checks and live Branch Protection settings
- Make drift review explicit (warn-only mode supports safe operations)

## Verification
- Offline smoke checks pass
- Optional live drift check returns:
  - 0 (match) or
  - 2 (warn-only drift) with action guidance
EOF

# PR erstellen (oder wiederverwenden, falls existiert)
if gh pr view >/dev/null 2>&1; then
  echo "ℹ️ PR existiert bereits für diesen Branch."
else
  gh pr create --base "$BASE" --head "$BRANCH" --title "$PR_TITLE" --body-file "$PR_BODY_FILE"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 4) Labels + watch checks (optional)
# ──────────────────────────────────────────────────────────────────────────────
echo "== 4) Labels + watch checks (optional) =="

if [ -n "${LABELS_CSV// /}" ]; then
  # gh akzeptiert mehrfach --add-label; wir splitten CSV
  IFS=',' read -r -a LABELS <<< "$LABELS_CSV"
  for L in "${LABELS[@]}"; do
    L_TRIM="$(echo "$L" | sed 's/^ *//;s/ *$//')"
    [ -n "$L_TRIM" ] && gh pr edit --add-label "$L_TRIM" || true
  done
fi

gh pr checks --watch
echo "✅ Done."
