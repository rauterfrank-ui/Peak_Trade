# Peak_Trade – Autonomous Trading Handout & Roadmap

**Status:** docs-only handout (paper stability guard)  
**Stand:** 2026-03-21  
**Branch:** feat/autonomous-trading-handout-roadmap  
**Scope:** Planning, Architecture, Roadmap – keine Deployment-Autorisation

---

## 1. Executive Summary

Peak_Trade ist ein modulares, research-getriebenes Trading-Framework für Krypto-Strategien mit konsequentem **Safety-First**- und **Governance-First**-Ansatz. Das System ist heute ein **Research-/Backtest-/Paper-/Shadow-System**. Live-Execution ist governance-locked und nicht aktiviert.

Dieses Handout beschreibt den aktuellen Stand, alle relevanten Schichten, AI-Layer, Model-Bindings, Governance-Grenzen, Execution, Risk, Observability und eine phasierte Roadmap von heute bis zu einem potenziell autonomen, selbstlernenden Tag-Trading-System. Es handelt sich um eine Planungs- und Architektur-Handreichung – keine Freigabe für Live-Trading, keine Änderung von Runtime oder Konfiguration.

**Kernaussagen:**
- Peak_Trade ist **nicht** evidenzbasiert als vollständig autonomes System.
- Der nächste Execution-Pfad bleibt deterministisch und gated; LLM-Proposer/Critic sind advisory/supervisory.
- Autonome Trading-Pfade sind **kontingent** auf zusätzliche Evidence, Controls und Review.

---

## 2. Current Peak_Trade State

### 2.1 Kurzbeschreibung

Peak_Trade ist ein Python-Framework (≥ 3.9) mit:
- Strategie-Library (ma_crossover, trend_following, mean_reversion, RSI, etc.)
- Backtest-Engine (bar-by-bar, no look-ahead)
- Research-Pipeline (Sweeps, Walk-Forward, Monte-Carlo, Robustness)
- Regime-Detection, Portfolio-Presets, VaR/CVaR, Stress-Testing
- Shadow-/Paper-/Testnet-Execution (keine echten Live-Orders)
- ExecutionPipeline MVP (deterministisch, NO-LIVE Adapter)
- Governance-Gates (Policy Critic, Evidence Packs, CodeGate)
- Ops-Stack (Runbooks, Evidence Index, Drills, CI/Gates)

### 2.2 Aktive Modi

| Modus | Status | Beschreibung |
|-------|--------|--------------|
| Research | Aktiv | Backtests, Sweeps, Regime-Analyse, Experiment-Registry |
| Paper | Aktiv | Simulierte Orders, kein echtes Kapital |
| Shadow | Aktiv | Live-Datenstrom + Paper-Execution, Drift-Detection |
| Testnet | Vorbereitet | Sandbox-Orders möglich, aber governance-gated |
| Live | **Gesperrt** | enable_live_trading=false, Live-Execution locked |

---

## 3. Full System Map

```
Data → Strategy → Sizing → Risk → Backtest/Research → Reporting → Governance/Ops/Live-Track
                                                                    ↑
Change (Docs/Code/Config) → CI/Gates → Merge → main
```

**Wesentliche Domänen:**
- **Research:** Strategie-Entwicklung, Backtests, Sweeps
- **Execution:** Order-Generierung, Routing, Adapter (Paper/Shadow/Null/InMemory)
- **Testnet/Live:** Exchange-Anbindung – aktuell nicht aktiviert
- **Governance:** Policy Critic, Risk-Gates, Evidence Packs, CodeGate

---

## 4. AI Layer Map

### 4.1 Authoritative Layer Matrix (AI Autonomy Layer Map v1.0)

| Layer ID | Layer Name | Purpose | Autonomy | Primary Model | Critic | Tool Access | Hard Constraints |
|----------|------------|---------|----------|---------------|--------|-------------|------------------|
| L0 | Ops/Docs | Runbooks, Checklisten | REC | gpt-5.2 | deepseek-r1 | files | Keine Live-Parameter; nur Docs |
| L1 | DeepResearch | Literatur, Evidenzrecherche | PROP | o3-deep-research | o3-pro | web, files | Nur Research-Outputs |
| L2 | Market Outlook | Makro/Regime/Szenarien | PROP | gpt-5.2-pro | deepseek-r1 | web (opt), files | Szenarien + Unsicherheit + No-Trade-Triggers |
| L3 | Trade Plan Advisory | Intraday Trade-Hypothesen | REC/PROP | gpt-5.2-pro | o3 | files | Keine Order-Parameter „ready to send“ |
| L4 | Governance / Policy Critic | Policy-Checks, Evidence Review | RO/REC | o3-pro | gpt-5.2-pro | files | Darf nichts freischalten ohne Evidence IDs |
| L5 | Risk Gate (Hard) | Limits, Kill-Switch, Bounded-Auto | RO | (kein LLM) | — | — | Deterministischer Code |
| L6 | Execution | Order Routing | EXEC (verboten) | — | — | — | Bis Freigabe verboten |

### 4.2 Autonomy Levels

- **RO (Read-Only):** Zusammenfassen, prüfen, extrahieren – keine Empfehlungen
- **REC (Recommend):** Empfehlung ohne Plan-Fixierung
- **PROP (Propose):** Konkreter Vorschlag, aber nicht ausführbar
- **EXEC:** Ausführung – **verboten** ohne explizite Freigabe

---

## 5. Model / Provider / Binding Map

### 5.1 Bekannte Modelle (AI Autonomy Matrix)

| Model ID | Family | Use Cases | Status |
|----------|--------|-----------|--------|
| gpt-5.2-pro | gpt-5 | L2, L3 | production |
| gpt-5.2 | gpt-5 | L0 fallback, L2/L3 fallback | production |
| gpt-5-mini | gpt-5 | L0 fallback | production |
| o3-deep-research | o3 | L1 | production |
| o3-pro | o3 | L4, L1 critic | production |
| o3 | o3 | L3 critic | production |
| o4-mini-deep-research | o4 | L1 fallback | production |
| deepseek-r1 | deepseek | L0/L2/L4 critic, fallback | production |

### 5.2 Provider/Model-Binding-Truth

- **code-wired:** Binding gilt als implementiert nur bei direktem Code-Nachweis
- **config-wired:** Binding gilt als implementiert nur bei aktivem Config + bekanntem Runtime-Pfad
- **docs-only:** Referenz nur in Doku → **kein** Runtime-Binding
- **unknown:** Exact ownership, runtime path, binding mechanism ungelöst

**Aktuell:** Proposer/Critic Runtime-Pfad und exakte Model-Bindings sind teils **UNKNOWN** oder **PARTIAL**. Siehe `docs/governance/ai/CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`, `PROVIDER_MODEL_BINDING_SPEC_V1.md`.

---

## 6. Governance + Safety Gates

### 6.1 Non-Negotiables

- **No-Live Defaults:** enable_live_trading=false in config.toml
- **Risk gewinnt immer:** Keine Overrides als Default-Mechanik
- **Live-Execution governance-locked:** Bis explizit freigegeben
- **Two-Man-Rule:** Freigaben für Live-Runs, Risk-Limits
- **Keine Secrets ins Repo:** .env/Keys gitignored

### 6.2 Policy Critic (LLM-PC)

- **Read-only** Governance-Layer
- Prüft Diffs, Config-Edits, Runbooks gegen Security/Risk/Execution/Docs
- Kann **bremsen**, nie beschleunigen
- Fail-Closed: Bei Exception → REVIEW_REQUIRED
- Hard-Gates bleiben souverän; LLM-PC ersetzt sie nicht

### 6.3 CI / Gates (Auszug)

| Gate | Kategorie | Trigger |
|------|-----------|---------|
| tests (3.9, 3.10, 3.11) | Test | PR/Push |
| Policy Critic Gate | Policy | PR (policy-sensitive paths) |
| Lint Gate | CI | PR |
| docs-reference-targets-gate | Docs | PR (md changes) |
| Docs Diff Guard Policy Gate | Docs | PR |
| required-checks-hygiene-gate | CI | PR |
| evidence-pack-validation-gate | Validation | PR |

---

## 7. Research → Shadow → Testnet → Live Pipeline

### 7.1 5-Stufen-Plan

1. **Research:** Backtests, Sweeps, Regime-Analyse
2. **Shadow:** Live-Daten + Paper-Execution (≥ 12 Wochen empfohlen)
3. **Testnet:** Sandbox-Orders (≥ 16 Wochen empfohlen)
4. **Shadow-Live:** Vorbereitung Live
5. **Live:** Echte Orders – nur nach expliziter Freigabe

### 7.2 Playbook Research → Live Portfolios (Phase 54)

- Portfolio-Preset auswählen → Research-CLI → Research-Pipeline v2 → Go/No-Go → Mapping auf Live-Konfig → Shadow/Paper/Testnet → Live-Readiness

### 7.3 Red Flags → sofortiger Stop

- Drawdown > 20%
- Crash ohne Recovery
- Ungeklärte Recon-Divergenzen
- Security Incident / Key-Leak-Verdacht

---

## 8. Execution Layer

### 8.1 ExecutionPipeline MVP (Phase 16A)

- Paket: `src/execution_pipeline/`
- Contracts: ExecutionContext, ExecutionPlan, ExecutionResult
- Adapter: NullExecutionAdapter, InMemoryExecutionAdapter – **NO-LIVE**
- Event-Schema: execution_event_v0 (created, validated, submitted, acked, filled, canceled, failed)
- Telemetrie: JSONL append-only
- Watch-API: read-only

### 8.2 Live Broker Boundary

- Live-Order-Execution: **locked** (Governance)
- Kein Executor-Dispatch zu Live ohne Freigabe
- Runbook: `docs/ops/runbooks/RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md`

### 8.3 Execution Authority

- Closest-to-trade = deterministischer, gated Pfad
- NO_TRADE baseline, deny-by-default, Treasury-Separation
- Proposer/Critic: advisory/supervisory, **keine** Execution-Authority

---

## 9. Risk Layer

### 9.1 Risk Layer v1.0

- VaR/CVaR (Historical, Parametric, Cornish-Fisher, EWMA)
- Component VaR, Monte Carlo VaR
- VaR Backtesting (Kupiec POF, Christoffersen, Basel Traffic Light)
- Stress Testing (historische Szenarien, Reverse Stress)
- VaR Backtesting stdlib-only refactoring (Phase 8A/B/D)

### 9.2 Kill Switch

- Config: `config/risk/kill_switch.toml`
- Architektur: `docs/risk/KILL_SWITCH_ARCHITECTURE.md`
- Runbook: `docs/risk/KILL_SWITCH_RUNBOOK.md`
- Drill: monatlich empfohlen (Shadow/Testnet only)
- Kill-Switch hat Priorität über jede LLM-Empfehlung

### 9.3 Bounded-Live Config (Phase 1)

- $100 daily loss limit, $500 total exposure
- enforce_limits=true, allow_override=false
- require_kill_switch_active=true
- 7-Tage-Mindestdauer pro Phase

---

## 10. Observability + Operator Layer

### 10.1 Observability-Plan (Phase 62)

- Metriken: system.health.*, portfolio.*, risk.*, research.*
- Logging: strukturiert, JSON-Logs
- Alerts: AlertLevel (INFO, WARNING, CRITICAL), AlertSink (Logging, Webhook, Slack)
- Zukünftig: Prometheus, Grafana, Alertmanager

### 10.2 Beweise (Evidence)

- EV-METRICSD-MODE-B-VERIFY: metricsd multiprocess, Prometheus targets
- EV-STRATRISK-TELEM-VFY: Strategy/Risk-Telemetrie :9111
- EV-AI-LIVE-OPS-LOCAL: AI Live Telemetry local verify
- Shadow MVS: Prometheus ready, Grafana health, datasource provisioned

### 10.3 Operator Workflows

- Ops Hub: `docs/ops/README.md`
- Control Center: AI Autonomy Control Center v0
- Runbooks: Docs Gates, Merge Log, Incident Handling, Kill Switch Drill, Live Mode Transition
- Drills: D01 (Pre-Flight), Phase 5 NO-LIVE Drill Pack

---

## 11. Evidence / Registry / Reproducibility Layer

### 11.1 Evidence Index (v0.15)

- Format: EV-YYYYMMDD-&lt;TAG&gt;
- Schema: `docs/ops/EVIDENCE_SCHEMA.md`
- Template: `docs/ops/EVIDENCE_ENTRY_TEMPLATE.md`
- Kategorien: CI/Workflow, Docs/Navigation, Drill, Governance/Runbook, AI Autonomy

### 11.2 Evidence Pack / CodeGate

- Evidence Packs referenzieren Layer-ID, Model-ID, SoD-Check
- CodeGate prüft gegen AI Autonomy Matrix
- L4 Critic Determinism Contract: kanonische Feldmuster, SHA256, Validator-CLI

### 11.3 Reproducibility

- Experiment-Registry, Run-Logging
- Deterministische Backtests (seed, bar-by-bar)
- Config-Audit-Trail, Merge-Logs unter `docs/ops/merge_logs/`

---

## 12. What Already Exists

### 12.1 Voll implementiert

| Bereich | Features |
|---------|----------|
| Data | Loader, Normalizer, Cache, Regime |
| Strategy | ma_crossover, trend_following, mean_reversion, RSI, Registry |
| Backtest | Engine, Stats, bar-by-bar |
| Research | Sweeps, Walk-Forward, Monte-Carlo, Portfolio-Robustness |
| Risk | VaR/CVaR, Stress, Kupiec, Christoffersen, Traffic Light |
| Execution | ExecutionPipeline MVP, Paper/Shadow, Null/InMemory Adapter |
| Governance | Policy Critic, Evidence Packs, Go/No-Go, CodeGate |
| Ops | Runbooks, Drills, Evidence Index, CI/Gates, Docs Gates |
| Observability | Live-Status-Reports, Alerts, Telemetry (teilweise) |

### 12.2 Teilweise implementiert

- Proposer/Critic: Semantik definiert, Runtime teils UNKNOWN
- Model-Bindings: Matrix vorhanden, exakte Zuordnung je Komponente teils offen
- Observability: Plan + erste Metriken, Prometheus/Grafana optional
- Shadow/Testnet: Infra vorbereitet, Governance-gated

---

## 13. What Is Missing

### 13.1 Architektur-Vision vs. Implementierung

| Feature | Status |
|---------|--------|
| Feature-Engine als zentrale Schicht | Fehlt |
| ECM-Fenster / ECM-Features | Fehlt |
| Sentiment (News/Makro/Onchain) | Fehlt |
| Orderbuch-/Tick-Daten | Fehlt |
| Echte Live-Order-Ausführung | Gesperrt |
| Testnet ohne Dry-Run | Nicht aktiviert |
| Multi-Exchange | Nur Kraken |
| Web-Dashboard: Auth, POST/PUT/DELETE | Fehlt |
| Real-Time-WebSocket-Streams | Nur REST/Polling |
| ML-basierte Strategien | Fehlt |
| Online Self-Improving Live Learning | Nicht evidenzbasiert |
| LLM als final trade authority | NICHT ERLAUBT |

### 13.2 Proposer/Critic Unknown-Reduction Backlog

- Exakter Proposer-Runtime-Pfad
- Exakter Critic Data-Contract
- Provider/Model-Binding pro Komponente
- Block/Downgrade-Semantik im Runtime (wo unterstützt)

---

## 14. Gap Matrix

| Gap | Kategorie | Severity | Evidence erforderlich |
|-----|-----------|----------|------------------------|
| Live-Execution | Governance | Hoch | Evidence Packs, Multi-Stakeholder-Approval |
| Proposer/Critic Runtime | AI | Mittel | Code/Config-Nachweis |
| Model-Bindings je Layer | AI | Mittel | Capability-Scope-Integration |
| Feature-Engine | Research | Mittel | Architektur-Entscheidung |
| Observability Stack (Prometheus/Grafana) | Ops | Mittel | Phase 62 Plan |
| Online Self-Learning | AI | Hoch | Explizite Implementierungs-Evidenz |
| Multi-Exchange | Infra | Niedrig | Priorisierung |

---

## 15. Roadmap Phases (Current → Autonomous System)

### Phase 0 – Foundation (bereits in Teilen umgesetzt)

- Execution Core, Risk v1.0, Governance Hardening, Observability Minimum
- Kill-Switch getestet, Evidence Packs für Phase-0-Gate

### Phase 1 – Shadow Trading (≥ 12 Wochen)

- Live Data Feed, Shadow Execution (Paper)
- Signal Validation, Drift Detection
- Operator UX, Daily Reports
- Ziele: Data Uptime ≥ 99.5%, Signal Match ≥ 90%, Recovery p95 &lt; 2 min

### Phase 2 – Testnet (≥ 16 Wochen)

- Exchange Client (Testnet), Lifecycle + Recon
- Performance/Latency (Signal→Order p95 &lt; 2000 ms)
- Drills: 24h stress, weekend, flash vol, kill switch
- Ziele: Order Success ≥ 99%, Fill Rate ≥ 98%, Recon 100%

### Phase 3 – Controlled Live

- Micro-Positionen, strenge Limits
- 24/7 Monitoring, Incident-Response
- Safety Analytics, Postmortem-Pipeline

### Phase 4 – Production

- Skalierung (Step-Ladder), Multi-Strategy
- Continuous Improvement Loop (gated)
- Quartalsweise Security-Audit

### Phase 5+ – Autonomous (kontingent)

- **Kontingent auf:** Zusätzliche Evidence, mehr Controls, expliziten Review
- Proposer/Critic vollständig runtime-evidenziert
- Online Learning nur mit Governance-Beweis
- Kein Claim auf „vollautonom“ ohne explizite Implementierungs-Nachweise

---

## 16. Hard Blockers / Non-Negotiables

1. **Kein Live-Trading ohne Evidence Packs und Governance-Freigabe**
2. **Kill-Switch** muss erreichbar und getestet sein
3. **Shadow ≥ 12 Wochen, Testnet ≥ 16 Wochen** – nicht wegoptimieren
4. **Red Flags → sofortiger Stop** (Drawdown &gt; 20%, Recon-Divergenzen, Security)
5. **LLM darf nie Execution-Authority haben** – deterministischer Pfad closest-to-trade
6. **Proposer ≠ Critic** (Separation of Duties; unterschiedliche Modelle)
7. **Fail-Closed** bei Unklarheit oder Unavailable
8. **Keine Secrets in Repo** – keine Key-Handling-Dokumentation mit Klartext

---

## 17. Recommended Sequencing

1. **Proposer/Critic Unknown-Reduction:** Runtime-Pfad, Data-Contract, Model-Binding klären
2. **Shadow-Stabilität:** Mindestlaufzeit einhalten, Drift-Reports, Incident-Log
3. **Testnet-Readiness:** Exchange-Sandbox, Recon, Drills
4. **Observability:** Prometheus/Grafana-Integration gemäß Phase-62-Plan
5. **Feature-Engine (optional):** Architektur-Entscheidung für zentrale Feature-Schicht
6. **Controlled Live:** Nur nach allen Gates, Bounded-Live-Config, 4 Sign-offs
7. **Autonomous Path:** Keine Beschleunigung ohne Evidence – jeder Schritt evidenzbasiert

---

## 18. What Must Remain Non-Autonomous Unless Explicitly Proven

- **Live-Order-Execution** – bis Governance-Freigabe
- **Risk-Limit-Überschreitung** – nie per LLM
- **Kill-Switch-Override** – nie per LLM
- **Config-Änderungen** an live_risk, enable_live_trading – Two-Man-Rule
- **Secrets/Credentials** – nie durch AI-Layer
- **Final Trade Authority** – bleibt deterministisch; LLM nur advisory/supervisory
- **Online Model Updates** – nur mit explizitem Governance-Nachweis

---

## 19. Appendix: Canonical Docs / Runbooks / Specs

| Thema | Pfad |
|-------|------|
| Governance Overview | docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md |
| AI Autonomy Matrix | docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md |
| Policy Critic Charter | docs/governance/LLM_POLICY_CRITIC_CHARTER.md |
| Critic/Proposer Boundary | docs/governance/ai/CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md |
| Provider/Model Binding | docs/governance/ai/PROVIDER_MODEL_BINDING_SPEC_V1.md |
| AI Layer Canonical Spec | docs/governance/ai/AI_LAYER_CANONICAL_SPEC_V1.md |
| Gates Overview | docs/ops/GATES_OVERVIEW.md |
| Evidence Index | docs/ops/EVIDENCE_INDEX.md |
| Project Summary | docs/PEAK_TRADE_PROJECT_SUMMARY_CURRENT_2026-01-27.md |
| Execution Roadmap | docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md |
| Execution Pipeline MVP | docs/execution/phase16/PHASE16A_EXECUTION_PIPELINE_MVP.md |
| Risk Layer Guide | docs/risk/RISK_LAYER_V1_GUIDE.md |
| Kill Switch | docs/risk/KILL_SWITCH_ARCHITECTURE.md, KILL_SWITCH_RUNBOOK.md |
| Observability Plan | docs/OBSERVABILITY_AND_MONITORING_PLAN.md |
| Playbook Research→Live | docs/PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md |
| Execution Governance Runbook | docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md |
| Live Operational Runbooks | docs/LIVE_OPERATIONAL_RUNBOOKS.md |

---

**Disclaimer:** Dieses Handout ist eine Planungs- und Architektur-Handreichung. Es stellt keine Finanzberatung dar und autorisiert kein Live-Trading. Jeder Pfad zu einem autonomen System ist kontingent auf zusätzliche Evidence, Controls und Review.

**Version:** v1.0  
**Datum:** 2026-03-21
