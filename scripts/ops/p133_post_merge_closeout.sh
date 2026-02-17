#!/usr/bin/env bash
# P133 Post-Merge Closeout — nur ausführen wenn PR MERGED!
# Usage: PR=1463 ./scripts/ops/p133_post_merge_closeout.sh
# Oder:  ./scripts/ops/p133_post_merge_closeout.sh 1463

set -euo pipefail

PR="${PR:-${1:-}}"
if [[ -z "$PR" ]]; then
  echo "Usage: PR=<num> $0   OR   $0 <PR_NUM>" >&2
  echo "Example: PR=1463 $0" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "=== P133 Post-Merge Closeout (PR=$PR) ==="

git checkout main
git fetch origin --prune
git reset --hard origin/main

./scripts/ops/pr_ops_v1.sh "$PR" --no-watch --no-retrigger --closeout --bundle || true
./scripts/ops/repo_clean_baseline_pin_v1.sh
./scripts/ops/final_done_pin_v1.sh

echo ""
echo "=== Done ==="
git status -sb
git --no-pager log -5 --oneline
