# Runbook — Noch nicht implementierte / offene Features (logische Reihenfolge)

> **Zweck:** Überblick über **offene Arbeit** im Repo — **kein** Merge-Gate, sondern **Planungs- und Triage-Hilfe**.  
> **Scope:** NO-LIVE; Priorisierung erfolgt getrennt von Live-Freigaben.  
> **Stand:** Automatisierte Tiefen-Stichprobe (`src&#47;**&#47;*.py`, zentrale `scripts/`, Schlüssel-`tests/`, Doku-Hinweise) — **2026-03-27**. Kein vollständiger Beweis, dass **jede** Zeile erfasst ist (Templates, Archiv-`docs/`, generierte Artefakte sind nur stichprobenartig berücksichtigt).

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
| A1 | Zentrale Config-Modulstruktur | GAP | `src/core/config.py` — Kommentar „central config module“ |
| A2 | R&D-Strategien in Live-Kontext konfigurierbar machen | GAP | `src/governance/config_validation.py` — Soft-Check TODO |
| A3 | Legacy-Momentum-Aufräumen | DEBT | `src/strategies/momentum.py` — Entfernen wenn Pipelines migriert |

---

## Stufe B — Daten, Feeds, synthetische Modelle

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| B1 | Fat-Tails / `scipy.stats.t` in synthetischen Modellen | GAP | `src/data/offline_realtime/synthetic_models/garch_regime_v0.py`, `src/data/feeds/offline_realtime_feed.py` |
| B2 | `RATIO_ADJUST` für Continuous Contracts | STUB | `src/data/continuous/continuous_contract.py` — „reserved; not implemented in MVP“ |
| B3 | Infostream-Collector defensive Defaults | GAP | `src/meta/infostream/collector.py` — Keys/Defaults |

---

## Stufe C — Execution, Orders, Portfolio, Risk

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| C1 | Live-Orderpfad / Exchange (bewusst nicht produktiv) | STUB/GAP | `src/orders/exchange.py` — Live-Operationen TODO/kommentiert |
| C2 | Paper-Orders / Adapter (Teile abstrakt) | STUB | `src/orders/paper.py` — `NotImplementedError`-Pfade in Basisklassen |
| C3 | Execution-Simple Gates | STUB | `src/execution_simple/gates.py` |
| C4 | Multi-Asset Risk-Enforcement | DONE | `src/risk/enforcement.py` — `max_corr` + DataFrame-Returns (Portfolio-Returns für VaR/CVaR) |
| C5 | Position-Sizing abstrakte Methoden | STUB | `src/core/position_sizing.py` — Basisklasse |
| C6 | Portfolio-Basis | STUB | `src/portfolio/base.py` |
| C7 | Core-Risk abstrakt | STUB | `src/core/risk.py` |
| C8 | Broker-Basis (Live) | STUB | `src/live/broker_base.py` |

---

## Stufe D — Live-Safety, Kill-Switch, Paper/Live-Grenze

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| D1 | Echte Pre/Post-State-Snapshots statt Platzhalter | DONE | `context["recon"]` + `src/ops/recon/context.py` — `SafetyGuard` (Runbook-B) |
| D2 | Kill-Switch Legacy-Adapter | DONE | D2 Slice 3: Adapter entfernt — `TODO_KILL_SWITCH_ADAPTER_MIGRATION.md` |
| D3 | CLI: `exchange_connected` aus echtem System | DONE | `kill-switch health` — `auto` nutzt HTTP-Probe (öffentliche URL, default Kraken) bzw. Env-Overrides; siehe `exchange_probe.py` |

---

## Stufe E — ML / Research / Strategien (Auswahl)

> Viele Strategien unter `src/strategies/` sind **Research-Stubs** (`NotImplementedError` in `generate_signals`) — **absichtlich**, bis Validierung. Hier nur **repräsentative** offene Punkte.

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| E1 | Meta-Labeling (ML) vollständig | GAP | `src/research/ml/meta/meta_labeling.py` — mehrere TODOs |
| E2 | Triple-Barrier-Labeling | GAP | `src/research/ml/labeling/triple_barrier.py` |
| E3 | Bouchaud / Gatheral Vol-Regime (Platzhalter-Signale) | STUB | `src/strategies/bouchaud/`, `src/strategies/gatheral_cont/` |
| E4 | Armstrong ECM-Cycle echte Signale | GAP | `src/strategies/armstrong/armstrong_cycle_strategy.py` |
| E5 | Ehlers DSP-Filter / Cycle | STUB | `src/strategies/ehlers/ehlers_cycle_filter_strategy.py` |
| E6 | López de Prado Meta-Labeling-Pipeline | STUB | `src/strategies/lopez_de_prado/meta_labeling_strategy.py` |
| E7 | El Karoui Vol-Regime-Signale | GAP | `src/strategies/el_karoui/el_karoui_vol_model_strategy.py` |
| E8 | Strategie-Ideen-Templates | STUB | `src&#47;strategies&#47;ideas&#47;*`, `scripts/new_idea_strategy.py` — Platzhalter für Autoren |
| E9 | Policy-Critic (Regel-Engine) | STUB | `src/governance/policy_critic/rules.py` — ggf. `NotImplementedError` |

---

## Stufe F — Meta: Infostream, Learning Loop, Promotion

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| F1 | Infostream: robuster Parser, Modell-/Key-Konfiguration | DONE | `evaluator.py` — Block-Extraktion, Fences, Bullets, Risk-Level, `resolve_infostream_model` / `INFOSTREAM_MODEL` |
| F2 | Learning Loop **Bridge** & **Emitter** (Signale) | DOC | `docs/LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` — als geplant; **keine** `bridge.py`/`emitter.py` unter `src/meta/learning_loop/` (nur `models.py`) |
| F3 | Learning/Promotion Roadmap v2 | DOC | dieselbe Doku — Slack, Web-UI, Auto-Rollback, TestHealth Pre-Checks, … |
| F4 | Knowledge / Vector-DB | STUB | `src/knowledge/vector_db.py` — `NotImplementedError`-Pfade |
| F5 | Execution-Telemetry | STUB | `src/execution/telemetry.py` |
| F6 | New-Listings-Collector-Basis | STUB | `src/research/new_listings/collectors/base.py` |

---

## Stufe G — Evidence, Reporting, Ops

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| G1 | Evidence-Pack **Multi-Hop-Migrationen** | GAP | `src/ai_orchestration/evidence_pack_schema.py` |
| G2 | Evidence-Generator **Redaction**-Regeln | GAP | `src/ai_orchestration/evidence_pack_generator.py` |
| G3 | Psychology-Heatmap „echte Analyse“ | GAP | `src/reporting/psychology_heatmap.py` |
| G4 | TestHealth-Runner Historie für Trends | GAP | `src/ops/test_health_runner.py` — P2 TODO |

---

## Stufe H — Observability-Session (HTTP)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| H1 | HTTP-Server auf Port (Session) | GAP | `src/obs/session.py` — TODO |

---

## Stufe I — Tests (explizit verschoben)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| I1 | BacktestEngine **Tracker-Integration** | TEST-DEFER | `tests/backtest/test_engine_tracking.py` — Phase 2 |
| I2 | Strategien **parameter_schema** | TEST-DEFER | `tests/strategies/test_parameter_schema.py` — Phase 2 |

---

## Stufe J — Scripts & Demo-Daten (operativ niedrig priorisiert)

| # | Thema | Tag | Hinweis / Ort |
|---|--------|-----|----------------|
| J1 | Kraken-/Marktdaten durch echte Quellen ersetzen | STUB | u. a. `scripts/generate_forward_signals.py`, `scripts/evaluate_forward_signals.py`, `scripts/run_portfolio_backtest_v2.py` |
| J2 | Optuna-Placeholder weiter ausbauen | STUB | `scripts/run_study_optuna_placeholder.py` |
| J3 | Platzhalter-Inventar regenerieren | TOOL | `scripts/ops/placeholders/generate_placeholder_reports.py` — erzeugt TODO-Inventar-MDs |

---

## Empfohlene Bearbeitungs-Reihenfolge (hochlevel)

1. **Governance & Safety-Draht** (D1–D3) — wenn Live-nah berührt, nur mit Freigabe.  
2. **Foundation** (A1–A2) — verbessert Steuerbarkeit des Rests.  
3. **Daten-Realismus** (B1–B3) — vor harten Research-Claims.  
4. **Evidence/Orchestration** (G1–G2) — für auditierbare PRs.  
5. **Infostream** (F1) — Betrieb KI-gestützter Pfade.  
6. **Learning Loop Bridge/Emitter** (F2) — nur wenn Promotion/Learning-Produktpriorität.  
7. **ML/Strategien** (E1–E7) — nach Research-Validierung, nicht blind implementieren.  
8. **Tests** (I1–I2) — wenn Core stabil.  
9. **Scripts/Demos** (J) — wenn operative Daten angebunden werden.

---

## Verwandte Dokumente

- [Finish Plan](../roadmap/FINISH_PLAN.md) — DoD & PR-Slices (PR 6–8 u. a. **landed**).  
- [Current focus](../roadmap/CURRENT_FOCUS.md) — menschlicher „wo stehen wir“.  
- [Chat-led open features (Triage-Prozess)](./RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — **wie** ihr Sessions führt (nicht nur diese Liste).  
- [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) — Navigation.

---

## Anhang — Inventar bei Bedarf neu erzeugen

```bash
python3 scripts/ops/placeholders/generate_placeholder_reports.py --help
```

(Ausgabe: u. a. `TODO_PLACEHOLDER_INVENTORY.md` — kann als **Ergänzung** zu dieser manuell kuratierten Liste dienen.)
