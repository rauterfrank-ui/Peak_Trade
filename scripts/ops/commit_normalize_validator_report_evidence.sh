#!/usr/bin/env bash
# Commit script change + write tight evidence.
# Verify whether it *actually* finished (exit code + final summary).
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

OUT="out/ops/portable_verify_failures/fix_normalize_validator_report_cli"
mkdir -p "$OUT"

# 0) Definitive verify (exit code + final summary + count)
python3 -m pytest -q tests/ai_orchestration/test_normalize_validator_report_cli.py \
  tests/ai_orchestration/test_l4_validator_report_normalization_determinism.py \
  | tee "$OUT/verify_q.txt"
EC=${PIPESTATUS[0]}
echo "PYTEST_EXIT_CODE=$EC" | tee "$OUT/verify_exit_code.txt"
test "$EC" -eq 0

python3 -m pytest -ra tests/ai_orchestration/test_normalize_validator_report_cli.py \
  tests/ai_orchestration/test_l4_validator_report_normalization_determinism.py \
  | tee "$OUT/verify_ra.txt"
EC2=${PIPESTATUS[0]}
echo "PYTEST_EXIT_CODE_RA=$EC2" | tee "$OUT/verify_exit_code_ra.txt"
test "$EC2" -eq 0

# Optional: show the final "passed" line(s) explicitly (proves completion)
rg -n "passed|failed|error|xfailed|xpassed|skipped" "$OUT/verify_q.txt" "$OUT/verify_ra.txt" | tee "$OUT/verify_summary_lines.txt" || true

# 1) Confirm the intended diff
SCRIPT="scripts/aiops/normalize_validator_report.py"
test -f "$SCRIPT"
git diff -- "$SCRIPT" | tee "$OUT/DIFF_normalize_validator_report.patch"

# 2) Commit (only if there are changes)
git status -sb | tee "$OUT/STATUS_before_commit.txt"

if ! git diff --quiet -- "$SCRIPT"; then
  git add "$SCRIPT"
  git commit -m "scripts(aiops): run normalize validator report without PYTHONPATH (repo-root sys.path + src imports)"
fi

git status -sb | tee "$OUT/STATUS_after_commit.txt"
git log -1 --oneline | tee "$OUT/LOG1_commit.txt"
git show --stat -1 | tee "$OUT/SHOW_STAT_commit.txt"

# 3) Hash evidence (macOS-safe)
(
  cd "$OUT"
  shasum -a 256 \
    verify_q.txt verify_exit_code.txt verify_ra.txt verify_exit_code_ra.txt verify_summary_lines.txt \
    DIFF_normalize_validator_report.patch STATUS_before_commit.txt STATUS_after_commit.txt LOG1_commit.txt SHOW_STAT_commit.txt \
    | tee SHA256.txt
)

# 4) Quick explanation for the "92%" suspicion (no prose; just show pytest collected count + completion)
python3 -m pytest --collect-only \
  tests/ai_orchestration/test_normalize_validator_report_cli.py \
  tests/ai_orchestration/test_l4_validator_report_normalization_determinism.py \
  | tee "$OUT/collect_only.txt"

rg -n "collected|tests collected" "$OUT/collect_only.txt" | tee "$OUT/collect_only_summary.txt" || true
