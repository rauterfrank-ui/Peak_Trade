# Peak_Trade – Cursor Multi‑Agent Orchestration Runbook (Phasen)

**Datum:** 2026-02-03  
**Input:** `FEHLENDE_FEATURES_PEAK_TRADE.md` (fehlende/geplante Features)  
**Output:** Reproduzierbarer, Safety‑First Implementierungs‑Workflow mit klaren Ein-/Ausstiegspunkten, Agent‑Rollen, Gates und Terminal‑Commands.

---

## 0. Leitplanken (nicht verhandelbar)

- **Offline‑First / NO‑LIVE:** Live‑Execution bleibt **blockiert** (L6 verboten). Alles bis max. **Shadow/Testnet/Dry‑Run**.
- **Reproduzierbarkeit:** versionierte Configs, Experiment‑Registry/Tracking, deterministische Seeds, Evidence‑Packs.
- **Risk & Governance:** deterministische Gates (L5), Policy‑Critic (L4), Audit‑Trail/Logs.
- **Incremental Delivery:** kleine PRs, harte Akzeptanzkriterien, CI‑Gates als “Definition of Done”.

---

## 1. Rollenmodell (Cursor Multi‑Agent)

### 1.1 Peak_Trade Layer‑Matrix (Referenz)
- **L0 (Ops/Docs):** Orchestrator + Critic (Runbook, Scope, Evidence)
- **L1 Runner (DeepResearch):** Research/Specs/ADR‑Drafts
- **L2 Runner (Market Outlook):** optional (Markt‑Kontext; nicht für “Entscheidung”)
- **L3 (Trade Plan Advisory):** nur Orchestrator/Layer‑Map (kein eigener Runner)
- **L4 Critic:** Policy/Governance/Threat‑Modeling/Abnahme
- **L5 (Risk Gate):** deterministischer Code (blockiert unsichere Pfade)
- **L6 (Execution):** verboten

### 1.2 Praktische Cursor‑Agenten (empfohlen)
- **ORCH:** Orchestrator (plan → split → assign → merge)
- **SPEC:** Architektur‑/ADR‑Agent (Design‑Docs)
- **IMPL:** Implementer (Code)
- **TEST:** Test/QA (unit/integration/determinism)
- **SEC:** Security/Governance (Threat model, secrets, auth, permissions)
- **CRIT:** L4‑Critic (policy + risk gate review)

---

## 2. Ausgangslage – konsolidierter Feature‑Backlog (ergänzt)

Aus `FEHLENDE_FEATURES_PEAK_TRADE.md` ergeben sich die Kern‑Epics. Zusätzlich ergänzt (sinnvoll) sind **Querschnitts‑Epics**, die typischerweise sonst die Delivery brechen.

### 2.1 Epics aus der Datei (kuratiert)
**E‑01 Feature‑Engine (zentral)**
- ``src&#47;features&#47;`` als echte Schicht (Unified Feature Pipeline, caching, versioning)
- ECM‑Features / Fenster
- Meta‑Labeling / Triple‑Barrier + Feature Extraction (fractional diff, vol‑adj returns, regime inputs)

**E‑02 Research Automation**
- Unified Sweep‑Pipeline CLI (``--run&#47;--report&#47;--promote``)
- Robustness: Monte‑Carlo/Bootstraps, rolling windows
- Metrics: Sortino/Calmar/Ulcer/Recovery, Heatmaps, comparison tool
- Nightly automation + alerts

**E‑03 Real‑Time Data & Streaming**
- WebSocket ingestion (Shadow only)
- Streaming backtest harness (tick/orderbook optional später)
- Latency monitoring / drop detection

**E‑04 Web Dashboard v1**
- AuthN/AuthZ, Access control
- SSE/WebSocket (statt Polling), optional RBAC
- Read‑write bleibt hinter Gates (kein Live‑Start/Stop ohne confirm tokens)

**E‑05 Exchange & Execution (weiterhin safe)**
- Multi‑Exchange Adapter (zunächst **paper + dry‑run**, keine echten orders)
- Fill‑tracking Simulator, Order routing stub
- Testnet orders nur wenn explizit freigeschaltet + Evidence + Review (optional später)

**E‑06 Advanced Risk & Portfolio**
- VaR/CVaR, Stress tests, attribution
- Auto‑Liquidation bei Limit breach (nur in Sim/Dry‑Run zuerst)
- Risk‑Parity / Portfolio Optimization

**E‑07 Infra/Scalability**
- Compose Profiles, optional K8s later
- Multi‑Instance safe scaling (read‑only first)

**E‑08 Community/Plugins**
- Plugin system (strategy/features/adapters)
- Contributing, templates, validation gates

### 2.2 Querschnitts‑Epics (sinnvoll ergänzt)
**X‑01 Evidence & Auditability**
- Evidence‑Pack Standard: inputs, config, seed, env, hashes, metrics, plots
- “Repro‑Check” CI job (re‑run minimal backtest → same checksum)

**X‑02 Observability / SLO**
- Prometheus metrics contract (labels, cardinality limits)
- Grafana dashboards versioned
- Structured logging + correlation IDs, tracing optional

**X‑03 Security Baseline**
- Secret scanning, dependency policies
- Web auth threat model (session, CSRF, rate limit)
- Permissions model (least privilege) + audit logs

**X‑04 Performance / Cost**
- Feature cache + columnar storage (parquet), memory profiling
- Streaming backpressure & batching

**X‑05 Packaging / Release**
- Versioning strategy, changelog, release checklist
- Golden config examples

---

## 3. Runbook in Phasen

Jede Phase hat **Entry**, **Exit**, **Deliverables**, **Commands**, **Agent‑Assignments**.

> Konvention: Branch‑Prefix pro Epic: ``feat&#47;E-01-feature-engine``, ``chore&#47;X-01-evidence``, etc.

---

### Phase 0 — Repo‑Sanity, Safety, Baseline

**Entry**
- Arbeitsverzeichnis sauber oder bewusst (stash/commit)
- Docker/Compose vorhanden (falls genutzt)
- CI lokal minimal ausführbar

**Ziele**
- Baseline herstellen: Tests/linters/targets laufen, Ports nicht kollidieren
- Gate‑Status dokumentieren

**Commands**
```bash
git status
git fetch --prune origin
git checkout -b chore/runbook-baseline

# Python env (Beispiel)
python -V
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Minimal Gates
pytest -q
ruff check .
ruff format --check .
```

**Exit**
- `pytest`, `ruff` grün
- Baseline‑Report in ``docs&#47;evidence&#47;phase0_baseline.md``

**Agent**
- ORCH (führt), TEST (validiert), CRIT (checkt “NO‑LIVE” Pfade)

---

### Phase 1 — Backlog Normalisierung (Specs → Tickets)

**Entry**
- Phase 0 Exit erfüllt
- `FEHLENDE_FEATURES_PEAK_TRADE.md` als Quelle verfügbar

**Ziele**
- Epics → Stories mit Akzeptanzkriterien, Dependencies, Risk Rating
- “Thin‑slice Plan”: zuerst X‑Epics (Evidence/Obs/Security), dann Feature Epics

**Deliverables**
- ``docs&#47;backlog&#47;EPICS.md``
- ``docs&#47;backlog&#47;STORIES.md`` (je Story: AC, tests, metrics, risk)
- ``docs&#47;adr&#47;`` Skeleton (ADR‑0001 …)

**Commands**
```bash
mkdir -p docs/backlog docs/adr docs/evidence
cp "FEHLENDE_FEATURES_PEAK_TRADE.md" docs/backlog/
$EDITOR docs/backlog/EPICS.md
$EDITOR docs/backlog/STORIES.md
```

**Exit**
- Stories priorisiert (P0/P1/P2)
- Jede P0‑Story hat: AC + test plan + evidence plan

**Agent**
- ORCH (split), SPEC (ADR draft), CRIT (risk rating), TEST (test plan)

---

### Phase 2 — Architektur & Verträge (ADRs + Interfaces)

**Entry**
- Phase 1 Exit erfüllt

**Ziele**
- Stabiler API‑Contract für Feature‑Engine + Streaming + Metrics + Web auth
- Minimale “MVP contracts”, bevor Code gebaut wird

**Deliverables (MVP)**
- ADR‑0001 Feature‑Engine (Inputs/Outputs, caching, feature registry)
- ADR‑0002 Streaming Data Interface (WS ingestion, backpressure)
- ADR‑0003 Metrics/Logging Contract (cardinality, naming)
- ADR‑0004 Web Auth Model (sessions/JWT, RBAC, CSRF)
- ADR‑0005 Risk Gate Extensions (auto‑liquidation in sim first)

**Commands**
```bash
$EDITOR docs/adr/ADR-0001-feature-engine.md
$EDITOR docs/adr/ADR-0002-streaming-interface.md
$EDITOR docs/adr/ADR-0003-observability-contract.md
$EDITOR docs/adr/ADR-0004-web-auth.md
$EDITOR docs/adr/ADR-0005-risk-gate-sim.md
```

**Exit**
- ADRs “Accepted”
- Code owners/critic sign‑off (mindestens CRIT)

**Agent**
- SPEC (writes), ORCH (reviews), CRIT/SEC (sign‑off), TEST (testability review)

---

### Phase 3 — Querschnitt zuerst (X‑Epics)

#### Phase 3A — X‑01 Evidence & Repro Gate

**Entry**
- ADRs vorhanden

**Implement (MVP)**
- ``src&#47;core&#47;evidence&#47;`` helpers
- ``scripts&#47;evidence&#47;make_evidence_pack.sh``
- CI job: minimal backtest checksum reproducibility

**Commands**
```bash
git checkout -b chore/X-01-evidence-pack
mkdir -p src/core/evidence scripts/evidence docs/evidence
$EDITOR scripts/evidence/make_evidence_pack.sh
pytest -q
git add -A && git commit -m "chore(evidence): add evidence pack generator + repro gate"
```

**Exit**
- Evidence pack erstellt für einen Beispiel‑Backtest
- CI job grün

**Agent**
- IMPL, TEST, CRIT

---

#### Phase 3B — X‑02 Observability Contract

**Implement**
- Prometheus metric naming/labels enforcement
- Grafana dashboards versioned (json in repo)

**Commands**
```bash
git checkout -b chore/X-02-observability
mkdir -p docs/observability grafana/dashboards
$EDITOR docs/observability/METRICS_CONTRACT.md
pytest -q
git add -A && git commit -m "chore(obs): define metrics contract and version dashboards"
```

**Exit**
- Metrics contract doc + linting checks (optional)  
- Dashboards render locally

---

#### Phase 3C — X‑03 Security Baseline (Web/Auth groundwork)

**Implement**
- Secret scan hooks, dependency policy
- Web auth scaffold (no write actions yet)

**Commands**
```bash
git checkout -b chore/X-03-security-baseline
mkdir -p docs/security
$EDITOR docs/security/THREAT_MODEL_WEB.md
pytest -q
git add -A && git commit -m "chore(sec): add web threat model + baseline policies"
```

**Exit**
- Threat model + baseline checks in CI

---

### Phase 4 — Feature Delivery (Thin Slices)

> Reihenfolge (empfohlen): **E‑01 → E‑02 → E‑04 → E‑03 → E‑06 → E‑05 → E‑07 → E‑08**

#### Phase 4A — E‑01 Feature‑Engine MVP (unified, versioned)

**MVP Scope**
- `FeatureSpec` (name, version, params, dependencies)
- ``FeaturePipeline.fit&#47;transform`` (pandas), deterministic
- Cache (parquet) keyed by (dataset_hash, feature_spec_hash)
- Registry write: ``registry&#47;features&#47;<name>&#47;<hash>.json``

**Commands**
```bash
git checkout -b feat/E-01-feature-engine
mkdir -p src/features src/features/pipeline src/features/registry tests/features
$EDITOR src/features/pipeline/pipeline.py
$EDITOR src/features/registry/registry.py
pytest -q
git add -A && git commit -m "feat(features): add unified feature pipeline + registry + cache"
```

**Exit**
- Unit tests: deterministic output hashes
- Evidence pack includes feature spec + cache keys

**Agent**
- SPEC (contract adherence), IMPL (code), TEST (determinism), CRIT (risk)

---

#### Phase 4B — E‑01 Meta‑Labeling / Triple‑Barrier (real implementation)

**MVP Scope**
- Implement `compute_triple_barrier_labels` (vectorized)
- Implement `_extract_features` minimal set:
  - fractional diff (configurable)
  - vol‑adj returns
  - regime indicators passthrough
- Tests: known small fixtures, edge cases

**Commands**
```bash
git checkout -b feat/E-01-meta-labeling
pytest -q
git add -A && git commit -m "feat(labels): implement triple barrier labeling + feature extraction"
```

**Exit**
- No placeholder outputs (no “zeros everywhere”)
- Benchmark doc: runtime on sample dataset

---

#### Phase 4C — E‑02 Unified Sweep Pipeline CLI

**MVP Scope**
- `run_sweep_pipeline.py --run --report --promote`
- Standard heatmap templates, rolling windows, MC bootstrap CI
- Produces evidence pack + registry entry per run

**Commands**
```bash
git checkout -b feat/E-02-sweep-cli
mkdir -p scripts/research
$EDITOR scripts/research/run_sweep_pipeline.py
pytest -q
git add -A && git commit -m "feat(research): add unified sweep pipeline CLI"
```

**Exit**
- End‑to‑end run on sample strategy passes
- Report artifacts written (plots, csv, json)

---

#### Phase 4D — E‑04 Web Dashboard Auth + Streaming UI (read-only first)

**MVP Scope**
- Login, session, RBAC “viewer/admin”
- Server push: SSE (simpler) → WS optional later
- Still **no** trading controls (nur Beobachtung)

**Commands**
```bash
git checkout -b feat/E-04-web-auth
pytest -q
git add -A && git commit -m "feat(web): add auth scaffold + server push (read-only)"
```

**Exit**
- Auth works locally
- Security checks + threat model updated
- No write endpoints without explicit gate

---

#### Phase 4E — E‑03 Streaming Ingestion (Shadow)

**MVP Scope**
- WS client adapter (exchange feed) behind feature flag
- Drop/latency metrics
- Persist raw stream to log/parquet for replay

**Commands**
```bash
git checkout -b feat/E-03-streaming-shadow
pytest -q
git add -A && git commit -m "feat(stream): add ws ingestion + replay logs (shadow)"
```

**Exit**
- Replay produces identical events ordering (as stored)
- Metrics stable (cardinality bounded)

---

#### Phase 4F — E‑06 Advanced Risk (sim first)

**MVP Scope**
- VaR/CVaR + stress scenarios
- Auto‑liquidation logic only in sim/dry‑run pipeline
- Hard gate: cannot trigger live order paths

**Commands**
```bash
git checkout -b feat/E-06-risk-advanced
pytest -q
git add -A && git commit -m "feat(risk): add var/cvar + stress + sim auto-liquidation"
```

**Exit**
- Risk report attached to evidence pack
- L5 gate unit tests cover “deny live”

---

### Phase 5 — Integration & Promotion Pipeline

**Ziele**
- “Research → Shadow → Testnet → Live” als formalisierter Promote‑Flow  
- Live bleibt blockiert: Promote endet bei Testnet/Dry‑Run unless governance exception.

**Deliverables**
- ``docs&#47;runbooks&#47;PROMOTION_PIPELINE.md``
- ``scripts&#47;ops&#47;promote_run.sh`` (requires confirm token)

**Commands**
```bash
mkdir -p docs/runbooks scripts/ops
$EDITOR docs/runbooks/PROMOTION_PIPELINE.md
$EDITOR scripts/ops/promote_run.sh
pytest -q
git add -A && git commit -m "chore(pipeline): formalize promote flow with confirm token"
```

**Exit**
- Shadow promotion works end‑to‑end (config + registry + evidence)
- Testnet dry‑run validated
- Live path still raises LiveNotImplementedError (expected)

---

### Phase 6 — Hardening & Release

**Ziele**
- Stabilität, docs, versioning, plugin templates, release checklist

**Commands**
```bash
$EDITOR docs/RELEASE_CHECKLIST.md
pytest -q
ruff check .
```

**Exit**
- Release checklist complete
- Version bump + changelog

---

## 4. Cursor Prompt‑Templates (copy/paste)

### ORCH (Orchestrator)
- Ziele: split into stories, enforce gates, keep PRs small.
- “Du darfst keine Live‑Execution aktivieren. Jede Änderung muss testbar und reproduzierbar sein.”

### SPEC (Architecture/ADR)
- Liefere: ADR + interfaces + migration plan + risks.
- Fokus: determinism, caching keys, schema evolution.

### IMPL (Code)
- Liefere: minimal MVP, clean API, logging/audit hooks.
- No hidden side effects; feature flags.

### TEST (QA)
- Liefere: unit + integration + determinism tests; fixtures; performance checks.
- Definiere “golden outputs” + checksum strategy.

### SEC/CRIT
- Liefere: threat model updates; policy checks; reject unsafe changes.
- Prüfe: secrets, auth, permissions, live gates.

---

## 5. Checklisten (DoD)

### 5.1 Story‑DoD (minimal)
- [ ] Akzeptanzkriterien erfüllt  
- [ ] Unit tests + determinism check  
- [ ] Evidence pack erzeugt & im PR referenziert  
- [ ] L4 critic sign‑off (bei Risk/Web/Execution)  
- [ ] Docs/ADR aktualisiert (falls interface geändert)

### 5.2 “No‑Live” Gate
- [ ] L6 bleibt verboten  
- [ ] Alle Execution‑Entry‑Points sind gated + tested  
- [ ] Confirm token erforderlich für promote steps  

---

## 6. Anhang – Quick Commands

```bash
# Neue Epic‑Arbeit starten
git checkout main
git pull --ff-only
git checkout -b feat/E-01-feature-engine

# Lokal prüfen
pytest -q
ruff check .
ruff format --check .

# Evidence pack erzeugen (falls implementiert)
./scripts/evidence/make_evidence_pack.sh
```

---

## 7. Original‑Input (Kurzreferenz)

> Datei: `FEHLENDE_FEATURES_PEAK_TRADE.md` – fehlende / geplante Features (Stand 2026‑02‑03)  
> Enthält u. a.: Feature‑Engine Placeholder, Meta‑Labeling TODO, Streaming/WebSocket, Web‑Auth, Multi‑Exchange, Advanced Risk, Research‑Sweeps.

