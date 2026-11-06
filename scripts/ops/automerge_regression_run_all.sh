#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Automerge-Regression: Planner → Implementer → Critic (kompletter Lauf)
# 1) planner: main aktualisieren, PR-Kandidaten aus Log extrahieren
# 2) implementer: GitHub-API (PR, Reviews, Checks, Actions) – braucht GITHUB_TOKEN
# 3) critic: Evidence auswerten, MERGE_ACTOR_CLASS, likely_automerge_workflows
# ─────────────────────────────────────────────────────────────
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(git rev-parse --show-toplevel)"

echo "[1/3] planner..."
bash "$SCRIPT_DIR/automerge_regression_planner.sh"

echo "[2/3] implementer (GITHUB_TOKEN required)..."
bash "$SCRIPT_DIR/automerge_regression_implementer.sh"

echo "[3/3] critic..."
bash "$SCRIPT_DIR/automerge_regression_critic.sh"

echo "All three agents done. Evidence in out/ops/automerge_regression/"
