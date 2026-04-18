# Required Checks Drift Guard — Quick Start

Kanonische Quelle: `config/ci/required_status_checks.json` (JSON SSOT).

## 🚀 One-Liner Setup (Copy/Paste)

```bash
cd ~/Peak_Trade && bash scripts/ops/setup_drift_guard_pr_workflow.sh
```

Das Setup-Skript:
- ✅ Erstellt/aktualisiert alle Workflow-Skripte
- ✅ Fügt `--dry-run` und `--offline-only` Flags hinzu
- ✅ Erstellt Smoke Tests
- ✅ Generiert vollständige Dokumentation
- ✅ Aktualisiert README_REGISTRY.md
- ✅ Führt Tests aus
- ✅ Committed alle Änderungen

---

## 🧪 Testing (Dry-Run)

### Option 1: Offline Only (schnellster Test)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only
```
- Nur Offline-Checks
- Kein `gh`/`jq` erforderlich
- Keine Git-Operationen

### Option 2: Mit Live-Check (vollständiger Test)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run
```
- Offline + Live-Checks
- Benötigt `gh` + `jq` + Auth
- Keine Git-Operationen
- Zeigt Drift-Status

---

## 🚢 Production Run

```bash
scripts/ops/run_required_checks_drift_guard_pr.sh
```

Oder mit Custom Config:

```bash
export BRANCH="feat/my-custom-drift-check"
export BASE="develop"
export LABELS_CSV="ops,ci,infrastructure"

scripts/ops/run_required_checks_drift_guard_pr.sh
```

---

## 📦 Was wurde erstellt?

### Skripte
```
scripts/ops/
├── setup_drift_guard_pr_workflow.sh          # 🆕 Setup-Skript
├── create_required_checks_drift_guard_pr.sh  # ✏️ Updated (+ flags)
├── run_required_checks_drift_guard_pr.sh     # ✏️ Updated (+ pass-through)
├── verify_required_checks_drift.sh           # ✅ Existing
└── tests/
    ├── test_drift_guard_pr_workflow.sh       # 🆕 Smoke Tests
    └── test_verify_required_checks_drift.sh  # ✅ Existing
```

### Dokumentation
```
docs/ops/
├── REQUIRED_CHECKS_DRIFT_GUARD.md            # 🆕 Main Guide
├── REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md # ✅ Existing (detailed)
└── DRIFT_GUARD_QUICK_START.md                # 🆕 This file

docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md # ✅ Existing (root)
```

---

## 🧪 Smoke Tests

### Manuell ausführen
```bash
scripts/ops/tests/test_drift_guard_pr_workflow.sh
```

### Was wird getestet?
- ✅ Wrapper-Skript existiert und ist ausführbar
- ✅ Main-Skript existiert und ist ausführbar
- ✅ Wrapper kann Main-Skript finden
- ✅ `--help` funktioniert
- ✅ `--dry-run` Flag vorhanden
- ✅ `--offline-only` Flag vorhanden
- ✅ `verify_required_checks_drift.sh` existiert
- ✅ Dokumentation vorhanden

---

## 🔧 Flags Reference

### `--dry-run`
- Führt alle Checks aus (offline + optional live)
- **Keine** Git-Operationen (commit/push/PR)
- Perfekt zum Testen ohne Side-Effects

### `--offline-only`
- Skippt Live-Check gegen GitHub API
- Nur lokale/Offline-Checks
- Benötigt **kein** `gh` oder `jq`

### Kombinationen
```bash
# Nur Offline, kein Git
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only

# Offline + Live, kein Git
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run

# Offline + Live, mit Git (Production)
scripts/ops/run_required_checks_drift_guard_pr.sh
```

---

## 📊 Exit Codes

### Offline Checks
- `0` — ✅ Alle Checks erfolgreich
- `1` — ❌ Fehler in Offline-Checks

### Live Checks
- `0` — ✅ Kein Drift (JSON SSOT effective required == live)
- `2` — ⚠️ Drift erkannt (warn-only) → **Nicht fatal**, aber Review erforderlich
- `1` — ❌ Fehler (Preflight: gh/jq/auth Problem)

---

## 🔗 Integration

### Ops Center
```bash
# Drift Check ist in doctor integriert
scripts/ops/ops_center.sh doctor
```

Ausgabe enthält:
```
🧭 Required Checks Drift Guard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Check: Branch Protection Required Checks (JSON SSOT effective required vs live)
   ✅ PASS - JSON SSOT matches live state
```

### CI/CD
```yaml
# .github/workflows/ops-checks.yml
- name: Required Checks Drift Guard
  run: |
    scripts/ops/verify_required_checks_drift.sh --warn-only
```

---

## 🐛 Troubleshooting

### "❌ gh fehlt"
```bash
brew install gh
gh auth login
```

### "❌ jq fehlt"
```bash
brew install jq
```

### "❌ Konnte kein passendes Script finden"
Stelle sicher, dass Skripte committed sind:
```bash
git add scripts/ops/*.sh
git status
```

### "⚠️ Drift detected (warn-only)"
**Das ist kein Fehler!** Du hast zwei Optionen:

1. **JSON SSOT aktualisieren** (wenn Live-State korrekt ist)
   ```bash
   # Update config/ci/required_status_checks.json
   # und pruefe effective_required_contexts = required_contexts - ignored_contexts
   ```

2. **Branch Protection anpassen** (wenn JSON SSOT korrekt ist)
   ```bash
   # Gehe zu GitHub Settings > Branches > Branch Protection Rules
   # Passe "Required status checks" an
   ```

---

## 📚 Related Documentation

- [REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md](REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md) — Main Guide (Operator Notes)
- [REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md](REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md) — Detailed PR Workflow
- [OPS_OPERATOR_CENTER.md](OPS_OPERATOR_CENTER.md) — Ops Center Overview

---

## 💡 Common Workflows

### 1. Initial Setup (einmalig)
```bash
cd ~/Peak_Trade
bash scripts/ops/setup_drift_guard_pr_workflow.sh
```

### 2. Quick Test (täglich)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only
```

### 3. Full Test vor PR (vor Commit)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run
```

### 4. Create PR (nach Feature-Implementierung)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh
```

### 5. Health Check (regelmäßig)
```bash
scripts/ops/ops_center.sh doctor
```

---

**Last Updated:** 2025-12-25  
**Quick Reference:** Copy/Paste friendly commands for peak productivity 🚀
