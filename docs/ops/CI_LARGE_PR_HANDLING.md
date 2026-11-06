# CI: Large PR Handling & Governance Automation

**Erstellt:** 2025-12-21  
**Status:** Aktiv  
**Zweck:** Dokumentation der CI-Anpassungen für mechanische Groß-PRs ohne Governance-Schwächung

---

## Übersicht

Dieses Dokument beschreibt, wie die CI-Pipeline angepasst wurde, um mechanische Groß-PRs (z.B. Format-Sweeps, automatische Refactorings) zu unterstützen, ohne die Governance-Standards zu schwächen.

### Problem
- Mechanische PRs mit vielen Dateien (>250) blockierten durch Policy Critic und Quarto Smoke
- Policy Critic analysierte alle Dateien → Timeout oder sehr lange Laufzeiten
- Quarto Smoke lief bei jedem PR, auch wenn keine Dokumentation geändert wurde
- Blockierte legitime PRs trotz pre-commit Hooks

### Lösung
1. **Policy Critic: Large-PR Guard mit LITE Mode**
   - Automatische Erkennung der PR-Größe
   - Abgestufte Analyse (FULL → LITE → LITE_MINIMAL)
   - Label-basierte Bypass-Option mit Safety Guards

2. **Quarto Smoke: Path-Filtering + Non-Blocking**
   - Läuft nur bei Dokumentations-Änderungen
   - Temporär non-blocking während Baseline-Stabilisierung

---

## Policy Critic: Large-PR Modes

### Schwellwerte

| PR-Größe | Mode | Verhalten |
|----------|------|-----------|
| ≤250 Dateien | **FULL** | Vollständige Analyse aller Dateien |
| 251-1200 Dateien | **LITE** | Priorisierte Teilmenge (max 80 Dateien) |
| >1200 Dateien ohne Label | **FAIL** | Blockiert, fordert PR-Split oder Label |
| >1200 Dateien mit Label | **LITE_MINIMAL** / **LITE_SENSITIVE** | Minimale Analyse (20-50 Dateien) |

### FULL Mode (≤250 Dateien)
- **Verhalten:** Analysiert alle geänderten Dateien
- **Zweck:** Standard-Governance für normale PRs
- **Keine Einschränkungen**

### LITE Mode (251-1200 Dateien)
- **Verhalten:** Analysiert priorisierte Teilmenge (max 80 Dateien)
- **Priorität:**
  1. Sensible Pfade: `src/governance/`, `src/execution/`, `src/risk/`, `src/live/`, `scripts/live/`
  2. Source Code: `src&#47;**&#47;*.py`
  3. Scripts: `scripts&#47;**&#47;*.py`
  4. Tests: `tests&#47;**&#47;*.py`
  5. Config: `config&#47;**&#47;*.toml`
- **Überspringt:** `docs/`, `templates/`, `**&#47;*.md` (außer sensible Pfade)
- **Message:** Warnung mit Empfehlung, PR zu splitten

### LITE_MINIMAL Mode (>1200 Dateien + Label)
- **Verhalten:** Analysiert nur Top 20 wichtige Dateien
- **Trigger:** PR hat Label `large-pr-approved`
- **Zweck:** Bypass für bewusst genehmigte Groß-PRs (z.B. automatische Refactorings)
- **Safety:** Nur wenn KEINE sensiblen Pfade geändert wurden
- **Warning:** Prominent in Job Summary, dass dies ein bewusster Bypass ist

### LITE_SENSITIVE Mode (>1200 Dateien + Label + Sensitive)
- **Verhalten:** Analysiert nur sensible Dateien (max 50)
- **Trigger:** PR hat Label `large-pr-approved` UND ändert sensible Pfade
- **Zweck:** Minimum-Governance für sehr große PRs mit kritischen Änderungen
- **Cannot Skip:** Sensible Pfade werden IMMER analysiert

### FAIL Modes

#### FAIL_TOO_LARGE
- **Trigger:** >1200 Dateien ohne `large-pr-approved` Label
- **Message:** "PR too large. Split PR or add label 'large-pr-approved'."
- **Action:** Job fails, blockiert Merge

#### FAIL_SENSITIVE
- **Trigger:** >1200 Dateien + sensible Pfade, AUCH MIT Label
- **Message:** "PR too large with sensitive path changes. Must be split."
- **Action:** Job fails, blockiert Merge
- **Grund:** Sensible Pfade dürfen nicht in sehr großen PRs ohne vollständige Review sein

---

## Sensible Pfade (Safety Guard)

Folgende Pfade werden als **sensitiv** eingestuft und erhalten besondere Behandlung:

```
src/governance/
src/execution/
src/risk/
src/live/
scripts/live/
```

**Regel:** Wenn ein PR >1200 Dateien hat UND sensible Pfade ändert:
- Label `large-pr-approved` reicht NICHT aus
- PR MUSS gesplittet werden
- **Grund:** Kritische Pfade erfordern vollständige Governance-Review

---

## Quarto Smoke Test

### Path-Filtering

Der Quarto Smoke Test läuft nur noch, wenn folgende Dateien geändert wurden:

```yaml
- 'docs/**'
- '**/*.md'
- '**/*.qmd'
- 'templates/quarto/**'
- 'scripts/dev/report_smoke.sh'
- '.github/workflows/quarto_smoke.yml'
```

**Vorteil:** Spart CI-Zeit bei Code-Only PRs

### Non-Blocking Status (Temporär)

- **Status:** `continue-on-error: true`
- **Grund:** Quarto Smoke Baseline noch nicht stabil (fehlende Dependencies, etc.)
- **TODO:** Entfernen sobald Baseline stabil ist
- **Tracking:** Job Summary zeigt prominente Warnung

---

## Verwendung

### Für Entwickler

#### Normaler PR (≤250 Dateien)
- Keine Änderungen
- Policy Critic läuft vollständig
- Quarto Smoke läuft nur bei Doku-Änderungen

#### Großer PR (251-1200 Dateien)
- Policy Critic läuft in LITE Mode
- Empfehlung: PR splitten für vollständige Review
- Merge ist möglich, wenn keine BLOCK-Violations

#### Sehr großer PR (>1200 Dateien)
**Option 1: PR Splitten (empfohlen)**
```bash
# Split in kleinere PRs
git checkout -b refactor-part1
# Cherry-pick relevante Commits
git cherry-pick <commit1> <commit2>
```

**Option 2: Label verwenden (Ausnahme)**
```bash
# Füge Label über GitHub UI hinzu
Label: large-pr-approved
```

⚠️ **WICHTIG:** Label funktioniert NICHT, wenn sensible Pfade geändert wurden!

#### Format-Sweep PR
Typischer Workflow für `ruff format` oder ähnliche mechanische Änderungen:

1. **Pre-Commit ausführen:**
   ```bash
   pre-commit run --all-files
   ```

2. **Lokale Checks:**
   ```bash
   # Stelle sicher, dass keine echten Code-Änderungen dabei sind
   git diff --stat

   # Verifiziere, dass Tests laufen
   python3 -m pytest tests/
   ```

3. **PR erstellen:**
   ```bash
   git checkout -b chore/format-sweep-2025-12-21
   git add -A
   git commit -m "chore: apply ruff format to entire codebase"
   git push origin chore/format-sweep-2025-12-21
   ```

4. **Label hinzufügen (falls >1200 Dateien):**
   - Gehe zu GitHub PR
   - Füge Label `large-pr-approved` hinzu
   - Policy Critic läuft in LITE_MINIMAL Mode

5. **Merge:**
   - Policy Critic zeigt LITE_MINIMAL Status
   - Job Summary warnt, dass dies ein bewusster Bypass ist
   - Merge ist erlaubt (wenn keine BLOCK-Violations)

### Für Reviewer

#### FULL Mode PR
- Standard-Review
- Alle Dateien wurden analysiert
- Verlasse dich auf Policy Critic Ergebnis

#### LITE Mode PR
- **Beachte:** Nur Teilmenge analysiert
- Job Summary zeigt, welche Dateien analysiert wurden
- **Empfehlung:**
  - Prüfe Job Summary auf LITE Mode Warnung
  - Überprüfe, ob PR gesplittet werden sollte
  - Manueller Spot-Check der nicht-analysierten Dateien

#### LITE_MINIMAL / LITE_SENSITIVE PR
- **WARNUNG:** Sehr großer PR mit Bypass
- Job Summary zeigt prominente Warnung
- **Action Required:**
  - Verstehe, warum dieser PR so groß ist
  - Prüfe, ob Split möglich/sinnvoll war
  - Manueller Review der sensiblen Pfade (bei LITE_SENSITIVE)
  - Dokumentiere Genehmigungsgrund im PR-Kommentar

---

## CI Job Summary

Jeder Policy Critic Run zeigt folgende Informationen:

### PR Size Analysis
- Total Changed Files
- Analysis Mode (FULL / LITE / LITE_MINIMAL / LITE_SENSITIVE)
- Files Analyzed (bei LITE)
- Sensitive Paths Count

### Policy Critic Results
- Exit Code
- Max Severity
- Recommended Action
- Violations
- Test Plan
- Operator Questions

### Analyzed Files (bei LITE)
- Top 20 analysierte Dateien
- Zeigt Priorisierung

### How to Control
- Schwellwerte
- Label-Usage
- Split-Empfehlung

---

## Lokale Verifikation

### Pre-Commit Hooks
```bash
# Installiere Hooks
pre-commit install

# Teste alle Dateien
pre-commit run --all-files

# Teste spezifische Hooks
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

### Policy Critic lokal
```bash
# Erzeuge Diff
git diff origin/main...HEAD > pr.diff

# Liste geänderte Dateien
CHANGED_FILES=$(git diff --name-only origin/main...HEAD | tr '\n' ',' | sed 's/,$//')

# Führe Policy Critic aus
python3 scripts/run_policy_critic.py \
  --diff-file pr.diff \
  --changed-files "$CHANGED_FILES"
```

### Quarto Smoke lokal
```bash
# Rendere Smoke Report
make report-smoke

# Öffne in Browser (macOS)
make report-smoke-open
```

---

## CI Jobs Matrix

| Job | Trigger | Blocking | Zweck |
|-----|---------|----------|-------|
| **Policy Critic** | PR mit kritischen Pfaden | Ja (bei BLOCK) | Governance Gate |
| **Quarto Smoke** | PR mit Doku-Änderungen | Nein (temp) | Doku-Validierung |
| **Lint** | Alle PRs | Ja | Code-Quality |
| **Tests** | Alle PRs | Ja | Functional Correctness |

### Policy Critic Trigger Paths
```yaml
- 'src/live/**'
- 'src/execution/**'
- 'src/exchange/**'
- 'src/risk/**'
- 'config/**'
- 'docs/governance/**'
- '.github/workflows/policy_critic.yml'
```

### Quarto Smoke Trigger Paths
```yaml
- 'docs/**'
- '**/*.md'
- '**/*.qmd'
- 'templates/quarto/**'
- 'scripts/dev/report_smoke.sh'
- '.github/workflows/quarto_smoke.yml'
```

---

## Wartung & Evolution

### Schwellwerte anpassen

Schwellwerte sind in `.github/workflows/policy_critic.yml` definiert:

```yaml
# Determine PR Size Mode Step
FULL_MODE_MAX_FILES=250
LITE_MODE_MAX_FILES=1200
```

**Anpassung:**
1. Edit Workflow-Datei
2. Ändere Konstanten
3. Teste mit verschiedenen PR-Größen
4. Dokumentiere Änderung hier

### Quarto Smoke Blocking aktivieren

Wenn Quarto Baseline stabil ist:

1. **Entferne `continue-on-error: true`:**
   ```yaml
   jobs:
     quarto-smoke:
       name: Render Quarto Smoke Report
       runs-on: ubuntu-latest
       # continue-on-error: true  <-- REMOVE THIS LINE
   ```

2. **Teste:**
   ```bash
   # Trigger Workflow manuell
   gh workflow run quarto_smoke.yml
   ```

3. **Verifiziere:** Mehrere PRs sollten ohne Fehler durchlaufen

4. **Dokumentiere:** Update dieses Dokument

### Sensible Pfade erweitern

Wenn neue kritische Module hinzukommen:

1. **Edit `.github/workflows/policy_critic.yml`:**
   ```yaml
   # Determine PR Size Mode Step
   SENSITIVE_PATTERNS="^(src/governance/|src/execution/|src/risk/|src/live/|scripts/live/|NEW_PATH/)"
   ```

2. **Update Policy Pack:**
   - `policy_packs/ci.yml`: critical_paths

3. **Dokumentiere:** Update dieses Dokument

---

## Häufige Szenarien

### Szenario 1: Format-Sweep über gesamte Codebase
- **Dateien:** 500+ Files
- **Mode:** LITE oder LITE_MINIMAL (mit Label)
- **Action:**
  1. Führe `pre-commit run --all-files` aus
  2. Commit
  3. Füge Label `large-pr-approved` hinzu (falls >1200)
  4. Merge nach LITE Review

### Szenario 2: Import-Refactoring mit kritischen Pfaden
- **Dateien:** 800 Files, inkl. `src/execution/`
- **Mode:** LITE (251-1200), analysiert execution/ Files
- **Action:**
  1. Policy Critic analysiert execution/ mit Priorität
  2. Prüfe Job Summary für violations
  3. Falls BLOCK: Fix und re-push
  4. Falls WARN: Reviewer entscheidet

### Szenario 3: Docs-only PR
- **Dateien:** 50 Markdown Files
- **Mode:** FULL (Policy Critic läuft nicht wegen path filter)
- **Quarto Smoke:** Läuft
- **Action:** Standard Merge

### Szenario 4: Risky Large PR mit sensitive paths
- **Dateien:** 1500 Files, inkl. `src/risk/`
- **Mode:** FAIL_SENSITIVE
- **Action:** PR MUSS gesplittet werden
- **Grund:** Keine Ausnahme für sehr große PRs mit kritischen Änderungen

---

## Metriken & Monitoring

### Zu beobachten
- Policy Critic LITE Mode Nutzung (Häufigkeit)
- `large-pr-approved` Label Usage
- FAIL_SENSITIVE Rate (sollte selten sein)
- Quarto Smoke Fehlerrate

### Alarme
- LITE_MINIMAL > 10% aller PRs → Review Prozess
- FAIL_SENSITIVE > 5 pro Monat → Entwickler-Kommunikation
- Quarto Smoke Fehlerrate > 20% → Baseline fixen

---

## Verwandte Dokumente

- [Policy Critic Charter](../governance/LLM_POLICY_CRITIC_CHARTER.md)
- [Policy Critic Status](../governance/POLICY_CRITIC_STATUS.md)
- [ADR: Tool Stack](../adr/ADR_0001_Peak_Tool_Stack.md)
- [PR 208 Merge Log](PR_208_MERGE_LOG.md)

---

## Changelog

| Datum | Änderung | Autor |
|-------|----------|-------|
| 2025-12-21 | Initial: Large-PR Handling implementiert | System |
| 2025-12-21 | Quarto Smoke Path-Filter + Non-Blocking | System |
