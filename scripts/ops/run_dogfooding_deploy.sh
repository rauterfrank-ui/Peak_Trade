#!/usr/bin/env bash
# Wrapper für das PR-Toolkit Dogfooding Deployment mit Safety Checks & Logging

cd ~/Peak_Trade

set -euo pipefail

echo "== Repo =="
git rev-parse --show-toplevel
echo

echo "== Preflight: working tree clean? =="
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: Working tree ist nicht clean:"
  git status --porcelain
  echo
  echo "➡️  Bitte commit/stash oder rerun mit clean tree."
  exit 1
fi
echo "OK"
echo

echo "== Update main =="
git checkout main
git pull --ff-only
echo

echo "== Run Dogfooding Deploy Script =="
chmod +x ./scripts/ops/deploy_pr_toolkit_dogfooding.sh
LOG="/tmp/deploy_pr_toolkit_dogfooding.$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: $LOG"
./scripts/ops/deploy_pr_toolkit_dogfooding.sh 2>&1 | tee "$LOG"

echo
echo "✅ Done. Log: $LOG"
