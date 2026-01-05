#!/usr/bin/env bash
# Peak_Trade AI-Ops Eval Runner (Promptfoo)
# Purpose: Run promptfoo evals with robust pre-flight checks
# Usage: ./scripts/aiops/run_promptfoo_eval.sh

set -euo pipefail

# === PRE-FLIGHT ===
echo "==> AI-Ops Eval Runner: Pre-Flight"

# 1) Verify git repo root
repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$repo_root" ]; then
  echo "ERROR: Not in a git repository." >&2
  exit 1
fi

cd "$repo_root"
echo "Repo root: $repo_root"
echo "Git status:"
git status -sb

# 2) Ensure node/npx available
if ! command -v node &> /dev/null; then
  echo "ERROR: node not found. Please install Node.js (LTS recommended)." >&2
  exit 1
fi

if ! command -v npx &> /dev/null; then
  echo "ERROR: npx not found. Please install Node.js with npx." >&2
  exit 1
fi

echo "Node version: $(node --version)"
echo "npx version: $(npx --version)"

# 3) Ensure promptfoo config exists
config_path="evals/aiops/promptfooconfig.yaml"
if [ ! -f "$config_path" ]; then
  echo "ERROR: Promptfoo config not found at $config_path" >&2
  exit 1
fi

echo "Config found: $config_path"

# 4) Check OPENAI_API_KEY (skip gracefully if missing)
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "NOTE: OPENAI_API_KEY not set. Skipping eval run (not a failure)."
  echo "To run evals: export OPENAI_API_KEY='sk-...'"
  exit 0
fi

echo "OPENAI_API_KEY: set (length: ${#OPENAI_API_KEY})"

# === SETUP ARTIFACTS DIR ===
artifacts_dir=".artifacts/aiops"
mkdir -p "$artifacts_dir"

timestamp=$(date -u +"%Y%m%dT%H%M%SZ")
log_file="$artifacts_dir/promptfoo_eval_${timestamp}.log"

echo "Artifacts dir: $artifacts_dir"
echo "Log file: $log_file"

# === RUN EVAL ===
echo ""
echo "==> Running promptfoo eval..."
echo ""

npx promptfoo@latest eval -c "$config_path" 2>&1 | tee "$log_file"

exit_code=${PIPESTATUS[0]}

echo ""
echo "==> Eval complete"
echo "Exit code: $exit_code"
echo "Log saved: $log_file"

exit $exit_code
