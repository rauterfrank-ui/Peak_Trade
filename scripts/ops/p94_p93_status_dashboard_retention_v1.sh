#!/usr/bin/env bash
set -euo pipefail

KEEP_N="${KEEP_N:-48}"
OPS_DIR="${OPS_DIR:-out/ops}"

# P93 artifacts:
# - Evidence dir:   out/ops/p93_online_readiness_status_<TS>/
# - Bundle:         out/ops/p93_online_readiness_status_<TS>.bundle.tgz (+ .sha256)
# - Pin:            out/ops/P93_STATUS_DASHBOARD_DONE_<TS>.txt (+ .sha256)

if ! [[ "$KEEP_N" =~ ^[0-9]+$ ]]; then
  echo "P94_RETENTION_FAIL invalid KEEP_N=$KEEP_N" >&2
  exit 2
fi

if [ ! -d "$OPS_DIR" ]; then
  echo "P94_RETENTION_FAIL ops_dir_missing ops_dir=$OPS_DIR" >&2
  exit 3
fi

# Collect timestamps from evidence dirs
# bash3.2-safe: no mapfile
dirs="$(ls -1 "$OPS_DIR" 2>/dev/null | grep '^p93_online_readiness_status_[0-9]\{8\}T[0-9]\{6\}Z$' || true)"
count="$(echo "$dirs" | sed '/^$/d' | wc -l | tr -d ' ')"

if [ "$count" -le "$KEEP_N" ]; then
  echo "P94_RETENTION_NOOP count=$count keep_n=$KEEP_N ops_dir=$OPS_DIR"
  exit 0
fi

# Sort oldest->newest, delete oldest (count-KEEP_N)
to_delete_n=$((count - KEEP_N))

# shellcheck disable=SC2086
to_delete="$(echo "$dirs" | LC_ALL=C sort | head -n "$to_delete_n" | sed '/^$/d')"

echo "$to_delete" | while IFS= read -r d; do
  [ -z "$d" ] && continue
  ts="${d#p93_online_readiness_status_}"

  evi_dir="$OPS_DIR/$d"
  bundle="$OPS_DIR/$d.bundle.tgz"
  bundle_sha="$bundle.sha256"
  pin="$OPS_DIR/P93_STATUS_DASHBOARD_DONE_${ts}.txt"
  pin_sha="$pin.sha256"

  rm -rf "$evi_dir" || true
  rm -f "$bundle" "$bundle_sha" "$pin" "$pin_sha" || true

  echo "P94_RETENTION_DELETE ts=$ts"
done

# recompute remaining
dirs_after="$(ls -1 "$OPS_DIR" 2>/dev/null | grep '^p93_online_readiness_status_[0-9]\{8\}T[0-9]\{6\}Z$' || true)"
count_after="$(echo "$dirs_after" | sed '/^$/d' | wc -l | tr -d ' ')"
echo "P94_RETENTION_OK deleted=$to_delete_n remaining=$count_after ops_dir=$OPS_DIR"
