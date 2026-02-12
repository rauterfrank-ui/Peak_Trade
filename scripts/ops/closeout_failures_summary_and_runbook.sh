#!/usr/bin/env bash
# FINAL CLOSEOUT: update FAILURES_SUMMARY.md and runbook with green status + evidence pointers,
# then optional push/PR commands.
set -euo pipefail
cd /Users/frnkhrz/Peak_Trade

git status -sb
git log -1 --oneline

# 1) Append closeout to FAILURES_SUMMARY.md (idempotent)
SUM="out/ops/portable_verify_failures/FAILURES_SUMMARY.md"
test -f "$SUM"

HDR="## Closeout — normalize_validator_report_cli (fixed) + suite green"
if ! rg -q --fixed-strings "$HDR" "$SUM" 2>/dev/null; then
  cat >> "$SUM" <<'EOF'

## Closeout — normalize_validator_report_cli (fixed) + suite green

- Fix commit: 604a53fb — scripts(aiops): run normalize validator report without PYTHONPATH (repo-root sys.path + src imports)
- Root cause: subprocess-run CLI script without PYTHONPATH; sys.path previously pointed at repo_root/src which breaks `import src.*`.
- Fix: scripts/aiops/normalize_validator_report.py now inserts repo-root on sys.path and uses `from src.ai_orchestration.*` imports.
- Verification:
  - pytest -q: 14 passed (Exit 0)
  - pytest -ra: 14 passed (Exit 0)
  - collect-only: 14 tests collected
- Evidence directory:
  - out/ops/portable_verify_failures/fix_normalize_validator_report_cli/
EOF
fi

git add -f "$SUM"
git commit -m "ops: closeout normalize_validator_report_cli failures (green) in FAILURES_SUMMARY" || true

# 2) Optional: also append a tiny note to the main runbook (idempotent)
RUNBOOK="docs/ops/runbooks/RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md"
test -f "$RUNBOOK"
RHDR="### Closeout — normalize_validator_report_cli (PYTHONPATH-free) green"
if ! rg -q --fixed-strings "$RHDR" "$RUNBOOK" 2>/dev/null; then
  cat >> "$RUNBOOK" <<'EOF'

### Closeout — normalize_validator_report_cli (PYTHONPATH-free) green
- Fix commit: 604a53fb (scripts/aiops/normalize_validator_report.py)
- Evidence: out/ops/portable_verify_failures/fix_normalize_validator_report_cli/
EOF
fi

git add "$RUNBOOK"
git commit -m "docs(ops): note normalize_validator_report_cli closeout in runbook" || true

# 3) Evidence snapshot for these closeout doc commits
EVD="out/ops/portable_verify_failures/closeout_docs"
mkdir -p "$EVD"

git status -sb | tee "$EVD/STATUS.txt"
git log -2 --oneline | tee "$EVD/LOG2.txt"
git show --stat -2 | tee "$EVD/SHOW_STAT_2.txt"
git diff --cached > "$EVD/DIFF_CACHED.patch" 2>/dev/null || true
(
  cd "$EVD"
  shasum -a 256 STATUS.txt LOG2.txt SHOW_STAT_2.txt DIFF_CACHED.patch 2>/dev/null | tee SHA256.txt
)

# 4) Optional publish
# git push -u origin feat/metrics-ulcer-recovery
# echo "https://github.com/rauterfrank-ui/Peak_Trade/compare/main...feat/metrics-ulcer-recovery?expand=1"
# gh pr create --fill
# gh pr view --web
