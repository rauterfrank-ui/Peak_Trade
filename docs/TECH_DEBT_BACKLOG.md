# Tech-Debt Backlog

Dieses Dokument sammelt bewusst aufgeschobene Tech-Debt-Items und größere TODOs.

> **Hinweis:** Diese Items sind bewusst nicht in v1.0 enthalten, werden aber für zukünftige Phasen dokumentiert.

---

## Kategorie A – Code-Struktur / Refactors

### Backtest-Engine: Portfolio-Allocation-Methoden

- [ ] `risk_parity` Allocation-Methode implementieren
  - Fundstelle: `src&#47;backtest&#47;engine.py` (Zeile 1318) (illustrative)
  - Kontext: Portfolio-Allocation-Methode für gleiches Risk-Level pro Strategie
  - Vorschlag: Implementierung basierend auf Volatility/Risk-Metriken
  - Status: implemented (Code PR #1030, merge `af02a6d5`) + Docs/Evidence PR #1031 (merge `c6fc8036`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_A_ALLOC_20260128.md`
  - Fundstellen: `src/backtest/engine.py`, `tests/backtest/test_engine_allocations.py`, `tests/backtest/test_engine_two_pass_allocation.py`

- [ ] `sharpe_weighted` Allocation-Methode implementieren
  - Fundstelle: `src&#47;backtest&#47;engine.py` (Zeile 1319) (illustrative)
  - Kontext: Portfolio-Allocation basierend auf historischer Sharpe-Ratio
  - Vorschlag: Benötigt historische Backtests als Input
  - Status: implemented (Code PR #1030, merge `af02a6d5`) + Docs/Evidence PR #1031 (merge `c6fc8036`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_A_ALLOC_20260128.md`
  - Fundstellen: `src/backtest/engine.py`, `tests/backtest/test_engine_allocations.py`, `tests/backtest/test_engine_two_pass_allocation.py`

### Walk-Forward: Parameter-Optimierung

- [ ] Parameter-Optimierung auf Train-Daten implementieren
  - Fundstelle: `src&#47;backtest&#47;walkforward.py` (Zeile 387) (illustrative)
  - Kontext: Train-Backtest für spätere Optimierung vorbereitet, aber noch nicht aktiv
  - Vorschlag: Integration mit Sweep-System für automatische Parameter-Optimierung
  - Status: implemented (Code PR #1028, merge `f37535c6`) + Docs/Evidence PR #1029 (merge `db4e71bf`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_A_WF_20260128.md`
  - Fundstellen: `src/backtest/walkforward.py`, `tests/backtest/test_walkforward_optimization.py`

### Legacy-API Cleanup

- [ ] Legacy-Funktionen in `macd.py` entfernen
  - Fundstelle: `src&#47;strategies&#47;macd.py` (Zeile 232) (illustrative)
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf MACDStrategy (OOP) umgestellt sind, dann entfernen

- [ ] Legacy-Funktionen in `bollinger.py` entfernen
  - Fundstelle: `src&#47;strategies&#47;bollinger.py` (Zeile 237) (illustrative)
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf BollingerBandsStrategy (OOP) umgestellt sind, dann entfernen

- [x] `run_full_portfolio.py`: Legacy-`*_signals`-Imports auf kanonischen `load_strategy()`-Pfad migriert
  - Fundstelle: `scripts/run_full_portfolio.py`
  - Kontext: Script importierte entfernte Legacy-Exports (`ma_crossover_signals` u.a.) und war beim Import gebrochen
  - Status: closed (PR feat/run-full-portfolio-load-strategy-migration-v1; offline Tests `tests/scripts/test_run_full_portfolio_load_strategy_v1.py`)
  - Fundstellen: `scripts/run_full_portfolio.py`, `src/strategies/__init__.py` (`load_strategy`), `tests/scripts/test_run_full_portfolio_load_strategy_v1.py`

- [x] `demo_execution_backtest.py`: paralleler `get_strategy_fn()`/`strategy_map` auf kanonischen `load_strategy()`-Pfad migriert
  - Fundstelle: `scripts/demo_execution_backtest.py`
  - Kontext: Hardcodierte `strategy_map` duplizierte STRATEGY_REGISTRY; Namensdrift (`breakout_donchian` vs. `breakout`, `momentum` vs. `momentum_1h`)
  - Status: closed (PR feat/demo-execution-backtest-load-strategy-migration-v1; offline Tests `tests/scripts/test_demo_execution_backtest_load_strategy_v1.py`)
  - Fundstellen: `scripts/demo_execution_backtest.py`, `src/strategies/__init__.py` (`load_strategy`), `tests/scripts/test_demo_execution_backtest_load_strategy_v1.py`

---

## Kategorie B – Daten-Integration & Exchange

### Echte Daten-Adapter

- [ ] Echten Daten-Adapter in `live_ops.py` integrieren
  - Fundstelle: `scripts&#47;live_ops.py` (Zeile 189) (illustrative)
  - Kontext: Aktuell Dummy-Implementation, später mit echtem Daten-Adapter (Kraken API etc.) ersetzen
  - Vorschlag: Integration mit bestehender Kraken-Integration in `src&#47;data&#47;kraken.py`

- [ ] Echten Daten-Adapter in `preview_live_orders.py` integrieren
  - Fundstelle: `scripts&#47;preview_live_orders.py` (Zeile 157) (illustrative)
  - Kontext: Aktuell Dummy-Implementation
  - Vorschlag: Integration mit bestehender Kraken-Integration

- [ ] Echte Kraken-Daten in `run_portfolio_backtest.py` verwenden
  - Fundstelle: `scripts&#47;run_portfolio_backtest.py` (Zeile 119) (illustrative)
  - Kontext: Aktuell Dummy-Daten, später mit echten Kraken-Daten ersetzen
  - Vorschlag: Integration mit `src&#47;data&#47;kraken.py`

- [ ] Echten Exchange-Client in `preview_live_portfolio.py` integrieren
  - Fundstelle: `scripts&#47;preview_live_portfolio.py` (Zeile 96) (illustrative)
  - Kontext: Später echten Exchange-Client integrieren (z.B. Kraken)
  - Vorschlag: Integration mit `src&#47;exchange&#47;kraken_testnet.py` oder `src&#47;exchange&#47;ccxt_client.py`

- [ ] Timeframe aus Daten ableiten in `run_shadow_execution.py`
  - Fundstelle: `scripts&#47;run_shadow_execution.py` (Zeile 502) (illustrative)
  - Kontext: Timeframe aktuell hardcoded, sollte aus Daten abgeleitet werden
  - Vorschlag: Automatische Erkennung aus DataFrame-Index oder Config
  - Status: implemented (Code PR #1021, merge `3d6aee01`) + Docs/Evidence PR #1022 (merge `7b16a509`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_B_20260128.md`
  - Fundstellen: `scripts/run_shadow_execution.py`, `tests/test_timeframe_infer.py`

---

## Kategorie C – Features / Nice-to-have

### Vollständige Implementierungen

- [ ] Vollständige Stress-Test-Implementierung
  - Fundstelle: `src&#47;experiments&#47;stress_tests.py` (Zeile 389) (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry für automatisches Laden
  - Status: implemented (Code PR #1023, merge `d218e201`) + Docs/Evidence PR #1024 (merge `acab43a1`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_C_20260128.md`
  - Fundstellen: `src/experiments/equity_loader.py`, `src/experiments/stress_tests.py`, `tests/experiments/test_equity_loader.py`

- [ ] Vollständige Monte-Carlo-Implementierung
  - Fundstelle: `src&#47;experiments&#47;monte_carlo.py` (Zeile 303) (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry
  - Status: implemented (Code PR #1023, merge `d218e201`) + Docs/Evidence PR #1024 (merge `acab43a1`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_C_20260128.md`
  - Fundstellen: `src/experiments/equity_loader.py`, `src/experiments/monte_carlo.py`, `tests/experiments/test_equity_loader.py`

- [ ] Vollständige Monte-Carlo-Robustness-Implementierung
  - Fundstelle: `scripts&#47;run_monte_carlo_robustness.py` (Zeile 139) (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry
  - Status: implemented (feat/monte-carlo-equity-loader-integration-v1) — `load_returns_for_config` nutzt kanonischen `equity_loader`; kein stiller Dummy-Fallback im Standardpfad; Synthetic nur via `--use-dummy-data`
  - Fundstellen: `scripts/run_monte_carlo_robustness.py`, `src/experiments/equity_loader.py`, `tests/scripts/test_run_monte_carlo_robustness_equity_loader_integration_v1.py`

- [ ] Vollständige Portfolio-Robustness-Returns-Loader-Implementierung
  - Fundstelle: `scripts&#47;run_portfolio_robustness.py` (Zeile 99) (illustrative)
  - Kontext: Sweep-basierter Returns-Loader mit stiller None-Rückgabe bei Ladefehlern
  - Vorschlag: Kanonischen `equity_loader` via `load_returns_for_config` nutzen; fail-closed wie Monte-Carlo (#4215)
  - Status: implemented (feat/portfolio-robustness-equity-loader-fail-closed-v1) — `build_returns_loader` nutzt kanonischen `equity_loader`; kein stiller None-Fallback; fehlende Komponenten fail-closed
  - Fundstellen: `scripts/run_portfolio_robustness.py`, `src/experiments/equity_loader.py`, `tests/scripts/test_run_portfolio_robustness_equity_loader_integration_v1.py`

### Registry-Logging

- [x] Registry-Logging in `demo_order_pipeline_backtest.py` implementieren
  - Fundstelle: `scripts&#47;demo_order_pipeline_backtest.py` (illustrative)
  - Kontext: Registry-Logging für automatisches Tracking via `log_backtest_result` (fail-closed `load_strategy`, kanonische Registry-Hints)

- [x] Legacy Demo-/Research-Scripts: direkte `generate_signals`-Imports auf kanonischen `load_strategy()`-Pfad migriert
  - Fundstellen: `scripts/run_simple_backtest.py`, `scripts/demo_portfolio_backtest.py`, `scripts/demo_backtest_with_risk.py`, `scripts/demo_complete_pipeline.py`, `scripts/run_momentum_realistic.py`
  - Kontext: Fünf Scripts umgingen `load_strategy()` mit direktem Modul-Import (`ma_crossover`, `momentum`); kanonische Keys `ma_crossover`, `momentum_1h`
  - Status: closed (PR feat/legacy-demo-scripts-load-strategy-migration-v1; offline Tests `tests/scripts/test_legacy_demo_scripts_load_strategy_v1.py`)

- [x] Realistic Backtest Runners: direkte OOP-Klassenimporte auf kanonischen `load_strategy()`-Pfad migriert
  - Fundstellen: `scripts/run_ma_realistic.py`, `scripts/run_donchian_realistic.py`, `scripts/run_rsi_realistic.py`
  - Kontext: Drei `*_realistic.py`-Scripts importierten `MACrossoverStrategy`, `DonchianBreakoutStrategy`, `RsiReversionStrategy` direkt; `run_ma_realistic.py` hatte fail-open return bei Strategie-Fehler
  - Status: closed (PR feat/realistic-backtest-runners-load-strategy-migration-v1; offline Tests `tests/scripts/test_realistic_backtest_runners_load_strategy_v1.py`)
  - Kanonische Keys: `ma_crossover`, `breakout_donchian`, `rsi_reversion`

---

## Kategorie D – Tests & Infra

### Pandas FutureWarnings (Phase 59)

- [ ] Pandas `.fillna` Downcasting Warnings beheben
  - Fundstelle: Diverse `src&#47;strategies&#47;*.py`
  - Kontext: `.shift(1).fillna(False)` Pattern löst FutureWarning in pandas 2.x aus
  - Status: implemented in PR #1036 (merge `7394f78c`, mergedAt 2026-01-28T05:58:36Z)
  - Aktueller Status: Warning behoben; keine pandas-Downcasting `FutureWarning` Filter mehr nötig
  - Vorschlag: (historisch) Bei pandas 3.0 Migration auf `.astype(bool)` umstellen
  - Priorität: Niedrig (erledigt; Regression-Test deckt Verhalten ab)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_D_20260128.md`
  - Fundstellen: `src/strategies/trend_following.py`, `src/strategies/mean_reversion.py`, `src/strategies/my_strategy.py`, `src/strategies/vol_breakout.py`, `src/strategies/mean_reversion_channel.py`, `src/strategies/ecm.py`, `tests/test_fillna_downcasting_regression.py`

### test_live_web.py Collection Error

- [ ] test_live_web.py reparieren oder entfernen
  - Fundstelle: `tests&#47;test_live_web.py`
  - Kontext: Fehler bei Test-Collection (vermutlich fehlende Dependency)
  - Aktueller Status: In pytest-Runs mit `--ignore=tests&#47;test_live_web.py` übersprungen
  - Vorschlag: Prüfen, ob Test noch benötigt wird, sonst entfernen
  - Priorität: Niedrig

---

## Kategorie E – Performance & Scale

### Data-Layer Caching

- [ ] Data-Layer Caching für große Research-Sweeps verbessern
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: Caching-Layer weiter ausbauen / mehr Reuse zwischen Runs
  - Vorschlag: Parquet-Format für persistierte Daten nutzen (falls noch nicht geschehen)

### Plot-Generation

- [ ] Plot-Generation optional machen für Performance-Benchmarks
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: `--no-plots` Flag für reine Performance-Benchmarks
  - Vorschlag: Asynchrone Plot-Generierung (später)
  - Status: implemented (Code PR #1025, merge `1cf7c45c`) + Docs/Evidence PR #1026 (merge `597b2703`)
  - Evidence: `docs/ops/evidence/EV_TECH_DEBT_E_20260128.md`
  - Fundstellen: `scripts/run_strategy_from_config.py`, `scripts/run_portfolio_backtest.py`, `src/backtest/reporting.py`

### Logging

- [ ] Logging in großen Research-Runs weiter drosseln oder Batch-weisen Output einführen
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: „Benchmark-/Silent"-Mode für Logs
  - Vorschlag: Batch-weiser Output statt einzelner Log-Zeilen

### pandas-Optimierungen

- [ ] pandas-Operationen optimieren (Vektorization, Reduzierung von Zwischenkopien)
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: Vektorization & Reduzierung von Zwischenkopien prüfen
  - Vorschlag: Nutzung von `numba` oder `cython` für kritische Loops (später)

---

## Governance / static crosslink (reference only)

- CI_AUDIT reciprocal guard: [`docs/ops/CI_AUDIT_KNOWN_ISSUES.md`](ops/CI_AUDIT_KNOWN_ISSUES.md) — § Tech-Debt Top-3 Runbook/Backlog CI_AUDIT ↔ DOCS_TRUTH_MAP static crosslink
- DOCS_TRUTH_MAP chronicle: [`docs/ops/registry/DOCS_TRUTH_MAP.md`](ops/registry/DOCS_TRUTH_MAP.md)
- Runbooks index: [`docs/ops/runbooks/README.md`](ops/runbooks/README.md)
- Operator runbook: [`docs/ops/runbooks/RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md`](ops/runbooks/RUNBOOK_TECH_DEBT_TOP3_ROI_FINISH.md) — **non-authorizing**; `TECH_DEBT_TOP3_NAVIGATION_FAIL_CLOSED=true`; backlog status semantics unchanged

---

**Hinweis:** Diese Items werden bei Bedarf in zukünftigen Phasen angegangen. Priorisierung erfolgt basierend auf Nutzer-Feedback und Projekt-Roadmap.
