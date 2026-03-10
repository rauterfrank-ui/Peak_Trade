> **Historisch / Referenz** — Nicht kanonisch. Snapshot aus Codebase-Analyse (Read-Only).  
> **Origin:** Wave 16 Integration, ursprünglich `docs/GOVERNANCE_DATAFLOW_REPORT.md`.  
> **Canonical:** [docs/governance/](../governance/), [docs/INDEX.md](../INDEX.md)

---

# Peak_Trade: Dataflow Matrix, Governance Coverage & Safety Gates

*Generiert aus Codebase-Analyse (Read-Only). Stand: 2025-03-10.*

---

## 1. Dataflow Matrix

### 1.1 Data Ingest

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Kraken OHLCV** | Kraken API | Normalizer | ParquetCache → `data&#47;cache` | — | Parquet | `src&#47;data&#47;kraken_pipeline.py`, `src&#47;data&#47;cache.py` |
| **Ingress A2→A5** | Events JSONL (NormalizedEvent) | `build_feature_view_from_jsonl` → FeatureView → EvidenceCapsule | `out&#47;ops&#47;views&#47;<run_id>.feature_view.json`, `out&#47;ops&#47;capsules&#47;<run_id>.capsule.json` | Pointer-only (kein payload/raw) | FeatureView + Capsule | `src&#47;ingress&#47;orchestrator&#47;ingress_orchestrator.py`, `docs&#47;runbooks&#47;appendix&#47;A_ingress_end_to_end.md` |
| **Knowledge** | RAG, Embeddings | Vector/TimeSeries | Chroma/Qdrant, Parquet/InfluxDB | `KNOWLEDGE_READONLY`, `KNOWLEDGE_WEB_WRITE_ENABLED` | `config.toml` (knowledge.*) | — |

---

### 1.2 Backtest

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Backtest** | OHLCV DataFrame, Strategy | `BacktestEngine` → Signale → `ExecutionPipeline` (PaperOrderExecutor) | `BacktestResult`, Equity-Curve, Trades | — | PnL, Stats | `src&#47;backtest&#47;engine.py`, `docs&#47;ORDER_PIPELINE_INTEGRATION.md` |
| **Portfolio Backtest** | `data_dict`, Strategy | `run_portfolio_strategy_backtest` | `PortfolioStrategyResult` | — | Multi-Asset-Ergebnisse | `src&#47;backtest&#47;engine.py` |

---

### 1.3 Research

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **New Listings** | CCXT/Replay Config | `run_pipeline` (orchestrator) | DB, Events | `enabled` in Config | RunResult | `src&#47;research&#47;new_listings&#47;orchestrator.py` |
| **R&D Presets** | `r_and_d_presets.toml` | Experiments | `config&#47;r_and_d_presets.toml` | `enabled=false` default | — | `src&#47;experiments&#47;r_and_d_presets.py` |

---

### 1.4 Shadow

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Shadow Session** | Strategy, Config | `ShadowPaperSession` → `ExecutionPipeline.for_shadow()` | `shadow_session_summary.json`, Run-Logs | Keine API-Calls | Simulierte Orders | `src&#47;live&#47;shadow_session.py`, `src&#47;execution&#47;pipeline.py` (for_shadow) |
| **Shadow Execution** | Strategy, Symbol | `run_shadow_execution.py` | Logs, keine echten Orders | 100 % simulativ | — | `scripts&#47;run_shadow_execution.py`, `docs&#47;PHASE_24_SHADOW_EXECUTION.md` |

---

### 1.5 Paper

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Paper** | Strategy, MarketContext | `ExecutionPipeline.for_paper()` | PaperOrderExecutor, Fills | — | Simulierte Fills | `src&#47;execution&#47;pipeline.py`, `src&#47;orders&#47;paper.py` |
| **Paper Session** | Config | `create_shadow_paper_session` | Session-Logs | — | — | `src&#47;live&#47;shadow_session.py` |

---

### 1.6 Testnet

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Testnet** | KrakenTestnetClient | `TestnetOrderExecutor` | Echte Testnet-Orders (wenn `testnet_dry_run=False`) | `testnet_dry_run=True` default, SafetyGuard | OrderLog | `src&#47;orders&#47;testnet_executor.py`, `src&#47;live&#47;testnet_orchestrator.py` |
| **Testnet Orchestrator** | Profile, Limits | `start_testnet_run` | `testnet_*` Run-Dirs | `testnet_limits` | — | `src&#47;live&#47;testnet_orchestrator.py` |

---

### 1.7 Live-Gated

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Execution Orchestrator** | OrderIntent | 8-Stage-Pipeline: Intent → Contract → Risk → Route → Adapter → Event → Post-Trade → Recon | `execution_events.jsonl`, Ledger | Stage 3: Risk Gate; Stage 4: Route Selection (`POLICY_LIVE_NOT_ENABLED`) | PipelineResult | `src&#47;execution&#47;orchestrator.py` |
| **Live Gates** | EnvironmentConfig | `is_live_execution_allowed` | — | `enable_live_trading`, `live_mode_armed`, `confirm_token`, `live_dry_run_mode` | allowed/reason | `src&#47;live&#47;safety.py`, `src&#47;live&#47;live_gates.py` |
| **Venue Adapters** | Order | AdapterRegistry | — | LIVE → reject (LIVE_BLOCKED) | paper/shadow/testnet only | `src&#47;execution&#47;venue_adapters&#47;registry.py` |

---

### 1.8 Observability

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Metrics** | Runtime-Events | `MetricsCollector` | In-Memory / Prometheus | — | Snapshot, Export | `src&#47;observability&#47;metrics.py`, `src&#47;core&#47;metrics.py` |
| **Execution Events** | Orchestrator Stages | JSONL Logger | `execution_events.jsonl` | NO_TRADE default | INTENT, RISK_REJECT, ORDER, FILL | `src&#47;observability&#47;execution_events.py` |
| **Alert Pipeline** | Alerts | Escalation | `alerts_history.jsonl`, Slack/Email | `config&#47;telemetry_alerting.toml` | — | `src&#47;live&#47;alert_pipeline.py` |
| **AI Events** | Execution-Watch | AI Live Exporter | `ai_events.jsonl` (Port 9110) | — | — | `scripts&#47;obs&#47;ai_live_exporter.py` |
| **OpenTelemetry** | Traces/Metrics | OTLP | Collector | — | — | `src&#47;obs&#47;otel.py` |

---

### 1.9 AI/Critics/Proposers

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **L1–L4 Orchestrator** | Layer-Inputs | Model-Calls (Primary/Fallback/Critic) | Evidence Packs, RunLogging | SoD (Proposer ≠ Critic), P49/P50 | Layer-Outputs | `src&#47;ai_orchestration&#47;orchestrator.py`, `src&#47;ai_orchestration&#47;models.py` |
| **L2 Market Outlook** | Makro/Regime | GPT-5.2-pro | `l2_market_outlook.json` | NoTradeTriggers | Szenarien, no_trade | `scripts&#47;aiops&#47;run_l2_market_outlook_capsule.py` |
| **L3 Trade Plan Advisory** | L2 + Capsule | GPT-5.2-pro | Trade-Hypothesen | Risk-Checklist, keine Order-Parameter | — | `scripts&#47;aiops&#47;run_l3_trade_plan_advisory_p5a.py` |
| **Policy v0/v1** | DecisionContext | `decide_policy_v1` | — | NO_TRADE default, ENV_LIVE, EDGE_LT_COSTS | PolicyDecision | `src&#47;observability&#47;policy&#47;policy_v1.py` |

---

### 1.10 Export/Reporting

| Phase | Input | Transformation | Storage/Artifacts | Policy/Risk Gate | Output | Evidence |
|-------|-------|----------------|-------------------|------------------|--------|----------|
| **Execution Reports** | BacktestResult, Logs | `ExecutionStats`, `from_*` | — | — | Stats, Plots | `src&#47;reporting&#47;execution_reports.py` |
| **Backtest Report** | Result, Equity | `build_backtest_report` | Markdown, PNG | — | Report | `src&#47;reporting&#47;backtest_report.py` |
| **Live Run Report** | Session-Daten | `build_live_run_report` | HTML/MD | — | Report | `src&#47;reporting&#47;live_run_report.py` |
| **Live Audit Export** | Live-Session | `export_live_audit_snapshot` | Snapshot-Reports | — | — | `scripts&#47;export_live_audit_snapshot.py` |
| **Promotion Loop** | Proposals | `engine.py` | `reports&#47;live_promotion`, `promotion_audit.jsonl` | — | — | `src&#47;governance&#47;promotion_loop&#47;engine.py` |

---

## 2. Governance Coverage

### 2.1 enable / armed

| Ort | Datei | Befund |
|-----|-------|--------|
| **ArmedGate** | `src&#47;ops&#47;gates&#47;armed_gate.py` | `ArmedState(enabled, armed, armed_since_epoch)`; `arm()`/`disarm()`; `require_armed()` |
| **Operator Context** | `src&#47;live&#47;operator_context.py` | `enabled`, `armed` in Context für live_gates |
| **Feature Activation** | `src&#47;live&#47;feature_activation.py` | `enabled and armed and confirm_ok` für double_play/dynamic_leverage |
| **Kill Switch** | `src&#47;risk_layer&#47;kill_switch&#47;adapter.py` | `armed`, `enabled`; `is_armed()` |
| **AI Activation Gate** | `config&#47;governance&#47;ai_activation_gate_v1.json` | `"enabled": false, "armed": false` |
| **Network Gate** | `src&#47;infra&#47;escalation&#47;network_gate.py` | `enable_live_trading`, `live_mode_armed` |

---

### 2.2 NO_TRADE

| Ort | Datei | Befund |
|-----|-------|--------|
| **Policy Enforcer** | `src&#47;execution&#47;policy&#47;policy_enforcer_v0.py` | `action == "NO_TRADE"` → block |
| **Policy v1** | `src&#47;observability&#47;policy&#47;policy_v1.py` | Default `NO_TRADE`; ENV_LIVE, MISSING_*, EDGE_LT_COSTS |
| **CI/PR Status** | `scripts&#47;ci&#47;prj_status_report.py`, `prk_health_summary.py` | `action == "NO_TRADE"` bei Stale/NoSuccess |
| **Incident** | `scripts&#47;ops&#47;incident_stop_now.sh` | `PT_FORCE_NO_TRADE=1` |
| **Runbooks** | `docs&#47;ops&#47;runbooks&#47;live_pilot_*.md` | Default NO_TRADE ohne explizites Arming |
| **CMES** | `src&#47;risk&#47;cmes&#47;reason_codes.py` | `NO_TRADE_TRIGGER_IDS` |

---

### 2.3 confirm token

| Ort | Datei | Befund |
|-----|-------|--------|
| **Environment** | `src&#47;core&#47;environment.py` | `LIVE_CONFIRM_TOKEN = "I_KNOW_WHAT_I_AM_DOING"`, `require_confirm_token`, `confirm_token` |
| **AI Activation Gate** | `src&#47;governance&#47;ai_activation_gate_v1.py` | `_confirm_token_ok()`, `confirm_token_env`, `confirm_token_required` |
| **Network Gate** | `src&#47;infra&#47;escalation&#47;network_gate.py` | `require_confirm_token`, `confirm_token == LIVE_CONFIRM_TOKEN` |
| **Audit** | `src&#47;live&#47;audit.py` | `confirm_token_present` (Boolean, Wert nicht exportiert) |
| **Config** | `config&#47;governance&#47;ai_activation_gate_v1.json` | `"confirm_token_env": "PT_CONFIRM_TOKEN"`, `"confirm_token_required": true` |

---

### 2.4 dry-run

| Ort | Datei | Befund |
|-----|-------|--------|
| **Live Drills** | `scripts&#47;run_live_dry_run_drills.py` | Phase-73-Dry-Run-Drills |
| **Telemetry Retention** | `src&#47;execution&#47;telemetry_retention.py`, `scripts&#47;ops&#47;telemetry_retention.py` | `dry_run=True` default, `--apply` für Änderungen |
| **Scheduler** | `tests&#47;test_scheduler_smoke.py` | `run_job(..., dry_run=True)` |
| **Portfolio Backtest** | `scripts&#47;run_portfolio_backtest.py` | `--dry-run` für Registry-Logging |
| **P98/P121** | `scripts&#47;ops&#47;p121_execution_wiring_proof_v1.sh` | `DRY_RUN=YES` erforderlich |
| **Testnet** | `src&#47;orders&#47;testnet_executor.py` | `testnet_dry_run` Flag |

---

### 2.5 no-trade defaults

| Ort | Datei | Befund |
|-----|-------|--------|
| **Policy v0/v1** | `src&#47;observability&#47;policy&#47;policy_v0.py`, `policy_v1.py` | Default `NO_TRADE` bei fehlenden Inputs |
| **Pipeline** | `src&#47;execution&#47;pipeline.py` | „Phase Policy v0: safety-first NO_TRADE default“ |
| **Incident/Pilot Snapshots** | `scripts&#47;ops&#47;build_incident_snapshot.sh`, `build_pilot_ready_snapshot.sh` | `"policy_note": "NO_TRADE default preserved"` |
| **deny-by-default** | `src&#47;ai_orchestration&#47;switch_layer_routing_v1.py` | `reason: str = "deny_by_default"` |
| **Governance Specs** | `docs&#47;governance&#47;ai&#47;*.md` | NO_TRADE baseline, deny-by-default |

---

## 3. Governance-Dokumente

### docs/governance/ (45 Dateien)

| Subdir | Dateien |
|--------|---------|
| **Root** | `README.md`, `AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`, `POLICY_CRITIC_*.md`, `POLICY_PACK_TUNING_LOG.md`, `LLM_POLICY_CRITIC_CHARTER.md`, `LAYER_LEARNING_SURFACES_STUB.md` |
| **ai/** | `CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`, `RUNTIME_UNKNOWN_RESOLUTION_V1.md`, `PROPOSER_RUNTIME_RESOLUTION_V1.md`, `CRITIC_RUNTIME_RESOLUTION_V2.md`, `AI_LAYER_CANONICAL_SPEC_V1.md`, `AI_UNKNOWN_REDUCTION_V1.md`, `EXECUTION_ADJACENT_AI_BOUNDARY_SPEC_V1.md`, `PROVIDER_MODEL_BINDING_SPEC_V1.md` (+ Changelogs) |
| **ai_autonomy/** | `README.md`, `QUICKSTART.md`, `PHASE1_*.md`–`PHASE4E_*.md`, `SCHEMA_MANDATORY_FIELDS.md` |
| **matrix/** | `AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` |
| **releases/** | `AI_MATRIX_VALIDATOR_V1.md` |
| **templates/** | `AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE*.md` |
| **evidence/** | `WP0C_GATE_EVIDENCE.md` |
| **todos/** | `AI_MATRIX_GATE_TODO.md` |

### policy_packs/ (3 Dateien)

| Datei | Inhalt |
|-------|--------|
| `ci.yml` | NO_SECRETS, NO_LIVE_UNLOCK, EXECUTION_ENDPOINT_TOUCH, etc. |
| `live_adjacent.yml` | Live-adjazente Policies |
| `research.yml` | Research-Policies |

### config/governance/ (1 Datei)

| Datei | Inhalt |
|-------|--------|
| `ai_activation_gate_v1.json` | `papertrail_ready`, `allow_ai_to_execute_live`, `live_unlock` (enabled, armed, confirm_token_*) |

---

## 4. Safety Gates

### 4.1 Proposer/Critic Separation

| Aspekt | Implementierung | Dateien |
|--------|-----------------|---------|
| **SoD Checker** | `proposer_model_id != critic_model_id`; optional Provider-Diversity | `src&#47;ai_orchestration&#47;sod_checker.py` |
| **Layer Metadata** | `LayerRunMetadata`: `primary_model_id`, `critic_model_id`; Validierung: Primary ≠ Critic | `src&#47;ai_orchestration&#47;models.py` |
| **Matrix** | L0–L6: Primary (Proposer) vs Independent Critic (z.B. DeepSeek-R1) | `docs&#47;governance&#47;matrix&#47;AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` |
| **Spec** | Proposer: advisory; Critic: supervisory; beide nicht execution authority | `docs&#47;governance&#47;ai&#47;CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md` |

---

### 4.2 Runtime Unknown Resolution

| Thema | Stand | Dateien |
|-------|-------|---------|
| **Proposer** | Wenig runtime-evidenziert, advisory-only | `docs&#47;governance&#47;ai&#47;PROPOSER_RUNTIME_RESOLUTION_V1.md` |
| **Critic** | Besser evidenziert, pre-execution/gate-adjacent | `docs&#47;governance&#47;ai&#47;CRITIC_RUNTIME_RESOLUTION_V2.md` |
| **Unknown** | Kein model-final trade authority; deterministisch gated | `docs&#47;governance&#47;ai&#47;RUNTIME_UNKNOWN_RESOLUTION_V1.md` |

---

### 4.3 Audit Trail / Logging

| Aspekt | Implementierung | Dateien |
|--------|-----------------|---------|
| **RunLogging** | `run_id`, `prompt_hash`, `artifact_hash`, `inputs_manifest`, `outputs_manifest`, `timestamp_utc`, `model_id` | `src&#47;ai_orchestration&#47;models.py` (RunLogging) |
| **SoDCheck** | `proposer_model_id`, `critic_model_id`, `result`, `reason`, `timestamp` | `src&#47;ai_orchestration&#47;sod_checker.py` |
| **Model Registry** | `logs&#47;ai_model_calls.jsonl` | `config&#47;model_registry.toml` |
| **Execution Events** | `execution_events.jsonl` (INTENT, RISK_REJECT, ORDER, FILL) | `src&#47;observability&#47;execution_events.py` |
| **Evidence Packs** | Schema mit Mandatory Fields | `docs&#47;governance&#47;ai_autonomy&#47;SCHEMA_MANDATORY_FIELDS.md` |

---

## 5. Referenz-Dateien (Governance & Pipelines)

| Bereich | Wichtige Dateien |
|---------|------------------|
| **Execution** | `src&#47;execution&#47;orchestrator.py` (8-Stage-Pipeline), `src&#47;execution&#47;pipeline.py` |
| **Live Gates** | `src&#47;live&#47;safety.py`, `src&#47;live&#47;live_gates.py` |
| **Armed Gate** | `src&#47;ops&#47;gates&#47;armed_gate.py` |
| **AI Live-Unlock** | `src&#47;governance&#47;ai_activation_gate_v1.py` |
| **Proposer/Critic SoD** | `src&#47;ai_orchestration&#47;sod_checker.py`, `src&#47;ai_orchestration&#47;models.py` |
| **Layer-Matrix** | `docs&#47;governance&#47;matrix&#47;AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` |
| **Gate-Übersicht** | `docs&#47;ops&#47;GATES_UND_DATENFLUSS_UEBERSICHT.md` |
