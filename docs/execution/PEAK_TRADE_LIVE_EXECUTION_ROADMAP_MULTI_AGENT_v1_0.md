# 🏔️ Peak_Trade — Live Execution Roadmap (Multi‑Agent / Cursor Edition) v1.0

Stand: 2025-12-29  
Quelle: abgeleitet aus *Live Execution Roadmap v1.1* (HTML) + Peak_Trade Workflow/Architektur-Notizen.  
Ziel dieses Dokuments: **Roadmap so schneiden, dass sie 1:1 mit Cursor Multi‑Agents** (parallel, konfliktarm, gate-driven) **umsetzbar** ist.

---

## 0) Kernprinzipien (nicht verhandelbar)

### Safety‑First / Gate‑Driven
- **Kein Live‑Trading ohne Evidence Packs.**
- **Kill‑Switch** (auto + manuell) muss erreichbar und getestet sein.
- **Shadow ≥ 12 Wochen**, **Testnet ≥ 16 Wochen** (nicht “wegoptimieren”).
- **Red Flags ⇒ sofortiger Stop**: Drawdown > 20%, Crash ohne Recovery, ungeklärte Recon-Divergenzen, Security Incident/Key Leak Verdacht.

### Multi‑Agent‑Ready by Design
Wir bauen **Work Packages (WPs)** so, dass:
- jede Einheit **klare File‑Ownership** hat (minimiert Merge-Konflikte),
- gemeinsame Berührungsflächen zuerst als **Contracts** stabilisiert werden,
- jede Einheit **DoD + Tests + Evidence** liefert,
- ein **Integrator‑Agent** alles zusammenführt und die Gate‑Checks fährt.

---

## 1) Cursor Multi‑Agent Operating Model (Standard)

### 1.1 Rollen
- **Integrator (Lead)**: definiert Contracts, genehmigt Schnittstellen, sammelt PR/Commits, löst Konflikte, führt CI/Tests aus, schreibt Gate‑Report.
- **Workstream Agents (A…D)**: implementieren ihre WPs strikt innerhalb der Ownership.

### 1.2 File‑Ownership Regeln
- Jeder WP hat einen **Ownership‑Block** (Pfadpattern).
- **No drive‑by refactors** außerhalb der Ownership.
- Shared‑Files (z.B. `config.toml`, zentrale src/core/config.py planned) werden **nur** vom Integrator geändert oder nach explizitem "Lock".

### 1.3 Branching / Merge‑Taktik
Empfohlen für Cursor Multi‑Agents:
- 1 gemeinsamer Feature‑Branch pro Phase: `feat/live-exec-phaseX-*`
- Pro Agent: kleine, saubere Commits (1–3).
- Integrator: squash/rebase nach Bedarf + “Integration Day” vor Gate.

### 1.4 Standard‑Artifacts pro WP
Jeder WP endet mit:
- **Files geändert/neu**
- **How to test** (pytest subset + ruff)
- **Evidence Output** (reports/*, docs/*, snapshots)
- **Risks / offene Punkte** (max 5)

---

## 2) Abhängigkeitsgraph (high level)

**Governance & Config** → **Execution Core** → **Shadow Trading** → **Testnet** → **Controlled Live** → **Production**  
Querschnitt: **Observability** + **Ops/Runbooks/Drills** begleiten *jede* Phase.

---

## 3) Architektur‑Alignment zu Peak_Trade (wichtig für Konfliktfreiheit)

Peak_Trade ist bereits modular aufgebaut (Data/Strategy/Core/Backtest + config + RiskManager).  
Daher gilt:
- Live‑Execution ergänzt, ersetzt aber nicht den Backtest‑Stack.
- Wir führen **ein neues Paket `src/execution/`** ein (klarer Namespace), und verdrahten es über **Contracts** an bestehende Komponenten:
  - Strategy‑Registry / Signal‑API
  - Config‑Loader
  - Risk‑Manager (wird in Live‑Pfad erweitert/gesplittet, aber kompatibel gehalten)

---

# PHASE 0 — FOUNDATION (Multi‑Agent Sprint‑Plan)

**Ziel:** Execution‑ und Risk‑Fundament so vollständig machen, dass Shadow Trading *aussagekräftig* ist und Testnet später *nicht* in Refactors erstickt.

## Phase‑0 Struktur (vorgeschlagene Pfade)
```
src/execution/
  contracts.py
  order_state_machine.py
  order_ledger.py
  position_ledger.py
  reconciliation.py
  retry_policy.py
  audit_log.py
  risk_hook.py
src/governance/
  live_mode_gate.py
src/observability/
  metrics.py
  logging.py
tests/execution/
tests/governance/
tests/observability/
docs/execution/
docs/ops/
reports/execution/
reports/risk/
```

## WP0E — Contracts & Interfaces (Integrator‑Blocker)
**Owner:** Integrator  
**Ownership:** `src/execution/contracts.py`, `src/execution/risk_hook.py`, minimale shared types.  
**DoD:**
- Definiert stabile Typen/Protokolle: `Order`, `OrderState`, `Fill`, `LedgerEntry`, `ReconDiff`, `RiskDecision`.
- Execution ruft Risk **über Interface** auf (keine zyklischen Imports).
- Minimaler Serialisierungs-/Determinismus‑Test (repr/json).

**Evidence:**
- `reports/execution/contracts_smoke.json` (stabiler Snapshot)
- `tests/execution/test_contracts_*.py` grün

---

## WP0A — Execution Core v1 (Critical Path)
**Agent:** Exec‑Agent  
**Ownership:** `src/execution/order_state_machine.py`, `order_ledger.py`, `position_ledger.py`, `audit_log.py`, `retry_policy.py` + `tests/execution/*`.

**DoD (MVP, testbar):**
- OSM: `CREATED → SUBMITTED → ACK → FILLED → CLOSED`
- Idempotente Transitions (retry‑sicher)
- Position Ledger = Single Source of Truth
- Audit Log append‑only & deterministisch
- Retry/Backoff Policy mit Error‑Taxonomie (stub ok)

**Tests:**
- State transition matrix + idempotency
- Ledger invariants (positions, realized/unrealized)
- “crash‑restart” Simulation (in‑memory rebuild) als unit/integration‑test

**Evidence:**
- `reports/execution/state_machine_coverage.md`
- `reports/execution/crash_restart_simulation.json`

---

## WP0B — Risk Layer v1.0 (Blocker)
**Agent:** Risk‑Agent  
**Ownership:** `src/execution/risk_hook.py` (nur via Contract), `src/risk_layer/live/*` oder `src/risk_layer/runtime/*`, `reports/risk/*`, `tests/risk_layer/*`.

**DoD:**
- Risk ist “first‑class citizen” im Execution Flow (RiskDecision: ALLOW/BLOCK/PAUSE).
- Portfolio VaR/CVaR + Kupiec POF + Stress‑Test (deterministisch generierbar).
- Daily/Weekly Loss Limits + Max DD Circuit Breaker
- Kill Switch (auto + manuell) als callable Interface (noch kein Exchange nötig)

**Tests:**
- Limits triggern deterministisch
- Kill‑switch behavior (simulated)
- Report generator ist stabil (CI‑friendly)

**Evidence:**
- `reports/risk/var_cvar_kupiec_*.md`
- `reports/risk/stress_suite_*.md`

---

## WP0C — Governance & Config Hardening
**Agent:** Gov‑Agent  
**Ownership:** src/governance/live_mode_gate.py (planned), config‑validation module, `tests/governance/*`, ggf. minimal src/core/config.py (planned, nur wenn Integrator freigibt).

**DoD:**
- Startup fail‑fast bei invalid config (Schema validation).
- Env separation: `dev/shadow/testnet/prod`
- Secrets injection (env/secure store stub)
- Config change audit trail
- Live Mode gating: explizit enable + multi‑step confirmation (default **blocked**)

**Evidence:**
- `reports/governance/config_validation_report.md`
- “live mode is blocked by default” proof test

---

## WP0D — Observability Minimum
**Agent:** Obs‑Agent  
**Ownership:** `src/observability/*`, `tests/observability/*`, minimal dashboard glue (nur read‑only).

**DoD:**
- Metrics: orders/min, error‑rate, reconnects, latency p95/p99
- Structured logging: trace_id/session_id/strategy_id
- Minimal Dashboard Snapshot (JSON export) oder Hook in bestehende Live‑Track UI (read‑only)

**Evidence:**
- `reports/observability/metrics_snapshot.json`
- `reports/observability/logging_fields.md`

---

## Phase‑0 Gate (Go/No‑Go → Phase 1)
**Blocker:**
- Risk v1.0: unit/integration tests grün
- Kill Switch & Limits: mit Sim‑Drills verifiziert
- Execution v1: OSM + Ledger + Recon (mindestens stub) mit Tests

**Required Evidence Pack:**
- `reports/risk/` (VaR/CVaR/Kupiec + Stress)
- `reports/execution/` (OSM coverage + crash‑restart)
- `docs/ops/` Runbook drafts
- CI: ruff + tests (3.9/3.10/3.11) pass

---

# PHASE 1 — SHADOW TRADING (Multi‑Agent Plan)

**Ziel:** Live‑Datenstrom + Paper Execution, um Drift, Data Quality, Stabilität und Observability zu validieren — ohne Kapitalrisiko.

## WP1A — Live Data Feed v1
**Ownership:** `src/data/live/*` oder `src/data/providers/*` (passend zur Repo‑Struktur), `tests/data/*`  
**DoD:** WebSocket + Reconnect + Backfill; Normalisierung identisch zum Backtest; Quality checks; Latency monitoring p95/p99.

## WP1B — Shadow Execution (Paper)
**Ownership:** `src/execution/paper/*`, `tests/execution/test_paper_*`  
**DoD:** Paper Orders → Fill Simulation (Slippage/Fee); Ledger in paper‑mode; Journal/Trade Log + tägliche Summary.

## WP1C — Signal Validation & Drift Detection
**Ownership:** `src/monitoring/drift/*` oder `src/observability/drift/*`, `reports/drift/*`  
**DoD:** Comparator: Shadow vs Backtest expectations; Drift metrics; Daily report generator (deterministisch); Auto‑Pause Regeln.

## WP1D — Operator UX
**Ownership:** `src/live_track/*` oder `src/ops_center/*`, `docs/ops/*`  
**DoD:** Live session registry & status overview; Minimal Alerts (P1/P2) + Runbook links.

## Phase‑1 Gate (Go/No‑Go → Phase 2)
**MINIMUM RUNTIME:** ≥ 12 Wochen  
**Ziele (Metriken):**
- Data Uptime ≥ 99.5%
- System Uptime ≥ 99%
- Signal Match Rate ≥ 90%
- False Positive Rate ≤ 10%
- Recovery median < 30s; p95 < 2min

**Evidence Pack:**
- 12 Wochen tägliche Reports (Drift/Quality)
- Incident Log + Lessons Learned
- Dashboard snapshots
- Audit: keine untracked secrets, keine policy violations

---

# PHASE 2 — TESTNET (Multi‑Agent Plan)

**Ziel:** Echter Order‑Lifecycle gegen Exchange‑Sandbox: Auth, Rate‑Limits, Partial fills, Reconciliation, Crash‑Recovery, Latency.

## WP2A — Exchange Client (Testnet)
**DoD:** Auth + Key handling über Secret injection; Rate limiter; WebSocket fills; Contract tests (payloads, error taxonomy).

## WP2B — Lifecycle + Recon “unter Feuer”
**DoD:** Partial fills korrekt; Orphan orders recon/fix workflow; Crash‑restart drill: state rebuild → consistent.

## WP2C — Performance & Latency Tests
**DoD (Targets):**
- Signal→Order p95 < 2000ms
- Submission < 500ms
- Full roundtrip p95 < 5000ms

## WP2D — Drills (Pflicht)
**DoD:** 24h stress, weekend test, flash vol sim, forced disconnect, kill switch drill.

## Phase‑2 Gate (Go/No‑Go → Phase 3)
**MINIMUM RUNTIME:** ≥ 16 Wochen  
**Ziele:**
- Order success rate ≥ 99%
- Fill rate ≥ 98%
- Reconciliation 100% (keine ungeklärten Divergenzen)
- Drills: alle PASS (inkl. crash‑restart)

**Evidence Pack:**
- Drill reports + “what would have happened in live?”
- Security review checklist (keys, rotation, least privilege)
- Ops review (runbooks verifiziert, operator dry‑run)

---

# PHASE 3 — CONTROLLED LIVE (Multi‑Agent Plan)

**Ziel:** Erste echte Trades mit Micro‑Positions, strengen Limits, 24/7 Monitoring, dokumentierten Interventionspfaden.

## WP3A — Controlled Live Config & Scaling Rules
- Skalenplan als config‑gesteuerte “Step‑Ladder”
- Hard stops (DD, auto‑pause frequency, etc.) als enforceable rules

## WP3B — 24/7 Monitoring & Incident Response
- Alert routes (P1/P2), on‑call checklists, incident templates
- “Operator intervention playbook” (kill‑switch, pause, resume)

## WP3C — Safety Analytics & Postmortem Pipeline
- Daily performance/risk digest
- Incident + action item tracking (deterministisch exportierbar)

**Gate (Go/No‑Go → Phase 4):**
- Stabiler Betrieb, Interventionspfade mehrfach geprobt, keine ungeklärten Recon‑Issues, Security review aktuell.

---

# PHASE 4 — PRODUCTION (Multi‑Agent Plan)

**Ziel:** Skalierung, Multi‑Strategy, kontinuierliche Verbesserung, robuste Governance.

## WP4A — Scaling Governance
- Kapitalerhöhung nur nach 30 Tagen stabil + Risiko‑Review
- Max 2x pro Monat; Rollback bei >10% DD
- Multi‑Strategy nur mit cross‑strategy risk aggregation

## WP4B — Continuous Improvement Loop (gated)
- Daily ops review
- Weekly risk & performance review
- Monthly backtest refresh + promotion loop (gated)
- Quarterly security audit

---

## 4) Cursor Prompt Pack (Kurz‑Templates)

### 4.1 Master‑Prompt (pro Phase, in Cursor Multi‑Agent Chat)
- “Erzeuge 1 Integrator + N Workstream Agents”
- “Setze Ownership + No‑Refactor‑Rule”
- “Alle liefern Completion Reports + Tests”

### 4.2 Per‑Agent Prompt‑Snippet (Copy/Paste)
Jeder Agent bekommt:
- **Aufgabe/Scope**
- **Ownership‑Pfadpattern**
- **DoD & Tests**
- **Evidence Outputs**
- **Stop‑Conditions** (wenn Schnittstelle unklar → Integrator fragen, nicht raten)

---

## 5) Nächster sinnvollster Schritt (konkret)

**Phase 0 starten als WP0E → WP0A/B/C/D parallel**  
1) Integrator: Contracts (WP0E) finalisieren  
2) Danach parallel: Execution (0A), Risk (0B), Governance (0C), Observability (0D)  
3) Integration Day + Phase‑0 Gate evidence pack

- WP4B (Manual-Only): Operator Drills + Evidence Pack
  - docs/execution/WP4B_OPERATOR_DRILLS_EVIDENCE_PACK.md
  - docs/execution/WP4B_EVIDENCE_PACK_TEMPLATE.md

---

## 6) Toolbox: bg_job Runner (Timeout-sichere Background Jobs)

Im Multi-Agent Kontext entstehen oft lange laufende Tasks (Backtests, VaR-Suites, Trainings), die ohne Timeout-Management in Cursor-Sessions fehlschlagen können. Der bg_job Runner sichert robuste Ausführung mit PID-Tracking, Log-Capture und Exit-Code-Verifikation.

**Discovery-first Command:**
```bash
bash 'scripts'/'ops'/'bg_job.sh' --help || bash 'scripts'/'ops'/'bg_job.sh' help
```

**Referenz:** `docs/ops/PR_486_MERGE_LOG.md`
