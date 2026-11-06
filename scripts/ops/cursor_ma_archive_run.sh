#!/usr/bin/env bash
set -euo pipefail

# Archive a completed MA run from snapshot (preferred) or live artifacts.
# Invariant: audit JSON must remain in out/ai/audit/ to keep manifest.ndjson references valid.
#
# Usage:
#   scripts/ops/cursor_ma_archive_run.sh <RUN_ID> [NEW_RUN_ID]
#
# Behavior:
#   - Source of truth: out/ai/snapshots/<RUN_ID>/ (must contain L2/L3/L4 + audit + SHA256SUMS)
#   - Copies (not moves) snapshot files into out/ai/archive/<RUN_ID>/ (append-only)
#   - Ensures out/ai/audit/<RUN_ID>_audit.json exists (restores from snapshot if missing)
#   - Creates NEW_RUN_ID scaffolds under out/ai/l2,l3,l4 for next run (local output; out/ is gitignored)

RUN_ID="${1:-}"
NEW_RUN_ID="${2:-}"
if [[ -z "$RUN_ID" ]]; then
  echo "usage: $0 <RUN_ID> [NEW_RUN_ID]" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SNAP="$ROOT/out/ai/snapshots/$RUN_ID"
ARCH="$ROOT/out/ai/archive/$RUN_ID"

test -d "$SNAP" || { echo "missing snapshot dir: $SNAP" >&2; exit 3; }

L2="$SNAP/${RUN_ID}_market_outlook.md"
L3="$SNAP/${RUN_ID}_trade_plan.md"
L4="$SNAP/${RUN_ID}_critic_decision.md"
AUD="$SNAP/${RUN_ID}_audit.json"
SUMS="$SNAP/SHA256SUMS"

for f in "$L2" "$L3" "$L4" "$AUD" "$SUMS"; do
  [[ -f "$f" ]] || { echo "missing snapshot file: $f" >&2; exit 4; }
done

mkdir -p "$ARCH"
for name in "${RUN_ID}_market_outlook.md" "${RUN_ID}_trade_plan.md" "${RUN_ID}_critic_decision.md" "${RUN_ID}_audit.json" "SHA256SUMS"; do
  [[ -e "$ARCH/$name" ]] && { echo "archive already contains file (refusing): $ARCH/$name" >&2; exit 5; }
done

cp -f "$L2" "$ARCH/"
cp -f "$L3" "$ARCH/"
cp -f "$L4" "$ARCH/"
cp -f "$AUD" "$ARCH/${RUN_ID}_audit.json"
cp -f "$SUMS" "$ARCH/"

# Ensure manifest referential integrity: keep audit in out/ai/audit/
mkdir -p "$ROOT/out/ai/audit"
if [[ ! -f "$ROOT/out/ai/audit/${RUN_ID}_audit.json" ]]; then
  cp -f "$AUD" "$ROOT/out/ai/audit/${RUN_ID}_audit.json"
fi

if [[ -z "$NEW_RUN_ID" ]]; then
  NEW_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)_matrix_gated"
fi

mkdir -p "$ROOT/out/ai/l2" "$ROOT/out/ai/l3" "$ROOT/out/ai/l4"

cat > "$ROOT/out/ai/l2/${NEW_RUN_ID}_market_outlook.md" <<'MD'
# L2 Market Outlook (PROPOSER)

## Regime hypotheses

## Scenario tree

## Uncertainty notes

## No-trade triggers
MD

cat > "$ROOT/out/ai/l3/${NEW_RUN_ID}_trade_plan.md" <<'MD'
# L3 Trade Plan Advisory (PROPOSER)

## Input reference
- L2 artifact: (fill)

## Setup templates (non-executable)

## Risk checklist

## No-trade conditions
MD

cat > "$ROOT/out/ai/l4/${NEW_RUN_ID}_critic_decision.md" <<'MD'
# L4 Governance Critic Decision

## Inputs
- L2 artifact: (fill)
- L3 artifact: (fill)

## Decision
REJECT

## Rationale (SoD / scope / fail-closed)

## Required changes
MD

echo "ARCHIVED=$ARCH"
echo "SNAPSHOT=$SNAP"
echo "NEW_RUN_ID=$NEW_RUN_ID"
