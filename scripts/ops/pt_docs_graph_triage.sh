#!/usr/bin/env bash
#
# pt_docs_graph_triage.sh
#
# Runs docs graph triage against the latest (or specified) snapshot.
#
# Usage:
#   ./scripts/ops/pt_docs_graph_triage.sh [SNAPSHOT_PATH] [OUT_DIR]
#
# Examples:
#   ./scripts/ops/pt_docs_graph_triage.sh
#   ./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json
#
# Exit:
#   0 = success (always, even if broken links found - this is triage, not a gate)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Default snapshot path (latest as of 2026-01-13)
SNAPSHOT_PATH="${1:-docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot.json}"

# Default output directory (same as snapshot directory)
if [ -z "${2:-}" ]; then
    OUT_DIR="$(dirname "$SNAPSHOT_PATH")"
else
    OUT_DIR="$2"
fi

echo "======================================================================"
echo "PEAK_TRADE DOCS GRAPH TRIAGE"
echo "======================================================================"
echo "Snapshot: $SNAPSHOT_PATH"
echo "Output:   $OUT_DIR"
echo "======================================================================"
echo

# Check snapshot exists
if [ ! -f "$SNAPSHOT_PATH" ]; then
    echo "Error: Snapshot file not found: $SNAPSHOT_PATH" >&2
    exit 1
fi

# Run triage script
uv run python scripts/ops/docs_graph_triage.py \
    --snapshot "$SNAPSHOT_PATH" \
    --out-dir "$OUT_DIR"

exit 0
