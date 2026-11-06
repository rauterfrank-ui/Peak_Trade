#!/usr/bin/env bash
# Fix the failing CI gates shown on PR #1271
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

BR="feat/metrics-ulcer-recovery"
git checkout "$BR"
git fetch origin --prune
git status -sb

mkdir -p out/ops/pr_1271_ci
git rev-parse HEAD | tee out/ops/pr_1271_ci/HEAD.txt
git log -1 --oneline | tee out/ops/pr_1271_ci/LOG1.txt

# 0) Run local lint + show what fails
ruff format src tests scripts 2>/dev/null || true
python3 -m ruff format src tests scripts 2>/dev/null || true
python3 -m ruff check src tests scripts 2>/dev/null || true
python3 -m pytest -q 2>/dev/null | tail -20 || true

# 1) Docs Token Policy Gate: fix any "allowed=True/False" patterns (must be escaped)
rg -n --hidden --glob '!.git/' "allowed=True/False" docs 2>/dev/null \
  | tee out/ops/pr_1271_ci/docs_token_policy_hits.txt || true

if test -s out/ops/pr_1271_ci/docs_token_policy_hits.txt; then
  for f in $(cut -d: -f1 out/ops/pr_1271_ci/docs_token_policy_hits.txt | sort -u); do
    test -f "$f" && perl -pi -e 's/allowed=True\/False/allowed=True&#47;False/g' "$f"
  done
fi

# 2) Docs Reference Targets Gate
for c in \
  "python3 scripts/ops/validate_docs_reference_targets.py" \
  "python3 scripts/ops/validate_docs_reference_targets.py --base origin/main" \
  "python3 scripts/ops/validate_docs_reference_targets.py --base main" \
  "python3 scripts/ops/validate_docs_reference_targets.py --help" \
; do
  echo ">> $c" | tee -a out/ops/pr_1271_ci/docs_ref_gate_attempts.txt
  (cd /Users/frnkhrz/Peak_Trade && eval "$c") >> out/ops/pr_1271_ci/docs_ref_gate_attempts.txt 2>&1 && break || true
done

# 3) Docs Diff Guard Policy Gate: remove tracked out/* from index
git ls-files out 2>/dev/null | tee out/ops/pr_1271_ci/tracked_out_files.txt || true
git ls-files out/ops 2>/dev/null | tee out/ops/pr_1271_ci/tracked_out_ops_files.txt || true

if test -s out/ops/pr_1271_ci/tracked_out_files.txt; then
  git rm -r --cached out 2>/dev/null || true
fi

# 4) L4 Critic Replay Determinism gate
python3 -m pytest tests/obs/test_ai_live_ops_determinism_v1.py -q 2>/dev/null || true
python3 -m pytest -k "l4_critic_replay or critic replay determinism" -q 2>/dev/null || true

# 5) Lint Gate
python3 -m ruff format src tests scripts
python3 -m ruff check src tests scripts

# 6) Doc token policy script
for c in \
  "python3 scripts/ops/validate_docs_token_policy.py --base origin/main" \
  "python3 scripts/ops/validate_docs_token_policy.py --base main" \
; do
  echo ">> $c" | tee -a out/ops/pr_1271_ci/docs_token_gate_attempts.txt
  (cd /Users/frnkhrz/Peak_Trade && eval "$c") >> out/ops/pr_1271_ci/docs_token_gate_attempts.txt 2>&1 && break || true
done

# 7) Commit fixes (only non-out changes; out/ stays untracked)
git status -sb | tee out/ops/pr_1271_ci/STATUS_before_commit.txt

if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  git reset -- out
  git status -sb
  git commit -m "ci: fix doc gates + remove tracked out artifacts" || true
fi

git status -sb | tee out/ops/pr_1271_ci/STATUS_after_commit.txt
git log -1 --oneline | tee out/ops/pr_1271_ci/LOG1_after.txt

# 8) Push to retrigger CI
git push origin "$BR"
