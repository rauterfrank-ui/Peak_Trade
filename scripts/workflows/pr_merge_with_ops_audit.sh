#!/usr/bin/env bash
set -euo pipefail

cd ~/Peak_Trade

echo "== Peak_Trade: PR Merge + Ops Merge-Log Audit Workflow =="

# 0) Safety: Working Tree clean?
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Working tree ist NICHT sauber. Bitte commit/stash zuerst:"
  git status -sb
  exit 1
fi
echo "✅ Working tree clean"

# 1) PR Nummer ermitteln (oder vorher: export PR=225)
PR="${PR:-}"
if [ -z "$PR" ]; then
  PR="$(gh pr view --json number -q .number 2>/dev/null || true)"
fi
if [ -z "$PR" ]; then
  echo "❌ Konnte PR nicht automatisch ermitteln."
  echo "👉 Bitte setze PR manuell und starte neu, z.B.:  export PR=225"
  echo "Hier sind deine offenen PRs:"
  gh pr status
  exit 1
fi
echo "✅ PR=$PR"

# 2) PR Overview + Checks
echo ""
echo "== PR Overview =="
gh pr view "$PR" --web=false || true
echo ""
echo "== CI Checks (watch) =="
gh pr checks "$PR" --watch

# 3) Ops Audit VOR Merge (Merge-Log Infrastruktur)
echo ""
echo "== Ops Audit: check_ops_merge_logs.py (pre-merge) =="
uv run python scripts/audit/check_ops_merge_logs.py

# 4) Merge (Squash) + Branch löschen
echo ""
echo "== Merge: squash + delete branch =="
gh pr merge "$PR" --squash --delete-branch

# 5) Lokal main aktualisieren
echo ""
echo "== Local main update =="
git switch main
git pull --ff-only

# 6) Post-Merge: nochmal Ops Audit (schneller Konsistenz-Check)
echo ""
echo "== Ops Audit: check_ops_merge_logs.py (post-merge) =="
uv run python scripts/audit/check_ops_merge_logs.py

# 7) Final Sanity
echo ""
echo "== Final Sanity =="
git status -sb
git log -1 --oneline

echo ""
echo "🎉 DONE: PR gemerged, main aktuell, Ops Merge-Log Audit grün."
