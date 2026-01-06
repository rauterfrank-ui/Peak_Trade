#!/usr/bin/env bash
set -euo pipefail

# Wave Restore Status Dashboard (Docs/Small PRs)
# Usage:
#   bash scripts/ops/wave_restore_status.sh

export GH_PAGER=cat PAGER=cat LESS='-FRX'

echo "== Repo =="
pwd
git rev-parse --show-toplevel
git status -sb
echo

echo "== Open PRs (summary) =="
gh pr list --state open --limit 200
echo

echo "== Open restore/* PRs (json-lite) =="
gh pr list --state open --limit 200 --json number,title,headRefName,baseRefName,isDraft,mergeable,updatedAt,url \
  --jq '.[] | select(.headRefName | startswith("restore/")) | {n:.number,title:.title,head:.headRefName,mergeable:.mergeable,updated:.updatedAt,url:.url}'
echo

echo "== Remote restore/* branches =="
git fetch --prune >/dev/null 2>&1 || true
git branch -r | grep -E '^  origin/restore/' || echo "(none)"
