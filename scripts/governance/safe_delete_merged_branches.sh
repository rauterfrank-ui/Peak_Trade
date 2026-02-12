#!/usr/bin/env bash
# Safe delete of remote branches: only when branch tip is ancestor of origin/main
# and branch is NOT the head of an open PR.
# Policy: DELETE_SAFE = ancestor of main + not open PR; KEEP_REVIEW = ahead>0 or open PR.
set -euo pipefail

# --- args ---
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<'EOF'
Usage:
  safe_delete_merged_branches.sh [--dry-run]

Flags:
  --dry-run   Do not delete remote branches; only report what would be deleted.
EOF
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      echo "Run with --help for usage." >&2
      exit 2
      ;;
  esac
done

cd "$(git rev-parse --show-toplevel)"
REPO_SLUG="${GITHUB_REPO_SLUG:-}"
if [[ -z "$REPO_SLUG" ]]; then
  origin_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ "$origin_url" =~ github\.com[:/]([^/]+/[^/.]+) ]]; then
    REPO_SLUG="${BASH_REMATCH[1]%.git}"
  else
    REPO_SLUG="rauterfrank-ui/Peak_Trade"
  fi
fi

echo "[Phase 0] Preflight"
git status -sb
git fetch origin --prune --tags
git checkout main
git pull --ff-only origin main

mkdir -p out/ops

echo "[Phase 1] Open PR head branches (GitHub API)"
python3 -c '
import json, os, sys, urllib.request
repo = os.environ.get("GITHUB_REPO_SLUG", "'"$REPO_SLUG"'")
url = f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=100"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
tok = os.environ.get("GITHUB_TOKEN")
if tok:
    req.add_header("Authorization", f"Bearer {tok}")
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        prs = json.load(r)
    heads = sorted({pr["head"]["ref"] for pr in prs})
    print("\n".join(heads))
except Exception as e:
    sys.stderr.write(f"Warning: could not fetch open PRs: {e}\n")
' > out/ops/open_pr_head_refs.txt || true

echo "[Phase 2] Compute DELETE_SAFE candidates (ancestor of origin/main, not PR-head)"
git for-each-ref --format='%(refname:short)' refs/remotes/origin \
  | sed 's|^origin/||' \
  | grep -v -E '^(HEAD|main)$' \
  | while read -r b; do
      if git merge-base --is-ancestor "refs/remotes/origin/$b" "refs/remotes/origin/main" 2>/dev/null; then
        echo "$b"
      fi
    done \
  > out/ops/remote_delete_safe_raw.txt

sort -u out/ops/remote_delete_safe_raw.txt > out/ops/remote_delete_safe_raw.sorted.txt

if [[ -s out/ops/open_pr_head_refs.txt ]]; then
  sort -u out/ops/open_pr_head_refs.txt > out/ops/open_pr_head_refs.sorted.txt
  comm -23 out/ops/remote_delete_safe_raw.sorted.txt out/ops/open_pr_head_refs.sorted.txt \
    > out/ops/remote_delete_safe.final.txt
else
  cp out/ops/remote_delete_safe_raw.sorted.txt out/ops/remote_delete_safe.final.txt
fi

DELETE_SAFE_FINAL="out/ops/remote_delete_safe.final.txt"
echo "DELETE_SAFE (remote) candidates:"
sed -n '1,200p' "$DELETE_SAFE_FINAL"

echo "[Phase 3] Delete DELETE_SAFE branches on origin"
if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY_RUN=1: skipping deletion. Would delete:"
  sed -n '1,200p' "$DELETE_SAFE_FINAL" || true
else
  while IFS= read -r b; do
    [ -n "$b" ] || continue
    git push origin --delete "$b"
  done < "$DELETE_SAFE_FINAL"
fi

echo "[Phase 4] Post-verify"
git fetch origin --prune
echo "Remaining remote branches (origin/*):"
git branch -r | sed 's|^  ||' | sed -n '1,200p'

echo "[Phase 5] KEEP_REVIEW report (branch behind ahead)"
python3 -c '
import subprocess, sys
def sh(*args):
    return subprocess.check_output(args, text=True).strip()
raw = sh("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").splitlines()
bs = [r.split("/", 1)[1] for r in raw if r.startswith("origin/") and r not in ("origin/HEAD", "origin/main")]
rows = []
for b in sorted(bs):
    out = sh("git", "rev-list", "--left-right", "--count", "refs/remotes/origin/main...refs/remotes/origin/" + b)
    behind, ahead = out.split()
    rows.append((b, int(behind), int(ahead)))
print("\n".join(f"{b}\t{behind}\t{ahead}" for b, behind, ahead in rows))
' > out/ops/remote_branches_ahead_behind.tsv

echo "KEEP_REVIEW report (branch behind ahead):"
sed -n '1,200p' out/ops/remote_branches_ahead_behind.tsv

echo "[Done] Optional: archive then delete branches with ahead>0:"
echo "  B=\"wip/some-branch\""
echo "  git tag \"archive/\${B//\\//-}\" \"refs/remotes/origin/\$B\""
echo "  git push origin \"archive/\${B//\\//-}\""
echo "  git push origin --delete \"\$B\""
