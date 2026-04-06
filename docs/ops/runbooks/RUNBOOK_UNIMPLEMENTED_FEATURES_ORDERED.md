# Runbook — Noch nicht implementierte / offene Features (logische Reihenfolge)

> **Zweck:** Überblick über **offene Arbeit** im Repo — **kein** Merge-Gate, sondern **Planungs- und Triage-Hilfe**.  
> **Scope:** NO-LIVE; Priorisierung erfolgt getrennt von Live-Freigaben.  
> **Stand:** Automatisierte Tiefen-Stichprobe (`src&#47;**&#47;*.py`, zentrale `scripts/`, Schlüssel-`tests/`, Doku-Hinweise) — **2026-03-31** (F2 Learning Loop Emitter/Bridge-Normalizer im Runbook als DONE; **F3** in `docs&#47;LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` §12 und `docs&#47;ops&#47;roadmap&#47;CURRENT_FOCUS.md` als optional/parked markiert). Kein vollständiger Beweis, dass **jede** Zeile erfasst ist (Templates, Archiv-`docs/`, generierte Artefakte sind nur stichprobenartig berücksichtigt).

---

## Legende

| Tag | Bedeutung |
|-----|-----------|
| **GAP** | Konkrete Lücke / Follow-up im Produktionspfad |
| **STUB** | Bewusster Platzhalter (Research, Demo, spätere Phase) |
| **DOC** | Nur in Doku als „geplant“ geführt; Code fehlt oder ist minimal |
| **TEST-DEFER** | Test ausdrücklich auf später verschoben |

---

## Stufe A — Foundation & Konfiguration

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| A1 | Zentrale Config-Modulstruktur | DONE | `src/core/config.py` (Facade + `__all__`); Import-Leitfaden [CONFIG_IMPORT_GUIDE.md](../../project_docs/CONFIG_IMPORT_GUIDE.md); Hotspots [A1_CONFIG_MODULE_INVENTORY_2026-03-29.md](../spikes/A1_CONFIG_MODULE_INVENTORY_2026-03-29.md) |
| A2 | R&D-Strategien in Live-Kontext konfigurierbar machen | DONE | `config_validation.py` — Soft-Check prod + `allow_rd_strategy_in_prod` / `rd_strategy_allowlist` |
| A3 | Legacy-Momentum-Aufräumen | DONE | `src/strategies/momentum.py` — modulare `generate_signals`/`add_momentum_indicators` delegieren an `MomentumStrategy`; gemeinsame Logik in `compute_momentum_series` (keine doppelte Signal-Pipeline mehr) |

---

## Stufe B — Daten, Feeds, synthetische Modelle

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| B1 | Fat-Tails / `scipy.stats.t` in synthetischen Modellen | DONE | Student-t-Innovationen via `sample_standardized_student_t` (`student_t_innovations.py`); genutzt in `garch_regime_v0.py`, `offline_realtime_feed.py` — NumPy, kein SciPy-Pflicht im Produktionspfad |
| B2 | `RATIO_ADJUST` für Continuous Contracts | DONE | `build_continuous_contract` + `AdjustmentMethod.RATIO_ADJUST` (`continuous_contract.py`); Smoke `test_build_continuous_ratio_adjust` in `tests/data/continuous/test_continuous_contract.py`; CLI `scripts/markets/build_continuous_contract.py` |
| B3 | Infostream-Collector defensive Defaults | DONE | `collector.py` — Typ-Koercion / Defaults für TestHealth-`summary.json` |

---

## Stufe C — Execution, Orders, Portfolio, Risk

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| C1 | Live-Orderpfad / Exchange (bewusst nicht produktiv) | STUB/GAP | `src&#47;orders&#47;exchange.py` — `LiveOrderExecutor` nur Dry-Run/Design, kein echter Live-Exchange-Client; `src&#47;orders&#47;paper.py` — `ExchangeOrderExecutor`-Stub (`NotImplementedError`). **Abgrenzung:** `src&#47;orders&#47;testnet_executor.py` (Testnet + API) ist ein separater Pfad und **kein** C1-Live-Freigabe |
| C2 | Paper-Orders / Adapter (Teile abstrakt) | DONE | `PaperOrderExecutor` + `PaperMarketContext` in `paper.py`; `OrderExecutor`-Protocol in `base.py`; Tests u. a. `tests/test_orders_smoke.py`. `ExchangeOrderExecutor`-Stub bleibt absichtlich (Live → C1) |
| C3 | Execution-Simple Gates | DONE | `gates.py` — PriceSanity, ResearchOnly, LotSize, MinNotional; `pipeline.py` + `build_execution_pipeline_from_config`; Tests `tests/execution_simple/test_execution_pipeline.py` |
| C4 | Multi-Asset Risk-Enforcement | DONE | `src/risk/enforcement.py` — `max_corr` + DataFrame-Returns (Portfolio-Returns für VaR/CVaR) |
| C5 | Position-Sizing abstrakte Methoden | DONE | `src/core/position_sizing.py` — `BasePositionSizer` / `BasePositionOverlay` (ABC), konkrete Sizer (`NoopPositionSizer`, `FixedSizeSizer`, `FixedFractionSizer`, Overlays/Pipeline); `build_position_sizer_from_config`; Tests `tests/test_position_sizing_overlay_pipeline.py`, `tests/test_vol_regime_overlay_sizer.py` |
| C6 | Portfolio-Basis | DONE | `src/portfolio/base.py` — `PortfolioContext`, `PortfolioStrategy` (Protocol), `BasePortfolioStrategy` (ABC), `make_portfolio_strategy`; Tests `tests/test_portfolio_integration.py`, `tests/test_portfolio_equal_weight.py`, `tests/test_portfolio_vol_target.py`, `tests/test_portfolio_fixed_weights.py` |
| C7 | Core-Risk abstrakt | DONE | `src/core/risk.py` — `BaseRiskManager` (ABC: `reset`, `adjust_target_position`); konkrete Manager (`NoopRiskManager`, `MaxDrawdownRiskManager`, `EquityFloorRiskManager`, `PortfolioVaRStressRiskManager`); `build_risk_manager_from_config`; Tests `tests/test_backtest_smoke.py`, `tests/risk/test_backtest_integration.py`, `tests/test_strategies_research_playground.py` |
| C8 | Broker-Basis (Live) | DONE | `src/live/broker_base.py` — `BaseBrokerClient`, `DryRunBroker`, `PaperBroker`; Tests u. a. `tests/test_preview_live_portfolio.py`, `tests/test_live_portfolio_monitor.py`, `tests/live/test_balance_semantics_guardrail.py` |

---

## Stufe D — Live-Safety, Kill-Switch, Paper/Live-Grenze

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| D1 | Echte Pre/Post-State-Snapshots statt Platzhalter | DONE | `context["recon"]` + `src/ops/recon/context.py` — `SafetyGuard` (Runbook-B) |
| D2 | Kill-Switch Legacy-Adapter | DONE | D2 Slice 3: Adapter entfernt — `TODO_KILL_SWITCH_ADAPTER_MIGRATION.md` |
| D3 | CLI: `exchange_connected` aus echtem System | DONE | `kill-switch health` — `auto` nutzt HTTP-Probe (öffentliche URL, default Kraken) bzw. Env-Overrides; siehe `exchange_probe.py` |

---

## Stufe E — ML / Research / Strategien (Auswahl)

> Einige Strategien unter `src/strategies/` sind **Research-Stubs** oder **OHLCV-Proxys** — hier nur **repräsentative** Einträge; Details in den jeweiligen Modulen/Tests.

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| E1 | Meta-Labeling (ML) vollständig | DONE | `src/research/ml/meta/meta_labeling.py` — `MetaModelSpec`, `apply_meta_model` (trainiert / in-Features-Training), `compute_meta_labels`, `compute_bet_size`, Modell-Fabrik (RandomForest, optional XGBoost); Tests `tests/test_meta_labeling.py` |
| E2 | Triple-Barrier-Labeling | DONE | `src/research/ml/labeling/triple_barrier.py` — `compute_triple_barrier_labels`, `get_vertical_barrier`, `get_horizontal_barriers`, `apply_pnl_stop_loss` (Platzhalter); Tests `tests/test_triple_barrier.py` |
| E3 | Bouchaud / Gatheral Vol-Regime (Research 0/1 OHLCV-Proxys) | DONE | `bouchaud_microstructure_strategy.py`, `vol_regime_overlay_strategy.py` — `generate_signals` deterministisch 0/1; Tests u. a. `tests/test_bouchaud_gatheral_cont_strategies.py`, `tests/test_r_and_d_strategy_gating.py` |
| E4 | Armstrong ECM-Cycle echte Signale | DONE | `src/strategies/armstrong/armstrong_cycle_strategy.py` — `generate_signals` pro Bar: `ArmstrongCycleModel` (`phase_for_date` → `get_position_for_phase`); `is_research_stub=False`; Tests u. a. `tests/strategies/armstrong/`, `tests/test_research_strategies.py` (Armstrong) |
| E5 | Ehlers DSP-Filter / Cycle | DONE | `src/strategies/ehlers/ehlers_cycle_filter_strategy.py` — Minimal-Slice: Ehlers **Super-Smoother** auf `close`, 0/1 wenn `close > smooth`; Fallback Flat bei `len < lookback`; `is_research_stub=False` in Metadaten; Tests u. a. `tests/test_ehlers_lopez_strategies.py`, `tests/test_r_and_d_strategy_gating.py` (Hilbert/Bandpass weiter optional) |
| E6 | López de Prado Meta-Labeling-Pipeline | DONE | `src/strategies/lopez_de_prado/meta_labeling_strategy.py` — delegiert Triple-Barrier an `src/research/ml/labeling/triple_barrier.py` und Meta-Modell-Anwendung an `src/research/ml/meta/meta_labeling.py`; `generate_signals` bleibt in diesem Slice bewusst flat |
| E7 | El Karoui Vol-Regime-Signale | DONE | `src/strategies/el_karoui/el_karoui_vol_model_strategy.py` — `generate_signals` aus `ElKarouiVolModel.regime_series` → `regime_position_map` (0/1); `is_research_stub=False`; Tests u. a. `tests/strategies/el_karoui/`, `tests/test_research_strategies.py` (El-Karoui) |
| E8 | Strategie-Ideen-Templates | DONE | `src/strategies/ideas/` — `template_example.py`, Generator `scripts/new_idea_strategy.py` (snake_case → Klasse, ASCII-CLI); Signale typ. ``{-1,0,1}``, ``validate()``; Tests `tests/strategies/test_idea_strategy_author_ux.py` |
| E9 | Policy-Critic (Regel-Engine) | DONE | `src/governance/policy_critic/rules.py` — `PolicyRule`-ABC; konkrete Regeln (`NoSecretsRule`, `NoLiveUnlockRule`, `ExecutionEndpointTouchRule`, `RiskLimitRaiseRule`, `MissingTestPlanRule`), `ALL_RULES`; Tests `tests/governance/policy_critic/test_rules.py` |

---

## Stufe F — Meta: Infostream, Learning Loop, Promotion

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| F1 | Infostream: robuster Parser, Modell-/Key-Konfiguration | DONE | `evaluator.py` — Block-Extraktion, Fences, Bullets, Risk-Level, `resolve_infostream_model` / `INFOSTREAM_MODEL` |
| F2 | Learning Loop **Bridge** & **Emitter** (Signale) | DONE | **Emitter:** `src&#47;meta&#47;learning_loop&#47;emitter.py` (`emit_learning_snippet`). **Bridge:** `src&#47;meta&#47;learning_loop&#47;bridge.py` (`normalize_patches`). Tests `tests&#47;meta&#47;test_learning_loop_emitter.py`, `tests&#47;meta&#47;test_learning_loop_bridge.py`; Doku `docs&#47;LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` |
| F3 | Learning/Promotion Roadmap v2 | DOC | **Bewusst nicht priorisiert** — optionale v2-Wunschliste in `docs&#47;LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` §12 („v2 Enhancements“); kein Feature-Fix bis Triage |
| F4 | Knowledge / Vector-DB | DONE | `src/knowledge/vector_db.py` — `ChromaDBAdapter` vollständig; `MemoryVectorAdapter` ohne optionale Deps (lexikalisches Scoring); `QdrantAdapter`/`PineconeAdapter`: add/search bewusst offen (Embeddings); Tests `tests/knowledge/test_vector_db_memory.py`, `tests/test_knowledge_integration.py` (Chroma optional) |
| F5 | Execution-Telemetry | DONE | `src/execution/telemetry.py` — `ExecutionEventEmitter`, `JsonlExecutionLogger` (optional `fixed_filename`), `FixedJsonlAppendOnlyWriter`, `CompositeEmitter`, `NullEmitter`; Tests `tests/execution/test_execution_telemetry.py`; Viewer/Health unter `telemetry_viewer.py`, `telemetry_health.py` |
| F6 | New-Listings-Collector-Basis | DONE | `src/research/new_listings/collectors/base.py` — `CollectorContext`, `RawEvent`, `Collector`-Protocol; konkrete Collector u. a. in `src/research/new_listings/collectors/`; Tests u. a. `tests/research/new_listings/test_p1_collector_contract.py`, `tests/research/new_listings/test_p8_ccxt_replay.py` |

---

## Stufe G — Evidence, Reporting, Ops

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| G1 | Evidence-Pack **Multi-Hop-Migrationen** | DONE | `src/ai_orchestration/evidence_pack_schema.py` — `_find_migration_path`, `migration_info.chain`; `tests/ai_orchestration/test_evidence_pack_schema.py` |
| G2 | Evidence-Generator **Redaction**-Regeln | DONE | `src/ai_orchestration/evidence_pack_generator.py` — `_redact_content` auf proposer/critic `content` & `rationale`; `tests/ai_orchestration/test_evidence_pack_generator.py` |
| G3 | Psychology-Heatmap „echte Analyse“ | DONE | `src/reporting/psychology_heuristics.py` — `compute_psychology_heatmap_from_events`, `TriggerTrainingPsychEventFeatures`; Legacy `extract_psychology_scores_from_events` in `psychology_heatmap.py` deprecated; `tests/reporting/test_psychology_heuristics.py` |
| G4 | TestHealth-Runner Historie für Trends | DONE | Trigger-Stats aus `history.json` via `compute_test_health_stats_for_triggers` (`test_health_history.py`) |

---

## Stufe H — Observability-Session (HTTP)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| H1 | HTTP-Server auf Port (Session) | DONE | `src/obs/session.py` — `start_session_http` delegiert an `ensure_metrics_server` in `src/obs/metrics_server.py` (in-process `/metrics`, Mode A/B, Port via Env) |

---

## Stufe I — Tests (explizit verschoben)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| I1 | BacktestEngine **Tracker-Integration** | DONE | `BacktestEngine._safe_tracker_log_params` / `_safe_tracker_log_metrics` in `engine.py` (Legacy + ExecutionPipeline); Fehler im Tracker brechen Backtest nicht ab; `tests/backtest/test_engine_tracking.py` |
| I2 | Strategien **parameter_schema** | DONE | `Param`/`validate_schema` in `parameters.py`; `parameter_schema` auf `MACrossoverStrategy`, `RsiReversionStrategy`, `DonchianBreakoutStrategy`; `tests/strategies/test_parameter_schema.py` |

---

## Stufe J — Scripts & Demo-Daten (operativ niedrig priorisiert)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| J1 | Kraken-/Marktdaten durch echte Quellen ersetzen | STUB | Dummy + **Slice 4:** opt-in Kraken-OHLCV (`load_kraken_ohlcv` / `load_ohlcv` in `scripts/_shared_ohlcv_loader.py` → `src.data.kraken.fetch_ohlcv_df`); CLI ``--ohlcv-source dummy\|kraken`` in `generate_forward_signals.py`, `evaluate_forward_signals.py`, `run_portfolio_backtest_v2.py`. Voller Ersatz aller Dummy-Pfade / weitere Quellen: weiterhin J1 |
| J2 | Optuna-Placeholder weiter ausbauen | DONE | Geliefert auf `main` (PR #2168): `run_study_optuna_placeholder.py` + CI; volle Strategie-Optimierung: `scripts/run_optuna_study.py` |
| J3 | Platzhalter-Inventar regenerieren | TOOL | Lokales Triage-Tool (kein CI-Gate): `python3 scripts/ops/placeholders/generate_placeholder_reports.py` — erzeugt `TODO_PLACEHOLDER_*.md` unter `.ops_local&#47;inventory&#47;` (**nicht committen**). Optional: **`--prefix PATH`** (mehrfach) für repo-relative Teilbäume (**PR #2259**). Smoke: `tests/ops/test_generate_placeholder_reports_smoke.py`. |

### Forward-Pipeline (J1 — Ops-Hinweis)

- **Gemeinsamer OHLCV-Pfad:** `scripts/_shared_ohlcv_loader.py` — `load_dummy_ohlcv` / **J1 Slice 4:** `load_kraken_ohlcv` & `load_ohlcv` (Default: dummy); genutzt von `scripts/generate_forward_signals.py`, `scripts/evaluate_forward_signals.py`, `scripts/run_portfolio_backtest_v2.py` (CLI ``--ohlcv-source``).
- **CLI-Abgleich Loader:** `scripts/_shared_forward_args.py` — dieselbe Quellen-Normalisierung wie ``load_ohlcv`` (``dummy``/``kraken``); ``--ohlcv-source`` ist **case-insensitive** (z. B. ``Kraken``, ``DUMMY``). **PR #2180.** Weiterhin **NO-LIVE** / **STUB** — kein neuer Anbieter.
- **Datenvertrag:** strikte OHLCV-Validierung (`validate_ohlcv`, UTC-stündlicher Index); keine API-Keys/Orders/C1 in diesem Dummy-Pfad.
- **Zeiten:** `as_of` in der Signal-CSV als **ISO-8601 UTC** mit **`Z`** (Generate: `format_as_of_iso_utc`); Evaluation: `parse_as_of_to_utc` beim Einlesen.
- **OHLCV-Fenster:** `generate_forward_signals.py --n-bars` und `evaluate_forward_signals.py --n-bars` **gleich wählen** (Default jeweils 200), damit Dummy-Preisreihe und Signal-Zeitstempel zusammenpassen. Portfolio: `run_portfolio_backtest_v2.py --bars` / **`--n-bars`** (Alias, gleiches `dest`).
- **Kraken (öffentliche OHLCV):** ``--ohlcv-source kraken`` — Netzwerk nötig; Kraken&#47;ccxt typisch **max. 720 Bars** pro Request (`KRAKEN_OHLCV_MAX_BARS`); **größere** ``--n-bars``-Fenster: Pagination im Loader (mehrere Requests, ``use_cache=False`` pro Paginations-Schritt). Generate&#47;Evaluate&#47;Portfolio weiterhin **dieselbe Quelle und gleiches `--n-bars`/`--bars`-Fenster** wählen. **Shortfall:** Es kann weniger History geben als ``--n-bars`` — der Loader setzt Observability (`kraken_bars_shortfall`, Warnung); ``ohlcv_source`` ist normalisiert, Dummy verlangt ``n_bars >= 1``. Vollständiger Wegfall von Dummy-Daten und weitere Anbieter: weiterhin **J1** (STUB) — Zeile J1.
- **Integrationssmoke (Generate/Evaluate):** `tests/test_forward_generate_evaluate_integration_smoke.py`.

#### Operator-Kurzreferenz (J1 Forward, NO-LIVE)

1. **Standard (ohne Netz):** ``--ohlcv-source dummy`` ist der Default — keine API-Keys, keine Broker-Verbindung. Für konsistente Signale&#47;Preise: ``generate_forward_signals`` und ``evaluate_forward_signals`` mit **demselben** ``--n-bars`` aufrufen (Default jeweils 200).
2. **Kraken (öffentliche OHLCV):** ``--ohlcv-source kraken`` — Netzwerk nötig; **dieselbe** Quelle und **dieselbe** Fenstergröße (``--n-bars``) in Generate und Evaluate wählen. Wenn weniger Bars zurückkommen als angefordert: **Shortfall** (Warnung, Meta ``kraken_bars_shortfall``); bei großen Fenstern Pagination im Loader (siehe Bullet „Kraken“ oben).
3. **Portfolio:** ``run_portfolio_backtest_v2.py`` nutzt ``--bars`` &#47; ``--n-bars`` (Alias); bei Abgleich mit Forward-Läufen dieselbe ``--ohlcv-source``-Logik wie oben.
4. **CLI-Hilfe:** gemeinsamer Epilog/Scope über ``scripts/_shared_forward_args.py`` (``--help`` bei den Forward-CLIs).
5. **Smoke (optional):** ``python3 -m pytest tests/test_forward_generate_evaluate_integration_smoke.py -q``
6. **Demo-Pipeline (Stub, offline):** ``bash scripts/dev/run_forward_dummy_pipeline_demo.sh`` — Generate → ``as_of`` so setzen, dass Evaluate mindestens einen Trade auswerten kann (analog Integrationssmoke; reines CLI ohne Anpassung endet oft mit „keine auswertbaren Signale“, wenn ``as_of`` auf der letzten Bar liegt); Artefakte unter ``.ops_local/forward_dummy_pipeline_demo/`` (gitignored). **NO-LIVE.**

---

## Empfohlene Bearbeitungs-Reihenfolge (hochlevel)

1. **Governance & Safety-Draht** (D1–D3) — wenn Live-nah berührt, nur mit Freigabe.  
2. **Foundation** (A1–A3 erledigt) — Steuerbarkeit / Konfig-Klarheit für den Rest.  
3. **Daten-Realismus** (B1–B3 erledigt) — vor harten Research-Claims.  
4. **Evidence/Orchestration** (G1–G4 erledigt) — für auditierbare PRs.  
5. **Infostream** (F1) — Betrieb KI-gestützter Pfade.  
6. **Learning Loop** (F2 erledigt: Emitter + Bridge-Normalizer) — weitere domänenspezifische Anbindungen nur bei Promotion/Learning-Produktpriorität.  
7. **ML/Strategien** (E1–E9) — nach Research-Validierung, nicht blind implementieren; **E3–E7** Signal-Slices in der Registry sind umgesetzt; **E8** ist die Autoren-Sandbox (Idea-Templates/Generator), nicht die produktive Strategy-Library.  
8. **Tests** (I1–I2 erledigt) — wenn Core stabil.  
9. **Scripts/Demos** (J) — wenn operative Daten angebunden werden.

---

## Verwandte Dokumente

- [Finish Plan](../roadmap/FINISH_PLAN.md) — DoD & PR-Slices (PR 6–8 u. a. **landed**).  
- [Current focus](../roadmap/CURRENT_FOCUS.md) — menschlicher „wo stehen wir“.  
- [Chat-led open features (Triage-Prozess)](./RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — **wie** ihr Sessions führt (nicht nur diese Liste).  
- [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) — Navigation.

---

## Anhang — Inventar bei Bedarf neu erzeugen

J3 ist ein **lokales TOOL** zur Übersicht über TODO-/Placeholder-Marker im Tree (kein Live-/Trading-Bezug). Typische Nutzung:

```bash
python3 scripts/ops/placeholders/generate_placeholder_reports.py
python3 scripts/ops/placeholders/generate_placeholder_reports.py --help
# Nur ausgewählte Teilbäume (z. B. Code vs. Docs getrennt triagieren):
python3 scripts/ops/placeholders/generate_placeholder_reports.py --prefix src/ --prefix scripts/
```

Reports landen unter **`.ops_local&#47;inventory&#47;`** (`TODO_PLACEHOLDER_INVENTORY.md`, `TODO_PLACEHOLDER_TARGET_MAP.md`) — Verzeichnis ist git-ignoriert; **nicht committen**. Optional: `--output-dir DIR` für eine andere Ausgabe (z. B. Tests); bei `--prefix` vermerkt die Inventar-Datei die gewählte **Scan scope** und die Target-Map nutzt dieselben Präfixe für die Triage-Slices (**PR #2259**).

(Ausgabe kann als **Ergänzung** zu dieser manuell kuratierten Liste dienen.)
