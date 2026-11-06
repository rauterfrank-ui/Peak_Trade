#!/usr/bin/env bash
set -euo pipefail

# Safe "empty commit" retrigger for PR checks.
# Works without gh. Use when UI shows missing checks / rollup symptom.

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${BRANCH}" == "main" ]]; then
  echo "ERROR: refusing to retrigger on main"
  exit 2
fi

# require clean working tree
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree not clean. Commit/stash first."
  exit 3
fi

NOW_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
EVI="out/ops/ci_pr_retrigger_${BRANCH//\//_}_${NOW_UTC}"
mkdir -p "${EVI}"

echo "branch=${BRANCH}" | tee "${EVI}/META.txt"
git rev-parse HEAD | tee "${EVI}/HEAD_BEFORE.txt"
git log -n 5 --oneline --decorate | tee "${EVI}/LOG5_BEFORE.txt"

# Create empty commit
git commit --allow-empty -m "ci: retrigger PR checks (${NOW_UTC})" | tee "${EVI}/COMMIT_OUT.txt"

git rev-parse HEAD | tee "${EVI}/HEAD_AFTER.txt"
git log -n 5 --oneline --decorate | tee "${EVI}/LOG5_AFTER.txt"

# Push
git push -u origin HEAD | tee "${EVI}/PUSH_OUT.txt" || true

# Checksums
if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${EVI}"/* > "${EVI}/SHA256SUMS.txt" || true
fi

echo "OK: retriggered. evidence=${EVI}"
