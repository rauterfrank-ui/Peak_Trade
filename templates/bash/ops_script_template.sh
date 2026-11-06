#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Peak_Trade – Ops Script Template
#
# Name:    <SCRIPT_NAME>
# Purpose: <ONE-LINER>
#
# Modes:
#   - Default: strict (fail fast)
#   - Robust:  PT_MODE=robust bash <script>.sh
#
# Conventions:
#   - Use pt_run_required() for gating steps
#   - Use pt_run() for mode-controlled steps
#   - Use pt_run_optional() for nice-to-have steps
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# 0) Locate script dir + source run helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=run_helpers.sh
source "${SCRIPT_DIR}/run_helpers.sh"

pt_section "Peak_Trade Ops: <SCRIPT_NAME>"
pt_log "Mode: $(pt_mode)"

# 1) Ensure repo root (deterministic)
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  cd "${REPO_ROOT}"
else
  # fallback: assume scripts/ops/ layout if this template was copied there
  cd "${SCRIPT_DIR}/../.."
fi
pt_log "Repo root: $(pwd)"

# 2) Required commands
pt_require_cmd git
pt_require_cmd gh
# pt_require_cmd jq      # uncomment if needed
# pt_require_cmd python  # uncomment if needed

# 3) Optional: preflight policy (uncomment if your script requires clean tree)
# [[ -z "$(git status --porcelain=v1)" ]] || pt_die "Working tree not clean"

# ─────────────────────────────────────────────────────────────
# STRICT CORE (gating)
# ─────────────────────────────────────────────────────────────
pt_section "Strict core (gating)"

# Example:
# pt_run_required "Update main" bash -lc 'git checkout main && git pull --ff-only'

# ─────────────────────────────────────────────────────────────
# MAIN WORK (mode-controlled)
# ─────────────────────────────────────────────────────────────
pt_section "Main work"

# Example:
# pt_run "Generate PR inventory" bash scripts/ops/pr_inventory_full.sh

# ─────────────────────────────────────────────────────────────
# OPTIONAL EXTRAS (never gating)
# ─────────────────────────────────────────────────────────────
pt_section "Optional extras (non-gating)"

# Example:
# pt_run_optional "Dry-run labels" bash scripts/ops/label_merge_log_prs.sh

pt_section "Done"
pt_log "✅ Completed"
