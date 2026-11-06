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
AUDIT_EXIT=0
uv run pip-audit --desc || {
  AUDIT_EXIT=$?
  if [[ $AUDIT_EXIT -eq 127 ]]; then
    echo "⚠️  pip-audit nicht gefunden - installiere pip-audit"
    uv pip install pip-audit
    AUDIT_EXIT=0
    uv run pip-audit --desc || AUDIT_EXIT=$?
  fi
}
echo "pip-audit exit code: $AUDIT_EXIT"
[[ $AUDIT_EXIT -eq 0 ]] && echo "✅ Keine Vulnerabilities gefunden" || echo "⚠️  Vulnerabilities gefunden (siehe oben)"

echo "== 4) Optional: SBOM Export (CycloneDX) =="
# Nützlich für Supply-Chain/Compliance Scans
uv export --format cyclonedx1.5 --output-file "$OUT_DIR/sbom.json"

echo "== 5) Lint/Format/Tests (CI-ähnlich) =="
LINT_EXIT=0
uv run ruff format --check . || LINT_EXIT=$?
uv run ruff check . || LINT_EXIT=$((LINT_EXIT + $?))

TEST_EXIT=0
uv run pytest -q || TEST_EXIT=$?

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 AUDIT SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Log:     $LOG"
echo "SBOM:    $OUT_DIR/sbom.json"
echo "pip-audit:   $([ $AUDIT_EXIT -eq 0 ] && echo '✅ PASS' || echo '⚠️  VULNERABILITIES FOUND')"
echo "Lint/Format: $([ $LINT_EXIT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Tests:       $([ $TEST_EXIT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FINAL_EXIT=0
[[ $AUDIT_EXIT -ne 0 ]] && FINAL_EXIT=1
[[ $LINT_EXIT -ne 0 ]] && FINAL_EXIT=1
[[ $TEST_EXIT -ne 0 ]] && FINAL_EXIT=1

exit $FINAL_EXIT
