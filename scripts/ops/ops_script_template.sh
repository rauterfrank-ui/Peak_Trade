#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – <SCRIPT NAME>
# Purpose: <1-liner>
#
# Modes:
#   - Default: strict (fail fast)
#   - Robust:  PT_MODE=robust ./script.sh   (warn-only on pt_run failures)
# Notes:
#   - Use pt_run_required() for gating steps
#   - Use pt_run_optional() for nice-to-have steps
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# 0) Locate script dir + source helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=run_helpers.sh
source "${SCRIPT_DIR}/run_helpers.sh"

pt_section "Peak_Trade Ops Script: <SCRIPT NAME>"
pt_log "Mode: $(pt_mode)"

# 1) Ensure we are in repo root (safe + deterministic)
# - prefer git root, fallback to ../.. relative if needed
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  cd "${REPO_ROOT}"
else
  # fallback: assume scripts/ops/ layout
  cd "${SCRIPT_DIR}/../.."
fi

pt_log "Repo root: $(pwd)"

# 2) Required commands (gating in strict, warn in robust)
pt_require_cmd git
pt_require_cmd gh
# pt_require_cmd jq        # uncomment if needed
# pt_require_cmd python    # uncomment if needed

# 3) Optional: sanity preflight (strict-core)
pt_run_required "Git status" git status --porcelain=v1
# If you require clean tree, enforce:
# [[ -z "$(git status --porcelain=v1)" ]] || pt_die "Working tree not clean"

# ─────────────────────────────────────────────────────────────
# STRICT CORE (gating): must succeed
# ─────────────────────────────────────────────────────────────
pt_section "Strict core (gating)"

# Example:
# pt_run_required "Update main" bash -lc 'git checkout main && git pull --ff-only'

# ─────────────────────────────────────────────────────────────
# MAIN WORK (mode-controlled): pt_run obeys PT_MODE
# ─────────────────────────────────────────────────────────────
pt_section "Main work"

# Example:
# pt_run "Generate PR inventory" bash scripts/ops/pr_inventory_full.sh

# ─────────────────────────────────────────────────────────────
# OPTIONAL EXTRAS (never gating): warn-only
# ─────────────────────────────────────────────────────────────
pt_section "Optional extras (non-gating)"

# Example:
# pt_run_optional "Dry-run labels" bash scripts/ops/label_merge_log_prs.sh

pt_section "Done"
pt_log "✅ Completed"
