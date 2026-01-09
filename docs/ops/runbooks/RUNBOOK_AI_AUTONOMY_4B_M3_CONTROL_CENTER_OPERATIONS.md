# RUNBOOK — AI Autonomy 4B M3 — Control Center Operations (v0.1)

Stand: 2026-01-09  
Scope: Docs-only / Operator Workflow  
Owner: Ops / AI Autonomy

---

## 0) Zweck & Guardrails

Dieses Runbook standardisiert die operative Nutzung des **AI Autonomy Control Center v0.1** als zentrale Steuer- und Sichtfläche.

### Guardrails (nicht verhandelbar)
- **No-Live / Governance-Locked:** Keine Ausführung von Live-Trading oder produktiven Exec-Pfaden.
- **Evidence-first:** Jede relevante Aussage wird auf ein konkretes Artefakt / Log / Doc referenziert.
- **Determinismus:** Änderungen an Artefakten erfolgen reproduzierbar; keine "manual-only" Zustände ohne Notiz.
- **SoD / Separation of Duties:** Operator dokumentiert, Reviewer bestätigt (bei PRs / Governance-Änderungen).

---

## 1) Entry Points (Single Source of Truth)

### Primary
- `docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md`

### Navigation
- `docs/ops/control_center/CONTROL_CENTER_NAV.md`

### Ops README Index
- `docs/ops/README.md` → Abschnitt „AI Autonomy Control Center"

---

## 2) Operator Rollenmodell (Minimal)

- **SHIFT OPERATOR:** Führt Daily Routine + Triage aus, erstellt Operator Output.
- **CI GUARDIAN (kann identisch sein, aber getrennte "Hats"):** Prüft CI Gates, dokumentiert Status.
- **REVIEWER (separat):** Prüft PRs / Änderungen an Governance/Docs, bestätigt "Go/No-Go" falls erforderlich.

---

## 3) Daily / Shift Routine (10–15 Minuten)

### 3.1 Pre-Check: Control Center öffnen
1) Öffne `AI_AUTONOMY_CONTROL_CENTER.md`  
2) Scanne **At-a-glance KPIs** (Tendenzen / "red flags")
3) Scanne **Layer Status Matrix (L0–L6)**

### 3.2 Minimaler Daily-Status (Pflicht)
Dokumentiere für die Schicht:
- Datum / Zeitfenster
- Layer-Status (L0–L6): OK / WARN / FAIL
- CI Gate Snapshot: PASS / FAIL / UNKNOWN (mit Quelle)
- Neue Evidence-Artefakte vorhanden? (ja/nein; welche)

> Output-Format: siehe Abschnitt 9 (Operator Output Template)

---

## 4) Layer-Triage Playbook (L0–L6)

### 4.1 Ziel: Einheitliche Interpretation
Die Layer-Matrix ist der Einstieg. Jede Abweichung wird als:
- **OK:** Keine offenen Findings, Artefakte vollständig, CI Gates grün
- **WARN:** Non-blocking Findings / Degradations / offene "Follow-ups"
- **FAIL:** Blocking Gate / fehlende Artefakte / Konsistenzbruch / Policy-Verstoß

### 4.2 Triage-Checkliste (für jeden Layer identisch)
Für Layer Lx:
1) **Status in Matrix** prüfen (OK/WARN/FAIL)
2) **Evidence** prüfen (Run Manifest / Operator Output / Links)
3) **CI Gates** prüfen (7 required checks; siehe Abschnitt 7)
4) **Troubleshooting** anwenden (Abschnitt 8)
5) **Entscheidung** dokumentieren:
   - "Monitor" (weiter beobachten)
   - "Fix Required" (Issue/PR erstellen)
   - "Escalate" (Reviewer/Owner)

### 4.3 Standard-Trigger für WARN/FAIL
- Fehlende oder nicht auflösbare Doc-Links (Reference Targets Gate)
- Evidence Pack unvollständig (Manifest/Output fehlt)
- CI Gate Failure in required checks
- Policy/Guardrail Konflikt (z.B. Live/Exec Pfade ohne Governance)

---

## 5) Evidence Artefacts (4B M3)

### 5.1 Erwartete Artefakte
- **Run Manifest**: Vollständige Dokumentation des Runs (Claims, Inputs, Outputs, Links)
- **Operator Output**: Deutscher Kurzbericht (Schicht-/Operator-Sicht)

### 5.2 Evidence Handling Regeln
- Artefakte müssen **pfad-stabil** sein (keine temporären lokalen Pfade).
- Jede Abweichung (fehlender Link, fehlendes Artefakt) muss im Operator Output stehen.
- Bei Änderungen an Evidence-Artefakten gilt: **Docs-only** und **Review erforderlich**.

---

## 6) Quick Actions (Operator-Kommandos & Links)

> Quelle: Control Center "Operator Quick Actions" Sektion (Single Source of Truth).

Operator nutzt ausschließlich:
- Dokumentierte Scripts/Commands
- Offizielle Runbook-Schritte
- Keine ad-hoc Live-Ausführung

Wenn ein Command "watch" oder "follow" timeouts verursacht:
- Nutze stattdessen "polling" (kurze Einzelabfragen) oder "view latest run" im CI/PR Kontext.
- Dokumentiere im Operator Output, welche Alternative genutzt wurde.

---

## 7) CI Gates Verifikation (Required Checks)

### 7.1 Ziel
Einheitliche Aussage "CI health" basiert auf den im Control Center referenzierten **7 required checks**.

### 7.2 Vorgehen
1) Prüfe den aktuellen Status im PR/Commit Kontext
2) Dokumentiere:
   - PASS/FAIL pro Gate
   - Run-ID / Commit SHA / PR #
   - Timestamp

> Wenn CI unbekannt ist (z.B. kein aktueller Run): als **UNKNOWN** markieren, nicht als PASS.

---

## 8) Troubleshooting (Standardfälle)

### 8.1 Docs Reference Targets Gate fail
Symptome:
- Gate meldet "missing reference targets" oder interpretiert Text als Pfad

Vorgehen:
1) Identifiziere die gemeldeten Zeilen
2) Prüfe, ob es echte Links sein sollen oder nur Text
3) Fix:
   - Branch/Code-Pfade in Inline-Code setzen oder neutralisieren
   - Echte Links auf existierende Dateien/Anchors korrigieren
4) Re-run CI / PR Update

### 8.2 "CI Watch" timeouts / hängt
Symptome:
- Watch-Kommandos laufen in Timeout / "stuck"

Vorgehen (polling statt watch):
- Prüfe zuletzt abgeschlossene Runs (Status + Logs)
- Prüfe spezifische Checks statt "global watch"
- Dokumentiere Alternative + Zeitpunkt

### 8.3 Layer Matrix zeigt WARN/FAIL ohne Artefakte
Vorgehen:
1) Control Center Navigation nutzen → Evidence / Runbooks Sektion
2) Fehlende Artefakte explizit notieren
3) Issue/PR für Artefakt-Nachlieferung erstellen

---

## 9) Operator Output Template (DE)

> Copy/Paste Vorlage. Immer Evidence-first schreiben.

### AI Autonomy — Operator Output (Kurzbericht)

Datum: YYYY-MM-DD  
Schicht: HH:MM–HH:MM (TZ)  
Context: PR/Commit/Run-ID (falls vorhanden)

#### Layer Status (L0–L6)
- L0: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L1: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L2: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L3: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L4: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L5: OK/WARN/FAIL — Evidenz: <Link/Pfad>
- L6: OK/WARN/FAIL — Evidenz: <Link/Pfad>

#### CI Gates (7 required)
- Gate 1: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 2: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 3: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 4: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 5: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 6: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>
- Gate 7: PASS/FAIL/UNKNOWN — Evidenz: <PR/Run>

#### Findings / Actions
- Finding 1 (severity: low/med/high): <Beschreibung> — Evidenz: <Link>
- Action: Monitor / Fix Required / Escalate — Owner: <Name/Role>

#### Notes
- Watch/Timeout Workaround genutzt? ja/nein (Details)

---

## 10) Change Log
- v0.1 (2026-01-09): Initial Runbook für Control Center Operations (4B M3)
