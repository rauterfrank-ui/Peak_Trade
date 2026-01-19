# RUNBOOK — Finish C2: Live Session Orchestrator + Dry-Run (Mock Broker)

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, deterministisch, evidence‑first, **snapshot‑only**, **DRY‑RUN only**, **NO‑LIVE default**

> **Stop Rules (C2)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders.  
> - **DRY‑RUN only**: nur Mock Broker.  
> - **Jeder Pfad, der `enabled=True` ohne expliziten Test‑Override braucht ⇒ STOP.**  
> - **Jede echte Broker‑Order ⇒ STOP.**  
> - **Keine Secrets** in Logs/Env/Docs.  
> - **Snapshot‑only**: keine Watch‑Loops.  
> - Scope‑Drift ⇒ STOP und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

Orchestrator‑Skeleton als State Machine, die die „Live Session“ als **kontrollierten Prozess** modelliert (DRY‑RUN, mock‑only):

- Startup Checks (config gating, allowlist present, preflight invariants)
- Run‑Loop als **bounded steps** (für Tests); keine unbounded loops
- Shutdown / cancel / safe stop (in dry‑run)
- Audit Events (append‑only, redacted)

---

## 1) Entry Point

### Voraussetzungen
- C1 Adapter skeleton + mock broker stable.

---

## 2) Exit Point (DoD)

- LiveSessionOrchestrator (state machine) existiert:
  - startup checks (config/allowlist/enabled flag **must be OFF in tests**)
  - runtime checks (health + invariants)
  - shutdown path (graceful)
  - audit log events (in-memory/file stub, no secrets)
- Dry-run E2E test: orchestrator + mock broker + deterministic fills.

---

## 3) Design‑Leitplanken (minimal, no‑watch)

### 3.1 Zustände (Beispiel)
- `INIT` → `PREFLIGHT_OK` → `DRYRUN_ACTIVE` → `STOPPING` → `STOPPED`
- Fehlerzustände: `PREFLIGHT_FAILED`, `ERROR_REQUIRES_OPERATOR`

### 3.2 Startup Checks (Snapshot‑Checks)
- enabled flag **muss OFF bleiben** (nur expliziter Test‑Override darf das ändern)
- allowlist vorhanden und nicht leer (rein syntaktisch; keine echten Broker IDs)
- BrokerAdapter = Mock Broker (deterministisch)
- Audit sink aktiv (in-memory/file stub; redacted)

### 3.3 „No Watch“ Umsetzung
- Orchestrator bietet `step()` oder `run_n_steps(n)` für Tests
- Operator‑Runbook nutzt nur **einmalige** Kommandos (Snapshot)

---

## 4) Snapshot Checks (no watch)

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git status -sb
git diff --stat

pytest -q
python -m ruff check .
python -m ruff format --check .
```

---

## 5) Proposed File Map

**Code (proposed paths):**
- `src/execution/live/orchestrator.py`
- `src/execution/live/state.py`
- `src/execution/live/audit.py`

**Tests (proposed paths):**
- `tests/execution/live/test_orchestrator_dryrun.py`

**Evidence (operator-created, optional):**
- `docs/ops/evidence/EV-YYYYMMDD-FINISH_C2-ORCH-DRYRUN-PASS.md`

---

## 7) Next PR Slice

**PR‑C3:** Reconciler + Safety Rails + Failure‑Matrix Tests (timeouts/dupes/partial fills).  
Siehe `RUNBOOK_FINISH_C3_RECONCILER_SAFETY_RAILS.md`.
