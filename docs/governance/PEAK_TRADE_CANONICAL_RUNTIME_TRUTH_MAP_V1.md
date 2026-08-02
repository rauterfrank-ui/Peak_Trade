# Peak Trade — Canonical Runtime Truth Map V1

```text
DOCUMENT_CLASS=CURRENT_RUNTIME_TRUTH
CAPABILITY_ID=CANONICAL_RUNTIME_TRUTH_MAP_AND_DOCUMENTATION_ALIGNMENT_V1
AUTHORITY=DOCUMENTARY_RUNTIME_TRUTH_ONLY
THIS_DOCUMENT_IS_NOT_TARGET_ARCHITECTURE=true
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
THIS_DOCUMENT_DOES_NOT_AUTHORIZE_RUNTIME_ACTIVATION=true
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false
CORE_LOGIC_CHANGE=false
RUNTIME_CODE_CHANGE=false
TRADING_CONFIG_MUTATION=false
ACTIVATION_CHANGE=false
```

**Rolle:** Kanonische Ist-Zustandskarte der Runtime-Wahrheit.  
**Nicht-Rolle:** Kein Zielbild, keine Activation-Authority, keine zweite Trading-SSOT.

Normative Governance-/Implementierungs-SSOT bleibt:

[`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md)

Capability-Closure-/Trading-Path-Arbeitsanweisung:

[`Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md`](Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md)

Navigations-Einstieg (keine Semantik):

[`PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md)

---

## 1. Repository baseline

| Feld | Wert |
|------|------|
| `ORIGIN_MAIN_SHA` | `4bac3303bd74967c0c81d02c5de16c431301e12e` |
| `VERIFICATION_DATE_UTC` | `2026-08-02T02:54:14Z` |
| `VERIFICATION_MODE` | local real git worktree; `git fetch origin --prune`; HEAD == `origin/main` before branch creation |
| `REPOSITORY_ROOT` | `/Users/frnkhrz/Peak_Trade_assessment_93b45a7` |
| `GIT_DIR` | `/Users/frnkhrz/Peak_Trade/.git/worktrees/Peak_Trade_assessment_93b45a7` |
| `LOCAL_REAL_REPOSITORY` | `true` (linked worktree of Peak_Trade; direct `.git` access) |
| `BASELINE_VALIDITY_RULE` | Every later implementation PR must revalidate against its actual `origin/main`. Counts/paths here are evidence snapshots, not timeless constants. |

### Verbindliche aktuelle Semantik (Snapshot)

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=BOUND_NOT_ACTIVATED
LIVE_TRADING=FAIL_CLOSED
DASHBOARD=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_TRADING_INPUT=false
DASHBOARD_SSOT=false
VOLATILITY_NUMERIC_MAX_AGE=WATCHDOG_ONLY_NON_ENFORCING
VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT=false
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
PHASE_1_MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false
UNIVERSE_RANKING_TRADING_AUTHORITY=false
PRODUCTIVE_RECONCILIATION_BOUND=false
FUTURES_ACCOUNTING_RUNTIME_BOUND=false
ECONOMIC_VALIDITY_OFFLINE_GATE_STATE=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
```

---

## 2. Status semantics (mandatory)

These terms are not synonyms:

| Status | Meaning |
|--------|---------|
| `DOCUMENTED` | Described in docs only |
| `DTO_EXISTS` | Types/contracts exist |
| `CODE_EXISTS` | Implementation exists |
| `CONFIG_EXISTS` | Config/artifact exists |
| `CONFIG_CONSUMED` | Productive entrypoint reads the config |
| `BOUND` | Wired into a productive host/call-graph |
| `RUNTIME_REACHABLE` | Reachable from a productive entrypoint under authorized conditions |
| `ACTIVATED` | Explicitly activated for runtime effect |
| `PERSISTED` | Durable state/evidence owner exists and writes |
| `RESTART_PROVEN` | Restart/recovery proven by evidence |
| `FAILURE_SAFE` | Fail-closed behavior proven |
| `EVIDENCE_PROVEN` | Verified evidence pack exists |
| `CAPABILITY_CLOSED` | Full closure criteria met |

Audit classification categories:

| Category | Treatment |
|----------|-----------|
| `INTENTIONAL_SAFETY_BARRIER` | Preserve; not an implementation defect |
| `CURRENT_PHASE_GAP` | Close in current single-future phase |
| `DEFERRED_REQUIRED_CAPABILITY` | Register owner/trigger/phase; implement later |
| `ORPHANED_REUSABLE_IMPLEMENTATION` | Prefer reuse after reachability proof |
| `LEGACY_DEAUTHORIZED` | Do not reactivate; prevent parallel authority |
| `DOCUMENTATION_DRIFT` | Correct docs without inventing runtime claims |
| `INSUFFICIENT_EVIDENCE` | No conclusion until verified |

---

## 3. CURRENT RUNTIME TRUTH

### 3.1 Productive / analytical entrypoints (enumerated)

| Entrypoint | Class | Activation | Evidence basis |
|------------|-------|------------|----------------|
| `scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py` | analytical simulated-economics bridge | `BOUND_NOT_ACTIVATED` for live order runtime; analytical simulation path only | package constants `RUNTIME_BRIDGE_LIVE_ACTIVATED=False`, `ORDERS_AUTHORIZED=False`, `LIVE_AUTHORIZED=False` |
| `scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py` | gated wallclock observation | not default-authorized; requires scoped GO/auth artifacts | Map of Truth / IPSO runbooks; non-authorizing by docs |
| `scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py` | productive public-MD issuance helper | merge does not authorize session | IPSO productive issuance runbook |
| `scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` | research/watchdog evidence accumulation | non-enforcing | max-age research contracts (`ENFORCEMENT_ENABLED=False`) |
| `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` | offline Master V2 / Double Play decision owner | offline / bound-not-activated | feature_state_map_v1; bridge `DECISION_AUTHORITY_OWNER` |

### 3.2 Reachable vs bound-not-activated vs blocked call-graphs

**Reachable analytical path (current):**

```text
Public Market Data
→ gated Wallclock Session (when separately authorized)
→ analytical Decision/Economics Bridge
→ integrated offline Master V2 / Double Play
→ intended action
→ simulated economics
→ evidence
```

**Bound but not activated:**

- Canonical runtime bridge live-order path: `RUNTIME_BRIDGE_LIVE_ACTIVATED=false` → status `BOUND_NOT_ACTIVATED`
- Master V2 / Double Play offline integration: wired in offline replay / analytical bridge; not live-activated
- Typed volatility presence / numeric max-age telemetry: bound as watchdog/research; enforcement false

**Deactivated / not authorized / fail-closed:**

- Live exchange order submission (`LiveNotImplementedError` / live package guards)
- Testnet order submission (`TESTNET_AUTHORIZED=false` on bridge constants)
- Paper execution as order authority (`PAPER_EXECUTION_AUTHORIZED=false`)
- Multi-future runtime (`MULTI_FUTURE_RUNTIME_AUTHORIZED=false`)
- Top-20 → Top-5 productive rotation (`TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false`)
- Universe/ranking as trading authority (`UNIVERSE_RANKING_TRADING_AUTHORITY=false`)
- Dashboard write/trading input (`DASHBOARD_TRADING_INPUT=false`)

### 3.3 Authority owners by capability (documentary)

| Capability | Authority owner (code/doc) | Current status |
|------------|----------------------------|----------------|
| Master V2 offline decision | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | `BOUND` offline / `BOUND_NOT_ACTIVATED` live |
| Double Play composition | `double_play_composition_matrix_v1` (canonical; legacy ops evaluator deauthorized) | `BOUND` offline |
| Wallclock analytical bridge | `ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1` | analytical reachable; live activation false |
| Portfolio economics model (simulated) | `ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1` | simulation only |
| Dashboard / Market UI | Market Dashboard Landscape V2 consumer surfaces | `READ_ONLY_CONSUMER`; `AUTHORITY_EFFECT=NONE` |
| Numeric volatility max-age | `canonical_volatility_numeric_max_age_*` research/policy contracts | watchdog/research/diagnostic; `enforcement_enabled=false` |
| Economic validity offline gate | progress registry + economic validity policy surfaces | `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false` |
| Live execution | `src/live` fail-closed / not implemented path | `INTENTIONAL_SAFETY_BARRIER` |

### 3.4 Active runtime-config truth (no config mutation; documentary)

Documented/code-constant effective safety posture for Phase-1 analytical bridge:

```text
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PAPER_EXECUTION_AUTHORIZED=false
CREDENTIALS_AUTHORIZED=false
AUTO_PROMOTION_AUTHORIZED=false
ECONOMIC_VALIDITY_PASS=false
RUNTIME_BRIDGE_LIVE_ACTIVATED=false
ENFORCEMENT_ENABLED=false   # numeric max-age
```

**Config-consumer caveat (`INSUFFICIENT_EVIDENCE` for global effective max positions):**

- Code default `src/live/risk_limits.py` exposes `max_open_positions = 5` as a class default.
- Historical/docs surfaces also mention other values (e.g. `10`, `2`).
- Phase-1 required semantics remain `PHASE_1_MAX_POSITIONS=1` / `SINGLE_SELECTED_FUTURE`.
- This Truth Map does **not** mutate config. Effective productive consumer proof for every Phase-1 entrypoint is deferred to Capability 0.3 (`Config Truth Alignment`). Classification: `CURRENT_PHASE_GAP` + partial `INSUFFICIENT_EVIDENCE` until consumer-trace closure.

### 3.5 Persistence / evidence / restart / economic gate

| Surface | Owner / status | Notes |
|---------|----------------|-------|
| Persistence | session/evidence ledgers under governed ops/research paths | no claim of full restart-proven portfolio persistence |
| Evidence | IPSO / wallclock bridge / vol-max-age research ledgers; progress registry | last baseline SHA for this map: `4bac3303…` |
| Restart / recovery | DR/runbook surfaces exist; full runtime restart proof | `RESTART_PROVEN=false` for canonical trading runtime (`INSUFFICIENT_EVIDENCE` / `CURRENT_PHASE_GAP`) |
| Economic Validity Offline Gate | registry authoritative fields | `ECONOMIC_VALIDITY_OFFLINE_GATE_STATE=false` / `PASS=false` |
| Productive reconciliation in runtime host | present but unbound in STEP-29U inventory | `PRODUCTIVE_RECONCILIATION_BOUND=false` |
| Futures accounting in runtime path | unwired / not runtime-bound | `FUTURES_ACCOUNTING_RUNTIME_BOUND=false` |

### 3.6 Known gaps (current)

1. Universe → Ranking → Single Selected Future persistence + runtime authority binding
2. Productive reconciliation host binding
3. Futures accounting runtime wiring
4. Canonical runtime activation (still must remain non-live)
5. Restart/recovery proof for productive runtime
6. Strategy registry full productive binding
7. Config truth alignment for `max_open_positions` effective consumers
8. Active-set rotation policy is deferred design reminder only (not productive Top-5)

### 3.7 Last verifiable evidence anchors

| Anchor | Path / claim | Class |
|--------|--------------|-------|
| Feature state map | `docs/governance/feature_state_map_v1.md` — `BOUND_NOT_ACTIVATED` / 0 live operational features | CURRENT_RUNTIME_TRUTH (snapshot SHA older than baseline; semantics still cited) |
| Bridge constants | `src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/constants_v1.py` | CURRENT_RUNTIME_TRUTH |
| Max-age non-enforcing | `ENFORCEMENT_ENABLED=False` in max-age policy/research contracts | CURRENT_RUNTIME_TRUTH |
| Dashboard consumer-only | Market Dashboard Landscape V2 `DASHBOARD_ROLE=PURE_READ_ONLY_CONSUMER` | CURRENT_RUNTIME_TRUTH |
| Economic gate false | `PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md` authoritative fields | CURRENT_RUNTIME_TRUTH |
| Forensic runbook baseline | Capability Closure Runbook header @ same SHA | CURRENT_RUNTIME_TRUTH + working runbook |

---

## 4. TARGET ARCHITECTURE (strictly separated)

Target path (not current runtime):

```text
Futures Discovery
→ Governed Universe
→ Ranking
→ Active-Set Selection
→ Per-Instrument Market State
→ Master V2
→ Double Play
→ Risk
→ Safety
→ Intent
→ Execution
→ Reconciliation
→ Portfolio State
→ Evidence
→ Restart Recovery
→ Operator Oversight
```

Primary target/governance SSOT documents:

- `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md` — `DOCUMENT_CLASS=TARGET_ARCHITECTURE` (contains Phase-1 safety bounds that remain currently binding)
- `docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md` — `DOCUMENT_CLASS=TARGET_ARCHITECTURE`
- `docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md` — deferred required capability reminder (not productive Top-5)

**Forbidden reading:** Do not treat target architecture, DTOs, offline tests, or deactivated bindings as activated runtime capabilities.

---

## 5. Trading-first priority (canonical)

```text
Market Data
→ Features
→ Market State
→ Master V2
→ Double Play
→ Bull/Bear
→ Risk
→ Safety
→ Intent
→ Execution
```

Numeric Volatility Max-Age remains watchdog/research/diagnostic/non-enforcing and must not displace this trading path.

---

## 6. Semantik guards (must remain visible)

```text
BOUND_NOT_ACTIVATED != READY
BOUND_NOT_ACTIVATED != ACTIVE
BOUND_NOT_ACTIVATED != ACTIVATED
LIVE_TRADING=FAIL_CLOSED
DASHBOARD=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_TRADING_INPUT=false
DASHBOARD_SSOT=false
VOLATILITY_NUMERIC_MAX_AGE=WATCHDOG_ONLY_NON_ENFORCING
VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT=false
PHASE_1_SELECTION=SINGLE_SELECTED_FUTURE
PHASE_1_MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
TOP20_OBSERVATION_OR_RESEARCH != TOP5_PRODUCTIVE_ROTATION != TOPN_ACTIVE_SET
TOP20_TO_TOP5_PRODUCTIVE_ROTATION=false
```

Protected cores (must not be changed by this documentation capability):

- Master V2, Double Play, Bull/Bear, Dynamic Scope, Composition, Confirmation, Entry/Exit precedence, Risk, Safety

---

## 7. Forensic document inventory (selected relevant set)

Legend for `DOCUMENT_CLASS_*`:

- `CURRENT` = `CURRENT_RUNTIME_TRUTH`
- `TARGET` = `TARGET_ARCHITECTURE`
- `HIST` = `HISTORICAL`

| DOCUMENT_PATH | CLASS_CURRENT | CLASS_PROPOSED | LAST_RELEVANT_SHA_OR_DATE | RUNTIME_CLAIMS | TARGET_ARCHITECTURE_CLAIMS | AUTHORITY_CLAIMS | ACTIVATION_CLAIMS | CONFLICTS_WITH_CURRENT_REPOSITORY | REQUIRED_CORRECTION | CORRECTION_APPLIED |
|---|---|---|---|---|---|---|---|---|---|---|
| `docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md` | CURRENT | CURRENT | `4bac3303…` / 2026-08-02 | Ist-Zustand only | separated §4 | documentary only | none | none | create | yes |
| `docs/governance/Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md` | CURRENT+working | CURRENT+working | baseline `4bac3303…` | BOUND_NOT_ACTIVATED etc. | §1.1 target separated | owner/operator working authority | fail-closed | internal title V1.1 vs filename V1_2 | store + note mismatch; do not silently rewrite | yes (stored; mismatch documented) |
| `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` | navigation | navigation + CURRENT pointer | main @ baseline | LIVE/ORDERS false | autonomy wording risk | no semantics | none | “vollautonomes Handelssystem” can be read as Ist | clarify target vs current; add Truth Map pointer + DOCUMENT_CLASS | yes |
| `docs/governance/feature_state_map_v1.md` | CURRENT snapshot | CURRENT | header SHA `2f1672bee…` / 2026-07-05 | BOUND_NOT_ACTIVATED; 0 live ops | none primary | decision-core owners | none live | older SHA than baseline | add DOCUMENT_CLASS; keep snapshot caveat | yes |
| `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md` | mixed SSOT | TARGET (+ Phase-1 current bounds) | adopted SSOT | Phase-1 MAX_POSITIONS=1; BOUND_NOT_ACTIVATED markers | full autonomy path | canonical SSOT | non-authorizing alone | target can be over-read as complete runtime | DOCUMENT_CLASS header | yes |
| `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4_current_state_multi_candidate_research_fleet.md` | HIST/adoption | HIST | historical | research fleet state | autonomy | none live | none | historical path | DOCUMENT_CLASS=HISTORICAL | yes |
| `docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.1_multi_future_target_model_clarification.md` | TARGET/HIST | TARGET | historical clarification | Phase-1 vs multi-future | multi-future target | none live | none | none material | DOCUMENT_CLASS=TARGET_ARCHITECTURE | yes |
| `docs/architecture/PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md` | TARGET | TARGET | DOCS_TRUTH_MAP cites as target | not full Ist | unified system target | two authority domains | none by reading | none if labeled | DOCUMENT_CLASS header | yes |
| `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md` | CURRENT progress | CURRENT | continuously updated | many ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false | step ladder | non-authorizing | blocked rewire | none for gate=false | DOCUMENT_CLASS header | yes |
| `docs/governance/PEAK_TRADE_RUNBOOK_EXECUTION_GOVERNANCE_V1.md` | governance | TARGET/governance | v1 | none live | package sequencing | non-authorizing | none | none | DOCUMENT_CLASS=TARGET_ARCHITECTURE | yes |
| `docs/ops/registry/DOCS_TRUTH_MAP.md` | CURRENT registry | CURRENT | ops registry | drift mapping | points to target runbooks | none | none | none | pointer to Runtime Truth Map | yes |
| `docs/ops/registry/REPO_TRUTH_CLAIMS.md` | CURRENT | CURRENT | ops registry | path-existence claims | none | none | none | none | none beyond inventory | no (no drift) |
| `docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md` | CURRENT dashboard | CURRENT | post-PR5548 closeout | PURE_READ_ONLY_CONSUMER; AUTHORITY_EFFECT=NONE | product planning | consumer-only | route read-only active ≠ trading active | “COMPLETE” refers to landscape consumer closeout, not trading runtime | DOCUMENT_CLASS + clarify COMPLETE≠trading activated | yes |
| `docs/ops/specs/MASTER_V2_DECISION_AUTHORITY_MAP_V1.md` | CURRENT/TARGET mix | CURRENT for authority map | INSUFFICIENT_EVIDENCE for full SHA | decision authority map | may include future | Master V2 authority | none live claimed here without read-through | INSUFFICIENT_EVIDENCE for conflicting claims without full scan | classify only | yes (class header if present/edited) |
| `docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md` | CURRENT | CURRENT | contract v0 | MARKET_DASHBOARD_AUTHORITY=false | lane taxonomy | authority levels | none | none material | DOCUMENT_CLASS | yes |
| `docs/ops/specs/RECONCILIATION_FLOW_SPEC.md` | TARGET/spec | TARGET | spec | pilot/safety recon | recon flow | safety | not productive host-bound | productive recon unbound | DOCUMENT_CLASS=TARGET_ARCHITECTURE | yes |
| `docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md` | CURRENT | CURRENT | inventory | reconciliation PRESENT_BUT_UNBOUND | later bind | none live | none | none | DOCUMENT_CLASS | yes |
| `docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md` | deferred reminder | TARGET/deferred | reminder | IMPLEMENTATION_STARTED=false | Top20→TopN later | ranking≠authority | none | Top-5 must not be called productive/regressed | DOCUMENT_CLASS=TARGET_ARCHITECTURE + deferred marker | yes |
| `docs/PHASE_42_TOPN_PROMOTION.md` | HIST/TARGET risk | HIST | phase doc | promotion language risk | TopN | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | may over-claim TopN readiness | DOCUMENT_CLASS=HISTORICAL; no Top5 productive claim | yes |
| `docs/ops/specs/MASTER_V2_CANONICAL_VOLATILITY_*` (family) | research/CURRENT | CURRENT research | many | watchdog/research | later enforcement discussion only | non-enforcing | research sessions only | enforcement must stay false | no enforcement uplift; family noted | partial (family rule in Truth Map; no mass rewrite) |
| `docs/webui/observability/UNIVERSE_SELECTION_READMODEL_V1.md` | CURRENT readmodel | CURRENT | webui | universe readmodel | selection UI | not trading authority | none | ranking≠trading authority | DOCUMENT_CLASS + authority false note | yes |
| `docs/LIVE_OPERATIONAL_RUNBOOKS.md` | HIST/ops index | HIST/non-authorizing | live ops overview | operational wording risk | live ops | non-authorizing | none | “operational” ≠ live-ready | DOCUMENT_CLASS=HISTORICAL + non-authorizing preserved | yes if edited; else inventory only |
| `docs/governance/READ_ONLY_CANONICAL_CHAIN_AND_ZERO_TRADE_BLOCKER_REAUDIT_V1.md` | CURRENT audit | CURRENT/HIST evidence | reaudit | zero-trade blockers | none | fail-closed | none | none | DOCUMENT_CLASS | yes |
| `docs/governance/Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md` | governance contract | TARGET/governance | PR#5226 markers | slice complete ≠ economic validity | chain repair | no runtime unlock | blocked slice 2 | “SLICE_1_COMPLETE” is wiring slice, not live | DOCUMENT_CLASS=TARGET_ARCHITECTURE | yes |
| Futures accounting runtime docs | scattered | INSUFFICIENT_EVIDENCE | — | unwired claim in closure runbook | accounting target | none proven productive | none | productive binding false | keep `FUTURES_ACCOUNTING_RUNTIME_BOUND=false` | no code change |
| Strategy registry wiring | feature_state_map Class B | CURRENT gap | feature map | many strategies unwired | registry closure later | none live | none | do not call fully integrated | none beyond truth map | inventory only |
| Shadow / Paper / Testnet / Live policy docs | mixed | CURRENT fail-closed + TARGET later | many | fail-closed | ladder 29U–29Z | safety | blocked | none if fail-closed preserved | no activation language uplift | inventory + guards |

### Inventory counts (this capability)

```text
DOCUMENTS_INVENTORIED=24_PRIMARY_PLUS_FAMILIES
CURRENT_RUNTIME_TRUTH_DOCUMENTS=12
TARGET_ARCHITECTURE_DOCUMENTS=8
HISTORICAL_DOCUMENTS=4
INSUFFICIENT_EVIDENCE_ITEMS=3
```

`INSUFFICIENT_EVIDENCE_ITEMS`:

1. Global effective `max_open_positions` consumer winner across all Phase-1 productive entrypoints (needs Capability 0.3 trace)
2. Full restart/recovery proof for canonical trading runtime host
3. Exhaustive futures-accounting owner/consumer matrix beyond unbound claim

---

## 8. Documentation drift found and corrected in this PR

| Drift | Evidence | Correction |
|-------|----------|------------|
| Map of Truth system purpose readable as already fully autonomous runtime | “vollautonomes Handelssystem” without Ist/Ziel separation | Clarified as target autonomy program; pointed to this Truth Map for Ist |
| Missing canonical Ist-Zustand owner file | no `PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md` before | Created |
| Missing DOCUMENT_CLASS on key maps/runbooks | headers absent | Added on selected high-risk docs only |
| Filename V1_2 vs internal title V1.1 on closure runbook | source header line 1 | Documented; content preserved byte-identical; no silent retitle |
| “COMPLETE” on dashboard landscape | landscape consumer closeout markers | Clarified COMPLETE ≠ trading runtime activated / ≠ SSOT |

No cosmetic repository-wide rewrite. No Master V2 / Double Play / Bull-Bear / Scope / Confirmation / Risk / Safety logic edits. No Python/runtime/config mutation.

---

## 9. Closure checklist for Capability 0.1

```text
DOCS_ACCURATE=true
RUNTIME_FLAGS_REFERENCED=true
TARGET_VS_CURRENT_SEPARATED=true
DASHBOARD_AUTHORITY_FALSE=true
VOL_MAX_AGE_ENFORCING_FALSE=true
BOUND_NOT_ACTIVATED_VISIBLE=true
SINGLE_SELECTED_FUTURE_VISIBLE=true
MAX_POSITIONS_ONE_VISIBLE=true
MULTI_FUTURE_UNAUTHORIZED_VISIBLE=true
TOP20_TOP5_TOPN_SEMANTICS_SEPARATED=true
CORE_LOGIC_CHANGE=false
RUNTIME_CODE_CHANGE=false
TRADING_CONFIG_MUTATION=false
ACTIVATION_CHANGE=false
```
