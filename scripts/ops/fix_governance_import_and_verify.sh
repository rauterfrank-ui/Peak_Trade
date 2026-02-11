#!/usr/bin/env bash
# Apply Governance import fix (1-line change) + focused verify.
# Change: src/ai_orchestration/l3_runner.py: from governance.learning ... -> from src.governance.learning ...
# Keine timeouts – volle Laufzeit für pytest.
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

git status -sb
git rev-parse --abbrev-ref HEAD

# 1) Locate the exact import line + show context
rg -n "from\s+governance\.learning\s+import" src/ai_orchestration/l3_runner.py || true
sed -n '1,80p' src/ai_orchestration/l3_runner.py

# 2) Patch the import (single replacement)
perl -pi -e 's/^from\s+governance\.learning\s+import\s+/from src.governance.learning import /' src/ai_orchestration/l3_runner.py

# 3) Show diff (should be 1 line)
git diff -- src/ai_orchestration/l3_runner.py

# 4) Verify: only the 2 governance failures (or fast grep-based selection)
# Prefer rerunning last-failed if you still have them recorded; otherwise target files that failed.
python3 -m pytest -q --lf -vv --maxfail=1 || true
python3 -m pytest -q --lf -vv || true

# If --lf includes other buckets, run just the relevant suite(s) you saw failing:
# python3 -m pytest -q -vv tests/ingress -k "governance|l3_runner" --tb=short || true

# 5) Commit + evidence
mkdir -p out/ops/portable_verify_failures/fix_governance_import
git status -sb | tee out/ops/portable_verify_failures/fix_governance_import/STATUS_before_commit.txt

git add src/ai_orchestration/l3_runner.py
git commit -m "ai: fix governance import path in l3 runner" || true

git status -sb | tee out/ops/portable_verify_failures/fix_governance_import/STATUS_after_commit.txt
git log -1 --oneline | tee out/ops/portable_verify_failures/fix_governance_import/LOG1.txt
git show --stat -1 | tee out/ops/portable_verify_failures/fix_governance_import/SHOW_STAT.txt

(
  cd out/ops/portable_verify_failures/fix_governance_import
  shasum -a 256 STATUS_before_commit.txt STATUS_after_commit.txt LOG1.txt SHOW_STAT.txt | tee SHA256.txt
)
