# Ops Runbook — Merge + Format Sweep Workflow

**Purpose:** Standardisierter Merge-Prozess + optionaler Format-Sweep, inkl. Large-PR Handling Simulation.

---

## What this uses

- Script: `scripts/workflows/merge_and_format_sweep.sh`
- Related: `docs/ops/CI_LARGE_PR_HANDLING.md`

---

## Preconditions

- `gh` CLI installiert & authentifiziert (`gh auth status`)
- Lokaler Working Tree sauber (`git status` → clean)
- `main` aktuell (`git pull --ff-only`)

---

## Quickstart

### Standard

```bash
PR_NUM=<nummer> ./scripts/workflows/merge_and_format_sweep.sh
```

**Was das tut:**
1. PR checks ansehen
2. PR mergen (squash + branch delete)
3. `main` aktualisieren
4. Format-Sweep Branch erstellen
5. `uv run pre-commit run --all-files` ausführen
6. Änderungen committen + pushen
7. Neuen Format-Sweep PR erstellen
8. Optional: `large-pr-approved` Label setzen (falls >1200 Files)

### Mit Large-PR Simulation

```bash
PR_NUM=<nummer> RUN_LARGE_SIM=1 LARGE_SIM_FILES=1250 \
  ./scripts/workflows/merge_and_format_sweep.sh
```

**Zusätzlich:**
- Erstellt Test-PR mit >1200 Dummy-Dateien
- Verzeichnis: `docs&#47;_ci_large_pr_test&#47;`
- **WICHTIG:** Test-PR NICHT mergen, nur zur CI-Verifikation

---

## Script Features

### Automatische Label-Verwaltung

- **>250 Files:** Policy Critic LITE Mode
- **>1200 Files:** Script setzt automatisch `large-pr-approved` Label
  - Aktiviert LITE_MINIMAL Mode (non-sensitive Files only)

### Error Handling

Das Skript bricht ab bei:
- ❌ Nicht-sauberem Working Tree (uncommitted changes)
- ❌ Fehlgeschlagenem PR Merge (required checks nicht grün)
- ❌ Fehlenden Commands (`git`, `gh`, `uv`)

---

## Step-by-Step Flow

### Phase 1: Vorbereitung

```bash
# 1) Repo-Status prüfen
cd ~/Peak_Trade
git status  # sollte clean sein

# 2) main aktualisieren
git checkout main
git pull --ff-only

# 3) PR-Nummer notieren
PR_NUM=<nummer>
```

### Phase 2: PR Checks & Merge

```bash
# 4) Quick Check
gh pr view $PR_NUM
gh pr checks $PR_NUM

# Optional: Live Watch (wartet bis alle Checks fertig sind)
gh pr checks $PR_NUM --watch

# 5) Merge durchführen
# Option A: Workflow-Script (empfohlen)
PR_NUM=$PR_NUM ./scripts/workflows/merge_and_format_sweep.sh

# Option B: Manuell
gh pr merge $PR_NUM --squash --delete-branch
git checkout main
git pull --ff-only
```

### Phase 3: Format-Sweep (falls Workflow-Script)

Das Workflow-Script führt automatisch aus:

```bash
# Erstellt Branch: chore/format-sweep-precommit-YYYY-MM-DD
# Führt aus: uv run pre-commit run --all-files
# Committet + pusht Änderungen
# Erstellt Format-Sweep PR
# Setzt Label (falls >1200 Files)
```

**Prüfung nach Workflow-Script:**

```bash
# Format-Sweep PR ansehen
gh pr list --state open --label large-pr-approved  # falls >1200 Files

# Oder: Letzten PR ansehen
gh pr list --state open --limit 1
```

### Phase 4: Verification

```bash
# main Status prüfen
git checkout main
git pull --ff-only
git status -sb

# Optional: Merge Log erstellen (siehe Abschnitt "Post-Merge Docs")
```

---

## Common Scenarios

### Scenario 1: Standard PR Merge (keine Format-Änderungen erwartet)

```bash
# Direkt mergen ohne Format-Sweep
PR_NUM=123 gh pr merge $PR_NUM --squash --delete-branch
git checkout main && git pull --ff-only
```

**Wann nutzen:**
- Reine Doku-PRs
- Kleine Bug-Fixes
- Keine Code-Änderungen

### Scenario 2: PR Merge + Format-Sweep

```bash
# Standard Workflow
PR_NUM=123 ./scripts/workflows/merge_and_format_sweep.sh
```

**Wann nutzen:**
- Nach größeren Feature-PRs
- Regelmäßige Format-Checks
- Vor Releases

### Scenario 3: Large-PR CI Test

```bash
# Mit Simulation
PR_NUM=123 RUN_LARGE_SIM=1 LARGE_SIM_FILES=1250 \
  ./scripts/workflows/merge_and_format_sweep.sh

# Nach CI-Verifikation: Simulation-PR schließen
gh pr close <SIM_PR_URL> --comment "CI large-PR handling verified. Closing test PR."
gh pr delete <SIM_PR_URL> --yes
```

**Wann nutzen:**
- Test des Large-PR Handling Systems
- Vor großen Refactorings
- CI-Pipeline-Verifikation

---

## Post-Merge Documentation

### Optional: Merge Log erstellen

```bash
# Branch erstellen
BR="docs/ops-pr<nummer>-merge-log"
git checkout -b "$BR"

# Merge Log Datei anlegen
cat > docs/ops/PR_<nummer>_MERGE_LOG.md <<'EOFLOG'
# PR #<nummer> — MERGE LOG

**PR:** #<nummer>
**Status:** ✅ MERGED
**Datum:** $(date +%Y-%m-%d)
**Branch:** `<branch-name>` (deleted)

## Summary
[Beschreibung der Änderungen]

## CI / Verification
[Check-Ergebnisse]

## What changed
[Dateien / Komponenten]
EOFLOG

# Indizes aktualisieren (siehe docs/ops/README.md und PEAK_TRADE_STATUS_OVERVIEW.md)
# Commiten, pushen, PR erstellen
git add docs/ops/PR_<nummer>_MERGE_LOG.md
git commit -m "docs(ops): add PR #<nummer> merge log"
git push -u origin "$BR"
gh pr create --title "docs(ops): add PR #<nummer> merge log" \
  --body "Post-merge documentation for PR #<nummer>." --base main

# Auto-Merge aktivieren
gh pr merge <PR_URL> --auto --squash --delete-branch
```

---

## Troubleshooting

### Problem: Working Tree nicht sauber

```bash
# Symptom
Working tree is not clean. Please commit/stash first.

# Lösung
git status
git stash  # oder: git add -A && git commit -m "..."
```

### Problem: PR Merge fehlgeschlagen

```bash
# Symptom
❌ Merge fehlgeschlagen (vermutlich required checks/rote Checks)

# Lösung
gh pr checks <PR_NUM>  # Checks prüfen
# Im Browser: GitHub Settings → Branch protection → Required checks
# Falls Quarto Smoke als required konfiguriert: entfernen oder Workflow fixen
```

### Problem: Pre-commit Hook Failed

```bash
# Symptom
pre-commit run --all-files failed (Exit Code 1)

# Häufig: end-of-file-fixer hat Dateien modifiziert
# Lösung: Erneut stagen + committen
git add -A
git commit -m "chore(format): pre-commit format sweep"
git push
```

### Problem: Label `large-pr-approved` fehlt

```bash
# Symptom
>1200 Files, aber Label wurde nicht gesetzt

# Lösung (manuell)
gh pr edit <PR_URL> --add-label "large-pr-approved"
```

---

## Environment Variables

Das Script unterstützt folgende ENV-Variablen:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `REPO_DIR` | `$HOME&#47;Peak_Trade` | Repo-Verzeichnis |
| `PR_NUM` | `216` | PR-Nummer zum Mergen |
| `RUN_LARGE_SIM` | `0` | Large-PR Simulation (0/1) |
| `LARGE_SIM_FILES` | `1250` | Anzahl Dummy-Dateien |

**Beispiel:**

```bash
REPO_DIR=/custom/path PR_NUM=200 ./scripts/workflows/merge_and_format_sweep.sh
```

---

## Safety Notes

### Was das Script NICHT tut

- ❌ Ändert KEINE Config-Dateien
- ❌ Ändert KEINE Core-Logik
- ❌ Führt KEINE Live-Orders aus
- ❌ Löscht KEINE Branches ohne Confirmation

### Was das Script MACHT

- ✅ Führt `pre-commit` über alle Dateien aus
- ✅ Committet Format-Änderungen (nur Whitespace/Linting)
- ✅ Erstellt PRs (keine direkten Commits zu `main`)
- ✅ Merged PRs nur wenn Checks grün sind

---

## Integration mit CI

Das Workflow-Script interagiert mit folgenden CI-Features:

### Policy Critic

- **<250 Files:** FULL Mode (alle Dateien analysiert)
- **250-1200 Files:** LITE Mode (reduzierte Analyse)
- **>1200 Files (mit Label):** LITE_MINIMAL Mode (nur non-sensitive)

### Quarto Smoke

- **Path Filter:** Triggert nur bei Änderungen in:
  - `docs&#47;**&#47;*.md`
  - `docs&#47;**&#47;*.qmd`
  - `reports&#47;quarto&#47;**`
- **Non-blocking:** Fail blockiert Merge nicht

### Expected Behavior

**Format-Sweep PR (typisch 1-50 Files):**
- ✅ Policy Critic: FULL Mode
- ✅ Quarto Smoke: Nicht getriggert (nur Code-Dateien)
- ✅ Required Checks: tests, audit, health gate

**Large-PR Simulation (>1200 Files):**
- ✅ Policy Critic: LITE_MINIMAL Mode (mit Label)
- ✅ Quarto Smoke: Getriggert (Dummy-Docs), aber non-blocking
- ✅ Required Checks: tests, audit, health gate

---

## Quick Reference

### Commands

```bash
# PR ansehen
gh pr view <PR_NUM>

# Checks ansehen
gh pr checks <PR_NUM>

# Checks live watchen
gh pr checks <PR_NUM> --watch

# PR mergen
gh pr merge <PR_NUM> --squash --delete-branch

# Auto-Merge aktivieren
gh pr merge <PR_NUM> --auto --squash --delete-branch

# PRs auflisten
gh pr list --state open
gh pr list --state open --label large-pr-approved

# Branch Status
git status -sb
git log --oneline -5
```

### Workflow-Script

```bash
# Standard
PR_NUM=<nummer> ./scripts/workflows/merge_and_format_sweep.sh

# Mit Large-PR Sim
PR_NUM=<nummer> RUN_LARGE_SIM=1 ./scripts/workflows/merge_and_format_sweep.sh

# Custom Repo
REPO_DIR=/path PR_NUM=<nummer> ./scripts/workflows/merge_and_format_sweep.sh
```

---

## History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2025-12-21 | Initial Runbook (basierend auf PR #216-#219 Erfahrung) |

---

## Related Documentation

- `docs/ops/CI_LARGE_PR_HANDLING.md` — CI Large-PR Handling System
- `docs/ops/PR_217_MERGE_LOG.md` — Workflow Script Merge Log
- `docs/ops/PR_218_MERGE_LOG.md` — Verifikation der CI-Features
- `scripts/workflows/merge_and_format_sweep.sh` — Das eigentliche Script
- `.github/workflows/policy_critic.yml` — Policy Critic Workflow
- `.github/workflows/quarto_smoke.yml` — Quarto Smoke Workflow

---

**Operator Note:** Dieses Runbook dokumentiert den etablierten Workflow basierend auf den PRs #216-#219 (Dezember 2025). Bei Änderungen am CI-System oder Workflow-Script entsprechend anpassen.
