#!/usr/bin/env bash
set -euo pipefail

PR_NUM="246"
REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
DATE_ISO="$(date -I)"

cd "$REPO_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Peak_Trade – Full Flow: Merge PR #$PR_NUM + Merge-Log PR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────────────────
# 0) Preflight
# ─────────────────────────────────────────────────────────────
echo ""
echo "📋 Step 0: Preflight"
git rev-parse --is-inside-work-tree >/dev/null
git fetch --all --prune

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "❌ Working tree not clean. Bitte commit/stash oder Änderungen verwerfen."
  git status
  exit 1
fi

# ─────────────────────────────────────────────────────────────
# 1) CI Checks beobachten (PR #246)
# ─────────────────────────────────────────────────────────────
echo ""
echo "👀 Step 1: Watch CI checks for PR #$PR_NUM"
gh pr checks "$PR_NUM" --watch

# ─────────────────────────────────────────────────────────────
# 2) PR mergen + Branch löschen
# ─────────────────────────────────────────────────────────────
echo ""
echo "✅ Step 2: Merge PR #$PR_NUM (squash + delete branch)"
gh pr merge "$PR_NUM" --squash --delete-branch

# ─────────────────────────────────────────────────────────────
# 3) Lokal main aktualisieren
# ─────────────────────────────────────────────────────────────
echo ""
echo "🔄 Step 3: Update local main"
git checkout main
git pull --ff-only

# ─────────────────────────────────────────────────────────────
# 4) Merge-Log PR vorbereiten
# ─────────────────────────────────────────────────────────────
echo ""
echo "📝 Step 4: Prepare merge-log PR for PR #$PR_NUM"

BR="docs/ops-pr${PR_NUM}-merge-log"
git checkout -b "$BR"

mkdir -p docs/ops

PR_TITLE="$(gh pr view "$PR_NUM" --json title -q .title)"
PR_URL="$(gh pr view "$PR_NUM" --json url -q .url)"
PR_AUTHOR="$(gh pr view "$PR_NUM" --json author -q .author.login)"
PR_MERGED_AT="$(gh pr view "$PR_NUM" --json mergedAt -q .mergedAt)"
PR_MERGE_COMMIT="$(gh pr view "$PR_NUM" --json mergeCommit -q .mergeCommit.oid)"

# Fallbacks, falls GitHub (aus irgendeinem Grund) Felder nicht liefert
PR_MERGED_AT="${PR_MERGED_AT:-TBD}"
PR_MERGE_COMMIT="${PR_MERGE_COMMIT:-TBD}"

MERGE_LOG_PATH="docs/ops/PR_${PR_NUM}_MERGE_LOG.md"

cat > "$MERGE_LOG_PATH" <<EOF
# PR #$PR_NUM — Merge Log

**PR:** $PR_URL
**Titel:** $PR_TITLE
**Merged:** $PR_MERGED_AT
**Merge-Commit:** $PR_MERGE_COMMIT
**Autor:** $PR_AUTHOR

---

## Summary

Dieser PR führt einen **End-to-End Deployment Drill** für die Knowledge-Deployment-Pipeline ein und behebt einen **Production Smoke Script Bug** unter \`set -euo pipefail\`.

---

## Why

Robuster, wiederholbarer Operator-Workflow für **CI → Merge → Lokaltest → optional Staging/Prod**, inkl.:
- Read-Endpunkte schnell verifizieren,
- **Write-Gating** sicher prüfen (403 im Prod-Mode),
- Bash-Fallen (z.B. leere Arrays unter \`set -u\`) sauber abfangen.

---

## Changes

### Added
- \`scripts/ops/knowledge_deployment_drill_e2e.sh\`
  - End-to-End Drill: Merge → Local Test → optional Staging/Prod
  - Konfigurierbar via ENV-Variablen
  - Cleanup via \`trap\`
  - Verbose Output Support

### Fixed
- \`scripts/ops/knowledge_prod_smoke.sh\`
  - Bugfix: **leeres \`EXTRA_HEADERS[@]\` Array** → **"unbound variable"** unter \`set -euo pipefail\`
  - Lösung: **Array-Längen-Check vor Iteration**

---

## Verification

### Bash Syntax
- ✅ \`scripts/ops/knowledge_prod_smoke.sh\`
- ✅ \`scripts/ops/knowledge_deployment_drill_e2e.sh\`

### Tests
- ✅ \`test_knowledge_prod_smoke_script.py\` — **17/17 passed**
- ✅ \`tests/ops\` — **75/75 passed** (0.23s)

### E2E Demo (lokal)
- ✅ Stats endpoint — **200**
- ✅ Snippets list — **200**
- ✅ Strategies list — **200**
- ✅ Search — **200**
- ✅ Write gating probe — **403** *(korrekt geblockt!)*

---

## Risk

🟢 **Minimal**
- Änderungen betreffen Ops-Skripte, keine Runtime-Produktionslogik.
- Bugfix reduziert Risiko (robust gegen \`set -u\` + leere Arrays).
- Drill-Skript ist optional und wirkt nur bei Operator-Ausführung.

---

## Operator How-To

### Local Drill (ohne Merge)
\`\`\`bash
cd ~/Peak_Trade
DO_MERGE=0 ./scripts/ops/knowledge_deployment_drill_e2e.sh
\`\`\`

### Drill gegen Staging
\`\`\`bash
cd ~/Peak_Trade
STAGING_URL="https://staging.example.com" \\
STAGING_TOKEN="..." \\
./scripts/ops/knowledge_deployment_drill_e2e.sh
\`\`\`

### Drill gegen Production (strict)
\`\`\`bash
cd ~/Peak_Trade
PROD_URL="https://prod.example.com" \\
PROD_TOKEN="..." \\
./scripts/ops/knowledge_deployment_drill_e2e.sh
\`\`\`

### Production Smoke (direkt)
\`\`\`bash
cd ~/Peak_Trade
./scripts/ops/knowledge_prod_smoke.sh
\`\`\`

---

## References
- PR #$PR_NUM: $PR_URL
- Files:
  - \`scripts/ops/knowledge_deployment_drill_e2e.sh\`
  - \`scripts/ops/knowledge_prod_smoke.sh\`
EOF

echo "✅ Wrote $MERGE_LOG_PATH"

# ─────────────────────────────────────────────────────────────
# 5) docs/ops/README.md + docs/PEAK_TRADE_STATUS_OVERVIEW.md aktualisieren (idempotent)
# ─────────────────────────────────────────────────────────────
echo ""
echo "🧩 Step 5: Update docs indexes (idempotent)"

python - <<'PY'
from pathlib import Path

pr_num = "246"
title = Path(".pr_title").read_text().strip() if Path(".pr_title").exists() else None
# In this script we don't rely on .pr_title; we read from env instead:
import os
title = os.environ.get("PR_TITLE", "") or "TBD"
merged_at = os.environ.get("PR_MERGED_AT", "") or "TBD"

readme = Path("docs/ops/README.md")
status = Path("docs/PEAK_TRADE_STATUS_OVERVIEW.md")

merge_line = f"- [PR #{pr_num}](PR_{pr_num}_MERGE_LOG.md) — {title} (merged {merged_at})"
changelog_line = f"- {os.environ.get('DATE_ISO','TBD')} — PR #{pr_num} merged: added knowledge deployment drill e2e script and fixed prod smoke script (empty EXTRA_HEADERS under set -u)."

def insert_after_heading(text: str, heading_candidates, line_to_insert: str) -> str:
    if line_to_insert in text:
        return text
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if any(ln.strip().lower() == h.lower() for h in heading_candidates):
            # insert after heading + optional blank line(s)
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            lines.insert(j, line_to_insert)
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    # fallback: append
    return text.rstrip("\n") + "\n\n" + line_to_insert + "\n"

if readme.exists():
    t = readme.read_text(encoding="utf-8")
    # Try common headings; if not found, we append at end.
    t2 = insert_after_heading(
        t,
        heading_candidates=["## Merge Logs", "## Merge-Logs", "## Merge Log", "## Merge-Log"],
        line_to_insert=merge_line
    )
    readme.write_text(t2, encoding="utf-8")

if status.exists():
    t = status.read_text(encoding="utf-8")
    t2 = insert_after_heading(
        t,
        heading_candidates=["## Changelog", "## Change Log", "# Changelog"],
        line_to_insert=changelog_line
    )
    status.write_text(t2, encoding="utf-8")

print("✅ Updated docs/ops/README.md and docs/PEAK_TRADE_STATUS_OVERVIEW.md (or appended if headings missing).")
PY

# Export vars for the python snippet (and for transparency)
export PR_TITLE PR_MERGED_AT DATE_ISO

# ─────────────────────────────────────────────────────────────
# 6) Quick checks + Commit + Push + PR erstellen
# ─────────────────────────────────────────────────────────────
echo ""
echo "🧪 Step 6: Quick checks"
uv run pytest -q tests/ops -q

echo ""
echo "💾 Step 7: Commit + Push + Open merge-log PR"
git add "$MERGE_LOG_PATH" docs/ops/README.md docs/PEAK_TRADE_STATUS_OVERVIEW.md

# --- Idempotency: exit cleanly if generator produced no changes ---
if git diff --quiet && git diff --cached --quiet; then
  echo "ℹ️ No changes to commit (already up-to-date). Exiting 0."
  exit 0
fi
# --- /Idempotency ---

git commit -m "docs(ops): add PR #${PR_NUM} merge log"
git push -u origin "$BR"

gh pr create \
  --title "docs(ops): add PR #${PR_NUM} merge log" \
  --body "Adds compact merge log for PR #${PR_NUM} and updates merge log indexes."

echo ""
echo "👀 Step 8: Watch merge-log PR checks"
ML_PR_NUM="$(gh pr view --json number -q .number)"
gh pr checks "$ML_PR_NUM" --watch

echo ""
echo "✅ Step 9: Merge merge-log PR (squash + delete branch)"
gh pr merge "$ML_PR_NUM" --squash --delete-branch

echo ""
echo "🔄 Step 10: Update local main (final)"
git checkout main
git pull --ff-only

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 DONE: PR #$PR_NUM merged + merge-log PR merged + local main updated."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
