#!/usr/bin/env bash
# CI trigger tool: create a temporary branch with a no-op change + revert, open PR to trigger required checks.
# Final merged tree is unchanged (no marker leakage).
set -euo pipefail

cd "$(cd "$(dirname "$0")/../.." && pwd)"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: working tree not clean" >&2
  exit 2
fi

if [ -n "$(git ls-files reports/ 2>/dev/null || true)" ]; then
  echo "ERROR: tracked files under reports/ (refuse)" >&2
  exit 3
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="${1:-src/__init__.py}"
BR="feat/ci-trigger-required-checks-${STAMP}"

test -f "${TARGET}" || { echo "ERROR: target missing: ${TARGET}" >&2; exit 4; }

git checkout -b "${BR}"

python3 - <<PY
from pathlib import Path
p = Path("${TARGET}")
t = p.read_text(encoding="utf-8").splitlines()
line = "CI_TRIGGER_REQUIRED_CHECKS = '${STAMP}'"
if line not in t:
    t.append(line)
p.write_text("\n".join(t).rstrip("\n") + "\n", encoding="utf-8")
print("added", line)
PY

git add "${TARGET}"
git commit -m "ci: trigger required checks (${STAMP})"

git revert --no-edit HEAD

git push -u origin HEAD

./scripts/ops/pr_safe_flow.sh create --fill
PT_CONFIRM_MERGE=YES ./scripts/ops/pr_safe_flow.sh automerge --squash --delete-branch
./scripts/ops/pr_safe_flow.sh status
