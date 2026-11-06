# Peak_Trade — Finish Runbook Pack (Cursor Multi‑Agent)

**Datum:** 2026-01-18  
**Modus:** governance‑safe, deterministisch, evidence‑first, **NO‑LIVE standard**  
**Kontext:** Cursor Multi‑Agent Chat (ORCHESTRATOR + 3–7 Agents parallel)

> **Stop Rules (global)**  
> - Kein Live‑Trading, keine Broker‑Orders, keine Secrets in Logs.  
> - Keine Watch‑Loops als Default (nur Snapshot‑Checks), außer explizit im Runbook erlaubt.  
> - Scope‑Drift → ORCHESTRATOR stoppt und fordert Re‑Scoping.  
> - Jede Phase endet mit einem **Snapshot** (Status/Gates/Artefakte).  

---

## Rollen (Standard‑Team, 3–7 Agents)

**ORCHESTRATOR (Lead):** Struktur, Phasen, Entscheidungen, Stop bei Drift  
**SCOPE_KEEPER:** Pfad-/Änderungsgrenzen, additive-only falls gefordert  
**ARCHITECT:** Contracts/Schemas, DoD, Abgrenzung  
**IMPLEMENTER:** Code/Config Changes (kleinste sinnvolle PR‑Slices)  
**TEST_ENGINEER:** Tests, determinism checks, fixtures  
**CI_GUARDIAN:** gh checks Snapshot, required checks hygiene  
**DOCS_SCRIBE:** Runbooks, Frontdoor Links, operator quickstarts  
**EVIDENCE_SCRIBE:** Evidence‑Snapshots, Merge‑Logs, EV‑IDs  
**RISK_OFFICER:** NO‑LIVE, safety rails, rollback/incident packs

> In Cursor Multi‑Agent Chat: ORCHESTRATOR startet alle Agents parallel (3–7) und sammelt Outputs pro Phase.

---

## Terminal‑Pre‑Flight (Pflichtblock für alle Runbooks)

```bash
# If you see > / dquote> / heredoc>, press Ctrl-C.

cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
pwd
git rev-parse --show-toplevel
git status -sb
```

# RUNBOOK B — Finish Level B (Beta): ExecutionPipeline + Ledger + Paper‑Trading (NO‑LIVE)

## Ziel (Definition)
Backtest‑Strategien laufen **über eine Execution‑Pipeline** (order intent → routed order → fills) mit:
- deterministischem Execution‑Simulator (fees/slippage/latency/partials)
- Ledger/Accounting (positions, realized/unrealized, fees)
- Pre‑Trade Risk Checks (exposure, max position, kill switch)
- Observability (order lifecycle metrics) — weiterhin watch‑only

## Einstiegspunkte
- **B‑E0:** “Signal→Trade” direkt im Backtest (keine Order‑Lifecycle).
- **B‑E1:** Order‑Model existiert, aber kein Ledger.
- **B‑E2:** Ledger existiert, aber Fill‑Semantics nicht deterministisch.
- **B‑E3:** Tests fehlen/fragil.

## Endpunkt (DoD)
- ExecutionPipeline Package:
  - `OrderIntent`, `OrderRequest`, `Order`, `Fill`, `ExecutionEvent`
  - deterministische Sim‑Engine (seeded)
  - `execution_events.jsonl` (append‑only)
- Ledger + Reconciler invariants getestet
- Pre‑trade rejects mit Codes + Logs
- Backtest Engine nutzt ExecutionPipeline (Strategy emits intents)
- CI: PASS; Docs: Contract + Operator runbook + Evidence

---

## Phase B0 — Architecture & Contracts (ARCHITECT + RISK_OFFICER)
**Exit:** Minimal viable pipeline contract frozen.

## Phase B1 — ExecutionPipeline Core (IMPLEMENTER + TEST_ENGINEER)
**Exit:** End‑to‑end for one intent; determinism tests PASS.

## Phase B2 — Ledger & Accounting (IMPLEMENTER + TEST_ENGINEER)
**Exit:** Reconciler invariants PASS.

## Phase B3 — Strategy→Execution Bridge (IMPLEMENTER)
**Exit:** Backtest produces execution log + trades.

## Phase B4 — Risk Gates & Circuit Breakers (RISK_OFFICER + IMPLEMENTER)
**Exit:** Reject codes observable + tested.

## Phase B5 — Observability & Watch‑Only Metrics (IMPLEMENTER + DOCS_SCRIBE)
**Exit:** local verify shows metrics + dashboard panels.

## Phase B6 — Docs/Evidence/Release (DOCS_SCRIBE + EVIDENCE_SCRIBE + CI_GUARDIAN)
**Exit:** Green CI + evidence pack.

---

## Cursor Multi‑Agent Promptblock (Start)
> **Wo einfügen:** Cursor Chat → Multi‑Agent

```md
ORCHESTRATOR: Starte RUNBOOK B (ExecutionPipeline Beta) mit 7 Agents parallel.
Agents: ARCHITECT, IMPLEMENTER, TEST_ENGINEER, RISK_OFFICER, CI_GUARDIAN, DOCS_SCRIBE, EVIDENCE_SCRIBE, SCOPE_KEEPER.

Phase B0: Liefere Contracts + PR‑Slice Plan (mind. 5 Slices).
Output: Plan + dann Phase B1 Promptblock (Slice 1).
```
