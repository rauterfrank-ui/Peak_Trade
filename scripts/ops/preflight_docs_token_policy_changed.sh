#!/usr/bin/env bash
#
# preflight_docs_token_policy_changed.sh — Local pre-PR docs token policy check
#
# Thin wrapper around scripts/ops/validate_docs_token_policy.py.
# Scans changed Markdown files vs merge-base (default: origin/main).
#
# NO-LIVE: local/git only — no brokers, orders, execution, or autofix by default.
#
# Usage:
#   ./scripts/ops/preflight_docs_token_policy_changed.sh [BASE_REF]
#
# Exit codes (delegated from validator):
#   0 — pass (or no changed Markdown)
#   1 — policy violations
#   2 — script error

set -euo pipefail

die() {
  echo "ERROR: $*" >&2
  exit 2
}

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "${ROOT}" ]] || die "not in a git repository"
cd "${ROOT}"

BASE_REF="${1:-origin/main}"

git fetch origin --prune >/dev/null 2>&1 || true

echo "== Docs token policy preflight (changed .md vs ${BASE_REF}) =="

VALIDATOR="scripts/ops/validate_docs_token_policy.py"
[[ -f "${VALIDATOR}" ]] || die "missing validator: ${VALIDATOR}"

run_validator() {
  if command -v uv >/dev/null 2>&1; then
    uv run python "${VALIDATOR}" --base "${BASE_REF}"
  else
    python3 "${VALIDATOR}" --base "${BASE_REF}"
  fi
}

if run_validator; then
  echo "OK: docs token policy preflight passed"
  exit 0
fi

EXIT_CODE=$?
echo "" >&2
echo "Docs token policy preflight FAILED." >&2
echo "Illustrative inline-code path tokens in Markdown must encode '/' as '&#47;'." >&2
echo "Examples: \`GET &#47;observability\`, \`readmodels&#47;file.json\`, \`BTC&#47;USD\`" >&2
echo "See: docs/ops/runbooks/RUNBOOK_DOCS_TOKEN_POLICY_GATE.md" >&2
echo "Optional dry-run fix: scripts/ops/autofix_docs_token_policy_inline_code_v2.py --dry-run <files>" >&2
exit "${EXIT_CODE}"
