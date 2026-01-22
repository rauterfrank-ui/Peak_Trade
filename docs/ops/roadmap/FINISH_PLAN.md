---
title: "Finish Plan (MVP→v1.0) — Repo Roadmap + DoD Checklists"
status: DRAFT
scope: docs-first (NO-LIVE)
last_updated: 2026-01-18
---

# Finish Plan (MVP→v1.0) — Repo Roadmap + DoD Checklists

**Ziel:** Eine konkrete “Finish”-Definition (MVP/Beta/v1.0) mit Workstreams, DoD-Checklisten, PR-Slicing-Plan und operator-freundlichen Verifikationsschritten.  
**Constraint:** Diese Datei ist **docs-only**. Sie definiert Arbeit und Nachweise — sie führt nichts live aus.

---

## Rollen (Multi-Agent Chat Mapping)

- **ORCHESTRATOR**: Struktur, Sequenz, PR-Slicing, verhindert Scope Creep
- **SCOPE_KEEPER**: Diese Pass-Phase ist **docs-only** (keine Runtime-Änderungen)
- **DOCS_SCRIBE**: schreibt/editiert die Markdown-Artefakte
- **RISK_OFFICER**: Stop-Rules, Guardrails, Risiko-Notizen (NO-LIVE)
- **QA/GATES**: Token-Policy + Reference-Targets + Diff-Guard (kein Broken-Link Debt)

---

## Stop Rules (NON-NEGOTIABLE)

- **NO-LIVE**: Kein Live-Trading, keine Live-Order-Platzierung, keine Creds/Secrets.
- **Snapshot-only Verify**: Verifikation ist **einmalig**, reproduzierbar, ohne Watch/Polling-Loops.
- **Evidence-first**: Jede “DONE”-Aussage braucht ein **prüfbares** Resultat (Command + Output/Exit-Code + Artefaktpfad).
- **No “missing file” references**: Keine Links/Targets auf nicht-existente Dateien. Wenn etwas “Gap” ist, dann als **Konzept** beschreiben, nicht als Dateipfad.
- **Token-Policy safe**:
  - Inline-Code-Pfade mit Slashes nur als **encoded** Form verwenden (z.B. `docs&#47;ops&#47;...`), wenn illustrativ.
  - Commands/real paths bevorzugt in **Code-Fences** oder als **existente Links**.

---

## Finish Level A — Level A (MVP)

### Definition
**MVP = Offline Research & Backtest Pipeline ist reproduzierbar und auditierbar** (keine Execution, keine Broker-Integration notwendig).

**Companion Runbook:** [RUNBOOK_FINISH_A_MVP.md](../runbooks/RUNBOOK_FINISH_A_MVP.md) (Backtest → Artifacts → Report → Watch‑Only Dashboard, snapshot-only, NO‑LIVE)

### DoD Checklist (MVP)

#### Governance / Safety (NO-LIVE)
- [ ] **NO-LIVE posture dokumentiert** (klar: research/backtest only).
- [ ] **Kill-Switch posture unverändert** (keine Unlocks; keine “break-glass” Änderungen).
- [ ] **Docs Gates** lokal reproduzierbar (Snapshot helper PASS).

#### Data / Inputs
- [ ] **Deterministische Datenquelle** für Backtests definiert (lokal, offline; keine “magischen” externen Dependencies).
- [ ] **Config/Defaults** dokumentiert (welche Parameter minimal erforderlich sind).

#### Backtest / Research
- [ ] **Einzel-Backtest** läuft durch (Exit-Code 0) und erzeugt ein Resultat (Stats/Report/Artefakt).
- [ ] **Portfolio-Backtest** läuft durch (Exit-Code 0) und erzeugt ein Resultat.
- [ ] **Keine Side-Effects** außerhalb des Repos (keine Writes nach `~`, keine Secrets).

#### Reporting / Artifacts
- [ ] **Outputs sind auffindbar** (ein klarer Output-Ordner oder Console Summary).
- [ ] **Konventionen dokumentiert**: “Wo liegen Reports? Welche Namensschemata?”

#### QA / CI Readiness
- [ ] **Targeted Tests** definiert und lokal ausführbar (mindestens 1 “smoke” + 1 “behavior” Test).
- [ ] **Operator Evidence Block** ist copy-paste-ready (siehe unten).

### Operator Quickstart (MVP) — Local Verify (Snapshot-only)

1) **Docs gates (changed scope)**:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

2) **Minimaler Backtest (offline)**:

```bash
python scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR --bars 100 -v
```

3) **Minimaler Portfolio-Backtest (offline)**:

```bash
python scripts/run_portfolio_backtest.py
```

4) **Minimaler Test-Snapshot** (falls du nur schnell einen “green signal” willst):

```bash
uv run pytest -q
```

### Operator Evidence Block (MVP)

```text
Finish Level A (MVP) — Evidence (Snapshot-only)
NO-LIVE: YES
Docs Gates Snapshot: bash scripts/ops/pt_docs_gates_snapshot.sh --changed → <PASS/FAIL>
Backtest Smoke: python scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR --bars 100 -v → exit=<0/!0>
Portfolio Smoke: python scripts/run_portfolio_backtest.py → exit=<0/!0>
Tests: uv run pytest -q → <summary>
Notes: <max 2 lines>
Risk: LOW
```

---

## Finish Level B — Level B (Beta): ExecutionPipeline + Ledger

### Definition
**Beta = ExecutionPipeline (paper/sim) + Ledger sind konsistent, deterministisch und testbar** — aber weiterhin **NO-LIVE**.

### NEXT_PHASE (ExecutionPipeline) — Slice 2: Ledger/Accounting + Deterministic PnL
- **Ziel**: Fill/Fee Events → Double‑Entry Journal + Balances → deterministische Positionen (WAC) + realized/unrealized PnL + Equity (snapshot/export).
- **Determinismus**: keine Floats, explizite Quantisierung, stabile Sortierung/JSON‑Exports, `ts_utc` ignorieren (Input-only).
- **Runbook**: [RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL.md](../runbooks/RUNBOOK_EXECUTION_SLICE2_LEDGER_PNL.md)

### DoD Checklist (Beta)

#### ExecutionPipeline (paper/sim, deterministisch)
- [ ] **Pipeline Contract** dokumentiert: Inputs → Events → Orders → Fills → Ledger.
- [ ] **Idempotenz**: Re-run mit gleichem Seed/Input erzeugt gleiche Ledger-Resultate (oder dokumentierte deterministische Abweichungen).
- [ ] **Reject/Fail-safe**: Rejects erzeugen **keine** falschen Ledger-Einträge.
- [ ] **Paper Broker** Tests vorhanden und grün.

#### Ledger (Konsistenz & Reconciliation)
- [ ] **Event→Ledger Mapping** getestet (Fill → Trade/Position Update).
- [ ] **Trend/Seed Ledger** kann aus Seed reproduziert werden (Replay-Fähigkeit).
- [ ] **Reconciliation Rules** dokumentiert (z.B. “what is source of truth?”).

#### QA / Evidence
- [ ] **Targeted Unit Tests** existieren (mind. 3: pipeline reject, event-to-ledger, trend ledger).
- [ ] **Operator Verify** ist snapshot-only und ohne live side-effects.

### Operator Quickstart (Beta) — Local Verify (Snapshot-only)

1) **Docs gates (changed scope)**:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

2) **Targeted tests (ExecutionPipeline + Ledger)**:

```bash
uv run pytest -q tests/execution/test_wp0d_reject_produces_no_ledger_entry.py
uv run pytest -q tests/execution/test_wp0d_event_to_ledger_fill_maps_to_trade.py
uv run pytest -q tests/ai_orchestration/test_trend_ledger_from_seed.py
```

3) **Optional: Pipeline demo (offline/paper)**:

```bash
python scripts/demo_order_pipeline_backtest.py --help
```

### Operator Evidence Block (Beta)

```text
Finish Level B (Beta) — Evidence (Snapshot-only)
NO-LIVE: YES (paper/sim only)
Docs Gates Snapshot: bash scripts/ops/pt_docs_gates_snapshot.sh --changed → <PASS/FAIL>
Tests (pipeline/ledger):
 - uv run pytest -q tests/execution/test_wp0d_reject_produces_no_ledger_entry.py → <PASS/FAIL>
 - uv run pytest -q tests/execution/test_wp0d_event_to_ledger_fill_maps_to_trade.py → <PASS/FAIL>
 - uv run pytest -q tests/ai_orchestration/test_trend_ledger_from_seed.py → <PASS/FAIL>
Notes: <max 2 lines>
Risk: MED (execution-adjacent, still NO-LIVE)
```

---

## Finish Level C — Level C (v1.0): Broker + Live-Ops (Governed)

### Definition
**v1.0 = Broker Integration + Live-Ops** sind vollständig dokumentiert, abgesichert und operationalisiert — inklusive “break-glass” Verfahren — aber **nur** unter Governance-Freigabe.

> Hinweis: In dieser Finish-Plan-Doku gilt weiterhin **NO-LIVE**. v1.0-DoD beschreibt, was für Live-Betrieb *existieren muss*, nicht was hier ausgeführt wird.

### DoD Checklist (v1.0)

#### Broker / Execution (Governed)
- [ ] **Broker Interface** klar (Order types, time-in-force, error taxonomy).
- [ ] **Paper/Testnet Coverage**: Tests und Runbooks vorhanden (mindestens paper broker).
- [ ] **Rate Limits / Retries** dokumentiert (inkl. Backoff, idempotency keys sofern vorhanden).
- [ ] **KILL SWITCH**: Drill/Runbook existiert und ist reproduzierbar (snapshot).

#### Live-Ops (Runbooks, Observability, Incident Handling)
- [ ] **Runbooks**: Start/Stop, Pre-Flight, Incident, Post-Mortem, Rollback, DR.
- [ ] **Observability**: Health signals, status reports, alerting hooks (mind. dokumentiert).
- [ ] **Audit Trail**: Evidence Index / Merge Logs / Status Reports integriert.
- [ ] **Permission Model** dokumentiert (wer darf was, wann, mit welcher Evidenz).

#### Governance Gates
- [ ] **No unlock without evidence**: Jede Live-Änderung ist ein eigener PR-Slice mit Risiko-Note + Tests + Operator-Verify.
- [ ] **Docs Gates** bleiben PASS (Token Policy, Reference Targets, Diff Guard).

### Operator Quickstart (v1.0) — Local Verify (Snapshot-only)

1) **Docs gates (changed scope)**:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

2) **Paper broker test (snapshot)**:

```bash
uv run pytest -q tests/execution/test_paper_broker.py
```

3) **Kill switch drill (snapshot)**:

```bash
uv run python scripts/ops/drill_kill_switch.py --help
```

### Operator Evidence Block (v1.0)

```text
Finish Level C (v1.0) — Evidence (Snapshot-only)
NO-LIVE: YES (this verify is local-only)
Docs Gates Snapshot: bash scripts/ops/pt_docs_gates_snapshot.sh --changed → <PASS/FAIL>
Paper Broker Test: uv run pytest -q tests/execution/test_paper_broker.py → <PASS/FAIL>
Kill Switch Drill: uv run python scripts/ops/drill_kill_switch.py --help → <exit>
Notes: <max 2 lines>
Risk: HIGH (broker/live-ops domain; execution-adjacent)
```

---

## Workstreams (1..6) — Inputs / Outputs / Contracts / Tests

### 1) Governance & Safety (NO-LIVE posture)
- **Inputs**: Governance docs, safety policies, gate runbooks, operator workflows
- **Outputs**: “NO-LIVE by default” posture, explicit approval boundaries, evidence templates
- **Contracts**:
  - No live execution without explicit operator approval + documented evidence
  - Snapshot-only verification (no watch loops)
  - Token-policy-safe docs (illustrative paths encoded)
- **Tests**:
  - Docs gates snapshot PASS (Token Policy, Reference Targets, Diff Guard)
  - Governance lock assertions (where applicable) are unchanged

### 2) Data & Market Data Layer (offline-first)
- **Inputs**: Historical OHLCV / datasets, config files, sampling policy
- **Outputs**: Deterministische datasets/fixtures, documented default configs
- **Contracts**:
  - Reproducibility: same inputs → same outputs
  - No hidden remote dependencies for MVP/Beta verification
- **Tests**:
  - Backtest smoke passes with minimal bars
  - Data validation checks (if present) are exercised in CI

### 3) Strategy & Research Surface
- **Inputs**: Strategy definitions, research configs, sweep presets
- **Outputs**: Reproducible backtest results, reports, experiment artifacts
- **Contracts**:
  - Strategy runs must be offline-safe (no broker/network dependency)
  - Output locations are documented and stable
- **Tests**:
  - Targeted strategy/unit tests (at least 1 “representative” strategy path)
  - Golden-report sanity checks (if available)

### 4) ExecutionPipeline (paper/sim only until governed)
- **Inputs**: Signals, portfolio state, execution config
- **Outputs**: Orders (planned), fills (simulated/paper), events stream
- **Contracts**:
  - Idempotent event processing and deterministic replays where required
  - Rejects don’t create ledger side-effects
- **Tests**:
  - `tests/execution/test_wp0d_reject_produces_no_ledger_entry.py`
  - `tests/execution/test_paper_broker.py` (paper)

### 5) Ledger & Reporting (audit trail)
- **Inputs**: Events/fills, positions, pricing snapshots
- **Outputs**: Ledger entries, trade logs, status reports
- **Contracts**:
  - Clear mapping: event→ledger semantics
  - Reconciliation rules documented
- **Tests**:
  - `tests/execution/test_wp0d_event_to_ledger_fill_maps_to_trade.py`
  - `tests/ai_orchestration/test_trend_ledger_from_seed.py`

### 6) Ops / CI / Docs Gates & Operator UX
- **Inputs**: PR slices, docs updates, runbooks, evidence artifacts
- **Outputs**: Merge-ready PRs with evidence blocks, stable navigation/frontdoors
- **Contracts**:
  - Docs-only PRs keep gates PASS
  - Reference targets are resolvable; no “missing file” references
- **Tests**:
  - Snapshot helper: `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`
  - Optional: fullscan/trend as separate evidence step when needed

---

## PR Slicing Plan (6–12 PRs)

> Prinzip: **kleine, auditierbare PRs**. Jede PR liefert “Evidence → Merge Log → Chain” fähige Verifikation. Keine PR mischt “execution-adjacent” risk mit reiner docs hygiene, außer explizit begründet.

### PR 1 — Finish Plan docs (docs-only)
- **Scope**: Finish Plan + Frontdoor link
- **Files**:
  - `docs&#47;ops&#47;roadmap&#47;FINISH_PLAN.md` (new)
  - `docs&#47;WORKFLOW_FRONTDOOR.md` (1 link entry)
- **Tests**:
  - `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`
- **Gates**:
  - Docs Token Policy Gate
  - Docs Reference Targets Gate
  - Docs Diff Guard Policy Gate
- **Operator verify**:
  - Evidence Block aus `RUNBOOK_LOCAL_DOCS_GATES_SNAPSHOT_CHANGED_SCOPE_CURSOR_MULTI_AGENT.md` verwenden

### PR 2 — MVP verify docs consolidation (docs-only)
- **Scope**: MVP verify commands in one “operator page” (no runtime changes)
- **Files (docs)**:
  - new doc under `docs/ops/roadmap/` (MVP verify page)
  - update cross-links (frontdoor/runbooks if needed)
- **Tests**:
  - docs gates snapshot (changed scope)
- **Gates**: docs gates (3)
- **Operator verify**:
  - Run the MVP quickstart commands and paste evidence block

### PR 3 — Beta execution/ledger test hardening (code + tests)
- **Scope**: Strengthen deterministic behavior and test coverage around pipeline↔ledger mapping
- **Files (patterns)**: src execution/ledger modules + tests execution/ai_orchestration
- **Tests**:
  - targeted pytest: reject/no-ledger, event-to-ledger, trend-ledger-from-seed
- **Gates**:
  - lint + pytest matrix (per repo CI)
  - governance-safe (no live unlock)
- **Operator verify**:
  - local pytest targeted + evidence block

### PR 4 — ExecutionPipeline contract docs + runbook (docs-first)
- **Scope**: Define “ExecutionPipeline contract” page + operator troubleshooting
- **Files (docs)**: new docs under ops/runbooks or ops/roadmap + cross-links
- **Tests/Gates**: docs gates snapshot
- **Operator verify**:
  - confirm contract aligns with current tests; no missing reference targets

### PR 5 — v1.0 broker readiness: paper/testnet separation (code + docs)
- **Scope**: Ensure broker layer is clearly separated (paper/testnet/live), with documented guardrails
- **Files (patterns)**: src execution/broker + docs governance/safety + tests execution
- **Tests**:
  - paper broker tests
  - kill switch drill test path (if covered)
- **Gates**:
  - all CI required checks
  - explicit risk note required
- **Operator verify**:
  - run paper broker test + kill switch drill (snapshot) and paste evidence

### PR 6 — Live-Ops runbook pack (docs-only)
- **Scope**: Live-Ops procedures (start/stop, incident, rollback) — documentation only, NO unlocks
- **Files (docs)**: ops/runbooks + cross-links to safety policy
- **Tests/Gates**: docs gates snapshot
- **Operator verify**:
  - run docs gates; validate link graph (reference targets PASS)

### PR 7 — Observability/status report hardening (code + docs)
- **Scope**: Make status reports reliable and operator-friendly (still snapshot-only)
- **Files (patterns)**: scripts for status reporting + docs guidance
- **Tests**:
  - targeted tests for report generation (if present) + smoke runs
- **Gates**: CI checks + docs gates
- **Operator verify**:
  - generate daily/weekly status report (local) and store output path as evidence

### PR 8 — Release checklist + “Go/No-Go” rubric (docs-only)
- **Scope**: One page “Go/No-Go” rubric aligned to Finish Level C
- **Files (docs)**: ops/release/runbooks + cross-links from frontdoor
- **Tests/Gates**: docs gates snapshot
- **Operator verify**:
  - evidence template ready for each release candidate

---

## Notes für QA/GATES (praktisch)

- **Run changed-scope docs gates**:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

- **Wenn Token Policy failt**: Inline illustrative paths als `&#47;` kodieren (siehe Operator Pack v1.1 Quickstart).
- **Wenn Reference Targets failt**: nur auf existente Ziele linken; “Gap” als Text beschreiben, nicht als Dateipfad.
- **Wenn Diff Guard Policy failt**: Policy Marker in required ops docs wiederherstellen (siehe Diff Guard Runbook).
