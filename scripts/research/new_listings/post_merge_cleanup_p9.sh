#!/usr/bin/env bash
# Post-merge cleanup: main up to date, delete local + remote feature branch.
# Run after PR feat/new-listings-p9-normalize-ccxt-tickers is merged.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git checkout main
git fetch origin --prune
git pull --ff-only origin main

# Sanity: merged P9 commits on main
git log -n 80 --oneline | grep -E "P9 normalize ccxt|cex:|ccxt_ticker|new_listings" || true

# Remove local branch
git branch -D feat/new-listings-p9-normalize-ccxt-tickers || true

# Remove remote branch if it exists
if git ls-remote --heads origin feat/new-listings-p9-normalize-ccxt-tickers >/dev/null 2>&1; then
  git push origin --delete feat/new-listings-p9-normalize-ccxt-tickers
fi

git status -sb
