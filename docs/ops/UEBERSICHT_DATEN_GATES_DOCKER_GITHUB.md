# Übersicht: Daten / Gates / Docker / GitHub

> Contract: Status/Evidence sind normativ definiert in:
> - `docs/ops/STATUS_MATRIX.md`
> - `docs/ops/evidence/README.md`

Stand: Februar 2026. Kurzreferenz für Docker-Compose-Stacks, Prometheus-Scrape-Targets und alle GitHub-Workflow-Actions inkl. zugehöriger Datentypen.

---

## Implementierungsstatus (Kurz)

- **Docker, Prometheus, GitHub-Workflows, Abschnitt 5 (Datenströme):** Alle genannten Komponenten sind **implementiert** (Scripts, Workflows, Exporter, Stage1, Trigger Training, Kraken-Pipeline, Alerts, Promotion, etc.). Keine fehlenden Scripts in Workflows.
- **Bewusst Phase-begrenzt / Stub:** Kill Switch im RiskHook (Phase 0: „not implemented“), PagerDuty-Eskalation (`pagerduty_stub`, Phase 85), Adapter-Protocol (WP0C placeholder). Research-Strategien mit TODO/NotImplementedError sind geplant für spätere Phasen.
- **Optional / Legacy:** OpenTelemetry (optional, `peak_trade[otel]`), ChromaDB-Workflow (optional), `peak_trade_session` (Mode A, oft deaktiviert; Mode B metricsd ist Standard).
- **Fazit:** Nichts Nachzügliches für die **Übersicht** – die Dokumentation deckt den aktuellen Stand ab. Erweiterungen (z. B. echter Kill Switch, PagerDuty) sind Phasen-Features, keine Lücken in dieser Übersicht.

---

## Gates (Kurzüberblick)

**Wichtig:** "Config vorhanden" ≠ "wirksam". Claims sind nur dann **enforced**, wenn Evidence ≥ E1 verlinkt ist.

| gate | claim | status | evidence | notes |
|------|--------|--------|----------|-------|
| Kill Switch | risk hook blocks order placement when kill switch enabled | enforced | docs/ops/evidence/packs/PR-02/EV-2026-02-PR02-001.json; docs/ops/evidence/packs/PR-02/EV-2026-02-PR02-002.json <!-- pt:ref-target-ignore --> | E1 unit + E2 light via SafetyGuard; audits to JSONL |
| PagerDuty | escalation provider interface exists; default stub | stub | docs/ops/evidence/packs/PR-01/EV-2026-02-PR01-000.json | real provider follows in PR-03 |

---

## Hinweise

- Bitte keine absoluten Aussagen ("verhindert zuverlässig"), solange `status != enforced`.
- Evidence-Packs sind append-only; jede Änderung an Claims benötigt neue Evidence-ID.

---

## 1. Docker – Daten/Endpoints pro Stack

Docker hat hier **keine** CI-„Gates“, sondern **Compose-Services** und **Prometheus-Scrape-Targets** (welche Metriken von wo gesammelt werden).

### 1.1 Compose-Stacks (Repositorium)

| Stack / Datei | Service(s) | Daten / Zweck |
|---------------|------------|----------------|
| **docker/compose.yml** | `mlflow` | MLflow Backend + Artifacts (Experiment-Tracking, Model-Metadaten, Runs); Port 5001→5000 |
| **docker/docker-compose.obs.yml** | `peaktrade-ops` | Ops Runner: Stage1-Snapshots, Stage1-Trends, Reports; kein Default-Command (z.B. `stage1-snapshot`, `stage1-trends`) |

### 1.2 Prometheus-Scrape-Targets („Daten-Gates“ in Docker)

Konfiguration typisch in `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml` bzw. als Volume in Prometheus-Stack:

| Job Name | Target | Port | Daten / Bedeutung |
|----------|--------|------|-------------------|
| **shadow_mvs** | `shadow_mvs_exporter` (Container) | 9109 | Shadow MVS Metriken (Mock/Sim) |
| **peak_trade_web** | `host.docker.internal:8000` | 8000 | Web-UI / App-Metriken (läuft auf Host) |
| **ai_live** | `host.docker.internal:9110` | 9110 | AI Live Exporter (Watch-only, Host) |
| **peak_trade_metricsd** | `host.docker.internal:9111` | 9111 | Strategy/Risk-Telemetrie (Mode B: metricsd Always-on) |
| *(optional)* **peak_trade_session** | `host.docker.internal:9111` | 9111 | Legacy: In-Process /metrics pro Session (Mode A, oft deaktiviert) |

Damit laufen in Docker-Umgebung folgende **Datenströme** über diese „Gates“:
- **Shadow/Sim-Metriken** → `shadow_mvs`
- **Web/App-Metriken** → `peak_trade_web`
- **AI-Live-Metriken** → `ai_live`
- **Strategy/Risk-Metriken** → `peak_trade_metricsd`

---

## 2. GitHub Workflows – alle Workflow-Actions nach Datentyp / Gate

### 2.1 Knowledge

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Knowledge Extras (ChromaDB) | `knowledge_extras_chromadb.yml` | schedule (Mo 06:30 UTC), workflow_dispatch | ChromaDB-basierte Knowledge-DB-Tests, optionale Evals |

### 2.2 Health (Test Health)

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Test Health Automation | `test_health.yml` | schedule, workflow_dispatch, push/PR/merge_group | CI Health Gate (weekly_core), Test-Health-Profile, Reports → Artifacts |
| Test Health Automation (Full Suite) | `test-health-automation.yml` | workflow_dispatch, schedule (nightly) | Alle Health-Profile inkl. Strategy-Coverage, Switch-Sanity, Nightly-Runs |

### 2.3 Strategie

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| CI | `ci.yml` | push/PR/merge_group, schedule, workflow_dispatch | **strategy-smoke**-Job: v1.1-Strategien-Validierung, Smoke-CLI, Artifacts |

### 2.4 Trigger-/Automations-Daten (InfoStream, TestHealth als Input)

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| InfoStream Automation | `infostream-automation.yml` | schedule (03:15 UTC), workflow_dispatch | TestHealth-Reports → IntelEvents, KI-Auswertung, INFOSTREAM_LEARNING_LOG.md |
| Market Outlook | `market_outlook_automation.yml` | schedule (05:00 UTC), workflow_dispatch | Tägliche Marktprognose (MarketSentinel), LLM-Integration |

### 2.5 Evidence / Policy / Execution-Review

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Evidence Pack Validation Gate | `evidence_pack_gate.yml` | PR, merge_group, workflow_dispatch | Evidence Packs erstellen + validieren (CI-Gate) |
| Policy Critic Gate | `policy_critic_gate.yml` | PR, merge_group | Policy-sensitive Pfade prüfen, ggf. Policy-Critic |
| Policy Critic Gate (Full) | `policy_critic.yml` | PR, merge_group | Evidence-Dateien, Execution-Review, Testplan-Check |
| Policy Guard – No Tracked Reports | `policy_tracked_reports_guard.yml` | (siehe Datei) | Sicherstellen, dass keine tracked Reports ignoriert werden |

### 2.6 Docs

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Docs Reference Targets Gate | `docs_reference_targets_gate.yml` | PR, merge_group, workflow_dispatch | Kaputte Referenzen in Markdown verhindern |
| Docs Diff Guard Policy Gate | `docs_diff_guard_policy_gate.yml` | PR, merge_group, workflow_dispatch | Docs-Policy bei Diff-Änderungen |
| Docs Token Policy Gate | `docs-token-policy-gate.yml` | PR, workflow_dispatch | Token-Policy für Docs |
| Docs Reference Targets Trend | `docs_reference_targets_trend.yml` | workflow_run (Docs Gate), PR | Trend zu Referenz-Targets (neue kaputte Links) |
| Docs Integrity Snapshot | `docs-integrity-snapshot.yml` | (siehe Datei) | Link-Graph, verwaiste Seiten (informational) |

### 2.7 VaR / Risk-Reports

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| VaR Report Regression Gate | `var_report_regression_gate.yml` | PR/push (paths), merge_group, workflow_dispatch | report_compare / report_index deterministisch, VaR-Fixtures |

### 2.8 Trend / AIOps (L4 Critic, Validator, Trend Seed/Ledger)

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| L4 Critic Replay Determinism | `l4_critic_replay_determinism.yml` | PR (paths), merge_group, workflow_dispatch | Critic-Replay deterministisch, critic_report.json |
| L4 Critic Replay Determinism (v2) | `l4_critic_replay_determinism_v2.yml` | (siehe Datei) | Wie oben + Normalized Validator Report (Phase 4E) |
| AIOps – Trend Seed from Normalized Report | `aiops-trend-seed-from-normalized-report.yml` | workflow_run (L4 Critic), main | Trend Seed aus normalisiertem Validator-Report |
| AIOps – Trend Ledger from Seed | `aiops-trend-ledger-from-seed.yml` | workflow_run (Trend Seed), workflow_dispatch | Trend Ledger aus Trend Seed |
| AI-Ops Promptfoo Evals | `aiops-promptfoo-evals.yml` | (siehe Datei) | Promptfoo-Evaluierungen für AI-Ops |

### 2.9 Replay / Recon

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Replay Compare Report | `replay_compare_report.yml` | PR (paths), workflow_dispatch | Deterministischer Replay, compare_report.json |
| Recon Audit Gate Smoke | `ci_recon_audit_gate_smoke.yml` | PR (paths), workflow_dispatch | Smoke für recon_audit_gate Scripts |

### 2.10 Lint / Typecheck / Optional Deps

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Lint | `lint.yml` | push/PR, paths | Ruff Linter |
| Lint Gate (Always Run) | `lint_gate.yml` | PR, merge_group | Lint-Gate (immer Check, intern path-bedingt) |
| typecheck-mypy | `typecheck-mypy.yml` | (siehe Datei) | MyPy |
| typecheck-pyright | `typecheck-pyright.yml` | (siehe Datei) | Pyright |
| optional-deps-gate | `optional-deps-gate.yml` | PR, workflow_dispatch | Optionale Dependencies Importierbarkeit |

### 2.11 Audit / Hygiene / Guards

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Audit | `audit.yml` | schedule (Mo 06:00 UTC), workflow_dispatch | pip-audit, run_audit.sh, Merge-Log-Checks |
| Full Security & Quality Audit (Weekly) | `full_audit_weekly.yml` | schedule, workflow_dispatch | Wöchentlicher Voll-Audit |
| Required Checks Hygiene Gate | `required-checks-hygiene-gate.yml` | PR (paths) | Naming/Contract für Required CI Checks |
| CI / Workflow Dispatch Guard | `ci-workflow-dispatch-guard.yml` | PR (paths) | Validierung workflow_dispatch Guards |
| Merge Log Hygiene | `merge_log_hygiene.yml` | schedule, workflow_dispatch | Merge-Log-Hygiene (Unicode, Bidi, etc.) |
| Merge Logs Sanity | `merge-logs-sanity.yml` | (siehe Datei) | Sanity-Checks Merge Logs |
| Guard reports/ must be ignored | `guard-reports-ignored.yml` | (siehe Datei) | Sicherstellen reports/ ignoriert |
| deps-sync-guard | `deps_sync_guard.yml` | PR, workflow_dispatch | Dependency-Sync |

### 2.12 CI / PR-Signal / Ops

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| CI | `ci.yml` | push/PR/merge_group, schedule, workflow_dispatch | Tests, Stability Smoke, RL v0.1, strategy-smoke, ci-required-contexts-contract |
| PR Merge State Signal | `ci-pr-merge-state-signal.yml` | PR | Informational PR-Merge-Status |
| Ops Doctor Dashboard | `ops_doctor_dashboard.yml` | schedule (Mo 06:30 UTC), workflow_dispatch | Ops-Dashboard |
| Ops Doctor Dashboard (Pages) | `ops_doctor_pages.yml` | schedule (Mo 06:15 UTC), workflow_dispatch | Ops-Pages |

### 2.13 Sonstige

| Workflow | Datei | Trigger | Daten / Zweck |
|----------|--------|---------|----------------|
| Offline Test Suites | `offline_suites.yml` | workflow_dispatch | Daily/Weekly Offline-Suites, Automation-Reports |
| MCP Smoke Preflight | `mcp_smoke_preflight.yml` | PR (paths), workflow_dispatch | MCP Smoke (signal-only) |
| Quarto Smoke Test | `quarto_smoke.yml` | PR (paths), workflow_dispatch | Quarto-Build Smoke |
| Add Issue to Project | `add-to-project.yml` | issues | Issues ins Projekt |

---

## 3. Kurz: Daten → „Wo läuft es?“

| Datentyp | Docker | GitHub (repräsentativ) |
|----------|--------|-------------------------|
| **Knowledge** | – | `knowledge_extras_chromadb.yml` |
| **Health** | – | `test_health.yml`, `test-health-automation.yml` |
| **Strategie** | – | `ci.yml` (strategy-smoke) |
| **Trigger/Automation** | – | `infostream-automation.yml`, `market_outlook_automation.yml` |
| **Evidence / Policy** | – | `evidence_pack_gate.yml`, `policy_critic_gate.yml`, `policy_critic.yml` |
| **Docs** | – | `docs_reference_targets_gate.yml`, `docs_diff_guard_policy_gate.yml`, `docs-token-policy-gate.yml`, Trend/Integrity |
| **VaR/Reports** | – | `var_report_regression_gate.yml` |
| **Trend/AIOps** | – | L4 Critic, Trend Seed, Trend Ledger, Promptfoo Evals |
| **Replay/Recon** | – | `replay_compare_report.yml`, `ci_recon_audit_gate_smoke.yml` |
| **Metriken (Observability)** | Prometheus scrape: shadow_mvs, peak_trade_web, ai_live, peak_trade_metricsd | – |
| **ML/Experiments** | MLflow (compose.yml) | – |
| **Ops-Reports** | Ops Runner (docker-compose.obs.yml) | Ops Doctor, Offline Suites |
| **Trigger Training** | – | Kein Workflow; Scripts/Offline-Suites (siehe Abschnitt 5) |
| **Market Data / Cache** | – | Kein Workflow; Kraken-Pipeline, Parquet-Cache (siehe Abschnitt 5) |
| **Alerts / Telemetrie / Promotion / Kill Switch** | – | Kein Workflow; Laufzeit- und Config-Pfade (siehe Abschnitt 5) |

---

## 4. Referenzen

- Status/Evidence-Contract: `docs/ops/STATUS_MATRIX.md`, `docs/ops/evidence/README.md`
- Docker: `docker/`, `docs/webui/observability/`
- Prometheus Scrape: `docs/webui/observability/PROMETHEUS_SCRAPE_EXAMPLE.yml`, `docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml`
- Workflows: `.github&#47;workflows&#47;*.yml`
- CI Required Checks: `docs/ops/ci_required_checks_matrix_naming_contract.md`
- Evidence Pack: `docs/ai/EVIDENCE_PACK_CI_GATE.md`
- Runtime-Gates (Execution, Live, Safety): `docs/ops/GATES_UND_DATENFLUSS_UEBERSICHT.md`

---

## 5. Datenströme ohne eigenen GitHub-Workflow (Code/Config/Scripts)

Diese Datenströme laufen **nicht** über einen eigenen CI-Workflow, sondern über lokale Scripts, Automations-Suites, Laufzeit oder Config-Pfade. Sie wurden bei der Repo-Durchsuchung ergänzt, damit keine Ströme vergessen werden.

| Datenstrom | Quelle / Eingang | Ausgang / Persistenz | Wo definiert / genutzt |
|------------|------------------|----------------------|-------------------------|
| **Kraken Data Pipeline** | Kraken API (OHLCV) | Normalizer → ParquetCache → `data&#47;cache` | `src/data/kraken_pipeline.py`, `src/data/cache.py`, `config.toml` (data.base_path) |
| **Knowledge Vector/TimeSeries** | RAG, Embeddings | Chroma/Pinecone/Qdrant: `data&#47;chroma_db`, `data&#47;timeseries` (Parquet/InfluxDB) | `config.toml` (knowledge.vector_db, knowledge.timeseries_db) |
| **Trigger Training** | Drill-Sessions, Events | `live_runs&#47;trigger_training_sessions.jsonl`, `reports&#47;trigger_training&#47;meta&#47;` (Operator Meta Report HTML) | `src/trigger_training/session_store.py`, `operator_meta_report.py`, `scripts&#47;generate_operator_meta_report*.py`; Offline-Suite nutzt Drills |
| **Live Audit Export** | Live-Session-Daten | Snapshot-Reports (Script) | `scripts/export_live_audit_snapshot.py` |
| **Alert Pipeline** | Alerts, Escalation | Slack/Email; `data&#47;telemetry&#47;alerts&#47;alerts_history.jsonl`, `logs&#47;telemetry_alerts.jsonl` | `src/live/alert_pipeline.py`, `config/telemetry_alerting.toml` |
| **Execution Events (Beta)** | Orchestrator, Stages | `execution_events.jsonl` (INTENT, RISK_REJECT, ORDER, FILL, …), Ledger | `src/execution/orchestrator.py`; Replay/Compare nutzt `logs&#47;execution&#47;execution_events.jsonl` |
| **AI Events (AI Live)** | Execution-Watch, Events | `PEAK_TRADE_AI_EVENTS_JSONL` / `ai_events.jsonl` → AI Live Exporter (Port 9110) | `scripts&#47;obs&#47;ai_live_exporter.py`, `scripts&#47;ops&#47;tmux_up.sh` <!-- pt:ref-target-ignore --> |
| **Promotion Loop** | Promotion Proposals | `reports&#47;live_promotion`, `reports&#47;promotion_audit&#47;promotion_audit.jsonl` | `config/promotion_loop_config.toml`, `src/governance/promotion_loop/engine.py` |
| **Kill Switch** | State, Audit | `data&#47;kill_switch&#47;state.json`, `data&#47;kill_switch&#47;audit`, `data&#47;kill_switch&#47;metrics.json` | `config/risk/kill_switch.toml` |
| **Model Registry / AI Calls** | Model-Calls | `logs&#47;ai_model_calls.jsonl` | `config/model_registry.toml` (log_destination) |
| **Shadow Quality Events** | Shadow-Pipeline | `reports&#47;shadow_quality_events.jsonl` (Beispiel-Config) | `config/shadow_pipeline_example.toml` |
| **Stage1 (Ops Runner)** | Snapshot/Trend-Scripts | Reports (z. B. aus Container); Stage1-Daily-Snapshot, Stage1-Trend-Report | `scripts/obs/stage1_daily_snapshot.py`, `scripts/obs/stage1_trend_report.py`; Docker `docker-compose.obs.yml` |
| **Offline Suites (Daily/Weekly)** | Automations-Jobs | `reports&#47;automation&#47;daily&#47;`, `reports&#47;automation&#47;weekly&#47;` (JSON/MD) | `scripts/automation/run_offline_daily_suite.py`, `run_offline_weekly_suite.py`; Workflow `offline_suites.yml` lädt Artifacts |
| **InfoStream Quellen** | TestHealth, OfflineRealtime, TriggerTraining, Macro/GeoRisk, Operator-Notes | INFO_PACKET → KI → EVAL_PACKAGE, LEARNING_SNIPPET, INFOSTREAM_LEARNING_LOG.md | `docs/infostream/README.md`, `scripts/generate_infostream_packet.py`, Workflow `infostream-automation.yml` |
| **VaR Backtest / Reports** | Risk-Validation | `reports&#47;var_backtest` | `config/var_backtest.toml` |
| **Scheduler / Live Risk** | Check Scripts | `reports&#47;live&#47;latest_orders.csv` (Beispiel) | `config/scheduler/jobs.toml` |
| **OpenTelemetry (optional)** | Traces/Metrics | OTLP-Export (z. B. Collector) | `src/obs/__init__.py` (init_otel), `pyproject.toml` / requirements (opentelemetry-exporter-otlp) |


## Canonical recovery note
Siehe: `docs/ops/DOCKER_RECOVERY_CANONICAL_STATE.md`

Kanonische Docker-/Prometheus-Pfade:
- `docker/compose.yml`
- `docker/docker-compose.obs.yml`
- `.local/prometheus/prometheus.docker.yml`
- `scripts/docker/run_l3_no_net.sh`

Historische Verweise auf entfernte `docs/webui/observability/DOCKER_COMPOSE_*.yml` sind Legacy.
