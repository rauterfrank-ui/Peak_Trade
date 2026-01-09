# Operator Drill Pack — AI Autonomy 4B Milestone 2 (Cursor Multi-Agent)

**Version:** 1.0  
**Status:** Active  
**Zielgruppe:** Ops-Operatoren  
**Kontext:** Phase 4B Milestone 2 — Evidence-First Operator Loop  
**Letzte Aktualisierung:** 2026-01-09

---

## A) Zweck & Leitplanken

### Zweck

Dieses Drill Pack dient der systematischen Operator-Kompetenzvalidierung für AI Autonomy Layer Runs mit Cursor Multi-Agent Orchestrierung. Jeder Drill ist ein eigenständiges, wiederholbares Szenario, das konkrete Fähigkeiten trainiert:

- Pre-Flight Disziplin (Repository Hygiene, Branch Hygiene, Dirty Tree Detection)
- Scope Lock Enforcement (Docs-only Contract Verification)
- Evidence Pack Completeness & Schema Validation
- CI Gate Triage & Evidence-Driven Remediation
- Docs Reference Targets Gate Handling
- Auto-Merge Safety & Readiness Verification
- Incident Micro-Drills (Timeout Handling, Flaky Checks)
- Closeout Procedures (Final Summary, Risk Assessment, Documentation Linking)

### Leitplanken (nicht verhandelbar)

**Evidence-First:**  
Alle Drill-Outputs müssen deterministisch dokumentiert sein. Keine spekulativen Claims, keine nicht-verifizierbaren Aussagen.

**No-Live / Drill-Only:**  
Kein Live Trading, keine Exchange Connectivity, keine realen Funds. Alle Drills laufen ausschließlich im Docs-/Governance-Bereich oder gegen Test-Fixtures.

**Separation of Duties (SoD):**  
Explizite Rollentrennung zwischen Operator (Ausführung) und Agent (Vorschlag). Operator hat finale Entscheidungsgewalt und Accountability.

**Determinismus:**  
Drill-Ergebnisse müssen reproduzierbar sein. Seeds, Versionen, Timestamps, Git-Refs werden dokumentiert.

---

## B) Nutzung dieses Packs (Operator-Anleitung)

### Empfohlene Kadenz

- **Wöchentlich:** 1-2 Drills pro Session (Rotation durch alle 8 Drills)
- **Vor Production-nahen Runs:** Vollständiger Durchlauf (alle 8 Drills)
- **Nach Incidents:** Gezielter Drill zu dem betroffenen Bereich

### Timeboxing

Jeder Drill hat eine empfohlene Timebox (10-25 Minuten). Bei Überschreitung:
- Drill abbrechen
- Status dokumentieren (Partial/Incomplete)
- Blocker identifizieren
- Später wiederholen

### Artefakt-Erfassung

Jeder Drill produziert strukturierte Artefakte:

**Operator Notes:**  
Kurzes Markdown-Dokument mit Drill-ID, Datum, Operator, Findings, Pass/Fail Status.

**Run Manifest:**  
Git-Ref, Tool-Versionen, Environment-Info (OS, Shell, Python Version).

**Validator Report:**  
Output von automatisierten Checks (Exit Codes, Logs, Screenshots wenn nötig).

**Evidence Pack Pointers:**  
Links zu erzeugten/validierten Evidence Packs (falls Drill einen erzeugt hat).

### Ablage-Struktur

```
docs/ops/drill_runs/
  YYYYMMDD_HHMMSS_<drill_id>_<operator>/
    operator_notes.md
    run_manifest.json
    validator_report.txt
    evidence_pack_pointers.txt (optional)
```

---

## C) Drill Format Template

Jeder Drill folgt dieser Struktur (Operatoren können dieses Template für eigene Drills wiederverwenden):

### Drill ID & Titel

Eindeutige Kennung (z.B. D01, D02) + beschreibender Titel.

### Objective

Ein Satz: Was wird trainiert/validiert?

### Preconditions / Inputs

Was muss vorher vorhanden/eingerichtet sein?

### Procedure (Step-by-Step)

Nummerierte, deterministische Schritte. Keine Ambiguität.

### Pass/Fail Criteria

Explizite, überprüfbare Bedingungen für Pass und Fail.

### Common Failure Modes & Fixes

Bekannte Stolpersteine + Operator Actions.

### Produced Artifacts

Liste der erzeugten Dateien/Artefakte + Ablageorte.

### Timebox

Empfohlene maximale Dauer.

---

## D) Drills (D01-D08)

---

## D01 — Pre-Flight Discipline

**Objective:**  
Repository-Hygiene, Branch-Hygiene und Dirty-Tree-Detection vor jedem Run verifizieren.

**Preconditions / Inputs:**
- Repository: `/Users/frnkhrz/Peak_Trade`
- Aktueller Branch: beliebig (wird dokumentiert)
- Kein laufender CI-Run erforderlich

**Procedure:**

1. **Repository Root bestätigen:**
   ```bash
   cd /Users/frnkhrz/Peak_Trade && pwd && git rev-parse --show-toplevel
   ```
   Erwartung: Beide Outputs zeigen `/Users/frnkhrz/Peak_Trade`.

2. **Git Status prüfen:**
   ```bash
   git status -sb
   ```
   Dokumentiere: Branch, Tracking-Status, Anzahl Uncommitted/Untracked Files.

3. **Dirty Tree Detection:**
   ```bash
   git diff --stat
   git diff --cached --stat
   ```
   Pass wenn beide leer sind (kein Output). Fail wenn Änderungen vorhanden.

4. **Branch Hygiene (origin/main Divergence):**
   ```bash
   git checkout main
   git fetch origin
   git log origin/main..main --oneline
   ```
   Pass wenn kein Output (main ist sync mit origin/main).  
   Fail wenn Commits vorhanden (unpushed local commits).

5. **Dokumentation erstellen:**
   Erstelle `docs/ops/drill_runs/YYYYMMDD_HHMMSS_D01_<operator>/operator_notes.md`:
   ```
   # Drill D01 — Pre-Flight Discipline
   - Datum: <ISO8601>
   - Operator: <Name>
   - Git Ref: <SHA>
   - Branch: <name>
   - Dirty Tree: YES/NO
   - Unpushed Commits: YES/NO
   - Status: PASS/FAIL
   - Findings: <kurz>
   ```

**Pass/Fail Criteria:**
- **PASS:** Dirty Tree = NO, Unpushed Commits = NO, alle Commands exit 0
- **FAIL:** Dirty Tree = YES OR Unpushed Commits = YES

**Common Failure Modes & Fixes:**
- **Dirty Tree durch IDE/Editor:** `.gitignore` prüfen, ungewollte Dateien stashen
- **Unpushed Commits:** `git push` oder Branch neu erstellen von `origin/main`
- **Detached HEAD:** `git checkout main`

**Produced Artifacts:**
- `operator_notes.md`
- `run_manifest.json` (optional: git ref, timestamp, operator)

**Timebox:** 10 Minuten

---

## D02 — Scope Lock Verification

**Objective:**  
Docs-only Contract Enforcement: Sicherstellen, dass nur Docs-Änderungen im Branch sind (keine Code-Änderungen).

**Preconditions / Inputs:**
- Branch mit Änderungen (kann auch mock/fixture sein)
- Base Branch: `origin/main`

**Procedure:**

1. **Scope-Änderungen identifizieren:**
   ```bash
   git diff --name-status origin/main...HEAD
   ```
   Dokumentiere alle geänderten Dateien.

2. **Docs-only Verification:**
   ```bash
   git diff --name-status origin/main...HEAD | grep -v '^[AMD][[:space:]]\+docs/'
   ```
   Pass wenn kein Output (nur docs/ Änderungen).  
   Fail wenn Files außerhalb `docs/` geändert wurden.

3. **Accidental Code Changes Detection:**
   Falls Fail in Schritt 2, liste explizit:
   ```bash
   git diff --name-status origin/main...HEAD | grep -v '^[AMD][[:space:]]\+docs/' > non_docs_changes.txt
   cat non_docs_changes.txt
   ```

4. **Evidence Capture:**
   Erstelle `operator_notes.md`:
   ```
   # Drill D02 — Scope Lock Verification
   - Datum: <ISO8601>
   - Branch: <name>
   - Base: origin/main
   - Docs-only: YES/NO
   - Non-Docs Changes: <count>
   - Status: PASS/FAIL
   - Files: <list if FAIL>
   ```

**Pass/Fail Criteria:**
- **PASS:** Alle Änderungen unter `docs/`, keine Files in `src/`, `tests/`, `config/`, `scripts/`, `.github/`
- **FAIL:** Mindestens ein File außerhalb `docs/` geändert

**Common Failure Modes & Fixes:**
- **Versehentliche Linter-Änderungen:** `git restore` + `git add -p` für selektives Staging
- **Auto-Formatter Runs:** `.git/info/exclude` für lokale IDE-Outputs
- **Config Bumps:** Separater Branch für Config, nicht in Docs-only Branch

**Produced Artifacts:**
- `operator_notes.md`
- `non_docs_changes.txt` (wenn FAIL)

**Timebox:** 10 Minuten

---

## D03 — Evidence Pack Completeness Drill

**Objective:**  
Evidence Pack gegen Schema validieren, Required Fields prüfen, deterministische Namensgebung verifizieren.

**Preconditions / Inputs:**
- Evidence Pack JSON (kann Fixture oder real sein)
- Schema Version bekannt (z.B. `2.0`)
- Validator Script: `scripts/validate_evidence_pack.py`

**Procedure:**

1. **Evidence Pack Fixture auswählen:**
   Falls kein reales Pack vorhanden:
   ```bash
   cp tests/fixtures/evidence_packs/valid_minimal.json /tmp/drill_d03_evidence_pack.json
   ```

2. **Schema Validation (strict):**
   ```bash
   python3 scripts/validate_evidence_pack.py /tmp/drill_d03_evidence_pack.json
   ```
   Exit 0 = PASS, Exit 1 = FAIL.

3. **Required Fields Check:**
   Prüfe manuell oder via `jq`:
   ```bash
   jq -r '.evidence_pack_id, .schema_version, .git_ref, .run_reason, .operator_id' /tmp/drill_d03_evidence_pack.json
   ```
   Pass wenn alle Felder non-null/non-empty.

4. **Deterministische Namensgebung:**
   Format: `EVP-<phase>-<layer>-<YYYYMMDD>-<seq>.json`  
   Prüfe via Pattern-Match:
   ```bash
   basename /tmp/drill_d03_evidence_pack.json | grep -E '^EVP-[A-Z0-9]+-[A-Z0-9]+-[0-9]{8}-[0-9]{3}\.json$'
   ```
   Exit 0 = PASS.

5. **Dokumentation:**
   ```
   # Drill D03 — Evidence Pack Completeness
   - Datum: <ISO8601>
   - Pack ID: <id>
   - Schema Version: <version>
   - Validation: PASS/FAIL
   - Required Fields: ALL PRESENT / MISSING <fields>
   - Naming: VALID / INVALID
   - Status: PASS/FAIL
   ```

**Pass/Fail Criteria:**
- **PASS:** Validation exit 0, alle Required Fields vorhanden, Naming-Pattern korrekt
- **FAIL:** Validation fail OR fehlende Fields OR falsches Naming

**Common Failure Modes & Fixes:**
- **Schema Version Mismatch:** Pack mit `"schema_version": "2.0"` updaten
- **Fehlende operator_id:** Manuell eintragen oder via Orchestrator regenerieren
- **Ungültiges Naming:** Rename via deterministische Konvention

**Produced Artifacts:**
- `operator_notes.md`
- `validator_report.txt` (stdout/stderr von Validator)
- Evidence Pack (falls neu erzeugt)

**Timebox:** 15 Minuten

---

## D04 — CI Gate Triage Drill

**Objective:**  
Failing CI Checks schnell identifizieren, Evidence-driven Remediation Plan erstellen.

**Preconditions / Inputs:**
- PR mit mindestens einem failing Check (kann Mock/Closed PR sein)
- `gh` CLI authentifiziert

**Procedure:**

1. **PR Checks Status abrufen:**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
   Dokumentiere: Anzahl failing, skipped, pending, successful.

2. **Failing Checks identifizieren:**
   ```bash
   gh pr checks <PR_NUMBER> --json name,conclusion --jq '.[] | select(.conclusion == "FAILURE") | .name'
   ```
   Liste alle Failing Checks.

3. **Root Cause Triage (pro Failing Check):**
   Für jeden Check:
   - Logs abrufen (via GitHub Web UI oder `gh run view`)
   - Failure Mode klassifizieren:
     - Lint Error
     - Test Failure
     - Schema Validation Error
     - Docs Reference Target Missing
     - Audit / Security Finding
     - Policy Violation
   - Remediation Action bestimmen

4. **Remediation Plan erstellen:**
   ```
   # CI Gate Triage — PR <NUM>
   - Failing Checks: <count>
   - Checks:
     - <Check Name>: <Failure Mode> → <Action>
     - <Check Name>: <Failure Mode> → <Action>
   - Priority: HIGH/MEDIUM/LOW
   - ETA: <time estimate>
   ```

5. **Dokumentation:**
   ```
   # Drill D04 — CI Gate Triage
   - Datum: <ISO8601>
   - PR: <NUM>
   - Failing Checks: <count>
   - Triage Time: <minutes>
   - Remediation Plan: <link to plan>
   - Status: PASS (plan created)
   ```

**Pass/Fail Criteria:**
- **PASS:** Alle Failing Checks identifiziert, Failure Mode klassifiziert, Remediation Action dokumentiert
- **FAIL:** Incomplete Triage OR keine Remediation Actions

**Common Failure Modes & Fixes:**
- **Flaky Tests:** Retry via GitHub UI, dokumentiere Flakiness
- **Timeout:** Identifiziere long-running Tests, optimiere oder erhöhe Timeout
- **External Dependency Failure:** Skip Check (mit Begründung) oder Fallback

**Produced Artifacts:**
- `operator_notes.md`
- `remediation_plan.md`

**Timebox:** 15 Minuten

---

## D05 — Docs Reference Targets Gate Drill

**Objective:**  
Fehlende Docs Reference Targets finden, reparieren, False Positives vermeiden.

**Preconditions / Inputs:**
- Branch mit Docs-Änderungen
- Script: `scripts/ops/verify_docs_reference_targets.sh`

**Procedure:**

1. **Gate lokal ausführen (Changed Files Only):**
   ```bash
   scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
   ```
   Exit 0 = PASS, Exit 1 = FAIL.

2. **Fehlende Targets identifizieren:**
   Falls Exit 1, lese Output:
   ```
   Missing target: docs/ops/FOO_BAR.md (referenced in docs/ops/README.md:42)
   Missing target: scripts/ops/baz.sh (referenced in docs/ops/RUNBOOK.md:123)
   ```
   Dokumentiere alle Missing Targets + Referencing Files.

3. **False Positive Check:**
   Für jeden Missing Target prüfe:
   - Ist das ein echter Pfad oder ein Command/Argument?
   - Ist das ein Glob-Pattern (sollte ignoriert werden)?
   - Ist das innerhalb eines Bash-Codeblocks (sollte ignoriert werden)?

4. **Remediation:**
   Für echte Missing Targets:
   - **Option A:** Datei erstellen (falls beabsichtigt aber vergessen)
   - **Option B:** Referenz korrigieren (Pfad/Filename fix)
   - **Option C:** Referenz entfernen (falls obsolet)

5. **Revalidierung:**
   ```bash
   scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
   ```
   Muss Exit 0 sein nach Remediation.

6. **Dokumentation:**
   ```
   # Drill D05 — Docs Reference Targets Gate
   - Datum: <ISO8601>
   - Missing Targets Initial: <count>
   - False Positives: <count>
   - Remediation Actions: <list>
   - Final Status: PASS/FAIL
   ```

**Pass/Fail Criteria:**
- **PASS:** Gate exit 0 nach Remediation, keine False Positives
- **FAIL:** Gate exit 1 OR nicht alle Missing Targets adressiert

**Common Failure Modes & Fixes:**
- **Branch Names als Paths:** Escaping oder umformulieren
- **Glob Patterns:** Sollten automatisch ignoriert werden, prüfe Regex
- **Relative Paths:** Müssen vom Markdown-File-Kontext aufgelöst werden

**Produced Artifacts:**
- `operator_notes.md`
- `missing_targets.txt` (initial list)
- `remediation_log.txt` (actions taken)

**Timebox:** 20 Minuten

---

## D06 — Auto-Merge Safety Drill

**Objective:**  
Auto-Merge Readiness verifizieren: Required Checks, Path Filters, Merge-Bereitschaft.

**Preconditions / Inputs:**
- PR in mergeable state (oder Mock PR)
- `gh` CLI authentifiziert
- Branch Protection Ruleset aktiv

**Procedure:**

1. **PR Status abrufen:**
   ```bash
   gh pr view <PR_NUMBER> --json mergeable,mergeStateStatus
   ```
   Dokumentiere: `mergeable` (true/false), `mergeStateStatus` (CLEAN/BLOCKED/UNKNOWN).

2. **Required Checks Status:**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
   Prüfe: Alle Required Checks sind successful (kein pending, kein failing).

3. **Path Filter Verification (falls relevant):**
   Wenn PR docs-only ist, prüfe dass irrelevante Checks skipped sind (nicht pending):
   ```bash
   gh pr checks <PR_NUMBER> --json name,conclusion --jq '.[] | select(.name | contains("tests")) | .conclusion'
   ```
   Erwartung: "SKIPPED" oder "SUCCESS", nicht "PENDING".

4. **Auto-Merge Enable (Dry-Run Simulation):**
   ```bash
   # Zeige Command ohne Ausführung
   echo "gh pr merge <PR_NUMBER> --auto --squash"
   ```
   Dokumentiere: Würde Command ausgeführt werden? YES/NO (basierend auf Status).

5. **Safety Checklist:**
   - [ ] `mergeable: true`
   - [ ] Alle Required Checks successful
   - [ ] Keine pending Checks (die nicht skipped werden dürfen)
   - [ ] Branch ist up-to-date mit base
   - [ ] Kein Admin-Override nötig

6. **Dokumentation:**
   ```
   # Drill D06 — Auto-Merge Safety
   - Datum: <ISO8601>
   - PR: <NUM>
   - Mergeable: true/false
   - Required Checks: PASS/FAIL
   - Safety Checklist: ALL PASS / <missing items>
   - Auto-Merge Ready: YES/NO
   - Status: PASS/FAIL
   ```

**Pass/Fail Criteria:**
- **PASS:** Safety Checklist vollständig, Auto-Merge würde succeeden
- **FAIL:** Mindestens ein Checklist-Item fail

**Common Failure Modes & Fixes:**
- **mergeable: UNKNOWN:** Warte 30-60s, refresh via `gh pr view --json mergeable`
- **Pending Checks:** Warte oder trigger erneut (je nach Check-Typ)
- **Branch out-of-date:** `git pull origin main && git push`

**Produced Artifacts:**
- `operator_notes.md`
- `safety_checklist.txt`

**Timebox:** 15 Minuten

---

## D07 — Incident Micro-Drill

**Objective:**  
Timeout / Flaky Check Handling: Operator Actions + Logging bei "watch" Timeouts oder flaky Checks.

**Preconditions / Inputs:**
- Simuliertes oder reales Timeout/Flaky-Szenario
- Runbook: `docs/ops/CURSOR_TIMEOUT_TRIAGE.md`

**Procedure:**

1. **Symptom Detection:**
   Simuliere eines der folgenden:
   - `gh pr checks --watch` timeout (>5 min kein Output)
   - Check zeigt "PENDING" obwohl erwartungsgemäß längst fertig
   - Check failed mit "timeout" in Logs

2. **Immediate Operator Actions:**
   - **Ctrl-C** zum Abbrechen des watch
   - Status manuell abrufen:
     ```bash
     gh pr checks <PR_NUMBER>
     ```
   - Screenshot/Copy des Status speichern

3. **Triage:**
   Für jeden "stuck" Check:
   - **Logs prüfen:**
     ```bash
     gh run view <RUN_ID> --log
     ```
   - **Failure Mode klassifizieren:**
     - Hard Timeout (GitHub Actions Limit)
     - External API Timeout (z.B. pip-audit)
     - Flaky Test (random failure)
     - Resource Exhaustion (Memory/Disk)
   - **Operator Action bestimmen:**
     - Retry via GitHub UI
     - Skip Check (mit Begründung)
     - Manual Verification (außerhalb CI)
     - Escalate (Maintainer/Admin)

4. **Evidence Logging:**
   Erstelle `incident_log.md`:
   ```
   # Incident Micro-Drill — <Type>
   - Datum: <ISO8601>
   - PR/Run: <NUM>
   - Symptom: <kurz>
   - Stuck Checks: <list>
   - Triage Time: <minutes>
   - Actions Taken: <list>
   - Resolution: RETRY/SKIP/ESCALATE/MANUAL
   - Status: RESOLVED/PENDING
   ```

5. **Runbook Verification:**
   Prüfe: Ist das Szenario in `CURSOR_TIMEOUT_TRIAGE.md` dokumentiert?  
   Falls nein: Ergänzung vorschlagen.

6. **Dokumentation:**
   ```
   # Drill D07 — Incident Micro-Drill
   - Datum: <ISO8601>
   - Incident Type: <timeout/flaky/resource>
   - Triage Time: <minutes>
   - Resolution: <status>
   - Runbook Coverage: YES/NO (gap identified)
   - Status: PASS (incident logged + resolved)
   ```

**Pass/Fail Criteria:**
- **PASS:** Incident detected, triaged, action taken, evidence logged
- **FAIL:** Keine Triage OR keine Dokumentation

**Common Failure Modes & Fixes:**
- **watch hängt:** Ctrl-C + manuelle Checks (kein automatisches watch)
- **Logs zu groß:** GitHub UI + Filter oder `tail` auf relevante Teile
- **Flaky Test kein Pattern:** Multiple Runs vergleichen, Issue öffnen

**Produced Artifacts:**
- `operator_notes.md`
- `incident_log.md`
- Screenshots (optional)

**Timebox:** 20 Minuten

---

## D08 — Closeout Drill

**Objective:**  
Final Summary erstellen, Risk Call dokumentieren, Merge-Log + Evidence Index verlinken.

**Preconditions / Inputs:**
- Abgeschlossener Run (kann Drill oder real sein)
- Template: `docs/ops/templates/MERGE_LOG_TEMPLATE_COMPACT.md`

**Procedure:**

1. **Run Summary erstellen:**
   ```
   # Closeout Summary — <Run ID>
   - Run Type: <Layer Run / Drill / PR>
   - Datum: <ISO8601>
   - Git Ref: <SHA>
   - Operator: <Name>
   - Duration: <minutes>
   - Result: SUCCESS/FAIL/PARTIAL
   ```

2. **Risk Assessment:**
   Klassifiziere Risiko:
   - **LOW:** Docs-only, keine Code-Änderungen, alle Gates grün
   - **MEDIUM:** Minor Code-Änderungen, alle Tests grün, kein Policy-Impact
   - **HIGH:** Execution-relevante Änderungen, Policy-Impact, oder Test-Failures

   Dokumentiere Mitigations (falls MEDIUM/HIGH).

3. **Linking:**
   - **Evidence Index:** Füge Entry zu `docs/ops/EVIDENCE_INDEX.md` hinzu:
     ```
     | <YYYYMMDD> | <Run ID> | <Type> | <Risk> | <link to closeout> |
     ```
   - **README:** Falls PR, füge Link zu Merge-Log in `docs/ops/README.md` hinzu (via Marker oder manuell).

4. **Artefakte Inventory:**
   Liste alle produzierten Artefakte:
   - Evidence Pack (falls vorhanden)
   - Operator Notes
   - Validator Reports
   - Logs/Manifests
   - Screenshots (falls vorhanden)

5. **Final Checklist:**
   - [ ] Summary vollständig
   - [ ] Risk dokumentiert
   - [ ] Evidence Index updated
   - [ ] README/Runbook Links gesetzt
   - [ ] Artefakte abgelegt (docs/ops/drill_runs/ oder data/evidence_packs/)

6. **Dokumentation:**
   ```
   # Drill D08 — Closeout
   - Datum: <ISO8601>
   - Run ID: <id>
   - Risk: LOW/MEDIUM/HIGH
   - Artefakte: <count>
   - Links Set: YES/NO
   - Status: PASS (closeout complete)
   ```

**Pass/Fail Criteria:**
- **PASS:** Alle Checklist-Items erfüllt, Links gesetzt, Artefakte abgelegt
- **FAIL:** Incomplete Summary OR fehlende Links OR Artefakte nicht abgelegt

**Common Failure Modes & Fixes:**
- **Fehlende Evidence Index Entry:** Manuell nachtragen via PR
- **Vergessene Runbook-Links:** Docs-Amendment-PR erstellen
- **Artefakte verloren:** Aus Git History oder CI Artifacts wiederherstellen

**Produced Artifacts:**
- `operator_notes.md` (Closeout Summary)
- `risk_assessment.md`
- Updated `EVIDENCE_INDEX.md` + `README.md`

**Timebox:** 25 Minuten

---

## E) Operator Competency Tracker (optional)

Operatoren können optional einen Competency Tracker führen:

```
# Operator: <Name>
# Period: <YYYYMMDD> - <YYYYMMDD>

| Drill ID | Date | Status | Time | Notes |
|----------|------|--------|------|-------|
| D01 | 2026-01-10 | PASS | 8 min | Clean run |
| D02 | 2026-01-10 | PASS | 9 min | No scope violations |
| D03 | 2026-01-11 | FAIL | 20 min | Missing operator_id, fixed + retry → PASS |
| D04 | 2026-01-12 | PASS | 12 min | 2 failing checks triaged |
| D05 | 2026-01-13 | PASS | 18 min | 3 missing targets fixed |
| D06 | 2026-01-14 | PASS | 10 min | Auto-merge ready |
| D07 | 2026-01-15 | PASS | 15 min | Timeout handled, logged |
| D08 | 2026-01-16 | PASS | 22 min | Full closeout |
```

**Ablage:** `docs/ops/drill_runs/<operator>/competency_tracker.md` (lokal, nicht committed)

---

## F) Change Log

- **2026-01-09 (v1.0):** Initial Release — 8 Drills für AI Autonomy 4B M2 (Evidence-First Operator Loop)
