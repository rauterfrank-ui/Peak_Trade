> **Historisch / Referenz** — Nicht kanonisch. Snapshot aus Read-only Repo-Audit.  
> **Origin:** Wave 16 Integration, ursprünglich `docs&#47;REPO_AUDIT_REPORT.md`.   <!-- pt:ref-target-ignore -->
> **Canonical:** [docs/INDEX.md](../INDEX.md), [docs/audit/README.md](README.md)

---

# Peak_Trade Repository Audit Report

**Stand:** 2026-03-10  
**Modus:** Read-only Audit

---

## 1. Repo Inventory

### 1.1 Top-Level Verzeichnisstruktur

| Verzeichnis | Top-Level Subdirs |
|-------------|-------------------|
| **src/** | `ai`, `ai_orchestration`, `aiops`, `analytics`, `autonomous`, `backtest`, `core`, `data`, `docs`, `exchange`, `execution`, `execution_pipeline`, `execution_simple`, `experiments`, `features`, `forward`, `governance`, `infra`, `ingress`, `knowledge`, `live`, `live_eval`, `macro_regimes`, `market_sentinel`, `markets`, `meta`, `notifications`, `obs`, `observability`, `ops`, `orders`, `peak_trade`, `portfolio`, `regime`, `reporting`, `research`, `risk`, `risk_layer`, `scheduler`, `sim`, `strategies`, `sweeps`, `theory`, `trigger_training`, `utils`, `webui` |
| **tests/** | `ai`, `ai_orchestration`, `aiops`, `backtest`, `ci`, `data`, `docs`, `e2e`, `exchange`, `execution`, `execution_simple`, `experiments`, `fixtures`, `golden`, `governance`, `infra`, `ingress`, `integration`, `live`, `markets`, `meta`, `notifications`, `obs`, `observability`, `ops`, `orphans`, `p10`–`p140`, `replay_pack`, `reporting`, `research`, `risk`, `risk_layer`, `scripts`, `sim`, `strategies`, `strategy`, `trigger_training`, `utils`, `validation`, `wave3`–`wave6`, `webui` + viele `test_*.py` Root-Dateien |
| **scripts/** | `ai`, `aiops`, `audit`, `automation`, `ci`, `data`, `dev`, `docker`, `execution`, `governance`, `live`, `markets`, `obs`, `ops`, `rescue`, `research`, `risk`, `run`, `utils`, `wave3`–`wave6`, `workflows` + ~150+ Python-Skripte, ~380 Shell-Skripte |
| **docs/** | `_worklogs`, `adr`, `ai`, `analysis`, `architecture`, `audit`, `ci`, `deep_research`, `dev`, `execution`, `features`, `governance`, `infra`, `infostream`, `learning_promotion`, `macro`, `mindmap`, `ops`, `position_sizing`, `project_docs`, `reporting`, `risk`, `roadmap`, `runbooks`, `shadow`, `stability`, `strategies`, `tracking`, `trigger_training`, `webui` + ~170 MD-Dateien im Root |

### 1.2 Zählungen

| Kategorie | Anzahl |
|-----------|--------|
| **Python-Module in src/** | 806 |
| **Test-Dateien in tests/** | 803 (test_*.py / *_test.py) |
| **Python-Skripte in scripts/** | 283 |
| **Shell-Skripte in scripts/** | 384 |

---

## 2. Main Entry Points

### 2.1 run_*.py (67 Dateien)

| Kategorie | Beispiele |
|----------|----------|
| **Backtest** | `run_backtest.py`, `run_simple_backtest.py`, `run_portfolio_backtest.py`, `run_registry_portfolio_backtest.py`, `run_walkforward_backtest.py`, `run_donchian_realistic.py`, `run_ma_realistic.py`, `run_momentum_realistic.py`, `run_rsi_realistic.py` |
| **Execution** | `run_execution_session.py`, `run_execution_simple_dry_run.py`, `run_shadow_execution.py`, `run_shadow_paper_session.py` |
| **Live/Testnet** | `run_live_beta_drill.py`, `run_live_dry_run_drills.py`, `run_testnet_session.py` |
| **Research/Sweep** | `run_experiment_sweep.py`, `run_strategy_sweep.py`, `run_sweep.py`, `run_sweep_pipeline.py`, `run_sweep_strategy.py`, `run_research_golden_path.py`, `run_idea_strategy.py`, `run_strategy_from_config.py` |
| **Portfolio** | `run_portfolio_backtest.py`, `run_portfolio_backtest_v2.py`, `run_portfolio_robustness.py`, `run_portfolio_smoke.py`, `run_full_portfolio.py` |
| **Risk** | `run_risk_stress_report.py`, `run_kupiec_pof.py`, `run_component_var_report.py`, `run_stress_tests.py`, `run_monte_carlo_robustness.py` |
| **AI/Ops** | `run_autonomous_workflow.py`, `run_learning_apply_cycle.py`, `run_policy_critic.py`, `run_market_scan.py`, `run_scheduler.py`, `run_optuna_study.py`, `run_promotion_proposal_cycle.py` |
| **Sonstige** | `run_forward_signals.py`, `run_offline_realtime_ma_crossover.py`, `run_offline_trigger_training_drill_example.py`, `run_web_dashboard.py`, `run_test_health_profile.py`, `run_layer_smoke_with_evidence_pack.py`, `run_strategy_switch_sanity_check.py` |

### 2.2 serve_*.py

| Datei | Beschreibung |
|-------|---------------|
| `serve_live_dashboard.py` | Live-Dashboard-Server |

### 2.3 pyproject.toml

- **Keine** `[project.scripts]` oder `entry_points` definiert.
- Entry Points werden über direkte Skript-Aufrufe (`python scripts&#47;run_*.py`) genutzt.

### 2.4 Makefile Targets (relevante Entry Points)

| Target | Beschreibung |
|--------|--------------|
| `test` | `pytest -q` |
| `lint` | `ruff check .` |
| `governance-gate` | AI-Matrix vs. Registry Konsistenz |
| `governance-validate` | `validate_ai_matrix_vs_registry.py --level P2` |
| `mlflow-up` / `mlflow-down` | MLflow Docker Compose |
| `report-smoke` | Quarto Smoke Report |
| `mlog` / `mlog-auto` | Merge-Log PR-Workflow |
| `wave3-*`, `wave4-*`, `wave5-*`, `wave6-*` | AI/Observability Smoke-Tests |
| `research-new-listings-smoke` | Research New Listings CLI |
| `ai-policy-audit-smoke` | AI Policy CLI |

---

## 3. Feature Matrix

| Feature | Code | Tests | Docs | CI |
|--------|------|-------|------|-----|
| **backtest** | ✅ `src&#47;backtest&#47;`, `run_backtest.py`, `run_simple_backtest.py`, etc. | ✅ `tests&#47;backtest&#47;`, viele `test_*backtest*.py` | ✅ BACKTEST_ENGINE.md, PHASE_*.md | ✅ ci.yml, var_report_regression_gate |
| **execution** | ✅ `src&#47;execution&#47;`, `src&#47;execution_pipeline&#47;`, `src&#47;execution_simple&#47;` | ✅ `tests&#47;execution&#47;` | ✅ PHASE_16A, ORDER_LAYER_SANDBOX, etc. | ✅ prbg-execution-evidence, shadow_paper_smoke |
| **live** | ✅ `src&#47;live&#47;`, `serve_live_dashboard.py`, `live_ops.py`, `live_monitor_cli.py` | ✅ `tests&#47;live&#47;`, `test_live_*.py` | ✅ LIVE_*, PHASE_33, 48, 49, 71–85 | ✅ prbd-live-readiness, prbi-live-pilot-scorecard |
| **shadow** | ✅ `src&#47;data&#47;shadow&#47;`, `run_shadow_execution.py`, `run_shadow_paper_session.py` | ✅ `test_shadow_execution.py`, etc. | ✅ PHASE_24, 31, 32, shadow/ | ✅ shadow_paper_smoke, prbe-shadow-testnet-scorecard |
| **paper** | ✅ `src&#47;execution&#47;paper&#47;`, `paper_trade_from_orders.py` | ✅ `test_*paper*.py` | ✅ PHASE_31, 32 | ✅ paper_session_audit_evidence, ci-scheduled-paper |
| **testnet** | ✅ `run_testnet_session.py`, `testnet_orchestrator_cli.py`, `src&#47;exchange&#47;` | ✅ `test_testnet_*.py`, `test_run_testnet_session.py` | ✅ PHASE_35, 37, 38, LIVE_TESTNET_* | ✅ prbj-testnet-exec-events |
| **AI/orchestration** | ✅ `src&#47;ai&#47;`, `src&#47;ai_orchestration&#47;`, `src&#47;aiops&#47;` | ✅ `tests&#47;ai&#47;`, `tests&#47;ai_orchestration&#47;`, `tests&#47;aiops&#47;` | ✅ AUTONOMOUS_*, governance/ai_autonomy | ✅ aiops-*, policy_critic_gate, ai-model-cards-validate |
| **governance** | ✅ `src&#47;governance&#47;`, `run_policy_critic.py` | ✅ `tests&#47;governance&#47;` | ✅ GOVERNANCE_*, PHASE_25, 83 | ✅ policy_critic_gate, governance-gate (Makefile) |
| **risk** | ✅ `src&#47;risk&#47;`, `src&#47;risk_layer&#47;` | ✅ `tests&#47;risk&#47;`, `tests&#47;risk_layer&#47;` | ✅ LIVE_RISK_LIMITS, risk/, RUNBOOKS | ✅ var_report_regression_gate |
| **observability** | ✅ `src&#47;obs&#47;`, `src&#47;observability&#47;` | ✅ `tests&#47;obs&#47;`, `tests&#47;observability&#47;` | ✅ OBSERVABILITY_AND_MONITORING_PLAN | ✅ test_health, ops_doctor_* |
| **ops-cockpit** | ✅ `src&#47;webui&#47;ops_cockpit.py`, `&#47;api&#47;ops-cockpit` | ✅ `tests&#47;webui&#47;test_ops_cockpit.py` | ✅ docs/ops/runbooks/webui_ops_cockpit*.md | ✅ (via webui/ci) |

---

## 4. Docs vs. Code: „Exists in Docs Only“ vs. „Exists in Code Only“

### 4.1 Exists in Docs Only (dokumentiert, Code fehlt oder ist Placeholder)

| Feature | Docs-Referenz | Code-Status |
|---------|---------------|-------------|
| **Feature-Engine / ECM** | FEHLENDE_FEATURES, trading_bot_notes | `src&#47;features&#47;` nur Placeholder |
| **ECM-Fenster / ECM-Features** | FEHLENDE_FEATURES | Nicht implementiert |
| **Theory (GBM, Heston, Option Pricing)** | FEHLENDE_FEATURES | `src&#47;theory&#47;` nur Placeholder |
| **Sentiment (News/Makro/Onchain)** | trading_bot_notes | Nicht implementiert |
| **Orderbuch-/Tickdaten** | trading_bot_notes | Nicht implementiert |
| **Echte Live-Orders** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Bewusst blockiert (SafetyGuard) |
| **Testnet ohne Dry-Run** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Bewusst blockiert |
| **Multi-Exchange** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Nur Kraken |
| **Web-Dashboard Auth/POST/PUT/DELETE** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Read-only |
| **SSE/WebSocket** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Nur Polling |
| **Real-Time-WebSocket-Streams** | PEAK_TRADE_V1_KNOWN_LIMITATIONS | Nur REST/Polling |

### 4.2 Exists in Code Only (Code vorhanden, Docs minimal/verstreut)

| Bereich | Code | Docs |
|---------|------|------|
| **ops/pXX** (p50–p99, p104, etc.) | Viele `src&#47;ops&#47;pXX&#47;` Module | Verstreut in docs/ops/, analysis/pXX/ |
| **tests/orphans** | `test_keep_modules_importable.py` | Kaum dokumentiert |
| **wave3–wave6** | `scripts&#47;wave3&#47;`–`wave6&#47;` | docs/ops/WAVE*_*.md |
| **aiops p4c, p5a, p6, p7** | `src&#47;aiops&#47;p4c&#47;`, etc. | docs/analysis/p105, p64, etc. |

---

## 5. Dead / Orphan Areas

### 5.1 Leere oder Placeholder-Module (keine Imports)

| Modul | Inhalt | Importe |
|-------|--------|---------|
| `src&#47;features&#47;` | Placeholder „wird später mit ECM-Features gefüllt“ | ❌ Keine |
| `src&#47;theory&#47;` | Placeholder „für spätere theoretische Modelle“ | ❌ Keine |
| `src&#47;sim&#47;` | Nur `"""Simulation modules."""` (Root); `sim.paper` wird genutzt | ⚠️ Root leer, Submodul aktiv |

### 5.2 Minimale __init__.py (≤2 Zeilen, potenziell Orphan)

- `src&#47;research&#47;new_listings&#47;collectors&#47;__init__.py` (0 Zeilen)
- `src&#47;ingress&#47;cli&#47;__init__.py` (0 Zeilen)
- `src&#47;observability&#47;nowcast&#47;__init__.py` (0 Zeilen) – **wird importiert** (decision_context_v1)
- Viele `src&#47;research&#47;pXX&#47;`, `src&#47;aiops&#47;pXX&#47;`, `src&#47;ops&#47;pXX&#47;` mit 1-Zeiler

### 5.3 Explizit als Orphan behandelte Module (tests/orphans)

`tests&#47;orphans&#47;test_keep_modules_importable.py` prüft Importierbarkeit von:

- `src.ai_orchestration.switch_layer_hook_v1`
- `src.aiops.p4c.capsule_schema`
- `src.ops.ai_execution_gate`
- `src.reporting.portfolio_psychology`
- `src.data.shadow.jsonl_logger`

### 5.4 src/peak_trade/

- `src&#47;peak_trade&#47;__init__.py`: „namespace for CLI entry points“ (1 Zeile)
- `src&#47;peak_trade&#47;governance&#47;__init__.py`: „Governance CLI and validators“ (1 Zeile)
- Keine `console_scripts` in pyproject.toml → Nutzung über `python -m src.research.new_listings` etc.

### 5.5 src/markets/

- Kein Root-`__init__.py` sichtbar; `src&#47;markets&#47;cme&#47;` wird von `scripts&#47;markets&#47;`, `tests&#47;markets&#47;`, `tests&#47;data&#47;continuous&#47;` importiert.
- CME-spezifisch; Spot-Fokus laut Limitations.

---

## 6. CI / Workflows (Auszug)

| Workflow | Zweck |
|----------|-------|
| `ci.yml` | Haupt-CI |
| `test_health.yml` | Test-Health |
| `lint.yml`, `lint_gate.yml` | Linting |
| `typecheck-pyright.yml`, `typecheck-mypy.yml` | Typen |
| `shadow_paper_smoke.yml` | Shadow/Paper |
| `policy_critic_gate.yml`, `policy_critic.yml` | Governance |
| `var_report_regression_gate.yml` | Risk/VaR |
| `evidence_pack_gate.yml` | Evidence Pack |
| `docs_*` | Docs-Integrität |
| `aiops-*`, `prbj-*`, `prbd-*`, `prbi-*`, `prbg-*` | AI/Ops/Execution/Live |

---

## 7. Zusammenfassung

| Metrik | Wert |
|--------|------|
| Python-Module (src) | 806 |
| Test-Dateien | 803 |
| Python-Skripte | 283 |
| Shell-Skripte | 384 |
| run_*.py Entry Points | 67 |
| serve_*.py Entry Points | 1 |
| Tote/Placeholder-Module | `features`, `theory` |
| Orphan-Tests | `tests&#47;orphans&#47;test_keep_modules_importable.py` |
| CI-Workflows | 68 |

Die Feature-Matrix zeigt eine gute Abdeckung von Backtest, Execution, Live, Shadow, Paper, Testnet, AI/Orchestration, Governance, Risk, Observability und Ops-Cockpit. Dokumentierte Lücken (Feature-Engine, Theory, Sentiment, Multi-Exchange, etc.) sind in `FEHLENDE_FEATURES_PEAK_TRADE.md` und `PEAK_TRADE_V1_KNOWN_LIMITATIONS.md` beschrieben.
