# Peak_Trade – Ops Tools

Bash-Skripte und Tools für Repository-Verwaltung, Health-Checks und PR-Analyse im Peak_Trade Repository.

---

## Closeouts & Playbooks
- `docs/ops/merge_logs/2025-12-27_mass_docs_pr_closeout.md` — Mass PR Wave Closeout (2025-12-27)
- `docs/ops/CASCADING_MERGES_AND_RERERE_PLAYBOOK.md` — Cascading merges & git rerere Operator Playbook

## Closeout Automation
- `scripts/ops/run_closeout_2025_12_27.sh` — Runner (Safety Gates + Auto-Merge Workflow)
- `scripts/ops/create_closeout_2025_12_27.sh` — Generator (Docs + PR scaffold)

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

Für einen vollständigen Ablauf von PR-Erstellung bis Merge und Verifikation steht jetzt ein detailliertes Runbook zur Verfügung. Siehe [OPS_OPERATOR_CENTER.md](OPS_OPERATOR_CENTER.md) ⭐

**Commands:**
- `status` — Repository-Status (git + gh)
- `pr <NUM>` — PR reviewen (safe, kein Merge)
- `doctor` — Health-Checks
- `audit` — Full Security & Quality Audit
- `merge-log` — Merge-Log Quick Reference
- `help` — Hilfe

**Design:** Safe-by-default, robust, konsistent.

---

## 🔒 Full Security & Quality Audit

**Umfassendes Audit-System für Security-Scanning, Dependency-Checks und Code-Qualität.**

### Quick Start

```bash
# Manuelles Audit ausführen
scripts/ops/ops_center.sh audit

# Oder direkt
./scripts/ops/run_full_audit.sh
```

### Was wird geprüft?

1. **Security Scanning** (`pip-audit`)
   - Scannt alle installierten Packages auf bekannte Vulnerabilities (CVEs)
   - Nutzt PyPI Advisory Database
   - Blockiert bei Findings (Exit != 0)

2. **SBOM Export** (Software Bill of Materials)
   - CycloneDX 1.5 Format
   - Vollständige Dependency-Liste mit Versionen und Hashes
   - Für Supply Chain Security & Compliance-Audits

3. **Repo Health** (`ops_center.sh doctor`)
   - Git-Status, Config-Validierung
   - Docs-Integrität, CI-Setup

4. **Code Quality**
   - `ruff format --check` (Format-Compliance)
   - `ruff check` (Linting)

5. **Test Suite**
   - `pytest -q` (Quick-Run aller Tests)

### Output & Artefakte

Alle Audit-Runs erzeugen versionierte Artefakte:

```
reports/audit/YYYYMMDD_HHMMSS/
├── full_audit.log    # Vollständiges Audit-Log
└── sbom.json         # Software Bill of Materials (CycloneDX 1.5)
```

**SBOM Use Cases:**
- Supply Chain Security: Identifikation aller Dependencies
- Compliance: SBOM-Anforderungen (z.B. Executive Order 14028)
- Vulnerability Tracking: Schnelle Prüfung ob betroffene Packages im Einsatz sind

### Knowledge DB In-Memory Fallback (Dev/Prod Hardening)

**Config Flag:** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK`

Die Knowledge Service API kann mit oder ohne ChromaDB (Vector DB) laufen:

- **Dev/Test (Default):** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK=true`
  - In-Memory Fallback aktiv wenn chromadb fehlt
  - API liefert 200/201 mit einfachem Keyword-Matching
  - **Use Case:** CI/lokale Dev ohne chromadb-Installation

- **Prod (Hardening):** `WEBUI_KNOWLEDGE_ALLOW_FALLBACK=false`
  - Kein Fallback erlaubt
  - API liefert **503 Service Unavailable** wenn chromadb fehlt
  - **Use Case:** Prod-Env wo Vector Search explizit required ist

**Empfehlung:**
- Dev/CI: Fallback enabled (Convenience)
- Prod: Fallback disabled + chromadb explizit installiert (Qualität)

### CI Integration

**Automatisches Weekly Audit:**
- Workflow: `.github/workflows/full_audit_weekly.yml`
- Schedule: Montags 06:00 UTC
- Manueller Trigger: `workflow_dispatch`
- Artifacts: 90 Tage (SBOM: 365 Tage)

**Failure-Verhalten:**
- Hard Fail bei pip-audit findings
- Hard Fail bei Lint-Errors
- Hard Fail bei Test-Failures

**Optional: ChromaDB Extras Workflow:**
- Workflow: `.github/workflows/knowledge_extras_chromadb.yml`
- Trigger: Jeden Montag 06:30 UTC + manuell via `workflow_dispatch`
- **Zweck:** Zusätzliches Signal für chromadb-backed Knowledge DB Tests
- **Status:** NICHT required für Merge (optional extra validation)
- Installiert chromadb und führt `tests/test_knowledge_readonly_gating.py` aus

### Troubleshooting

**Q: Audit failed - wo finde ich Details?**
```bash
# Letztes Audit-Log finden
ls -lt reports/audit/ | head -5

# Log lesen
tail -100 reports/audit/TIMESTAMP/full_audit.log
```

**Q: SBOM für Compliance-Check benötigt?**
```bash
# Letztes SBOM exportieren
ls -t reports/audit/**/sbom.json | head -1
```

**Q: Nur Security-Scan ohne Tests?**
```bash
# pip-audit direkt ausführen
uv run pip-audit --desc
```

---

## 📊 Risk Analytics – Component VaR Reporting

**Operator-Reports für Component VaR Analyse (Phase 2A)**

```bash
# Quick Start mit Fixtures
scripts/ops/ops_center.sh risk component-var --use-fixtures

# Mit eigenen Daten
scripts/ops/ops_center.sh risk component-var --returns data.csv --alpha 0.99
```

**Output:** HTML + JSON + CSV Reports in `results/risk/component_var/<run_id>/`

**Dokumentation:** [../risk/COMPONENT_VAR_PHASE2A_REPORTING.md](../risk/COMPONENT_VAR_PHASE2A_REPORTING.md) ⭐

**Features:**
- Multi-Format Output (HTML/JSON/CSV)
- Automatische Sanity Checks (Euler property, weights normalization)
- Top-Contributors-Analyse
- Deterministisch und reproduzierbar

---

## 🏥 Ops Doctor – Repository Health Check

Umfassendes Diagnose-Tool für Repository-Health-Checks mit strukturiertem JSON- und Human-Readable-Output.

### Quick Start

## Docs Diff Guard (auto beim Merge)

### Required Checks Drift Guard (v1)

- Operator Notes: `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`
- Quick Commands:
  - `scripts/ops/verify_required_checks_drift.sh` (offline)
  - `scripts/ops/ops_center.sh doctor` → zeigt Drift-Guard/Health-Status (falls eingebunden)

### Docs Navigation Health (Link Guard)

**Zweck:** Verhindert kaputte interne Links und Anchors in der Ops-Dokumentation, Root README und Status Overview.

**Quick Start:**
```bash
# Standalone Check
scripts/ops/check_ops_docs_navigation.sh

# Als Teil von ops doctor
scripts/ops/ops_center.sh doctor
```

**Features:**
- Prüft interne Markdown-Links (Format: `[text]\(path\)`) auf existierende Zieldateien
- Validiert Anchor-Links (Format: `[text]\(file.md#heading\)`) gegen tatsächliche Überschriften
- Ignoriert externe Links (http://, https://, mailto:)
- Schnell und offline (keine Netzwerk-Anfragen)

**Scope:** `README.md`, `docs/ops/*`, `docs/PEAK_TRADE_STATUS_OVERVIEW.md`

**Tip:** Vor großen Docs-Refactorings einmal laufen lassen, um kaputte Links zu vermeiden.

### Docs Reference Targets

**Zweck:** Validiert, dass alle referenzierten Repo-Pfade in Markdown-Docs (Config/Scripts/Docs) tatsächlich existieren.

**Quick Start:**
```bash
# Standalone Check (nur geänderte Markdown-Dateien)
scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Alle Docs scannen
scripts/ops/verify_docs_reference_targets.sh

# Als Teil von ops doctor (warn-only)
scripts/ops/ops_center.sh doctor
```

**Features:**
- Findet referenzierte Pfade in Markdown-Links (`[text]\(path\)`), Inline-Code (`` `path` ``), und Bare-Pfaden
- Validiert Existenz von: `config/*.toml`, `docs/*.md`, `scripts/*.sh`, `src/*.py`, `.github/*.yml`
- Ignoriert externe URLs (http/https) und Anchor-Only-Links
- Exit 0 = OK/nicht anwendbar, Exit 1 = FAIL (CI), Exit 2 = WARN (ops doctor)

**CI Integration:**
- Läuft automatisch bei PRs via `.github/workflows/docs_reference_targets_gate.yml`
- Exit 0 wenn keine Markdown-Dateien geändert wurden (not applicable)
- Exit 1 bei fehlenden Targets (blockiert Merge)

**Scope:** Alle `*.md` Dateien (im --changed Mode: nur geänderte Dateien)

**Use Case:** Verhindert kaputte Referenzen z.B. nach Datei-Umbenennungen oder -Verschiebungen.

## Docs Reference Targets Guardrail — Supported Formats

Der Check `docs-reference-targets-gate` stellt sicher, dass in Docs referenzierte **Repo-Targets** (Dateien) existieren, ohne typische Markdown-/Shell-False-Positives zu triggern.

### Unterstützte Referenzen (werden geprüft)
- **Plain paths** relativ zum Repo-Root, z.B. `docs/ops/README.md`, `scripts/ops/ops_center.sh`
- **Markdown-Links**: `[Text]\(docs/ops/README.md\)`
- **Anchors** werden ignoriert (nur Datei wird geprüft): `RISK_LAYER_ROADMAP.md#overview`
- **Query-Parameter** werden ignoriert: `docs/ops/README.md?plain=1`
- **Relative Pfade in Docs** werden korrekt resolved (relativ zur jeweiligen Markdown-Datei)

**Beispiele (konzeptionell):**
```
./README.md      # Same directory
../risk/README.md # Parent directory
```

### Ignorierte Muster (werden NICHT als Repo-Targets gezählt)
- **URLs**: `http://…`, `https://…`, z.B. `<https://example.com/docs/ops/README.md>`
- **Globs/Wildcards**: `*`, `?`, `[]`, `< >` (z.B. `docs/*.md`, `docs/**/README.md`)
- **Commands mit Spaces** (z.B. `./scripts/ops/ops_center.sh doctor`)
- **Directories mit trailing slash** (z.B. `docs/ops/`)
- **Referenzen innerhalb von Bash-Codeblöcken**:
  ```bash
  # Alles innerhalb dieses Blocks wird NICHT als Target gecheckt
  cat docs/ops/__fixture_missing_target__nope.md
  ```

### Golden Corpus Tests
Das Verhalten ist durch ein "Golden Corpus" an Fixtures abgedeckt (Regressionssicherheit):
- `tests/fixtures/docs_reference_targets/pass/` — Valide Referenzen + ignorierte Muster
- `tests/fixtures/docs_reference_targets/fail/` — Fehlende Targets (muss detected werden)
- `tests/fixtures/docs_reference_targets/relative_repo/` — Isolated Fixture-Repo für relative Pfade

**Pytest Tests:**
```bash
pytest -q tests/ops/test_verify_docs_reference_targets_script.py
```

---

Beim `--merge` läuft standardmäßig automatisch ein **Docs Diff Guard**, der große versehentliche Löschungen in `docs/*` erkennt und **den Merge blockiert**.

### Override-Optionen
```bash
# Custom Threshold (z.B. bei beabsichtigter Restrukturierung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Warn-only (kein Fail, nur Warnung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Guard komplett überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

**Siehe auch:**
- Vollständige Dokumentation: `docs/ops/README.md` (Abschnitt "Docs Diff Guard")
- PR Management Toolkit: `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- Standalone Script: `scripts/ops/docs_diff_guard.sh`
- Merge-Log: `docs/ops/PR_311_MERGE_LOG.md`

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
- **Implementation Summary**: [OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md](reports/OPS_DOCTOR_IMPLEMENTATION_SUMMARY.md)

### Merge-Log Health Integration

`ops doctor` prüft automatisch die Merge-Log-Infrastruktur:

```bash
# Volle Prüfung (Validator + Tests, ~10s)
ops doctor

# Schnellmodus (nur Validator, <1s)
ops doctor --quick
```

**Geprüft wird:**
- ✅ Merge-Log Generator (executable + markers)
- ✅ Dokumentation (marker format)
- 🧪 Offline Tests (falls `--quick` nicht gesetzt)

**Exit Codes:**
- `0` = Alle Checks bestanden
- `!= 0` = Mindestens ein Check fehlgeschlagen

### Formatter Policy Guardrail

- Zusätzlich verifiziert `ops doctor`, dass das CI-Enforcement aktiv ist (Lint Gate enthält den Drift-Guard-Step).
`ops doctor` prüft automatisch, dass keine `black --check` Enforcement in Workflows/Scripts existiert:

```bash
# Formatter Policy Check (immer aktiv, auch bei --quick)
ops doctor
ops doctor --quick
```

**Source of Truth:**
- ✅ `ruff format --check` (CI + Ops)
- ❌ `black --check` (nicht erlaubt)

**Geprüft wird:**
- ✅ .github/workflows (keine black enforcement)
- ✅ scripts (keine black enforcement)

**Enforcement:**
- 🏥 **ops doctor** (lokal, immer aktiv)
- 🛡️ **CI Lint Gate** (automatisch bei jedem PR, auch docs-only)

**Bei Verstößen:**
```bash
# Manueller Check
scripts/ops/check_no_black_enforcement.sh
```

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

## 🚨 Incidents & Post-Mortems

* **2025-12-26 — Formatter Drift (Audit) → Tool Alignment**

  * **Root Cause:** Repo nutzt `ruff format`, Legacy/Drift führte zu Audit-Failures (detected by `ruff format --check`).
  * **Fix:** **#354** merged → `black` entfernt, **Single Source of Truth = RUFF**; Guardrail `check_no_black_enforcement.sh` ✅
  * **Campaign:** #283/#303 auto-merge pending; #269 closed (superseded); #259 merge via Web-UI (fehlender OAuth `workflow` scope).
  * **RCA:** `incidents/2025-12-26_formatter_drift_audit_alignment.md`

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

- [Peak_Trade Tooling & Evidence Chain Runbook](Peak_Trade_TOOLING_AND_EVIDENCE_CHAIN_RUNBOOK.md)
- [CI Large PR Implementation Report](reports/CI_LARGE_PR_IMPLEMENTATION_REPORT.md)
- [Merge Log Workflow](PR_208_MERGE_LOG.md)

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

### Batch Generator (Automatisiert)

Für mehrere PRs gleichzeitig oder single-PR mit Auto-Update der docs.

**Tool:** `scripts/ops/generate_merge_logs_batch.sh`

**Verwendung:**

```bash
# Single PR
ops merge-log 281

# Mehrere PRs (batch)
ops merge-log 278 279 280

# Preview Mode (dry-run, keine Änderungen)
ops merge-log --dry-run 281

# Batch mit best-effort (sammelt Fehler, läuft weiter)
ops merge-log --keep-going 278 279 999
```

**Requirements:**
- `gh` CLI installiert + authentifiziert (`gh auth login`)
- PRs müssen bereits gemerged sein

**Output:**
- Erstellt `docs/ops/PR_<NUM>_MERGE_LOG.md` für jedes PR
- Updates automatisch `docs/ops/README.md` + `docs/ops/MERGE_LOG_WORKFLOW.md` (via Marker)

**Flags:**
- `--dry-run` — Preview Mode: zeigt Änderungen, schreibt nichts
- `--keep-going` — Best-Effort: läuft bei Fehlern weiter, Exit 1 am Ende falls welche
- `--help` — Zeigt Usage

**Validierung:**

```bash
# Setup validieren (offline, <1s)
scripts/ops/validate_merge_logs_setup.sh
```

#### Marker Format (MERGE_LOG_EXAMPLES)

Die folgenden Dateien **müssen** diese Marker enthalten für Auto-Updates:
- `docs/ops/README.md`
- `docs/ops/MERGE_LOG_WORKFLOW.md`

**Format:**
```html
<!-- MERGE_LOG_EXAMPLES:START -->
- PR #290 — chore(ops): guard against black enforcement drift: docs/ops/PR_290_MERGE_LOG.md
- PR #307 — docs(ops): document README_REGISTRY guardrail for ops doctor: docs/ops/PR_307_MERGE_LOG.md
- PR #309 — feat(ops): add branch hygiene script (origin/main enforcement): docs/ops/PR_309_MERGE_LOG.md
- PR #311 — feat(ops): add docs diff guard (mass-deletion protection): docs/ops/PR_311_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->




```

Das Batch-Tool ersetzt den Inhalt zwischen den Markern idempotent.

**Validator:** `scripts/ops/validate_merge_logs_setup.sh` prüft:
- Generator ist executable
- Marker sind vorhanden in beiden Dateien
- `ops_center.sh` hat die Integration

**Siehe auch:** [MERGE_LOG_WORKFLOW.md](MERGE_LOG_WORKFLOW.md)

### Liste

- [PR #322](PR_322_MERGE_LOG.md) — docs(risk): Component VaR MVP (Implementation + Tests + Docs) (merged 2025-12-25)
- [PR #323](PR_323_MERGE_LOG.md) — feat(ops): Required Checks Drift Guard v1 (merged 2025-12-25)
- [PR #261](PR_261_MERGE_LOG.md) — chore(ops): add stash triage helper (export-first, safe-by-default) (merged 2025-12-23)
- [PR #250](PR_250_MERGE_LOG.md) — feat(ops): add ops_doctor repo health check tool (merged 2025-12-23)
- [PR #243](PR_243_MERGE_LOG.md) — feat(webui): knowledge API endpoints + readonly/web-write gating + smoke runners (merged 2025-12-22)
- [PR #237](PR_237_MERGE_LOG.md) — chore(ops): add shared bash run helpers (strict/robust) (merged 2025-12-21)
- [PR #235](PR_235_MERGE_LOG.md) — fix(ops): improve label_merge_log_prs.sh to find open PRs (merged 2025-12-21)
- [PR #234](PR_234_MERGE_LOG.md) — chore(ops): PR inventory + merge-log labeling scripts (merged 2025-12-21)
- [PR #123](PR_123_MERGE_LOG.md) — docs: core architecture & workflow documentation (P0+P1) (merged 2025-12-23)

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

## Stability & Resilience

- **Stability & Resilience Plan v1**: [STABILITY_RESILIENCE_PLAN_V1.md](STABILITY_RESILIENCE_PLAN_V1.md)
  - Production-readiness initiative (data contracts, atomic cache, error taxonomy, reproducibility, config validation, observability, CI smoke gates)
  - Milestone: [Stability & Resilience v1](https://github.com/rauterfrank-ui/Peak_Trade/milestone/1)
  - Issues: [#124](https://github.com/rauterfrank-ui/Peak_Trade/issues/124) - [#134](https://github.com/rauterfrank-ui/Peak_Trade/issues/134)

---

## Related Documentation

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

<!-- MERGE_LOG_EXAMPLES:START -->
- PR #278 — merge log for PR #123 + ops references: docs/ops/PR_278_MERGE_LOG.md
- PR #279 — salvage untracked docs/ops assets: docs/ops/PR_279_MERGE_LOG.md
- PR #280 — archive session reports to worklogs: docs/ops/PR_280_MERGE_LOG.md
- PR #307 — docs(ops): document README_REGISTRY guardrail for ops doctor: docs/ops/PR_307_MERGE_LOG.md
- PR #309 — feat(ops): add branch hygiene script (origin/main enforcement): docs/ops/PR_309_MERGE_LOG.md
- PR #311 — feat(ops): add docs diff guard (mass-deletion protection): docs/ops/PR_311_MERGE_LOG.md
<!-- MERGE_LOG_EXAMPLES:END -->
- PR #292 — formatter policy drift guard enforced in CI (Merge-Log): docs/ops/PR_292_MERGE_LOG.md
- PR #295 — guard the guardrail (CI enforcement presence) (Merge-Log): docs/ops/PR_295_MERGE_LOG.md

### Policy Guard Pattern
- Template: docs/ops/POLICY_GUARD_PATTERN_TEMPLATE.md

### Ops Doctor Dashboard
- Generate: scripts/ops/generate_ops_doctor_dashboard.sh
- Output: reports/ops/ops_doctor_dashboard.html

### Ops Doctor Dashboard (CI)
- Workflow: `.github/workflows/ops_doctor_dashboard.yml` (manual + scheduled)
- Output artifacts: `ops-doctor-dashboard` (HTML + JSON)
- Local generation: `bash scripts/ops/generate_ops_doctor_dashboard.sh`

### Ops Doctor Dashboard (CI + Pages)
- Workflow: `.github/workflows/ops_doctor_pages.yml` (manual + scheduled)
- Run artifacts: `ops-doctor-dashboard` (index.html + index.json)
- Pages: Settings → Pages → Source = GitHub Actions (einmalig aktivieren)


### Ops Doctor Dashboard Badge

- Badge semantics: PASS (exit 0), WARN (exit 2), FAIL (any other non-zero)

## Branch Hygiene (origin/main)
Um zu verhindern, dass versehentlich lokale (unpushed) Commits in einen PR rutschen, erstelle neue Branches **immer von `origin/main`**:

```bash
git checkout main
scripts/ops/new_branch_from_origin_main.sh feat/my-change
```

Das Script prüft:
- ✅ Working tree ist clean
- ✅ Lokaler `main` ist NICHT ahead von `origin/main` (verhindert unpushed commits)
- ✅ Erstellt Branch explizit von `origin/main`

**Warum?** Siehe PR #305: Branch wurde vom lokalen `main` abgezweigt, der 2 unpushte Commits hatte → 4 Dateien statt 1 im PR.

## Docs Diff Guard (Mass-Deletion Schutz)

Wenn ein PR versehentlich massive Docs-Deletions enthält (z.B. README „-972"), ist das eine Red-Flag.

### Automatische Integration (seit PR #311)

Der Docs Diff Guard ist **automatisch in `review_and_merge_pr.sh` integriert** und läuft vor jedem `--merge`:

```bash
# Default: Guard läuft automatisch (Threshold: 200 Deletions/File unter docs/)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge

# Override: Custom Threshold
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Override: Warn-only (kein Fail)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Override: Guard überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

### Standalone (manuelle Pre-Merge Check)

Alternativ kann das Script auch manuell für lokale Checks genutzt werden:

```bash
# Standard: fail bei Violations
scripts/ops/docs_diff_guard.sh --base origin/main --threshold 200

# Warn-only (ohne Exit 1)
scripts/ops/docs_diff_guard.sh --warn-only

# Custom Threshold
scripts/ops/docs_diff_guard.sh --threshold 500
```

### Wie es funktioniert

- Zählt Deletions pro File unter `docs/` (via GitHub PR Files API oder `git diff --numstat`)
- Fails bei >= 200 Deletions per File (default)
- `--warn-only` zum Testen ohne Exit 1
- `--threshold <n>` zum Anpassen

**Use-Case:** PR #310 hatte ursprünglich `-972` in README.md → wäre erkannt worden.

## Risk & Safety Gates (Operator Hub)

Schnellzugriff auf die pre-trade Risk Gates & Operator-Runbooks:

- VaR Gate Runbook: `docs/risk/VAR_GATE_RUNBOOK.md`
- Stress Gate Runbook: `docs/risk/STRESS_GATE_RUNBOOK.md`
- Liquidity Gate Runbook: `docs/risk/LIQUIDITY_GATE_RUNBOOK.md`
- Risk Layer Roadmap: `docs/risk/RISK_LAYER_ROADMAP.md`

Hinweis: Gates sind standardmäßig konservativ/disabled-by-default ausrollbar; Aktivierung erfolgt über Config-Profile (Paper/Shadow → Monitoring → Live).

---

## Merge-Log Amendment Policy (Immutable History)

**Prinzip:** Merge-Logs sind **immutable**. Nachträgliche Änderungen an bereits gemergten Merge-Logs erfolgen **nicht** durch direktes Editieren in `main`, sondern **immer** über einen **separaten Docs-only PR**.

### Wann ist ein Amendment erlaubt?
- **Klarheit/Lesbarkeit:** bessere Summary/Why/Changes-Struktur, präzisere Operator-Schritte
- **Fehlende Referenzen:** Runbook-/PR-/Issue-Links nachtragen
- **Korrekturen ohne Semantik-Änderung:** Tippfehler, Formatierung, eindeutige Faktenkorrektur (z.B. PR-Nummer/Dateiname)

### Wie wird amended?
1. **Neuer Branch** von `main` (Docs-only)
2. Änderung am Merge-Log durchführen **oder** (empfohlen) einen kleinen „Amendment"-Zusatz/Follow-up Log hinzufügen
3. **Commit + PR** (Label: `documentation`)
4. Optional: **Auto-Merge** aktivieren, wenn alle Required Checks grün

### Was ist *nicht* erlaubt?
- Rewriting von technischen Entscheidungen oder Risiko-Semantik, wenn dadurch die ursprüngliche historische Darstellung „umgebogen" wird  
  → In dem Fall: **Follow-up PR + neues Merge-Log** oder „Incident/Correction Note" mit Verweis.

### Empfehlung (Ops-Workflow)
- Große Korrekturen: **neues** kurzes Dokument `docs/ops/merge_logs/<date>_amendment_<ref>.md` mit Verweis auf das Original
- Kleine Korrekturen: PR gegen das betroffene Merge-Log mit klarer PR-Body-Begründung (Docs-only)

---

## GitHub Auth & Token Helper

Peak_Trade bevorzugt GitHub CLI (`gh`). Wenn ein Script einen Token braucht, nutze den zentralen Helper:

- Safe Debug (zeigt nur Prefix + Länge, kein Leak):
  - `scripts/utils/get_github_token.sh --debug`
- Validierung (Exit != 0 wenn kein gültiger Token gefunden wird):
  - `scripts/utils/get_github_token.sh --check`
- Verwendung in Scripts:
  - `TOKEN="$(scripts/utils/get_github_token.sh)"`

Unterstützte Token-Formate:
- `gho_*`  (GitHub CLI OAuth Token)
- `ghp_*`  (Classic PAT)
- `github_pat_*` (Fine-grained PAT)

Token-Quellen (Priorität):
`GITHUB_TOKEN` → `GH_TOKEN` → macOS Clipboard (`pbpaste`) → `gh auth token`

Empfohlenes Setup:
- `gh auth login --web`
- Danach laufen Scripts ohne PAT-Erstellen/Löschen.

Security:
- Tokens niemals in Logs echo'en oder als "eigene Zeile" ins Terminal pasten.
