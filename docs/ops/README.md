# Peak_Trade – Ops Tools

Bash-Skripte und Tools für Repository-Verwaltung, Health-Checks und PR-Analyse im Peak_Trade Repository.

---

## 🎯 Ops Operator Center – Zentraler Einstiegspunkt

**Ein Command für alle Operator-Workflows.**

```bash
# Quick Start
scripts/ops/ops_center.sh status
scripts/ops/ops_center.sh pr 263
scripts/ops/ops_center.sh doctor
scripts/ops/ops_center.sh merge-log
```

### PR Full Workflow Runbook

Für einen vollständigen Ablauf von PR-Erstellung bis Merge und Verifikation steht jetzt ein detailliertes Runbook zur Verfügung. Siehe [PR_FULL_WORKFLOW_RUNBOOK.md](PR_FULL_WORKFLOW_RUNBOOK.md) im gleichen Verzeichnis.

**Commands:**
- `status` — Repository-Status (git + gh)
- `pr <NUM>` — PR reviewen (safe, kein Merge)
- `doctor` — Health-Checks
- `merge-log` — Merge-Log Quick Reference
- `help` — Hilfe

**Dokumentation:** [OPS_OPERATOR_CENTER.md](OPS_OPERATOR_CENTER.md) ⭐

**Design:** Safe-by-default, robust, konsistent.

---

## 🏥 Ops Doctor – Repository Health Check

Umfassendes Diagnose-Tool für Repository-Health-Checks mit strukturiertem JSON- und Human-Readable-Output.

### Quick Start

```bash
# Alle Checks ausführen
./scripts/ops/ops_doctor.sh

# JSON-Output
./scripts/ops/ops_doctor.sh --json

# Spezifische Checks
./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock

# Demo
./scripts/ops/demo_ops_doctor.sh
```

### Features

- ✅ 9 Repository-Health-Checks (Git, Dependencies, Config, Docs, Tests, CI/CD)
- ✅ JSON- und Human-Readable-Output
- ✅ Spezifische Check-Ausführung
- ✅ Exit-Codes für CI/CD-Integration
- ✅ Umfassende Dokumentation

### Dokumentation

- **Vollständige Dokumentation**: [OPS_DOCTOR_README.md](OPS_DOCTOR_README.md)
- **Beispiel-Output**: [ops_doctor_example_output.txt](ops_doctor_example_output.txt)
- **Implementation Summary**: [OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md](../../OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md)

---

## 🚀 PR Management Toolkit

Vollständiges Toolkit für sicheres PR-Review und Merge mit Safe-by-Default-Design.

### Quick Start

```bash
# Review-only (safe default)
scripts/ops/review_and_merge_pr.sh --pr 259

# Review + Merge (2-step, empfohlen)
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main

# One-Shot Workflow
PR=259 ./scripts/ops/pr_review_merge_workflow_template.sh
```

### Features

- ✅ **Safe-by-Default**: Review-only ohne `--merge` Flag
- ✅ **Multi-Layer Validation**: Working Tree, Mergeable Status, Review Decision, CI Checks
- ✅ **Intelligent Retry Logic**: Automatische Retries bei `UNKNOWN` Mergeable-Status
- ✅ **Selective Allow-Fail**: Für bekannte Flaky-Checks (z.B. audit)
- ✅ **Watch Mode**: Wartet automatisch auf CI-Check-Completion
- ✅ **Dry-Run Support**: Test-Modus ohne echte Änderungen

### Dokumentation

- **Quick Start**: [PR_MANAGEMENT_QUICKSTART.md](PR_MANAGEMENT_QUICKSTART.md) ⭐
- **Vollständige Dokumentation**: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)
- **Basis-Tool**: `scripts/ops/review_and_merge_pr.sh`
- **One-Shot Workflow**: `scripts/ops/pr_review_merge_workflow.sh`
- **Template Workflow**: `scripts/ops/pr_review_merge_workflow_template.sh`

---

## 📝 PR Description Templates

Kompakte, operator-zentrierte PR-Beschreibungs-Skeletons für Copy/Paste in GitHub.

### Quick Start

```bash
# Copy/Paste direkt in GitHub PR Description
cat docs/ops/PR_DESCRIPTION_SKELETONS.md

# gh CLI mit Skeleton A (Code PR)
gh pr create --title "feat: ..." --body-file <(sed -n '/^## Skeleton A/,/^## Skeleton B/p' docs/ops/PR_DESCRIPTION_SKELETONS.md | tail -n +3)
```

### Verfügbare Skeletons

| Skeleton | Use Case | Key Sections |
|----------|----------|--------------|
| **A: Feature/Code PR** | Core, Strategies, Execution, Risk, Governance | Safety/Governance + Verification + Risk + Rollback + Operator How-To |
| **B: Docs/Ops PR** | Runbooks, Tooling-Docs, Merge-Logs | Reader Impact + Verification (Links/Commands) |

### Features

- ✅ Direkt als GitHub PR Description nutzbar
- ✅ Kompakt, operator-zentriert, keine Floskeln
- ✅ Safety/Governance-Checklisten (Policy Critic, Guardrails)
- ✅ Verification Gates (CI + Local Commands)
- ✅ Risk Assessment + Rollback Plan
- ✅ Operator How-To für neue Workflows

**Vollständige Dokumentation:** [PR_DESCRIPTION_SKELETONS.md](PR_DESCRIPTION_SKELETONS.md) ⭐

---

## 📋 Übersicht – PR Tools

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

- [PR #240](PR_240_MERGE_LOG.md) — test(ops): add run_helpers adoption guard (merged 2025-12-21)
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
- ✅ Shared helpers (`run_helpers.sh`) für konsistentes Error-Handling

### `label_merge_log_prs.sh` spezifisch

- ✅ **DRY_RUN=1** als Standard (keine versehentlichen Änderungen)
- ✅ Empty-Result-Check (Exit wenn keine PRs gefunden)
- ✅ Optional: Label-Auto-Creation mit `ENSURE_LABEL=1`

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

### Bash Helpers

Die Ops-Skripte nutzen `scripts/ops/run_helpers.sh` für konsistentes Error-Handling:

```bash
# Automatisch gesourced in pr_inventory_full.sh und label_merge_log_prs.sh
# Bietet: pt_run_required(), pt_run_optional(), pt_require_cmd(), pt_log(), etc.

# Modes:
# - PT_MODE=strict (default): Fehler → Abort
# - PT_MODE=robust: Fehler → Warn + Continue

# Beispiel (robust mode):
PT_MODE=robust bash scripts/ops/pr_inventory_full.sh
```

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

## 🧪 Knowledge DB Ops Scripts

| Script | Zweck | Use Case |
|--------|-------|----------|
| `knowledge_smoke_runner.sh` | Manual smoke tests (server restart required) | Lokale Entwicklung |
| `knowledge_smoke_runner_auto.sh` | Auto smoke tests (all 3 modes) | Lokale Entwicklung, vollständiger Test |
| `knowledge_prod_smoke.sh` | Remote production smoke tests | Post-Deployment, Staging/Prod, CI/CD |

### knowledge_prod_smoke.sh — Production Deployment Drill

Remote smoke tests gegen live deployments ohne Server-Restart.

**Verwendung:**

```bash
# Basic
BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh

# With auth
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --token "$TOKEN"

# Strict mode
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --strict

# Custom prefix
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com --prefix /v1/knowledge
```

**Exit Codes:**
- 0 = All checks passed
- 1 = One or more checks failed
- 2 = Degraded in strict mode

**Runbook:** [Knowledge Production Deployment Drill](../runbooks/KNOWLEDGE_PRODUCTION_DEPLOYMENT_DRILL.md)

---

## 📋 Merge Logs

### Workflow

**Standard Process:** Jeder Merge-Log wird als eigener PR erstellt (Review + CI + Audit-Trail).

- **Vollständige Dokumentation:** [MERGE_LOG_WORKFLOW.md](MERGE_LOG_WORKFLOW.md)
- **Template:** [templates/ops/merge_log_template.md](../../templates/ops/merge_log_template.md)

**Quick Start:**

```bash
PR=<NUM>
git checkout -b docs/merge-log-$PR
# Erstelle docs/ops/PR_${PR}_MERGE_LOG.md + link in README
git add docs/ops/PR_${PR}_MERGE_LOG.md docs/ops/README.md
git commit -m "docs(ops): add compact merge log for PR #${PR}"
git push -u origin docs/merge-log-$PR
gh pr create --title "docs(ops): add merge log for PR #${PR}" --body "..."
```

### Liste

- [PR #261](PR_261_MERGE_LOG.md) — chore(ops): add stash triage helper (export-first, safe-by-default) (merged 2025-12-23)
- [PR #250](PR_250_MERGE_LOG.md) — feat(ops): add ops_doctor repo health check tool (merged 2025-12-23)
- [PR #237](PR_237_MERGE_LOG.md) — chore(ops): add shared bash run helpers (strict/robust) (merged 2025-12-21)
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

- [PR #246](PR_246_MERGE_LOG.md) — chore(ops): add knowledge deployment drill e2e + fix prod smoke headers (merged 2025-12-22T21:52:11Z)

## 🛡️ Policy Critic & Governance Triage

### Policy Critic False-Positive Runbook

Operator-Runbook für Format-only PRs, die vom Policy Critic fälschlicherweise blockiert werden.

**Use Case:** Ein PR ändert nur Formatting (Black, Ruff, Import-Sorting), wird aber vom Policy Critic blockiert.

**Runbook:** [POLICY_CRITIC_TRIAGE_RUNBOOK.md](POLICY_CRITIC_TRIAGE_RUNBOOK.md)

**Key Features:**
- ✅ Format-Only Definition + Beispiele
- ✅ Preflight-Checks (gh pr diff/view)
- ✅ Decision Tree für Admin-Bypass
- ✅ Audit-Trail Template (Accountability)
- ✅ Post-Merge Sanity-Checks (ruff/black/pytest)
- ✅ Do-NOT-Bypass Criteria (Execution/Risk/Config/Deps)
- ✅ Rollback-Plan bei Fehlern

**Quick Start:**

```bash
# 1) Preflight-Checks
gh pr view <PR_NUMBER> --json files
gh pr diff <PR_NUMBER> --stat

# 2) Audit-Kommentar (siehe Runbook)
gh pr comment <PR_NUMBER> --body "<AUDIT_TEMPLATE>"

# 3) Admin-Bypass (nur bei format-only!)
gh pr merge <PR_NUMBER> --admin --squash

# 4) Post-Merge Sanity
git pull --ff-only
ruff check . && black --check .
```

**⚠️ WICHTIG:** Kein Bypass bei Execution/Risk/Config/Deps/Governance Changes!

---

### Format-Only Guardrail (CI Implementation)

**Status:** ✅ Active (ab PR #XXX)

Die im Runbook dokumentierte "Safety Fix" Mechanik ist jetzt als **CI-Guardrail** implementiert.

**Komponenten:**

1. **Verifier Script:** `scripts/ops/verify_format_only_pr.sh`
   - Deterministischer Format-Only Check via git worktree + tree hash comparison
   - Exit 0 = Format-only confirmed, Exit 1 = Not format-only

2. **GitHub Actions Job:** `format-only-verifier` (required check)
   - Läuft auf allen PRs
   - Prüft Label `ops/format-only`
   - Führt Verifier Script aus (wenn Label gesetzt)
   - **FAIL** wenn Label gesetzt aber Verifier FAIL → verhindert Merge

3. **Policy Critic No-Op:** Conditional skip
   - Policy Critic läuft als no-op **nur wenn:**
     - Label `ops/format-only` gesetzt **UND**
     - `format-only-verifier` PASS ✅
   - Sonst: Policy Critic läuft normal (blockierend)

**Operator How-To:**

```bash
# 1) Label setzen (nur nach manual preflight!)
gh pr edit <PR> --add-label "ops/format-only"

# 2) CI prüfen: format-only-verifier muss grün sein
gh pr checks <PR>

# 3) Falls Verifier FAIL:
#    - Label entfernen
#    - PR fixen (non-format changes entfernen)
#    - Oder: regulärer Review-Prozess
gh pr edit <PR> --remove-label "ops/format-only"
```

**Warum das funktioniert:**

- ✅ Kein "Bypass" – Skip nur mit blockierendem Verifier
- ✅ Reduziert False-Positive Friction (Format-PRs laufen durch)
- ✅ Verhindert Bypass-Kultur (kein `--admin` mehr nötig)
- ✅ Erhält Safety Layer (echte PRs triggern weiterhin Policy Critic)
- ✅ Saubere Evidence Chain (Label + Verifier Logs + Audit Trail)

**Workflow:**

```
PR mit Label "ops/format-only"
  │
  ▼
format-only-verifier (required check)
  │
  ├─ Label nicht gesetzt? → SUCCESS (no-op), Policy Critic läuft normal
  │
  ├─ Label gesetzt + Verifier PASS? → SUCCESS, Policy Critic no-op ✅
  │
  └─ Label gesetzt + Verifier FAIL? → FAIL ❌ (PR blockiert, Label entfernen)
```

**Siehe auch:** [Policy Critic Triage Runbook](POLICY_CRITIC_TRIAGE_RUNBOOK.md) (Safety Fix Sektion)

---

## 🧯 Known CI Issues

- [CI Audit Known Issues](CI_AUDIT_KNOWN_ISSUES.md) — Pre-existing Black formatting issue (non-blocking)

## 🗂️ Stash Hygiene & Triage

### Stash Hygiene Policy

Best Practices für sicheres Stash-Management:

- **Policy & Ablauf:** [STASH_HYGIENE_POLICY.md](STASH_HYGIENE_POLICY.md)
  - Keyword-based drop (keine index-basierten Drops)
  - Export-before-delete Workflow
  - Recovery-Branch-Strategie

### Stash Triage Tool

Automatisiertes Stash-Management mit Safe-by-Default-Design:

- **Tool:** [`scripts/ops/stash_triage.sh`](../../scripts/ops/stash_triage.sh)
- **Tests:** [`tests/ops/test_stash_triage_script.py`](../../tests/ops/test_stash_triage_script.py)

**Quick Start:**

```bash
# List all stashes
scripts/ops/stash_triage.sh --list

# Export all stashes (safe, no deletion)
scripts/ops/stash_triage.sh --export-all

# Export + drop (requires explicit confirmation)
scripts/ops/stash_triage.sh --export-all --drop-after-export --confirm-drop
```

**Features:**

- ✅ Safe-by-Default (no deletion without explicit flags)
- ✅ Keyword-Filter für selektiven Export
- ✅ Strukturierter Export (Patch + Metadata)
- ✅ Session Report mit Triage-Übersicht
- ✅ Exit 2 bei unsicherer Nutzung (Drop ohne Confirm)

**Export-Ablage:** `docs/ops/stash_refs/`

Siehe [STASH_HYGIENE_POLICY.md](STASH_HYGIENE_POLICY.md) für Details zur Automation-Sektion.

## 📋 Merge Logs → Workflow
- PR #262 — Merge Log (meta: merge-log workflow standard): `PR_262_MERGE_LOG.md`

---

<!-- OPS_MERGE_BOTH_PRS_FAIL_FAST -->
## 🔀 Merge Both PRs (DOCS → FEATURE) — Fail-Fast Helper

**Script:** `scripts/ops/merge_both_prs.sh`

### What it does (safe-by-default)

✅ **Fail-Fast Checks:**
- `state == OPEN` (nicht CLOSED/MERGED)
- `isDraft == false` (blockiert Draft-PRs)
- `baseRefName == BASE_BRANCH` (z.B. main)
- `mergeable == MERGEABLE` (keine Konflikte)
- `reviewDecision == APPROVED` (optional, `REQUIRE_APPROVAL=true`)

✅ **Workflow:**
1. Watch CI für DOCS PR (`gh pr checks --watch`)
2. Merge DOCS PR (squash + delete-branch)
3. Update local main
4. Watch CI für FEATURE PR
5. Merge FEATURE PR (squash + delete-branch)
6. Update local main
7. Post-merge sanity: `python -m pytest -q`

✅ **Safety:**
- Working tree muss clean sein (keine uncommitted changes)
- Mergeable-Retry-Logic (GitHub API kann "UNKNOWN" zurückgeben)
- gh auth status check vor Start
- DRY_RUN mode für Testing

### Usage

```bash
# Standard (alle Defaults)
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# DRY_RUN (nur Checks, kein Merge)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Ohne Approval-Check (für persönliche Repos)
REQUIRE_APPROVAL=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

<!-- BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->

### Workflow: DRY_RUN → Real Merge

```bash
# Step 1: Test erst (DRY_RUN)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Falls Output: "✅ Done. Both PRs processed."
# → Alle Checks grün!

# Step 2: Echtes Merge
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

**Warum DRY_RUN?**
- ✅ Testet alle Fail-Fast-Checks (state, draft, base, mergeable, reviewDecision)
- ✅ Kein Merge, keine Git-State-Changes
- ✅ Safe-by-default Testing vor echtem Merge

<!-- END MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->

# Custom Base-Branch
BASE_BRANCH=feat/my-branch DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Ohne CI-Watch (wenn schon grün)
WATCH_CHECKS=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

### Configuration Knobs

| Env-Var | Default | Beschreibung |
|---------|---------|--------------|
| `REQUIRE_APPROVAL` | `true` | Erfordert `reviewDecision=APPROVED` |
| `FAIL_ON_DRAFT` | `true` | Aborted wenn PR ein Draft ist |
| `BASE_BRANCH` | `main` | Erwarteter Target-Branch |
| `MERGE_METHOD` | `squash` | `squash` / `merge` / `rebase` |
| `DELETE_BRANCH` | `true` | Löscht Branch nach Merge |
| `WATCH_CHECKS` | `true` | Watched CI vor Merge |
| `UPDATE_MAIN` | `true` | Updated local main nach Merge |
| `RUN_PYTEST` | `true` | Führt pytest nach Merges aus |
| `DRY_RUN` | `false` | Nur Checks, kein Merge |

### Error Scenarios

**PR not mergeable:**
```bash
ERROR: PR #123 is not mergeable (mergeable=CONFLICTING). Resolve conflicts / rebase.
```

**Fix:** Rebase auf main, Konflikte lösen, force-push

**PR not approved:**
```bash
ERROR: PR #123 not approved (reviewDecision=null). Get approval or set REQUIRE_APPROVAL=false.
```

**Fix:** `gh pr review 123 --approve` oder `REQUIRE_APPROVAL=false` Override

**Working tree dirty:**
```bash
ERROR: Working tree not clean. Commit/stash first.
```

**Fix:** `git stash push -u -m "temp"` oder commit changes

### Best Practices

1. **DRY_RUN erst:** Test Checks ohne Merge
   ```bash
   DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
   ```

2. **CI manuell prüfen:** Falls CI schon grün → `WATCH_CHECKS=false` (schneller)

3. **Approval-Workflow:** Self-approve als Maintainer
   ```bash
   gh pr review 123 --approve
   gh pr review 124 --approve
   DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
   ```

**Related:**
- Split Mixed PRs: `scripts/ops/split_mixed_pr.sh`
- Generate PR Bodies: `scripts/ops/generate_pr_bodies.sh`
- PR Management Toolkit: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)

<!-- MERGE_BOTH_PRS_QUICK_REFERENCE -->
### Quick Reference

**Cheat-Sheet:** [MERGE_BOTH_PRS_CHEATSHEET.md](pr_bodies/MERGE_BOTH_PRS_CHEATSHEET.md) ⭐

```bash
# Standard
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# DRY_RUN
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Personal Repo
REQUIRE_APPROVAL=false DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

<!-- BEGIN MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->

### Workflow: DRY_RUN → Real Merge

```bash
# Step 1: Test erst (DRY_RUN)
DRY_RUN=true DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh

# Falls Output: "✅ Done. Both PRs processed."
# → Alle Checks grün!

# Step 2: Echtes Merge
DOCS_PR=123 FEAT_PR=124 ./scripts/ops/merge_both_prs.sh
```

**Warum DRY_RUN?**
- ✅ Testet alle Fail-Fast-Checks (state, draft, base, mergeable, reviewDecision)
- ✅ Kein Merge, keine Git-State-Changes
- ✅ Safe-by-default Testing vor echtem Merge

<!-- END MERGE_BOTH_PRS_DRYRUN_WORKFLOW -->
```
