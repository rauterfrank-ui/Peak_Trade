# Feature State Map v1

**Status:** ACTIVE (read-only governance map)  
**Erzeugt:** 2026-07-05  
**Branch:** `main` @ `2f1672bee8761f8d50def3f6ef31cc803824b2e9`  
**Quelle:** [`docs&#47;audit/feature_drift_reconciliation_report_v1.md`](../audit/feature_drift_reconciliation_report_v1.md) <!-- pt:ref-target-ignore -->
**Scope:** Dokumentations-Alignment only — keine Code-, Runtime- oder CI-Mutation

---

## 1. Zweck und Gültigkeit

Dieses Dokument ist die **kanonische Feature-State-Map** für Peak_Trade. Es übersetzt den Drift-Reconciliation-Report in eine stabile Referenztabelle für Governance, Docs-Review und Wiring-Planung.

**Validation Rule (verbindlich):**

```text
NOT in Runtime Decision Core → NON-OPERATIONAL (even if implemented)
```

**Runtime Decision Core (Code-Owner):**

- `src&#47;trading/master_v2&#47;integrated_offline_trading_logic_replay_v1.py` (Replay-Kette) <!-- pt:ref-target-ignore -->
- `src&#47;trading/master_v2&#47;canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` (Slice B) <!-- pt:ref-target-ignore -->

**Integrationsstatus (frozen):** `BOUND_NOT_ACTIVATED` / `BOUND_OFFLINE` — **0 live operational features** zum Evidence-Stand.

### Legende

| Spalte | Bedeutung |
|--------|-----------|
| **Class** | A = Core-bound · B = Implemented, not wired · C = Docs-only · D = Moved/consolidated |
| **Runtime Status** | `Operational` nur bei aktiviertem Live-Runtime-Core (aktuell: keine) · sonst `Non-operational` |
| **Source of Truth** | `Runtime` = Decision Core · `Strategy` = Registry/Module · `Docs` = dokumentiert, Code fehlt/stale |
| **Wiring Status** | `Wired` = in Replay/Bridge konsumiert · `Unwired` = implementiert, kein Core-Pfad · `Orphaned` = Code ohne Registry/Owner |
| **Action Required** | `None` · `Wire` · `Remove` · `Rename` · `Defer` — **Docs-only-Empfehlung**, keine Implementierung in diesem Slice |

---

## 2. Canonical Feature State Map

### 2.1 CLASS A — Runtime Decision Core (core-bound, offline)

| Feature Name | Class | Runtime Status | Source of Truth | Wiring Status | Action Required |
|--------------|-------|----------------|-----------------|---------------|-----------------|
| Market Context | A | Non-operational | Runtime · `canonical_market_context_v1` | Wired | None |
| Master V2 Orchestration (Integrated Replay) | A | Non-operational | Runtime · `integrated_offline_trading_logic_replay_v1` | Wired | None |
| Bull Directional Assessment | A | Non-operational | Runtime · `directional_assessment_v1` (LONG) | Wired | None |
| Bear Directional Assessment | A | Non-operational | Runtime · `directional_assessment_v1` (SHORT) | Wired | None |
| Double Play Composition | A | Non-operational | Runtime · `double_play_composition_matrix_v1` | Wired | None |
| Dynamic Scope (init / events / state) | A | Non-operational | Runtime · `canonical_scope_initialization_v1`, `deterministic_scope_event_generator_v1`, `double_play_state` | Wired | None |
| Survival Assessment | A | Non-operational | Runtime · `survival_assessment_v1` | Wired | None |
| Strategy Suitability Binding | A | Non-operational | Runtime · `suitability_binding_v1` | Wired | None |
| Entry/Exit Policy | A | Non-operational | Runtime · `double_play_entry_exit_policy_v0` | Wired | None |
| Canonical Trading Decision Evidence | A | Non-operational | Runtime · `canonical_trading_decision_evidence_v1` | Wired | None |
| Capital / Risk / Sizing (combined, Slice B) | A | Non-operational | Runtime · `capital_risk_sizing_v1` | Wired (Slice B offline) | Defer (Scope/Risk owner split — Docs) |
| Canonical Order Intent | A | Non-operational | Runtime · `canonical_order_intent_v1` | Wired (Slice B offline) | None |
| Intent Compatibility Firewall | A | Non-operational | Runtime · `intent_compatibility_firewall_v1` | Wired (Slice B offline) | None |

### 2.2 CLASS B — Implemented, not in Core (wiring gaps)

| Feature Name | Class | Runtime Status | Source of Truth | Wiring Status | Action Required |
|--------------|-------|----------------|-----------------|---------------|-----------------|
| Scope Capital (separate Runbook owner) | B | Non-operational | Runtime (packet handoff only) · `ScopeCapitalEnvelopeHandoffV1` | Unwired | Wire (design note) / Defer |
| Risk Decision (separate Runbook owner) | B | Non-operational | Runtime (merged in sizing) · Runbook v2.6 | Unwired | Defer (Docs clarify merge) |
| Master V2 Decision Packet Flow | B | Non-operational | Runtime · `local_evaluator_v1`, `decision_packet_v1` | Unwired (parallel track) | Defer |
| MV2 Research Wiring (`mv2_research_wiring_v1`) | B | Non-operational | Strategy → Runtime adapter | Unwired (non-default path) | Wire (document sequence) |
| Strategy: `ma_crossover` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire (via Suitability snapshot) |
| Strategy: `rsi_reversion` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `breakout_donchian` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `momentum_1h` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `bollinger_bands` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `macd` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `trend_following` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `mean_reversion` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `my_strategy` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `breakout` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `vol_regime_filter` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `composite` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `regime_aware_portfolio` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `armstrong_cycle` | B | Non-operational | Strategy · `registry.py` | Unwired | Rename (vs `ecm_cycle`) |
| Strategy: `el_karoui_vol_model` | B | Non-operational | Strategy · `registry.py` | Unwired | Wire |
| Strategy: `ehlers_cycle_filter` | B | Non-operational | Strategy · `registry.py` (r_and_d) | Unwired | Defer |
| Strategy: `meta_labeling` | B | Non-operational | Strategy · `registry.py` (r_and_d, stub) | Unwired | Defer |
| Strategy: `bouchaud_microstructure` | B | Non-operational | Strategy · `registry.py` (r_and_d) | Unwired | Defer |
| Strategy: `vol_regime_overlay` | B | Non-operational | Strategy · `registry.py` (r_and_d) | Unwired | Defer |
| Strategy (functional): `ecm_cycle` | B | Non-operational | Strategy · loader ref only | Unwired | Rename |
| Strategy (functional): `mean_reversion_channel` | B | Non-operational | Strategy · loader ref only | Unwired | Wire |
| Strategy (functional): `rsi_strategy` | B | Non-operational | Strategy · alias → `rsi` | Unwired | Rename |
| Strategy (functional): `vol_breakout` | B | Non-operational | Strategy · loader ref only | Unwired | Wire |
| Strategy: `breakout_confirmation_v1` | B | Non-operational | Strategy · `breakout_confirmation_v1.py` | Orphaned | Wire / Remove |
| Psychology Heatmap / Heuristics | B | Non-operational | Strategy-adjacent · `src&#47;reporting/psychology_*.py` | Orphaned | Rename (Docs) | <!-- pt:ref-target-ignore -->

### 2.3 CLASS C — Documentation only (no operational runtime path)

| Feature Name | Class | Runtime Status | Source of Truth | Wiring Status | Action Required |
|--------------|-------|----------------|-----------------|---------------|-----------------|
| Feature-Engine (central layer) | C | Non-operational | Docs · `FEHLENDE_FEATURES` §2; placeholder `src&#47;features/` | Unwired | Defer | <!-- pt:ref-target-ignore -->
| Sentiment (News / Makro / Onchain) | C | Non-operational | Docs · Roadmap Phase 14 | Unwired | Defer |
| Orderbuch / Tickdaten | C | Non-operational | Docs · `trading_bot_notes` | Unwired | Defer |
| Meta-Labeling Feature Pipeline | C | Non-operational | Docs · `FEHLENDE_FEATURES` §6; stub in code | Unwired | Defer |
| WebSocket Real-Time Streams | C | Non-operational | Docs · `KNOWN_LIMITATIONS`, Roadmap 12 | Unwired | Defer |
| Multi-Exchange Live | C | Non-operational | Docs · `KNOWN_LIMITATIONS` | Unwired | Defer |
| Web-Dashboard Auth / Write / SSE | C | Non-operational | Docs · `KNOWN_LIMITATIONS` | Unwired | Defer |
| Auto-Position-Liquidation | C | Non-operational | Docs · `KNOWN_LIMITATIONS` | Unwired | Defer |

### 2.4 CLASS D — Moved / consolidated (naming & authority drift)

| Feature Name | Class | Runtime Status | Source of Truth | Wiring Status | Action Required |
|--------------|-------|----------------|-----------------|---------------|-----------------|
| ECM Features (consolidated) | D | Non-operational | Strategy · `src&#47;strategies&#47;ecm.py`, `armstrong&#47;` (was `src&#47;features/`) | Unwired | Rename | <!-- pt:ref-target-ignore -->
| `ecm_cycle` naming surface | D | Non-operational | Docs/Config · `[strategy.ecm_cycle]` vs `armstrong_cycle` | Unwired | Rename |
| `el_karoui_vol_v1` alias | D | Non-operational | Strategy · alias → `el_karoui_vol_model` | Unwired | Remove (Docs) |
| Legacy Ops Double Play evaluator | D | Non-operational | Runtime (legacy) · `src&#47;ops/double_play/` | Unwired | Remove (Docs marker) | <!-- pt:ref-target-ignore -->
| Legacy LiveSessionRunner | D | Non-operational | Runtime (guarded) · `legacy_runtime_entrypoint_guard_v0` | Unwired | None |
| FEHLENDE_FEATURES duplicates | D | N/A | Docs · 4 paths → canonical `docs&#47;features/` | N/A | Remove (redirect-only) | <!-- pt:ref-target-ignore -->
| Strategy loader map | D | Non-operational | Strategy · derived from `registry.get_loader_module_map()` | Wired | None |
| Double Play authority (canonical) | D | Non-operational | Runtime · `double_play_composition_matrix_v1` (replaces ops evaluator) | Wired | Rename (Docs) |

### 2.5 Safety / Execution domain (outside Decision Core — informational)

| Feature Name | Class | Runtime Status | Source of Truth | Wiring Status | Action Required |
|--------------|-------|----------------|-----------------|---------------|-----------------|
| Independent Pre-Trade Safety Kernel | — | Non-operational | Runtime (Safety Core) · offline slice | Unwired (post-decision) | None |
| KillSwitch | — | Non-operational | Runtime · `src&#47;risk_layer/kill_switch/` | Unwired (veto layer) | None | <!-- pt:ref-target-ignore -->
| Execution Permission / Adapter | — | Non-operational | Runtime · `src&#47;execution&#47;` | Unwired (post-decision) | None | <!-- pt:ref-target-ignore -->
| Reconciliation | — | Non-operational | Runtime · `src&#47;ops/recon/`, `execution&#47;live/reconcile.py` | Unwired (post-execution) | None | <!-- pt:ref-target-ignore -->

---

## 3. Documentation Inconsistencies (Docs-only drift)

Nur dokumentarische Abweichungen — **keine Code-Änderung in diesem Pass**.

| ID | Typ | Stale / Duplicate Reference | Canonical Truth | Action Required |
|----|-----|----------------------------|-----------------|-----------------|
| DOC-01 | Duplicate naming | `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` (root) | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | Remove (redirect-only) | <!-- pt:ref-target-ignore -->
| DOC-02 | Duplicate naming | `docs&#47;analysis/FEHLENDE_FEATURES_PEAK_TRADE.md` | `docs&#47;features/FEHLENDE_FEATURES_PEAK_TRADE.md` | Remove (redirect-only) | <!-- pt:ref-target-ignore -->
| DOC-03 | Stale reference | `docs&#47;analysis/missing_features_plan.md` → `src&#47;features/pipeline.py` | ECM in `src&#47;strategies&#47;`; Feature-Engine deferred | Defer | <!-- pt:ref-target-ignore -->
| DOC-04 | Stale reference | `docs&#47;audit/REPO_AUDIT_REPORT.md` Feature-Matrix (Wave 16) | This map + drift report v1 | Rename (historical banner) | <!-- pt:ref-target-ignore -->
| DOC-05 | Mismatched module path | `DOCS_REFERENCE_TARGETS` → `src&#47;features` | `src&#47;strategies&#47;ecm.py` + placeholder banner | Rename | <!-- pt:ref-target-ignore -->
| DOC-06 | Duplicate naming | ECM: `ecm_cycle` in `config&#47;config.toml` | `armstrong_cycle` in `registry.py` | Rename | <!-- pt:ref-target-ignore -->
| DOC-07 | Mismatched module path | Psychology under `docs&#47;features/psychology/` | Code: `src&#47;reporting/psychology_*.py` | Rename | <!-- pt:ref-target-ignore -->
| DOC-08 | Stale reference | `src&#47;docs&#47;peak_trade_documentation.md` maps `ecm_cycle` | `registry.py` canonical IDs | Rename | <!-- pt:ref-target-ignore -->
| DOC-09 | Duplicate naming | `el_karoui_vol_v1` in legacy docs&#47;examples | `el_karoui_vol_model` | Remove | <!-- pt:ref-target-ignore -->
| DOC-10 | Stale reference | Feature-Engine ECM in older FEHLENDE_FEATURES copies | Strategy-layer ECM (consolidated) | Rename |
| DOC-11 | Authority drift | Ops `evaluate_double_play` implied authoritative | `double_play_composition_matrix_v1` canonical | Rename |
| DOC-12 | Stale reference | R&D strategies „not implemented“ in some FEHLENDE copies | Partial stubs exist in `src&#47;strategies&#47;` | Defer | <!-- pt:ref-target-ignore -->

---

## 4. Summary Matrix

| Class | Count | Runtime Status | Primary Action |
|-------|-------|----------------|--------------|
| **A** Core-bound | 13 | All Non-operational (offline `BOUND_NOT_ACTIVATED`) | None |
| **B** Implemented, unwired | 32+ | All Non-operational | Wire (Docs sequence) · Rename (ECM/RSI) |
| **C** Docs-only | 8 | All Non-operational | Defer |
| **D** Moved/consolidated | 8 | All Non-operational | Rename · Remove duplicates |
| **Live Operational** | **0** | — | — |

---

## 5. Cross-References

| Artefakt | Rolle |
|----------|-------|
| [`feature_drift_reconciliation_report_v1.md`](../audit/feature_drift_reconciliation_report_v1.md) | Evidence source (frozen) |
| [`FEHLENDE_FEATURES_PEAK_TRADE.md`](../features/FEHLENDE_FEATURES_PEAK_TRADE.md) | Kanonischer Feature Catalog |
| [`PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md`](../architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md) | Decision Core Zielbild |
| [`STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md`](../ops/specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md) | ECM/Armstrong wiring read-model |
| [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | Authority gaps |

---

## 6. Non-Goals (this slice)

- Keine Strategy-Layer-Mutation
- Keine Runtime-Core-Mutation
- Keine neuen Features
- Keine Logik-Refactors
- Kein Runtime-Start, kein CI, keine Tests

**Nächster Docs-only-Schritt (Operator GO):** DOC-01, DOC-02, DOC-05, DOC-06, DOC-07 gemäß §3 — weiterhin ohne Code.

**Map-Owner:** Feature State Map v1  
**Evidence frozen at:** `2f1672bee8761f8d50def3f6ef31cc803824b2e9`
