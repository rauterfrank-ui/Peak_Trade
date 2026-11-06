#!/usr/bin/env bash
set -euo pipefail

# Ops Doctor – Minimal Smoke Tests
# ==================================
# Schnelle, nicht-interaktive Tests für CI/CD

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Ops Doctor – Minimal Smoke Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "${REPO_ROOT}"

FAIL_COUNT=0

# Test 1: --help funktioniert
echo "Test 1/4: --help flag"
if ./scripts/ops/ops_doctor.sh --help > /dev/null 2>&1; then
    echo "✅ --help works"
else
    echo "❌ --help failed"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 2: Shell-Script Syntax Check
echo "Test 2/4: Shell script syntax"
if bash -n ./scripts/ops/ops_doctor.sh; then
    echo "✅ Shell syntax valid"
else
    echo "❌ Shell syntax errors"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 3: JSON-Output ist valide
echo "Test 3/4: JSON output validation"
# Nur stdout prüfen, stderr und Exit Code ignorieren
# (ops_doctor kann Exit Code 2 bei warnings haben, was ok ist)
JSON_TMP="/tmp/ops_doctor_test_$$.json"
./scripts/ops/ops_doctor.sh --json 2>/dev/null > "$JSON_TMP" || true
if python3 -m json.tool "$JSON_TMP" > /dev/null 2>&1; then
    echo "✅ JSON output valid"
    rm -f "$JSON_TMP"
else
    echo "❌ JSON output invalid"
    echo "Output preview:"
    head -10 "$JSON_TMP"
    rm -f "$JSON_TMP"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Test 4: Python-Modul direkt ausführbar
echo "Test 4/4: Python module direct execution"
if python3 -m src.ops.doctor --check repo.git_root > /dev/null 2>&1; then
    echo "✅ Python module works"
else
    echo "❌ Python module failed"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi
echo ""

# Ergebnis
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ All smoke tests passed!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "❌ $FAIL_COUNT smoke test(s) failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
