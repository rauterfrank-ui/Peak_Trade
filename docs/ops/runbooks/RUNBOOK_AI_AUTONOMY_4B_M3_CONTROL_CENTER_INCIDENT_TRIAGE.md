# RUNBOOK — AI Autonomy 4B M3 — Control Center Incident Triage
Stand: 2026-01-09  
Scope: Docs-only / View-only operations (no-live)

## 0. Zweck & Guardrails
Dieses Runbook standardisiert Incident-Erkennung, Triage, Evidenzsicherung und Eskalation rund um den AI Autonomy Control Center Betrieb.

**Guardrails:**
- Kein Live-Trading, keine Automationen mit Trading-Wirkung.
- View-only Monitoring: CI, Dashboard, Logs/Artefakte nur lesen.
- Evidence-first: Erst Evidenz sichern, dann Hypothesen ableiten.
- Separation of Duties (SoD): Änderungen nur via PR; keine "hot edits" in main.

## 1. Definition: "Incident" im Control Center Kontext
Ein Incident ist jede Situation, in der mindestens eine Bedingung zutrifft:
- CI Required Gates sind rot oder flappen (z. B. Lint Gate, audit, docs-reference-targets-gate, strategy-smoke).
- Control Center Dashboard ist nicht zuverlässig nutzbar (z. B. wiederholte Timeouts, unvollständige Statusanzeige).
- Evidence Capture ist unvollständig oder nicht audit-stabil (fehlende Artefakte, fehlende Operator-Notes).
- Guardrails scheinen verletzt (z. B. Verdacht auf non-docs Änderung).

## 2. Severity Levels (S0–S3)
| Level | Bezeichnung | Kriterium | Zielzeit |
|------:|-------------|-----------|---------|
| S0 | Info / Noise | Kein Gate betroffen, keine Auswirkung | best-effort |
| S1 | Degradation | Non-blocking Probleme (z. B. Bugbot neutral, UI Timeout sporadisch) | same day |
| S2 | Gate Failure | Required Gate rot oder deterministisch reproduzierbar | sofortige Triage |
| S3 | Governance Risk | Verdacht auf Guardrail-/Policy-Verstoß | sofort stoppen + eskalieren |

## 3. Standard-Triage Ablauf (A–F)
### A) Stabilisieren (Stop-the-bleed)
- Kein Aktionismus: keine "Fixes" ohne Evidenz.
- Wenn UI/Watch timeouts: auf timeout-sichere Methoden wechseln (siehe Abschnitt 4).

### B) Evidenz sichern (Minimum Evidence Pack)
Erzeuge/aktualisiere folgende Artefakte (als Operator Notes oder Ticket-Anhang):
- **Timestamp (Europe/Berlin):** `YYYY-MM-DDTHH:MM+01:00`
- **Kontext:** "Was sollte passieren?" vs "Was ist passiert?"
- **Gate/Signal:** exakter Check-Name (wie in GitHub Checks angezeigt)
- **Reproduzierbarkeit:**
  - 1/3/5 Versuche? Flapping?
  - Immer gleich oder abhängig von Zeit/Load?
- **Sichtbare Symptome** (kurz, präzise)
- **Screenshots** (wenn UI) oder Copy-Paste Snippets (wenn CLI)

### C) Klassifizieren (Welche Kategorie?)
Kategorien:
1) CI Gate Failure (required)
2) Docs Integrity / Reference Targets
3) Dashboard Availability / Timeout
4) Policy / Guardrail Concern
5) Unknown / Needs deeper triage

### D) Root Cause Hypothesen (max. 3)
- Formuliere maximal 3 Hypothesen.
- Jede Hypothese braucht: "Welche Evidenz stützt das?" und "Welche Evidenz würde es falsifizieren?"

### E) Nächster sicherer Schritt
- Für docs-only Incidents: Fokus auf Links, Targets, Formatierung, deterministische Artefakte.
- Für CI-Gates: zuerst lokal reproduzieren (wenn möglich), sonst GitHub-Run Details auswerten.

### F) Abschluss: Outcome dokumentieren
- **Status:** resolved / mitigated / open
- **Fix-Pfad:** PR-Referenz (falls erstellt)
- **Lessons Learned:** 3 bullets, keine Roman-Länge

## 4. Timeout-sichere Monitoring Methoden (UI/Watch Workarounds)
Wenn "watch" oder Live-Updates timeouts verursachen:

**GitHub UI:**
- Auf den spezifischen Check klicken und Details laden lassen (statt Live-Stream).
- Re-Load im Intervall (manuell) statt Dauer-Streaming.

**Minimal-Polling via gh CLI (wenn verfügbar):**
- Lieber kurze status snapshots als endloses Streaming.
- Polling-Intervall konservativ wählen (z. B. 15–30s), um Rate Limits zu vermeiden.

**Evidence Capture:**
- Bei UI-Timeouts: Screenshot + Timestamp + "Attempt #n" notieren.
- Bei CLI: Ausgabe in eine lokale Notizdatei kopieren (kein Commit erforderlich).

## 5. Gate-spezifische Triage-Kurzpfade
### 5.1 docs-reference-targets-gate
**Typische Ursachen:**
- Verweis auf nicht existierende Datei/Anker
- Branch-Namen/Begriffe, die wie Pfade aussehen

**Sofortmaßnahmen:**
- Betroffene Markdown-Datei lokalisieren (CI Output) und Referenz neutralisieren:
  - Entweder existierenden Target-Link setzen oder Text so umformulieren, dass er nicht als Target interpretiert wird.

### 5.2 Check Docs Link Debt Trend
**Typische Ursachen:**
- "Nackte" Pfad-Strings, die wie Links wirken
- Unsaubere Markdown-Struktur

**Sofortmaßnahmen:**
- Nicht-existente Targets entfernen/ersetzen
- Tabellen/Listen sauber formatieren

### 5.3 Lint Gate / audit (bei docs-only selten, aber möglich)
- Prüfen, ob Lint/Audit überhaupt docs betrifft oder indirekt getriggert wurde.
- Bei Verdacht auf Scope Drift: sofort SCOPE_KEEPER einschalten.

## 6. Eskalation & Kommunikation
**Wann eskalieren:**
- S3 Governance Risk sofort.
- S2 Gate Failure, wenn nach 2 Iterationen keine klare Ursache.

**Kommunikationsschema:**
- "Status / Impact / Evidence / Next Step / Owner / ETA (optional)"
- Kein Blame, nur Fakten.

## 7. Cross-References
- **Control Center Operations Runbook:**  
  `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_OPERATIONS.md`
- **Control Center Dashboard Runbook:**  
  `docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_4B_M3_CONTROL_CENTER_DASHBOARD.md`

## 8. Operator Output Template (Copy/Paste)
```
Timestamp (Europe/Berlin):
Incident Level:
Category:
Observed:
Expected:
Evidence Captured:
Repro Steps:
Top Hypotheses:
Next Safe Step:
Outcome:
```
