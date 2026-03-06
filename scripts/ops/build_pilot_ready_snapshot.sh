#!/usr/bin/env bash
set -euo pipefail

STRICT="${STRICT:-0}"
if [[ "$STRICT" != "0" && "$STRICT" != "1" ]]; then
  echo "STRICT must be 0 or 1" >&2
  exit 2
fi

UTC_TS="$(date -u +"%Y%m%dT%H%M%SZ")"
SNAPSHOT_DIR="out/ops/pilot_ready_snapshot_${UTC_TS}"
INPUTS_DIR="${SNAPSHOT_DIR}/inputs"

mkdir -p "$SNAPSHOT_DIR" "$INPUTS_DIR"

declare -a EXPECTED_PATHS=(
  "out/ops/prbi_latest"
  "out/ops/prbg_latest"
  "out/ops/prbe_latest"
  "out/ops/prbj_latest"
  "config/ops/live_pilot_caps.toml"
)

declare -a FOUND_PATHS=()
declare -a MISSING_PATHS=()

copy_into_inputs() {
  local src="$1"
  local base
  base="$(basename "$src")"
  if [[ -d "$src" ]]; then
    cp -R "$src" "${INPUTS_DIR}/${base}"
  else
    cp "$src" "${INPUTS_DIR}/${base}"
  fi
}

for path in "${EXPECTED_PATHS[@]}"; do
  if [[ -e "$path" ]]; then
    FOUND_PATHS+=("$path")
    copy_into_inputs "$path"
  else
    MISSING_PATHS+=("$path")
  fi
done

if [[ "$STRICT" == "1" && "${#MISSING_PATHS[@]}" -gt 0 ]]; then
  printf 'STRICT=1 and required inputs are missing:\n' >&2
  printf ' - %s\n' "${MISSING_PATHS[@]}" >&2
  exit 1
fi

MANIFEST_PATH="${SNAPSHOT_DIR}/manifest.json"
SHA_PATH="${SNAPSHOT_DIR}/SHA256SUMS.txt"
SUMMARY_JSON_PATH="${SNAPSHOT_DIR}/snapshot_summary.json"
SUMMARY_MD_PATH="${SNAPSHOT_DIR}/snapshot_summary.md"
DONE_PATH="${SNAPSHOT_DIR}/DONE_${UTC_TS}.txt"
DONE_SHA_PATH="${DONE_PATH}.sha256"

found_json="[]"
if [[ "${#FOUND_PATHS[@]}" -gt 0 ]]; then
  found_json="$(printf '%s\n' "${FOUND_PATHS[@]}" | python3 - <<'PY'
import json, sys
items=[line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(items, indent=2))
PY
)"
fi

missing_json="[]"
if [[ "${#MISSING_PATHS[@]}" -gt 0 ]]; then
  missing_json="$(printf '%s\n' "${MISSING_PATHS[@]}" | python3 - <<'PY'
import json, sys
items=[line.strip() for line in sys.stdin if line.strip()]
print(json.dumps(items, indent=2))
PY
)"
fi

cat > "$SUMMARY_JSON_PATH" <<EOF_JSON
{
  "timestamp_utc": "${UTC_TS}",
  "strict_mode": "${STRICT}",
  "snapshot_dir": "${SNAPSHOT_DIR}",
  "policy_note": "NO_TRADE default preserved",
  "discovered_inputs": ${found_json},
  "missing_inputs": ${missing_json},
  "verification": {
    "sha256_file": "SHA256SUMS.txt",
    "command": "cd ${SNAPSHOT_DIR} && shasum -a 256 -c SHA256SUMS.txt"
  }
}
EOF_JSON

{
  echo "# Pilot Ready Snapshot"
  echo
  echo "- Timestamp (UTC): ${UTC_TS}"
  echo "- Strict mode: ${STRICT}"
  echo "- Snapshot dir: ${SNAPSHOT_DIR}"
  echo "- Policy note: NO_TRADE default preserved"
  echo
  echo "## Discovered inputs"
  if [[ "${#FOUND_PATHS[@]}" -eq 0 ]]; then
    echo "- __MISSING__"
  else
    printf -- '- %s\n' "${FOUND_PATHS[@]}"
  fi
  echo
  echo "## Missing inputs"
  if [[ "${#MISSING_PATHS[@]}" -eq 0 ]]; then
    echo "- none"
  else
    printf -- '- __MISSING__: %s\n' "${MISSING_PATHS[@]}"
  fi
  echo
  echo "## Verification"
  echo '```bash'
  echo "cd ${SNAPSHOT_DIR}"
  echo "shasum -a 256 -c SHA256SUMS.txt"
  echo '```'
} > "$SUMMARY_MD_PATH"

cat > "$DONE_PATH" <<EOF_DONE
PILOT_READY_SNAPSHOT_DONE
timestamp_utc=${UTC_TS}
snapshot_dir=${SNAPSHOT_DIR}
strict_mode=${STRICT}
policy_note=NO_TRADE default preserved
EOF_DONE

python3 - <<PY > "$MANIFEST_PATH"
import json
manifest = {
    "timestamp_utc": "${UTC_TS}",
    "strict_mode": "${STRICT}",
    "snapshot_dir": "${SNAPSHOT_DIR}",
    "generated_files": [
        "manifest.json",
        "SHA256SUMS.txt",
        "snapshot_summary.json",
        "snapshot_summary.md",
        "$(basename "$DONE_PATH")",
        "$(basename "$DONE_SHA_PATH")",
    ],
    "copied_inputs_dir": "inputs",
    "discovered_inputs": ${found_json},
    "missing_inputs": ${missing_json},
    "policy_note": "NO_TRADE default preserved",
}
print(json.dumps(manifest, indent=2))
PY

(
  cd "$SNAPSHOT_DIR"
  shasum -a 256 \
    manifest.json \
    snapshot_summary.json \
    snapshot_summary.md \
    "$(basename "$DONE_PATH")" \
    > SHA256SUMS.txt

  shasum -a 256 "$(basename "$DONE_PATH")" > "$(basename "$DONE_SHA_PATH")"
)

echo "Created snapshot: ${SNAPSHOT_DIR}"
echo "Verify with: cd ${SNAPSHOT_DIR} && shasum -a 256 -c SHA256SUMS.txt"
