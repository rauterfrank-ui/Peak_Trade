# RUNBOOK — Finish C1: Broker Adapter Skeleton + Unit Tests (Mocked)

**Datum:** 2026-01-18  
**Status:** DRAFT  
**Modus:** governance‑safe, deterministisch, evidence‑first, **snapshot‑only**, **NO‑LIVE default**

> **Stop Rules (C1)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders.  
> - **Jede echte Netzwerk‑Integration ⇒ STOP.**  
> - **Jede Speicherung/Logging von Credentials ⇒ STOP.**  
> - 100% mocked tests: **no network**.  
> - **Snapshot‑only**: keine Watch‑Loops.  
> - Scope‑Drift ⇒ STOP und ORCHESTRATOR re‑scoped.

---

## 0) Zweck

Ein minimaler, testbarer Broker‑Abstraktionslayer, der spätere Live‑Ops **möglich macht**, aber in C1 **nur** als **Fake/Mock** betrieben wird:

- BrokerAdapter Interface + Skeleton
- deterministischer Mock Broker
- idempotency + retries/backoff + rate‑limit resilience (Design **und** Tests)

---

## 1) Entry Point

### Voraussetzungen
- C0 Contract ist **merged** oder mindestens finalisiert („frozen“).
- Scope: **Adapter skeleton + Unit Tests + Mocks** (keine Runtime/Live‑Änderungen).

---

## 2) Exit Point (DoD)

- BrokerAdapter Interface + Skeleton vorhanden:
  - `place_order`, `cancel_order`, `query_order`, `list_open_orders`
  - fills ingest (**mocked** event stream)
  - idempotency key handling (Design + Tests)
  - retries/backoff policy (Design + Tests)
  - rate‑limit resilience (Design + Tests)
- 100% mocked tests: **keine** realen HTTP calls / keine externe IO.

---

## 3) Adapter Contract (minimal, C1)

> **Hinweis:** C1 definiert den kleinsten Contract, der C2/C3 ermöglicht, ohne Live zu aktivieren.

### 3.1 Commands
- `place_order(request) -> broker_order_id`
- `cancel_order(broker_order_id) -> status`
- `query_order(broker_order_id) -> order_snapshot`
- `list_open_orders() -> list[order_snapshot]`

### 3.2 Events (Fills / Execution Reports)
- fills ingest via **mocked** event stream (z.B. `iter_fills(since_cursor)`)
- idempotency key handling ist explizit (z.B. `idempotency_key` oder `client_order_id`)

### 3.3 Error Model
- transient (retryable): timeouts, temporary unavailable
- permanent (non‑retryable): invalid params, rejected
- bounded retries + backoff (deterministisch in tests; z.B. injected clock)
- rate limit responses werden als transient behandelt (bounded)

---

## 4) Snapshot Checklist (C1)

- [ ] `git status -sb` (Scope korrekt? keine uncommitted changes empfohlen)
- [ ] `pytest -q` (snapshot)
- [ ] `python -m ruff check .` (snapshot)
- [ ] `python -m ruff format --check .` (snapshot)
- [ ] Diff‑Review: keine Secrets; keine network integration; kein live unlock

---

## 5) Proposed File Map (indicative)

**Code (proposed paths):**
- ``src&#47;execution&#47;broker&#47;base.py`` (interfaces, dataclasses)
- ``src&#47;execution&#47;broker&#47;mock_broker.py`` (deterministic mock)
- ``src&#47;execution&#47;broker&#47;idempotency.py``
- ``src&#47;execution&#47;broker&#47;retry.py``

**Tests (proposed paths):**
- ``tests&#47;execution&#47;broker&#47;test_adapter_contract.py``
- ``tests&#47;execution&#47;broker&#47;test_idempotency.py``
- ``tests&#47;execution&#47;broker&#47;test_retry_policy.py``

**Evidence (operator-created, optional):**
- ``docs&#47;ops&#47;evidence&#47;EV-YYYYMMDD-FINISH_C1-ADAPTER-PASS.md``

---

## 6) Operator Pre‑Flight (Terminal)

> Ctrl‑C wenn `>` / `dquote>` / `heredoc>`.

```bash
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
pwd && git rev-parse --show-toplevel && git status -sb
```

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

- Adapter skeleton + tests (mocked)
- Evidence Snapshot (siehe `TEMPLATES_FINISH_C_EVIDENCE.md`)

---

## 9) Next PR Slice

**PR‑C2:** Live Session Orchestrator (Dry‑Run) mit FakeBroker + Audit Log.  
Siehe `RUNBOOK_FINISH_C2_LIVE_SESSION_ORCHESTRATOR_DRYRUN.md`.
