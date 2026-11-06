#!/usr/bin/env bash
set -euo pipefail

TS="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

EVI="out/ops/repo_clean_baseline_${TS}"
BUNDLE="${EVI}.bundle.tgz"
PIN="out/ops/REPO_CLEAN_BASELINE_DONE.txt"

mkdir -p "$EVI"

# Snapshot
git status -sb > "$EVI/STATUS.txt"
git rev-parse HEAD > "$EVI/MAIN_HEAD.txt"
git log -n 10 --oneline --decorate > "$EVI/LOG10.txt"
(gh pr list --state open --json number,title,headRefName,url 2>/dev/null || echo "[]") > "$EVI/OPEN_PRS.txt"

# SHA256SUMS (repo-root relative paths; avoids xargs/sysconf)
(
  cd "$ROOT"
  find "$EVI" -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' -print \
    | LC_ALL=C sort \
    | while IFS= read -r f; do shasum -a 256 "$f"; done
) > "$EVI/SHA256SUMS.txt"

# Bundle
tar -czf "$BUNDLE" "$EVI"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"

# Pin
MAIN_HEAD="$(cat "$EVI/MAIN_HEAD.txt")"
BUNDLE_SHA256="$(cut -d' ' -f1 < "${BUNDLE}.sha256")"
cat > "$PIN" <<EOF
REPO_CLEAN_BASELINE_DONE OK
timestamp_utc=${TS}
main_head=${MAIN_HEAD}
evi=${EVI}
bundle=${BUNDLE}
bundle_sha256=${BUNDLE_SHA256}
EOF
shasum -a 256 "$PIN" > "${PIN}.sha256"

# Verify (must run from repo-root because SHA256SUMS paths are repo-root relative)
shasum -c "$EVI/SHA256SUMS.txt" >/dev/null
shasum -c "${BUNDLE}.sha256" >/dev/null
shasum -c "${PIN}.sha256" >/dev/null

echo "REPO_CLEAN_BASELINE_PIN_OK ts=${TS} head=${MAIN_HEAD} evi=${EVI}"
