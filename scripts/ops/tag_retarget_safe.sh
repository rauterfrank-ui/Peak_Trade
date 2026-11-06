#!/usr/bin/env bash
set -euo pipefail

# Safe tag retarget: move an annotated tag to a new target (e.g. after squash-merge).
# Fetches remote state, recreates tag locally, and only force-pushes when remote differs.
# Why --force-with-lease can fail for tags: after deleting and recreating the tag locally,
# the new tag object has a different SHA; the lease (expected remote value) may still
# refer to the old object or be lost, so git reports "stale info" and refuses the push.
# This helper uses an explicit precheck instead.

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: $0 <TAG> <TARGET_REF>"
  echo "  Retarget an annotated tag to TARGET_REF (commit), then push."
  echo "  Only forces push if remote tag object differs from the new local one."
  exit 0
fi

TAG="${1:?tag name required}"
TARGET="${2:?target ref required}"

git fetch origin --prune --tags >/dev/null

local_target="$(git rev-parse "$TARGET")"

echo "[info] retarget tag: $TAG -> $local_target"

# show remote state (may be absent)
remote_lines="$(git ls-remote --tags origin "refs/tags/$TAG" 2>/dev/null || true)"
if [[ -n "$remote_lines" ]]; then
  echo "[info] remote before:"
  echo "$remote_lines"
else
  echo "[info] remote before: <absent>"
fi

# recreate tag locally (annotated)
git tag -d "$TAG" >/dev/null 2>&1 || true
git tag -a "$TAG" -m "retarget: $TAG -> $local_target" "$local_target"

# push with lease-like precheck: only force if remote differs
remote_sha="$(git ls-remote --tags origin "refs/tags/$TAG" 2>/dev/null | awk 'NR==1{print $1}')"
local_tag_obj="$(git rev-parse "refs/tags/$TAG")"

echo "[info] local tag object: $local_tag_obj"
echo "[info] remote tag object: ${remote_sha:-<absent>}"

if [[ -n "${remote_sha:-}" && "$remote_sha" != "$local_tag_obj" ]]; then
  echo "[warn] remote tag object differs; forcing update"
  git push --force origin "refs/tags/$TAG"
else
  git push origin "refs/tags/$TAG"
fi

echo "[ok] pushed."
echo "[info] remote after:"
git ls-remote --tags origin "refs/tags/$TAG" 2>/dev/null || true
