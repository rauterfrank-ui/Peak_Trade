#!/usr/bin/env bash
set -euo pipefail

require_file() { test -f "$1" || { echo "ERR missing file: $1" >&2; exit 2; }; }
require_dir()  { test -d "$1" || { echo "ERR missing dir: $1" >&2; exit 2; }; }

TS_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
EVI_DIR="out/ops/p137_exec_net_shadow_readonly_finish_pack_${TS_UTC}"
BUNDLE="out/ops/p137_exec_net_shadow_readonly_finish_pack_${TS_UTC}.bundle.tgz"
PIN="out/ops/P137_EXEC_NET_SHADOW_READONLY_FINISH_PACK_DONE_${TS_UTC}.txt"

mkdir -p "$EVI_DIR"

latest_pin() {
  local pat="$1"
  ls -1 ${pat} 2>/dev/null | sort | tail -n 1
}

P135_PIN="$(latest_pin 'out/ops/P135_EXEC_NET_SHADOW_READONLY_EVI_DONE_*.txt')"
P136_PIN="$(latest_pin 'out/ops/P136_EXEC_NET_SHADOW_READONLY_FINISH_SNAPSHOT_DONE_*.txt')"
REPO_CLEAN_PIN="out/ops/REPO_CLEAN_BASELINE_DONE.txt"
FINAL_DONE_PIN="out/ops/FINAL_DONE.txt"

test -n "${P135_PIN:-}" || { echo "ERR no P135 pin found" >&2; exit 2; }
test -n "${P136_PIN:-}" || { echo "ERR no P136 pin found" >&2; exit 2; }

# Extract fields
get_field() {
  local file="$1" key="$2"
  grep -E "^${key}=" "$file" | tail -n 1 | sed "s/^${key}=//"
}

P135_EVI="$(get_field "$P135_PIN" evi)"
P135_BUNDLE="$(get_field "$P135_PIN" bundle)"
P136_EVI="$(get_field "$P136_PIN" evi)"
P136_BUNDLE="$(get_field "$P136_PIN" bundle)"

require_file "$P135_PIN"
require_file "${P135_PIN}.sha256"
require_file "$P136_PIN"
require_file "${P136_PIN}.sha256"
require_file "$REPO_CLEAN_PIN"
require_file "${REPO_CLEAN_PIN}.sha256"
require_file "$FINAL_DONE_PIN"
require_file "${FINAL_DONE_PIN}.sha256"

require_dir "$P135_EVI"
require_file "$P135_BUNDLE"
require_file "${P135_BUNDLE}.sha256"
require_dir "$P136_EVI"
require_file "$P136_BUNDLE"
require_file "${P136_BUNDLE}.sha256"

# Copy pins + bundles (and their sha256) + minimal manifests
mkdir -p "$EVI_DIR/p135" "$EVI_DIR/p136" "$EVI_DIR/pins"

cp -a "$P135_PIN" "${P135_PIN}.sha256" "$EVI_DIR/pins/"
cp -a "$P136_PIN" "${P136_PIN}.sha256" "$EVI_DIR/pins/"
cp -a "$REPO_CLEAN_PIN" "${REPO_CLEAN_PIN}.sha256" "$EVI_DIR/pins/"
cp -a "$FINAL_DONE_PIN" "${FINAL_DONE_PIN}.sha256" "$EVI_DIR/pins/"

cp -a "$P135_BUNDLE" "${P135_BUNDLE}.sha256" "$EVI_DIR/p135/"
cp -a "$P136_BUNDLE" "${P136_BUNDLE}.sha256" "$EVI_DIR/p136/"

# Link EVI dirs (copy minimal, not whole tree)
printf "%s\n" "$P135_EVI" > "$EVI_DIR/p135/EVI_PATH.txt"
printf "%s\n" "$P136_EVI" > "$EVI_DIR/p136/EVI_PATH.txt"

cat > "$EVI_DIR/LATEST_PINS.txt" <<EOF
P135_PIN=$P135_PIN
P136_PIN=$P136_PIN
REPO_CLEAN_PIN=$REPO_CLEAN_PIN
FINAL_DONE_PIN=$FINAL_DONE_PIN
EOF

# Manifest (simple)
cat > "$EVI_DIR/manifest.json" <<EOF
{
  "ts_utc": "${TS_UTC}",
  "p135_pin": "${P135_PIN}",
  "p136_pin": "${P136_PIN}",
  "repo_clean_pin": "${REPO_CLEAN_PIN}",
  "final_done_pin": "${FINAL_DONE_PIN}",
  "p135_bundle": "${P135_BUNDLE}",
  "p136_bundle": "${P136_BUNDLE}"
}
EOF

# SHA256SUMS (repo-root-relative, sandbox-safe generator + style guard)
bash scripts/ops/sha256sums_no_xargs_v1.sh "$EVI_DIR"

# Bundle + sidecar
tar -czf "$BUNDLE" "$EVI_DIR"
shasum -a 256 "$BUNDLE" > "${BUNDLE}.sha256"

# DONE pin + sidecar (repo-root-relative SHA format)
cat > "$PIN" <<EOF
P137_EXEC_NET_SHADOW_READONLY_FINISH_PACK_DONE OK
timestamp_utc=${TS_UTC}
main_head=$(git rev-parse HEAD)
evi=${EVI_DIR}
bundle=${BUNDLE}
bundle_sha256=$(cut -d ' ' -f1 < "${BUNDLE}.sha256")
p135_pin=${P135_PIN}
p136_pin=${P136_PIN}
EOF
shasum -a 256 "$PIN" > "${PIN}.sha256"

# Verify
shasum -a 256 -c "${PIN}.sha256"
shasum -a 256 -c "${BUNDLE}.sha256"
shasum -a 256 -c "${EVI_DIR}/SHA256SUMS.txt"

echo "P137_OK pin=${PIN} evi=${EVI_DIR} bundle=${BUNDLE}"
