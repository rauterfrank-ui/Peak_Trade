#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# verify_format_only_pr.sh — Format-Only PR Verifier (Strict)
# ────────────────────────────────────────────────────────────────────────────
# Purpose: Deterministic check whether a PR contains ONLY formatting changes.
#
# Usage:
#   ./scripts/ops/verify_format_only_pr.sh <base_sha> <head_sha>
#
# Strategy:
#   1. Validate: only Modified files (no Add/Delete/Rename)
#   2. Validate: only allowed file extensions
#   3. Create two git worktrees (base and head)
#   4. Apply canonical formatter in both worktrees
#   5. Compare resulting tree hashes
#   6. If trees match => FORMAT_ONLY (exit 0)
#   7. If trees differ => NOT FORMAT_ONLY (exit 1)
#
# Exit Codes:
#   0 = Format-only confirmed
#   1 = Not format-only (or validation failed)
# ────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────
# Config
# ────────────────────────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS=".py .md .toml .yml .yaml .json .ini .cfg .txt .sh"
TEMP_BASE="$(mktemp -d)/base_worktree"
TEMP_HEAD="$(mktemp -d)/head_worktree"

# ────────────────────────────────────────────────────────────────────────────
# Cleanup trap
# ────────────────────────────────────────────────────────────────────────────

cleanup() {
  echo ""
  echo "🧹 Cleanup..."
  if [ -d "$TEMP_BASE" ]; then
    git worktree remove "$TEMP_BASE" --force 2>/dev/null || true
  fi
  if [ -d "$TEMP_HEAD" ]; then
    git worktree remove "$TEMP_HEAD" --force 2>/dev/null || true
  fi
}
trap cleanup EXIT

# ────────────────────────────────────────────────────────────────────────────
# Args
# ────────────────────────────────────────────────────────────────────────────

if [ $# -ne 2 ]; then
  echo "❌ Usage: $0 <base_sha> <head_sha>" >&2
  exit 1
fi

BASE_SHA="$1"
HEAD_SHA="$2"

echo "════════════════════════════════════════════════════════════════════════"
echo "🔍 Format-Only PR Verifier (Strict)"
echo "════════════════════════════════════════════════════════════════════════"
echo "Base SHA: $BASE_SHA"
echo "Head SHA: $HEAD_SHA"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# Step 1: Validate commit SHAs
# ────────────────────────────────────────────────────────────────────────────

echo "▸ Validating commit SHAs..."
if ! git rev-parse --verify "$BASE_SHA" >/dev/null 2>&1; then
  echo "❌ Base SHA not found: $BASE_SHA" >&2
  exit 1
fi
if ! git rev-parse --verify "$HEAD_SHA" >/dev/null 2>&1; then
  echo "❌ Head SHA not found: $HEAD_SHA" >&2
  exit 1
fi
echo "  ✅ SHAs valid"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# Step 2: Check file status (only Modified allowed)
# ────────────────────────────────────────────────────────────────────────────

echo "▸ Checking file status (only Modified allowed)..."
CHANGED_FILES=$(git diff --name-status "$BASE_SHA" "$HEAD_SHA")
echo "$CHANGED_FILES"
echo ""

if echo "$CHANGED_FILES" | grep -q '^[ADR]'; then
  echo "❌ FAIL: PR contains Added/Deleted/Renamed files (not format-only)" >&2
  echo ""
  echo "Changed files:"
  echo "$CHANGED_FILES" | grep '^[ADR]' >&2
  echo ""
  echo "🛡️ Recommendation: Remove label 'ops/format-only' from PR"
  exit 1
fi
echo "  ✅ Only Modified files"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# Step 3: Check file extensions (allowlist)
# ────────────────────────────────────────────────────────────────────────────

echo "▸ Checking file extensions (allowlist: $ALLOWED_EXTENSIONS)..."
MODIFIED_FILES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
INVALID_FILES=""

for file in $MODIFIED_FILES; do
  ext="${file##*.}"
  # Handle files without extension (e.g., Makefile, Dockerfile)
  if [ "$ext" = "$file" ]; then
    # Check if it's a known extensionless file
    basename=$(basename "$file")
    if [[ "$basename" =~ ^(Makefile|Dockerfile|LICENSE|README)$ ]]; then
      continue
    else
      INVALID_FILES="${INVALID_FILES}${file}\n"
    fi
  elif ! echo "$ALLOWED_EXTENSIONS" | grep -qw ".$ext"; then
    INVALID_FILES="${INVALID_FILES}${file}\n"
  fi
done

if [ -n "$INVALID_FILES" ]; then
  echo "❌ FAIL: Files with non-allowed extensions detected:" >&2
  echo -e "$INVALID_FILES" >&2
  echo ""
  echo "🛡️ Recommendation: Remove label 'ops/format-only' from PR"
  exit 1
fi
echo "  ✅ All files have allowed extensions"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# Step 4: Create worktrees
# ────────────────────────────────────────────────────────────────────────────

echo "▸ Creating temporary worktrees..."
git worktree add --detach "$TEMP_BASE" "$BASE_SHA" >/dev/null 2>&1
git worktree add --detach "$TEMP_HEAD" "$HEAD_SHA" >/dev/null 2>&1
echo "  ✅ Worktrees created"
echo "     Base: $TEMP_BASE"
echo "     Head: $TEMP_HEAD"
echo ""

# ────────────────────────────────────────────────────────────────────────────
# Step 5: Apply canonical formatter in both worktrees
# ────────────────────────────────────────────────────────────────────────────

apply_formatter() {
  local worktree_path="$1"
  local label="$2"

  echo "▸ Applying formatter in $label worktree..."
  cd "$worktree_path"

  # Check if uv is available
  if command -v uv >/dev/null 2>&1; then
    echo "  Using: uv run ruff format ."
    uv run ruff format . >/dev/null 2>&1 || {
      echo "  ⚠️  ruff format failed, trying black..."
      uv run black . >/dev/null 2>&1 || {
        echo "  ⚠️  black also failed, skipping formatting"
      }
    }
  else
    echo "  uv not found, trying ruff directly..."
    if command -v ruff >/dev/null 2>&1; then
      ruff format . >/dev/null 2>&1 || echo "  ⚠️  ruff format failed"
    elif command -v black >/dev/null 2>&1; then
      black . >/dev/null 2>&1 || echo "  ⚠️  black failed"
    else
      echo "  ⚠️  No formatter found (ruff/black), skipping"
    fi
  fi

  # Fix trailing whitespace and EOF (minimal)
  if command -v find >/dev/null 2>&1; then
    # Trailing whitespace
    find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" \) \
      -not -path "./.git/*" \
      -exec sed -i '' 's/[[:space:]]*$//' {} \; 2>/dev/null || true

    # Ensure EOF newline (Python, Markdown, YAML, TOML)
    find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" \) \
      -not -path "./.git/*" \
      -exec sh -c 'tail -c1 "$1" | read -r _ || echo >> "$1"' _ {} \; 2>/dev/null || true
  fi

  # Stage all changes
  git add -A

  # Create tree hash
  TREE_HASH=$(git write-tree)
  echo "  Tree hash: $TREE_HASH"
  echo ""

  cd - >/dev/null
  echo "$TREE_HASH"
}

BASE_TREE=$(apply_formatter "$TEMP_BASE" "base")
HEAD_TREE=$(apply_formatter "$TEMP_HEAD" "head")

# ────────────────────────────────────────────────────────────────────────────
# Step 6: Compare tree hashes
# ────────────────────────────────────────────────────────────────────────────

echo "▸ Comparing tree hashes..."
echo "  Base tree: $BASE_TREE"
echo "  Head tree: $HEAD_TREE"
echo ""

if [ "$BASE_TREE" = "$HEAD_TREE" ]; then
  echo "════════════════════════════════════════════════════════════════════════"
  echo "✅ FORMAT-ONLY CONFIRMED"
  echo "════════════════════════════════════════════════════════════════════════"
  echo "The PR contains ONLY formatting changes."
  echo "Tree hashes match after canonical formatting."
  echo ""
  echo "🛡️ Policy Critic may be skipped (guardrail satisfied)."
  echo "════════════════════════════════════════════════════════════════════════"
  exit 0
else
  echo "════════════════════════════════════════════════════════════════════════"
  echo "❌ NOT FORMAT-ONLY"
  echo "════════════════════════════════════════════════════════════════════════"
  echo "The PR contains NON-formatting changes."
  echo "Tree hashes differ after canonical formatting."
  echo ""
  echo "This indicates logic, config, or semantic changes beyond formatting."
  echo ""
  echo "🛡️ Recommendation:"
  echo "   1. Remove label 'ops/format-only' from PR"
  echo "   2. Policy Critic will run normally (no skip)"
  echo "   3. If this is a false positive, investigate diff manually"
  echo "════════════════════════════════════════════════════════════════════════"
  exit 1
fi
