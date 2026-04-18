# Required Checks Drift Guard — PR Workflow

Kanonische Quelle: `config/ci/required_status_checks.json` (JSON SSOT).

Dieses Workflow-Skript erstellt automatisch einen PR für das **Required Checks Drift Guard** Feature und folgt dem gleichen Operator-Pattern wie `create_and_open_merge_log_pr.sh`.

## Was das Skript macht

### Phase 1: Offline Checks
- Führt `scripts/ops/verify_required_checks_drift.sh` aus (offline).
- Führt `scripts&#47;ops&#47;ops_center.sh doctor` aus (falls vorhanden).
- Führt `pytest` aus (nur wenn ein `tests/` Verzeichnis existiert; best-effort).

### Phase 2: Live Drift Check (optional)
- Prüft, ob `gh` und `jq` verfügbar sind und ob `gh auth status` erfolgreich ist.
- Führt Live-Check gegen GitHub Branch Protection / Required Checks aus (warn-only möglich).

**Exit Codes (Live-Teil)**
- `0` — ✅ **Kein Drift** (JSON SSOT effective required und live identisch)
- `2` — ⚠️ **Drift erkannt (warn-only)** → Review drift, **JSON SSOT aktualisieren** oder **Branch Protection** anpassen
- `1` — ❌ **Fehler** (Preflight failed: `gh`/`jq`/Auth Problem)

### Phase 3: Commit + Push + PR
- Erstellt einen Commit **nur wenn Änderungen vorhanden sind**.
- Pusht den Branch.
- Erstellt einen PR mit strukturiertem Body (What/Why/Verification).

### Phase 4: Labels + CI Watch
- Fügt Labels hinzu (default: `ops,ci`).
- Überwacht CI Checks via `gh pr checks --watch`.

---

## Quick Start

### Option 1: Wrapper-Skript (empfohlen)

```bash
cd ~/Peak_Trade
scripts/ops/run_required_checks_drift_guard_pr.sh
```

Das Wrapper-Skript findet automatisch das passende Drift-Workflow-Skript und führt es aus.

### Option 2: Direkt

```bash
cd ~/Peak_Trade
scripts/ops/create_required_checks_drift_guard_pr.sh
```

### Option 3: Copy/Paste — Terminal/iTerm (End-to-End)

Dieser Block findet das passende Drift-Workflow-Skript automatisch (falls der Dateiname variiert) und führt es aus:

```bash
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
# Optional: Overrides (nur relevant, wenn das Script ENV-Overrides unterstützt)
export BRANCH="${BRANCH:-feat/required-checks-drift-guard-v1}"
export BASE="${BASE:-main}"
export LABELS_CSV="${LABELS_CSV:-ops,ci}"

"$SCRIPT"
```

---

## Environment Variables (optional)

Alle Skripte unterstützen folgende Overrides:

```bash
# Branch configuration
export BRANCH="feat/my-custom-branch"
export BASE="develop"  # default: main

# PR configuration
export COMMIT_MSG="feat(ops): custom commit message"
export PR_TITLE="feat(ops): custom PR title"

# Labels (comma-separated)
export LABELS_CSV="ops,ci,infrastructure"

# Repository location
export REPO_DIR="/path/to/your/repo"
```

---

## Skript-Architektur

```
scripts/ops/
├── run_required_checks_drift_guard_pr.sh
│   └─> Finder + Wrapper (one-block style)
│
└── create_required_checks_drift_guard_pr.sh
    ├─> Phase 1: Offline Checks
    ├─> Phase 2: Live Drift Check
    ├─> Phase 3: Commit + Push + PR
    └─> Phase 4: Labels + CI Watch
```

---

## Integration mit Ops Center

Das Drift Guard Feature ist vollständig in `ops_center.sh doctor` integriert:

```bash
# Full health check (includes drift guard)
scripts/ops/ops_center.sh doctor

# Quick health check (skip some tests)
scripts/ops/ops_center.sh doctor --quick
```

Die `doctor` Ausgabe enthält:

```
🧭 Required Checks Drift Guard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Check: Branch Protection Required Checks (JSON SSOT effective required vs live)
   ✅ PASS - JSON SSOT matches live state

   oder

   ⚠️  WARN - Drift detected between doc and live
      [diff details here]
   📖 Details: scripts/ops/verify_required_checks_drift.sh
```

---

## Troubleshooting

### "❌ gh fehlt"
```bash
# macOS
brew install gh

# Authenticate
gh auth login
```

### "❌ jq fehlt"
```bash
# macOS
brew install jq
```

### "❌ Konnte kein passendes Script finden"
Stelle sicher, dass das Skript committed ist:
```bash
git add scripts/ops/create_required_checks_drift_guard_pr.sh
git commit -m "feat(ops): add drift guard PR workflow"
```

### "⚠️ Drift detected (warn-only)"
Das ist **kein Fehler**, sondern eine Warnung. Du hast zwei Optionen:
1. **Dokumentation aktualisieren** (falls Live-State korrekt ist)
2. **Branch Protection anpassen** (falls JSON SSOT korrekt ist)

Siehe: `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`

---

## Related Documentation

- `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` — Operator Guide
- `docs/ops/OPS_OPERATOR_CENTER.md` — Ops Center Overview
- `scripts/ops/verify_required_checks_drift.sh` — Core Drift Check Script
- `scripts/ops/tests/test_verify_required_checks_drift.sh` — Smoke Tests

---

## Example Output

```
🔎 Suche Drift-Guard PR-Workflow Script…
✅ Script gefunden: scripts/ops/create_required_checks_drift_guard_pr.sh

== HELP (falls verfügbar) ==
ℹ️ Keine --help Option verfügbar

== RUN ==
== 1) Offline checks ==
✅ Required Checks: No Drift (ok)

== 2) Optional live drift check (requires gh auth + jq) ==
✅ Required Checks: No Drift (ok)

== 3) Commit + push + PR ==
ℹ️ Working tree clean – kein Commit nötig.
Everything up-to-date

== 4) Labels + watch checks (optional) ==
✅ Done.
```

---

**Last Updated:** 2025-12-25
**Maintained by:** Peak_Trade Ops Team
