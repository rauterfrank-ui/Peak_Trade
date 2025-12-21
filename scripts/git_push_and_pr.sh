#!/usr/bin/env bash
set -euo pipefail

cd ~/Peak_Trade

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Peak_Trade: Push + PR (aus bestehenden Commits)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 0) Preflight
echo ""
echo "📋 Preflight: git status"
git status --porcelain
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree ist nicht clean. Bitte commit/stash zuerst."
  exit 1
fi

echo ""
echo "⬇️  Fetch origin..."
git fetch origin --prune

# 1) Show last commits
echo ""
echo "📋 Last 5 commits:"
git log -5 --oneline --decorate

# 2) Check if HEAD is ahead of origin/main
AHEAD_COUNT="$(git rev-list --count origin/main..HEAD || echo "0")"
echo ""
echo "🔎 Ahead of origin/main: ${AHEAD_COUNT} commits"

if [[ "${AHEAD_COUNT}" == "0" ]]; then
  echo "✅ Nichts zu pushen/PRen: HEAD ist nicht ahead von origin/main."
  echo "ℹ️  Falls du dachtest, die Commits seien noch nicht oben: sie sind vermutlich schon auf origin/main."
  exit 0
fi

# 3) Ensure we're on a PR branch (not main)
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${CURRENT_BRANCH}" == "main" ]]; then
  BR="chore/ops-convenience-pack-$(date +%Y-%m-%d)-$(git rev-parse --short HEAD)"
  echo ""
  echo "🌿 Du bist auf main. Erstelle PR-Branch: ${BR}"
  git checkout -b "${BR}"
  CURRENT_BRANCH="${BR}"
else
  echo ""
  echo "🌿 Du bist bereits auf Branch: ${CURRENT_BRANCH}"
fi

# 4) Push branch
echo ""
echo "⬆️  Push branch -> origin/${CURRENT_BRANCH}"
git push -u origin "${CURRENT_BRANCH}"

# 5) Create PR (gh if available)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧾 Create PR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v gh >/dev/null 2>&1; then
  echo "✅ gh gefunden – erstelle PR gegen main..."
  # --fill nutzt Commit-Messages als Default Title/Body (robust, ohne dass wir Details raten müssen)
  gh pr create --base main --head "${CURRENT_BRANCH}" --fill

  echo ""
  echo "🔍 PR öffnen:"
  gh pr view --web

  echo ""
  echo "🧪 CI Checks (watch):"
  gh pr checks --watch
else
  echo "⚠️ gh CLI nicht gefunden."
  echo "➡️  Öffne GitHub und erstelle PR manuell:"
  echo "   - Base: main"
  echo "   - Compare: ${CURRENT_BRANCH}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Push + PR abgeschlossen"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
