#!/usr/bin/env bash
set -euo pipefail
cd ~/Peak_Trade

PR=259

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚦 Peak_Trade – PR #$PR Review → Merge (Ops-safe)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 0) Preflight: sauberer Working Tree (empfohlen)
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ Working Tree ist NICHT clean."
  echo "   Empfehlung: commit/stash, oder nur Review-only mit --dirty-ok."
  echo ""
fi

# Mergeable-Retries (für GitHub 'UNKNOWN' kurze Phase)
export MERGEABLE_RETRIES=5
export MERGEABLE_SLEEP_SEC=2

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1) REVIEW-ONLY (mit Watch, audit darf failen)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
scripts/ops/review_and_merge_pr.sh --pr "$PR" --watch --allow-fail audit

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2) MERGE (squash) + Update main (mit Watch, audit darf failen)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
scripts/ops/review_and_merge_pr.sh --pr "$PR" --watch --allow-fail audit --merge --method squash --update-main

echo ""
echo "✅ Done. Post-check:"
git status -sb
git log -1 --oneline
