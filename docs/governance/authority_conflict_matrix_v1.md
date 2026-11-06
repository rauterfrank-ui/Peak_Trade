# Authority Conflict Matrix v1

**Status:** READ-ONLY ANALYSIS — keine Auflösung, keine Enforcement  
**Erzeugt:** 2026-07-05  
**Branch:** `main` @ `2f1672bee8761f8d50def3f6ef31cc803824b2e9`  
**State:** post-docs-convergence (Section A applied; Section B/C/D offen)

**Inputs:**

- [`feature_state_map_v1.md`](feature_state_map_v1.md)
- [`drift_cleanup_plan_v1.md`](drift_cleanup_plan_v1.md)
- [`drift_safe_docs_patch_v1.md`](../audit/drift_safe_docs_patch_v1.md)
- Runtime Decision Core (read-only inspection)

**Validation Rule (frozen):**

```text
NOT in Runtime Decision Core → NON-OPERATIONAL (even if implemented)
```

**Runtime Decision Core (Code-Owner, frozen):**

| Surface | Owner |
|---------|-------|
| Integrated Replay (Slice A) | `src&#47;trading/master_v2&#47;integrated_offline_trading_logic_replay_v1.py` | <!-- pt:ref-target-ignore -->
| Intent Pipeline Bridge (Slice B) | `src&#47;trading/master_v2&#47;canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` | <!-- pt:ref-target-ignore -->
| Integrationsstatus | `BOUND_NOT_ACTIVATED` / `BOUND_OFFLINE` — **0 live operational features** |

**Legende — Konflikttyp:**

| Typ | Bedeutung |
|-----|-----------|
| **A** | Pure Documentation Mismatch |
| **B** | Strategy vs Runtime Misalignment |
| **C** | Registry Ownership Conflict |
| **D** | Architectural Ambiguity (no clear owner) |

**Legende — Risiko:**

| Stufe | Bedeutung |
|-------|-----------|
| **HIGH** | Fehlrouting oder falsche Authority-Annahme bei Aktivierung plausibel |
| **MEDIUM** | Verwechslungsrisiko; aktuell offline/fail-closed abgefangen |
| **LOW** | Sichtbarkeits-/Naming-Drift; begrenzte Laufzeitwirkung solange Core inaktiv |

---

## 1. ECM Authority Chain

### AUTH-001 — Dual strategy identity: `ecm_cycle` vs `armstrong_cycle`

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Registry/Config · Documentation |
| **Type** | **C** (Registry Ownership Conflict) |
| **Current Ownership (per layer)** | **Runtime:** weder ID im Decision Core · **Strategy:** `ecm_cycle` = functional-only (`_FUNCTIONAL_ONLY_STRATEGY_IDS` → `src&#47;strategies&#47;ecm.py`); `armstrong_cycle` = `StrategySpec` in `_STRATEGY_REGISTRY` · **Registry/Config:** Loader-Map enthält beide Keys; Config hat `[strategy.ecm_cycle]` und `[strategy.armstrong_cycle]` · **Docs:** post-A-Patch kanonisch auf Strategy-Layer; Identity-Split weiter offen (DOC-06 BLOCKED) | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Ein kanonischer `strategy_id` mit dokumentierter Alias- oder Dual-Path-Matrix (Optionen in drift_cleanup_plan §C.1 AUTH-ECM-01) |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | Governance Decision Record „ECM Identity“ (R-02); Operator-Ratifikation; ggf. Registry-Alias **oder** Config-Migration — **nicht** docs-only |

**Evidence:** `registry.py` L162–170 (`armstrong_cycle` StrategySpec), L232/L252–254 (`ecm_cycle` functional-only); `config&#47;config.toml` L492–502 vs L1370–1380; `STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md` §4. <!-- pt:ref-target-ignore -->

---

### AUTH-002 — Config section `strategy.ecm_cycle` ohne StrategySpec-Key

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Registry/Config · Strategy Layer |
| **Type** | **C** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** kein `StrategySpec` für `ecm_cycle` · **Registry/Config:** `[strategy.ecm_cycle]` in `config&#47;config.toml` aktiv; kein `[strategy.ecm_cycle]` in `config&#47;strategy_tiering.toml` · **Docs:** als BLOCKED (DOC-06) markiert | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Config-Section aligned to canonical `strategy_id` (`armstrong_cycle`) **oder** explizite „legacy config section“-Semantik mit load-path matrix |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | AUTH-001 Closure; Config-Governance-Entscheid (out of scope für Safe-Docs-Patch) |

**Evidence:** `config&#47;config.toml` L492; `strategy_tiering.toml` — kein `ecm_cycle`-Block; drift_cleanup_plan §2.1 DOC-06 = BLOCKED. <!-- pt:ref-target-ignore -->

---

### AUTH-003 — Feature-Engine path `src&#47;features/` vs Strategy-layer ECM <!-- pt:ref-target-ignore -->

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Documentation · Strategy Layer · Registry/Config |
| **Type** | **A** (docs layer B-01 CLOSED) + **D** (Schicht-Ambiguität bleibt) |
| **Status (docs layer)** | **CLOSED (2026-07-17)** — PR #5274 / B-01: `missing_features_plan.md` deferred/STRUCTURAL banner + Class C pointer; Feature-Engine remains Class C deferred (no runtime enablement) |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** ECM-Math in `src&#47;strategies&#47;ecm.py`, OOP in `src&#47;strategies&#47;armstrong&#47;` · **Registry/Config:** — · **Docs:** kanonischer Catalog (`FEHLENDE_FEATURES`) markiert `src&#47;features/` als deferred; `missing_features_plan.md` (DOC-03/B-01) **CLOSED** deferred-aligned via PR #5274 — residual Type D layer ambiguity unchanged | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Feature-Engine = Class C deferred; ECM = Strategy layer only — docs plan surface aligned; residual architecture ambiguity remains Type D |
| **Risk Level** | **MEDIUM** (residual Type D only; docs deferred path no longer stale) |
| **Resolution Dependency** | Docs layer B-01: **CLOSED** via PR #5274 · Residual Type D / code moves: **blocked** without separate Product-Entscheid |

**Evidence:** `src&#47;features/__init__.py` (Placeholder); `feature_state_map_v1.md` Class C/D; PR #5274; `docs/product/evidence/drift_b01_b07_missing_features_plan_deferred_alignment_v0_20260717T033503Z/`. <!-- pt:ref-target-ignore -->

---

### AUTH-004 — Parallel implementations: `ecm.py` (functional) vs `ArmstrongCycleStrategy` (OOP)

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** zwei Codepfade für ECM/Armstrong-Semantik ohne explizite „shared lib vs strategy“-Bindung · **Registry/Config:** unterschiedliche Loader-Refs (`ecm` vs `armstrong.armstrong_cycle_strategy`) · **Docs:** Wiring Inventory verzeichnet Beobachtung, entscheidet nicht |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Semantik-Entscheid: shared library **oder** single strategy **oder** dokumentierte research/production split |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | AUTH-001; Operator-Semantik-Entscheid (AUTH-ECM-02 in drift_cleanup_plan) |

**Evidence:** `src&#47;strategies&#47;ecm.py`; `registry.py` L232/L244; `STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md` §4–5. <!-- pt:ref-target-ignore -->

---

### AUTH-005 — Armstrong live-readiness metadata triangle

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Registry/Config · Documentation |
| **Type** | **C** + **B** |
| **Current Ownership (per layer)** | **Runtime:** NON-OPERATIONAL (nicht im Core) · **Strategy:** `registry.py` — `armstrong_cycle`: `tier="production"`, `is_live_ready=True`, `allowed_environments` inkl. `live` · **Registry/Config:** `config&#47;config.toml` `[strategy.armstrong_cycle]`: `tier="r_and_d"`, `is_live_ready=false`; `strategy_tiering.toml`: `allow_live=false`, `tier="r_and_d"` · **Docs:** Wiring Inventory § „Live-readiness metadata tension note“ | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Dual-Source-Contract-konforme Leseregel; **eine** ratifizierte Live-Readiness-Wahrheit pro `strategy_id` |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | `STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1`; separates governed alignment slice (nicht aus Read-Model inferieren) |

**Evidence:** `registry.py` L162–169; `config&#47;config.toml` L1370–1376; `config&#47;strategy_tiering.toml` L130–138; Wiring Inventory § „Live-readiness metadata tension note“. <!-- pt:ref-target-ignore -->

---

## 2. Double Play Authority

### AUTH-006 — Ops legacy evaluator vs MV2 composition matrix

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Strategy-adjacent Ops · Documentation |
| **Type** | **B** |
| **Status (docs markers)** | **CLOSED (2026-07-17)** — PR #5272 / B-03: both ops runbooks project `LEGACY_NON_AUTHORITATIVE` + Slice E crosslink |
| **Current Ownership (per layer)** | **Runtime:** kanonisch offline = `double_play_composition_matrix_v1` in `integrated_offline_trading_logic_replay_v1` · **Strategy:** — · **Registry/Config:** — · **Docs:** `MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` Slice E — Ops = `LEGACY_NON_AUTHORITATIVE` (runbooks reconciled) |
| **Expected Canonical Ownership** | MV2 composition matrix = einzige offline Decision-Core-Authority; Ops-Evaluator nur Annotation/non-authorizing (docs markers enforced; runtime rewire **not** authorized) |
| **Risk Level** | **HIGH** (residual if misread as runtime authority — mitigated by docs markers + Slice E) |
| **Resolution Dependency** | Docs markers: **CLOSED** via B-03 / PR #5272 · Runtime rewire: **blocked** — requires separate Adapt/Master-V2 design GO (not in Section B docs slices) |

**Evidence:** `src&#47;ops/double_play/specialists.py`; `evaluate_double_play_authority_boundary_v0.py`; `MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` Slice E; ops runbooks `double_play.md` + `double_play_specialists.md`; PR #5272; evidence `docs/product/evidence/drift_b03_ops_double_play_authority_markers_v0_20260717T032034Z/`. <!-- pt:ref-target-ignore -->

---

### AUTH-007 — Decision packet handoff vs runtime Double Play observations

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** `DoubleplayResolutionHandoffV1` = deklaratives Packet-Feld (`decision_packet_v1`); Ops-Evaluator liefert `active_specialist`, `switch_state`, scores — **kein** automatischer Mirror · **Strategy:** — · **Registry/Config:** — · **Docs:** Authority Map §95–101 explizit getrennt |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Expliziter Sync-Contract (field mapping, veto, review) **oder** dauerhafte Trennung mit klarer Consumer-Leseregel |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | „Adapt to Master V2“ Design Change (AUTH-DP-02); nicht Teil von Docs-Cleanup |

**Evidence:** `decision_packet_v1.py` / `local_evaluator_v1.py`; `MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` L95–101; drift_cleanup_plan §C.2 AUTH-DP-02.

---

### AUTH-008 — Multiple Double Play replay surfaces

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** (a) `integrated_offline_trading_logic_replay_v1` — composition matrix + entry/exit policy; (b) `offline_double_play_scenario_replay_v0` — Szenario-Replay mit Packet-Fixtures inkl. `ScopeCapitalEnvelopeHandoffV1`; (c) Ops `evaluate_double_play` — legacy · **Strategy:** — · **Registry/Config:** — · **Docs:** Class D „Double Play authority (canonical)“ → composition matrix |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Integrated Replay = canonical offline owner; andere Surfaces explizit subordinate/non-authoritative |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | B-06 Decision-authority map Ergänzung; WG-07 Closure |

**Evidence:** `feature_state_map_v1.md` §2.4; `offline_double_play_scenario_replay_v0.py`; drift report WG-07.

---

## 3. Registry Authority

### AUTH-009 — `breakout_confirmation_v1` orphan module

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Registry/Config |
| **Type** | **C** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** Modul `src&#47;strategies&#47;breakout_confirmation_v1.py` existiert (`CONFIRMATION_OWNER` self-declared) · **Registry/Config:** kein `StrategySpec`, nicht in `_STRATEGY_REGISTRY` oder functional set · **Docs:** AUTH-REG-01 / DEF-05 flagged | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Registry-Eintrag **oder** explizite experimental/deprecated Disposition **oder** Remove |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | Code+Registry slice (DEF-05); Operator-Entscheid disposition |

**Evidence:** `breakout_confirmation_v1.py` L17; drift report B-02/WG-04.

---

### AUTH-010 — Functional-only IDs without full OOP StrategySpec

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Registry/Config |
| **Type** | **C** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** `ecm_cycle`, `rsi_strategy`, `vol_breakout`, `mean_reversion_channel` in `_FUNCTIONAL_ONLY_STRATEGY_IDS` — Canonical Entry mit `factory_ref=functional:...` · **Registry/Config:** Loader-Map keys present; kein OOP Spec · **Docs:** ST-F01..04 NOT operational |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Einheitliche Alias-/Promotion-Policy (wie `el_karoui_vol_v1` → `el_karoui_vol_model`) **oder** dauerhafte functional-tier-Dokumentation |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | Registry alias policy ratification; AUTH-REG-02 |

**Evidence:** `registry.py` L252–254, L372–381; drift_cleanup_plan §C.3 AUTH-REG-02.

---

### AUTH-011 — `rsi_strategy` vs `rsi_reversion` dual identity

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Registry/Config · Documentation |
| **Type** | **C** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** `rsi_reversion` = StrategySpec; `rsi_strategy` = functional-only → module `rsi` · **Registry/Config:** beide in loader map; kein `_LEGACY_ALIASES`-Eintrag für `rsi_strategy` · **Docs:** feature_state_map Rename-Empfehlung |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Alias `rsi_strategy` → `rsi_reversion` (analog `el_karoui_vol_v1`) **oder** dokumentierte functional/OOP split |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | Registry alias policy; konsistent mit AUTH-010 |

**Evidence:** `registry.py` L86–90, L229, L253; feature_state_map_v1 §2.2.

---

### AUTH-012 — Registry production tier vs Runtime NON-OPERATIONAL rule

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Runtime Decision Core · Documentation |
| **Type** | **B** |
| **Current Ownership (per layer)** | **Runtime:** Validation Rule — nur Core-bound = wired; **0 operational** · **Strategy:** 23+ registrierte IDs, viele `tier="production"` · **Registry/Config:** Tiering TOML separat · **Docs:** CR-P1-01; post-A-Patch teilweise klargestellt |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Registry-Tier = Implementierungs-/Promotion-Metadaten; Runtime-Operational = Core-Wiring + Activation — immer explizit getrennt in Docs und Operator-UIs |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | WG-01 Registry→Suitability→Replay Read Model (B-04); DEF-02; keine Tier-Inflation ohne Core-Wiring |

**Evidence:** `feature_state_map_v1.md` Validation Rule; drift report CR-P1-01, WG-01; `suitability_binding_v1.py` L116–128 (offline snapshot, not runtime registry).

---

### AUTH-013 — Inconsistent alias policy: `el_karoui_vol_v1` aliased, `ecm_cycle` not

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Registry/Config · Documentation |
| **Type** | **C** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** `_LEGACY_ALIASES` enthält nur `el_karoui_vol_v1` → `el_karoui_vol_model` · **Registry/Config:** `ecm_cycle` bleibt separater canonical entry · **Docs:** DOC-09 Safe-Fix applied für El-Karoui; ECM weiter BLOCKED |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Konsistente Alias-Grammatik über alle Legacy-IDs |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | AUTH-001; Registry policy v2 planning |

**Evidence:** `registry.py` L330–341 vs L252–254; drift_safe_docs_patch_v1 §3 (DOC-06 offen).

---

## 4. Scope / Risk / Sizing Ownership

### AUTH-014 — Runbook three owners vs `capital_risk_sizing_v1` merge

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **B** + **D** |
| **Current Ownership (per layer)** | **Runtime:** Slice B — `evaluate_capital_risk_sizing_v1` merged chain (ScopeCapitalEnvelope → PreSizingRisk → Sizing → PostSizingRisk) in `capital_risk_sizing_v1.py` · **Strategy:** — · **Registry/Config:** — · **Docs:** Runbook v2.6 — separate Owner: Risk, Sizing, Scope Capital (`SCOPE_CAPITAL_ROLE=CAPITAL_ENVELOPE_OWNER`) |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Entweder (a) merged-by-intent mit expliziter Runbook-Annotation **oder** (b) drei dedizierte Replay-Steps — Architecture ratification |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | B-05 / AUTH-B-05; R-06 Scope Capital design note; DEF-03, DEF-04 |

**Evidence:** `capital_risk_sizing_v1.py` L4–7; Runbook v2.6 L232–234, L267; drift report B-03/B-04, WG-03, CR-P1-04.

---

### AUTH-015 — Scope Capital: Decision Packet handoff vs Replay chain absence

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **B** |
| **Current Ownership (per layer)** | **Runtime:** `ScopeCapitalEnvelopeHandoffV1` in `decision_packet_v1` / `local_evaluator_v1` — **input/handoff**; **nicht** in `integrated_offline_trading_logic_replay_v1` · **Strategy:** — · **Registry/Config:** — · **Docs:** WG-02; Class B „Scope Capital (separate Runbook owner)“ |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Dedizierter Replay-Step **oder** bewusst in Slice B sizing input merged — explizit ratifiziert |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | AUTH-014 Closure; R-06; DEF-03 |

**Evidence:** `local_evaluator_v1.py` L64; grep: no `ScopeCapital` in `integrated_offline_trading_logic_replay_v1.py`; `feature_state_map_v1.md` §2.2 Class B.

---

### AUTH-016 — Slice A vs Slice B authority split (replay ends before sizing)

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** Slice A Replay → evidence through entry/exit policy; Slice B Bridge → `capital_risk_sizing_v1` → order intent → firewall · **Strategy:** — · **Registry/Config:** — · **Docs:** feature_state_map Class A listet beide; `BOUND_NOT_ACTIVATED` |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Klare „canonical chain“-Dokumentation: welcher Slice welche Owner-Stufen bindet; keine implizite Vollständigkeit von Slice A allein |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | Canonical Core Runtime activation design (DEF-01); Runbook Step 29P/29Q boundary docs |

**Evidence:** `integrated_offline_trading_logic_replay_v1.py` (no capital_risk imports); `canonical_core_runtime_integration_intent_pipeline_bridge_v0.py` L7, L40–46.

---

### AUTH-017 — Decision Packet flow vs Integrated Replay (parallel MV2 paths)

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** (a) `evaluate_master_v2_local_flow_v1` / `decision_packet_v1` — assemble/validate/critic path; (b) `run_integrated_offline_trading_logic_replay_v1` — compute path · **Strategy:** — · **Registry/Config:** — · **Docs:** B-06/WG-07; Authority Map stage table „partial/unclear“ |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Integrated Replay = canonical **compute** owner; Decision Packet = canonical **handoff/evidence** schema — mit expliziter Richtungs- und Prioritätsregel |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | B-06 authority map supplement; DEF-01 activation stack |

**Evidence:** `master_v2&#47;__init__.py` exports both paths; drift report B-05/WG-07; `MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` §4 stage table. <!-- pt:ref-target-ignore -->

---

### AUTH-018 — Attestation bindings vs merged sizing module

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Runtime Decision Core · Meta/Governance · Documentation |
| **Type** | **D** |
| **Current Ownership (per layer)** | **Runtime:** `capital_risk_sizing_v1` — single module · **Strategy:** — · **Registry/Config:** — · **Docs/Meta:** `trading_core_decision_attestation_v1` referenziert separate slots (`scope_capital`, `sizing`) mit Owner-Refs |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Attestation slot model aligned to Runbook owners **or** attestation updated to reflect merged module semantics |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | AUTH-014; attestation contract review slice |

**Evidence:** `trading_core_decision_attestation_v1.py` L79–112; `capital_risk_sizing_v1.py` merged chain docstring.

---

## 5. Strategy ↔ Runtime Wiring (cross-cutting)

### AUTH-019 — No default Registry → Suitability → Replay wiring

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Runtime Decision Core · Documentation |
| **Type** | **B** |
| **Current Ownership (per layer)** | **Runtime:** `suitability_binding_v1` requires `SuitabilityStrategyRegistryV1` offline snapshot — not auto-built from `registry.py` · **Strategy:** full registry in `registry.py` · **Registry/Config:** — · **Docs:** WG-01; only `mv2_research_wiring_v1` builds adapter path |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Documented sequence + optional default snapshot builder — **not** implicit registry = core strategies |
| **Risk Level** | **HIGH** |
| **Resolution Dependency** | B-04 Read Model spec; DEF-02; WG-01 |

**Evidence:** `suitability_binding_v1.py` L116–128; `src&#47;backtest/mv2_research_wiring_v1.py`; drift report WG-01. <!-- pt:ref-target-ignore -->

---

### AUTH-020 — `el_karoui_vol_model` registry vs R&D documentation drift

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Strategy Layer · Documentation |
| **Type** | **A** (partially fixed) + **B** |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** `el_karoui_vol_model` StrategySpec, `tier="production"`, `is_live_ready=True` in registry · **Registry/Config:** tiering TOML `tier="r_and_d"`, `allow_live=false` · **Docs:** DOC-09 alias cleanup applied; tier tension analog AUTH-005 |
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Dual-source read per contract; consistent R&D vs production labeling |
| **Risk Level** | **MEDIUM** |
| **Resolution Dependency** | AUTH-005 pattern; strategy tiering reconciliation |

**Evidence:** `registry.py` L171–178; `strategy_tiering.toml` L146–153; drift_safe_docs_patch_v1 A-04.

---

## 6. Remaining Documentation Authority Drift (post Section A)

### AUTH-021 — `missing_features_plan.md` Feature-Engine stale DAG

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Documentation |
| **Type** | **A** |
| **Status** | **CLOSED (2026-07-17)** — PR #5274 / B-01+B-07: deferred/STRUCTURAL banner + Class C pointer + DAG NON-OPERATIONAL footnote on `missing_features_plan.md` |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** — · **Registry/Config:** — · **Docs:** `docs&#47;analysis/missing_features_plan.md` — STRUCTURAL/DEFERRED aligned (B-01/B-07 CLOSED); not operational wiring authority | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership** | Deferred header + link `feature_state_map_v1` Class C — **satisfied on main** (docs projection only; Feature-Engine remains NON-OPERATIONAL) |
| **Risk Level** | **LOW** |
| **Resolution Dependency** | None (B-01/B-07 reconciled on main via PR #5274 @ `721f28f52b81b01f01ec310eee0dbcdc75d10cce`) |

**Evidence:** drift_cleanup_plan §4 B-01/B-07 CLOSED; PR #5274; `docs/product/evidence/drift_b01_b07_missing_features_plan_deferred_alignment_v0_20260717T033503Z/`; binding discovery `docs/product/evidence/post_b01_b07_next_workstream_discovery_v1_20260717T034127Z/`.

---

### AUTH-022 — R&D stub status grammar inconsistency across FEHLENDE copies

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Documentation · Strategy Layer |
| **Type** | **A** |
| **Status** | **CLOSED (2026-07-17)** — PR #5270 merged `rd_strategy_status_grammar_v0`; FEHLENDE §5.2.1 uses stub / research-only / missing |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** ehlers, meta_labeling, bouchaud, gatheral classified research-only · **Registry/Config:** registered as `r_and_d` · **Docs:** DOC-12 / B-02 CLOSED — grammar owner `src/governance/rd_strategy_status_grammar_v0.py` + SSOT `docs/features/rd_strategy_status_grammar_v0.json` |
| **Expected Canonical Ownership** | Einheitliche Status-Tabelle: stub / research-only / missing (enforced fail-closed at grammar boundary) |
| **Risk Level** | **LOW** |
| **Resolution Dependency** | None (B-02 reconciled on main @ 1d099ca746cc5790cd6d35487e788bd3a5da7b44) |

**Evidence:** drift_cleanup_plan §4 B-02 CLOSED; PR #5270; docs/product/evidence/rd_strategy_status_grammar_v0_20260717T025957Z/; post-merge pack docs/product/evidence/post_drift_b02_next_workstream_discovery_v1_20260717T031201Z/.

---

### AUTH-023 — Psychology „Feature“ vs Reporting layer (residual path drift)

| Feld | Inhalt |
|------|--------|
| **Affected Layers** | Documentation · Strategy-adjacent code |
| **Type** | **A** (partially fixed) |
| **Current Ownership (per layer)** | **Runtime:** — · **Strategy:** — · **Registry/Config:** — · **Docs:** A-06 applied reporting banners; `docs&#47;features/psychology/` path bleibt · **Code:** `src&#47;reporting/psychology_*.py` | <!-- pt:ref-target-ignore -->
| **Expected Canonical Ownership (NOT ENFORCED YET)** | Reporting layer in docs; optional path move `docs&#47;reporting/psychology/` (Operator GO) | <!-- pt:ref-target-ignore -->
| **Risk Level** | **LOW** |
| **Resolution Dependency** | A-06 follow-up optional; DOC-07 closed for content, path optional |

**Evidence:** drift_safe_docs_patch_v1 A-06; feature_state_map_v1 DOC-07.

---

## 7. Summary Matrix

| Conflict ID | Kurzbezeichnung | Type | Risk | Primary Layer Collision |
|-------------|-----------------|------|------|-------------------------|
| AUTH-001 | `ecm_cycle` vs `armstrong_cycle` identity | C | HIGH | Strategy ↔ Registry/Config |
| AUTH-002 | Config `[strategy.ecm_cycle]` ohne Spec | C | HIGH | Registry/Config |
| AUTH-003 | `src&#47;features/` vs Strategy ECM | A+D | MEDIUM | Docs ↔ Strategy — **docs layer B-01 CLOSED** (PR #5274); residual Type D remains | <!-- pt:ref-target-ignore -->
| AUTH-004 | `ecm.py` vs `ArmstrongCycleStrategy` | D | MEDIUM | Strategy |
| AUTH-005 | Armstrong live-readiness triangle | C+B | HIGH | Strategy ↔ Registry/Config |
| AUTH-006 | Ops DP evaluator vs composition matrix | B | HIGH | Runtime ↔ Ops — **docs markers CLOSED** (PR #5272 / B-03); runtime rewire still blocked |
| AUTH-007 | Packet handoff vs runtime DP observations | D | MEDIUM | Runtime |
| AUTH-008 | Multiple DP replay surfaces | D | MEDIUM | Runtime |
| AUTH-009 | `breakout_confirmation_v1` orphan | C | MEDIUM | Strategy ↔ Registry |
| AUTH-010 | Functional-only IDs policy | C | MEDIUM | Registry |
| AUTH-011 | `rsi_strategy` vs `rsi_reversion` | C | MEDIUM | Registry |
| AUTH-012 | Production tier vs NON-OPERATIONAL | B | HIGH | Strategy ↔ Runtime |
| AUTH-013 | Inconsistent alias policy (ECM) | C | MEDIUM | Registry |
| AUTH-014 | Runbook 3 owners vs merged sizing | B+D | HIGH | Runtime ↔ Docs |
| AUTH-015 | Scope Capital packet vs replay gap | B | HIGH | Runtime |
| AUTH-016 | Slice A / Slice B split | D | MEDIUM | Runtime |
| AUTH-017 | Decision Packet vs Integrated Replay | D | HIGH | Runtime |
| AUTH-018 | Attestation slots vs merged module | D | MEDIUM | Runtime ↔ Meta |
| AUTH-019 | No default Registry→Core wiring | B | HIGH | Strategy ↔ Runtime |
| AUTH-020 | El Karoui tier tension | A+B | MEDIUM | Strategy ↔ Docs |
| AUTH-021 | `missing_features_plan` stale DAG | A | LOW | Docs — **CLOSED** (PR #5274 / B-01+B-07) |
| AUTH-022 | R&D stub status grammar | A | LOW | Docs ↔ Strategy — **CLOSED** (PR #5270 / B-02) |
| AUTH-023 | Psychology path residual | A | LOW | Docs |

### Count by Type

| Type | Count |
|------|-------|
| **A** — Pure Documentation Mismatch | 5 listed (AUTH-003 residual A+D; AUTH-020/023 open; AUTH-021/022 CLOSED) |
| **B** — Strategy vs Runtime Misalignment | 8 |
| **C** — Registry Ownership Conflict | 8 |
| **D** — Architectural Ambiguity | 10 |

*Hinweis: Mehrfachklassifikation bei kombinierten Typen (z. B. AUTH-003 = A+D) — Summary zählt Primärtyp.*

### Count by Risk

| Risk | Count |
|------|-------|
| HIGH | 9 |
| MEDIUM | 11 |
| LOW | 3 |

---

## 8. Resolution Dependency Graph (read-only — keine Ausführung)

```text
AUTH-001 (ECM Identity Record)
├── AUTH-002 (Config alignment)
├── AUTH-004 (ecm.py vs Armstrong semantics)
├── AUTH-013 (alias policy consistency)
└── DOC-06 closure

AUTH-014 (Scope/Risk/Sizing architecture ratification)
├── AUTH-015 (Scope Capital replay integration)
├── AUTH-016 (Slice A/B documentation)
├── AUTH-018 (Attestation alignment)
├── DEF-03, DEF-04
└── B-05

AUTH-017 (MV2 path canonicalization)
├── AUTH-008 (DP replay surfaces)
├── B-06
└── DEF-01 (activation)

AUTH-019 (Registry→Core wiring)
├── AUTH-012 (tier vs operational)
├── B-04
└── DEF-02

AUTH-006 (DP authority — docs markers CLOSED via B-03 / PR #5272)
└── Runtime rewire residual: INTENTIONAL_POLICY_STATE / separate Adapt GO only
```

---

## 9. Explicit Non-Actions (this artifact)

- Keine Konfliktauflösung
- Keine Registry-Alias-Mutation
- Keine Config-Migration
- Keine Runtime-Bridge-Aktivierung
- Keine Reclassifikation der Feature State Map
- Keine Enforcement der „Expected Canonical Ownership“-Spalte

**Nächster Schritt (Operator):** Priorisierung HIGH-Konflikte AUTH-001, AUTH-005, AUTH-006, AUTH-012, AUTH-014, AUTH-015, AUTH-017, AUTH-019 für separates Governance/Architecture-Review — **nicht** in diesem Scan.

---

## 10. Cross-References

| Artefakt | Rolle |
|----------|-------|
| [`feature_state_map_v1.md`](feature_state_map_v1.md) | Kanonische Feature-Wahrheit |
| [`drift_cleanup_plan_v1.md`](drift_cleanup_plan_v1.md) | Safe vs Blocked vs Deferred Plan |
| [`drift_safe_docs_patch_v1.md`](../audit/drift_safe_docs_patch_v1.md) | Section A applied evidence |
| [`feature_drift_reconciliation_report_v1.md`](../audit/feature_drift_reconciliation_report_v1.md) | Frozen audit source |
| [`STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md`](../ops/specs/STRATEGY_ECM_ARMSTRONG_WIRING_INVENTORY_READ_MODEL_V0.md) | ECM wiring read-model |
| [`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`](../ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md) | MV2 authority boundaries |

**Matrix-Owner:** Authority Conflict Matrix v1  
**Evidence frozen at:** `2f1672bee8761f8d50def3f6ef31cc803824b2e9`
