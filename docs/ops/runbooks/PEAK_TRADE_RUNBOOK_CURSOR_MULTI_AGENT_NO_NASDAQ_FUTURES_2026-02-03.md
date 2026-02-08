# Peak_Trade – Cursor Multi‑Agent Runbook (ohne Nasdaq/Futures)

**Quelle:** `UEBERSICHT_OFFENE_PUNKTE.md` (Stand 2026‑02‑03).  
**Wichtig:** Alles rund um *Nasdaq* und/oder *Futures‑Handel* wird in diesem Runbook **bewusst ausgelassen** und nicht geplant/implementiert. (Später separat.)  
**Prinzipien:** Offline‑First · Safety‑First · Evidence‑Chain · Reproduzierbarkeit · deterministische Gates (kein Live by default)

---

## 0) Multi‑Agent Setup (Cursor)

### 0.1 Rollen (Agents) & Verantwortlichkeiten
- **Orchestrator (L0 / Primary + Critic)**  
  Zerlegt Arbeit in Phasen/Tasks, definiert Acceptance Criteria, pflegt Evidence‑Chain.
- **Implementer (L1 / Primary)**  
  Implementiert Code/Configs/Scripts gemäß Task‑Spec.
- **Verifier (L4 / Critic)**  
  Policy/Safety/Quality‑Review: Gates, gefährliche Pfade, nicht deterministische Stellen, Logging/Audit.
- **Tester (QA)**  
  Tests, Repro, CI‑Kompatibilität, Regression‑Checks, Coverage‑Risiken.
- **Docsmith (Docs/Ops)**  
  Docs/Runbooks/Drills/Evidence Packs, Operator‑UX, “how to run” + “how to debug”.

> **Definition:** Jede Phase endet mit **Evidence Pack** (Artefakte + Checks + Verweise), bevor die nächste Phase startet.

### 0.2 Standard‑Artefakte pro Task (Evidence‑Chain)
- `run_id` / `results_id` (oder Äquivalent) als stabile Referenzen
- Logs: Start/Ende, Parameter, Git SHA, Env‑Infos
- Tests/Checks: `pytest`, Lints/Format, (falls vorhanden) Evidence‑Validator
- Minimaler README‑Abschnitt: *Purpose*, *How to run*, *Failure modes*

### 0.3 Default‑Commands (lokal)
```bash
git status
git rev-parse --short HEAD
python -V
python -m pip -V
python -m pip install -e ".[dev]"
pytest -q
```

---

## 1) Phase A – Baseline & Repo‑Readiness

### Ziel
Stabile Arbeitsbasis: saubere Toolchain, reproduzierbare Runs, eindeutige Runner‑Konventionen.

### Einstieg (Entry)
- Repo lokal verfügbar, `python -m pip install -e ".[dev]"` läuft
- `pytest -q` ist grundsätzlich ausführbar (auch wenn einzelne Tests derzeit ignored sind)

### Schritte
1. **Repo‑Hygiene**
   ```bash
   git fetch --all --prune
   git status
   ```
2. **Smoke‑Tests**
   ```bash
   pytest -q
   ```
3. **CI/Drill‑Inventory vorbereiten (D01 #1)**
   - Liste der CI‑Workflows + Haupt‑Gates in `docs/ops/drills/` ablegen.

### Exit (Done)
- `pytest -q` läuft deterministisch (bekannte Ausnahmen dokumentiert)
- D01‑Inventory Draft vorhanden (als Markdown)
- Evidence Pack A erstellt

---

## 2) Phase B – Evidence‑Chain Standardisieren (Runner‑konform)

### Ziel
Einheitliche Runner‑Signatur: `run_id`, `results/`, Registry‑Logging, konsistente CLI‑Flags, reproduzierbare Reports.

### Einstieg
- Phase A done
- Runner‑Index (Docs) als Referenz verfügbar

### Schritte (Top‑Priorität laut Übersicht)
1. **`research_cli.py` – PARTIAL → READY**
   - `run_id/results/` vollständig integrieren
   - Output‑Layout standardisieren: `artifacts/<run_id>/...`
2. **`run_backtest.py` – READY**
   - Als Referenz für Output‑Konventionen verwenden
3. **`live_ops.py` – TODO**
   - Fokus hier: **Evidence‑Chain + Readiness**, nicht “Live”.  
   - Dummy‑Adapter klar markieren + Schnittstellen definieren.

### Command‑Checks
```bash
python scripts/research_cli.py --help
python scripts/run_backtest.py --help
python scripts/live_ops.py --help || true
```

### Exit
- Alle Tier‑A Runner erzeugen identische Evidence‑Struktur
- Dokumentierte “How to reproduce” Schritte
- Evidence Pack B erstellt

---

## 3) Phase C – Risk Layer: Foundation & VaR Core (kritisch)

### Ziel
Risk‑Core gemäß Roadmap Phase 1: VaR‑Grundlagen, saubere Schnittstellen, deterministischer Output.

### Einstieg
- Phase B done (Evidence‑Chain steht)
- Risk‑Roadmap als Referenz

### Schritte
1. **Risk‑API definieren** (Interfaces, Inputs/Outputs, Units)
2. **VaR Core implementieren**
   - Parametrisierung & Defaults
   - Logging/Audit (Inputs, Konfidenz, Horizon, Method)
3. **Integration Hooks (Defense‑in‑Depth vorbereiten)**
   - *Kill‑Switch* bleibt Stub, aber Hook‑Points sauber.

### Checks
```bash
pytest -q
python -m pip check
```

### Exit
- VaR Core vorhanden + Unit‑Tests
- Dokumentierte Failure‑Modes
- Evidence Pack C erstellt

---

## 4) Phase D – Risk Layer: Backtesting & Validation (kritisch)

### Ziel
Roadmap Phase 2: VaR‑Backtesting, Validierung, Report‑Artefakte.

### Einstieg
- Phase C done

### Schritte
1. Backtesting‑Methoden (z. B. Kupiec/Christoffersen‑ähnliche Logik – je nach Spec)
2. Validierungs‑Reports in Evidence‑Chain integrieren
3. CI‑Gate: Risk‑Backtest muss deterministisch sein (seeded)

### Exit
- Reproduzierbarer Risk‑Validation‑Report pro `run_id`
- Evidence Pack D erstellt

---

## 5) Phase E – Risk Layer: Stress Testing & Szenarien (kritisch)

### Ziel
Roadmap Phase 4: Stress‑Tests + Szenarien in Evidence‑Chain.

### Einstieg
- Phase D done

### Schritte
1. Szenario‑Definitionen als versionierte Configs
2. Stress‑Runner: `--run/--report` Pattern
3. Output: Tabellen + Plots (optional), alles unter `artifacts/<run_id>/`

### Exit
- Stress‑Suite läuft lokal + CI‑fähig
- Evidence Pack E erstellt

---

## 6) Phase F – Tests/Infra Fix: `test_live_web.py`

### Ziel
Collection Error beheben (oder Test entfernen), damit `pytest` ohne `--ignore` läuft.

### Einstieg
- Phase A done

### Schritte
```bash
pytest -q tests/test_live_web.py -vv
# Fehlerursache isolieren, dann entweder reparieren oder sauber entfernen/skippen
```

### Exit
- Kein Collection Error mehr
- Entscheidung dokumentiert (Fix vs. Remove)
- Evidence Pack F erstellt

---

## 7) Phase G – Backtest‑Registry: Tests & Dynamic Rebalancing

### Ziel
Backtest‑Registry robust machen (Unit‑Tests) + Dynamic Rebalancing implementieren (TODO).

### Einstieg
- Evidence‑Chain Konventionen stehen (Phase B)

### Schritte
1. Unit‑Tests für Registry‑API
2. Dynamic Rebalancing (Config‑gesteuert)
3. Docs: API/Implementation nachziehen

### Exit
- Registry‑Tests laufen in CI
- Dynamic Rebalancing implementiert + dokumentiert
- Evidence Pack G erstellt

---

## 8) Phase H – Feature‑Engine & Meta‑Labeling (Scaffold)

### Ziel
`src/features/` von Placeholder zu nutzbarer Basisschicht: Feature‑Pipeline, Meta‑Labeling Stubs entfernen.

### Einstieg
- Phase B done

### Schritte (aus Übersicht)
1. Feature‑Engine Skeleton (Contracts, DataFrame‑Schemas, Caching Hooks)
2. `compute_triple_barrier_labels` implementieren (kein “return zeros”)
3. `_extract_features` implementieren (kein leeres DataFrame)

### Checks
```bash
pytest -q
python -c "import pandas as pd; print('ok')"
```

### Exit
- Features liefern valide Outputs + Tests
- Evidence Pack H erstellt

---

## 9) Phase I – Research Sweeps & Robustness Automation

### Ziel
Research‑Pipeline konsolidieren: Sweeps, Metriken, Robustness, Reports.

### Einstieg
- Phase H (mind. Meta‑Labeling/Features) done

### Schritte
1. Unified Pipeline‑CLI: `run_sweep_pipeline.py --run/--report/--promote`
2. Templates: Heatmap (2×2), Drawdown‑Heatmap, Rolling‑Stabilität
3. Robustness: Monte‑Carlo + Correlation‑Matrix‑Plot
4. Metriken erweitern: Calmar, Ulcer, Recovery‑Factor

### Exit
- Nightly‑fähig (lokal triggerbar), deterministisch seedbar
- Evidence Pack I erstellt

---

## 10) Phase J – Learning/Promotion Loop (Bridge/Emitter)

### Ziel
Learning Loop Bridge + Emitter implementieren (High). Später: Automations/Slack/UI.

### Einstieg
- Phase I done (Results/Registry vorhanden)

### Schritte
1. Bridge (Results → Proposal)
2. Emitter (Proposal → Artefakte/Queue)
3. Minimal‑Automation Hook (Medium), Slack/UI bleiben Low

### Exit
- End‑to‑End Proposal Cycle lokal lauffähig
- Evidence Pack J erstellt

---

## 11) Phase K – Ops Drills (D01/D07)

### Ziel
Operatives Vertrauen: Drill‑Packs, Timeboxing, Incident Micro‑Drill.

### Einstieg
- Phase A done

### Schritte
1. D01 #1 CI Workflow Inventory finalisieren
2. D01 #2 Timebox Guidance aktualisieren
3. D07 Incident Micro‑Drill durchführen (Timeout Handling)

### Exit
- Drill‑Artefakte versioniert + wiederholbar
- Evidence Pack K erstellt

---

## 12) Phase L – Performance & Scale (Research‑Runs)

### Ziel
Große Sweeps effizient + leise: Caching, Logging‑Throttle, Pandas‑Optimierungen.

### Einstieg
- Phase I done

### Schritte
1. Data‑Layer Caching (Parquet/Reuse) ausbauen
2. Logging drosseln (Silent/Benchmark Mode)
3. Pandas‑Optimierungen (Zwischenkopien, Vektorisierung)

### Exit
- Benchmark‑Run zeigt messbare Verbesserungen
- Evidence Pack L erstellt

---

## 13) Phase M – Release Readiness (v1.x)

### Ziel
“Ship‑bar”: Docs, Gates, Known Limitations sauber, keine impliziten Live‑Pfad‑Aktivierungen.

### Einstieg
- Phase B + C + F mindestens done

### Schritte
1. Known Limitations aktualisieren (ohne Nasdaq/Futures)
2. Safety‑Gates Review (L4 Critic Pflicht)
3. Docs: Quickstart + Troubleshooting + Evidence‑Index

### Exit
- Release Checklist erfüllt
- Evidence Pack M erstellt

---

## Appendix – Cursor Task Templates

### Task‑Spec (Copy/Paste)
```text
TITLE:
SCOPE:
NON-GOALS:
ENTRY CRITERIA:
EXIT CRITERIA:
FILES/LOCATIONS:
IMPLEMENTATION NOTES:
TEST PLAN:
EVIDENCE PACK:
RISKS:
```

### Evidence Pack Layout (empfohlen)
```text
artifacts/<run_id>/
  meta.json
  logs/
  reports/
  plots/
  results/
  env/
```
