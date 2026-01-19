# RUNBOOK — Finish C4: Observability + Operator UX + Dry-Run E2E

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, deterministisch, evidence‑first, **snapshot‑only**, **NO‑LIVE default**

> **Stop Rules (C4)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders.  
> - Operator UX bleibt **watch‑only** (read‑only).  
> - **Keine Secrets** (auch nicht in metrics labels/logs).  
> - **Snapshot‑only**: keine Watch‑Loops als Runbook‑Standard.  
> - Scope‑Drift ⇒ STOP und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

Finish‑C Observability & Operator UX für den Dry‑Run Track:

- Health/Readiness Snapshots
- Order‑Lifecycle Metriken (nur intern/fake events)
- Operator‑Dry‑Run (Start → Snapshot → Stop) ohne Live‑Enablement

---

## 1) Entry Point

### Voraussetzungen
- C3 reconciliation/safety stable.
- Dry‑Run kann deterministisch „n steps“ laufen (kein watch loop).

---

## 2) Exit Point (DoD)

- Health + Order lifecycle metrics (mocked):
  - counters for place/cancel/query
  - order state transitions
  - reconciliation mismatches
  - retry attempts used
- Operator UX (watch-only):
  - status snapshot endpoint oder CLI report
  - no write actions
- Dry-run E2E: orchestrator -> mock broker -> metrics -> snapshot report.

---

## 3) Observability Targets (mocked, minimal aber konkret)

### 3.1 Health
- `orchestrator_state`
- `last_audit_event_ts`
- `reconciler_last_ok_ts`
- `safety_rail_trips_total`

### 3.2 Execution / Order Lifecycle (aus Mock Broker Events)
- `orders_place_total`
- `orders_cancel_total`
- `orders_query_total`
- `order_state_transitions_total` (z.B. NEW→ACK→PARTIAL→FILLED)
- `reconcile_mismatches_total`
- `retry_attempts_total` (bounded)

> Keine Labels mit sensitiven Daten (keine account ids, keine tokens, keine raw symbols wenn policy es verbietet).

---

## 4) Operator UX (watch‑only, snapshot‑only)

> Ziel: einmaliger Dry‑Run, danach Snapshot‑Report exportieren (kein watch, keine write actions).

- Option A: **Status Snapshot Endpoint** (read‑only)
- Option B: **CLI Status Report** (read‑only, einmalig)

Dry‑Run Ablauf (E2E, snapshot‑only):
- Step 1: Pre‑flight + Tests
- Step 2: Dry‑Run starten (Mock Broker, enable‑flag bleibt false)
- Step 3: Metrics + Status Snapshot erzeugen (Report)
- Step 4: Prozess stoppen

---

## 5) Snapshot Checks (no watch)

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git diff --stat

pytest -q
python -m ruff check .
python -m ruff format --check .
```

---

## 6) Proposed File Map

**Code (proposed paths):**
- ``src&#47;observability&#47;execution_metrics.py`` (oder passender existing observability layer)
- ``src&#47;execution&#47;live&#47;status_snapshot.py``

**Tests (proposed paths):**
- ``tests&#47;observability&#47;test_execution_metrics.py``

**Operator Snapshots (local artifacts, not committed by default):**
- ``out&#47;finish_c&#47;dryrun_health_snapshot.json``
- ``out&#47;finish_c&#47;dryrun_status_snapshot.json`` (oder `.md`)
- ``out&#47;finish_c&#47;dryrun_metrics_snapshot.json``

---

## 8) Next PR Slice

**PR‑C5:** Controlled Readiness: Readiness‑Checklist + Evidence‑Templates + Incident Pack + final runbooks.  
Siehe `RUNBOOK_FINISH_C5_CONTROLLED_READINESS.md`.
