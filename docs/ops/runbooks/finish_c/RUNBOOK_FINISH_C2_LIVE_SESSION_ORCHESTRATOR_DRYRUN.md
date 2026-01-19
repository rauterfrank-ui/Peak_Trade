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
- ``src&#47;execution&#47;live&#47;orchestrator.py``
- ``src&#47;execution&#47;live&#47;state.py``
- ``src&#47;execution&#47;live&#47;audit.py``

**Tests (proposed paths):**
- ``tests&#47;execution&#47;live&#47;test_orchestrator_dryrun.py``

**Evidence (operator-created, optional):**
- ``docs&#47;ops&#47;evidence&#47;EV-YYYYMMDD-FINISH_C2-ORCH-DRYRUN-PASS.md``

---

## 6) Contract: C2 Dryrun Artifacts (snapshot-only)

Der C2-Orchestrator produziert **strukturierte Artefakte** in deterministischer Reihenfolge.  
Wichtig: Artefakte sind **operator-created** und dürfen **nicht committed** werden.

### 6.1 Artefakt-Typen

- **Events (JSONL)**: ``out&#47;finish_c&#47;c2&#47;<run_id>&#47;events.jsonl``
  - Pro Zeile ein Event (Schema: `C2_DRYRUN_V1`)
  - Felder: `event_id`, `run_id`, `strategy_id`, `event_type`, `ts_sim`, `ts_utc`, `payload`
  - Determinismus: `ts_sim` ist monotonic (SimClock), `event_id` ist `stable_id(...)` über kanonische Felder

- **State Snapshots (JSONL)**: ``out&#47;finish_c&#47;c2&#47;<run_id>&#47;state_snapshots.jsonl``
  - Pro Zeile ein `SessionStateSnapshot` (Status-Transitions)
  - Status: `INIT` → `RUNNING` → `COMPLETED` (oder `REJECTED` / `FAILED`)

- **Metrics Snapshot (JSON)**: ``out&#47;finish_c&#47;c2&#47;<run_id>&#47;metrics.json``
  - Ein Snapshot-Objekt (Schema: `C2_DRYRUN_METRICS_V1`)
  - Felder u.a.: `events_emitted`, `audit_events`, `sink_retries`, `status`

### 6.2 Audit Events (append-only)

- **Audit (JSONL)**: ``out&#47;finish_c&#47;c2&#47;<run_id>&#47;audit.jsonl``
  - Determinismus: `seq` strikt monoton, `ts` kommt ausschließlich aus injected clock
  - Typische Codes: `C2_DRYRUN_START`, `C2_REJECT_*`, `C2_SINK_WRITE_RETRY`, `C2_SINK_WRITE_FAILED`, `C2_DRYRUN_STOP`

---

## 7) Operator Invocation (snapshot-only)

Beispiel: einmaliger Dryrun, schreibt Artefakte nach `out/finish_c/...` (operator-created).

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"

python - <<'PY'
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.execution.live.orchestrator import DryrunConfig, LiveSessionOrchestrator

class FixedClock:
    def __init__(self, dt):
        self._dt = dt
    def now(self):
        return self._dt

run_id = "run_demo_001"
out_dir = Path("out/finish_c/c2") / run_id
out_dir.mkdir(parents=True, exist_ok=True)

events_path = out_dir / "events.jsonl"
state_path = out_dir / "state_snapshots.jsonl"
metrics_path = out_dir / "metrics.json"
audit_path = out_dir / "audit.jsonl"

cfg = DryrunConfig(strategy_id="strat_demo", run_id=run_id, seed=123, clock_mode="fixed", max_sink_retries=0)
orch = LiveSessionOrchestrator()

clock = FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
with events_path.open("w") as ev_f, state_path.open("w") as st_f, metrics_path.open("w") as m_f, audit_path.open("w") as a_f:
    res = orch.run_dryrun(cfg, clock=clock, event_sink=ev_f, state_sink=st_f, metrics_sink=m_f, audit_sink=a_f)

print(json.dumps({"accepted": res.accepted, "status": res.status.value, "run_id": res.run_id}, sort_keys=True))
PY
```

## 8) Next PR Slice

**PR‑C3:** Reconciler + Safety Rails + Failure‑Matrix Tests (timeouts/dupes/partial fills).  
Siehe `RUNBOOK_FINISH_C3_RECONCILER_SAFETY_RAILS.md`.
