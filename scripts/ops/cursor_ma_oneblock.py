import sys

msg = sys.stdin.read().rstrip("\n")

print(
    f"""set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

printf "%s\\n" "CONTEXT: REPO ROOT + CURRENT BRANCH"
git rev-parse --show-toplevel
git status -sb
git log -1 --oneline

printf "%s\\n" "INPUT (USER STATUS)"
cat <<'MSG'
{msg}
MSG

printf "%s\\n" "CURSOR MULTI-AGENT ORCHESTRATOR: NEXT ACTIONS (single consolidated block)"
if command -v gh >/dev/null 2>&1; then
  head_branch=$(git rev-parse --abbrev-ref HEAD)
  pr=$(gh pr list --head "$head_branch" --json number --jq '.[0].number' 2>/dev/null || true)
  if [ -n "$pr" ]; then
    gh pr view "$pr" --json number,state,baseRefName,headRefName,mergeable,reviewDecision --jq '.'
    gh pr checks "$pr" || true
  else
    printf "%s\\n" "No PR found for head=$head_branch. Create one:"
    gh pr create --base main --head "$head_branch" --fill || true
  fi
else
  printf "%s\\n" "gh not available; use repo scripts or UI for PR/checks."
fi
"""
)
