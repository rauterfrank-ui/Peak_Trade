#!/usr/bin/env bash
# usage: wp_b5_affected_cmp.sh <worktree> <outdir>  — CI-style 8-shard run of diff-affected tests/ops files, 900s hard stop.
set -uo pipefail
WT="$1"; OUT="$2"
cd "$WT"
rm -rf "$OUT"; mkdir -p "$OUT"
PYTEST_ARGS=(-q --tb=line -rfE -m "not network and not external_tools" -p no:cacheprovider)
FILES=()
while IFS= read -r f; do [ -f "$f" ] && FILES+=("$f"); done < /tmp/wp_b5_ks_affected_ops_excl.txt
FILES+=(tests/risk_layer)
START=$(date +%s)
echo "START=$START FILES=${#FILES[@]}" > "$OUT/summary.txt"
PIDS=()
for ((s = 0; s < 8; s++)); do
  ( sf=(); for i in "${!FILES[@]}"; do (( i % 8 == s )) && sf+=("${FILES[i]}"); done
    ./scripts/pt -m pytest "${sf[@]}" "${PYTEST_ARGS[@]}" > "$OUT/shard_$s.log" 2>&1
    echo "RC=$? END=$(date +%s)" >> "$OUT/shard_$s.log" ) &
  PIDS+=($!)
done
( sleep 900; echo "HARD_STOP_900" >> "$OUT/summary.txt"; pkill -f "$WT/.venv/bin/python -m pytest" ) & WD=$!
for p in "${PIDS[@]}"; do wait "$p"; done
kill "$WD" 2>/dev/null
echo "WALLCLOCK=$(( $(date +%s) - START ))" >> "$OUT/summary.txt"
