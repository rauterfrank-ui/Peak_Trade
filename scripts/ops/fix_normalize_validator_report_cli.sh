#!/usr/bin/env bash
# Fix remaining sandbox-safe failures: normalize_validator_report_cli (ModuleNotFoundError: No module named 'src')
# Strategy (robust): make the CLI script self-contained by adding repo-root to sys.path at runtime.
# This avoids relying on PYTHONPATH when tests invoke it via subprocess.
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

OUT="out/ops/portable_verify_failures/fix_normalize_validator_report_cli"
mkdir -p "$OUT"

git status -sb
git log -1 --oneline

# 0) Confirm which tests are failing and where they live
python3 -m pytest -q -ra -m "not network and not external_tools" \
  | tee "$OUT/sandbox_safe_before.txt" || true

# 1) Locate the failing normalize_validator_report_cli tests + the invoked script
rg -n --hidden --glob '!.git/' "normalize_validator_report_cli" tests scripts src \
  | tee "$OUT/rg_normalize_validator_report_cli.txt" || true

# If the tests call a script path, extract it quickly:
rg -n --hidden --glob '!.git/' "python3\s+scripts/|subprocess\.(run|check_call)\(|normalize_validator_report" tests \
  | tee "$OUT/rg_subprocess_calls.txt" || true

# 2) Identify the script(s) that import from src.* and currently fail without PYTHONPATH
rg -n --hidden --glob '!.git/' "ModuleNotFoundError: No module named 'src'|import src\.|from src\." scripts tests \
  | tee "$OUT/rg_src_imports_scripts_tests.txt" || true

# Heuristic: pick the script that the failing test invokes (from rg_subprocess_calls).
# If ambiguous, list candidate scripts mentioning normalize/validator/report:
rg -n --hidden --glob '!.git/' "normalize|validator|report" scripts \
  | tee "$OUT/rg_candidate_scripts.txt" || true
