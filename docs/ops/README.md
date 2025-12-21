# Peak_Trade – Ops PR Tools

Zwei Bash-Skripte zur Verwaltung und Analyse von Pull Requests im Peak_Trade Repository.

---

## 📋 Übersicht

| Skript | Zweck | Output | Network | Safe Default |
|--------|-------|--------|---------|--------------|
| `pr_inventory_full.sh` | Vollständiges PR-Inventar + Analyse | JSON/CSV/Markdown | ✅ Read-only | ✅ Ja |
| `label_merge_log_prs.sh` | Automatisches Labeln von Merge-Log-PRs | GitHub Labels | ✅ Write | ✅ DRY_RUN=1 |

---

## 🔍 PR Inventory (vollständig)

Generiert ein vollständiges PR-Inventar inkl. Analyse, CSV-Export und Markdown-Report.

### Verwendung

```bash
# Standard (alle Defaults)
./scripts/ops/pr_inventory_full.sh

# Mit custom Repository
REPO=owner/name ./scripts/ops/pr_inventory_full.sh

# Mit custom Output-Verzeichnis
OUT_ROOT=$HOME/Peak_Trade/reports/ops ./scripts/ops/pr_inventory_full.sh

# Mit Limit
LIMIT=500 ./scripts/ops/pr_inventory_full.sh

# Alle Optionen kombiniert
REPO=rauterfrank-ui/Peak_Trade \
LIMIT=1000 \
OUT_ROOT=/tmp \
./scripts/ops/pr_inventory_full.sh

# Help anzeigen
./scripts/ops/pr_inventory_full.sh --help
```

### Output-Struktur

```
/tmp/peak_trade_pr_inventory_<timestamp>/
├── open.json              # Alle offenen PRs
├── closed_all.json        # Alle geschlossenen PRs (inkl. merged)
├── merged.json            # Nur gemergte PRs
├── merge_logs.csv         # Merge-Log-PRs als CSV
└── PR_INVENTORY_REPORT.md # Zusammenfassung + Statistiken
```

### Report-Inhalt

Der `PR_INVENTORY_REPORT.md` enthält:

- **Totals**: Open, Closed, Merged, Closed (unmerged)
- **Category Counts**:
  - `merge_log` – PRs mit Pattern `^docs\(ops\): add PR #\d+ merge log`
  - `ops_infra` – Ops/Workflow/CI/Audit/Runbook-PRs
  - `format_sweep` – Format/Lint/Pre-commit-PRs
  - `other` – Alle anderen
- **Latest merge-log PRs**: Top 25 mit Links

### Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REPO` | `rauterfrank-ui/Peak_Trade` | GitHub Repository |
| `LIMIT` | `1000` | Max. PRs pro Abfrage |
| `OUT_ROOT` | `/tmp` | Output-Verzeichnis |

### Beispiel-Output

```markdown
# Peak_Trade – PR Inventory Report

- Generated: 2025-12-21 14:30:00

## Totals

- Open PRs: **3**
- Closed (all): **215**
- Merged: **198**
- Closed (unmerged): **17**

## Category counts (closed_all)

- merge_log: **147**
- ops_infra: **23**
- format_sweep: **8**
- other: **37**

## Latest merge-log PRs (top 25)

- PR #208 — docs(ops): add PR #207 merge log (2025-12-20T10:15:00Z)
  - https://github.com/rauterfrank-ui/Peak_Trade/pull/208
...
```

---

## 🏷️ Label Merge-Log PRs

Findet alle Merge-Log-PRs und labelt sie automatisch (mit DRY_RUN-Protection).

### Verwendung

```bash
# DRY RUN (Standard): Nur anzeigen, keine Änderungen
./scripts/ops/label_merge_log_prs.sh

# DRY RUN mit custom Label
LABEL="documentation/merge-log" ./scripts/ops/label_merge_log_prs.sh

# ECHT: Labels wirklich anwenden
DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

# Mit Label-Auto-Creation
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

# Alle Optionen kombiniert
REPO=rauterfrank-ui/Peak_Trade \
LABEL="ops/merge-log" \
LIMIT=1000 \
ENSURE_LABEL=1 \
DRY_RUN=0 \
./scripts/ops/label_merge_log_prs.sh

# Help anzeigen
./scripts/ops/label_merge_log_prs.sh --help
```

### Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REPO` | `rauterfrank-ui/Peak_Trade` | GitHub Repository |
| `LABEL` | `ops/merge-log` | Label-Name |
| `LIMIT` | `1000` | Max. PRs pro Abfrage |
| `DRY_RUN` | `1` | 1 = nur anzeigen, 0 = wirklich labeln |
| `ENSURE_LABEL` | `0` | 1 = Label erstellen falls nicht vorhanden |

### Pattern-Matching

Das Skript findet PRs mit folgendem Titel-Pattern (case-insensitive):

```
^docs\(ops\): add PR #\d+ merge log
```

**Beispiele:**
- ✅ `docs(ops): add PR #207 merge log`
- ✅ `Docs(ops): Add PR #123 Merge Log`
- ❌ `feat: add merge log for PR #123`
- ❌ `docs(ops): update merge log`

### Output

```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️  Peak_Trade: Label merge-log PRs
Repo: rauterfrank-ui/Peak_Trade | Label: ops/merge-log | DRY_RUN=1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found merge-log PRs: 147
List: /tmp/peak_trade_merge_log_prs.txt

DRY RUN (no changes). First 30 PRs:
 - PR #208
 - PR #206
 - PR #204
 ...

To actually apply labels:
  DRY_RUN=0 LABEL="ops/merge-log" scripts/ops/label_merge_log_prs.sh
```

---

## 🛡️ Sicherheitsfeatures

### Beide Skripte

- ✅ `set -euo pipefail` für strikte Fehlerbehandlung
- ✅ Preflight-Checks für `gh` CLI und Python
- ✅ `gh auth status` Validierung
- ✅ Help-Text (`--help`, `-h`)
- ✅ Auto-Detection von `python3` / `python`

### `label_merge_log_prs.sh` spezifisch

- ✅ **DRY_RUN=1** als Standard (keine versehentlichen Änderungen)
- ✅ Empty-Result-Check (Exit wenn keine PRs gefunden)
- ✅ Optional: Label-Auto-Creation mit `ENSURE_LABEL=1`

---

## 🧩 Ops Bash Run Helpers (strict/robust)

Für konsistente "fail-fast" vs "warn-only" Semantik in neuen Ops-Skripten nutzen wir:
- `scripts/ops/run_helpers.sh` (Quelle der Wahrheit, inkl. Quick Reference im Header)

**Default:** strict (fail fast)  
**Robust mode:** `PT_MODE=robust bash <script>.sh` (optional: `MODE=robust`)

**Minimal usage (copy/paste):**
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=run_helpers.sh
source "${SCRIPT_DIR}/run_helpers.sh"

pt_require_cmd gh
pt_section "Strict core"
pt_run_required "Update main" bash -lc 'git checkout main && git pull --ff-only'

pt_section "Main work"
pt_run "Do the thing" bash -lc 'echo "work"'

pt_section "Optional extras"
pt_run_optional "Dry-run labels" bash scripts/ops/label_merge_log_prs.sh
```

**Hinweis:** Bestehende Skripte (`pr_inventory_full.sh`, `label_merge_log_prs.sh`) verwenden die Helpers **nicht** (bleiben im Original-Stil). Nur für neue Skripte gedacht.

---

## 📦 Voraussetzungen

### System-Tools

```bash
# GitHub CLI
brew install gh
gh auth login

# Python (3.x bevorzugt)
python3 --version
# oder
python --version
```

### Python-Module

Beide Skripte verwenden nur Standard-Library-Module:
- `json`
- `re`
- `csv`
- `pathlib`
- `datetime`
- `sys`

---

## 🔄 Workflow-Beispiele

### 1. Vollständige PR-Analyse

```bash
# Step 1: Inventory generieren
./scripts/ops/pr_inventory_full.sh

# Step 2: Report öffnen
code /tmp/peak_trade_pr_inventory_$(date +%Y%m%d)*/PR_INVENTORY_REPORT.md

# Step 3: CSV analysieren
open /tmp/peak_trade_pr_inventory_$(date +%Y%m%d)*/merge_logs.csv
```

### 2. Merge-Log-PRs labeln (sicher)

```bash
# Step 1: DRY RUN (was würde passieren?)
./scripts/ops/label_merge_log_prs.sh

# Step 2: Review der gefundenen PRs
cat /tmp/peak_trade_merge_log_prs.txt

# Step 3: Label erstellen (falls nötig) + anwenden
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh
```

### 3. Batch-Processing (beide Skripte)

```bash
#!/usr/bin/env bash
# ops_pr_maintenance.sh

# 1) Inventory
echo "=== Generating PR Inventory ==="
OUT_ROOT=$HOME/Peak_Trade/reports/ops ./scripts/ops/pr_inventory_full.sh

# 2) Labeling
echo ""
echo "=== Labeling Merge-Log PRs ==="
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/ops/label_merge_log_prs.sh

echo ""
echo "✅ PR Maintenance complete"
```

---

## 🐛 Troubleshooting

### Error: `gh CLI fehlt`

```bash
brew install gh
gh auth login
```

### Error: `gh ist nicht authentifiziert`

```bash
gh auth login
gh auth status
```

### Error: `python fehlt`

```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3
```

### Label existiert nicht

```bash
# Option 1: Auto-Create
ENSURE_LABEL=1 DRY_RUN=0 ./scripts/label_merge_log_prs.sh

# Option 2: Manuell erstellen
gh label create "ops/merge-log" \
  --description "Merge-log documentation PRs" \
  --color "ededed"
```

### DRY_RUN deaktivieren funktioniert nicht

```bash
# Richtig:
DRY_RUN=0 ./scripts/label_merge_log_prs.sh

# Falsch (String wird als truthy interpretiert):
DRY_RUN=false ./scripts/label_merge_log_prs.sh
```

---

## 📝 Logging & Debugging

### Temporäre Dateien

```bash
# PR Nummern (label_merge_log_prs.sh)
cat /tmp/peak_trade_merge_log_prs.txt

# Inventory Output (pr_inventory_full.sh)
ls -lh /tmp/peak_trade_pr_inventory_*/
```

### Debug-Modus aktivieren

```bash
# Bash Debug-Output
bash -x ./scripts/ops/pr_inventory_full.sh

# Mit set -x im Skript
# Füge nach der shebang-Zeile hinzu:
# set -x
```

---

## 🧪 Tests

Beide Skripte haben entsprechende Tests im `tests/`-Verzeichnis.

### Relevante Test-Dateien

```bash
# Workflow-Tests
tests/test_ops_merge_log_workflow_wrapper.py

# Integration-Tests (falls vorhanden)
tests/integration/test_ops_pr_tools.py
```

### Test-Ausführung

```bash
# Einzelner Test
pytest tests/test_ops_merge_log_workflow_wrapper.py -v

# Alle Ops-Tests
pytest tests/ -k "ops" -v
```

---

## 📚 Verwandte Dokumentation

- [Peak_Trade Tooling & Evidence Chain Runbook](../Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md)
- [CI Large PR Implementation Report](../CI_LARGE_PR_IMPLEMENTATION_REPORT.md)
- [Merge Log Workflow](../docs/ops/PR_208_MERGE_LOG.md)

---

## 📋 Merge Logs

- [PR #235](PR_235_MERGE_LOG.md) — fix(ops): improve label_merge_log_prs.sh to find open PRs (merged 2025-12-21)
- [PR #234](PR_234_MERGE_LOG.md) — chore(ops): PR inventory + merge-log labeling scripts (merged 2025-12-21)

---

## 🔮 Zukünftige Erweiterungen

### Geplant

- [ ] GitHub Actions Integration (automatisches Labeling bei PR-Creation)
- [ ] Slack/Discord-Benachrichtigungen bei Labeling
- [ ] Extended Report mit Contributor-Statistiken
- [ ] CSV-Export für alle Kategorien (nicht nur merge_logs)
- [ ] Label-Bulk-Removal-Skript (Reversal-Tool)

### Nice-to-Have

- [ ] Web-UI für PR-Inventory (Quarto Dashboard)
- [ ] Automatische PR-Cleanup-Empfehlungen
- [ ] Integration mit `knowledge_db` (AI-gestütztes Tagging)
- [ ] Time-Series-Analyse (PR-Volume über Zeit)

---

## 💡 Tipps & Best Practices

### Performance

```bash
# Für große Repos: Limit reduzieren
LIMIT=500 ./scripts/ops/pr_inventory_full.sh

# Parallele Ausführung (wenn mehrere Repos)
for repo in repo1 repo2 repo3; do
  REPO="owner/$repo" ./scripts/ops/pr_inventory_full.sh &
done
wait
```

### Sicherheit

```bash
# Immer zuerst DRY_RUN
./scripts/ops/label_merge_log_prs.sh

# Label-Creation separat testen
ENSURE_LABEL=1 DRY_RUN=1 ./scripts/ops/label_merge_log_prs.sh
```

### Maintenance

```bash
# Alte Inventory-Outputs aufräumen (älter als 30 Tage)
find /tmp -name "peak_trade_pr_inventory_*" -type d -mtime +30 -exec rm -rf {} +

# Cleanup-Skript erstellen
cat > scripts/ops/cleanup_old_inventories.sh <<'EOF'
#!/usr/bin/env bash
find /tmp -name "peak_trade_pr_inventory_*" -type d -mtime +30 -print -exec rm -rf {} +
EOF
chmod +x scripts/ops/cleanup_old_inventories.sh
```

---

## 📁 Datei-Struktur

```
/Users/frnkhrz/Peak_Trade/scripts/
├── ops/
│   ├── pr_inventory_full.sh       # ✅ PR Inventory + Analyse
│   └── label_merge_log_prs.sh     # ✅ Automatisches Labeln
└── OPS_PR_TOOLS_README.md         # ✅ Diese Dokumentation
```

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-21  
**Maintainer:** Peak_Trade Ops Team
