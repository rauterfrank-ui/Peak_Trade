# Peak_Trade – Ops Script Template Guide

## 📋 Übersicht

Für **neue** Ops-Skripte steht ein standardisiertes Template mit wiederverwendbaren Bash-Helpers zur Verfügung.

**Wichtig:** Bestehende Skripte (z.B. `pr_inventory_full.sh`, `label_merge_log_prs.sh`) bleiben unverändert. Das Template ist nur für neue Skripte gedacht.

---

## 🗂️ Dateien

| Datei | Zweck |
|-------|-------|
| `scripts/ops/run_helpers.sh` | Shared bash helper functions (source-only) |
| `scripts/ops/ops_script_template.sh` | Template für neue Ops-Skripte |

> **Path note**
>
> The operator-facing template path is `scripts&#47;ops&#47;ops_script_template.sh`.
> A historical copy also exists at `templates&#47;bash&#47;ops_script_template.sh`.
> For current operator workflows, prefer the `scripts&#47;ops&#47;` path used in this guide.
>

---

## 🚀 Quick Start

### 1. Neues Skript erstellen

```bash
# Template kopieren
cp scripts/ops/ops_script_template.sh scripts/ops/mein_neues_script.sh

# Anpassen
# - <SCRIPT NAME> → Dein Skript-Name
# - <1-liner> → Kurze Beschreibung
# - Implementiere deine Logik in den markierten Sektionen
```

### 2. Ausführen

```bash
# Default (strict mode): Fehler → Abort
bash scripts/ops/mein_neues_script.sh

# Robust mode: Fehler → Warn + Continue
PT_MODE=robust bash scripts/ops/mein_neues_script.sh
```

---

## 📦 Helper-Funktionen

### `pt_mode()`
Gibt aktuellen Mode zurück (`strict` oder `robust`).

### `pt_log(msg)`
Timestamped logging auf stdout.

### `pt_warn(msg)`
Warning auf stderr (mit ⚠️).

### `pt_die(msg)`
Fehler auf stderr (mit ❌) + exit (außer in interaktiver Shell).

### `pt_section(msg)`
Formatierte Section-Header mit Unicode-Box.

### `pt_require_cmd(cmd)`
Prüft, ob Command verfügbar ist.
- **Strict mode:** Exit bei fehlendem Command
- **Robust mode:** Warn + Continue

### `pt_run(label, cmd...)`
Führt Command aus, Verhalten abhängig von `PT_MODE`:
- **Strict mode:** Fehler → `pt_die()`
- **Robust mode:** Fehler → `pt_warn()` + Continue

### `pt_run_required(label, cmd...)`
Immer abort bei Fehler (auch in robust mode).

### `pt_run_optional(label, cmd...)`
Nie abort bei Fehler (auch in strict mode).

---

## 🎯 Template-Struktur

```bash
#!/usr/bin/env bash
set -euo pipefail

# 0) Source helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/run_helpers.sh"

# 1) Repo root detection (git-safe)

# 2) Required commands (pt_require_cmd)

# 3) Preflight checks

# ─── STRICT CORE (gating) ───
# pt_run_required() für kritische Steps

# ─── MAIN WORK (mode-controlled) ───
# pt_run() für Hauptlogik

# ─── OPTIONAL EXTRAS (non-gating) ───
# pt_run_optional() für Nice-to-Have
```

---

## 📝 Beispiel-Nutzung

### Gating Step (immer erforderlich)

```bash
pt_run_required "Update main" bash -c 'git checkout main && git pull --ff-only'
```

Verhält sich so:
- **Strict:** Fehler → Exit
- **Robust:** Fehler → Exit (gating!)

### Main Work (mode-abhängig)

```bash
pt_run "Generate inventory" bash scripts/ops/pr_inventory_full.sh
```

Verhält sich so:
- **Strict:** Fehler → Exit
- **Robust:** Fehler → Warn + Continue

### Optional Extra (nie gating)

```bash
pt_run_optional "Dry-run labels" bash scripts/ops/label_merge_log_prs.sh
```

Verhält sich so:
- **Strict:** Fehler → Warn + Continue
- **Robust:** Fehler → Warn + Continue

---

## 🛡️ Best Practices

### 1. Gating vs. Non-Gating klar trennen

```bash
# ✅ Good: Klar getrennte Sections
pt_section "Strict core (gating)"
pt_run_required "Update main" git pull --ff-only

pt_section "Optional extras (non-gating)"
pt_run_optional "Cleanup" rm -rf /tmp/temp_files
```

### 2. Repo Root Detection nutzen

```bash
# ✅ Good: Template-Pattern (git-safe)
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
  cd "${REPO_ROOT}"
else
  cd "${SCRIPT_DIR}/../.."
fi
```

### 3. Command-Checks am Anfang

```bash
# ✅ Good: Früh prüfen
pt_require_cmd git
pt_require_cmd gh
pt_require_cmd jq
```

### 4. Logging konsequent nutzen

```bash
# ✅ Good: Strukturiertes Logging
pt_log "Starting main work..."
pt_run "Build report" python3 scripts/generate_live_status_report.py --help
pt_log "Main work completed"
```

---

## ⚙️ Modes im Detail

### Strict Mode (default)

```bash
# Kein ENV → strict
bash scripts/ops/mein_script.sh

# Explizit
PT_MODE=strict bash scripts/ops/mein_script.sh
```

**Verhalten:**
- `pt_require_cmd` → Exit bei fehlendem Command
- `pt_run` → Exit bei Fehler
- `pt_run_required` → Exit bei Fehler
- `pt_run_optional` → Warn + Continue

### Robust Mode

```bash
PT_MODE=robust bash scripts/ops/mein_script.sh
```

**Verhalten:**
- `pt_require_cmd` → Warn + Continue
- `pt_run` → Warn + Continue
- `pt_run_required` → Exit bei Fehler (!)
- `pt_run_optional` → Warn + Continue

---

## 🧪 Testing

```bash
# Syntax check
bash -n scripts/ops/mein_script.sh

# Dry-run (falls implementiert)
DRY_RUN=1 bash scripts/ops/mein_script.sh

# Robust mode test
PT_MODE=robust bash scripts/ops/mein_script.sh
```

---

## 🔗 Verwandte Dokumentation

- Bestehende Skripte: `docs/ops/README.md`
- Workflow-Doku: `docs/ops/WORKFLOW_SCRIPTS.md`

---

**Version:** 1.0  
**Erstellt:** 2025-12-21  
**Status:** Ready for use (neue Skripte only)
