#!/usr/bin/env bash
set -euo pipefail

# ===== Setup: Versionierte Artefakte + Logging =====
OUT_DIR="reports/audit/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT_DIR"
LOG="$OUT_DIR/full_audit.log"
exec > >(tee -a "$LOG") 2>&1

echo "OUT_DIR=$OUT_DIR"
echo "GIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo 'N/A')"
echo "UV_VERSION=$(uv --version 2>/dev/null || echo 'N/A')"
echo "PY_VERSION=$(python --version 2>/dev/null || echo 'N/A')"
echo

# ===== 0) Preconditions =====
git rev-parse --show-toplevel >/dev/null

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree ist NICHT clean. Bitte commit/stash, dann erneut."
  git status --porcelain
  exit 2
fi

command -v uv >/dev/null 2>&1 || { echo "❌ uv nicht gefunden (Peak_Trade nutzt uv)."; exit 3; }

echo "== 1) Sync (reproducible env) =="
uv sync

echo "== 2) Peak_Trade Repo-Health (falls vorhanden) =="
if [[ -x scripts/ops/ops_center.sh ]]; then
  scripts/ops/ops_center.sh doctor
else
  echo "(skip) scripts/ops/ops_center.sh nicht gefunden"
fi

echo "== 3) Dependency Vulnerability Audit (pip-audit) =="
# pip-audit scannt das aktuelle Environment (kompatibel mit uv)
echo "-- pip-audit (installed packages) --"
uv run pip-audit --desc || {
  echo "⚠️  pip-audit fehlgeschlagen - installiere pip-audit falls nicht vorhanden"
  uv pip install pip-audit
  uv run pip-audit --desc
}

echo "== 4) Optional: SBOM Export (CycloneDX) =="
# Nützlich für Supply-Chain/Compliance Scans
uv export --format cyclonedx1.5 --output-file "$OUT_DIR/sbom.json"

echo "== 5) Lint/Format/Tests (CI-ähnlich) =="
uv run ruff format --check .
uv run ruff check .
uv run pytest -q

echo
echo "✅ FULL AUDIT DONE: deps (pip-audit), repo-health, sbom.json, lint + tests"
