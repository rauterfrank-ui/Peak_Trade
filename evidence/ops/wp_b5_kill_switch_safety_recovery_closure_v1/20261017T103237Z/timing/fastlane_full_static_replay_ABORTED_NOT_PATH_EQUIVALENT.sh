#!/usr/bin/env bash
# Local path-equivalent replay of ci.yml fast-lane FULL_STATIC_CONTRACTS + tests(3.11) PR_BOUNDED_FULL.
set -uo pipefail
cd /private/tmp/peak_trade_wp_b5
OUT=/tmp/wp_b5_timing
rm -rf "$OUT"; mkdir -p "$OUT"
PYTEST_ARGS=(-q --tb=short -m "not network and not external_tools" -p no:cacheprovider)
START=$(date +%s)
echo "START=$START" > "$OUT/summary.txt"
OPS_FILES=()
while IFS= read -r f; do OPS_FILES+=("$f"); done < <(find tests/ops -name 'test_*.py' -type f | LC_ALL=C sort)
echo "OPS_FILES=${#OPS_FILES[@]}" >> "$OUT/summary.txt"
( ./scripts/pt -m pytest tests/ci "${PYTEST_ARGS[@]}" > "$OUT/ci.log" 2>&1; echo "RC=$? END=$(date +%s)" >> "$OUT/ci.log" ) &
PIDS=($!)
for ((s = 0; s < 8; s++)); do
  ( files=(); for i in "${!OPS_FILES[@]}"; do (( i % 8 == s )) && files+=("${OPS_FILES[i]}"); done
    ./scripts/pt -m pytest "${files[@]}" "${PYTEST_ARGS[@]}" > "$OUT/shard_$s.log" 2>&1
    echo "RC=$? END=$(date +%s)" >> "$OUT/shard_$s.log" ) &
  PIDS+=($!)
done
for p in "${PIDS[@]}"; do wait "$p"; done
FL_END=$(date +%s)
echo "FASTLANE_WALLCLOCK=$((FL_END - START))" >> "$OUT/summary.txt"
TARGETS="tests/ci/test_ci_diff_aware_test_selection_v1.py tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py tests/ci/test_pr_head_sha_required_checks_liveness_guard.py tests/ci/test_required_checks_config.py tests/ci/test_required_checks_hygiene.py tests/ci/test_workflows_no_pull_request_target_contract_v0.py tests/test_data_contracts.py tests/test_error_taxonomy.py tests/test_resilience.py tests/test_stability_smoke.py"
T0=$(date +%s)
./scripts/pt -m pytest $TARGETS "${PYTEST_ARGS[@]}" > "$OUT/pr_bounded.log" 2>&1
echo "RC=$? END=$(date +%s)" >> "$OUT/pr_bounded.log"
echo "PR_BOUNDED_WALLCLOCK=$(( $(date +%s) - T0 ))" >> "$OUT/summary.txt"
echo "DONE=$(date +%s)" >> "$OUT/summary.txt"
