#!/usr/bin/env bash
# Nach dem manuellen gh auth login ausführen: PR erstellen und im Browser öffnen.
set -euo pipefail

cd /Users/frnkhrz/Peak_Trade
BR="feat/vol-regime-universal-wrapper"

echo "=== Auth-Status ==="
gh auth status -h github.com

echo ""
echo "=== PR erstellen ==="
gh pr create --base main --head "$BR" --fill

echo ""
echo "=== PR im Browser öffnen ==="
gh pr view --web
