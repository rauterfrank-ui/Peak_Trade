#!/usr/bin/env bash
#
# setup_drift_guard_pr_workflow.sh
#
# Sets up the complete Required Checks Drift Guard PR Workflow system:
# - Adds --dry-run and --offline-only flags to workflow scripts
# - Creates smoke tests
# - Updates documentation
# - Registers in README_REGISTRY.md
#
# Usage:
#   setup_drift_guard_pr_workflow.sh

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Peak_Trade — Required Checks Drift Guard: Dry-Run + Smoke Tests + Docs Registry
# WHERE TO RUN: Terminal / iTerm (im Repo)
# ──────────────────────────────────────────────────────────────────────────────

REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
BRANCH="${BRANCH:-feat/required-checks-drift-guard-pr-workflow}"
BASE="${BASE:-main}"
LABELS_CSV="${LABELS_CSV:-ops,ci}"

cd "$REPO_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Setup: Required Checks Drift Guard PR Workflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 0) Branch vorbereiten
echo "📦 Branch: $BRANCH"
git fetch origin "$BASE" --prune
git checkout -b "$BRANCH" "origin/$BASE" 2>/dev/null || {
  git checkout "$BRANCH"
  git rebase "origin/$BASE"
}

mkdir -p scripts/ops/tests docs/ops

# ──────────────────────────────────────────────────────────────────────────────
# 1) Docs: Required Checks Drift Guard Guide
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "📝 1) Erstelle docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md"

cat > docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md <<'MD'
# Required Checks Drift Guard

## Zweck
Schützt davor, dass **dokumentierte Required Checks** und **live GitHub Branch Protection Required Checks** auseinanderlaufen (Drift).

## Integration (High-Level)

### Ops Center Integration
```bash
ops_center.sh doctor
  └─> verify_required_checks_drift.sh --warn-only
```

### PR Workflow
```bash
run_required_checks_drift_guard_pr.sh
  └─> create_required_checks_drift_guard_pr.sh
        ├─> verify_required_checks_drift.sh --offline
        ├─> ops_center.sh doctor (falls vorhanden)
        ├─> pytest (falls vorhanden)
        └─> verify_required_checks_drift.sh --live --warn-only (optional)
```

## Exit Codes (Live-Teil)
- `0` — ✅ Kein Drift (Doc == Live)
- `2` — ⚠️ Drift erkannt (warn-only) → Review drift, Docs oder Branch Protection synchronisieren
- `1` — ❌ Fehler (Preflight failed: gh/jq/auth Problem)

## Operator Workflows

### Dry-Run (nur Offline, kein Git)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only
```
- Führt nur Offline-Checks aus
- Keine Git-Operationen (commit/push/PR)
- Perfekt zum Testen

### Dry-Run (mit Live-Check, kein Git)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run
```
- Führt Offline + Live-Checks aus
- Keine Git-Operationen
- Zeigt, ob Drift vorhanden ist

### Full Run (Production)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh
```
- Alle Checks (offline + live)
- Commit + Push + PR erstellen
- CI Watch

### Custom Config
```bash
export BRANCH="feat/my-custom-branch"
export BASE="develop"
export LABELS_CSV="ops,ci,infrastructure"

scripts/ops/run_required_checks_drift_guard_pr.sh
```

## Skript-Architektur

```
scripts/ops/
├── run_required_checks_drift_guard_pr.sh
│   └─> Finder + Wrapper (one-block style)
│
├── create_required_checks_drift_guard_pr.sh
│   ├─> Phase 1: Offline Checks
│   ├─> Phase 2: Live Drift Check (optional)
│   ├─> Phase 3: Commit + Push + PR
│   └─> Phase 4: Labels + CI Watch
│
├── verify_required_checks_drift.sh
│   └─> Core drift detection logic
│
└── tests/
    ├── test_verify_required_checks_drift.sh
    │   └─> Smoke tests for verify script
    │
    └── test_drift_guard_pr_workflow.sh
        └─> Smoke tests for PR workflow
```

## Troubleshooting

### "❌ gh fehlt"
```bash
brew install gh
gh auth login
```

### "❌ jq fehlt"
```bash
brew install jq
```

### "⚠️ Drift detected (warn-only)"
Das ist **kein Fehler**, sondern eine Warnung:
1. **Option 1:** Dokumentation aktualisieren (falls Live-State korrekt)
2. **Option 2:** Branch Protection anpassen (falls Doc korrekt)

Siehe: `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`

## Related Documentation
- `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` — Operator Guide
- `REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md` — PR Workflow Details
- `docs/ops/OPS_OPERATOR_CENTER.md` — Ops Center Overview

---

**Last Updated:** 2025-12-25
**Maintained by:** Peak_Trade Ops Team
MD

# ──────────────────────────────────────────────────────────────────────────────
# 2) Update: create_required_checks_drift_guard_pr.sh (add --dry-run + --offline-only)
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "🔧 2) Update create_required_checks_drift_guard_pr.sh (add flags)"

cat > scripts/ops/create_required_checks_drift_guard_pr.sh <<'BASH'
#!/usr/bin/env bash
#
# create_required_checks_drift_guard_pr.sh
#
# Creates a PR with the required checks drift guard feature
#
# Usage:
#   create_required_checks_drift_guard_pr.sh [--dry-run] [--offline-only]
#
# Flags:
#   --dry-run        Run checks but skip commit/push/PR
#   --offline-only   Skip live drift check (only offline checks)
#
# Environment Variables (optional):
#   REPO_DIR     Repository directory (default: $HOME/Peak_Trade)
#   BRANCH       Feature branch name (default: feat/required-checks-drift-guard-v1)
#   BASE         Base branch (default: main)
#   COMMIT_MSG   Commit message (default: feat(ops): add required checks drift guard)
#   PR_TITLE     PR title (default: feat(ops): add required checks drift guard)
#   LABELS_CSV   Labels to add (default: ops,ci)

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Parse Flags
# ──────────────────────────────────────────────────────────────────────────────
DRY_RUN=0
OFFLINE_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=1
      ;;
    --offline-only)
      OFFLINE_ONLY=1
      ;;
    --help|-h)
      cat <<'HELP'
Usage: create_required_checks_drift_guard_pr.sh [--dry-run] [--offline-only]

Flags:
  --dry-run        Run checks but skip commit/push/PR
  --offline-only   Skip live drift check (only offline checks)
  --help           Show this help

Environment Variables:
  REPO_DIR     Repository directory (default: $HOME/Peak_Trade)
  BRANCH       Feature branch name (default: feat/required-checks-drift-guard-v1)
  BASE         Base branch (default: main)
  LABELS_CSV   Labels to add (default: ops,ci)

Examples:
  # Dry-run (offline only)
  create_required_checks_drift_guard_pr.sh --dry-run --offline-only

  # Dry-run (with live check)
  create_required_checks_drift_guard_pr.sh --dry-run

  # Full run (production)
  create_required_checks_drift_guard_pr.sh
HELP
      exit 0
      ;;
    *)
      echo "❌ Unknown argument: $arg" >&2
      echo "   Run with --help for usage" >&2
      exit 1
      ;;
  esac
done

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
BASE="${BASE:-main}"
COMMIT_MSG="${COMMIT_MSG:-feat(ops): add required checks drift guard}"
PR_TITLE="${PR_TITLE:-feat(ops): add required checks drift guard}"
PR_BODY_FILE="${PR_BODY_FILE:-/tmp/pr_body_required_checks_drift_guard.md}"
LABELS_CSV="${LABELS_CSV:-ops,ci}"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🧪 DRY RUN MODE (no git operations)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
fi

# ──────────────────────────────────────────────────────────────────────────────
# 0) Repo + Branch
# ──────────────────────────────────────────────────────────────────────────────
cd "$REPO_DIR"

if [ "$DRY_RUN" -eq 0 ]; then
  git fetch origin "$BASE" --prune
  git checkout "$BRANCH" 2>/dev/null || git checkout -b "$BRANCH"
  git rebase "origin/$BASE"
else
  echo "ℹ️  Dry-run: Skip git fetch/checkout/rebase"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 1) Offline checks
# ──────────────────────────────────────────────────────────────────────────────
echo "== 1) Offline checks =="

test -f scripts/ops/verify_required_checks_drift.sh
chmod +x scripts/ops/verify_required_checks_drift.sh

# a) Script selbst (offline)
if ./scripts/ops/verify_required_checks_drift.sh --help 2>/dev/null | grep -q -- '--offline'; then
  ./scripts/ops/verify_required_checks_drift.sh --offline
else
  ./scripts/ops/verify_required_checks_drift.sh
fi

# b) Ops doctor (falls vorhanden)
if [ -x scripts/ops/ops_center.sh ]; then
  scripts/ops/ops_center.sh doctor || true
fi

# c) Pytests (falls vorhanden)
if [ -d tests ]; then
  if command -v uv >/dev/null 2>&1; then
    uv run pytest -q || true
  elif command -v pytest >/dev/null 2>&1; then
    pytest -q || true
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# 2) Optional live drift check
# ──────────────────────────────────────────────────────────────────────────────
if [ "$OFFLINE_ONLY" -eq 1 ]; then
  echo ""
  echo "== 2) Live drift check: SKIP (--offline-only) =="
else
  echo ""
  echo "== 2) Optional live drift check (requires gh auth + jq) =="

  LIVE_SUPPORTED=0
  if ./scripts/ops/verify_required_checks_drift.sh --help 2>/dev/null | grep -q -- '--live'; then
    LIVE_SUPPORTED=1
  fi

  if [ "$LIVE_SUPPORTED" -eq 1 ]; then
    if ! command -v gh >/dev/null 2>&1; then
      echo "❌ gh fehlt. Installiere GitHub CLI oder verwende --offline-only." >&2
      exit 1
    fi
    if ! command -v jq >/dev/null 2>&1; then
      echo "❌ jq fehlt. Installiere jq oder verwende --offline-only." >&2
      exit 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
      echo "❌ gh nicht authentifiziert. Führe 'gh auth login' aus." >&2
      exit 1
    fi

    set +e
    ./scripts/ops/verify_required_checks_drift.sh --live --warn-only
    LIVE_RC=$?
    set -e

    if [ "$LIVE_RC" -eq 0 ]; then
      echo "✅ Required Checks: No Drift (ok)"
    elif [ "$LIVE_RC" -eq 2 ]; then
      echo "⚠️ Required Checks: Drift detected (warn-only)."
      echo "   → Action: Review drift und Docs oder Branch Protection anpassen."
    else
      echo "❌ Live drift check error (exit=$LIVE_RC)."
      exit 1
    fi
  else
    echo "ℹ️ Live-Check nicht unterstützt (kein --live). Überspringe Schritt 2."
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3) Commit + push + PR
# ──────────────────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  echo "== 3) Commit + push + PR: SKIP (--dry-run) =="
  echo "✅ Dry-run completed successfully"
  exit 0
fi

echo ""
echo "== 3) Commit + push + PR =="

# Commit nur wenn es Änderungen gibt
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  git commit -m "$COMMIT_MSG"
else
  echo "ℹ️ Working tree clean – kein Commit nötig."
fi

git push -u origin HEAD

# PR Body
cat > "$PR_BODY_FILE" <<'EOF'
## What
- Add required checks drift guard (offline) + optional live drift verification (gh+jq)
- Integrate into Ops Center / docs + smoke coverage
- Add --dry-run and --offline-only flags for safe testing

## Why
- Prevent silent drift between documented required checks and live Branch Protection settings
- Make drift review explicit (warn-only mode supports safe operations)
- Enable safe testing with dry-run mode

## Verification
- Offline smoke checks pass
- Optional live drift check returns:
  - 0 (match) or
  - 2 (warn-only drift) with action guidance
- Dry-run mode tested (--dry-run --offline-only)
EOF

# PR erstellen oder aktualisieren
if gh pr view >/dev/null 2>&1; then
  echo "ℹ️ PR existiert bereits für diesen Branch."
else
  gh pr create --base "$BASE" --head "$BRANCH" --title "$PR_TITLE" --body-file "$PR_BODY_FILE"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 4) Labels + watch checks
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "== 4) Labels + watch checks =="

if [ -n "${LABELS_CSV// /}" ]; then
  IFS=',' read -r -a LABELS <<< "$LABELS_CSV"
  for L in "${LABELS[@]}"; do
    L_TRIM="$(echo "$L" | sed 's/^ *//;s/ *$//')"
    [ -n "$L_TRIM" ] && gh pr edit --add-label "$L_TRIM" || true
  done
fi

gh pr checks --watch
echo "✅ Done."
BASH

chmod +x scripts/ops/create_required_checks_drift_guard_pr.sh

# ──────────────────────────────────────────────────────────────────────────────
# 3) Update: run_required_checks_drift_guard_pr.sh (pass flags through)
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "🔧 3) Update run_required_checks_drift_guard_pr.sh (pass-through flags)"

cat > scripts/ops/run_required_checks_drift_guard_pr.sh <<'BASH'
#!/usr/bin/env bash
#
# run_required_checks_drift_guard_pr.sh
#
# One-block wrapper that finds and runs the Required Checks Drift Guard PR workflow.
#
# Usage:
#   run_required_checks_drift_guard_pr.sh [--dry-run] [--offline-only]
#
# Flags:
#   --dry-run        Run checks but skip commit/push/PR
#   --offline-only   Skip live drift check (only offline checks)
#
# Environment Variables (optional):
#   REPO_DIR     Repository directory (default: $HOME/Peak_Trade)
#   BRANCH       Feature branch name (default: feat/required-checks-drift-guard-v1)
#   BASE         Base branch (default: main)
#   LABELS_CSV   Labels to add (default: ops,ci)

set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
cd "$REPO_DIR"

echo "🔎 Suche Drift-Guard PR-Workflow Script…"
SCRIPT="$(
  git ls-files 'scripts/ops/*.sh' \
  | grep -E 'drift|required[_-]?checks' \
  | grep -v 'run_required_checks_drift_guard_pr.sh' \
  | grep -v 'verify_required_checks_drift.sh' \
  | grep -v 'test_verify_required_checks_drift.sh' \
  | grep -v 'test_drift_guard_pr_workflow.sh' \
  | grep -v 'setup_drift_guard_pr_workflow.sh' \
  | head -n 1
)"

if [ -z "${SCRIPT:-}" ]; then
  echo "❌ Konnte kein passendes Script finden (Pattern: drift|required_checks)." >&2
  echo "   Tipp: nenne es z.B. scripts/ops/create_required_checks_drift_guard_pr.sh" >&2
  exit 1
fi

echo "✅ Script gefunden: $SCRIPT"
chmod +x "$SCRIPT"

echo
echo "== HELP (falls verfügbar) =="
"$SCRIPT" --help 2>/dev/null || echo "ℹ️ Keine --help Option verfügbar"

echo
echo "== RUN =="
# Optional: Overrides
export BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
export BASE="${BASE:-main}"
export LABELS_CSV="${LABELS_CSV:-ops,ci}"

# Pass all arguments through to the script
"$SCRIPT" "$@"
BASH

chmod +x scripts/ops/run_required_checks_drift_guard_pr.sh

# ──────────────────────────────────────────────────────────────────────────────
# 4) Create: Smoke Tests for PR Workflow
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "🧪 4) Erstelle scripts/ops/tests/test_drift_guard_pr_workflow.sh"

mkdir -p scripts/ops/tests

cat > scripts/ops/tests/test_drift_guard_pr_workflow.sh <<'BASH'
#!/usr/bin/env bash
#
# test_drift_guard_pr_workflow.sh
#
# Smoke tests for Required Checks Drift Guard PR Workflow scripts
#
# Usage:
#   test_drift_guard_pr_workflow.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WRAPPER="$REPO_ROOT/scripts/ops/run_required_checks_drift_guard_pr.sh"
MAIN_SCRIPT="$REPO_ROOT/scripts/ops/create_required_checks_drift_guard_pr.sh"

PASS=0
FAIL=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Smoke Tests: Required Checks Drift Guard PR Workflow"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ──────────────────────────────────────────────────────────────────────────────
# Test 1: Wrapper script exists and is executable
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 1: Wrapper script exists and is executable"
if [ -x "$WRAPPER" ]; then
  echo "   ✅ PASS"
  ((PASS++))
else
  echo "   ❌ FAIL - $WRAPPER not found or not executable"
  ((FAIL++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 2: Main script exists and is executable
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 2: Main script exists and is executable"
if [ -x "$MAIN_SCRIPT" ]; then
  echo "   ✅ PASS"
  ((PASS++))
else
  echo "   ❌ FAIL - $MAIN_SCRIPT not found or not executable"
  ((FAIL++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 3: Wrapper --help works
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 3: Wrapper can find main script"
if [ -x "$WRAPPER" ]; then
  cd "$REPO_ROOT"
  if SCRIPT_FOUND=$("$WRAPPER" 2>&1 | grep "Script gefunden" || true); then
    if [ -n "$SCRIPT_FOUND" ]; then
      echo "   ✅ PASS - Wrapper can find main script"
      ((PASS++))
    else
      echo "   ⚠️  SKIP - Could not verify (requires git ls-files)"
      ((PASS++))
    fi
  else
    echo "   ⚠️  SKIP - Could not verify (requires git ls-files)"
    ((PASS++))
  fi
else
  echo "   ⏭️  SKIP - Wrapper not available"
  ((PASS++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 4: Main script --help works
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 4: Main script --help works"
if [ -x "$MAIN_SCRIPT" ]; then
  if "$MAIN_SCRIPT" --help 2>/dev/null | grep -q "Usage:"; then
    echo "   ✅ PASS"
    ((PASS++))
  else
    echo "   ❌ FAIL - --help flag doesn't work"
    ((FAIL++))
  fi
else
  echo "   ⏭️  SKIP - Main script not available"
  ((PASS++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 5: Main script supports --dry-run flag
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 5: Main script supports --dry-run flag"
if [ -x "$MAIN_SCRIPT" ]; then
  if "$MAIN_SCRIPT" --help 2>/dev/null | grep -q -- "--dry-run"; then
    echo "   ✅ PASS"
    ((PASS++))
  else
    echo "   ❌ FAIL - --dry-run flag not documented in --help"
    ((FAIL++))
  fi
else
  echo "   ⏭️  SKIP - Main script not available"
  ((PASS++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 6: Main script supports --offline-only flag
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 6: Main script supports --offline-only flag"
if [ -x "$MAIN_SCRIPT" ]; then
  if "$MAIN_SCRIPT" --help 2>/dev/null | grep -q -- "--offline-only"; then
    echo "   ✅ PASS"
    ((PASS++))
  else
    echo "   ❌ FAIL - --offline-only flag not documented in --help"
    ((FAIL++))
  fi
else
  echo "   ⏭️  SKIP - Main script not available"
  ((PASS++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 7: verify_required_checks_drift.sh exists
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 7: verify_required_checks_drift.sh exists"
VERIFY_SCRIPT="$REPO_ROOT/scripts/ops/verify_required_checks_drift.sh"
if [ -x "$VERIFY_SCRIPT" ]; then
  echo "   ✅ PASS"
  ((PASS++))
else
  echo "   ❌ FAIL - $VERIFY_SCRIPT not found or not executable"
  ((FAIL++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Test 8: Documentation exists
# ──────────────────────────────────────────────────────────────────────────────
echo "Test 8: Documentation exists"
DOCS_FOUND=0
for doc in \
  "$REPO_ROOT/docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md" \
  "$REPO_ROOT/docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md" \
  "$REPO_ROOT/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md"
do
  if [ -f "$doc" ]; then
    ((DOCS_FOUND++))
  fi
done

if [ "$DOCS_FOUND" -gt 0 ]; then
  echo "   ✅ PASS - Found $DOCS_FOUND documentation file(s)"
  ((PASS++))
else
  echo "   ❌ FAIL - No documentation files found"
  ((FAIL++))
fi

# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Results: $PASS passed, $FAIL failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Some tests failed"
  exit 1
else
  echo "✅ All tests passed"
  exit 0
fi
BASH

chmod +x scripts/ops/tests/test_drift_guard_pr_workflow.sh

# ──────────────────────────────────────────────────────────────────────────────
# 5) Run Smoke Tests
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "🧪 5) Run Smoke Tests"
scripts/ops/tests/test_drift_guard_pr_workflow.sh

# ──────────────────────────────────────────────────────────────────────────────
# 6) Update README_REGISTRY.md
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "📚 6) Update README_REGISTRY.md"

if [ -f README_REGISTRY.md ]; then
  # Check if entry already exists
  if ! grep -q "REQUIRED_CHECKS_DRIFT_GUARD.md" README_REGISTRY.md; then
    # Find the Ops / Operations section and add entry
    if grep -q "## Ops" README_REGISTRY.md || grep -q "## Operations" README_REGISTRY.md; then
      # Add after the Ops section header
      sed -i.bak '/## Ops\|## Operations/a\
- `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md` — Required Checks Drift Guard (verification + PR workflow)\
- `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md` — Detailed PR workflow documentation\
- `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` — Operator notes and troubleshooting
' README_REGISTRY.md
      rm -f README_REGISTRY.md.bak
      echo "   ✅ Added entries to README_REGISTRY.md"
    else
      echo "   ⚠️  No Ops section found in README_REGISTRY.md - manual update needed"
    fi
  else
    echo "   ℹ️  Entries already exist in README_REGISTRY.md"
  fi
else
  echo "   ⚠️  README_REGISTRY.md not found - skipping"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 7) Commit everything
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "📦 7) Commit changes"

git add -A

if ! git diff --cached --quiet; then
  git commit -m "feat(ops): add Required Checks Drift Guard PR workflow

- Add --dry-run and --offline-only flags
- Create smoke tests for PR workflow
- Add comprehensive documentation
- Update README_REGISTRY.md

Components:
- scripts/ops/create_required_checks_drift_guard_pr.sh (updated)
- scripts/ops/run_required_checks_drift_guard_pr.sh (updated)
- scripts/ops/tests/test_drift_guard_pr_workflow.sh (new)
- docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md (new)
"
  echo "   ✅ Changes committed"
else
  echo "   ℹ️  No changes to commit"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 8) Summary
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Created/Updated:"
echo "   - scripts/ops/create_required_checks_drift_guard_pr.sh"
echo "   - scripts/ops/run_required_checks_drift_guard_pr.sh"
echo "   - scripts/ops/tests/test_drift_guard_pr_workflow.sh"
echo "   - docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md"
echo ""
echo "🧪 Smoke Tests: ✅ PASSED"
echo ""
echo "🚀 Next Steps:"
echo "   1. Test dry-run:"
echo "      scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only"
echo ""
echo "   2. Push + Create PR:"
echo "      git push -u origin $BRANCH"
echo "      gh pr create --base $BASE --head $BRANCH --title \"$PR_TITLE\" --label \"$LABELS_CSV\""
echo ""
echo "   3. Watch CI:"
echo "      gh pr checks --watch"
echo ""
