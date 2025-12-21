#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Peak_Trade – PR Inventory (FULL, not just 30) + Analysis Report
# Output: /tmp/peak_trade_pr_inventory_YYYYmmdd_HHMMSS/
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=run_helpers.sh
source "${SCRIPT_DIR}/run_helpers.sh"

REPO="${REPO:-rauterfrank-ui/Peak_Trade}"
LIMIT="${LIMIT:-1000}"
OUT_ROOT="${OUT_ROOT:-/tmp}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<EOF
Usage:
  REPO=owner/name LIMIT=1000 OUT_ROOT=/tmp ./scripts/ops/pr_inventory_full.sh

Outputs:
  \$OUT_ROOT/peak_trade_pr_inventory_<timestamp>/
    - open.json
    - closed_all.json
    - merged.json
    - merge_logs.csv
    - PR_INVENTORY_REPORT.md
EOF
  exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔎 Peak_Trade: PR Inventory + Analyse"
echo "Repo: $REPO | Limit: $LIMIT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Preflight
pt_require_cmd gh
pt_require_cmd python3 || pt_require_cmd python

PYBIN="python3"
command -v python3 >/dev/null || PYBIN="python"

if ! gh auth status >/dev/null 2>&1; then
  echo "❌ gh ist nicht authentifiziert. Bitte einmal ausführen: gh auth login"
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
OUT="$OUT_ROOT/peak_trade_pr_inventory_${TS}"
mkdir -p "$OUT"
echo "✅ Output dir: $OUT"

# Optional: default repo setzen (still safe)
pt_run_optional "Set default repo" gh repo set-default "$REPO"

FIELDS="number,title,state,createdAt,closedAt,mergedAt,author,url,headRefName,baseRefName,labels"

echo ""
echo "📥 Export PR lists (open/closed/merged)..."
gh pr list --state open   --limit "$LIMIT" --json $FIELDS > "$OUT/open.json"
gh pr list --state closed --limit "$LIMIT" --json $FIELDS > "$OUT/closed_all.json"
gh pr list --state merged --limit "$LIMIT" --json $FIELDS > "$OUT/merged.json"

echo "✅ Export done:"
echo " - $OUT/open.json"
echo " - $OUT/closed_all.json"
echo " - $OUT/merged.json"

echo ""
echo "🧠 Analyse + Reports..."
export PR_INVENTORY_OUT="$OUT"
"$PYBIN" - <<'PY'
import json, re, csv, os
from pathlib import Path
from datetime import datetime

out = Path(os.environ["PR_INVENTORY_OUT"])

open_p  = json.loads((out/"open.json").read_text(encoding="utf-8"))
closed  = json.loads((out/"closed_all.json").read_text(encoding="utf-8"))
merged  = json.loads((out/"merged.json").read_text(encoding="utf-8"))

# closed_all enthält auch merged (merged ⊂ closed).
closed_unmerged = [pr for pr in closed if not pr.get("mergedAt")]

merge_log_re  = re.compile(r"^docs\(ops\): add PR #\d+ merge log", re.I)
ops_infra_re  = re.compile(r"\bops\b|\bworkflow\b|\bci\b|\baudit\b|\brunbook\b|\bmerge log\b", re.I)
format_re     = re.compile(r"(format|pre-commit|fmt|ruff-format|black|lint)\b", re.I)

def cat(title: str) -> str:
    t = title or ""
    if merge_log_re.search(t): return "merge_log"
    if format_re.search(t):    return "format_sweep"
    if ops_infra_re.search(t): return "ops_infra"
    return "other"

counts = {
    "open": len(open_p),
    "closed_all": len(closed),
    "merged": len(merged),
    "closed_unmerged": len(closed_unmerged),
}

cat_counts = {"merge_log":0, "ops_infra":0, "format_sweep":0, "other":0}
for pr in closed:
    cat_counts[cat(pr.get("title",""))] += 1

merge_logs = []
for pr in closed:
    if cat(pr.get("title","")) == "merge_log":
        merge_logs.append({
            "number": pr["number"],
            "title": pr.get("title",""),
            "url": pr.get("url",""),
            "mergedAt": pr.get("mergedAt","") or "",
            "closedAt": pr.get("closedAt","") or "",
        })

merge_logs.sort(key=lambda x: (x["mergedAt"] or x["closedAt"]), reverse=True)

def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in fields})

write_csv(out/"merge_logs.csv", merge_logs, ["number","title","url","mergedAt","closedAt"])

md = []
md.append("# Peak_Trade – PR Inventory Report")
md.append("")
md.append(f"- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
md.append("")
md.append("## Totals")
md.append("")
md.append(f"- Open PRs: **{counts['open']}**")
md.append(f"- Closed (all): **{counts['closed_all']}**")
md.append(f"- Merged: **{counts['merged']}**")
md.append(f"- Closed (unmerged): **{counts['closed_unmerged']}**")
md.append("")
md.append("## Category counts (closed_all)")
md.append("")
for k in ["merge_log","ops_infra","format_sweep","other"]:
    md.append(f"- {k}: **{cat_counts[k]}**")
md.append("")
md.append("## Latest merge-log PRs (top 25)")
md.append("")
for r in merge_logs[:25]:
    when = r["mergedAt"] or r["closedAt"] or ""
    md.append(f"- PR #{r['number']} — {r['title']} ({when})")
    md.append(f"  - {r['url']}")
md.append("")
md.append("## Files")
md.append("")
md.append("- open.json")
md.append("- closed_all.json")
md.append("- merged.json")
md.append("- merge_logs.csv")
md.append("- PR_INVENTORY_REPORT.md")
md.append("")

(out/"PR_INVENTORY_REPORT.md").write_text("\n".join(md), encoding="utf-8")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("✅ Report generated")
print(f" - {out/'PR_INVENTORY_REPORT.md'}")
print(f" - {out/'merge_logs.csv'}")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
PY

echo ""
echo "✅ Done."
echo "Report: $OUT/PR_INVENTORY_REPORT.md"
echo "CSV:    $OUT/merge_logs.csv"
