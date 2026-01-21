# Peak_Trade — Finish Level C (Live‑Broker‑Ops Track) — MASTER RUNBOOK

**Datum:** 2026-01-18  
**Status:** DRAFT (docs-only, governance-first)  
**Modus:** governance‑safe, deterministisch, evidence‑first, **NO‑LIVE default**  
**Kontext:** Cursor Multi‑Agent (ORCHESTRATOR + 5–7 Agents parallel)

> **Stop Rules (global, NON‑NEGOTIABLE)**  
> - **Default NO‑LIVE**: keine realen Broker‑Calls, keine Orders, keine Accounts.  
> - **Keine Secrets** (Keys, Tokens, Credentials) in Logs, Code, Docs, Screenshots.  
> - **Snapshot‑only Checks**: keine Watch‑Loops als Default (nur explizit erlaubt).  
> - **Scope‑Drift ⇒ STOP**: ORCHESTRATOR stoppt und fordert Re‑Scoping.  
> - Jede Phase endet mit **Status‑Snapshot + Artefakte‑Liste + Next PR Slice**.

---

## 0) Ziel & Nicht‑Ziele

### Ziel
Finish Level C liefert einen optionalen „live‑nahen“ Track (Broker Adapter + Live Ops) unter strikter Governance:

- Broker Adapter (idempotent, rate‑limited, resilient; **Mock‑first**)
- Live Session Orchestrator (State Machine + Audit Log; **Dry‑Run** mit Mock‑Broker)
- Reconciler + Safety Rails (Fehlerfälle, Recovery, invariants; **tests zuerst**)
- Observability + Operator UX (Health, Order‑Lifecycle‑Metriken, Operator‑Dry‑Run)
- Controlled Readiness (Checklist + Evidence + Incident Pack) — **ohne Live‑Enablement**

### Nicht‑Ziele
- Kein Live‑Trading, keine reale Broker‑Integration, keine echten Endpunkte/Accounts.  
- Keine „Enable live“ Anleitung (nur Governance‑Locks/Mechanik, die default *off* ist).  
- Keine Dauerschleifen/Auto‑Polling als Runbook‑Standard.

---

## 1) Einstiegspunkte (C‑E0 … C‑E3)
- **C‑E0:** Nur Backtest/Paper; keine Broker‑Abstraktion.  
- **C‑E1:** ExecutionPipeline existiert; Broker fehlt.  
- **C‑E2:** Broker‑Adapter existiert; Ops/Orchestrator fehlt.  
- **C‑E3:** Governance/Safety/Tests/Docs fehlen.

---

## 2) Runbooks (Phase‑Pointer)

- [C0 — Governance Contract](RUNBOOK_FINISH_C0_GOVERNANCE_CONTRACT.md)
- [C1 — Broker Adapter Skeleton](RUNBOOK_FINISH_C1_BROKER_ADAPTER_SKELETON.md)
- [C2 — Orchestrator Dry‑Run](RUNBOOK_FINISH_C2_LIVE_SESSION_ORCHESTRATOR_DRYRUN.md)
- [C3 — Reconciler + Safety Rails](RUNBOOK_FINISH_C3_RECONCILER_SAFETY_RAILS.md)
- [C4 — Observability + Operator Dry‑Run](RUNBOOK_FINISH_C4_OBSERVABILITY_OPERATOR_DRYRUN.md)
- [C5 — Controlled Readiness](RUNBOOK_FINISH_C5_CONTROLLED_READINESS.md)
- [D1 — Artifacts Repro](RUNBOOK_D1_ARTIFACTS_REPRO.md)
  - Zweck: standardisierte Run‑Artefakte + Repro‑Pack (Manifest/Snapshots)
  - Entry: Runner/Backtests existieren, Outputs sind inkonsistent/unversioniert
  - Output/DoD: `run_manifest.json`, `config_snapshot.json`, `metrics.json`, `equity.csv`, `trades.csv` + determinism PASS
- [D4 — Ops/Governance Polish](RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md)
  - Zweck: stabile Docs‑Gates, konsistente Templates, Merge‑Log/Evidence Hygiene
  - Entry: Gate‑Incidents durch Links/Templates/Merge‑Log Drift
  - Output/DoD: docs gates PASS + operator‑lesbarer Gate‑Snapshot + referenzierte Release‑Checklist
- [Templates — Evidence](TEMPLATES_FINISH_C_EVIDENCE.md)
- [Templates — Incident Pack](TEMPLATES_FINISH_C_INCIDENT_PACK.md)

---

## 3) Phasen (C0–C5) — Entry/Exit

- **C0 — Governance Contract & Threat Model**
  - Entry: docs‑only contract/threat model scope
  - Exit: contract frozen (NO‑LIVE default, allowlist + enable‑flag, no‑secrets, snapshot‑only, audit‑log design)
- **C1 — Broker Adapter Skeleton + Unit Tests (mocked)**
  - Entry: contract frozen
  - Exit: adapter + fake broker + unit tests (idempotency/retry) grün; no network
- **C2 — Live Session Orchestrator + Dry‑Run (mock broker)**
  - Entry: C1 grün
  - Exit: state machine + audit events + dry‑run integration tests grün; bounded steps
- **C3 — Reconciler & Safety Rails + Failure Tests**
  - Entry: C2 grün
  - Exit: reconciliation invariants + tripwires + failure matrix tests grün
- **C4 — Observability + Operator UX + Dry‑Run E2E**
  - Entry: C3 grün
  - Exit: health + order lifecycle metrics + operator dry‑run snapshots (watch‑only)
- **C5 — Controlled Readiness + Checklist + Evidence Template**
  - Entry: C4 grün
  - Exit: readiness checklist + evidence/incident templates final; **Live bleibt opt‑in**

---

## 4) Output‑Artefakte (immer)

- **Docs**: Runbooks + Contracts + (optional) Failure Maps
- **Tests**: Unit + Mocked Integration + Failure Szenarios
- **Evidence**: Snapshot‑Datei(en) gemäß Template
- **CI**: Snapshot der relevanten Checks (**keine Watch**)

---

## 5) Task Map (minimal, governance‑safe)

> **Hinweis:** Dies ist eine Plan‑Landkarte. Die konkreten Code‑Änderungen passieren erst ab PR‑C1.

- **PR‑C0**
  - Scope: docs‑only (Contracts/Threat Model/Runbooks/Templates)
  - Stop‑Rules + Snapshot‑Commands pro Phase
  - „NO‑LIVE default“ + allowlist + enable‑flag Gating als wiederkehrendes Muster (Design‑Ebene)

- **PR‑C1**
  - Pfade (proposed):
    - ``src&#47;execution&#47;broker&#47;adapter.py`` (Interface/Protocol)
    - ``src&#47;execution&#47;broker&#47;fake_broker.py`` (FakeBroker, deterministisch)
    - ``src&#47;execution&#47;broker&#47;errors.py``
    - ``tests&#47;execution&#47;broker&#47;test_adapter_contract.py``
    - ``tests&#47;execution&#47;broker&#47;test_idempotency.py``

- **PR‑C2**
  - Pfade (proposed):
    - ``src&#47;live&#47;orchestrator&#47;state.py`` (State Machine)
    - ``src&#47;live&#47;orchestrator&#47;orchestrator.py``
    - ``src&#47;live&#47;orchestrator&#47;audit.py``
    - ``tests&#47;live&#47;orchestrator&#47;test_dryrun_with_fake_broker.py``

- **PR‑C3**
  - Pfade (proposed):
    - ``src&#47;live&#47;reconcile&#47;reconciler.py``
    - ``src&#47;live&#47;safety&#47;rails.py``
    - ``tests&#47;live&#47;reconcile&#47;test_reconciler_failure_matrix.py``

- **PR‑C4**
  - Pfade (proposed):
    - ``src&#47;observability&#47;metrics_orders.py`` (order lifecycle metrics)
    - ``src&#47;webui&#47;...`` (watch‑only views, falls vorhanden)
    - ``tests&#47;observability&#47;test_metrics_smoke.py``

- **PR‑C5**
  - Pfade (proposed):
    - ``docs&#47;ops&#47;runbooks&#47;finish_c&#47;*`` (finalize)
    - ``docs&#47;ops&#47;evidence&#47;EV-YYYYMMDD-FINISH_C5-READINESS.md`` (operator-created)

---

## 6) Snapshot‑Only Standardkommandos (Operator, global)

> **Kein Watch.** Alle Commands sind einmalige Snapshots.

```bash
# Pre-flight
cd /Users/frnkhrz/Peak_Trade || cd "$HOME/Peak_Trade"
git rev-parse --show-toplevel
git status -sb

# Diff snapshots
git diff --stat
git diff

# Tests/Lint (snapshot-only)
pytest -q
python -m ruff check .
python -m ruff format --check .

# Docs gates (snapshot-only, changed scope)
./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main

# Narrow check (optional, if docs gates are too heavy)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
./scripts/ops/verify_docs_reference_targets_trend.sh --changed --base origin/main

# Docs/Ops hygiene (nur wenn relevant; snapshot-only)
python scripts/ops/check_merge_log_hygiene.py

# Optional: repo-specific docs token/reference scripts (nur falls vorhanden)
# python scripts/ops/check_docs_token_policy.py
# python scripts/ops/check_docs_reference_targets.py
```

---

## 7) PR‑Slicing

Siehe Abschnitt „PR Plan“ in den Phasen‑Runbooks (C0–C5).

---

## 8) Risk Notes (Master)

- **Haupt‑Risiko:** „Docs/Code driftet in Live‑Enablement“ (unbeabsichtigte Unlocks).  
  **Kontrolle:** Default NO‑LIVE, allowlist + enable‑flag, Tests/Mocks only, explizite Stop‑Rules.
- **Secrets‑Leak‑Risiko:** in Debug‑Logs, CI output, docs examples.  
  **Kontrolle:** keine Credential‑Beispiele; redaction; „no secrets“ als DoD‑Gate.
- **Watch‑Loop‑Risiko:** Polling/Auto‑Refresh in Ops‑Tools.  
  **Kontrolle:** Snapshot‑only Runbooks; Loops nur mit späterer expliziter Freigabe.
