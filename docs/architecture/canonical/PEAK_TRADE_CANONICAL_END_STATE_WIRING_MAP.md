# Peak_Trade Canonical End-State Wiring Map

```text
DOCUMENT_CLASS=CANONICAL_DERIVED_ARCHITECTURE_MAP
PRIMARY_SEMANTIC_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
RUNTIME_AUTHORITY_EFFECT=NONE
TRADING_AUTHORITY_EFFECT=NONE
DASHBOARD_AUTHORITY_EFFECT=NONE
NON_RUNTIME_AUTHORIZING=true
STALE_IF_HEAD_DIFFERS=true
FORENSIC_REPOSITORY_SHA=b9038bacf09b59de81a0a73d6e49575a0f05f242
DOCUMENT_SHA256=e35c811c5e1d4d4602b0cddb1283ce5d5ec879a6990120df2f2e73f0c3a1eff5
VERIFIED_AT=2026-08-05T17:03:44Z
DOCUMENT_SHA256_MODEL=SHA256_OF_FILE_BYTES_WITH_PENDING_PLACEHOLDER_BEFORE_STAMP
CAPABILITY_ID=PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP_MATERIALIZATION_V1
REPOSITORY_PATH=docs/architecture/canonical/PEAK_TRADE_CANONICAL_END_STATE_WIRING_MAP.md
```

```text
DASHBOARD_READ_ONLY_CONSUMER=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_TRADING_INPUT=false
DASHBOARD_RUNTIME_DEPENDENCY_ADDED=false
RUNTIME_DEPENDS_ON_DASHBOARD=false
PRESENTATION_LAYER_CHANGED=false
DASHBOARD_FILES_CHANGED=false
```

```text
PHASE_9_2_STEP_4_CURRENT_STATUS=OPEN
STEP_4_RUNTIME_COMPONENTS_EXIST=true
STEP_4_PRODUCTIVE_SESSION_BINDING_EXISTS=false
STEP_4_GOVERNED_FAULT_PATH_EXISTS=false
STEP_4_REAL_SESSION_OBSERVED=false
STEP_4_LADDER_CLOSED=false
NEXT_REQUIRED_BINDING_CAPABILITY=PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1
```

------------------------------------------------------------------------

# 1. Purpose, Authority and Non-Authority

This document is a **derived forensic architecture map** of Peak_Trade’s
canonical end-state wiring, produced from repository evidence at
`FORENSIC_REPOSITORY_SHA` and from the Owner-ratified Master Runbook.

It answers:

1. which productive runtime edges currently exist and are bound;
2. which target edges the Master Runbook requires;
3. which gaps remain, with mandatory gap classifications.

It is **not**:

- a second SSOT;
- a runtime, trading, dashboard, authorization or activation authority;
- a substitute for Code / Config / Persistence / Evidence truth;
- permission to start Public-MD network sessions, consume authorization,
  mutate rulesets, or reach Live / Testnet / credentials / real capital.

Claim vocabulary follows Master Runbook §3 only. Unproven closed claims
are forbidden. Every factual statement is either repository-proven,
`CURRENT_GAP`, or `TARGET_BINDING` (runbook-derived and separated from
current runtime).

------------------------------------------------------------------------

# 2. Repository and Runbook Binding

| Field | Value |
| --- | --- |
| Forensic SHA | `b9038bacf09b59de81a0a73d6e49575a0f05f242` (`origin/main`, PR #5750 tip) |
| Primary semantic authority | `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` |
| Navigation index | `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` |
| Runbook forensic baseline (historical) | `a8653d520ba3563dddb41aa175445d14725ac9b9` |
| Runbook `CURRENT_FORENSIC_TRUTH_SHA` field | `beacc35d754fd8ab0a37190b882f71b8fb78cb38` (**DOCUMENTATION_DRIFT** vs this map’s `origin/main`) |
| Order boundary | No Live / Testnet / paper-exchange orders; no credentials; no real capital |
| Selection mode | `SINGLE_SELECTED_FUTURE`; `MULTI_FUTURE_RUNTIME_AUTHORIZED=false` |

```text
THIS_MAP_DOES_NOT_UPDATE_RUNBOOK_SEMANTICS=true
THIS_MAP_DOES_NOT_AUTHORIZE_NETWORK_SESSION=true
THIS_MAP_DOES_NOT_AUTHORIZE_AUTHORIZATION_CONSUMPTION=true
STALE_IF_origin/main_DIFFERS_FROM_FORENSIC_REPOSITORY_SHA=true
```

------------------------------------------------------------------------

# 3. Canonical Prime Trading Path

## 3.1 TARGET_BINDING — Startup / Restart (Master Runbook §1)

```text
Persisted Selection
→ Native Instrument Binding
→ Reconciliation Gate
→ Public Market Data
→ Distinct Observation Acceptance
→ Features
→ Market State
→ Confirmation
→ Master V2
→ Double Play
→ Dynamic Scope
→ Survival/Suitability/Composition
→ Risk
→ Safety
→ Intent
```

## 3.2 TARGET_BINDING — Economic Transition

```text
Intent
→ Simulated Execution
→ Simulated Fill
→ Futures Accounting
→ Portfolio Persistence
→ Reconciliation
→ Evidence
→ Restart Reconstruction
```

## 3.3 CURRENT — Cap 7.2 authoritative host graph (Master Runbook §5.3)

```text
Authorization / session / selection / native binding / reconciliation
→ OKX public market data
→ DistinctMarketObservationAcceptor (C1)
→ ObservationAcceptanceResult
→ Features / regime pipeline
→ Directional Confirmation Progress (C2)
→ Directional Assessment Integration (C3)
→ previous RuntimeScopeState / Dynamic Scope transition
→ Exit-policy producer evaluation
→ Master V2 / Double Play integrated offline replay
→ confirmation / scope / decision-path atomic commits
→ Risk → Safety → Intent
→ Simulated execution / fill / accounting / portfolio
→ Evidence → Verifier
```

Productive host entry (Cap 7.2 constants):

- `PRODUCTIVE_HOST` =
  `src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/decision_economics_cycle_bridge_v1.py`
- `PRODUCTIVE_HOST_ENTRY` =
  `ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1.run_bridge_cycle_v1`
- CLI: `scripts/ops/run_single_future_stateful_no_order_runtime_activation_v1.py`
- CLI: `scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py`

Abbreviated wallclock hardening_v2 surface (documentation residual, not a
second decision authority):

```text
okx_public_market_data
→ feature_pipeline
→ regime_pipeline
→ canonical_volatility_productive_runtime_cmc_typed_binding
→ master_v2_double_play_integrated_offline_replay
→ risk_position_sizing
→ safety_kernel
→ intended_side_quantity
→ analytical_simulated_execution
→ simulated_fill_fee_slippage
→ session_persistent_portfolio
→ evidence
→ full_economic_reconstruction_verifier
```

```text
ONE_DECISION_AUTHORITY_CHAIN=true
NO_PARALLEL_DECISION_AUTHORITY_STACK=true
HOST_CALL_GRAPH_DOCUMENTATION_RESIDUAL=
  WALLCLOCK_HARDENING_V2_CALL_GRAPH_OMITS_EXPLICIT_C1_C2_STAGES_VS_CAP72_HOST
HOST_CALL_GRAPH_RESIDUAL_IS_CORE_LOGIC_DEFECT=false
PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED=false
```

------------------------------------------------------------------------

# 4. Current Productive Runtime Graph

## Graph A — Startup/Restart (CURRENT)

```text
Persisted Selection [PERSISTED + RESTART_PROVEN; selection/ranking/universe packages]
→ Native Instrument Binding [RUNTIME_REACHABLE; Cap 7.2 / public-MD hosts]
→ Reconciliation Gate [BOUND + PERSISTED + RESTART_PROVEN;
   src/ops/productive_reconciliation_runtime_binding_v1]
→ Public Market Data [RUNTIME_REACHABLE + CONFIG_CONSUMED for Public-MD capable hosts;
   PUBLIC_MD_NETWORK_SESSION requires separate Owner-GO]
→ Distinct Observation Acceptance / C1
   [BOUND + PERSISTED + RESTART_PROVEN; Cap 6.1
   src/ops/stateful_confirmation_and_c1_productive_binding_v1]
→ Features / Market State / typed volatility→CMC
   [BOUND + EVIDENCE_PROVEN cold-start; G17 CLOSED_AND_COLD_START_PROVEN]
→ Confirmation C2/C3 + confirmation_session_id
   [BOUND + PERSISTED + RESTART_PROVEN; Cap 6.1]
→ Master V2 / Double Play
   [RUNTIME_REACHABLE; src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py]
→ Dynamic Scope / RuntimeScopeState
   [BOUND + PERSISTED + RESTART_PROVEN; Cap 6.2
   src/ops/dynamic_scope_persistence_binding_v1]
→ Survival/Suitability/Composition [BOUND via Master V2 / Cap 6.x path]
→ Exit-policy producers [BOUND; Cap 6.5 src/ops/exit_policy_producer_binding_v1]
→ Risk / Safety [BOUND on Cap 7.2 host]
→ Intent [BOUND on Cap 7.2 host]
```

## Graph B — Economic Transition (CURRENT, offline no-order / deterministic scopes)

```text
Intent
→ SimulatedExecutionPortV1
   [BOUND + ACTIVATED offline Cap 7.2;
   src/ops/single_future_stateful_no_order_runtime_activation_v1/simulated_execution_port_v1.py]
→ Simulated Fill / Fee / Slippage
   [EVIDENCE_PROVEN deterministic Cap 7.1;
   PUBLIC_MD natural outcome = CURRENT_GAP / EVIDENCE_GAP]
→ Futures Accounting
   [BOUND; ops.productive_futures_accounting_runtime_binding_v1 delegate]
→ Portfolio Persistence [PERSISTED]
→ Reconciliation [BOUND]
→ Evidence + full_economic_reconstruction_verifier
   [EVIDENCE_PROVEN for closed capability packages]
→ Restart Reconstruction
   [RESTART_PROVEN Cap 6.4 deterministic stateful no-order;
   Phase 9.2 Public-MD restart outcome still OPEN]
```

## Graph C — Public-MD Session (CURRENT)

```text
Canonical Session Spec
  (e.g. config/ops/phase_9_2_public_md_smoke_session_contract_v1.json;
   restart contracts under config/ops/phase_9_2_*)
→ Session-GO / Authorization surfaces
  (canonical_durable_authorization_*; paper_shadow confirm_token;
   phase_9_2 session-GO / segment authorization packages)
→ Productive Session Entrypoint
  (integrated paper_shadow wallclock runner;
   Phase 9.2 restart network entrypoint + real-network wallclock binding)
→ Public GET Transport
  (eea_public_md_transport_v1 / okx_public_market_data_client_v1; GET-only allowlists)
→ Pacing / Rate-Limit Classification / Retry Budget / Backoff
  [CODE_EXISTS + TESTED_UNIT + preflight proven;
   productive Step-4 session binding = CURRENT_GAP]
→ Heartbeat / Stale Gate / Reconnect budgets
  [CODE_EXISTS in wallclock session execution; smoke/one-hour telemetry exists]
→ Distinct Observation → Canonical Stateful Runtime
→ Session Telemetry → Evidence Bundle → Verifier
```

Activation truth at forensic SHA (repo + runbook §5.2, scoped):

```text
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true_offline_no_order_cap72_scope_only
SIMULATED_EXECUTION_ACTIVE=true_offline_no_order_cap72_scope_only
PUBLIC_MD_RUNTIME_CAPABLE=true
PUBLIC_MD_NETWORK_SESSION_OBSERVED_IN_CAP72_ACTIVATION=false
PHASE_9_2_PUBLIC_MD_LONG_RUNNING_LADDER_CLOSED=false
REAUTHORIZATION_REQUIRED_BEFORE_NEW_PUBLIC_MD_NETWORK_SESSION=true
```

------------------------------------------------------------------------

# 5. Target End-State Runtime Graph

## TARGET_BINDING — No-order finish (Master Runbook §2.1 / §21.1)

```text
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
PUBLIC_MARKET_DATA_ACTIVE=true
PUBLIC_MD_NATURAL_MARKET_LIFECYCLE_EVIDENCE_COMPLETE=true
PHASE_9_2_SESSION_LADDER_COMPLETE=true
NO_LIVE_ORDERS=true
NO_TESTNET_ORDERS=true
NO_PAPER_EXCHANGE_ORDERS=true
NO_EXCHANGE_CREDENTIAL_USE=true
REAL_CAPITAL_MOVEMENT=false
```

## TARGET_BINDING — Physical execution separation (§2.3)

```text
Canonical Intent
→ SimulatedExecutionPort
→ Simulated Fill
→ Canonical Futures Accounting
```

```text
REAL_EXECUTION_ADAPTER_CONSTRUCTED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
ORDER_SIDE_EFFECT_OCCURRED=false
```

## TARGET_BINDING — Phase 11 autonomy loop (non-authorizing architecture only)

Documented in Master Runbook §11; **not** authorized by this map. Execution
ports may later include Testnet/Live adapters under separate Owner-GO; the
no-order host must remain physically separate.

------------------------------------------------------------------------

# 6. Current-vs-Target Gap Matrix

| ID | Area | Current | Target | Classification | Blocks now |
| --- | --- | --- | --- | --- | --- |
| W1 | Phase 9.2 ladder beyond smoke/one-hour | Partially complete; Step 3 binding ready, outcome open; Steps 4–7 open | Ladder complete | `EVIDENCE_GAP` / `DEFERRED_REQUIRED_CAPABILITY` | Yes — critical path |
| W2 | Public-MD natural Entry/Exit lifecycle | Deterministic Cap 7.1 proven; natural Public-MD open | Natural lifecycle evidenced | `EVIDENCE_GAP` | Yes for Phase 9.2 DoD |
| W3 | Step 4 rate-limit/reconnect session | Components exist; no productive session binding / governed fault path | Bound + outcome-observed + verified | `WIRING_GAP` | Yes for Step 4 |
| W4 | Step 3 restart/recovery real session | Binding implemented (PR #5750); `RESTART_RECOVERY_LADDER_STEP_CLOSED=false` | Governed real session verifier PASS | `EVIDENCE_GAP` | Yes — before ladder advance |
| W5 | hardening_v2 distance literals | Residual host-consumer literals after Cap 6.3 | Owned typed config consumers | `CONFIG_DRIFT` (partial residual) | Review-only; no threshold mutation authorized |
| W6 | Runbook `CURRENT_FORENSIC_TRUTH_SHA` vs `origin/main` | Runbook field older than forensic SHA | Reconciled current-truth SHA | `DOCUMENTATION_DRIFT` | Docs freshness |
| W7 | Numeric vol max-age | Non-enforcing | Separate Phase 10 decision | `INTENTIONAL_SAFETY_BARRIER` / intentional current phase | No |
| W8 | Multi-future runtime | Unauthorized | Future program only | `INTENTIONAL_SAFETY_BARRIER` | Multi-future only |
| W9 | Strategy registry breadth | Non-authoritative / deferred | Tiered closure after single-future | `DEFERRED_REQUIRED_CAPABILITY` | Strategy breadth |
| W10 | Live/Testnet/credentials | Fail-closed unreachable under this program | Separate Phase 11 | `INTENTIONAL_SAFETY_BARRIER` | Live program only |
| W11 | Funding proof completeness | Insufficient where funding enters claims | Dedicated evidence | `INSUFFICIENT_EVIDENCE` | Funding claims only |

Closed Cap 6.1–6.5 / 7.1–7.2 / G17 items remain historical; do not reopen as Immediate Next (Master Runbook §22).

------------------------------------------------------------------------

# 7. Authority Ownership Matrix

| Concern | Authority owner (repository) | Status | Notes |
| --- | --- | --- | --- |
| Semantic implementation plan | Master Runbook | `DOCUMENTED` + Owner-ratified | Non-runtime-authorizing |
| Cap 7.2 activation | `ops.single_future_stateful_no_order_runtime_activation_v1` | `ACTIVATED` offline no-order scope | Config: `config/runtime/single_future_stateful_no_order_runtime_activation_v1.json` |
| Productive cycle host | `decision_economics_cycle_bridge_v1.run_bridge_cycle_v1` | `RUNTIME_REACHABLE` | Cap 7.2 `PRODUCTIVE_HOST_ENTRY` |
| C1/C2/C3 confirmation | `ops.stateful_confirmation_and_c1_productive_binding_v1` | `BOUND` `PERSISTED` `RESTART_PROVEN` | Single writer |
| Dynamic Scope | `ops.dynamic_scope_persistence_binding_v1` | `BOUND` `PERSISTED` `RESTART_PROVEN` | Single writer |
| Master V2 / Double Play / Bull-Bear | `trading.master_v2.integrated_offline_trading_logic_replay_v1` | `RUNTIME_REACHABLE` | Core logic frozen unless Owner-ratified |
| Exit-policy producers | `ops.exit_policy_producer_binding_v1` | `BOUND` | Cap 6.5 |
| Reconciliation | `ops.productive_reconciliation_runtime_binding_v1` | `BOUND` `PERSISTED` `RESTART_PROVEN` | Before Alpha |
| Simulated execution | `SimulatedExecutionPortV1` | `BOUND` Cap 7.2 | Physically separate from venue adapters |
| Futures accounting delegate | `ops.productive_futures_accounting_runtime_binding_v1` | `BOUND` | Via Cap 7.2 constants |
| Atomic restart / pending evidence | `ops.full_decision_path_atomic_restart_closure_v1` | `RESTART_PROVEN` deterministic scope | Cap 6.4 |
| Public-MD wallclock runner | `run_productive_wallclock_session_v1` | `RUNTIME_REACHABLE` when separately authorized | Paper-shadow productive issuance package |
| Phase 9.2 Step 3 binding | `ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1` | `BOUND` binding-only; outcome open | Does not start network session |
| Dashboard / Landscape | `src&#47;webui&#47;*` read models | `DOCUMENTED` read-only | `AUTHORITY_EFFECT=NONE` |
| Live / Testnet / credentials | Explicitly unreachable under Cap 7.2 / Phase 9.2 contracts | `INTENTIONAL_SAFETY_BARRIER` | Hard-stop if reachable |

------------------------------------------------------------------------

# 8. Productive Entrypoint and Caller Map

| Entrypoint | Path / symbol | Role | Status |
| --- | --- | --- | --- |
| Cap 7.2 activation CLI | `scripts/ops/run_single_future_stateful_no_order_runtime_activation_v1.py` | Offline no-order activation | `RUNTIME_REACHABLE` |
| Cap 7.2 host cycle | `run_bridge_cycle_v1` | Productive decision→economics cycle | `RUNTIME_REACHABLE` |
| Wallclock full bridge CLI | `scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py` | Bridge host runner | `RUNTIME_REACHABLE` |
| Wallclock hardening v2 CLI | `scripts/ops/run_wallclock_bridge_hardening_v2.py` | Abbreviated Public-MD bridge | `RUNTIME_REACHABLE` (residual vs Cap 7.2 stage labels) |
| Public-MD no-order shadow evidence | `scripts/ops/run_single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.py` | Evidence host | `RUNTIME_REACHABLE` under contract |
| Deterministic offline evidence | `scripts/ops/run_single_future_canonical_runtime_deterministic_offline_evidence_v1.py` | Cap 7.1 path | `EVIDENCE_PROVEN` deterministic |
| Paper-shadow wallclock session | `scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py` | Public-MD session runner family | Requires separate GO |
| Productive authorization issuance | `scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py` | Issuance + wallclock | Requires separate GO |
| Phase 9.2 preflight | `scripts/ops/run_phase_9_2_public_md_session_preflight_v1.py` | Ladder/preflight proofs; no network | `TESTED_INTEGRATION` / evidence sealed |
| Phase 9.2 restart harness CLIs | `run_phase_9_2_restart_recovery_*` | Contract/segments/verify | `CODE_EXISTS` `BOUND` offline |
| Phase 9.2 Step 3 network entrypoint | `scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py` | Productive PRE/POST entry identity | `BOUND`; real network gated |
| Phase 9.2 Step 3 wallclock binding | `scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.py` | Binding gate/preflight/evidence; refuses `--request-real-network` in binding CLI | `BOUND`; session not started by merge |

Caller/callee invariant: research strategies must not bypass Master V2 /
Double Play into Intent/Fill/Order (Master Runbook §4.3).

------------------------------------------------------------------------

# 9. State Root and Single-Writer Matrix

| State root | Writer identity / package | Persist | Restart | Classification |
| --- | --- | --- | --- | --- |
| Selection / ranking / universe | Productive selection packages (Cap baseline) | Yes | Yes | `DURABLE_SOURCE_STATE` |
| Reconciliation | `productive_reconciliation_runtime_binding_v1` single writer | Yes | Yes | `DURABLE_SOURCE_STATE` |
| Confirmation + `confirmation_session_id` | Cap 6.1 single writer | Yes | Yes | `DURABLE_DECISION_STATE` |
| Observation identity / epoch | Cap 6.1 / C1 acceptor path | Yes (minimal) | Yes | `DURABLE_DECISION_STATE` |
| Dynamic Scope `RuntimeScopeState` | Cap 6.2 single writer | Yes | Yes | `DURABLE_DECISION_STATE` |
| Exit-policy continuity | Cap 6.5 writer | Yes (where required) | Partial/proven per Cap 6.5 | `DURABLE_DECISION_STATE` |
| Decision-path atomic commit marker | Cap 6.4 `decision_path_commit_marker_v1.json` | Yes | Yes | Commit authority |
| Pending evidence cursor | Cap 6.4 `pending_evidence_cursor_v1.json` | Yes | Idempotent recovery | Evidence durability |
| Portfolio / accounting | Futures accounting + portfolio persistence | Yes | Yes | `DURABLE_SOURCE_STATE` |
| Activation commit | Cap 7.2 `activation_commit_marker_v1.json` | Yes | Loaded | Control state |
| Kill-switch / degradation (autonomy target) | TARGET_BINDING Phase 11 | Required later | Required later | Not closed for Live |
| Dashboard projections | Read-model only | Rebuildable | N/A | Must not be SSOT |

Master Runbook §6.6 single-writer requirement remains binding: writer
conflicts hard-stop before Alpha advances.

------------------------------------------------------------------------

# 10. Config Owner and Consumer Matrix

| Config / key surface | Owner | Consumer | Status |
| --- | --- | --- | --- |
| Cap 7.2 activation | `config/runtime/single_future_stateful_no_order_runtime_activation_v1.json` | Cap 7.2 package | `CONFIG_EXISTS` `CONFIG_CONSUMED` |
| Cap 6.3 confirmed keys (`confirmation_epochs`, distances) | Typed decision-config ownership (Cap 6.3) | Confirmation / scope path | `CONFIG_CONSUMED`; numerics unchanged |
| hardening_v2 local distance literals | Host residual | hardening_v2 bridge | `CONFIG_DRIFT` residual; review-only |
| Phase 9.2 smoke session | `config/ops/phase_9_2_public_md_smoke_session_contract_v1.json` | Phase 9.2 preflight | `CONFIG_EXISTS` `CONFIG_CONSUMED` |
| Phase 9.2 restart session | `config/ops/phase_9_2_restart_recovery_session_contract_v1.json` | Restart harness | `CONFIG_EXISTS` |
| Phase 9.2 Step 3 wallclock binding | `config/ops/phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.json` | Binding package | `CONFIG_EXISTS` `CONFIG_CONSUMED`; `network_session_allowed_by_capability_config=false` |
| Public-MD pacing policy | `PublicMdRequestPacingPolicyV1` / research + wallclock constants | Transport + preflight | `CODE_EXISTS` `CONFIG_CONSUMED` on wallclock path |
| Review-only numerics (`PRICE_PATH_MAX_LEN`, fee/slippage bps) | Ownership review open | Multiple | Not proven incorrect |

Silent fallback forbidden for selection, native binding, mark, volatility,
observation identity, confirmation session ID, Dynamic Scope, portfolio,
risk limits, authorization, confirm token, event time, execution adapter,
order authorization (Master Runbook §9.3).

------------------------------------------------------------------------

# 11. Persistence, Atomicity and Journal Map

Cap 6.4 chose and proved a versioned multi-record transaction with commit
marker and pending-evidence recovery (Master Runbook §6.5 options).

```text
RUNTIME_STATE_COMMIT
  = decision_path atomic commit across confirmation / scope / related roots
EVIDENCE_MATERIALIZATION
  = separate durability; failure must not roll back valid economic commit
PENDING_EVIDENCE_CURSOR
  = idempotent recovery after evidence-write failure
```

Repository owners:

- `src/ops/full_decision_path_atomic_restart_closure_v1/persistence_v1.py`
- Commit marker / pending evidence paths in Cap 6.4 constants
- Confirmation commit marker: `confirmation_commit_marker_v1.json` (Cap 6.1)
- Phase 9.2 restart harness reuses Cap 6.4 marker filename
  `decision_path_commit_marker_v1.json` via `state_root_adapter_v1`

```text
ATOMICITY_MODEL=VERSIONED_MULTI_RECORD_WITH_COMMIT_MARKER_AND_PENDING_EVIDENCE_CURSOR
NO_MIXED_CONFIRMATION_SCOPE_OBSERVATION_COMMIT=TARGET_AND_CAP64_PROVEN_DETERMINISTIC_SCOPE
```

------------------------------------------------------------------------

# 12. Restart and Recovery Map

| Scope | Mechanism | Status |
| --- | --- | --- |
| Deterministic stateful no-order decision path | Cap 6.4 atomic restart closure | `RESTART_PROVEN` |
| Confirmation / Dynamic Scope | Cap 6.1 / 6.2 persistence load | `RESTART_LOADED` `RESTART_PROVEN` |
| Cap 7.2 activation | Activation commit marker + host binding | `RESTART_LOADED` in package tests |
| Phase 9.2 restart/recovery ladder Step 3 | PRE→exit 82→POST new process; bundle verifier; real-network wallclock binding | Binding `BOUND`; real session `OUTCOME_OBSERVED=false`; ladder step not closed |
| Process supervision | `scripts/ops/online_readiness_supervisor_v1.sh` + launchd/systemd units; ops runbooks V2.4 | `CODE_EXISTS` / ops domain; not a trading authority |
| Autonomy crash/restart (Phase 11) | TARGET_BINDING | Unauthorized |

Forbidden: silent confirmation or Dynamic Scope reinitialization after prior
durable commit.

------------------------------------------------------------------------

# 13. Public Market Data Transport Map

| Component | Path | Status |
| --- | --- | --- |
| OKX public client | `src/ops/okx_public_market_data_client_v1.py` | `CODE_EXISTS`; raises `RATE_LIMIT_HTTP_429` |
| EEA Public-MD transport | `src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/eea_public_md_transport_v1.py` | `BOUND` on wallclock session path; GET-only; 429 classification + Retry-After |
| Cap 7.2 network boundary | Cap 7.2 constants allowlist `PUBLIC_MARKET_DATA_ENDPOINTS_ONLY` | `CONFIG_CONSUMED` |
| Phase 9.2 allowlist | `EEA_PUBLIC_MD_HOST=eea.okx.com`; GET-only | Preflight / smoke contract |
| Private endpoints | Forbidden prefixes under Cap 7.2 | `INTENTIONAL_SAFETY_BARRIER` |

```text
PUBLIC_MD_NO_ORDER=true_for_this_program
PUBLIC_MD_PRIVATE_ENDPOINT_REACHABLE=false_under_cap72_contracts
```

------------------------------------------------------------------------

# 14. Rate-Limit, Retry, Backoff and Reconnect Map

## Components that exist (repository-proven)

| Component | Path | Productive binding today |
| --- | --- | --- |
| Pacing policy + `MonotonicRequestPacerV1` | `src/research/canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1/public_md_rate_limit_policy_v1.py` | Consumed by wallclock/preflight |
| Phase 9.2 pacing/staleness proof | `src/ops/phase_9_2_public_md_session_preflight_v1/pacing_safety_v1.py` | Preflight evidence; not Step-4 session |
| Rate-limit metric hygiene | `src/ops/phase_9_2_public_md_session_preflight_v1/rate_limit_metric_v1.py` | `TESTED_UNIT` |
| Transport 429 + Retry-After | `eea_public_md_transport_v1` | Bound on wallclock transport |
| Heartbeat / staleness | `heartbeat_staleness_v1.StalenessTrackerV1` | Bound on wallclock session; killstate `STALE_DATA` |
| HTTP 429 budget abort | `session_runtime_v1` / killstate `HTTP_429_BUDGET_EXCEEDED` | Bound on wallclock session |
| Smoke reconnect budgets | Phase 9.2 preflight constants | Contractual for smoke; not Step-4 campaign |
| Generic rate limiters | `src/core/rate_limiter.py`, `src&#47;execution&#47;networked&#47;limits&#47;*` | Execution-domain; not Phase 9.2 Step-4 owner |
| Bounded reconnect policy (AWS/testnet contract) | `aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0` | Separate domain; not Phase 9.2 Step-4 binding |

## Phase 9.2 Step 4 forensic verdict

```text
PHASE_9_2_STEP_4_CURRENT_STATUS=OPEN
STEP_4_RUNTIME_COMPONENTS_EXIST=true
STEP_4_PRODUCTIVE_SESSION_BINDING_EXISTS=false
STEP_4_GOVERNED_FAULT_PATH_EXISTS=false
STEP_4_REAL_SESSION_OBSERVED=false
STEP_4_LADDER_CLOSED=false
NEXT_REQUIRED_BINDING_CAPABILITY=PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1
```

Interpretation:

1. Pacing / 429 / backoff / reconnect budgets / stale gates **exist as code
   and are used on smoke/one-hour wallclock paths and preflight proofs**.
2. There is **no** Cap-style productive binding package analogous to
   `PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1`
   for a governed `RATE_LIMIT_RECONNECT_SESSION`.
3. There is **no** dedicated governed fault-injection session path that
   closes Step 4 with verifier PASS under a Step-4 session identity.
4. Incidental `reconnect_events.jsonl` / `stale_events.jsonl` from smoke or
   one-hour sessions are **not** Step-4 ladder closure.
5. Improvised harnesses are forbidden: reuse wallclock runner, pacing
   owner, transport classification, Cap 6.4 state roots, authorization
   mint/consume path, and ladder verifier vocabulary — same reuse rule
   proven by Step 3 binding.
6. Step 4 remains open until a later separately authorized real session
   observes and verifies rate-limit/reconnect behavior; documentation or
   preflight alone cannot close it.
7. Steps 5–7 must consume the same bound pacing/429/reconnect/stale
   surfaces; they must not invent parallel transport or decision cores.

Smallest binding slice required:

```text
Session spec RATE_LIMIT_RECONNECT_SESSION
→ Session-GO + per-session authorization bindings
→ Productive entrypoint identity (reuse wallclock runner)
→ Explicit fault/session mechanism for 429/reconnect/stale
→ Evidence bundle + verifier claims
→ No core-logic / threshold mutation
→ No permanent unscoped enable flag
```

Dependency note (`CURRENT_GAP` ordering): Step 3 real governed restart
session remains open at forensic SHA; Step 4 binding must not bypass Step 3
closure criteria, even though Step 4 is the named next *binding capability*
after Step 3’s binding readiness.

------------------------------------------------------------------------

# 15. Observation, Confirmation and Scope Identity Map

| Identity | Meaning | Status |
| --- | --- | --- |
| `market_event_time` | Market-assigned observation time | Contractual |
| `observation_identity` | Stable accepted observation ID | Cap 6.1 |
| `observation_epoch` | Advances only on DISTINCT accept | Cap 6.1 `BOUND` |
| `decision_cycle_id` | Host cycle; must not substitute epoch | Enforced in contracts |
| `confirmation_session_id` | Stable confirmation lifecycle ID | `PERSISTED` `RESTART_PROVEN` |
| `runtime_session_id` | Host/session execution identity | Session contracts |
| Dynamic Scope state | `RuntimeScopeState` continuity | Cap 6.2 |

Invariants (Master Runbook §7):

```text
DUPLICATE_OBSERVATION_DOES_NOT_ADVANCE=true
MISSING_OBSERVATION_DOES_NOT_ADVANCE=true
DECISION_CYCLE_DOES_NOT_IMPLY_NEW_OBSERVATION=true
CONFIRMATION_SESSION_ID_STABLE_ACROSS_CYCLES=true
INSTRUMENT_STATE_ISOLATED=true
```

C1/C2/C3 productive symbols live under
`src/ops/stateful_confirmation_and_c1_productive_binding_v1/host_binding_v1.py`
and Master V2 specs (`MASTER_V2_C1_*`, `MV2_C2_*`, `MV2_C3_*`).

------------------------------------------------------------------------

# 16. Decision, Risk, Safety and Exit Precedence Map

```text
Market State
→ Master V2
→ Double Play
→ Survival / Suitability / Composition
→ Risk
→ Safety
→ Intent
```

Exit-policy producers are bound (Cap 6.5) and must not be stubbed false.
Open-position protection must not depend on Alpha health (Phase 11 target
rule; already design-binding for no-order safety).

Research models (Armstrong, El Karoui, Ehlers, …) remain
`RESEARCH_INFORMATION` unless separately promoted (Master Runbook §4.3).

------------------------------------------------------------------------

# 17. Intent, Simulated Execution and Accounting Map

## Graph F — Execution Isolation (CURRENT + TARGET)

```text
Canonical Intent
→ SimulatedExecutionPortV1
→ Simulated Fill
→ Canonical Futures Accounting
```

Explicit negatives (must remain true under this program):

```text
No-Order Host ↛ Real Execution Adapter
No-Order Host ↛ Private Endpoint
No-Order Host ↛ Exchange Credentials
No-Order Host ↛ Order Submission
```

Repository proof surfaces:

- `SimulatedExecutionPortV1` construction only in Cap 7.2 host binding
- Cap 7.2 network allowlists forbid private trade/account paths
- Cap 7.2 constants: `LIVE_ORDERS=false`, `TESTNET_ORDERS=false`,
  `EXCHANGE_CREDENTIAL_USE=false`

Economic evidence:

- Cap 7.1 deterministic Entry/Exit/Fee/Slippage: `EVIDENCE_PROVEN`
- Public-MD natural Entry/Exit: `CURRENT_GAP` (`EVIDENCE_GAP`)

------------------------------------------------------------------------

# 18. Reconciliation Map

```text
Startup / continuous operation
→ productive_reconciliation_runtime_binding_v1.startup_gate_v1
→ taxonomy / classifier outcomes
→ block Alpha on unresolved divergence
→ persist reconciliation state (single writer)
```

Phase 9.2 restart POST segment requires reconciliation before Alpha
(`required_reconciliation_before_alpha=true` in Step 3 binding config).

Phase 11 extends reconciliation hierarchy (credentials, open orders,
positions, balances, …) — `TARGET_BINDING` only; unauthorized here.

------------------------------------------------------------------------

# 19. Evidence Producer and Verifier Claim Map

| Producer / verifier | Path | Claims scope |
| --- | --- | --- |
| Cap 7.1 actionability evidence | `ops.simulated_entry_reduce_exit_actionability_evidence_v1` | Deterministic lifecycle |
| Full economic reconstruction verifier | `full_economic_reconstruction_verifier_v1` | Accounting reconstruction |
| Phase 9.2 preflight evidence | `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/preflight/` | Ladder definition, pacing proof, network boundary |
| Smoke / one-hour session evidence | `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/sessions/phase_9_2_public_md_smoke_session_v1/MANIFEST.sha256`, `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/sessions/phase_9_2_public_md_one_hour_governed_session_noproxy_b0e882b9714a/MANIFEST.sha256` | Closed steps on historical session SHA `b0e882b9714a…` |
| Phase 9.2 actionability forensic telemetry | `ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1` | Funnel/telemetry; not ladder closure alone |
| Phase 9.2 restart bundle verifier | `phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.verifier_v1` | PRE/POST identity + commit continuity |
| Step 3 binding evidence materializer | `phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1` | Binding readiness; not real-session PASS |
| Wallclock outcome completeness | `phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1` | Outcome projection completeness |

Claim rule: path reachability ≠ observed outcome ≠ verified evidence
(Master Runbook closing principle).

------------------------------------------------------------------------

# 20. Phase-9.2 Session Ladder Integration Map

Ladder source:
`src/ops/phase_9_2_public_md_session_preflight_v1/constants_v1.py` /
preflight evidence `phase_9_2_session_ladder_v1.json`.

## Graph D — Phase-9.2 Ladder

```text
1 Smoke
→ 2 One-Hour Governed
→ 3 Restart/Recovery
→ 4 Rate-Limit/Reconnect
→ 5 Prolonged Natural Market
→ 6 Adverse/Stale Data
→ 7 Multi-Session Continuity Campaign
```

### Step 1 — Smoke

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `EVIDENCE_PROVEN` / ladder closed for smoke |
| PRODUCTIVE_ENTRYPOINT | Paper-shadow wallclock runner under smoke session id |
| SESSION_SPEC | `config/ops/phase_9_2_public_md_smoke_session_contract_v1.json` / `phase_9_2_public_md_smoke_session_v1` |
| AUTHORIZATION_SCOPE | Historical smoke authorization artifacts under evidence package |
| STATE_ROOTS | Cap 6.x confirmation/scope/atomic roots via stateful runtime |
| FAULT_OR_SESSION_MECHANISM | Short duration; pacing/stale budgets in smoke contract |
| EVIDENCE_BUNDLE | `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/sessions/phase_9_2_public_md_smoke_session_v1/MANIFEST.sha256` |
| VERIFIER | Session completion / economic verifier artifacts in bundle |
| PREDECESSOR | Cap 7.2 + Phase 9.2 preflight |
| SUCCESSOR | One-hour governed |
| OPEN_GAPS | None for smoke closure claim |
| CLOSURE_CRITERIA | Smoke PASS already recorded |

### Step 2 — One-Hour Governed

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `EVIDENCE_PROVEN` on session truth SHA `b0e882b9714a615f633fb09b8ee4f9a19f54d470` |
| PRODUCTIVE_ENTRYPOINT | Wallclock productive runner |
| SESSION_SPEC | `phase_9_2_public_md_one_hour_governed_session_noproxy_b0e882b9714a` |
| AUTHORIZATION_SCOPE | Evidence `authorization&#47;` + consumption records |
| STATE_ROOTS | Full Cap 6.x / portfolio / evidence cursors |
| FAULT_OR_SESSION_MECHANISM | Natural wallclock; reconnect/stale telemetry incidental |
| EVIDENCE_BUNDLE | `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/sessions/phase_9_2_public_md_one_hour_governed_session_noproxy_b0e882b9714a/MANIFEST.sha256` |
| VERIFIER | `full_economic_reconstruction_verifier.json`, completion/terminal verdicts |
| PREDECESSOR | Smoke |
| SUCCESSOR | Restart/Recovery |
| OPEN_GAPS | Does not close Steps 3–7; SHA-bound historical session |
| CLOSURE_CRITERIA | One-hour PASS on that truth SHA (recorded) |

### Step 3 — Restart/Recovery

| Field | Value |
| --- | --- |
| CURRENT_STATUS | Binding `BOUND` / `CODE_EXISTS` / `TESTED_*`; real outcome **OPEN** (`RESTART_RECOVERY_LADDER_STEP_CLOSED=false`) |
| PRODUCTIVE_ENTRYPOINT | `run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py` + wallclock binding CLI |
| SESSION_SPEC | `phase_9_2_public_md_restart_recovery_session_v1` / restart contracts under `config&#47;ops&#47;phase_9_2_*` |
| AUTHORIZATION_SCOPE | Session-GO + Owner-GO + Owner-Session-GO + per-segment single-use auth + confirm-token (required later; not started by binding merge) |
| STATE_ROOTS | Cap 6.4 adapter fields including `confirmation_session_id`, atomic commit position |
| FAULT_OR_SESSION_MECHANISM | PRE → controlled exit 82 → POST new process; same-process POST rejected |
| EVIDENCE_BUNDLE | Binding evidence package + future real-session bundle |
| VERIFIER | `verify_restart_bundle_v1` / harness verifier |
| PREDECESSOR | One-hour |
| SUCCESSOR | Rate-Limit/Reconnect |
| OPEN_GAPS | `EVIDENCE_GAP`: governed real Public-MD session not observed at forensic SHA |
| CLOSURE_CRITERIA | Separately authorized real session + verifier PASS; merge alone insufficient |

### Step 4 — Rate-Limit/Reconnect

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `OPEN` |
| PRODUCTIVE_ENTRYPOINT | **Missing Step-4 binding entrypoint** (must reuse wallclock runner; not yet packaged) |
| SESSION_SPEC | Ladder name `RATE_LIMIT_RECONNECT_SESSION` only; dedicated productive binding config **absent** |
| AUTHORIZATION_SCOPE | Not issued for Step 4 |
| STATE_ROOTS | Must reuse Cap 6.x / Cap 7.2 roots; no parallel state model |
| FAULT_OR_SESSION_MECHANISM | **CURRENT_GAP** — governed 429/reconnect/stale fault path not bound as Step-4 session |
| EVIDENCE_BUNDLE | Preflight `pacing_rate_limit_proof_v1.json` only (not session closure) |
| VERIFIER | Not Step-4-closed |
| PREDECESSOR | Step 3 (restart/recovery) |
| SUCCESSOR | Prolonged natural market |
| OPEN_GAPS | `WIRING_GAP` + `EVIDENCE_GAP` (see §14) |
| CLOSURE_CRITERIA | Binding capability + governed real session + verifier PASS; no improvised harness |

### Step 5 — Prolonged Natural Market

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `OPEN` |
| PRODUCTIVE_ENTRYPOINT | Reuse wallclock / stateful host after Steps 3–4 surfaces exist |
| SESSION_SPEC | Not materialized as closed productive binding |
| AUTHORIZATION_SCOPE | Separate Owner-GO required |
| STATE_ROOTS | Same canonical roots |
| FAULT_OR_SESSION_MECHANISM | Natural duration continuity |
| EVIDENCE_BUNDLE | Absent for closed claim |
| VERIFIER | Absent for closed claim |
| PREDECESSOR | Step 4 |
| SUCCESSOR | Adverse/stale |
| OPEN_GAPS | `DEFERRED_REQUIRED_CAPABILITY` / `EVIDENCE_GAP` |
| CLOSURE_CRITERIA | Master Runbook Phase 9.2 metrics + verifier PASS |

### Step 6 — Adverse/Stale Data

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `OPEN` (binding ready; governed session not closed) |
| PRODUCTIVE_ENTRYPOINT | `scripts&#47;ops&#47;run_phase_9_2_step_6_adverse_stale_data_session_continuation_v1.py` |
| PRODUCTIVE_STEP6_EXECUTOR | `ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1` |
| SESSION_SPEC | `config&#47;ops&#47;phase_9_2_public_md_adverse_stale_data_session_contract_v1.json` |
| AUTHORIZATION_SCOPE | Separate Owner-GO for later real session; binding itself `NETWORK_SESSION_ALLOWED=false` |
| STATE_ROOTS | Canonical |
| STALE_DATA_CLASSIFIER | `heartbeat_staleness_v1.StalenessTrackerV1` |
| ADVERSE_DATA_CLASSIFIER | `killstate_runtime_v1.STALE_DATA` |
| FAULT_OR_SESSION_MECHANISM | `governed_injected_stale_data_fault_v1` (`RECEIVE_LAG` / `DATA_HOLD` only; default disabled) |
| EVIDENCE_BUNDLE | `docs&#47;evidence&#47;capability_phase_9_2_step_6_adverse_stale_data_session_continuation_v1&#47;SUMMARY.json` |
| VERIFIER | `verifier_v1` (binding + later productive session contract) |
| PREDECESSOR | Step 5 |
| SUCCESSOR | Multi-session campaign |
| OPEN_GAPS | `EVIDENCE_GAP` for governed real-network Step-6 session closure |
| CLOSURE_CRITERIA | Stale blocks Alpha without fabricated observations; productive session verifier PASS |

### Step 7 — Multi-Session Continuity Campaign

| Field | Value |
| --- | --- |
| CURRENT_STATUS | `OPEN` |
| PRODUCTIVE_ENTRYPOINT | Campaign harness not closed |
| SESSION_SPEC | Ladder name `MULTI_SESSION_CONTINUITY_CAMPAIGN` |
| AUTHORIZATION_SCOPE | Repeated governed sessions; separate GOs |
| STATE_ROOTS | Cross-session continuity of durable roots |
| FAULT_OR_SESSION_MECHANISM | Repeated continuity under prior step mechanisms |
| EVIDENCE_BUNDLE | Absent for closure |
| VERIFIER | Absent for closure |
| PREDECESSOR | Step 6 |
| SUCCESSOR | Phase 9.2 ladder complete → feeds natural lifecycle DoD |
| OPEN_GAPS | `EVIDENCE_GAP` |
| CLOSURE_CRITERIA | `PHASE_9_2_SESSION_LADDER_COMPLETE=true` only after all steps evidenced |

```text
PHASE_9_2_SESSION_LADDER_COMPLETE=false
ONE_HOUR_RESTART_RECONNECT_PROLONGED_ADVERSE_REPEATED_LADDER_FULLY_CLOSED=false
SEPARATE_OWNER_GO_REQUIRED_FOR_PUBLIC_MD_NETWORK_SESSION=true
```

------------------------------------------------------------------------

# 21. Dashboard and Presentation Isolation Boundary

## Graph E — Dashboard Isolation

```text
Runtime SSOT
→ Persistence / Evidence
→ Read Model
→ Dashboard
```

Explicit negatives:

```text
Dashboard ↛ Runtime Decision
Dashboard ↛ Authorization
Dashboard ↛ Reconciliation
Dashboard ↛ Evidence Generation
Dashboard ↛ Restart
Dashboard ↛ Trading Input
```

Repository surfaces:

- Master Runbook §4.4 / §4.7 Canonical Presentation Architecture
- `docs/runbooks/canonical/PEAK_TRADE_CANONICAL_PRESENTATION_IMPLEMENTATION_RUNBOOK.md`
- `docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`
- `src&#47;webui&#47;market_dashboard_landscape_v2&#47;*` projections / presenters

```text
DASHBOARD_READ_ONLY_CONSUMER=true
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_TRADING_INPUT=false
RUNTIME_DEPENDS_ON_DASHBOARD=false
```

This map adds **no** dashboard runtime dependency.

------------------------------------------------------------------------

# 22. Testnet, Live, Credential and Order Isolation Boundary

Under Cap 7.2 / Phase 9.2 contracts at forensic SHA:

```text
enable_live_trading / live_authorized / orders_authorized = false (program boundary)
testnet_authorized=false
paper_execution_authorized=false
exchange_credentials_loaded=false
real_capital_movement=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

Phase 11 documents Testnet→Live progression as architecture only. Nothing
in this map, Cap 7.2 activation, or Phase 9.2 binding merges authorizes
those modes.

------------------------------------------------------------------------

# 23. Predecessor/Successor Capability Handoff Map

```text
Cap 6.0 Preflight (historical)
→ Cap 6.1 Confirmation/C1
→ Cap 6.2 Dynamic Scope
→ Cap 6.3 Config ownership (residual review item)
→ Cap 6.4 Atomic restart
→ Cap 6.5 Exit-policy producers
→ Cap 7.1 Deterministic simulated lifecycle evidence
→ Cap 7.2 Offline no-order activation
→ G17 Typed volatility→CMC (CLOSED_AND_COLD_START_PROVEN)
→ Phase 9.2 ladder continuation (CURRENT_CRITICAL_PATH)
    Step1 Smoke PASS
    → Step2 One-hour PASS (SHA-bound)
    → Step3 Restart binding READY; real session OPEN
    → Step4 Rate-limit/reconnect binding REQUIRED (this map’s named next binding)
    → Steps 5–7 OPEN
→ Phase 10 Numeric max-age decision (optional / non-enforcing now)
→ Phase 11 Testnet/Live autonomy (separate unauthorized program)
```

Handoff contract (Master Runbook §22.1): each capability must declare input
and output state roots, bind predecessor digests, and leave outputs
directly consumable without parallel authority adapters.

------------------------------------------------------------------------

# 24. Unresolved Gaps and Required Binding Order

1. **Do not reopen** Cap 6.1–6.5 / 7.1–7.2 / G17 as Immediate Next.
2. Complete **Step 3 governed real Public-MD restart/recovery session**
   (authorization + confirm-token + verifier PASS). Classification:
   `EVIDENCE_GAP`.
3. Materialize **`PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1`**
   reusing existing pacing/429/reconnect/stale owners — no improvised
   harness. Classification: `WIRING_GAP`.
4. Execute Step 4 governed real session → Steps 5–7 in ladder order.
5. Close Public-MD natural lifecycle evidence (`EVIDENCE_GAP`).
6. Reconcile Master Runbook current-truth SHA field (`DOCUMENTATION_DRIFT`)
   under a docs-only capability when Owner-authorized.
7. Keep Live/Testnet/credentials/`MULTI_FUTURE` fail-closed
   (`INTENTIONAL_SAFETY_BARRIER`).

------------------------------------------------------------------------

# 25. Repository Evidence Index

| Evidence / owner surface | Role |
| --- | --- |
| `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` | Semantic authority |
| `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` | Navigation only |
| `src/ops/single_future_stateful_no_order_runtime_activation_v1/` | Cap 7.2 |
| `src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/` | Productive host |
| `src/ops/stateful_confirmation_and_c1_productive_binding_v1/` | Cap 6.1 |
| `src/ops/dynamic_scope_persistence_binding_v1/` | Cap 6.2 |
| `src/ops/full_decision_path_atomic_restart_closure_v1/` | Cap 6.4 |
| `src/ops/exit_policy_producer_binding_v1/` | Cap 6.5 |
| `src/ops/simulated_entry_reduce_exit_actionability_evidence_v1/` | Cap 7.1 |
| `src/ops/productive_reconciliation_runtime_binding_v1/` | Reconciliation |
| `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` | Master V2 / Double Play |
| `src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/` | Public-MD session runtime |
| `src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/` | Auth issuance + wallclock entry |
| `src/ops/phase_9_2_public_md_session_preflight_v1/` | Ladder/preflight |
| `src/ops/phase_9_2_restart_recovery_session_contract_and_productive_harness_v1/` | Step 3 harness |
| `src/ops/phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1/` | Step 3 binding |
| `docs/ops/specs/CAPABILITY_PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1.md` | Step 3 capability spec |
| `docs/evidence/capability_phase_9_2_long_running_stateful_public_md_simulation_evidence_v1/` | Phase 9.2 evidence root |
| `src/webui/market_dashboard_landscape_v2/` | Presentation read models |
| `docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md` | Sibling derived wiring map (strategy-specific; not this map’s SSOT) |

------------------------------------------------------------------------

# 26. Drift and Update Procedure

1. Re-read Master Runbook completely before any mutations that claim current
   runtime truth.
2. Bind every refresh to exact `git rev-parse origin/main`.
3. Re-run forensic enumeration of entrypoints, callers, state roots, config
   consumers, persistence owners, evidence producers and verifiers.
4. Recompute this document’s raw-byte `DOCUMENT_SHA256`.
5. Classify new findings only with Master Runbook gap vocabulary (§20).
6. Never promote `CODE_EXISTS` to `CAPABILITY_CLOSED` without evidence +
   verifier.
7. Never use this map to authorize network sessions, authorization
   consumption, Live/Testnet, credentials, or capital movement.
8. If `origin/main` ≠ `FORENSIC_REPOSITORY_SHA`, treat this document as
   `STALE` until refreshed.

```text
END_STATE_WIRING_MAP_COMPLETE=true_for_forensic_sha_binding
UNSUPPORTED_CLAIMS_POLICY=ZERO_UNPROVEN_CLOSED_CLAIMS
```
