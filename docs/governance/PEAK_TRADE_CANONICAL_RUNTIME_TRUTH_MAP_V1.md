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

Aktuelle normative Governance-/Implementierungsautorität:

[`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md)

Historische Vorgängerautorität (SUPERSEDED):

[`Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`](Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md)

Capability-Closure-/Trading-Path-Arbeitsanweisung:

[`Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md`](Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md)

Navigations-Einstieg (keine Semantik):

[`PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md)

---

## 1. Repository baseline

| Feld | Wert |
|------|------|
| `ORIGIN_MAIN_SHA` | `58af5100ef8c307f4dbe5e95fe4a13102272a1b0` |
| `VERIFICATION_DATE_UTC` | `2026-08-02T05:40:00Z` |
| `VERIFICATION_MODE` | local real git worktree; `git fetch origin --prune`; HEAD == `origin&#47;main` before Capability 4.1 branch creation |
| `REPOSITORY_ROOT` | `/Users/frnkhrz/Peak_Trade_assessment_93b45a7` |
| `GIT_DIR` | `/Users/frnkhrz/Peak_Trade/.git/worktrees/Peak_Trade_assessment_93b45a7` |
| `LOCAL_REAL_REPOSITORY` | `true` (linked worktree of Peak_Trade; direct `.git` access) |
| `BASELINE_VALIDITY_RULE` | Every later implementation PR must revalidate against its actual `origin&#47;main`. Counts/paths here are evidence snapshots, not timeless constants. |
| `CONFIG_TRUTH_ALIGNMENT` | Capability 0.3 owner `ops.config_truth_alignment_contract_v1` — Phase-1 effective values proven; Cap 4.1 readiness preserves non-activation |

### Verbindliche aktuelle Semantik (Snapshot)

```text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE
STATEFUL_RUNTIME_READY_FOR_ACTIVATION=true
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
PUBLIC_MD_RUNTIME_CAPABLE=true
PUBLIC_MD_NETWORK_SESSION_OBSERVED=false
RUNTIME_ACTIVATED=true
LIVE_TRADING=FAIL_CLOSED
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
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
PRODUCTIVE_RECONCILIATION_BOUND=true
FUTURES_ACCOUNTING_RUNTIME_BOUND=true
FULL_SINGLE_FUTURE_CALL_GRAPH_PROVEN=true
ECONOMIC_VALIDITY_OFFLINE_GATE_STATE=false
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
```

**Status note (CURRENT vs TARGET):** Capability 7.2 activates the internal stateful no-order runtime (`FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE` / `SIMULATED_EXECUTION_ACTIVE`) with public-MD capability but **without** starting a public-MD network session. Forbidden remain: live/testnet/paper-exchange orders, credentials, real capital, multi-future. Phase 9.2 is the separate long-running public-MD simulation evidence program.

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
| `scripts/ops/run_single_future_canonical_runtime_deterministic_offline_evidence_v1.py` | Cap 5.1 deterministic offline evidence entrypoint | `READY_FOR_ACTIVATION`; `RUNTIME_ACTIVATED=false`; offline replay only | Cap 5.1 evidence; reuses Cap 4.1/2.4 host; fixtures only; no network/auth consumption/activation |
| `scripts/ops/run_single_future_canonical_runtime_pre_activation_closure_v1.py` | Cap 4.1 pre-activation closure entrypoint | `READY_FOR_ACTIVATION`; `RUNTIME_ACTIVATED=false` | Cap 4.1 evidence; reuses Cap 2.4 host; no live/orders/auth consumption |
| `scripts/ops/run_single_selected_future_runtime_binding_v1.py` | Cap 2.4 productive single-future analytical host | host reused by Cap 4.1/5.1; not a second canonical host | Cap 2.4 / 3.1 / 4.1 / 5.1 evidence |
| `scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py` | analytical simulated-economics bridge | live order path remains non-activated; analytical simulation path only | package constants `RUNTIME_BRIDGE_LIVE_ACTIVATED=False`, `ORDERS_AUTHORIZED=False`, `LIVE_AUTHORIZED=False` |
| `scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py` | gated wallclock observation | not default-authorized; requires scoped GO/auth artifacts | Map of Truth / IPSO runbooks; non-authorizing by docs |
| `scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py` | productive public-MD issuance helper | merge does not authorize session | IPSO productive issuance runbook |
| `scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` | research/watchdog evidence accumulation | non-enforcing | max-age research contracts (`ENFORCEMENT_ENABLED=False`) |
| `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` | offline Master V2 / Double Play decision owner | offline / non-activated live | feature_state_map_v1; bridge `DECISION_AUTHORITY_OWNER` |

### 3.2 Reachable vs bound-not-activated vs blocked call-graphs

**Reachable analytical single-future path (current, Cap 4.1 proven offline):**

```text
Authorization Contract Validation (offline structural; no consumption)
→ Analytical Session Lock (local; not network trading session)
→ Governed Futures Universe
→ Productive Ranking
→ Persisted Single Selected Future
→ Selection Integrity / Venue-Native Binding
→ Cap 2.4 Runtime Binding + Cap 1.1 Reconciliation
→ Public Market Data
→ Feature Pipeline
→ Typed Volatility Presence
→ Master V2 / Double Play
→ Risk / Safety / Intent
→ Simulated Fill + Canonical Futures Accounting
→ Portfolio/Risk Persistence
→ Evidence / Verifier
```

Status after Cap 4.1: `CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION` with `RUNTIME_ACTIVATED=false`.

**Bound / ready but not activated:**

- Cap 4.1 pre-activation closure: `READY_FOR_ACTIVATION`; activation remains separate Owner-GO
- Canonical runtime bridge live-order path: `RUNTIME_BRIDGE_LIVE_ACTIVATED=false` (not live-activated)
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
| Live execution | `src&#47;live` fail-closed / not implemented path | `INTENTIONAL_SAFETY_BARRIER` | <!-- pt:ref-target-ignore -->

### 3.4 Active runtime-config truth (Capability 0.3 aligned)

Phase-1 effective safety posture for productive entrypoints (owner:
`src&#47;ops&#47;config_truth_alignment_contract_v1.py`):

```text
max_open_positions=1
enable_live_trading=false
ORDERS_AUTHORIZED=false
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
PAPER_EXECUTION_AUTHORIZED=false
CREDENTIALS_AUTHORIZED=false
AUTO_PROMOTION_AUTHORIZED=false
ECONOMIC_VALIDITY_PASS=false
RUNTIME_BRIDGE_LIVE_ACTIVATED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
ENFORCEMENT_ENABLED=false   # numeric max-age; WATCHDOG_ONLY/RESEARCH_ONLY/DIAGNOSTIC_ONLY
VOLATILITY_NUMERIC_MAX_AGE_ENFORCEMENT=false
```

**Effective precedence (deterministic):**

```text
phase1_hard_safety_constants
→ validated_cli_overrides (cannot enable safety flags; max_open_positions must be 1)
→ peak_config productive path (config/config.toml)
→ missing safety flags default false
→ missing max_open_positions FAIL_CLOSED (no fallback to 5 / None / unlimited)
```

**Missing / invalid semantics:**

| Key / case | Behavior |
|---|---|
| missing `max_open_positions` | fail-closed (no fallback to 5) |
| `max_open_positions` &lt; 1 or &gt; 1 | fail-closed for Phase 1 |
| missing safety auth flags | default `false` |
| safety flag `true` in Phase 1 | rejected |
| malformed boolean | fail-closed |
| root `config.toml` (`max_open_positions=10`) | `HISTORICAL` / blocked as Phase-1 authority |
| `config/config.test.toml` (`=5`) | `TEST_ONLY` / blocked |
| `LiveRiskLimits.from_config` missing→`None` skip | `PRODUCTIVE_LEGACY`; Phase-1 adapter requires exact `1` |

**Productive config consumers (Capability 0.3 trace):**

| Surface | Class |
|---|---|
| Wallclock simulated-economics bridge constants | `PRODUCTIVE_CANONICAL` |
| IPSO wallclock observation / issuance helpers | `PRODUCTIVE_CANONICAL` |
| Offline Master V2 replay | `PRODUCTIVE_CANONICAL` |
| Vol max-age research accumulation | `RESEARCH_ONLY` (non-enforcing) |
| `LiveRiskLimits.from_config` | `PRODUCTIVE_LEGACY` (aligned via Phase-1 adapter) |
| Universe/ranking as trading authority | Selection/trading authority remains `DEAD_OR_UNREACHABLE`; Cap 2.1 universe + Cap 2.2 ranking are `PRODUCTIVE_CANONICAL` candidate-context producers only (`ALPHA_ALLOWED=false`, no `SINGLE_SELECTED_FUTURE`) |
| Productive reconciliation host (Capability 1.1 startup gate on wallclock bridge) | `PRODUCTIVE_CANONICAL` (`PRODUCTIVE_RECONCILIATION_BOUND=true`; live/orders still fail-closed) |
| Governed Futures Universe Producer (Capability 2.1) | `PRODUCTIVE_CANONICAL` universe snapshot owner `ops.governed_futures_universe_producer_v1`; `CODE_EXISTS+BOUND+PERSISTED+RESTART_PROVEN`; `ACTIVATED=false`; ranking/selection/alpha not granted |
| Productive Futures Ranking Producer (Capability 2.2) | `PRODUCTIVE_CANONICAL` Top-20 candidate-context owner `ops.productive_futures_ranking_producer_v1`; `CODE_EXISTS+BOUND+PERSISTED+RESTART_PROVEN`; `ACTIVATED=false`; `TOP20_IS_CONTEXT_ONLY=true`; selection/alpha/multi-future not granted |
| Productive Futures Accounting Runtime Binding (Capability 3.1) | `PRODUCTIVE_CANONICAL` owner `ops.productive_futures_accounting_runtime_binding_v1`; reuses `src/execution/paper/futures_accounting.py`; `FUTURES_ACCOUNTING_RUNTIME_BOUND=true`; `ACTIVATED=false`; live/orders fail-closed |
| Single Future Canonical Runtime Pre-Activation Closure (Capability 4.1) | `PRODUCTIVE_CANONICAL` owner `ops.single_future_canonical_runtime_pre_activation_closure_v1`; reuses Cap 2.4 host; `READY_FOR_ACTIVATION`; `RUNTIME_ACTIVATED=false`; live/orders/auth-consumption fail-closed |
| Single Future Canonical Runtime Deterministic Offline Evidence (Capability 5.1) | `PRODUCTIVE_CANONICAL` owner `ops.single_future_canonical_runtime_deterministic_offline_evidence_v1`; reuses Cap 4.1/2.4 host; offline fixtures only; historical `READY_FOR_ACTIVATION`; no network/auth consumption |
| Simulated Entry/Reduce/Exit Actionability Evidence (Capability 7.1) | `PRODUCTIVE_CANONICAL` owner `ops.simulated_entry_reduce_exit_actionability_evidence_v1`; end-to-end simulated lifecycle evidence; `RUNTIME_ACTIVATED=false` in Cap 7.1 itself |
| Single-Future Stateful No-Order Runtime Activation (Capability 7.2) | `PRODUCTIVE_CANONICAL` owner `ops.single_future_stateful_no_order_runtime_activation_v1`; activates no-order stateful runtime; `FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true`; `SIMULATED_EXECUTION_ACTIVE=true`; `PUBLIC_MD_NETWORK_SESSION_OBSERVED=false`; live/testnet/paper/credentials fail-closed |

Verification: `CONFIG_TRUTH_ALIGNMENT_V1`; live remains fail-closed; multi-future unauthorized;
numeric max-age non-enforcing; Cap 4.1 readiness is not activation.

### 3.5 Persistence / evidence / restart / economic gate

| Surface | Owner / status | Notes |
|---------|----------------|-------|
| Persistence | session/evidence ledgers under governed ops/research paths | no claim of full restart-proven portfolio persistence |
| Evidence | IPSO / wallclock bridge / vol-max-age research ledgers; progress registry; config truth alignment report | last baseline SHA for this map: `7a320ff95…` |
| Restart / recovery | Cap 4.1 offline restart/recovery probe for recon/universe/ranking/selection/accounting/portfolio/risk/evidence | `RESTART_PROVEN=true` for Cap 4.1 pre-activation offline closure; live activation still forbidden |
| Economic Validity Offline Gate | registry authoritative fields | `ECONOMIC_VALIDITY_OFFLINE_GATE_STATE=false` / `PASS=false` (explicit; Cap 4.1 requires explicit state) |
| Productive reconciliation in runtime host | bound as mandatory startup gate before first decision cycle (Capability 1.1) | `PRODUCTIVE_RECONCILIATION_BOUND=true`; owner `ops.productive_reconciliation_runtime_binding_v1`; alpha only on MATCH / verified reduce-only recovery; live/orders still fail-closed |
| Futures accounting in runtime path | bound after simulated fill / before portfolio+risk persistence (Capability 3.1) | `FUTURES_ACCOUNTING_RUNTIME_BOUND=true`; owner `ops.productive_futures_accounting_runtime_binding_v1`; kernel `src/execution/paper/futures_accounting.py`; live/orders still fail-closed |
| Cap 4.1 pre-activation closure | full single-future call graph proven offline | `READY_FOR_ACTIVATION`; `RUNTIME_ACTIVATED=false`; evidence under `docs/evidence/capability_4_1_single_future_canonical_runtime_pre_activation_closure_v1/` |
| Cap 5.1 deterministic offline evidence | Cap 4.1 call graph proven under versioned offline market-data replay + restart/digest parity | `READY_FOR_ACTIVATION`; `RUNTIME_ACTIVATED=false`; evidence under `docs/evidence/capability_5_1_single_future_canonical_runtime_deterministic_offline_evidence_v1/` |

### 3.6 Known gaps (current)

1. Universe → Ranking → Single Selected Future persistence + runtime authority binding — **closed by Capabilities 2.1–2.4**
2. Productive reconciliation host binding — **closed by Capability 1.1**; live activation still forbidden
3. Futures accounting runtime wiring — **closed by Capability 3.1**
4. Canonical runtime pre-activation closure — **closed by Capability 4.1** as `READY_FOR_ACTIVATION` (`RUNTIME_ACTIVATED=false`); live activation still forbidden
5. Canonical stateful no-order activation — **closed by Capability 7.2** (`FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true`); public-MD network sessions remain separate (Phase 9.2 Owner-GO)
6. Strategy registry full productive binding
7. Config truth alignment for `max_open_positions` effective consumers — **closed by Capability 0.3** (`CONFIG_TRUTH_ALIGNMENT_V1`)
8. Active-set rotation policy — **registered by Capability 0.4** as `DEFERRED_REQUIRED_CAPABILITY` in `PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1` / `docs/governance/deferred_work_recovery_register_v1.json` (Phase 6; not productive Top-5; implementation/activation unauthorized; prior reminder remains `REMINDER_ONLY`)

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
- `docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md` + `docs/governance/deferred_work_recovery_register_v1.json` — canonical Deferred-Work Recovery Register (Capability 0.4; `MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0` = `DEFERRED_REQUIRED_CAPABILITY`; not productive Top-5)
- `docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md` — `REMINDER_ONLY` surface; authority superseded by the canonical register

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
READY_FOR_ACTIVATION != ACTIVATED
READY_FOR_ACTIVATION != ACTIVATED_NO_LIVE_ORDERS
READY_FOR_ACTIVATION != LIVE
READY_FOR_ACTIVATION != ACTIVE
RUNTIME_ACTIVATED=false
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
| `docs/governance/Peak_Trade_Canonical_Capability_Closure_Runtime_Recovery_Trading_Path_Runbook_V1_2_Trading_First.md` | CURRENT+working | CURRENT+working | baseline `4bac3303…` | BOUND_NOT_ACTIVATED etc. | §1.1 target separated | owner/operator working authority | fail-closed | internal title V1.1 vs filename V1_2 | store + note mismatch; do not silently rewrite | yes (stored; mismatch documented; repo-admission token encoding + trailing-whitespace normalization only) |
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
| `docs/governance/PEAK_TRADE_DEFERRED_WORK_RECOVERY_REGISTER_V1.md` / `docs/governance/deferred_work_recovery_register_v1.json` | CURRENT register | CURRENT | Capability 0.4 | CURRENT_RUNTIME_EFFECT=NONE | Phase-6 deferred rotation | register only | none | Top-5 not productive; multi-future unauthorized | create + register rotation workstream | yes |
| `docs/planning/deferred/MULTI_FUTURE_ACTIVE_SET_ROTATION_REPLACEMENT_POLICY_V0_DEFERRED_REMINDER.md` | deferred reminder | REMINDER_ONLY | reminder | IMPLEMENTATION_STARTED=false | Top20→TopN later | ranking≠authority | none | Top-5 must not be called productive/regressed; authority superseded by Deferred-Work Register | DOCUMENT_CLASS=TARGET_ARCHITECTURE + deferred marker + register pointer | yes |
| `docs/PHASE_42_TOPN_PROMOTION.md` | HIST/TARGET risk | HIST | phase doc | promotion language risk | TopN | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | may over-claim TopN readiness | DOCUMENT_CLASS=HISTORICAL; no Top5 productive claim | yes |
| `docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_*` (family) | research/CURRENT | CURRENT research | many | watchdog/research | later enforcement discussion only | non-enforcing | research sessions only | enforcement must stay false | no enforcement uplift; family noted | partial (family rule in Truth Map; no mass rewrite) |
| `docs/webui/observability/UNIVERSE_SELECTION_READMODEL_V1.md` | CURRENT readmodel | CURRENT | webui | universe readmodel | selection UI | not trading authority | none | ranking≠trading authority | DOCUMENT_CLASS + authority false note | yes |
| `docs/LIVE_OPERATIONAL_RUNBOOKS.md` | HIST/ops index | HIST/non-authorizing | live ops overview | operational wording risk | live ops | non-authorizing | none | “operational” ≠ live-ready | DOCUMENT_CLASS=HISTORICAL + non-authorizing preserved | yes if edited; else inventory only |
| `docs/governance/READ_ONLY_CANONICAL_CHAIN_AND_ZERO_TRADE_BLOCKER_REAUDIT_V1.md` | CURRENT audit | CURRENT/HIST evidence | reaudit | zero-trade blockers | none | fail-closed | none | none | DOCUMENT_CLASS | yes |
| `docs/governance/Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md` | governance contract | TARGET/governance | PR#5226 markers | slice complete ≠ economic validity | chain repair | no runtime unlock | blocked slice 2 | “SLICE_1_COMPLETE” is wiring slice, not live | DOCUMENT_CLASS=TARGET_ARCHITECTURE | yes |
| Futures accounting runtime docs | Cap 3.1 spec + evidence | CURRENT bound | Cap 3.1 | productive binding true, not activated | accounting runtime | none live | none | keep `ACTIVATED=false` | DOCUMENT_CLASS + Cap 3.1 evidence | yes if edited |
| Strategy registry wiring | feature_state_map Class B | CURRENT gap | feature map | many strategies unwired | registry closure later | none live | none | do not call fully integrated | none beyond truth map | inventory only |
| Shadow / Paper / Testnet / Live policy docs | mixed | CURRENT fail-closed + TARGET later | many | fail-closed | ladder 29U–29Z | safety | blocked | none if fail-closed preserved | no activation language uplift | inventory + guards |

### Inventory counts (this capability)

```text
DOCUMENTS_INVENTORIED=24_PRIMARY_PLUS_FAMILIES
CURRENT_RUNTIME_TRUTH_DOCUMENTS=12
TARGET_ARCHITECTURE_DOCUMENTS=8
HISTORICAL_DOCUMENTS=4
INSUFFICIENT_EVIDENCE_ITEMS=2
```

`INSUFFICIENT_EVIDENCE_ITEMS`:

1. Full restart/recovery proof for canonical trading runtime host
2. Exhaustive futures-accounting owner/consumer matrix beyond unbound claim

Closed by Capability 0.3: global Phase-1 effective `max_open_positions=1` consumer-trace + fail-closed missing/invalid semantics (`CONFIG_TRUTH_ALIGNMENT_V1`).

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
