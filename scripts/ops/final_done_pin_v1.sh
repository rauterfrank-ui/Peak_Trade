#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TS="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
EVI="out/ops/final_done_${TS}"

mkdir -p "$EVI"

# Core snapshot files
git status -sb > "$EVI/STATUS.txt"
git rev-parse HEAD > "$EVI/MAIN_HEAD.txt"
git log -n 10 --oneline --decorate > "$EVI/LOG10.txt"

# Open PRs best-effort (TLS may break gh); keep deterministic output
if command -v gh >/dev/null 2>&1; then
  if gh pr list --state open --json number,title,headRefName,baseRefName,author --jq '.' > "$EVI/OPEN_PRS.json" 2>/dev/null; then
    : # ok
  else
    echo "[]" > "$EVI/OPEN_PRS.json"
  fi
else
  echo "[]" > "$EVI/OPEN_PRS.json"
fi

# SHA256SUMS (macOS compatible, repo-root paths)
find "$EVI" -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' -print \
  | LC_ALL=C sort \
  | while IFS= read -r f; do
      shasum -a 256 "$f"
    done > "$EVI/SHA256SUMS.txt"

# Verify from repo-root
shasum -a 256 -c "$EVI/SHA256SUMS.txt" >/dev/null

# Bundle
BUNDLE="${EVI}.bundle.tgz"
tar -czf "$BUNDLE" "$EVI"
BUNDLE_SHA="$(shasum -a 256 "$BUNDLE" | awk '{print $1}')"

# Pin
PIN="out/ops/FINAL_DONE.txt"
cat > "$PIN" <<PIN
FINAL_DONE OK
timestamp_utc=${TS}
main_head=$(cat "$EVI/MAIN_HEAD.txt")
evi=${EVI}
bundle=${BUNDLE}
bundle_sha256=${BUNDLE_SHA}
PIN

shasum -a 256 "$PIN" > "${PIN}.sha256"

echo "FINAL_DONE_PIN_OK pin=${PIN} ts=${TS} head=$(cat "$EVI/MAIN_HEAD.txt") evi=${EVI}"
