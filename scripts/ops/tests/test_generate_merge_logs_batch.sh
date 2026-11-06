#!/usr/bin/env bash
#
# test_generate_merge_logs_batch.sh - Offline self-test for merge log batch generator
#
# Tests dry-run and keep-going semantics using a stubbed gh CLI (no network/auth required).

set -uo pipefail  # Note: removed -e to allow test failures without exiting

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GENERATOR="$REPO_ROOT/scripts/ops/generate_merge_logs_batch.sh"

FAILED=0
PASSED=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pass() {
  echo "✅ $1"
  ((PASSED++))
}

fail() {
  echo "❌ $1"
  ((FAILED++))
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Stub gh CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
setup_stub_gh() {
  local stub_dir
  stub_dir="$(mktemp -d)"

  cat > "$stub_dir/gh" <<'STUB'
#!/usr/bin/env bash
# Stub gh CLI for offline testing

handle_pr_view() {
  shift  # skip 'view'

  # Parse args
  pr_num=""
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      --json)
        shift  # skip --json
        shift  # skip fields (title,mergedAt,mergeCommit)
        ;;
      *)
        pr_num="$1"
        shift
        ;;
    esac
  done

  # Simulate known PRs
  case "$pr_num" in
    281)
      cat <<JSON
{
  "title": "Test PR 281",
  "mergedAt": "2025-12-24T10:00:00Z",
  "mergeCommit": {
    "oid": "abc1234567890123456789012345678901234567"
  }
}
JSON
      exit 0
      ;;
    999)
      echo "ERROR: PR not found" >&2
      exit 1
      ;;
    *)
      # Generic PR
      cat <<JSON
{
  "title": "Generic PR $pr_num",
  "mergedAt": "2025-12-24T10:00:00Z",
  "mergeCommit": {
    "oid": "def0000000000000000000000000000000000000"
  }
}
JSON
      exit 0
      ;;
  esac
}

case "$1" in
  auth)
    # Always pass auth check
    exit 0
    ;;
  pr)
    shift
    case "$1" in
      view)
        handle_pr_view "$@"
        ;;
      checks)
        echo "All checks passed (stub)"
        exit 0
        ;;
    esac
    ;;
esac

exit 0
STUB

  chmod +x "$stub_dir/gh"
  echo "$stub_dir"
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Merge Log Batch Generator - Offline Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Setup
STUB_DIR="$(setup_stub_gh)"
export PATH="$STUB_DIR:$PATH"

# ──────────────────────────────────────────────────────────
# Test 1: --help flag
# ──────────────────────────────────────────────────────────
if bash "$GENERATOR" --help >/dev/null 2>&1; then
  pass "Test 1: --help flag works"
else
  fail "Test 1: --help flag failed"
fi

# ──────────────────────────────────────────────────────────
# Test 2: --dry-run produces no files
# ──────────────────────────────────────────────────────────
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
git init -q .

mkdir -p docs/ops
cat > docs/ops/README.md <<'EOF'
# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

cat > docs/ops/MERGE_LOG_WORKFLOW.md <<'EOF'
# Test Workflow
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

# Run dry-run (with stub gh in PATH)
OUTPUT=$(PATH="$STUB_DIR:$PATH" bash "$GENERATOR" --dry-run 281 2>&1 || true)
EXIT_CODE=$?

if [[ "$EXIT_CODE" -eq 0 ]]; then
  # Check no new files created
  if [[ ! -f "docs/ops/PR_281_MERGE_LOG.md" ]]; then
    pass "Test 2: --dry-run produces no files"
  else
    fail "Test 2: --dry-run created files (should not)"
  fi
else
  fail "Test 2: --dry-run command failed (exit $EXIT_CODE)"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TMPDIR"

# ──────────────────────────────────────────────────────────
# Test 3: --keep-going collects failures
# ──────────────────────────────────────────────────────────
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
git init -q .

mkdir -p docs/ops
cat > docs/ops/README.md <<'EOF'
# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

cat > docs/ops/MERGE_LOG_WORKFLOW.md <<'EOF'
# Test Workflow
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

# Run with keep-going (281 succeeds, 999 fails)
OUTPUT="$(PATH="$STUB_DIR:$PATH" bash "$GENERATOR" --keep-going 281 999 2>&1 || true)"

if echo "$OUTPUT" | grep -q "Failures"; then
  if echo "$OUTPUT" | grep -q "999"; then
    pass "Test 3: --keep-going collects failures"
  else
    fail "Test 3: --keep-going didn't report PR 999 failure"
  fi
else
  fail "Test 3: --keep-going didn't show failure summary"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TMPDIR"

# ──────────────────────────────────────────────────────────
# Test 4: Fail-fast without --keep-going
# ──────────────────────────────────────────────────────────
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
git init -q .

mkdir -p docs/ops
cat > docs/ops/README.md <<'EOF'
# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

cat > docs/ops/MERGE_LOG_WORKFLOW.md <<'EOF'
# Test Workflow
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

# Run without keep-going (should fail on 999 and not process further)
if PATH="$STUB_DIR:$PATH" bash "$GENERATOR" 999 281 >/dev/null 2>&1; then
  fail "Test 4: should have failed on PR 999"
else
  pass "Test 4: fail-fast works (exited on first failure)"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TMPDIR"

# ──────────────────────────────────────────────────────────
# Test 5: Successful run creates files
# ──────────────────────────────────────────────────────────
TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
git init -q .

mkdir -p docs/ops
cat > docs/ops/README.md <<'EOF'
# Test README
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

cat > docs/ops/MERGE_LOG_WORKFLOW.md <<'EOF'
# Test Workflow
<!-- MERGE_LOG_EXAMPLES:START -->
<!-- MERGE_LOG_EXAMPLES:END -->
EOF

# Run without dry-run
if PATH="$STUB_DIR:$PATH" bash "$GENERATOR" 281 >/dev/null 2>&1; then
  if [[ -f "docs/ops/PR_281_MERGE_LOG.md" ]]; then
    pass "Test 5: successful run creates merge log file"
  else
    fail "Test 5: merge log file not created"
  fi
else
  fail "Test 5: generator command failed"
fi

# Cleanup
cd - >/dev/null
rm -rf "$TMPDIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cleanup stub
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rm -rf "$STUB_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary: $PASSED passed, $FAILED failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$FAILED" -gt 0 ]]; then
  exit 1
fi

exit 0
