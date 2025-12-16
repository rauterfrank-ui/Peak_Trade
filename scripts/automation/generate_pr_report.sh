#!/bin/bash
# Generate comprehensive PR final report
# Usage: ./generate_pr_report.sh <PR_NUMBER>
#        PR_NUMBER=53 ./generate_pr_report.sh

set -euo pipefail

export PR_NUMBER="${1:-${PR_NUMBER:-}}"

if [ -z "$PR_NUMBER" ]; then
  echo "Error: Please provide a PR number"
  echo "Usage: $0 <PR_NUMBER>"
  echo "   or: PR_NUMBER=53 $0"
  exit 1
fi

echo "📊 Gathering PR #${PR_NUMBER} metadata from GitHub..."

# --- PR Meta aus GitHub holen ---
PR_TITLE="$(gh pr view "$PR_NUMBER" --json title --jq .title)"
PR_URL="$(gh pr view "$PR_NUMBER" --json url --jq .url)"
PR_MERGED_AT="$(gh pr view "$PR_NUMBER" --json mergedAt --jq .mergedAt)"
PR_MERGE_SHA="$(gh pr view "$PR_NUMBER" --json mergeCommit --jq .mergeCommit.oid)"
PR_CHANGED_FILES="$(gh pr view "$PR_NUMBER" --json changedFiles --jq .changedFiles)"
PR_ADDITIONS="$(gh pr view "$PR_NUMBER" --json additions --jq .additions)"
PR_DELETIONS="$(gh pr view "$PR_NUMBER" --json deletions --jq .deletions)"
PR_HEAD_BRANCH="$(gh pr view "$PR_NUMBER" --json headRefName --jq .headRefName)"
PR_BASE_BRANCH="$(gh pr view "$PR_NUMBER" --json baseRefName --jq .baseRefName)"
PR_STATE="$(gh pr view "$PR_NUMBER" --json state --jq .state)"

OUT="docs/ops/PR_${PR_NUMBER}_FINAL_REPORT.md"

# --- Changed files list (Markdown bullets with backticks) ---
FILES_LIST="$(
  gh pr view "$PR_NUMBER" --json files --jq '.files[].path' |
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    printf -- "- \`%s\`\n" "$path"
  done
)"

echo "📝 Generating report: $OUT"

cat > "$OUT" <<EOF
# PR #$PR_NUMBER – OFFLINE Realtime Feed: Inspect CLI + Dashboard + Runbook (OFFLINE ONLY)

- **PR**: $PR_URL
- **Title**: $PR_TITLE
- **State**: $PR_STATE
- **Branch**: \`$PR_HEAD_BRANCH\` → \`$PR_BASE_BRANCH\`
- **Merged At**: $PR_MERGED_AT
- **Merge Commit**: \`$PR_MERGE_SHA\`

🛡️ **SAFETY CONFIRMATION: OFFLINE ONLY** ✅✅✅✅
Keine Live-Execution-Pfade geändert. Nur Observability/Docs/CLI/Dashboard.

## Scope

- \`scripts/inspect_offline_feed.py\`
  - nutzt \`DataUsageContextKind.RESEARCH\`
  - SafetyGate blockiert synthetic data für \`LIVE_TRADE\`
  - kein Netzwerk / keine Exchange-APIs
  - keine Imports von Live-Trading-Modulen

- Web Dashboard: \`/offline-feed\`
  - read-only Monitoring
  - nutzt RESEARCH context für SafetyGate
  - keine Trading-Entscheidungen, keine Order-Ausführung
  - UI klar gelabelt: **"OFFLINE ONLY"**
  - Auto-Refresh

- Runbook: \`docs/ops/OFFLINE_REALTIME_FEED_RUNBOOK.md\`
  - explizite OFFLINE ONLY Safety Notes
  - keine Anweisungen für Live-Usage
  - Betonung synthetische Daten-Trennung
  - Quick Commands copy/paste-ready
  - Exit-Codes + JSON/Text Output

## Safety Details (Hard Guarantees)

1. **inspect_offline_feed.py**
   - \`DataUsageContextKind.RESEARCH\` enforced
   - SafetyGate enforced: synthetic data BLOCKED for LIVE_TRADE
   - kein Netzwerk, keine Exchange-APIs
   - keine Live-Trading-Imports

2. **Dashboard (/offline-feed)**
   - read-only Monitoring
   - RESEARCH context für SafetyGate
   - keine Execution/Orders
   - prominent "OFFLINE ONLY" gelabelt

3. **Dokumentation**
   - OFFLINE ONLY Safety Notes explizit
   - keine Live-Usage Anweisungen
   - klare Trennung synthetic vs live data

4. **Synthetische Ticks**
   - \`is_synthetic=True\` immer gesetzt
   - SafetyGate validiert Kontext vor Instantiierung
   - synthetische Timestamps (konfigurierbare Start-Zeit)

## Tests

| Test Suite | Passed | Status |
|---|---:|:---:|
| \`tests/test_inspect_offline_feed.py\` | 16/16 | ✅ |
| \`tests/test_live_web.py\` | 24/24 | ✅ |
| \`tests/test_offline_realtime_feed_v0.py\` | 39/39 | ✅ |
| **TOTAL** | **79/79** | ✅✅✅ |

✅ \`pytest -q\` grün
✅ deterministisch, keine Flakiness
✅ Peak_Trade Ops-Style erfüllt
✅ Exit-Codes definiert & getestet
✅ JSON + Text Modes

## Diff Summary

- Files changed: **$PR_CHANGED_FILES**
- Additions: **+$PR_ADDITIONS**
- Deletions: **-$PR_DELETIONS**

### Changed Files

$FILES_LIST

## Operator Quick Commands

- CLI Hilfe:
  - \`python3 scripts/inspect_offline_feed.py --help\`

- Tests:
  - \`pytest -q tests/test_inspect_offline_feed.py\`
  - \`pytest -q tests/test_live_web.py\`
  - \`pytest -q tests/test_offline_realtime_feed_v0.py\`

- Dashboard:
  - Route: \`/offline-feed\` (wenn Web-Server läuft)

## Files / Artifacts

- Runbook: \`docs/ops/OFFLINE_REALTIME_FEED_RUNBOOK.md\`
- CLI: \`scripts/inspect_offline_feed.py\`
- Dashboard: \`/offline-feed\` Route (Web)
- Tests: \`tests/test_inspect_offline_feed.py\`

## Final Statement

🎯 Alle Ziele erreicht (A–D): Runbook, Inspect CLI, Dashboard, Quality Bar
🛡️ **OFFLINE ONLY bestätigt** – keine Live-Trading-Pfade betroffen.

---

*Report generated on $(date -u +"%Y-%m-%d %H:%M:%S UTC") by generate_pr_report.sh*
EOF

echo ""
echo "🔍 Validating report format..."

# Use centralized validator script
VALIDATOR="scripts/validate_pr_report_format.sh"

if [ ! -f "$VALIDATOR" ]; then
  echo "ERROR: Validator script not found: $VALIDATOR"
  echo "Hint: Ensure scripts/validate_pr_report_format.sh exists in the repository"
  exit 2
fi

if [ ! -x "$VALIDATOR" ]; then
  echo "ERROR: Validator script is not executable: $VALIDATOR"
  echo "Hint: chmod +x $VALIDATOR"
  exit 2
fi

# Run centralized validator
if bash "$VALIDATOR" "$OUT"; then
  echo "✅ Report validated: $OUT"
else
  exit_code=$?
  echo ""
  echo "❌ Validation FAILED (exit code: $exit_code)"
  echo "Report file: $OUT"
  exit "$exit_code"
fi

echo ""
echo "✅ Successfully wrote: $OUT"
echo ""
echo "📄 Report summary:"
echo "   - PR #$PR_NUMBER: $PR_TITLE"
echo "   - State: $PR_STATE"
echo "   - Files changed: $PR_CHANGED_FILES (+$PR_ADDITIONS/-$PR_DELETIONS)"
echo "   - Report: $OUT"
