#!/usr/bin/env bash
# Peak_Trade AI-Ops Eval Runner (Promptfoo)
# Purpose: Run promptfoo evals with robust pre-flight checks and audit telemetry
# Usage: ./scripts/aiops/run_promptfoo_eval.sh

set -euo pipefail

# === VERSION PINS (for reproducibility) ===
PROMPTFOO_VERSION="0.120.8"  # Update this for new promptfoo releases
CANONICAL_NODE_VERSION="v25.2.1"  # Canonical Node version (see .nvmrc)

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
echo "Git SHA: $(git rev-parse HEAD)"
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

node_version=$(node --version)
npx_version=$(npx --version)
echo "Node version: $node_version"
echo "npx version: $npx_version"

# Warn if Node version doesn't match canonical (non-failing)
if [ "$node_version" != "$CANONICAL_NODE_VERSION" ]; then
  echo "WARNING: Node version mismatch. Expected: $CANONICAL_NODE_VERSION, Got: $node_version"
  echo "         For reproducible evals, align to .nvmrc: nvm use"
fi

# 3) Ensure promptfoo config exists
config_path="evals/aiops/promptfooconfig.yaml"
if [ ! -f "$config_path" ]; then
  echo "ERROR: Promptfoo config not found at $config_path" >&2
  exit 1
fi

echo "Config found: $config_path"
echo "Promptfoo version (pinned): $PROMPTFOO_VERSION"

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
git_sha=$(git rev-parse HEAD)
log_file="$artifacts_dir/promptfoo_eval_${timestamp}.log"

echo "Artifacts dir: $artifacts_dir"
echo "Log file: $log_file"

# Write audit telemetry header to log
{
  echo "=== AI-Ops Eval Run Audit ==="
  echo "Timestamp: $timestamp"
  echo "Git SHA: $git_sha"
  echo "Node version: $node_version"
  echo "npx version: $npx_version"
  echo "Promptfoo version: $PROMPTFOO_VERSION"
  echo "Config path: $config_path"
  echo "==========================="
  echo ""
} > "$log_file"

# === RUN EVAL ===
echo ""
echo "==> Running promptfoo eval..."
echo ""

npx promptfoo@${PROMPTFOO_VERSION} eval -c "$config_path" 2>&1 | tee -a "$log_file"

exit_code=${PIPESTATUS[0]}

echo ""
echo "==> Eval complete"
echo "Exit code: $exit_code"
echo "Log saved: $log_file"

exit $exit_code
