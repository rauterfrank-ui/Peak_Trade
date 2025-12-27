#!/usr/bin/env bash
set -euo pipefail

CI_FILE=".github/workflows/ci.yml"

die() { echo "❌ $*" >&2; exit 1; }
ok()  { echo "✅ $*"; }

[[ -f "$CI_FILE" ]] || die "Missing $CI_FILE"

# Helper: extract a job block by job id at 2-space indentation under jobs:
extract_job_block() {
  local job_id="$1"
  awk -v id="$job_id" '
    BEGIN { in_block = 0 }
    $0 ~ ("^  " id ":[[:space:]]*$") { in_block = 1; print; next }
    in_block == 1 && /^  [A-Za-z0-9_.-]+:[[:space:]]*$/ && $0 !~ ("^  " id ":[[:space:]]*$") { exit }
    in_block == 1 { print }
  ' "$CI_FILE"
}

tests_block="$(extract_job_block "tests" || true)"
[[ -n "${tests_block}" ]] || die "Job 'tests' not found in $CI_FILE"

# 1) Ensure matrix check names are versioned: tests (${{ matrix.python-version }})
echo "$tests_block" | grep -Eq '^[[:space:]]+name:[[:space:]]*tests[[:space:]]*\(\$\{\{[[:space:]]*matrix\.python-version[[:space:]]*\}\}\)' \
  || die "Job 'tests' must set: name: tests (\${{ matrix.python-version }})"

# 2) Guard against job-level if on tests (4-space indentation)
#    Step-level if is deeper (typically 8+ spaces), so this catches the problematic one.
echo "$tests_block" | grep -Eq '^    if:[[:space:]]' \
  && die "Job-level if detected on 'tests'. Required contexts may go missing. Use step-level gating instead."

ok "tests job naming + no job-level if: OK"

# strategy-smoke is commonly required too
smoke_block="$(extract_job_block "strategy-smoke" || true)"
if [[ -n "${smoke_block}" ]]; then
  # Avoid job-level if here too (same missing-context pitfall)
  echo "$smoke_block" | grep -Eq '^    if:[[:space:]]' \
    && die "Job-level if detected on 'strategy-smoke'. If it's required, contexts may go missing. Use step-level gating instead."
  ok "strategy-smoke no job-level if: OK"
else
  echo "ℹ️  Job 'strategy-smoke' not found (skipping guard for it)."
fi

# Optional: ensure 'changes' job exists (for docs-only detection design)
changes_block="$(extract_job_block "changes" || true)"
[[ -n "${changes_block}" ]] || echo "ℹ️  Job 'changes' not found (ok if you don't use docs-only gating)."

ok "CI required context contract looks good."
