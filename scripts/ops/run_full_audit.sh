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

echo "== 3) Dependency Vulnerability Audit (pip-audit via uvx) =="
# pip-audit kann Requirements-Dateien auditieren: `pip-audit -r requirements.txt`
# uv kann aus uv.lock u.a. requirements.txt exportieren (stdout oder --output-file).
REQ_RUNTIME="$(mktemp -t peak_trade_requirements_runtime.XXXXXX.txt)"
uv export --format requirements.txt --output-file "$REQ_RUNTIME"  # runtime deps

echo "-- pip-audit runtime deps --"
uvx pip-audit@latest -r "$REQ_RUNTIME"  # uvx = tool-runner

# Optional: dev/test dependency-groups (best effort; falls Gruppen nicht existieren -> skip)
for grp in dev test; do
  REQ_GRP="$(mktemp -t peak_trade_requirements_${grp}.XXXXXX.txt)"
  if uv export --format requirements.txt --group "$grp" --output-file "$REQ_GRP" 2>/dev/null; then
    echo "-- pip-audit group: $grp --"
    uvx pip-audit@latest -r "$REQ_GRP"
  else
    echo "(skip) uv dependency-group '$grp' nicht vorhanden"
  fi
  rm -f "$REQ_GRP"
done

rm -f "$REQ_RUNTIME"

echo "== 4) Optional: SBOM Export (CycloneDX) =="
# Nützlich für Supply-Chain/Compliance Scans
uv export --format cyclonedx1.5 --output-file "$OUT_DIR/sbom.json"

echo "== 5) Lint/Format/Tests (CI-ähnlich) =="
uv run ruff format --check .
uv run ruff check .
uv run pytest -q

echo
echo "✅ FULL AUDIT DONE: deps (pip-audit), repo-health, sbom.json, lint + tests"
