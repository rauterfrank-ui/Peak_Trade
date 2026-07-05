# Feature Drift Reconciliation Report v1

**Modus:** READ-ONLY — keine Codeänderungen, kein Runtime-Start, kein CI-Trigger  
**Erzeugt:** 2026-07-05  
**Branch:** `main` @ `2f1672bee8761f8d50def3f6ef31cc803824b2e9` (aligned with `origin&#47;main`) <!-- pt:ref-target-ignore -->
**Worktree:** modified docs only (6 files unstaged; kein Python-Code geändert)

---

## 1. Runbook-Referenz und Methodik

**Hinweis:** Die Datei `Peak_Trade_Feature_Drift_Reconciliation_Runbook_v1.0` ist im Repository **nicht** als eigenständiges Artefakt vorhanden. Diese Analyse folgt dem vom Operator spezifizierten Schema (Klassifikation A–D, Validation Rule) und bindet kanonische Owner aus:

| Surface | Owner-Pfad |
|---------|------------|
| Trading Decision Core (Zielbild) | `docs&#47;architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md` | <!-- pt:ref-target-ignore -->
| Runtime Decision Core (Code-Orchestrator) | `src&#47;trading/master_v2&#47;integrated_offline_trading_logic_replay_v1.py` | <!-- pt:ref-target-ignore -->
| Intent-Pipeline-Erweiterung (Slice B) | `src&#47;trading/master_v2&#47;canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` | <!-- pt:ref-target-ignore -->
| Strategy Registry | `src&#47;strategies&#47;registry.py` | <!-- pt:ref-target-ignore -->
| MV2-Suitability-Wiring | `src&#47;strategies&#47;suitability_registry_adapter_v1.py`, `src&#47;backtest/mv2_research_wiring_v1.py` | <!-- pt:ref-target-ignore -->
| Feature Catalog / Gaps | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` (kanonisch), Duplikate unter `docs&#47;FEHLENDE_FEATURES_*` | <!-- pt:ref-target-ignore -->
| Drift-/Audit-Baseline | `docs&#47;audit/REPO_AUDIT_REPORT.md`, `docs&#47;ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` | <!-- pt:ref-target-ignore -->

**Validation Rule (verbindlich):** Feature **nicht** im Runtime Decision Core referenziert → **NOT operational**.

**Operational-Definition in diesem Report:**

- **Im Core:** explizit in `run_integrated_offline_trading_logic_replay_v1` oder der Slice-B-Intent-Pipeline konsumiert/produziert.
- **Operational:** im Core **und** nicht durch `BOUND_NOT_ACTIVATED` / `BOUND_OFFLINE` auf Runtime-Ebene blockiert — aktuell ist **kein** Live-Runtime-Pfad aktiviert; alle Core-Komponenten sind **offline gebunden**.

---

## 2. Runtime Decision Core Scan

### 2.1 Kanonische Kette (Runbook v2.6)

```text
Market Context → Master V2 Composition → Bull → Bear → Double Play → Dynamic Scope
→ Risk → Sizing → Scope Capital → Canonical Order Intent
→ [Safety/Execution Core — außerhalb Decision Core]
```

### 2.2 Im Code referenzierte Decision-Core-Komponenten

| # | Semantik (Runbook) | Modul / Owner | In Replay v1 | In Slice-B Bridge | Operational |
|---|-------------------|---------------|-------------|-------------------|-------------|
| 1 | Market Context | `trading.master_v2.canonical_market_context_v1` | ✅ | ✅ (via Replay) | Offline only |
| 2 | Master V2 Composition / Orchestration | `integrated_offline_trading_logic_replay_v1` | ✅ | ✅ | Offline only |
| 3 | Bull Evaluation | `directional_assessment_v1` (LONG) | ✅ | — | Offline only |
| 4 | Bear Evaluation | `directional_assessment_v1` (SHORT) | ✅ | — | Offline only |
| 5 | Double Play Resolution | `double_play_composition_matrix_v1` | ✅ | — | Offline only |
| 6 | Dynamic Scope | `canonical_scope_initialization_v1`, `deterministic_scope_event_generator_v1`, `double_play_state` | ✅ | — | Offline only |
| 7 | Survival (Vorstufe Suitability) | `survival_assessment_v1` | ✅ | — | Offline only |
| 8 | Strategy Suitability | `suitability_binding_v1` | ✅ | — | Offline only |
| 9 | Entry/Exit Policy | `double_play_entry_exit_policy_v0` | ✅ | — | Offline only |
| 10 | Decision Evidence | `canonical_trading_decision_evidence_v1` | ✅ | ✅ | Offline only |
| 11 | Risk Decision | `src&#47;governance/capital_risk_sizing_v1` | ❌ | ✅ (`evaluate_capital_risk_sizing_v1`) | Offline only | <!-- pt:ref-target-ignore -->
| 12 | Sizing Decision | (combined in `capital_risk_sizing_v1`) | ❌ | ✅ | Offline only |
| 13 | Scope Capital | `ScopeCapitalEnvelopeHandoffV1` (decision packet only) | ❌ | partial via sizing input | **NOT operational** |
| 14 | Canonical Order Intent | `canonical_order_intent_v1` | ❌ | ✅ | Offline only |
| 15 | Intent Firewall | `intent_compatibility_firewall_v1` | ❌ | ✅ | Offline only |

**Integrationsstatus:** `INTEGRATION_STATUS_BOUND_NOT_ACTIVATED`, `CAPITAL_RISK_SIZING_BINDING_STATUS=BOUND_OFFLINE`, `CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED` (Slice A–D Evidence).

### 2.3 Nicht im Decision Core (Safety / Execution Domain)

Diese Features sind im kanonischen System, aber **nicht** Teil des Trading Decision Core:

| Feature | Owner | Operational im Trading-Pfad |
|---------|-------|----------------------------|
| Independent Pre-Trade Safety Kernel | `independent_pre_trade_safety_kernel_v1` (offline slice) | Nein (Safety Core) |
| KillSwitch | `src&#47;risk_layer/kill_switch/` | Veto-Layer, nicht Decision Core | <!-- pt:ref-target-ignore -->
| Execution Permission / Adapter | `src&#47;execution&#47;`, `adapter_submission_contract_v1` | Post-Decision | <!-- pt:ref-target-ignore -->
| Reconciliation | `src&#47;ops/recon/`, `src&#47;execution&#47;live/reconcile.py` | Post-Execution | <!-- pt:ref-target-ignore -->
| Legacy Ops Double Play | `src.ops.double_play.specialists.evaluate_double_play` | **LEGACY_NON_AUTHORITATIVE** |

---

## 3. Strategy Layer Scan

### 3.1 Registry-Inventar (`src&#47;strategies&#47;registry.py`) <!-- pt:ref-target-ignore -->

**23 kanonische Strategy-IDs** (19 OOP `StrategySpec` + 4 functional-only):

| strategy_id | Tier | live_ready | Im Decision Core (Suitability-Pfad) |
|-------------|------|------------|--------------------------------------|
| armstrong_cycle | production | ✅ | Nur wenn Snapshot explizit gebaut |
| bollinger_bands | production | ✅ | Nur wenn Snapshot explizit gebaut |
| bouchaud_microstructure | r_and_d | ❌ | Nur Research-Wiring |
| breakout | production | ✅ | Nur wenn Snapshot explizit gebaut |
| breakout_donchian | production | ✅ | Nur wenn Snapshot explizit gebaut |
| composite | production | ✅ | Nur wenn Snapshot explizit gebaut |
| ecm_cycle | functional | — | Loader-Ref only; kein StrategySpec |
| ehlers_cycle_filter | r_and_d | ❌ | Nur Research-Wiring |
| el_karoui_vol_model | production | ✅ | Nur wenn Snapshot explizit gebaut |
| ma_crossover | production | ✅ | Nur wenn Snapshot explizit gebaut |
| macd | production | ✅ | Nur wenn Snapshot explizit gebaut |
| mean_reversion | production | ✅ | Nur wenn Snapshot explizit gebaut |
| mean_reversion_channel | functional | — | Loader-Ref only |
| meta_labeling | r_and_d | ❌ | Nur Research-Wiring |
| momentum_1h | production | ✅ | Nur wenn Snapshot explizit gebaut |
| my_strategy | production | ✅ | Nur wenn Snapshot explizit gebaut |
| regime_aware_portfolio | production | ✅ | Nur wenn Snapshot explizit gebaut |
| rsi_reversion | production | ✅ | Nur wenn Snapshot explizit gebaut |
| rsi_strategy | functional | — | Alias-Loader → `rsi` |
| trend_following | production | ✅ | Nur wenn Snapshot explizit gebaut |
| vol_breakout | functional | — | Loader-Ref only |
| vol_regime_filter | production | ✅ | Nur wenn Snapshot explizit gebaut |
| vol_regime_overlay | r_and_d | ❌ | Nur Research-Wiring |

**Legacy-Alias:** `el_karoui_vol_v1` → `el_karoui_vol_model` (DEPRECATED_ALIAS).

### 3.2 Implementiert, aber nicht in zentraler Registry

| Modul | Pfad | Wiring-Status |
|-------|------|---------------|
| Breakout Confirmation v1 | `src&#47;strategies&#47;breakout_confirmation_v1.py` | ❌ nicht in `registry.py` | <!-- pt:ref-target-ignore -->
| ECM (funktional) | `src&#47;strategies&#47;ecm.py` | functional ID `ecm_cycle`; parallel `armstrong_cycle` | <!-- pt:ref-target-ignore -->
| Psychology Heatmap/Heuristics | `src&#47;reporting/psychology_*.py` | Reporting-only, kein Strategy-Registry-Eintrag | <!-- pt:ref-target-ignore -->

### 3.3 Export / Wiring zum Decision Core

| Wiring-Pfad | Status |
|-------------|--------|
| `build_suitability_registry_from_snapshot()` → `SuitabilityStrategyRegistryV1` | ✅ Adapter vorhanden |
| `mv2_research_wiring_v1.py` nutzt Adapter | ✅ Research/Backtest-Pfad |
| `integrated_offline_trading_logic_replay_v1` | Akzeptiert **Offline-Snapshot**, nicht Live-Registry |
| `src&#47;strategies&#47;__init__.py` `load_strategy()` | Deprecated view; leitet auf `registry.py` | <!-- pt:ref-target-ignore -->
| Runtime Live Session | `legacy_runtime_entrypoint_guard_v0` — **deauthorized** |

**Fazit Strategy Layer:** Strategien sind implementiert und registry-konsolidiert, aber **keine** einzelne Strategie ist per se im Runtime Decision Core operational — nur der generische Suitability-Slot mit explizitem Snapshot.

---

## 4. Repo Reference Scan (ripgrep-Zusammenfassung)

### 4.1 Feature-Namen & Aliases mit Drift-Risiko

| Name | Canonical | Deprecated / Alias | Modulpfad(e) |
|------|-----------|---------------------|--------------|
| ECM / Armstrong | `armstrong_cycle` | `ecm_cycle` (functional), Config `[strategy.ecm_cycle]` | `src&#47;strategies&#47;armstrong&#47;`, `src&#47;strategies&#47;ecm.py` | <!-- pt:ref-target-ignore -->
| El Karoui | `el_karoui_vol_model` | `el_karoui_vol_v1` | `src&#47;strategies&#47;el_karoui/` | <!-- pt:ref-target-ignore -->
| RSI | `rsi_reversion` | `rsi_strategy` | `src&#47;strategies&#47;rsi_reversion.py`, `rsi.py` | <!-- pt:ref-target-ignore -->
| Feature-Engine | (nicht operational) | Docs referenzieren `src&#47;features/` | Placeholder only | <!-- pt:ref-target-ignore -->
| Double Play (Ops) | `double_play_composition_matrix_v1` | `evaluate_double_play` (ops) | MV2 vs `src&#47;ops/double_play/` | <!-- pt:ref-target-ignore -->

### 4.2 Deprecated References (aktiv im Repo)

| Referenz | Status | Risiko |
|----------|--------|--------|
| `src&#47;features/` in FEHLENDE_FEATURES*, DOCS_REFERENCE_TARGETS | Placeholder; Docs sagen „fehlt“ | Doc/Code drift (ECM jetzt in strategies) | <!-- pt:ref-target-ignore -->
| `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` (Root) | SUPERSEDED-Banner → `docs&#47;features/` | Duplikat-Pflege | <!-- pt:ref-target-ignore -->
| `config&#47;config.toml` `[strategy.ecm_cycle]` | Config ohne StrategySpec-Key | Config/Registry split | <!-- pt:ref-target-ignore -->
| `src&#47;docs&#47;peak_trade_documentation.md` | Mappt `"ecm_cycle": "ecm"` | Legacy-Doku | <!-- pt:ref-target-ignore -->
| Psychology Features | Docs unter `docs&#47;features/psychology/` | Code in `src&#47;reporting/`, nicht Feature-Engine | <!-- pt:ref-target-ignore -->

---

## 5. Documentation Scan

| Dokument | Rolle | Drift vs. Code |
|----------|-------|----------------|
| `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | **Kanonischer Feature Catalog** | ECM als „strategy layer ✅“; Feature-Engine ❌ — konsistent | <!-- pt:ref-target-ignore -->
| `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` | Superseded duplicate | Banner vorhanden; Inhalt teils älter (2026-02-10) | <!-- pt:ref-target-ignore -->
| `docs&#47;analysis/FEHLENDE_FEATURES_PEAK_TRADE.md` | Analysis duplicate | Parallel gepflegt | <!-- pt:ref-target-ignore -->
| `docs&#47;analysis/missing_features_plan.md` | Implementation plan | Referenziert noch `src&#47;features/pipeline.py` als Ziel | <!-- pt:ref-target-ignore -->
| `docs&#47;audit/REPO_AUDIT_REPORT.md` | Wave-16 Snapshot | Feature-Matrix veraltet (pre-ECM-consolidation teils) | <!-- pt:ref-target-ignore -->
| `docs&#47;ops/specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md` | Wiring read-model | Dual-map `ecm_cycle` vs `armstrong_cycle` dokumentiert | <!-- pt:ref-target-ignore -->
| `docs&#47;ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` | Authority gaps | Scope/Capital/Risk partial-unclear | <!-- pt:ref-target-ignore -->
| `docs&#47;architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md` | Zielbild Decision Core | Explizit „nicht voll implementiert“ | <!-- pt:ref-target-ignore -->

---

## 6. Feature Inventory Table

| ID | Feature | Code | Decision Core | Docs | Class | Operational |
|----|---------|------|---------------|------|-------|-------------|
| DC-01 | Market Context | ✅ | ✅ | ✅ | A | Offline |
| DC-02 | Master V2 Orchestration (Replay) | ✅ | ✅ | ✅ | A | Offline |
| DC-03 | Bull Directional Assessment | ✅ | ✅ | ✅ | A | Offline |
| DC-04 | Bear Directional Assessment | ✅ | ✅ | ✅ | A | Offline |
| DC-05 | Double Play Composition | ✅ | ✅ | ✅ | A | Offline |
| DC-06 | Dynamic Scope (init/events/state) | ✅ | ✅ | ✅ | A | Offline |
| DC-07 | Survival Assessment | ✅ | ✅ | partial | A | Offline |
| DC-08 | Suitability Binding | ✅ | ✅ | partial | A | Offline |
| DC-09 | Entry/Exit Policy | ✅ | ✅ | partial | A | Offline |
| DC-10 | Capital/Risk/Sizing (combined) | ✅ | partial (Slice B) | partial | A | Offline |
| DC-11 | Canonical Order Intent | ✅ | partial (Slice B) | partial | A | Offline |
| DC-12 | Scope Capital (separate owner) | partial (packet handoff) | ❌ | ✅ | B | **NOT operational** |
| DC-13 | Risk Decision (separate owner) | partial (merged in sizing) | ❌ | ✅ | B | **NOT operational** |
| ST-01..19 | Production Strategy Library | ✅ | via Suitability only | ✅ | B | **NOT operational** |
| ST-R01..04 | R&D Strategies | ✅/stub | via Suitability only | ✅ | B | **NOT operational** |
| ST-F01..04 | Functional-only IDs (ecm_cycle, etc.) | ✅ | indirect | partial | B | **NOT operational** |
| ST-X01 | breakout_confirmation_v1 | ✅ | ❌ | ❌ | B | **NOT operational** |
| FE-01 | Feature-Engine (`src&#47;features/`) | placeholder | ❌ | ❌ fehlt | C | **NOT operational** | <!-- pt:ref-target-ignore -->
| FE-02 | Sentiment (News/Makro/Onchain) | ❌ | ❌ | ❌ fehlt | C | **NOT operational** |
| FE-03 | Orderbuch/Tickdaten | ❌ | ❌ | ❌ fehlt | C | **NOT operational** |
| FE-04 | Meta-Labeling Feature Pipeline | stub/TODO | ❌ | partial | C | **NOT operational** |
| FE-05 | WebSocket Real-Time Streams | ❌ | ❌ | ❌ fehlt | C | **NOT operational** |
| FE-06 | Multi-Exchange Live | ❌/blocked | ❌ | ❌ fehlt | C | **NOT operational** |
| FE-07 | Web-Dashboard Auth/Write | ❌ | ❌ | ❌ fehlt | C | **NOT operational** |
| FE-08 | Psychology Heatmap/Heuristics | ✅ reporting | ❌ | ✅ docs&#47;features | C | **NOT operational** | <!-- pt:ref-target-ignore -->
| MV-01 | ECM Features | ✅ strategies | ❌ (nicht Feature-Engine) | drift | D | **NOT operational** |
| MV-02 | ecm_cycle naming | functional loader | ❌ | config&#47;docs | D | **NOT operational** | <!-- pt:ref-target-ignore -->
| MV-03 | Legacy Ops Double Play evaluator | ✅ ops | ❌ (non-auth) | ✅ marked legacy | D | **NOT operational** |
| MV-04 | Legacy LiveSessionRunner | guarded | ❌ | ✅ Slice D | D | **NOT operational** |
| MV-05 | FEHLENDE_FEATURES root duplicate | — | — | superseded | D | N/A |

---

## 7. Klassifikation A–D

### CLASS A — Active Feature (im Runtime Decision Core referenziert)

Alle DC-01 bis DC-11. **Hinweis:** „Active“ bedeutet **Core-Bindung**, nicht Live-Runtime-Aktivierung. Stand heute: **offline replay only**, `BOUND_NOT_ACTIVATED`.

### CLASS B — Implemented but not in Core (Wiring Gaps)

| Gap | Details |
|-----|---------|
| **B-01** | Gesamte Strategy Library (23 IDs): implementiert, nur über manuellen `SuitabilityStrategyRegistryV1`-Snapshot an Core anschlussfähig |
| **B-02** | `breakout_confirmation_v1`: Code ohne Registry-Eintrag |
| **B-03** | Scope Capital als separater Owner: nur `ScopeCapitalEnvelopeHandoffV1` in Decision Packet, nicht in Replay-Kette |
| **B-04** | Risk als separater Owner: in Runbook distinct, im Code in `capital_risk_sizing_v1` merged |
| **B-05** | Master V2 Decision Packet Flow (`local_evaluator_v1`, `decision_packet_v1`): parallel track, nicht canonical replay owner |
| **B-06** | `ecm_cycle` functional ID vs `armstrong_cycle` StrategySpec — dual identity |
| **B-07** | Research-only Wiring (`mv2_research_wiring_v1`) — nicht Default-Runtime-Pfad |

### CLASS C — Documentation Only

FE-01 bis FE-08 (siehe Inventory). Zentrale Feature-Engine, Sentiment, Streaming, Multi-Exchange-Live, Web-Auth, Meta-Labeling-Pipeline, Psychology als Feature-Layer.

### CLASS D — Moved / Consolidated

| Item | From → To |
|------|-----------|
| ECM Feature-Engine path | `src&#47;features/` (vision) → `src&#47;strategies&#47;ecm.py` + `armstrong&#47;` | <!-- pt:ref-target-ignore -->
| Strategy loader map | Legacy dict → derived from `registry.get_loader_module_map()` |
| FEHLENDE_FEATURES canonical | `docs&#47;FEHLENDE_FEATURES_*` → `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | <!-- pt:ref-target-ignore -->
| Double Play authority | `src&#47;ops/double_play/` → `double_play_composition_matrix_v1` (offline canonical) | <!-- pt:ref-target-ignore -->
| Live runtime entry | `LiveSessionRunner` → guarded; canonical bridge `BOUND_NOT_ACTIVATED` |
| El Karoui naming | `el_karoui_vol_v1` → `el_karoui_vol_model` |

---

## 8. Drift List

### 8.1 CLASS C — Documentation Only (Doc behauptet Feature, Code fehlt oder bewusst ausgeschlossen)

| Priority | Feature | Doc-Quelle | Code-Realität |
|----------|---------|------------|---------------|
| P2 | Zentrale Feature-Engine | FEHLENDE_FEATURES §2, trading_bot_notes | `src&#47;features/__init__.py` Placeholder | <!-- pt:ref-target-ignore -->
| P2 | Sentiment-Daten | FEHLENDE_FEATURES, Roadmap Phase 14 | Kein Modul |
| P2 | Orderbuch/Tick | FEHLENDE_FEATURES | Kein Modul |
| P3 | WebSocket Streaming | KNOWN_LIMITATIONS, Roadmap 12 | REST/Polling only |
| P3 | Multi-Exchange Live | KNOWN_LIMITATIONS | Kraken-fokussiert; Gates blockieren |
| P3 | Web Auth / POST Orders | KNOWN_LIMITATIONS | Read-only Dashboard |
| P3 | Meta-Labeling Features | FEHLENDE_FEATURES §6 | TODO/Null-Returns |
| P3 | Auto-Position-Liquidation | KNOWN_LIMITATIONS | Nicht implementiert |

### 8.2 CLASS D — Moved / Consolidated (Doc/Code-Naming divergiert)

| Priority | Drift | Alt | Neu / Kanonisch | Aktion (Empfehlung) |
|----------|-------|-----|-----------------|---------------------|
| **P1** | ECM identity split | `ecm_cycle`, `src&#47;features/` | `armstrong_cycle`, `src&#47;strategies&#47;ecm.py` | Registry-Alias oder Config-Migration dokumentieren | <!-- pt:ref-target-ignore -->
| **P1** | FEHLENDE_FEATURES duplicates | 4 Pfade | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | Duplikate synchronisieren oder archivieren | <!-- pt:ref-target-ignore -->
| P2 | Double Play evaluator | `src&#47;ops/double_play/` | MV2 composition matrix | Legacy-Marker in Ops-Docs verstärken | <!-- pt:ref-target-ignore -->
| P2 | Feature-Engine ECM refs | DOCS_REFERENCE_TARGETS → `src&#47;features` | strategies layer | Reference targets aktualisieren | <!-- pt:ref-target-ignore -->
| P3 | Psychology „Features“ | `docs&#47;features/psychology/` | `src&#47;reporting/psychology_*` | Umbenennung in Docs (Reporting, nicht Feature-Engine) | <!-- pt:ref-target-ignore -->
| P3 | REPO_AUDIT_REPORT Matrix | Wave-16 Snapshot | Aktueller Stand | Audit-Report als historisch markieren (teilweise done) |

---

## 9. Wiring Gaps (CLASS B — detailliert)

| ID | Gap | Impact | Evidence |
|----|-----|--------|----------|
| WG-01 | Kein automatischer Registry→Core-Wiring-Pfad in Runtime | Strategien existieren, werden nicht ohne Snapshot im Core selektiert | `suitability_binding_v1` verlangt `SuitabilityStrategyRegistryV1`; nur `mv2_research_wiring_v1` baut Snapshot |
| WG-02 | Scope Capital nicht in Replay-Kette | Runbook-Owner `SCOPE_CAPITAL_ROLE` ohne dedizierten Replay-Step | `ScopeCapitalEnvelopeHandoffV1` nur Decision Packet |
| WG-03 | Risk/Sizing semantisch merged | Runbook trennt Risk, Sizing, Scope Capital; Code merged in Slice B | `capital_risk_sizing_v1` |
| WG-04 | `breakout_confirmation_v1` orphan module | Implementierung ohne Registry | Datei existiert, kein `StrategySpec` |
| WG-05 | `ecm_cycle` vs `armstrong_cycle` | Config/TOML vs Registry mismatch | `config&#47;config.toml`, `registry.py` | <!-- pt:ref-target-ignore -->
| WG-06 | Canonical bridge nicht aktiviert | Core existiert offline, kein Live-Einstieg | `BOUND_NOT_ACTIVATED` across Slices A–D |
| WG-07 | Decision Packet vs Integrated Replay | Zwei parallele MV2-Pfade | `__init__.py` exports packet flow; replay owner separat |

---

## 10. Critical Risks (Priority 1–2)

### Priority 1

| Risk | Beschreibung | Validation Rule Impact |
|------|--------------|------------------------|
| **CR-P1-01** | **False operational assumption:** 23 registrierte Strategien wirken „production-ready“, sind aber **NOT operational** ohne Core-Snapshot und Runtime-Aktivierung | Jede Strategie außerhalb Replay = nicht operational |
| **CR-P1-02** | **ECM/ecm_cycle/armstrong_cycle identity drift:** Config, functional loader, StrategySpec und Docs verwenden unterschiedliche IDs für dieselbe Semantik | Fehlrouting bei `load_strategy("ecm_cycle")` vs `create_strategy_from_config("armstrong_cycle")` |
| **CR-P1-03** | **Dual Double Play authority:** Ops-Legacy-Evaluator vs MV2 composition matrix — Reviewer verwechseln autoritative Quelle | Legacy marked NON_AUTHORITATIVE; Drift bei manuellen Ops-Checks |
| **CR-P1-04** | **Scope/Risk/Sizing owner collapse:** Runbook definiert 3 Owner; Replay+Bridge liefern nur combined sizing — Governance-Reviews können Gates fälschlich als „filled“ lesen | Scope Capital **NOT operational** als separater Owner |

### Priority 2

| Risk | Beschreibung |
|------|--------------|
| **CR-P2-01** | FEHLENDE_FEATURES an 4 Pfaden — widersprüchliche „implementiert/fehlt“-Aussagen (Root vs features/) |
| **CR-P2-02** | Feature-Engine Placeholder (`src&#47;features/`) weiterhin in CI Docs-Reference-Targets verankert | <!-- pt:ref-target-ignore -->
| **CR-P2-03** | R&D Strategien (meta_labeling, bouchaud, ehlers) mit TODO/Stubs — Docs teils „nicht implementiert“, Code teils vorhanden |
| **CR-P2-04** | Psychology-Features dokumentiert unter `docs&#47;features/`, implementiert unter `src&#47;reporting/` — falsche Schicht-Zuordnung | <!-- pt:ref-target-ignore -->
| **CR-P2-05** | `BOUND_NOT_ACTIVATED` über gesamten Canonical Core — jede Demo/Script-Nutzung von Legacy-Entrypoints trotz Slice-D-Guard |

---

## 11. Minimal Fix Recommendations (ohne Implementierung)

| # | Empfehlung | Scope | Aufwand |
|---|------------|-------|---------|
| R-01 | **Single FEHLENDE_FEATURES owner:** Root/analysis-Duplikate auf Redirect-only reduzieren; nur `docs&#47;features/` pflegen | Docs | S | <!-- pt:ref-target-ignore -->
| R-02 | **ECM identity decision record:** Entweder `ecm_cycle` → Alias von `armstrong_cycle` in Registry **oder** Config-Migration zu `armstrong_cycle` — eine Zeile in `STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE` | Docs/Governance | S |
| R-03 | **`breakout_confirmation_v1`:** Registry-Eintrag hinzufügen **oder** Modul als experimental markieren/entfernen | Code+Registry | S |
| R-04 | **Wiring-Gap-Dokument:** Explizite „Registry → Suitability → Replay“-Sequenz in `docs&#47;ops/specs/` (read-only), analog ECM inventory | Docs | S | <!-- pt:ref-target-ignore -->
| R-05 | **DOCS_REFERENCE_TARGETS:** `src&#47;features` Target auf `src&#47;strategies&#47;ecm.py` + Banner „Feature-Engine deferred“ | Docs/CI config | S | <!-- pt:ref-target-ignore -->
| R-06 | **Scope Capital Replay-Step:** Design-Notiz ob `ScopeCapitalEnvelopeHandoffV1` in Replay integriert oder bewusst in Sizing merged bleibt | Architecture | M |
| R-07 | **Psychology relabel:** Docs von `docs&#47;features/psychology/` nach `docs&#47;reporting/` oder Crosslink | Docs | S | <!-- pt:ref-target-ignore -->
| R-08 | **REPO_AUDIT_REPORT:** Historisch-Banner + Verweis auf diesen Report v1 | Docs | S |

**Explizit nicht empfohlen in diesem Slice:** Runtime-Aktivierung, Live-Gate-Änderungen, CI-Workflow-Mutation, Feature-Engine-Neubau.

---

## 12. Zusammenfassung

| Metrik | Wert |
|--------|------|
| Decision-Core-Komponenten (Replay) | 10 Layer + Evidence |
| Slice-B-Erweiterungen | Risk/Sizing/Intent/Firewall (offline) |
| Strategy Registry IDs | 23 |
| CLASS A (Core-bound) | 11 |
| CLASS B (Wiring gaps) | 7 Gruppen |
| CLASS C (Doc-only) | 8 |
| CLASS D (Moved/consolidated) | 6 |
| **Live operational Features** | **0** (Validation Rule: nicht im aktivierten Runtime Core) |

**Schlussfolgerung:** Der Runtime Decision Core ist als **offline replay chain** substantiell implementiert (Master V2 / Bull / Bear / Double Play / Dynamic Scope / Suitability / Entry-Exit). Die Strategy Library, Feature-Engine-Vision und zahlreiche Roadmap-Features sind **nicht operational**. Dominanter Drift: **ECM/Feature-Engine-Konsolidierung**, **Duplikat-Dokumentation**, **Registry↔Core-Wiring**, und **Scope/Risk/Sizing-Owner-Trennung** im Zielbild vs. Code.

---

**Nächster Schritt (Operator):** Review dieses Reports; bei GO gezielte Docs-Only-Slices R-01, R-02, R-04, R-05, R-08 — weiterhin ohne Runtime-Start.

**Report-Owner:** READ-ONLY Feature Drift Reconciliation v1  
**Evidence frozen at:** `2f1672bee8761f8d50def3f6ef31cc803824b2e9`
