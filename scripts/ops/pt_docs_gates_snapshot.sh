#!/usr/bin/env bash
#
# pt_docs_gates_snapshot.sh — Peak_Trade Docs Gates Snapshot Helper
#
# Purpose:
#   Single entry-point for local reproduction of all 3 Docs CI Gates:
#   - Docs Token Policy Gate
#   - Docs Reference Targets Gate
#   - Docs Diff Guard Policy Gate
#
# Constraints:
#   - Snapshot-only (NO watch loops, NO polling)
#   - Clear PASS/FAIL output with next actions
#   - No abrupt exits; return codes + context
#   - Pre-flight guards for safety
#
# Usage:
#   ./scripts/ops/pt_docs_gates_snapshot.sh [OPTIONS]
#
# Options:
#   --changed       Run in "changed files" mode (default: against origin/main)
#   --all           Run full repo scan (slow, ~30s)
#   --base <ref>    Base ref for --changed mode (default: origin/main)
#   -h, --help      Show this help
#
# Exit Codes:
#   0 = All gates passed
#   1 = One or more gates failed
#   2 = Error (invalid args, missing dependencies)
#
# Examples:
#   # Quick check (PR workflow)
#   ./scripts/ops/pt_docs_gates_snapshot.sh --changed
#
#   # Full repo audit
#   ./scripts/ops/pt_docs_gates_snapshot.sh --all
#
#   # Against specific branch
#   ./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/develop

set -euo pipefail

# ============================================================================
# PRE-FLIGHT: Terminal Safety Guards
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Peak_Trade Docs Gates Snapshot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ℹ️  If stuck in prompt (> or dquote>), press Ctrl-C to abort."
echo ""

# ============================================================================
# DEFAULTS & ARG PARSING
# ============================================================================

MODE="changed"  # "changed" or "all"
BASE_REF="origin/main"
SHOW_HELP=0

usage() {
  cat <<'EOF'
pt_docs_gates_snapshot.sh — Docs Gates Local Reproduction

SNAPSHOT-ONLY (no watch loops)

Usage:
  ./scripts/ops/pt_docs_gates_snapshot.sh [OPTIONS]

Options:
  --changed       Check changed files only (fast, PR mode) [default]
  --all           Full repo scan (slow, ~30s)
  --base <ref>    Base ref for --changed mode (default: origin/main)
  -h, --help      Show this help

Exit Codes:
  0 = All gates passed
  1 = One or more gates failed
  2 = Error (invalid args, missing tools)

Examples:
  # PR workflow (default)
  ./scripts/ops/pt_docs_gates_snapshot.sh --changed

  # Full audit
  ./scripts/ops/pt_docs_gates_snapshot.sh --all

  # Custom base branch
  ./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/develop

Gates Checked:
  1. Docs Token Policy Gate       (uv run python)
  2. Docs Reference Targets Gate  (bash)
  3. Docs Diff Guard Policy Gate  (python3)

Dependencies:
  - uv (for Token Policy Gate)
  - python3 (for Diff Guard Policy Gate)
  - bash, git

See also:
  - docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md
  - docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md
  - docs/ops/runbooks/RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --changed) MODE="changed"; shift ;;
    --all) MODE="all"; shift ;;
    --base) BASE_REF="${2:-}"; [[ -n "$BASE_REF" ]] || { echo "❌ Missing value for --base"; exit 2; }; shift 2 ;;
    -h|--help) SHOW_HELP=1; shift ;;
    *) echo "❌ Unknown argument: $1"; usage; exit 2 ;;
  esac
done

if [[ "$SHOW_HELP" == "1" ]]; then
  usage
  exit 0
fi

# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

echo "📍 Pre-Flight Checks"
echo "───────────────────────────────────────────────────────────────────────"

# Check we're in a git repo
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "❌ Not in a git repository"
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "   Repo Root:    $REPO_ROOT"
echo "   Current Dir:  $(pwd)"
echo "   Branch:       $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'DETACHED')"
echo "   Mode:         $MODE"
if [[ "$MODE" == "changed" ]]; then
  echo "   Base Ref:     $BASE_REF"
fi
echo ""

# Check dependencies
MISSING_DEPS=()
command -v uv >/dev/null 2>&1 || MISSING_DEPS+=("uv")
command -v python3 >/dev/null 2>&1 || MISSING_DEPS+=("python3")

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
  echo "❌ Missing dependencies: ${MISSING_DEPS[*]}"
  echo "   Install: pip install uv  (or see docs/ops/README.md)"
  exit 2
fi

echo "✅ All dependencies present"
echo ""

# ============================================================================
# GATE 1: DOCS TOKEN POLICY GATE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Gate 1/3: Docs Token Policy Gate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

GATE1_STATUS=0
GATE1_CMD="uv run python scripts/ops/validate_docs_token_policy.py"

if [[ "$MODE" == "changed" ]]; then
  GATE1_CMD="$GATE1_CMD --changed --base $BASE_REF"
elif [[ "$MODE" == "all" ]]; then
  GATE1_CMD="$GATE1_CMD --all"
fi

echo "📋 Command: $GATE1_CMD"
echo ""

if $GATE1_CMD; then
  echo ""
  echo "✅ Docs Token Policy Gate: PASS"
  GATE1_STATUS=0
else
  EXIT_CODE=$?
  echo ""
  echo "❌ Docs Token Policy Gate: FAIL (exit code: $EXIT_CODE)"
  echo ""
  echo "📖 Next Actions:"
  echo "   1. Review violations above"
  echo "   2. Fix: Encode illustrative paths with &#47; (e.g., \`scripts&#47;example.py\`)"
  echo "   3. Re-run: $GATE1_CMD"
  echo "   4. See: docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md"
  GATE1_STATUS=1
fi

echo ""

# ============================================================================
# GATE 2: DOCS REFERENCE TARGETS GATE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Gate 2/3: Docs Reference Targets Gate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

GATE2_STATUS=0
GATE2_CMD="bash scripts/ops/verify_docs_reference_targets.sh"

if [[ "$MODE" == "changed" ]]; then
  GATE2_CMD="$GATE2_CMD --changed --base $BASE_REF"
fi

echo "📋 Command: $GATE2_CMD"
echo ""

if $GATE2_CMD; then
  echo ""
  echo "✅ Docs Reference Targets Gate: PASS"
  GATE2_STATUS=0
else
  EXIT_CODE=$?
  echo ""
  echo "❌ Docs Reference Targets Gate: FAIL (exit code: $EXIT_CODE)"
  echo ""
  echo "📖 Next Actions:"
  echo "   1. Review missing targets above"
  echo "   2. Fix:"
  echo "      - Real file renamed/moved: Update docs to new path"
  echo "      - Illustrative example: Encode with &#47; (e.g., \`config&#47;example.toml\`)"
  echo "      - Typo: Correct the path"
  echo "   3. Re-run: $GATE2_CMD"
  echo "   4. See: docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md"
  GATE2_STATUS=1
fi

echo ""

# ============================================================================
# GATE 3: DOCS DIFF GUARD POLICY GATE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Gate 3/3: Docs Diff Guard Policy Gate"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

GATE3_STATUS=0
GATE3_CMD="python3 scripts/ci/check_docs_diff_guard_section.py"

echo "📋 Command: $GATE3_CMD"
echo ""

if $GATE3_CMD; then
  echo ""
  echo "✅ Docs Diff Guard Policy Gate: PASS"
  GATE3_STATUS=0
else
  EXIT_CODE=$?
  echo ""
  echo "❌ Docs Diff Guard Policy Gate: FAIL (exit code: $EXIT_CODE)"
  echo ""
  echo "📖 Next Actions:"
  echo "   1. Review missing marker files above"
  echo "   2. Fix: python3 scripts/ops/insert_docs_diff_guard_section.py --files <path>"
  echo "   3. Re-run: $GATE3_CMD"
  echo "   4. See: docs/ops/runbooks/RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md"
  GATE3_STATUS=1
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL_FAIL=$((GATE1_STATUS + GATE2_STATUS + GATE3_STATUS))

if [[ "$GATE1_STATUS" == "0" ]]; then
  echo "   ✅ Docs Token Policy Gate"
else
  echo "   ❌ Docs Token Policy Gate"
fi

if [[ "$GATE2_STATUS" == "0" ]]; then
  echo "   ✅ Docs Reference Targets Gate"
else
  echo "   ❌ Docs Reference Targets Gate"
fi

if [[ "$GATE3_STATUS" == "0" ]]; then
  echo "   ✅ Docs Diff Guard Policy Gate"
else
  echo "   ❌ Docs Diff Guard Policy Gate"
fi

echo ""

if [[ "$TOTAL_FAIL" == "0" ]]; then
  echo "🎉 All gates passed! Docs changes are merge-ready."
  echo ""
  echo "📖 Next Steps:"
  echo "   - Commit your changes: git add . && git commit"
  echo "   - Push and create PR: git push -u origin <branch>"
  echo "   - CI will run the same checks automatically"
  echo ""
  exit 0
else
  echo "⚠️  $TOTAL_FAIL gate(s) failed. Review actions above and re-run."
  echo ""
  echo "📖 Quick Fixes:"
  echo "   - Token Policy:     Encode illustrative paths with &#47;"
  echo "   - Reference Targets: Update broken paths or encode illustrative ones"
  echo "   - Diff Guard:       Insert policy marker with insertion script"
  echo ""
  echo "📚 Runbooks:"
  echo "   - docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE_OPERATOR.md"
  echo "   - docs/ops/runbooks/RUNBOOK_DOCS_REFERENCE_TARGETS_GATE_OPERATOR.md"
  echo "   - docs/ops/runbooks/RUNBOOK_DOCS_DIFF_GUARD_POLICY_GATE_OPERATOR.md"
  echo ""
  exit 1
fi
