#!/usr/bin/env bash
set -euo pipefail

# Ops Doctor Demo Script
# =======================
# Demonstriert die verschiedenen Verwendungsmöglichkeiten des Ops Doctor Tools.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 Ops Doctor Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "${REPO_ROOT}"

# Demo 1: Alle Checks (Human-Readable)
echo "📋 Demo 1: Alle Checks (Human-Readable)"
echo "Command: ./scripts/ops/ops_doctor.sh"
echo ""
./scripts/ops/ops_doctor.sh
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter to continue to Demo 2..."
echo ""

# Demo 2: JSON-Output
echo "📋 Demo 2: JSON-Output"
echo "Command: ./scripts/ops/ops_doctor.sh --json | head -30"
echo ""
./scripts/ops/ops_doctor.sh --json | head -30
echo ""
echo "... (truncated)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter to continue to Demo 3..."
echo ""

# Demo 3: Spezifische Checks
echo "📋 Demo 3: Spezifische Checks"
echo "Command: ./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock"
echo ""
./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter to continue to Demo 4..."
echo ""

# Demo 4: Python-Modul direkt
echo "📋 Demo 4: Python-Modul direkt"
echo "Command: python3 -m src.ops.doctor --check config.pyproject"
echo ""
python3 -m src.ops.doctor --check config.pyproject
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "🎉 Demo abgeschlossen!"
echo ""
echo "📚 Weitere Informationen:"
echo "   - Dokumentation: docs/ops/OPS_DOCTOR_README.md"
echo "   - Tests: python3 -m pytest tests/ops/test_doctor.py -v"
echo "   - Hilfe: ./scripts/ops/ops_doctor.sh --help"
