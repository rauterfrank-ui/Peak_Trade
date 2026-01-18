# Peak_Trade — Finish Runbook A (MVP): Backtest → Artifacts → Report → Watch‑Only Dashboard

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance-safe, deterministisch, evidence-first, NO-LIVE  
**Kontext:** Cursor Multi‑Agent Chat (ORCHESTRATOR + 3–7 Agents parallel)

> **Stop Rules (global)**  
> - Kein Live‑Trading, keine Broker‑Orders, keine Secrets in Logs.  
> - Keine Watch‑Loops als Default (nur Snapshot‑Checks), außer explizit im Runbook erlaubt.  
> - Scope‑Drift → ORCHESTRATOR stoppt und fordert Re‑Scoping.  
> - Jede Phase endet mit einem Snapshot (Status/Gates/Artefakte).

---

## Rollen (Standard‑Team, 3–7 Agents)

- **ORCHESTRATOR (Lead):** Struktur, Phasen, Entscheidungen, Stop bei Drift
- **SCOPE_KEEPER:** Pfad-/Änderungsgrenzen, additive-only falls gefordert
- **ARCHITECT:** Contracts/Schemas, DoD, Abgrenzung
- **IMPLEMENTER:** Code/Config Changes (kleinste sinnvolle PR‑Slices)
- **TEST_ENGINEER:** Tests, determinism checks, fixtures
- **CI_GUARDIAN:** Required checks Snapshot, required checks hygiene
- **DOCS_SCRIBE:** Runbooks, Frontdoor Links, operator quickstarts
- **EVIDENCE_SCRIBE:** Evidence‑Snapshots, Merge‑Logs, EV‑IDs
- **RISK_OFFICER:** NO‑LIVE, safety rails, rollback/incident packs

> In Cursor Multi‑Agent Chat: ORCHESTRATOR startet die Agents parallel und sammelt Outputs pro Phase.

---

## Terminal‑Pre‑Flight (Pflichtblock)

```bash
# If you see > / dquote> / heredoc>, press Ctrl-C.

cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
pwd
git rev-parse --show-toplevel
git status -sb
```

---

## Ziel (Definition)

Ein Operator kann deterministisch einen Backtest laufen lassen und bekommt:
- standardisierte Run‑Artefakte (CSV/JSON)
- einen minimalen Report (HTML oder Notebook)
- eine Watch‑Only Web/API Ansicht (Run‑Liste + Run‑Detail + Health)
- grüne Tests + Docs‑Gates + Evidence‑Pack

---

## Einstiegspunkte

- **A‑E0 (Greenfield MVP):** Backtest läuft, aber Artefakte/Report/Web sind uneinheitlich.
- **A‑E1 (Artifacts existieren):** Es gibt schon Output‑Files; wir standardisieren Schema + Pfade.
- **A‑E2 (Web/API v0 existiert):** Wir ergänzen nur die fehlenden Endpunkte/Views.
- **A‑E3 (Docs/Gates rot):** Wir machen zuerst Gates‑Remediation, dann MVP‑Slice.

---

## Endpunkt (DoD)

### Artifacts Contract v1

- Canonical Runner erzeugt Run‑Folder mit:
  - `config_snapshot.json` (inkl. git sha, strategy_id, seed, timeframe, universe)
  - `equity.csv`, `trades.csv`, `metrics.json`, `run_manifest.json`
  - optional `report.html` (oder `report.ipynb`)

### Watch‑Only API (v0)

Endpoints (MVP):

```text
GET /api/v0/health
GET /api/v0/runs
GET /api/v0/runs/{run_id}
```

Optional (wenn schon vorhanden oder leicht ableitbar):

```text
GET /api/v0/runs/{run_id}/files
GET /api/v0/runs/{run_id}/equity
```

### Ops/Docs/CI

- Docs + Operator Quickstart (≤5 Minuten)
- CI: required checks clean, docs gates PASS
- Evidence: EV‑Snapshot + Merge‑Log Template bereit

---

## Phase A0 — Scope & PR‑Slicing (ORCHESTRATOR + ARCHITECT + SCOPE_KEEPER)

**Output:** 3–6 PR‑Slices, jeweils klein, testbar, gate‑safe.

**Agent Tasks (parallel):**
- ARCHITECT: MVP‑Contracts (Artifacts Schema v1 + API v0)
- SCOPE_KEEPER: Pfad‑Allowlist für MVP‑Slice
- CI_GUARDIAN: Required checks Liste + Snapshot Commands
- DOCS_SCRIBE: Operator Quickstart skeleton + Frontdoor link plan
- EVIDENCE_SCRIBE: Evidence Template (PASS snapshots)
- RISK_OFFICER: Stop rules + rollback notes

**Gate (Exit A0):**
- PR‑Plan: Slice‑Liste mit Files + Tests + Verify Steps.

---

## Phase A1 — Artifacts Contract v1 (ARCHITECT + IMPLEMENTER + TEST_ENGINEER)

**Ziel:** Ein Run‑Folder ist versioniert und maschinenlesbar.

**Implementations‑Checkliste:**
- `RunManifest` (run_id, started_at, git_sha, config_hash, seed, strategy_id, universe, timeframe, engine_version)
- Exporter:
  - `equity.csv`: timestamp, equity, drawdown, cash, exposure
  - `trades.csv`: ts, symbol, side, qty, price, fees, pnl
  - `metrics.json`: summary stats + risk stats
- Determinism: gleiche Inputs → gleiche `config_hash` + gleiche key metrics (Toleranzen definieren)

**Tests:**
- Golden snapshot test (small fixture dataset)
- Schema validation test (jsonschema/pydantic)

**Exit A1:**
- Lokaler Run produziert Artefakte; Tests PASS.

---

## Phase A2 — Minimal Report (DOCS_SCRIBE + IMPLEMENTER)

**Ziel:** Report generator aus Run‑Folder.

**Exit A2:**
- `report.html` wird erzeugt (inkl. Equity curve + key metrics table)

---

## Phase A3 — Watch‑Only API/Web v0 (IMPLEMENTER + TEST_ENGINEER + CI_GUARDIAN)

**Ziel:** Read‑only Endpunkte auf Artefakt‑Folder.

**Tests:**
- API contract tests
- Path traversal protection tests

**Exit A3:**
- Curl‑Snapshot zeigt alle Endpunkte OK.

---

## Phase A4 — Docs, Runbooks, Frontdoor (DOCS_SCRIBE + SCOPE_KEEPER)

**Exit A4:**
- docs-token-policy-gate + docs-reference-targets-gate PASS.

---

## Phase A5 — Evidence Pack + PR Merge Hygiene (EVIDENCE_SCRIBE + CI_GUARDIAN)

**Exit A5:**
- EV‑PASS snapshot committed (policy-konform).

---

## Cursor Multi‑Agent Promptblock (Start)

> Wo einfügen: Cursor Chat → Multi‑Agent

```md
ORCHESTRATOR: Starte RUNBOOK A (Finish MVP) mit 6 Agents parallel.
Agents: SCOPE_KEEPER, ARCHITECT, IMPLEMENTER, TEST_ENGINEER, CI_GUARDIAN, DOCS_SCRIBE, EVIDENCE_SCRIBE, RISK_OFFICER.

Phase A0: Erzeuge PR‑Slice Plan (3–6 Slices) + DoD Checkliste.
Output: Eine Seite Plan + dann Phase A1 Promptblock (Slice 1).
```
