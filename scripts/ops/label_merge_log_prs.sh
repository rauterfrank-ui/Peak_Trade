#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Peak_Trade – Label merge-log PRs (DRY_RUN default)
# Finds: PR titles matching "^docs(ops): add PR #... merge log"
# Action: gh pr edit <n> --add-label <LABEL>
# ─────────────────────────────────────────────────────────────

REPO="${REPO:-rauterfrank-ui/Peak_Trade}"
LABEL="${LABEL:-ops/merge-log}"
LIMIT="${LIMIT:-1000}"
DRY_RUN="${DRY_RUN:-1}"          # 1 = show only, 0 = apply
ENSURE_LABEL="${ENSURE_LABEL:-0}" # 1 = create label if missing

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<EOF
Usage:
  REPO=owner/name LABEL="ops/merge-log" LIMIT=1000 DRY_RUN=1 ./scripts/ops/label_merge_log_prs.sh

Safe defaults:
  DRY_RUN=1 (no GitHub changes)

To apply:
  DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh
EOF
  exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏷️  Peak_Trade: Label merge-log PRs"
echo "Repo: $REPO | Label: $LABEL | DRY_RUN=$DRY_RUN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

command -v gh >/dev/null || { echo "❌ gh CLI fehlt."; exit 1; }
command -v python3 >/dev/null || command -v python >/dev/null || { echo "❌ python fehlt."; exit 1; }

PYBIN="python3"
command -v python3 >/dev/null || PYBIN="python"

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh ist nicht authentifiziert. Bitte einmal ausführen: gh auth login"
  exit 1
fi

gh repo set-default "$REPO" >/dev/null 2>&1 || true

# Optional: ensure label exists
if [[ "$ENSURE_LABEL" == "1" ]]; then
  if ! gh label list --limit 1000 --json name -q ".[] | select(.name==\"$LABEL\") | .name" | grep -q "^${LABEL}$" ; then
    echo "ℹ️ Label '$LABEL' existiert nicht → erstelle..."
    # Farbe/Description bewusst simpel; kann später angepasst werden.
    gh label create "$LABEL" --description "Automatically labeled merge-log PRs" --color "ededed" >/dev/null
    echo "✅ Label created: $LABEL"
  fi
fi

TMP="/tmp/peak_trade_merge_log_prs.txt"
TMP_JSON="/tmp/peak_trade_prs.json"
rm -f "$TMP" "$TMP_JSON"

# PR Nummern extrahieren (closed, full)
gh pr list --state closed --limit "$LIMIT" --json number,title > "$TMP_JSON"

"$PYBIN" - <<'PY' > "$TMP"
import json, re, sys
from pathlib import Path
data = json.loads(Path("/tmp/peak_trade_prs.json").read_text())
rx = re.compile(r"^docs\(ops\): add PR #\d+ merge log", re.I)
nums = [str(pr["number"]) for pr in data if rx.search(pr.get("title",""))]
print("\n".join(nums))
PY

COUNT="$(wc -l < "$TMP" | tr -d ' ')"
echo "Found merge-log PRs: $COUNT"
echo "List: $TMP"

if [[ "$COUNT" == "0" ]]; then
  echo "✅ Nothing to do."
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo ""
  echo "DRY RUN (no changes). First 30 PRs:"
  head -n 30 "$TMP" | sed 's/^/ - PR #/'
  echo ""
  echo "To actually apply labels:"
  echo "  DRY_RUN=0 LABEL=\"$LABEL\" scripts/ops/label_merge_log_prs.sh"
  exit 0
fi

echo ""
echo "Applying label '$LABEL' to all merge-log PRs..."
while IFS= read -r n; do
  [[ -z "$n" ]] && continue
  echo " - labeling PR #$n"
  gh pr edit "$n" --add-label "$LABEL" >/dev/null
done < "$TMP"

echo "✅ Done. You can now filter by label: $LABEL"
