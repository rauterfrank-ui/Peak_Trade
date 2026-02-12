# RUNBOOK: Tech-Debt Top-3 ROI bis Finish (Cursor Multi-Agent Chat)

Stand: 2026-01-28  
Modus: **Cursor Multi-Agent Chat**  
Leitplanken: **NO-LIVE / Research-safe** • kleine PRs • deterministisch • token-policy-safe Docs

---

## 1) Zielbild

Wir erledigen (technisch) die **Top-3 ROI Tech-Debt Items** aus dem Backlog in **3 kleinen PRs**:

1) **C — Equity-Curve Loader vollständig**  
   - Dummy/None/„nicht implementiert“-Pfade entfernen  
   - betrifft: Monte-Carlo + Stress-Tests (Equity Curves laden)

2) **B — Timeframe aus Daten ableiten**  
   - hardcoded `"1h"` in `run_shadow_execution` eliminieren  
   - Override per CLI bleibt möglich

3) **E — Plot-Generation wirklich optional (`--no-plots`)**  
   - nicht nur Docs, sondern echter Flag + Guards + Test

**Definition of Done (pro Item)**  
- Code implementiert (kein stiller Dummy/None auf Standardpfad)  
- Tests vorhanden + grün (lokal & CI)  
- Docs aktualisiert (Backlog-Status-Kommentar + Fundstellen; Token-Policy safe)  
- Evidence Pack vorhanden  
- PR gemerged

---

## 2) Scope / Nicht-Ziele

### In-Scope
- Nur die drei Items (C, B, E) inkl. minimaler Plumbing/Refactors, die dafür nötig sind

### Out-of-Scope
- Live-Trading / echte Exchange-Writes / echte Order-Sends
- Großrefactors außerhalb der drei Items
- „Eine PR für alles“

---

## 3) Rollenmodell (Cursor Multi-Agent)

**ORCHESTRATOR**  
- führt Phasen, stoppt Scope-Creep, trackt Checklisten & Evidence

**ARCHITECT**  
- definiert Contracts (Loader API, Failure-Modes, Flag-Plumbing)

**IMPLEMENTER**  
- setzt Code um, hält Diffs klein, entfernt Dummy-Fallbacks

**TEST_ENGINEER**  
- erstellt Fixtures + Unit/Integration-Tests (stabil, deterministic, no externals)

**DOCS_SCRIBE**  
- aktualisiert Backlog/Notes (token-policy safe), ergänzt Fundstellen

**OPS_SCRIBE**  
- PR Body + Evidence Pack, Verification Steps, Operator How-To

**RISK_OFFICER**  
- prüft NO-LIVE, Side-Effects, Defaults, Failure-Modes (kein stilles „tut so als ob“)

---

## 4) Branch/PR Strategie

**Eine Änderung = ein Branch = eine PR.** Empfohlen:

- `feat/techdebt-equity-loader`  → Item C  
- `feat/techdebt-timeframe-infer` → Item B  
- `feat/techdebt-no-plots-flag` → Item E

PR Titles (Beispiel):
- `techdebt(C): implement equity curve loader for experiments`
- `techdebt(B): infer timeframe in shadow execution`
- `techdebt(E): add --no-plots flag (real)`

---

## 5) Phase Plan bis Finish

### Phase 0 — Pre-Flight (Operator Safety)

Ziel: Sicherstellen, dass du im richtigen Repo bist und nicht in einer Shell-Continuation hängst.

```bash
# == PRE-FLIGHT (Ctrl-C wenn du in > / dquote> / heredoc festhängst) ==
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb 2>/dev/null || true
```

Exit-Kriterium: Repo root sichtbar + `git status -sb` ok.

---

### Phase 1 — Discovery (exakte Stellen + Kontext)

Ziel: Exakte Stellen im Code lokalisieren, damit Design/Implementation minimal bleibt.

#### Item C (Equity Loader)
Hunt:
- Monte-Carlo Loader/None-Pfad
- Stress-Tests Dummy/Fallback Pfad
- existierende Run-Dir / Export / Registry-Mechaniken (wenn vorhanden)

Output:
- Welche Artefakte sind „Equity Curves“? (Format, Pfad, Name)
- Welche Call-Sites müssen umgestellt werden?
- Minimaler Contract + Failure-Mode

#### Item B (Timeframe Infer)
Hunt:
- Stelle mit hardcoded `"1h"`
- Woher kommt das DataFrame/Index?
- Welche Timeframes sind im Projekt üblich (m/ h/ d)?

Output:
- Minimaler Inference-Algorithmus
- Override-Logik
- Testfälle

#### Item E (`--no-plots`)
Hunt:
- Wo werden Plots erzeugt? (`matplotlib`, `plotly`, `savefig`, Report-Assets)
- Welche Runner/CLIs sind „große Runs“ (Sweeps/Research/Reporting)?

Output:
- Liste der zentralen Plot-Entry-Points
- Minimaler Flag-Plan
- Testplan (keine Artefakte bei `--no-plots`)

Exit-Kriterium: Für C/B/E jeweils 5–10 Zeilen „Current → Target → Minimal Contract“.

---

### Phase 2 — Design (Contracts, Failure-Modes, Minimal-API)

Ziel: Einmal sauber entscheiden, bevor Code geschrieben wird.

#### Item C — Equity-Curve Loader Contract (empfohlen)
- Einführung eines shared Loaders, z.B. `src&#47;experiments&#47;equity_loader.py`
- API (Beispiel):
  - `load_equity_curves_from_run_dir(run_dir, *, max_curves=None) -> list[pd.Series]`
  - optional: `load_equity_curves_from_results(results_obj, ...) -> list[pd.Series]`

**Regel:** Standardpfad liefert **niemals** `None`.  
Wenn keine Daten vorhanden: `ValueError` mit hilfreicher Message (oder explizites `allow_dummy=True`, nur wenn wirklich notwendig).

#### Item B — Timeframe Inference Contract
- Funktion: `infer_timeframe_from_index(index: pd.DatetimeIndex) -> str`
- Heuristik:
  - median delta berechnen
  - Mapping auf `1m, 5m, 15m, 30m, 1h, 4h, 1d`
- Verhalten:
  - Wenn CLI `--timeframe` gesetzt: Override gewinnt
  - Wenn Index irregular und kein Override: klarer Fehler oder warn + definierter Fallback (Design festlegen!)

#### Item E — `--no-plots`
- Flag wird in den wichtigsten Runnern eingeführt (mind. 1 „großer Run“)
- Plot-Calls werden guard-ed:
  - `if no_plots: skip`
  - optional: 1 Logzeile „plots disabled“
- Tests:
  - garantiert keine Plot-Artefakte auf Disk bei `--no-plots`

Exit-Kriterium: RISK_OFFICER gibt Go für die Contracts (NO-LIVE, keine stillen Fakes).

---

### Phase 3 — Implementierung (3 PRs)

Ziel: Kleine, reviewbare Diffs. Jede PR führt nur ein Item durch.

#### PR-C: Equity Loader
- neuen Loader anlegen
- Monte-Carlo Loader-Pfad auf Loader umstellen
- Stress-Tests Dummy-Pfad entfernen/ersetzen

#### PR-B: Timeframe Infer
- Inference-Funktion + Mapping
- hardcoded `"1h"` entfernen
- Override-Logik (CLI wins) sicherstellen

#### PR-E: `--no-plots`
- Flag in Runner(n)
- Guards in Plot-Entry-Points
- Minimal invasive, ohne große Refactors

Exit-Kriterium: PR Branch builds lokal, Tests (targeted) grün.

---

### Phase 4 — Tests (Unit + Mini-Integration)

Ziel: Jeder PR bringt belastbare Tests, die echte Regression verhindern.

#### Item C Tests (Beispiele)
- `tests&#47;experiments&#47;test_equity_loader.py`
  - `tmp_path` Fixture mit minimalen Equity Artefakten
  - assert `len(curves) > 0`
- Integration:
  - Monte-Carlo kann mit geladenen Curves laufen
  - Stress-Tests laufen ohne Dummy-Fallback

#### Item B Tests (Beispiele)
- `tests&#47;scripts&#47;test_timeframe_infer.py`
  - `DatetimeIndex` mit festen Frequenzen → erwarteter timeframe string
  - irregular case → Verhalten wie im Contract

#### Item E Tests (Beispiele)
- `tests&#47;scripts&#47;test_no_plots_flag.py`
  - Runner mit `--no-plots` in `tmp_path` ausführen
  - assert: keine Plot-Dateien / keine plot assets erzeugt

Exit-Kriterium: Tests grün, keine Flakes, keine externen Abhängigkeiten.

---

### Phase 5 — Docs Update (Backlog + Notes)

Ziel: Backlog-Checkboxen bleiben ggf. formal offen, aber der **Implementierungsstand** wird dokumentiert.

Pflicht:
- Backlog-Datei ergänzen:
  - Status-Kommentar „implemented in PR/commit …“
  - Fundstellen (Datei + Lines/Abschnitt), sodass man es wiederfindet

Für Item E zusätzlich:
- Performance Notes ergänzen:
  - Beispiel-CLI in Code-Fence
  - erwartetes Verhalten (keine Plot-Artefakte)

Exit-Kriterium: Docs sind token-policy safe (Pfade/Commands in Code-Fences).

---

### Phase 6 — PR Review & Merge

Ziel: PRs sauber, required checks PASS, Merge entsprechend eurer Gates.

OPS_SCRIBE liefert pro PR:
- PR Body (Template unten)
- Verification Kommandos
- Risk Note (NO-LIVE)

Exit-Kriterium: PR gemerged + Branch gelöscht (wenn Standard).

---

### Phase 7 — Evidence Pack & Finish Marker

Ziel: Reproduzierbare Evidence je Item.

Pro Item eine Evidence-Datei:

```text
docs/ops/evidence/EV_TECH_DEBT_<ITEM>_<YYYYMMDD>.md
```

Evidence Inhalt (Pflicht):
- PR Link + Merge Commit
- Tests executed (exakte commands)
- Result Summary (kurz)
- ggf. File-List / Artefakte (z.B. „no plots generated“)

Finish ist erreicht, wenn:
- 3 PRs gemerged (C/B/E)
- 3 Evidence-Files vorhanden
- Backlog Status-Kommentare + Fundstellen ergänzt

---

## 6) Cursor Multi-Agent Chat — Startprompt (ORCHESTRATOR)

> In Cursor Multi-Agent Chat als erste Nachricht einfügen.

```text
Du bist ORCHESTRATOR für Peak_Trade Tech-Debt Top-3 ROI bis Finish.
Scope ist strikt: (C) Equity Curve Loader für MonteCarlo+StressTests, (B) Timeframe infer in shadow execution, (E) echtes --no-plots.
Arbeite mit Agenten: ARCHITECT, IMPLEMENTER, TEST_ENGINEER, DOCS_SCRIBE, OPS_SCRIBE, RISK_OFFICER.

Regeln:
- 3 kleine PRs, kein Scope-Creep.
- Keine stillen Fallbacks: keine None-Returns als Normalfall, klare Fehler oder explizites Flag.
- Token-policy safe docs: Pfade/Commands in Code-Fences.
- Liefere am Ende je Item: (1) Datei-Liste, (2) Tests, (3) PR Body, (4) Evidence Pack Content.

Starte mit Phase 1 (Discovery): Sammle exakte Stellen + Kontext + minimalen Contract-Vorschlag je Item.
```

---

## 7) PR Body Template (OPS_SCRIBE)

```md
## Summary
<1–2 Sätze>

## Why
<Problem / Impact>

## Changes
- ...
- ...

## Verification
- Tests:
  - <command>
- Evidence:
  - <path to EV file>

## Risk
LOW/MED + Begründung (NO-LIVE, keine side effects)

## Operator How-To
- <wie nutzen, wenn relevant>
```

---

## 8) Checklisten (ORCHESTRATOR)

### Item C — Equity Loader
- [ ] Discovery: exakte Fundstellen + Artefakt-Quelle geklärt
- [ ] Contract: kein `None` auf Standardpfad
- [ ] Loader implementiert
- [ ] Monte-Carlo integriert
- [ ] Stress-Tests integriert
- [ ] Tests + Fixtures grün
- [ ] Docs: Backlog Status + Fundstellen
- [ ] PR merged
- [ ] Evidence File

### Item B — Timeframe Infer
- [ ] Discovery: hardcode gefunden + Datenquelle klar
- [ ] Inference implementiert (median delta + mapping)
- [ ] Override (CLI wins)
- [ ] Tests: freq + irregular case
- [ ] Docs: Backlog Status + Fundstellen
- [ ] PR merged
- [ ] Evidence File

### Item E — `--no-plots`
- [ ] Discovery: Plot-Entry-Points identifiziert
- [ ] Flag in Runner(n) implementiert
- [ ] Plot guards implementiert (keine Artefakte)
- [ ] Tests: no plot artifacts
- [ ] Docs: Performance Notes + Backlog Status + Fundstellen
- [ ] PR merged
- [ ] Evidence File

---

## 9) Evidence Template (OPS_SCRIBE)

```md
# EV_TECH_DEBT_<ITEM>_<YYYYMMDD>

PR: <link>
Merge Commit: <sha>

## Scope
- <Item C/B/E: 1–2 bullets>

## Tests executed
- <command>
- <command>

## Verification result
- PASS: <short>

## Notes / Risk
- NO-LIVE confirmed
- <any caveats>
```

---

## 10) Operator Notes (Guardrails)

- Keine „Dummy“-Implementationen als Default akzeptieren.
- Keine stillen Fallbacks, die Research-Ergebnisse „schönrechnen“.
- Wenn etwas optional sein soll: explizites Flag + klar dokumentiertes Verhalten.
- Wenn etwas fehlt: lieber sauberer Fehler mit hilfreicher Message als `None`.
