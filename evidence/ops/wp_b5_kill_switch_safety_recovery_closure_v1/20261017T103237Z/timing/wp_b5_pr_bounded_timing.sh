#!/usr/bin/env bash
# Path-equivalent replay of ci.yml job "tests (3.11)" under PR_BOUNDED_FULL (run_matrix=true => fast-lane FULL_STATIC_CONTRACTS skipped).
set -uo pipefail
cd /private/tmp/peak_trade_wp_b5
OUT=/tmp/wp_b5_timing_pr_bounded
rm -rf "$OUT"; mkdir -p "$OUT"
START=$(date +%s)
RC_ALL=0
{
  echo "## step: Stability Smoke Tests (Fast Gate)"
  ./scripts/pt -m pytest tests/test_stability_smoke.py tests/test_data_contracts.py tests/test_error_taxonomy.py tests/test_resilience.py -m smoke -v --tb=short -p no:cacheprovider || RC_ALL=1
  echo "## step: Import and collection smoke"
  ./scripts/pt -c "import src" || RC_ALL=1
  ./scripts/pt -m pytest --collect-only -q tests/test_stability_smoke.py -p no:cacheprovider || RC_ALL=1
  echo "## step: Run PR_BOUNDED_FULL tests (matrix)"
  TARGETS="$(./scripts/pt scripts/ops/ci_test_selection_v1.py --files-file /tmp/wp_b5_final_files.txt --patch-file /tmp/wp_b5_final.patch --diff-base-ref origin/main --event-name pull_request | sed -n 's/^pr_bounded_pytest_targets=//p')"
  VALIDATED=()
  while IFS= read -r t; do [ -n "$t" ] && VALIDATED+=("$t"); done < <(./scripts/pt scripts/ops/ci_test_selection_v1.py --emit-validated-pytest-targets "$TARGETS")
  echo "PR_BOUNDED_FULL_VALIDATED_TARGET_COUNT=${#VALIDATED[@]}"
  ./scripts/pt -m pytest "${VALIDATED[@]}" -q --tb=short -m "not network and not external_tools" -p no:cacheprovider || RC_ALL=1
} > "$OUT/raw.log" 2>&1
END=$(date +%s)
echo "RC_ALL=$RC_ALL WALLCLOCK=$((END - START)) START=$START END=$END" | tee "$OUT/summary.txt"
