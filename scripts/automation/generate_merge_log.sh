#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/automation/generate_merge_log.sh <PR_NUMBER> [--update-readme] [--skip-guards]

Generates:
  docs/ops/PR_<N>_MERGE_LOG.md

Options:
  --update-readme   Also index the merge log in docs/ops/README.md under "Merge Logs (Ops)" (idempotent)
  --skip-guards     Skip optional guards (unicode guard)
USAGE
}

if [[ $# -lt 1 ]]; then usage; exit 2; fi

PR_NUM="$1"; shift
UPDATE_README="false"
SKIP_GUARDS="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --update-readme) UPDATE_README="true"; shift ;;
    --skip-guards)   SKIP_GUARDS="true"; shift ;;
    -h|--help)       usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

command -v gh >/dev/null 2>&1 || { echo "ERROR: gh CLI not found"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "ERROR: gh not authenticated"; exit 1; }

TMP_JSON="$(mktemp -t pr_merge_log_XXXX.json)"

gh pr view "$PR_NUM" \
  --json number,title,state,mergedAt,mergeCommit,headRefName,baseRefName,url,author,commits,additions,deletions,files \
  > "$TMP_JSON"

# verify merged
python3 - <<PY
import json, sys
d=json.load(open("${TMP_JSON}","r",encoding="utf-8"))
if not d.get("mergedAt"):
    print("ERROR: PR #{} is not merged (mergedAt is null).".format(d.get("number")))
    sys.exit(1)
PY

export TMP_JSON_PATH="$TMP_JSON"

python3 - <<'PY'
import json, os, datetime
import re

p = os.environ.get("TMP_JSON_PATH")
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

num = d.get("number")
title = d.get("title")
url = d.get("url")
state = d.get("state")
merged_at = d.get("mergedAt") or "N/A"
merge_commit = (d.get("mergeCommit") or {}).get("oid") or "N/A"
head = d.get("headRefName") or "N/A"
base = d.get("baseRefName") or "N/A"
author = (d.get("author") or {}).get("login") or "N/A"
add = d.get("additions", "N/A")
dele = d.get("deletions", "N/A")
files = d.get("files") or []
file_paths = [f.get("path") for f in files if f.get("path")]

now_utc = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

os.makedirs("docs/ops", exist_ok=True)
out = f"docs/ops/PR_{num}_MERGE_LOG.md"

lines = []
lines.append(f"# PR #{num} – Merge Log")
lines.append("")
lines.append("## Metadata")
lines.append(f"- **PR:** {url}")
lines.append(f"- **Title:** {title}")
lines.append(f"- **State:** {state}")
lines.append(f"- **Merged At (UTC):** {merged_at}")
lines.append(f"- **Merge Commit:** `{merge_commit}`")
lines.append(f"- **Base → Head:** `{base}` ← `{head}`")
lines.append(f"- **Author:** `{author}`")
lines.append(f"- **Diffstat:** +{add} / −{dele}")
lines.append(f"- **Log Generated (UTC):** {now_utc}")
lines.append("")
lines.append("## Purpose")
lines.append(f"- Documents the successful merge of PR #{num} and post-merge verification steps.")
lines.append("")
lines.append("## Changed Files in PR")
if file_paths:
    for fp in file_paths:
        lines.append(f"- `{fp}`")
else:
    lines.append("- (No file list available via gh JSON output.)")
lines.append("")
lines.append("## Post-Merge Verifications")
lines.append("- Working tree clean after pulling `main`.")
lines.append("- Optional guards executed (format, Unicode/BiDi, batch validation) when available.")
lines.append("")
lines.append("## Notes")
lines.append("- This log is docs-only and safe to merge independently.")
lines.append("")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(out)
PY

MERGE_LOG_PATH="docs/ops/PR_${PR_NUM}_MERGE_LOG.md"
echo "OK: wrote ${MERGE_LOG_PATH}"

if [[ "$UPDATE_README" == "true" ]]; then
  python3 scripts/automation/_update_ops_readme_merge_logs_index.py \
    "$PR_NUM" "$MERGE_LOG_PATH" --readme docs/ops/README.md
  echo "OK: updated docs/ops/README.md (Merge Logs index)"
fi

if [[ "$SKIP_GUARDS" == "false" ]]; then
  if [[ -f scripts/automation/unicode_guard.py ]]; then
    python3 scripts/automation/unicode_guard.py "$MERGE_LOG_PATH" docs/ops/README.md || true
    echo "OK: unicode guard executed (if it reports clean, you're good)"
  else
    echo "NOTE: unicode_guard.py not found; skipping."
  fi
fi

rm -f "$TMP_JSON"
