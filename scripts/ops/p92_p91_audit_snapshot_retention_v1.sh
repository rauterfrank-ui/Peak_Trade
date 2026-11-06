#!/usr/bin/env bash
set -euo pipefail

KEEP_N="${KEEP_N:-48}"                      # keep last N snapshots (e.g. 48 ~= 4h @5min)
OPS_DIR="${OPS_DIR:-out/ops}"
PREFIX="${PREFIX:-p91_shadow_soak_audit_snapshot_}"
PIN_PREFIX="${PIN_PREFIX:-P91_AUDIT_SNAPSHOT_DONE_}"

if ! [[ "$KEEP_N" =~ ^[0-9]+$ ]] || [ "$KEEP_N" -lt 1 ]; then
  echo "usage: KEEP_N=<int>=48 OPS_DIR=out/ops bash $0" >&2
  exit 2
fi

cd "$(git rev-parse --show-toplevel)"

# snapshot dirs (bash 3.2 compatible: no mapfile)
dirs=()
while IFS= read -r d; do
  [[ -n "$d" ]] && dirs+=("$d")
done < <(ls -1 "$OPS_DIR" 2>/dev/null | grep "^${PREFIX}" | grep -v '\.' | LC_ALL=C sort)
count="${#dirs[@]}"

if [ "$count" -le "$KEEP_N" ]; then
  echo "P92_RETENTION_NOOP count=$count keep_n=$KEEP_N ops_dir=$OPS_DIR"
  exit 0
fi

to_delete_count=$((count - KEEP_N))
dels=()
for i in $(seq 0 $((to_delete_count - 1))); do
  dels+=("${dirs[$i]}")
done

# Delete dirs + their bundles (if any) + pins (best-effort)
for d in "${dels[@]}"; do
  evi="$OPS_DIR/$d"
  bun="$OPS_DIR/$d.bundle.tgz"
  bun_sha="$bun.sha256"

  rm -rf "$evi" 2>/dev/null || true
  rm -f "$bun" "$bun_sha" 2>/dev/null || true

  # delete matching pin(s) by timestamp embedded in name
  # example: p91_shadow_soak_audit_snapshot_20260216T095035Z -> ts=20260216T095035Z
  ts="${d#${PREFIX}}"
  rm -f "$OPS_DIR/${PIN_PREFIX}${ts}.txt" "$OPS_DIR/${PIN_PREFIX}${ts}.txt.sha256" 2>/dev/null || true
done

echo "P92_RETENTION_OK deleted=$to_delete_count remaining=$KEEP_N ops_dir=$OPS_DIR"
