set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/frnkhrz/Peak_Trade}"
cd "${REPO_ROOT}"

echo "GIT-KONTEXT: main (preflight)"
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb

SRC_COMMIT="${1:-}"
SRC_PATH="${2:-}"
DST_PATH="${3:-}"
BRANCH_SLUG="${4:-docs/restore-todo}"

if [ -z "${SRC_COMMIT}" ] || [ -z "${SRC_PATH}" ] || [ -z "${DST_PATH}" ]; then
  echo "USAGE: scripts/ops/restore_todo_to_docs.sh <src_commit> <src_path> <dst_path> [branch]"
  echo "EXAMPLE: scripts/ops/restore_todo_to_docs.sh 5fa7a405 out/ops/todos/P4C_TODO_20260219T064354Z.md docs/ops/todos/P4C_TODO_20260219T064354Z.md docs/persist-p4c-todo"
  exit 2
fi

echo "GIT-KONTEXT: main (restore file content into dst)"
mkdir -p "$(dirname "${DST_PATH}")"
git show "${SRC_COMMIT}:${SRC_PATH}" > "${DST_PATH}"

echo "GIT-KONTEXT: main (no-op guard: only proceed if dst changed vs HEAD)"
if git diff --quiet -- "${DST_PATH}"; then
  echo "NO_CHANGES: ${DST_PATH} already matches HEAD; nothing to do."
  exit 0
fi

echo "GIT-KONTEXT: ${BRANCH_SLUG} (commit + PR safe flow)"
git checkout -b "${BRANCH_SLUG}"

git add "${DST_PATH}"
git commit -m "docs(todos): restore $(basename "${DST_PATH}") from ${SRC_COMMIT}"
git push -u origin HEAD

./scripts/ops/pr_safe_flow.sh create --fill
PT_CONFIRM_MERGE=YES ./scripts/ops/pr_safe_flow.sh automerge --squash --delete-branch
./scripts/ops/pr_safe_flow.sh status
