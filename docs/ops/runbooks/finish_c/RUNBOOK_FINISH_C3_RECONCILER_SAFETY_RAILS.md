# RUNBOOK — Finish C3: Reconciler & Safety Rails + Failure Szenario Tests

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, deterministisch, evidence‑first, **snapshot‑only**, **NO‑LIVE default**

> **Stop Rules (C3)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders.  
> - Tests sind **mock-only**; keine externe IO.  
> - **Keine Secrets** (auch nicht in Fail‑Logs).  
> - **Snapshot‑only**: keine Watch‑Loops.  
> - Scope‑Drift ⇒ STOP und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

Ein Reconciler stellt sicher, dass interne Sicht (intent/orders) und externe Sicht (broker snapshots/fills) konsistent bleiben — auch bei Fehlern:

- dedupe + idempotency enforcement
- bounded retries (kein retry storm)
- invariants + „tripwires“ (safety rails)
- failure matrix tests (timeouts, dupes, partial fills, out‑of‑order events)

---

## 1) Entry Point

### Voraussetzungen
- C2 Orchestrator dry-run pass.

---

## 2) Exit Point (DoD)

- Reconciler implementiert (mocked):
  - local intent vs broker-reported state reconciliation
  - detection of stuck/canceled/partial-fill mismatches
- Safety Rails:
  - hard disable live by default
  - invariants (no negative balances, no duplicate fills, idempotency enforcement)
  - bounded retries (no watch loops)
- Failure tests:
  - rate-limit responses
  - partial fills
  - timeout / transient failures
  - duplicate fill events (idempotency)
  - cancel race

---

## 3) Reconciler (minimal, mocked)

Ziel: Abgleich zwischen:
- **local intent/orders** (Orchestrator-Sicht)
- **broker-reported state** (Mock Broker snapshots + fills)

Outputs (beispielhaft):
- reconcile report (diffs/mismatches)
- planned corrective actions (mocked)

---

## 4) Safety Rails (Invariants, NO‑LIVE default)

> Invariants sind „hart“: Wenn verletzt ⇒ **STOPPING** + Operator Intervention.

- hard disable live by default (Design: default-off gating bleibt intakt)
- no negative balances
- no duplicate fills (idempotency enforcement)
- bounded retries (max attempts / max duration; deterministisch)

---

## 5) Failure Szenario Tests (mock-only)

- rate-limit responses
- partial fills
- timeout / transient failures
- duplicate fill events (idempotency)
- cancel race

---

## 6) Proposed File Map

**Code (proposed paths):**
- `src/execution/live/reconcile.py`
- `src/execution/live/safety.py`

**Tests (proposed paths):**
- `tests/execution/live/test_reconcile_failures.py`
- `tests/execution/live/test_safety_rails.py`

**Evidence (operator-created, optional):**
- `docs/ops/evidence/EV-YYYYMMDD-FINISH_C3-RECONCILE-PASS.md`

---

## 7) Snapshot Checks (no watch)

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git diff --stat

pytest -q
python -m ruff check .
python -m ruff format --check .
```

---

## 8) Artifacts

- Reconciler + safety rails + tests
- Evidence Snapshot (siehe `TEMPLATES_FINISH_C_EVIDENCE.md`)

---

## 9) Next PR Slice

**PR‑C4:** Observability (Health + Order‑Lifecycle Metrics) + Operator UX Dry‑Run (watch‑only).  
Siehe `RUNBOOK_FINISH_C4_OBSERVABILITY_OPERATOR_DRYRUN.md`.
