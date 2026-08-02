# Peak_Trade Master Runbook --- Canonical Stateful No-Order System Finish V2.2

**DOCUMENT_CLASS:** `CANONICAL_MASTER_RUNBOOK`\
**STATUS:** `CANONICAL_WORKING_AUTHORITY`\
**RATIFIED_BY_OWNER:** `true`\
**REPOSITORY_PATH:** `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`\
**AUTHORITY_EFFECT:** `IMPLEMENTATION_AND_OPERATIONAL_SEMANTIC_AUTHORITY`\
**RUNTIME_AUTHORIZATION_EFFECT:** `NONE`\
**AUTHORITY:** Repository Owner / Operator\
**SYSTEM:** Peak_Trade Futures-only, Master V2 / Double Play\
**FORENSIC_BASELINE_SHA:** `a8653d520ba3563dddb41aa175445d14725ac9b9`\
**FORENSIC_BASELINE_SOURCE:**
`FULL_SYSTEM_CANONICAL_RUNTIME_COMPLETENESS_AND_RUNBOOK_INPUT_AUDIT_V1`\
**PREVIOUS_RUNBOOK_BASELINE:**
`docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`\
**SUPERSEDES:**
`docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md`\
**TARGET_RUNTIME:** Fully stateful canonical runtime with public market
data and simulated execution\
**ORDER_BOUNDARY:** No Live orders, no Testnet orders, no
exchange-credential use, no real-capital movement\
**CURRENT_SELECTION_MODE:** `SINGLE_SELECTED_FUTURE`\
**CURRENT_MAX_POSITIONS:** `1`\
**MULTI_FUTURE_RUNTIME_AUTHORIZED:** `false`\
**VOLATILITY_NUMERIC_MAX_AGE_ENFORCING:** `false`\
**DASHBOARD_AUTHORITY_EFFECT:** `NONE`\
**REVISION:** `V2.3_SEMANTIC_INTEGRATION_FULL_AUTONOMY_TARGET_RELEASE`\
**RATIFICATION_STATE:**
`OWNER_RATIFIED_PENDING_MERGE_SHA_BINDING`\
**REPOSITORY_SHA:** `PENDING_UNTIL_MERGE_TO_ORIGIN_MAIN`\
**DOCUMENT_SHA256:** `PENDING_SEE_RATIFICATION_MANIFEST`\
**VERIFIED_AT:** `PENDING_SEE_RATIFICATION_MANIFEST`\
**STALE_IF_HEAD_DIFFERS:** `true`

------------------------------------------------------------------------

# 0. Purpose and Binding Interpretation

This runbook is the Owner-ratified canonical implementation and closure plan
for completing Peak_Trade as a coherent, stateful, restart-safe and
evidence-proven trading runtime while keeping all exchange-order paths
disabled. Repository working authority is established by placement and Owner
ratification; merge-SHA binding remains pending in the ratification manifest.

It defines:

1.  how Peak_Trade is intended to operate logically;
2.  what is already implemented, bound, persisted or proven;
3.  which runtime gaps remain;
4.  the mandatory capability sequence to reach the target state;
5.  the safety, evidence and activation gates that must remain intact;
6.  how future unknown gaps are detected and incorporated without
    silently changing the trading logic;
7.  how the canonical stateful core is extended through Testnet and a
    separately authorized Live program into bounded full autonomy.

This runbook does not itself authorize:

``` text
LIVE_TRADING
TESTNET_EXECUTION
PAPER_EXCHANGE_ORDERS
EXCHANGE_CREDENTIAL_USE
REAL_CAPITAL_MOVEMENT
MULTI_FUTURE_RUNTIME
CORE_TRADING_LOGIC_CHANGES
```

The runbook may describe future Testnet and Live programs, but those
programs remain separate and unauthorized until explicit Owner-GO is
issued under their own contracts.

------------------------------------------------------------------------

# 1. Canonical Prime Directive

Peak_Trade is a trading engine, not a capability collection.

Every capability must close a specific, provable edge in the canonical
trading path:

``` text
Startup / Restart:
Persisted Selection
→ Native Instrument Binding
→ Reconciliation Gate
→ Public Market Data
→ Distinct Observation Acceptance
→ Features
→ Market State
→ Directional Confirmation
→ Master V2
→ Double Play
→ Dynamic Scope
→ Survival / Suitability / Composition
→ Risk
→ Safety
→ Intent

Economic Transition:
Intent
→ Simulated Execution
→ Futures Accounting
→ Portfolio Persistence
→ Economic Verification / Reconciliation
→ Evidence
→ Restart Recovery
→ Operator Oversight
```

A capability is P0/P1 only when it:

-   closes a gap in this path;
-   preserves or improves state continuity;
-   improves deterministic restart or recovery;
-   proves Entry, Exit, Fee, Slippage, Risk or Safety behavior;
-   removes ambiguous authority or hidden config drift;
-   prevents unsafe activation or evidence overclaim.

Governance and documentation are required when they protect runtime
truth, but they must not displace the trading-path finish sequence.

------------------------------------------------------------------------

# 2. Non-Negotiable Safety Boundary

## 2.1 Target runtime boundary

The intended finish state of this program is:

``` text
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
PUBLIC_MARKET_DATA_ACTIVE=true
NO_LIVE_ORDERS=true
NO_TESTNET_ORDERS=true
NO_PAPER_EXCHANGE_ORDERS=true
NO_EXCHANGE_CREDENTIAL_USE=true
REAL_CAPITAL_MOVEMENT=false
```

The system may fully evaluate market data, generate Entry/Reduce/Exit
intents, produce simulated fills, apply Fees and Slippage, update
portfolio state, reconcile, restart and generate evidence.

It must not submit any order to an exchange.

## 2.2 Required negative controls

Until separate programs are authorized, the following must remain false
or unreachable:

``` text
enable_live_trading=false
live_authorized=false
orders_authorized=false
testnet_authorized=false
paper_execution_authorized=false
runtime_bridge_live_activated=false
exchange_credentials_loaded=false
real_capital_movement=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

## 2.3 Physical execution separation

The completed no-order runtime must terminate at a simulated execution
boundary:

``` text
Canonical Intent
→ SimulatedExecutionPort
→ Simulated Fill
→ Canonical Futures Accounting
```

It must not rely only on a Boolean switch to avoid real orders. Real
venue execution must remain physically and authoritatively separate from
the no-order host.

Required proof:

``` text
REAL_EXECUTION_ADAPTER_CONSTRUCTED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
ORDER_SIDE_EFFECT_OCCURRED=false
```

## 2.4 Core logic protection

Wiring, persistence, restart, config, evidence and activation
capabilities must not silently change:

-   Master V2;
-   Double Play;
-   Bull/Bear logic;
-   confirmation semantics;
-   Dynamic Scope rules;
-   Composition precedence;
-   Entry/Exit precedence;
-   Risk decisions;
-   Safety decisions.

Every implementation must report exactly one of:

``` text
CORE_LOGIC_CHANGE=false
```

or:

``` text
CORE_LOGIC_CHANGE=true
OWNER_RATIFICATION_REQUIRED=true
```

Default expectation for Capabilities 6.x and 7.x:

``` text
CORE_LOGIC_CHANGE=false
```

## 2.5 Execution-mode terminology

The following terms are binding and must not be used interchangeably:

  -----------------------------------------------------------------------
  Term                                Binding meaning
  ----------------------------------- -----------------------------------
  `SHADOW`                            Decision evaluation without
                                      exchange orders. A session contract
                                      must state whether simulated
                                      economics are committed.

  `INTERNAL_SIMULATED_EXECUTION`      Canonical simulated fills, Fees,
                                      Slippage, Accounting and Portfolio
                                      persistence with no exchange side
                                      effect.

  `PAPER_EXCHANGE_EXECUTION`          Venue- or adapter-based demo/paper
                                      orders. Forbidden in this program.

  `PUBLIC_MD_NO_ORDER`                Public market-data access only; no
                                      private endpoint, credential or
                                      order side effect.
  -----------------------------------------------------------------------

Mandatory rule:

``` text
SHADOW != INTERNAL_SIMULATED_EXECUTION
INTERNAL_SIMULATED_EXECUTION != PAPER_EXCHANGE_EXECUTION
PAPER_EXCHANGE_EXECUTION_ALLOWED=false
```

------------------------------------------------------------------------

# 3. Canonical Status Semantics

The following terms are not interchangeable.

  -----------------------------------------------------------------------------
  Status                                    Binding meaning
  ----------------------------------------- -----------------------------------
  `DOCUMENTED`                              A target, contract or description
                                            exists.

  `DTO_EXISTS`                              A data structure exists.

  `CODE_EXISTS`                             An implementation exists.

  `TESTED_UNIT`                             Direct unit behavior is tested.

  `TESTED_INTEGRATION`                      Multiple components are tested
                                            together.

  `CONFIG_EXISTS`                           A config value or schema exists.

  `CONFIG_CONSUMED`                         A productive consumer reads the
                                            config.

  `BOUND`                                   A component is connected to a call
                                            graph.

  `RUNTIME_REACHABLE`                       A productive entrypoint can execute
                                            it.

  `HOST_READY_FOR_ACTIVATION`               The host graph is complete enough
                                            to start under its current
                                            contract.

  `STATEFUL_RUNTIME_READY_FOR_ACTIVATION`   Required decision state,
                                            persistence and restart closure are
                                            proven.

  `ACTIVATED`                               Runtime execution is authorized and
                                            running under valid gates.

  `PERSISTED`                               State is durably stored.

  `RESTART_LOADED`                          Persisted state is loaded after
                                            restart.

  `RESTART_PROVEN`                          Post-restart behavior is
                                            deterministically verified.

  `PATH_REACHABLE`                          A path can be called.

  `OUTCOME_OBSERVED`                        The intended outcome occurred in a
                                            governed session.

  `EVIDENCE_PROVEN`                         Evidence and verifier prove the
                                            claimed behavior.

  `CAPABILITY_CLOSED`                       All capability-specific closure
                                            criteria are satisfied.
  -----------------------------------------------------------------------------

Mandatory rule:

``` text
Implemented
≠ Bound
≠ Reachable
≠ Stateful
≠ Restart-Proven
≠ Activated
≠ Outcome-Observed
≠ Evidence-Proven
≠ Closed
```

------------------------------------------------------------------------

# 4. Canonical Authority Model

## 4.1 Runtime authority

Runtime authority remains in code and explicitly ratified runtime
contracts.

Documentation is semantic and operational authority for implementation,
but may not simulate runtime truth.

## 4.2 Decision authority

The canonical decision chain is:

``` text
Market State
→ Master V2
→ Double Play
→ Survival / Suitability / Composition
→ Risk
→ Safety
→ Intent
```

No research strategy, dashboard component, legacy evaluator or utility
script may bypass this chain.

## 4.3 Strategy authority

Named research models and strategy implementations are non-authority
unless explicitly promoted by a later capability.

Current default classification:

``` text
Armstrong                 = RESEARCH_INFORMATION
El Karoui                 = RESEARCH_INFORMATION
Ehlers                    = RESEARCH_INFORMATION
Bouchaud                  = RESEARCH_INFORMATION
Lopez de Prado            = RESEARCH_INFORMATION
Gatheral                  = RESEARCH_INFORMATION
Bollinger / Midband       = RESEARCH_INFORMATION
ECM / ECM Cycle           = LEGACY_OR_NON_AUTHORITY
Momentum / MR / Trend     = REGISTRY_OR_RESEARCH
```

Permitted direction:

``` text
Research Signal
→ Suitability / Composition input
→ Master V2 / Double Play authority
```

Forbidden direction:

``` text
Research Strategy
→ Direct Intent
→ Direct Fill
→ Direct Order
```

## 4.4 Dashboard authority

The dashboard is always:

``` text
READ_ONLY_CONSUMER=true
TRADING_INPUT=false
SSOT=false
AUTHORITY_EFFECT=NONE
```

Permitted flow:

``` text
Runtime SSOT
→ Persistence / Evidence
→ Read Model
→ Dashboard
```

Forbidden flow:

``` text
Dashboard
→ Runtime Decision
```

## 4.5 Universe, ranking and selection authority

Current single-future authority chain:

``` text
Governed Futures Universe
→ Productive Ranking
→ Persisted Single Selected Future
→ Native Instrument Binding
→ Runtime Consumer
```

Semantics:

``` text
TOP20 = candidate context only
SINGLE_SELECTED_FUTURE = current trading selection authority
TOP_N_ACTIVE_SET = future multi-future authority, currently unauthorized
```

## 4.6 Volatility authority

Typed volatility presence may participate in already-ratified Alpha
gating.

Numeric volatility max-age remains non-enforcing at the forensic
baseline.

Until a separate evidence-based Owner-ratified capability changes this
policy:

``` text
NUMERIC_MAX_AGE_EFFECT=DIAGNOSTIC_ONLY
ENFORCEMENT_ENABLED=false
ALPHA_MUTATION=false
RISK_MUTATION=false
SAFETY_MUTATION=false
```

Numeric max-age must not block the finish of the stateful runtime unless
a separate, evidence-based Owner-ratified capability changes this
policy.

------------------------------------------------------------------------

# 5. Current Forensic Runtime Truth at Baseline SHA

## 5.1 Baseline

``` text
FORENSIC_BASELINE_SHA=a8653d520ba3563dddb41aa175445d14725ac9b9
BRANCH=main
HEAD_EQUALS_ORIGIN_MAIN=true
TRACKED_WORKTREE_CLEAN=true
UNTRACKED_EVIDENCE_PRESERVED=true
```

The baseline is an evidence snapshot, not a timeless constant. Every
implementation capability must revalidate the actual `origin/main` SHA.

## 5.2 Current host and activation truth

``` text
CANONICAL_RUNTIME_ENTRYPOINT_STATUS=READY_FOR_ACTIVATION
FULL_CANONICAL_CALL_GRAPH_PROVEN=true_for_single_future_no_order_host_graph_only
FULL_CANONICAL_STATEFUL_RUNTIME_CURRENTLY_EXISTS=false
FULL_CANONICAL_STATEFUL_RUNTIME_CURRENTLY_ACTIVATED=false
SIMULATED_EXECUTION_FULLY_REACHABLE=BOUND_NOT_ACTIVATED_ZERO_FILL_EVIDENCE
CURRENT_CAP52_AUTHORIZATION_VALID_FOR_NEW_RUN=NOT_PROVEN
REAUTHORIZATION_REQUIRED_BEFORE_NEW_RUN=true
TESTNET_REACHABLE=false
LIVE_REACHABLE=false
```

Interpretation:

-   The single-future no-order host graph is largely assembled.
-   The complete stateful decision runtime is not yet closed.
-   Host readiness must not be treated as stateful-runtime readiness.
-   Activation must not occur until Capabilities 6.1--7.1 satisfy their
    gates.

## 5.3 Canonical productive no-order call graph

``` text
Authorization validation / consumption
→ Session lock
→ Governed futures universe
→ Productive ranking
→ Persisted single selected future
→ Native instrument binding
→ Reconciliation
→ OKX public market data capture
→ Public-MD no-order shadow replay
→ Features
→ Typed volatility presence
→ Master V2
→ Double Play
→ cycle-local Survival / Suitability / Composition where reached
→ Risk
→ Safety
→ Intent
→ Simulated fill
→ Canonical futures accounting
→ Portfolio and risk persistence
→ Evidence
→ Verifier
```

## 5.4 Closed or materially established baseline capabilities

The following are no longer to be treated as missing greenfield work:

  -----------------------------------------------------------------------
  Capability area                     Baseline state
  ----------------------------------- -----------------------------------
  Productive reconciliation           Bound, persisted, restart proven
                                      for its current scope.

  Governed futures universe           Bound, persisted, restart proven.

  Productive ranking                  Bound, persisted, restart proven.

  Single selected future              Bound, persisted, restart proven.

  Native instrument binding           Runtime consumed.

  Canonical futures accounting        Bound with model/integration tests.

  Portfolio/risk persistence          Persisted.

  Public-MD no-order host             Bound and evidence-producing.

  Master V2 / Double Play             Runtime reachable and
                                      parity-proven.

  Live/Testnet blocking               Fail-closed and outside Cap5 host.
  -----------------------------------------------------------------------

These components must still be revalidated after relevant changes, but
they are not the active critical-path starting point.

## 5.5 Current critical state gaps

``` text
C1_PRODUCTIVELY_BOUND=false
C2_PRODUCTIVELY_BOUND=false
C3_PRODUCTIVELY_BOUND=partial
CONFIRMATION_STATE_PERSISTED=false
CONFIRMATION_SESSION_ID_STABLE=false
DYNAMIC_SCOPE_STATE_PERSISTED=false
MASTER_V2_STATE_PERSISTED=false
DOUBLE_PLAY_STATE_PERSISTED=false
RESTART_END_TO_END_PROVEN=partial
```

## 5.6 Current evidence gaps

``` text
ENTRY_FILL_EVIDENCE_PROVEN=false
EXIT_FILL_EVIDENCE_PROVEN=false
FEE_EVIDENCE_PROVEN=false
SLIPPAGE_EVIDENCE_PROVEN=false
NONZERO_SIMULATED_ECONOMICS_EVIDENCE=false
```

## 5.7 Current known defects and drifts

``` text
CORE_LOGIC_DEFECT_DETECTED=false
WIRING_DEFECTS_DETECTED=true
STATE_PERSISTENCE_DEFECTS_DETECTED=true
CONFIG_DRIFT_DETECTED=true
DOCUMENTATION_DRIFT_DETECTED=true
EVIDENCE_CLAIM_DEFECTS_DETECTED=true
LEGACY_PARALLEL_AUTHORITY_DETECTED=false_on_productive_Cap2x_to_Cap5x_hosts
```

------------------------------------------------------------------------

# 6. Canonical State Ownership and Persistence Model

## 6.1 State categories

Every runtime state must be classified as exactly one of:

``` text
DURABLE_SOURCE_STATE
DURABLE_DECISION_STATE
DERIVED_REBUILDABLE_STATE
EPHEMERAL_SESSION_STATE
EVIDENCE_ONLY_STATE
```

## 6.2 Durable source state

Already durable or substantially proven:

-   Universe Snapshot;
-   Ranking Snapshot;
-   Selected Future;
-   Reconciliation State;
-   Portfolio State;
-   Accounting State;
-   typed volatility state where explicitly configured;
-   evidence ledgers and manifests.

## 6.3 Required durable decision state

The finish program must derive the persistence schema from the actual
canonical domain contracts and persist only the minimal sufficient
state.

Mandatory rules:

``` text
PERSISTENCE_SCHEMA_DERIVED_FROM_ACTUAL_DOMAIN_CONTRACTS=true
NO_NEW_PARALLEL_STATE_MODEL=true
NO_DUPLICATION_OF_DETERMINISTICALLY_REBUILDABLE_STATE=true
```

The required semantic restoration scope includes:

-   C1 observation identity and epoch progression;
-   C2 directional confirmation carrier;
-   stable confirmation session identity;
-   Dynamic Scope runtime state;
-   required Master V2 / Double Play carrier state;
-   survival/suitability/composition state where continuity affects
    decisions;
-   pending Exit policy state where time or invalidation continuity
    matters.

## 6.4 Derived rebuildable state

A value should not be duplicated in persistence if it can be
deterministically rebuilt from canonical durable state.

Examples may include:

-   feature vectors rebuilt from persisted market observations;
-   regime derived from deterministic feature state;
-   current unrealized PnL derived from position and mark;
-   immutable config-derived rule objects.

Each rebuildable field requires:

``` text
REBUILD_INPUTS_EXPLICIT=true
REBUILD_DETERMINISTIC=true
REBUILD_DIGEST_MATCH_PROVEN=true
```

## 6.5 Atomicity requirement

A cycle must not commit mutually inconsistent runtime state such as:

``` text
confirmation advanced but scope not committed
scope advanced but observation epoch not committed
simulated fill committed but portfolio not committed
```

Runtime-state commit and evidence materialization are separate
durability concerns:

``` text
RUNTIME_STATE_COMMIT
EVIDENCE_MATERIALIZATION
```

An evidence-write failure must not silently roll back a valid economic
commit. It must create a durable pending-evidence cursor or equivalent
idempotent recovery state.

Capability 6.4 must choose and prove one of:

1.  atomic runtime-state bundle;
2.  write-ahead journal with deterministic recovery;
3.  versioned multi-record transaction with commit marker and replay.

## 6.6 Single-writer requirement

There must be one authoritative writer per state root.

At minimum:

``` text
Observation/Confirmation Writer = single
Dynamic Scope Writer            = single
Portfolio/Accounting Writer     = single
Selection Writer                = single
Reconciliation Writer           = single
Evidence Commit Writer          = single or idempotently partitioned
```

Writer conflicts must hard-stop before Alpha advances.

------------------------------------------------------------------------

# 7. Event-Time, Identity and Ordering Semantics

The runtime must distinguish:

  -----------------------------------------------------------------------
  Field                               Meaning
  ----------------------------------- -----------------------------------
  `market_event_time`                 Time assigned to the market
                                      observation by the market-data
                                      contract.

  `observation_identity`              Stable identity of the accepted
                                      market observation.

  `observation_epoch`                 Monotonic epoch that advances only
                                      on accepted DISTINCT observations.

  `decision_cycle_id`                 Host cycle identifier; must not
                                      substitute for observation epoch.

  `confirmation_session_id`           Stable ID for one confirmation
                                      lifecycle and instrument context.

  `runtime_session_id`                Host/session execution identity.

  `persistence_commit_time`           Time at which durable state was
                                      committed.

  `wall_clock_time`                   Operational clock; not market-event
                                      authority.
  -----------------------------------------------------------------------

Mandatory invariants:

``` text
DUPLICATE_OBSERVATION_DOES_NOT_ADVANCE=true
MISSING_OBSERVATION_DOES_NOT_ADVANCE=true
DECISION_CYCLE_DOES_NOT_IMPLY_NEW_OBSERVATION=true
CONFIRMATION_SESSION_ID_STABLE_ACROSS_CYCLES=true
INSTRUMENT_STATE_ISOLATED=true
EVENT_ORDER_VALIDATED=true
```

Out-of-order, duplicate, stale or conflicting observations must be
classified explicitly and fail safely.

------------------------------------------------------------------------

# 8. Evidence Claim Semantics

## 8.1 Entry evidence ladder

``` text
ENTRY_PATH_CODE_EXISTS
→ ENTRY_PATH_RUNTIME_REACHABLE
→ ENTRY_INTENT_OBSERVED
→ ENTRY_SIMULATED_FILL_OBSERVED
→ ENTRY_ACCOUNTING_APPLIED
→ ENTRY_PORTFOLIO_PERSISTED
→ ENTRY_RESTART_RECONSTRUCTED
→ ENTRY_END_TO_END_EVIDENCE_PROVEN
```

## 8.2 Exit evidence ladder

``` text
EXIT_PATH_CODE_EXISTS
→ EXIT_PATH_RUNTIME_REACHABLE
→ EXIT_INDEPENDENCE_PROVEN
→ EXIT_INTENT_OBSERVED
→ EXIT_SIMULATED_FILL_OBSERVED
→ EXIT_ACCOUNTING_APPLIED
→ EXIT_PORTFOLIO_PERSISTED
→ EXIT_RESTART_RECONSTRUCTED
→ EXIT_END_TO_END_EVIDENCE_PROVEN
```

## 8.3 Fee and slippage evidence

Model defaults or unit tests do not prove productive economics.

Required proof:

``` text
SIMULATED_FILL_COUNT>0
TOTAL_FEES>0
TOTAL_SLIPPAGE>0
ACCOUNTING_RECONSTRUCTION_MATCH=true
EVIDENCE_VERIFIER_PASS=true
```

## 8.4 Claim correction rule

`EXIT_PATH_PROVEN=true` may not be emitted solely because an exit
function is callable.

Use one of:

``` text
EXIT_PATH_REACHABLE=true
EXIT_INDEPENDENCE_PROVEN=true
EXIT_FILL_OBSERVED=true
EXIT_END_TO_END_EVIDENCE_PROVEN=true
```

Each field must be tied to actual evidence.

------------------------------------------------------------------------

# 9. Config Truth and Consumer Ownership

## 9.1 Canonical rule

A runtime-relevant value is canonical only when all are true:

``` text
CONFIG_SCHEMA_EXISTS=true
CONFIG_VALUE_EXPLICIT=true
CONFIG_CONSUMER_IDENTIFIED=true
EFFECTIVE_VALUE_PROVEN=true
CONFIG_DIGEST_PERSISTED=true
NO_SILENT_FALLBACK=true
```

## 9.2 Confirmed config drift and ownership review

The forensic baseline distinguishes confirmed config drift from values
that merely require ownership review.

### Confirmed config drift

``` text
confirmation_epochs=2
up_distance=200.0
adverse_exit_distance=80.0
reversal_distance=120.0
```

These values are runtime-relevant and locally owned in the bridge rather
than consumed from a canonical typed configuration surface.

### Config ownership review required

``` text
PRICE_PATH_MAX_LEN=64
fee_rate_bps=2.0
slippage_bps=1.0
```

These values are hardcoded or locally owned, but the forensic baseline
does not by itself prove that they are semantically incorrect.

Before migration, classify each value as exactly one of:

``` text
IMMUTABLE_DOMAIN_CONSTANT
CANONICAL_RUNTIME_CONFIG
EXECUTION_MODEL_CONFIG
ACCOUNTING_MODEL_CONSTANT
TEST_FIXTURE_ONLY
```

The required closure is:

``` text
runtime-relevant value
→ explicit classification
→ typed canonical owner where required
→ explicit productive consumer
→ version and digest
→ evidence binding
→ no fallback ambiguity
```

Core trading semantics and numeric values must remain unchanged unless a
separate Owner-authorized core/config-policy capability explicitly
changes them.

## 9.3 Forbidden defaults

Silent fallback is forbidden for:

-   selected instrument;
-   native instrument binding;
-   mark price;
-   volatility;
-   observation identity;
-   confirmation session ID;
-   Dynamic Scope state;
-   portfolio state;
-   risk limits;
-   authorization;
-   confirm token;
-   event time;
-   execution adapter;
-   order authorization.

Missing truth must become `MISSING`, `INVALID`, `STALE` or `CONFLICT`
and fail closed.

After any prior durable commit:

``` text
SILENT_CONFIRMATION_REINITIALIZATION=false
SILENT_DYNAMIC_SCOPE_REINITIALIZATION=false
```

------------------------------------------------------------------------

# 10. Known Gap Register

  -------------------------------------------------------------------------------------------------------------------------------------
  Gap                       Classification                            Severity Required resolution                Blocks
  ------------------------- -------------------------------- ----------------- ---------------------------------- ---------------------
  `G01` C1 not productively `WIRING_GAP`                                  HIGH Bind real Distinct Observation     Stateful runtime,
  bound                                                                        Acceptor in canonical host.        actionability

  `G02` C2 carrier not      `STATE_PERSISTENCE_GAP`                       HIGH Persist directional confirmation   Confirmation, restart
  persisted                                                                    state by stable session/instrument 
                                                                               key.                               

  `G03` C3 receives         `WIRING_GAP`                                  HIGH Pass actual C1 acceptance result.  Candidate/Confirmed
  non-advancing placeholder                                                                                       progression

  `G04` Confirmation        `STATE_IDENTITY_GAP`                          HIGH Stable session identity across     Confirmation
  session ID unstable                                                          cycles and restart.                correctness

  `G05` Dynamic Scope       `STATE_PERSISTENCE_GAP`                       HIGH Persist and reload                 Scope continuity,
  reinitialized                                                                `RuntimeScopeState`.               Entry/Exit

  `G06` Decision restart    `RESTART_GAP`                                 HIGH Recover C1/C2/Scope/required       Full runtime
  incomplete                                                                   MV2-DP state.                      activation

  `G07` Bridge parameters   `CONFIG_DRIFT`                              MEDIUM Move to canonical typed config     Reproducibility
  hardcoded                                                                    without changing values.           

  `G08` Exit-policy         `WIRING_GAP`                           MEDIUM/HIGH Bind real                          Lifecycle proof
  producers stubbed false                                                      adverse/profit/time/invalidation   
                                                                               producers.                         

  `G09` Zero                `EVIDENCE_GAP`                                HIGH Governed simulated actionability   Activation
  Entry/Exit/Fee/Slippage                                                      and full lifecycle evidence.       
  evidence                                                                                                        

  `G10` Exit claim          `EVIDENCE_CLAIM_DEFECT`                     MEDIUM Split reachability, independence   Trustworthy evidence
  overstates evidence                                                          and observed fill claims.          

  `G11` Runtime not         `ACTIVATION_GAP`                            MEDIUM Separate activation after state    Target runtime
  activated                                                                    and evidence closure.              

  `G12` Numeric max-age     `INTENTIONAL_CURRENT_PHASE`                    LOW Keep watchdog unless later         Does not block finish
  non-enforcing                                                                ratified.                          

  `G13` Multi-future        `INTENTIONAL_SAFETY_BARRIER`               LOW now Future program only.               Multi-future only
  unauthorized                                                                                                    

  `G14` Strategy registry   `DEFERRED_REQUIRED_CAPABILITY`              MEDIUM Tiered registry closure after      Strategy breadth
  non-authoritative                                                            single-future activation.          

  `G15` Evidence SHAs lag   `EVIDENCE_FRESHNESS_GAP`                LOW/MEDIUM Re-seal only when relevant         Current proof claims
  current HEAD                                                                 code/config changes.               

  `G16` Funding proof       `INSUFFICIENT_EVIDENCE`                        LOW Dedicated accounting evidence if   Funding claims only
  incomplete                                                                   funding enters scope.              
  -------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 11. Mandatory Capability Closure Standard

Every capability specification must include:

``` text
CAPABILITY_ID
TITLE
OWNER_REQUIREMENT
FORENSIC_BASELINE_SHA
EXPECTED_ORIGIN_MAIN_SHA
CURRENT_STATE
TARGET_STATE
IN_SCOPE
OUT_OF_SCOPE
DEPENDENCIES
AUTHORITY_OWNER
PRODUCTIVE_ENTRYPOINT
CALL_GRAPH_BEFORE
CALL_GRAPH_AFTER
STATE_OWNERS
CONFIG_KEYS
CONFIG_CONSUMERS
PERSISTENCE_MODEL
ATOMICITY_MODEL
RESTART_SEMANTICS
FAILURE_SEMANTICS
SAFETY_INVARIANTS
CORE_LOGIC_CHANGE
TEST_PLAN
FAILURE_INJECTION_PLAN
EVIDENCE_PLAN
CLAIM_SEMANTICS
ACTIVATION_STATE
ROLLBACK_PLAN
DOCS_UPDATE
NOTION_UPDATE
```

Mandatory closure matrix:

``` text
CODE_EXISTS
CONFIG_EXISTS
CONFIG_CONSUMED
PRODUCTIVE_CALLER_EXISTS
RUNTIME_REACHABLE
AUTHORITY_UNAMBIGUOUS
STATE_OWNER_UNAMBIGUOUS
PERSISTENCE_PROVEN
ATOMICITY_PROVEN
RESTART_PROVEN
FAILURE_SAFE
INTEGRATION_TESTED
NEGATIVE_TESTED
FAILURE_INJECTION_TESTED
DETERMINISTIC_REPLAY_PROVEN
EVIDENCE_PRODUCED
EVIDENCE_VERIFIED
CLAIMS_MATCH_EVIDENCE
DOCS_ACCURATE
ACTIVATION_EXPLICIT
LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED
```

Fields may be `N&#47;A` only with an explicit reason.

------------------------------------------------------------------------

# 12. Canonical Finish Sequence

The sequence below is dependency-binding. A later capability may not
bypass an unresolved earlier gate.

------------------------------------------------------------------------

# PHASE 6.1 --- Stateful Confirmation and C1 Productive Binding

## Capability ID

``` text
CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1
```

## Goal

Bind the existing C1/C2/C3 confirmation model into the productive
single-future host without changing confirmation thresholds, Master V2,
Double Play, Bull/Bear, Risk or Safety logic.

## Required target graph

``` text
Public Market Observation
→ Observation Identity
→ DistinctMarketObservationAcceptor
→ ObservationAcceptanceResult
→ Observation Epoch
→ Directional Confirmation Progress
→ C3 Directional Assessment Integration
→ Candidate / Confirmed state
→ canonical confirmation state commit
```

## Persistence derivation

Before implementation, produce a domain-to-persistence matrix:

  ---------------------------------------------------------------------------------
  Domain     Canonical         Persist             Rebuild     Ephemeral Reason
  field      owner            directly   deterministically               
  ---------- ----------- ------------- ------------------- ------------- ----------

  ---------------------------------------------------------------------------------

Persist only the actual canonical fields required to restore:

-   C1 observation identity and epoch state;
-   C2 directional confirmation progression;
-   stable instrument and confirmation-session identity;
-   C3 phase, validity and expiry semantics;
-   repository and config bindings.

No parallel persistence DTO may silently become a second decision
authority.

## Invariants

``` text
C1_PRODUCTIVELY_BOUND=true
C2_PRODUCTIVELY_BOUND=true
C3_PRODUCTIVELY_BOUND=true
DUPLICATE_DOES_NOT_ADVANCE=true
NO_SAMPLE_DOES_NOT_ADVANCE=true
DECISION_CYCLE_DOES_NOT_ADVANCE_CONFIRMATION=true
CONFIRMATION_SESSION_ID_STABLE=true
CONFIRMATION_STATE_PERSISTED=true
INSTRUMENT_ISOLATION=true
SILENT_CONFIRMATION_REINITIALIZATION=false
CORE_LOGIC_CHANGE=false
```

## Required tests

-   first accepted observation;
-   duplicate observation;
-   no-sample cycle;
-   out-of-order event;
-   direction change;
-   observe → candidate;
-   candidate → confirmed;
-   invalidation/expiry;
-   restart after each confirmation phase;
-   conflicting writer;
-   corrupt checkpoint;
-   deterministic replay digest match.

## Evidence

Must prove actual productive progression on governed fixtures and the
canonical host path, not only direct module tests.

## Activation

``` text
RUNTIME_ACTIVATED=false
LIVE_TESTNET_ORDERS=false
```

------------------------------------------------------------------------

# PHASE 6.2 --- Dynamic Scope Persistence Binding

## Capability ID

``` text
CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1
```

## Goal

Carry the existing canonical `RuntimeScopeState` continuously through
productive cycles and restart without changing Dynamic Scope rules or
numeric values.

## Required target graph

``` text
Confirmed Directional State
→ Previous Canonical RuntimeScopeState
→ Dynamic Scope Transition
→ New Canonical RuntimeScopeState
→ state commit
→ next cycle / restart reload
```

## Persistence derivation

The persistence schema must be derived from the actual
`RuntimeScopeState` and related canonical domain contracts.

Required semantic restoration scope:

-   instrument isolation;
-   directional context;
-   canonical scope boundaries and anchors;
-   event-time ownership;
-   confirmation linkage where required by the domain model;
-   position context where required;
-   state version and config digest.

## Required fixes

-   eliminate productive `existing_scope=None` reinitialization except
    for a semantically valid first-scope or reset transition;
-   reload prior scope by canonical instrument/session context;
-   bind event time correctly;
-   preserve Dynamic Scope behavior and continuity tests;
-   do not change scope distances or transition logic.

## Invariants

``` text
DYNAMIC_SCOPE_PRODUCTIVELY_BOUND=true
DYNAMIC_SCOPE_STATE_PERSISTED=true
DYNAMIC_SCOPE_RESTART_PROVEN=true
SCOPE_REINITIALIZATION_ONLY_WHEN_SEMANTICALLY_VALID=true
SILENT_DYNAMIC_SCOPE_REINITIALIZATION=false
CORE_LOGIC_CHANGE=false
```

## Required tests

-   initial scope creation;
-   continuation over distinct observations;
-   duplicate observation no-op;
-   adverse transition;
-   reversal transition;
-   position open;
-   flat state;
-   restart at each transition;
-   corrupt/missing scope state;
-   deterministic replay match.

------------------------------------------------------------------------

# PHASE 6.3 --- Decision Config Ownership and Consumer Closure

## Capability ID

``` text
CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1
```

## Goal

Remove confirmed bridge config drift and classify other locally owned
values without changing any trading or execution-model numeric value.

## Mandatory classification

For each candidate value, record:

``` text
CURRENT_OWNER
TARGET_OWNER
VALUE_CLASSIFICATION
PRODUCTIVE_CONSUMER
EFFECTIVE_VALUE
FALLBACK_BEHAVIOR
CONFIG_DIGEST_BINDING
CORE_LOGIC_EFFECT
```

## Confirmed migration scope

``` text
confirmation_epochs
up_distance
adverse_exit_distance
reversal_distance
```

## Review-only scope unless repository evidence requires migration

``` text
PRICE_PATH_MAX_LEN
fee_rate_bps
slippage_bps
```

## Invariants

``` text
CONFIG_RUNTIME_DRIFT=false_for_in_scope_runtime_values
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
NO_SILENT_FALLBACK=true
CONFIG_CONSUMER_TRACE_COMPLETE=true
CORE_LOGIC_CHANGE=false
```

------------------------------------------------------------------------

# PHASE 6.4 --- Full Decision-Path Restart and Atomic Checkpoint Closure

## Capability ID

``` text
CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1
```

## Goal

Prove that the complete required decision state survives crash and
restart without semantic drift or duplicated economic effects.

## Included state

At minimum:

``` text
C1 observation state
C2 confirmation carrier
C3 integration state
Dynamic Scope state
required Master V2 / Double Play carrier state
feature rebuild inputs
selection state reference
portfolio/accounting state
reconciliation state
volatility state reference
runtime commit position
pending evidence cursor / journal position
```

## Required decisions

For each field classify:

``` text
PERSIST_DIRECTLY
REBUILD_DETERMINISTICALLY
EPHEMERAL_ONLY
```

## Atomicity contract

The capability must implement and prove a transaction boundary that
prevents partial semantic commits.

Required failure points:

-   crash before state write;
-   crash during state write;
-   crash after state write before commit marker;
-   crash after runtime commit before evidence materialization;
-   crash after simulated fill before portfolio persistence;
-   crash after portfolio persistence before verifier/evidence cursor;
-   duplicate replay after restart.

## Invariants

``` text
DECISION_PATH_RESTART_PROVEN=true
NO_DUPLICATE_CONFIRMATION_ADVANCE=true
NO_DUPLICATE_FILL=true
NO_LOST_SCOPE_TRANSITION=true
NO_PORTFOLIO_STATE_ROLLBACK=true
RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART=true
DIGEST_MATCH_AFTER_RESTART=true
EVIDENCE_RECOVERY_IDEMPOTENT=true
CORE_LOGIC_CHANGE=false
```

------------------------------------------------------------------------

# PHASE 6.5 --- Exit Policy Producer Binding

## Capability ID

``` text
CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1
```

## Goal

Replace unbound false placeholders with actual canonical Exit-policy
evaluation while preserving the existing precedence and core logic.

## Mandatory pre-implementation authority matrix

  -------------------------------------------------------------------------------------
  Exit class     Existing    Current    State      Event-time   Persisted   Canonical
                 producer    caller     owner      dependency   state       authority
  -------------- ----------- ---------- ---------- ------------ ----------- -----------
  Adverse        required    required   required   required     required    required

  Profit         required    required   required   required     required    required

  Time           required    required   required   required     required    required

  Invalidation   required    required   required   required     required    required

  Reversal       where       required   required   required     required    required
                 canonical                                                  

  Hard-risk      required    required   required   required     required    required
  reduce                                                                    

  Safety exit    required    required   required   required     required    required
  -------------------------------------------------------------------------------------

`PolicySignalV0(triggered=False)` may remain only where it represents a
real evaluated false condition.

## Precedence rule

The implementation must first prove the actual canonical precedence in
code. The runbook does not authorize inventing or reordering precedence.

Expected audit reference:

``` text
Safety Exit
→ Hard-Risk Reduce
→ Reconciliation Action
→ Mandatory Adverse / Profit / Time / Invalidation Exit
→ Reduce / Hold
→ Alpha Entry
```

## Invariants

``` text
EXIT_POLICY_PRODUCERS_BOUND=true
PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB=false
POSITION_FLIP_ALLOWED=false
CORE_LOGIC_CHANGE=false
```

------------------------------------------------------------------------

# PHASE 7.1 --- Simulated Entry, Reduce and Exit Actionability Evidence

## Capability ID

``` text
CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1
```

## Goal

Produce end-to-end deterministic evidence that the canonical stateful
runtime can complete full simulated trade lifecycles.

## Deterministic governed evidence sessions

These sessions must prove actionability:

1.  deterministic long lifecycle;
2.  deterministic short lifecycle;
3.  partial reduce lifecycle;
4.  restart while flat;
5.  restart after Entry before Exit;
6.  restart during confirmation;
7.  restart during active Dynamic Scope;
8.  adverse exit;
9.  profit exit;
10. time or invalidation exit where canonical;
11. duplicate event and replay protection;
12. corrupt checkpoint fail-closed.

## Public-MD continuity session

A separate public-MD no-order session must prove:

-   state continuity;
-   stable confirmation identity;
-   no duplicate confirmation advance;
-   no duplicate fills;
-   restart/recovery behavior;
-   pacing, rate-limit and stale-data safety;
-   repository/config/evidence binding.

A public-MD session is not required to naturally produce a trade and
must not cause threshold or core-logic changes merely to force
actionability.

## Mandatory evidence metrics

``` text
cycles
distinct_observation_count
duplicate_observation_count
confirmation_phase_transitions
candidate_count
confirmed_count
scope_transition_count
entry_intent_count
entry_fill_count
reduce_intent_count
reduce_fill_count
exit_intent_count
exit_fill_count
total_fees
total_slippage
realized_pnl
unrealized_pnl
restart_count
recovery_count
reconciliation_results
risk_veto_count
safety_veto_count
verifier_result
```

## Closure criteria

``` text
ENTRY_END_TO_END_EVIDENCE_PROVEN=true
EXIT_END_TO_END_EVIDENCE_PROVEN=true
NONZERO_FEE_EVIDENCE_PROVEN=true
NONZERO_SLIPPAGE_EVIDENCE_PROVEN=true
ACCOUNTING_RECONSTRUCTION_MATCH=true
RESTART_DURING_OPEN_POSITION_PROVEN=true
EVIDENCE_CLAIMS_MATCH_TELEMETRY=true
LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED=true
```

------------------------------------------------------------------------

# PHASE 7.2 --- Single-Future Canonical Stateful Runtime Activation

## Capability ID

``` text
CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1
```

## Goal

Activate the fully stateful single-future runtime with public market
data and internal simulated execution only.

## Preconditions

``` text
C1_PRODUCTIVELY_BOUND=true
C2_PRODUCTIVELY_BOUND=true
C3_PRODUCTIVELY_BOUND=true
CONFIRMATION_STATE_PERSISTED=true
CONFIRMATION_SESSION_ID_STABLE=true
DYNAMIC_SCOPE_STATE_PERSISTED=true
DECISION_PATH_RESTART_PROVEN=true
EXIT_POLICY_PRODUCERS_BOUND=true
ENTRY_END_TO_END_EVIDENCE_PROVEN=true
EXIT_END_TO_END_EVIDENCE_PROVEN=true
NONZERO_FEE_EVIDENCE_PROVEN=true
NONZERO_SLIPPAGE_EVIDENCE_PROVEN=true
RECONCILIATION_BEFORE_ALPHA=true
CONFIG_TRUTH_ALIGNED=true
EVIDENCE_VERIFIER_PASS=true
LEGACY_PARALLEL_AUTHORITY_ABSENT=true
REAL_EXECUTION_ADAPTER_CONSTRUCTED=false
EXCHANGE_ORDER_SUBMIT_REACHABLE=false
EXCHANGE_CREDENTIAL_ACCESS_REACHABLE=false
PUBLIC_MD_PRIVATE_ENDPOINT_REACHABLE=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

## Network boundary

``` text
NETWORK_ALLOWLIST=PUBLIC_MARKET_DATA_ENDPOINTS_ONLY
HTTP_METHOD_ALLOWLIST=GET_ONLY
PRIVATE_ENDPOINT_REACHABLE=false
AUTH_HEADER_PRESENT=false
```

## Execution-port boundary

The no-order host must not be able to switch polymorphically to real
venue execution.

Required architectural proof:

``` text
SIMULATED_EXECUTION_PORT_SEPARATE_FROM_REAL_EXECUTION_PORT=true
NO_REAL_SUBMIT_ORDER_INTERFACE_IN_NO_ORDER_HOST=true
```

## Status transition

Only this capability may change:

``` text
STATEFUL_RUNTIME_READY_FOR_ACTIVATION=true
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
```

It must preserve:

``` text
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
```

## Rollback

Rollback must be immediate, deterministic and preserve evidence/state
for forensic review.

A failed activation must result in:

``` text
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=false
ALPHA_BLOCKED=true
EXIT_RISK_SAFETY_STATE_PRESERVED=true
```

------------------------------------------------------------------------

# PHASE 8 --- Multi-Future Policy and Runtime Program

Multi-future remains outside the single-future finish critical path.

## 8.1 Policy first

Before implementation, ratify:

-   active-set size and Top-N semantics;
-   promotion/demotion thresholds;
-   hysteresis and cooldown;
-   treatment of open positions;
-   global and per-instrument risk budgets;
-   correlation and concentration limits;
-   state isolation;
-   deterministic intent arbitration;
-   single global execution/accounting writer;
-   restart and reconciliation per instrument.

## 8.2 Runtime implementation

Required architecture:

``` text
Global Universe
→ Global Ranking
→ Active-Set Policy
→ Per-Instrument Stateful Runtime Context
→ Global Portfolio Risk
→ Global Safety
→ Intent Arbitration
→ Simulated Execution
→ Reconciliation
```

End state before separate activation:

``` text
MULTI_FUTURE_RUNTIME_IMPLEMENTED=true
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
```

------------------------------------------------------------------------

# PHASE 9.1 --- Strategy Registry Closure

## Goal

Convert strategy sprawl into a tiered, enforceable registry without
bypassing Master V2 / Double Play.

## Required tiers

``` text
CANONICAL_AUTHORITY
AUTHORIZED_COMPOSITION_INPUT
RESEARCH_INFORMATION
EXPERIMENT_ONLY
LEGACY_DEAUTHORIZED
```

## Required closure

-   every strategy classified;
-   productive callers enumerated;
-   direct-order capability absent;
-   suitability/composition contract explicit;
-   disabled strategies fail closed;
-   config/version mismatch rejected;
-   restart deterministic;
-   no silent authority promotion.

This phase is not allowed to alter core trading logic without separate
Owner ratification.

------------------------------------------------------------------------

# PHASE 9.2 --- Long-Running Stateful Public-MD Simulation Evidence

## Goal

Prove runtime continuity over natural market phases after activation,
using public market data and internal simulated execution only.

## Session ladder

1.  short smoke session;
2.  one-hour governed session;
3.  restart/recovery session;
4.  rate-limit and reconnect session;
5.  prolonged natural-market session;
6.  adverse/stale-data session;
7.  repeated multi-session continuity campaign.

## Operational requirements

-   no zero-interval request bursts;
-   explicit pacing budget;
-   bounded retry and backoff;
-   rate-limit classification;
-   heartbeat and staleness monitoring;
-   stable session/state identity;
-   no duplicate confirmation advance;
-   no duplicate fills;
-   evidence manifest per session;
-   exact repository/config binding.

## Evaluation metrics

-   actionability distribution;
-   HOLD/ENTRY/REDUCE/EXIT distribution;
-   false-HOLD diagnostics;
-   risk/safety veto reasons;
-   drawdown;
-   profit factor;
-   Sharpe only with sufficient samples;
-   turnover;
-   Fee/Slippage impact;
-   restart/recovery success;
-   state divergence;
-   verifier outcomes.

No performance result from these sessions constitutes financial advice
or Live authorization.

------------------------------------------------------------------------

# PHASE 10 --- Numeric Volatility Max-Age Decision Program

Numeric max-age remains optional and non-enforcing until evidence
justifies a separate decision.

Required research before enforcement discussion:

-   age histograms;
-   regime strata;
-   volatility strata;
-   actionability strata;
-   data-quality strata;
-   false-positive block analysis;
-   false-negative stale acceptance analysis;
-   threshold sensitivity;
-   walk-forward analysis;
-   Monte Carlo/resampling;
-   stress scenarios;
-   session-to-session stability.

No enforcement may be activated without an explicit capability defining:

``` text
threshold
reference_time
clock_source
missing_behavior
stale_behavior
alpha_behavior
exit_behavior
risk_behavior
safety_behavior
grace_period
recovery_semantics
evidence
rollback
```

------------------------------------------------------------------------

# PHASE 11 --- Canonical Testnet-to-Live Full-Autonomy Program

## 11.0 Purpose, authority and non-authorization boundary

This phase defines the mandatory target architecture and closure sequence
for evolving the proven canonical stateful runtime into a fully autonomous
exchange-trading system. It is designed as the direct semantic successor
of Phases 6.x--10 and must consume the exact same decision, state, risk,
safety, accounting, persistence, reconciliation and evidence contracts.

This phase is architectural and operational semantic authority only. It
does not itself authorize Testnet, Live orders, credential use or real
capital movement. Every activation transition requires an explicit
Owner-ratified capability, valid authorization scope and a separately
issued activation contract.

Mandatory separation:

``` text
AUTONOMY_ARCHITECTURE_DEFINED=true
TESTNET_AUTHORIZED=false
LIVE_AUTHORIZED=false
EXCHANGE_CREDENTIAL_USE_AUTHORIZED=false
REAL_CAPITAL_MOVEMENT_AUTHORIZED=false
OWNER_GO_REQUIRED_FOR_EACH_ACTIVATION=true
```

Nothing in Phases 6.x--10 or in this Phase 11 definition may implicitly
make a real execution path reachable.

## 11.1 Full-autonomy target definition

Peak_Trade is fully autonomous only when the complete productive loop can
operate without routine human intervention while remaining bounded by
pre-ratified policy, risk and safety contracts.

The canonical autonomous loop is:

``` text
Startup / Restart
→ Repository and config integrity verification
→ Authorization and mode verification
→ Credential availability and scope verification
→ Venue connectivity and clock synchronization
→ Universe / selection / instrument binding
→ Exchange-state reconciliation
→ Public and private market/account state ingestion
→ Distinct observation acceptance
→ Features / market state / confirmation
→ Master V2 / Double Play / Dynamic Scope
→ Survival / Suitability / Composition
→ Portfolio Risk / Venue Risk / Safety
→ Canonical Intent
→ Order Plan
→ Pre-submit validation
→ Idempotent exchange submission
→ Acknowledgement / rejection handling
→ Partial-fill / fill / cancel / replace lifecycle
→ Futures accounting
→ Portfolio and order-state persistence
→ Exchange reconciliation
→ Evidence and audit materialization
→ Health evaluation
→ Continue, degrade, exit-only, cancel-all or halt
```

Full autonomy does not mean unconstrained operation. It means:

``` text
NO_ROUTINE_MANUAL_DECISION_REQUIRED=true
NO_ROUTINE_MANUAL_ORDER_ENTRY_REQUIRED=true
NO_ROUTINE_MANUAL_RESTART_REQUIRED=true
NO_ROUTINE_MANUAL_RECONCILIATION_REQUIRED=true
AUTONOMOUS_RECOVERY_WITHIN_RATIFIED_BOUNDS=true
AUTONOMOUS_DEGRADATION_WITHIN_RATIFIED_BOUNDS=true
AUTONOMOUS_HALT_ON_UNRESOLVED_UNCERTAINTY=true
OWNER_AUTHORITY_RETAINED=true
```

## 11.2 Symbiotic architecture contract

The Live program must extend, not replace, the canonical no-order system.
There must be one decision authority chain and one semantic state machine
from observation through economic settlement.

Required architecture:

``` text
Canonical Stateful Trading Core
→ Canonical Intent Contract
→ Mode-Specific Execution Boundary
   ├─ SimulatedExecutionPort
   ├─ TestnetExecutionPort
   └─ LiveExecutionPort
→ Canonical Execution Event Contract
→ Canonical Futures Accounting
→ Canonical Portfolio / Risk State
→ Canonical Reconciliation
→ Canonical Evidence
```

Mandatory rules:

``` text
ONE_DECISION_AUTHORITY_CHAIN=true
ONE_CANONICAL_INTENT_SCHEMA=true
ONE_CANONICAL_EXECUTION_EVENT_SCHEMA=true
ONE_ACCOUNTING_AUTHORITY=true
ONE_PORTFOLIO_AUTHORITY=true
ONE_RECONCILIATION_AUTHORITY=true
MODE_SPECIFIC_EXECUTION_SIDE_EFFECTS_ONLY=true
NO_LIVE_ONLY_ALPHA_LOGIC=true
NO_TESTNET_ONLY_ALPHA_LOGIC=true
NO_EXECUTION_ADAPTER_DECISION_AUTHORITY=true
CORE_LOGIC_CHANGE=false
```

The execution adapter may translate canonical intent into venue-native
requests, but it may not alter direction, desired economic exposure,
strategy reason, risk result or safety result.

## 11.3 Autonomy state model

The autonomous runtime must maintain durable state for at least:

``` text
Runtime mode and activation epoch
Authorization ID, scope and expiry
Credential reference metadata, never plaintext
Venue session and connectivity state
Exchange clock offset and synchronization state
Canonical intent IDs and decision digests
Order plan IDs
Client order IDs and venue order IDs
Order lifecycle state
Pending submit / cancel / amend commands
Acknowledgements, rejections, partial fills and fills
Open positions and exchange-reported positions
Local accounting and exchange balances/margins
Risk reservations and exposure locks
Reconciliation checkpoints
Kill-switch state
Degradation state
Recovery attempt state
Evidence cursor and audit chain
```

Each field must be classified as:

``` text
DURABLE_CONTROL_STATE
DURABLE_EXECUTION_STATE
DURABLE_ECONOMIC_STATE
DERIVED_REBUILDABLE_STATE
EPHEMERAL_CONNECTION_STATE
EVIDENCE_ONLY_STATE
FORBIDDEN_TO_PERSIST
```

Plaintext credentials, confirm tokens and secret material are always:

``` text
FORBIDDEN_TO_PERSIST=true
FORBIDDEN_IN_LOGS=true
FORBIDDEN_IN_PROCESS_ARGUMENTS=true
FORBIDDEN_IN_EVIDENCE=true
```

## 11.4 Canonical order lifecycle

Every Live or Testnet order must follow one deterministic lifecycle:

``` text
INTENT_CREATED
→ ORDER_PLAN_CREATED
→ RISK_RESERVED
→ PRE_SUBMIT_VALIDATED
→ SUBMIT_PENDING
→ SUBMIT_ATTEMPTED
→ ACKNOWLEDGED | REJECTED | UNKNOWN
→ OPEN | PARTIALLY_FILLED | FILLED | CANCEL_PENDING | AMEND_PENDING
→ CANCELLED | EXPIRED | FILLED | TERMINAL_REJECTED
→ ACCOUNTED
→ RECONCILED
→ EVIDENCED
```

Mandatory invariants:

``` text
CLIENT_ORDER_ID_DETERMINISTIC_AND_UNIQUE=true
SUBMISSION_IDEMPOTENT=true
UNKNOWN_SUBMIT_RESULT_NEVER_BLINDLY_RETRIED=true
EXCHANGE_QUERY_BEFORE_RETRY=true
NO_DUPLICATE_ORDER=true
NO_DUPLICATE_FILL_APPLICATION=true
PARTIAL_FILL_ACCOUNTING_INCREMENTAL=true
CANCEL_REPLACE_STATEFUL=true
TERMINAL_STATE_IMMUTABLE=true
ORDER_AND_PORTFOLIO_STATE_ATOMIC_OR_JOURNALED=true
```

A timeout after submission is an `UNKNOWN` economic state, not a failed
order. The runtime must reconcile by deterministic identifiers before any
new submission is permitted.

## 11.5 Autonomous reconciliation hierarchy

Reconciliation is the first operational authority after startup and the
continuous authority during operation.

Required reconciliation layers:

1. credential and account identity;
2. venue instrument and contract metadata;
3. open orders;
4. recent orders and trades;
5. positions;
6. balances, equity and available margin;
7. local portfolio and accounting;
8. risk reservations;
9. pending commands;
10. evidence and commit cursors.

Required outcomes:

``` text
MATCH
SAFE_REBUILD
SAFE_ADOPT_EXCHANGE_TRUTH
CANCEL_UNKNOWN_ORDERS
EXIT_ONLY
REDUCE_ONLY
CANCEL_ALL_AND_HALT
HARD_STOP_OWNER_REVIEW
```

Exchange truth may be adopted only under an explicit canonical policy.
It must never silently overwrite local decision history or evidence.

Mandatory invariant:

``` text
RECONCILIATION_BEFORE_ALPHA=true
RECONCILIATION_CONTINUOUS=true
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY=true
POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE=true
```

## 11.6 Credential and authorization autonomy

Credentials must be loaded only by the dedicated execution host after
mode, authorization, repository SHA, config digest, account identity and
venue scope have all been validated.

Required credential contract:

``` text
LEAST_PRIVILEGE=true
WITHDRAWAL_PERMISSION=false
ACCOUNT_SCOPE_EXPLICIT=true
VENUE_SCOPE_EXPLICIT=true
INSTRUMENT_SCOPE_EXPLICIT=true
IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED=true
SECRET_REFERENCE_ONLY_IN_CONFIG=true
PLAINTEXT_SECRET_NEVER_PERSISTED=true
ROTATION_SUPPORTED=true
REVOCATION_DETECTED=true
CREDENTIAL_FAILURE_FAILS_CLOSED=true
```

Authorization must bind at least:

``` text
repository SHA
config digest
runtime mode
venue
account identity
instrument or active-set scope
maximum notional
maximum leverage
maximum position count
maximum session duration
loss and drawdown limits
allowed order types
allowed side effects
activation epoch
expiry
```

The runtime may autonomously renew ordinary venue sessions, reconnect and
recover within an existing valid authorization. It may not autonomously
extend authorization scope, increase capital limits, enable a new venue or
change from Testnet to Live.

## 11.7 Risk and safety hierarchy for autonomous Live operation

The existing canonical risk and safety authority remains binding. Live
operation adds venue- and execution-specific protections beneath it.

Required precedence:

``` text
Persistent Kill Switch
→ Emergency Cancel-All / Exit Policy
→ Venue / Account Integrity Gate
→ Hard Portfolio Risk
→ Reconciliation Action
→ Position Protection and Canonical Exit
→ Order-Lifecycle Safety
→ Alpha Entry / Increase
```

Required autonomous controls include:

- maximum gross and net notional;
- maximum leverage and margin utilization;
- per-instrument and global exposure limits;
- order-rate and cancel-rate limits;
- maximum open-order count;
- price-collar and mark/index deviation checks;
- maximum slippage and spread policy;
- stale market/private-data blocking;
- exchange clock-drift limit;
- daily and session loss limits;
- peak-to-trough drawdown limit;
- consecutive rejection and error limits;
- reconciliation divergence limits;
- connectivity and heartbeat limits;
- concentration and correlation limits for multi-future operation;
- persistent kill switch and emergency disable.

Mandatory safety rule:

``` text
ALPHA_MAY_DEGRADE_TO_BLOCKED=true
NEW_ENTRY_MAY_DEGRADE_TO_EXIT_ONLY=true
OPEN_POSITION_PROTECTION_MUST_NOT_DEPEND_ON_ALPHA_HEALTH=true
UNBOUNDED_AUTONOMOUS_RETRY=false
AUTONOMOUS_LIMIT_INCREASE=false
```

## 11.8 Degradation and autonomous recovery states

The runtime must use an explicit finite-state operating model:

``` text
OFF
PREFLIGHT
RECONCILING
READY
ACTIVE
DEGRADED_NO_NEW_ENTRY
EXIT_ONLY
REDUCE_ONLY
CANCEL_ALL
RECOVERING
HALTED
OWNER_LOCKED
```

Every transition must have a reason code, triggering evidence, authority
source and persisted timestamp.

Autonomous recovery is permitted only when:

``` text
ROOT_CAUSE_CLASSIFIED=true
RECOVERY_POLICY_PRE_RATIFIED=true
RETRY_BUDGET_AVAILABLE=true
AUTHORIZATION_STILL_VALID=true
NO_UNRESOLVED_ECONOMIC_AMBIGUITY=true
POST_RECOVERY_RECONCILIATION_PASS=true
```

Autonomous recovery is forbidden for:

- credential-scope mismatch;
- repository or config integrity mismatch;
- unknown account identity;
- unexplained position divergence;
- kill-switch activation;
- repeated duplicate-order evidence;
- risk-limit breach requiring limit change;
- evidence-chain corruption affecting economic truth;
- unauthorized mode or venue transition.

These conditions require `OWNER_LOCKED` or `HALTED`.

## 11.9 Persistent kill switch and emergency control plane

The kill switch must be independent of Alpha, durable across restart and
capable of preventing all new exposure.

Required properties:

``` text
KILL_SWITCH_PERSISTED=true
KILL_SWITCH_FAIL_CLOSED=true
KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT=true
KILL_SWITCH_SURVIVES_RESTART=true
KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME=true
OWNER_AUTHORITY_REQUIRED_TO_CLEAR=true
CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA=true
EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA=true
```

The emergency control plane must support authenticated, audited commands
for at least:

``` text
BLOCK_NEW_ENTRY
EXIT_ONLY
REDUCE_ONLY
CANCEL_ALL
HALT_AFTER_CANCEL
PERSISTENT_KILL
```

No emergency command may silently increase risk or re-enable trading.

## 11.10 Process, host and dependency resilience

Full autonomy requires that ordinary failures do not require manual
restart. The deployment architecture must therefore include a supervised
execution host with bounded restart and recovery behavior.

Required controls:

``` text
PROCESS_SUPERVISION=true
SINGLE_ACTIVE_EXECUTION_LEADER=true
SPLIT_BRAIN_PREVENTED=true
DURABLE_LEASE_OR_FENCING=true
CRASH_RESTART_SUPPORTED=true
HOST_REBOOT_RECOVERY_SUPPORTED=true
DEPENDENCY_HEALTH_CLASSIFIED=true
BOUNDED_RECONNECT=true
BOUNDED_BACKOFF=true
NO_ZERO_INTERVAL_RETRY=true
```

A standby instance may observe and prepare for takeover, but it may not
submit orders until authoritative fencing proves the previous writer can
no longer act.

## 11.11 Venue adapter contract

Each venue adapter must be a narrow anti-corruption layer. It owns:

- authentication transport;
- venue-native instrument translation;
- request signing;
- endpoint and rate-limit handling;
- native order serialization;
- venue-event normalization;
- exchange clock synchronization;
- idempotent lookup by canonical identifiers.

It does not own:

- Alpha;
- Master V2 or Double Play decisions;
- portfolio strategy;
- risk-limit policy;
- safety policy;
- accounting authority;
- autonomous limit changes.

Required proof:

``` text
VENUE_ADAPTER_DECISION_AUTHORITY=false
VENUE_NATIVE_EVENT_NORMALIZED=true
ROUNDING_AND_PRECISION_EXPLICIT=true
MIN_SIZE_AND_NOTIONAL_VALIDATED=true
ORDER_TYPE_SUPPORT_EXPLICIT=true
RATE_LIMIT_BUDGET_EXPLICIT=true
ERROR_TAXONOMY_EXPLICIT=true
```

## 11.12 Testnet progression program

Testnet is a mandatory execution-side-effect proving ground, but it must
not be treated as proof of Live economics or operational equivalence.

Mandatory Testnet sequence:

``` text
11.12.1 Read-only private API and account identity
→ 11.12.2 Order serialization dry-run
→ 11.12.3 Single controlled order lifecycle
→ 11.12.4 Entry / partial fill / cancel / exit lifecycles
→ 11.12.5 Unknown-submit and reconnect recovery
→ 11.12.6 Restart with open order and open position
→ 11.12.7 Kill-switch and emergency control proof
→ 11.12.8 Long-running autonomous Testnet campaign
```

Testnet closure requires:

``` text
TESTNET_ORDER_LIFECYCLE_PROVEN=true
TESTNET_RECONCILIATION_PROVEN=true
TESTNET_RESTART_PROVEN=true
TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN=true
TESTNET_KILL_SWITCH_PROVEN=true
TESTNET_AUTONOMOUS_RECOVERY_PROVEN=true
TESTNET_EVIDENCE_VERIFIED=true
```

## 11.13 Live shadow and canary progression

Live activation must progress through bounded stages without bypassing
the canonical core:

``` text
LIVE_PRIVATE_READ_ONLY
→ LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION
→ LIVE_DRY_RUN_ORDER_PLAN
→ LIVE_CANARY_MINIMUM_EXPOSURE
→ LIVE_BOUNDED_SINGLE_FUTURE
→ LIVE_BOUNDED_MULTI_SESSION
→ LIVE_AUTONOMOUS_SINGLE_FUTURE
→ future Owner-ratified multi-future autonomy
```

Each stage requires its own maximum exposure, duration, loss budget,
order count, rollback contract and evidence verifier.

Canary rules:

``` text
MINIMUM_RATIFIED_NOTIONAL_ONLY=true
POSITION_COUNT_LIMIT=1_unless_separately_ratified
NO_AUTOMATIC_STAGE_PROMOTION=true
OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION=true
AUTOMATIC_STAGE_DEMOTION_ALLOWED=true
AUTOMATIC_HALT_ALLOWED=true
```

## 11.14 Live order and economic evidence ladder

Live proof claims must use a stricter ladder:

``` text
LIVE_EXECUTION_CODE_EXISTS
→ LIVE_EXECUTION_PATH_REACHABLE
→ LIVE_PRIVATE_READ_ONLY_PROVEN
→ LIVE_ORDER_PLAN_OBSERVED
→ LIVE_SUBMIT_ACK_OBSERVED
→ LIVE_FILL_OBSERVED
→ LIVE_FEE_OBSERVED
→ LIVE_POSITION_RECONCILED
→ LIVE_ACCOUNTING_RECONSTRUCTED
→ LIVE_RESTART_RECONSTRUCTED
→ LIVE_AUTONOMOUS_RECOVERY_OBSERVED
→ LIVE_END_TO_END_EVIDENCE_PROVEN
```

No Testnet, fixture or simulated result may satisfy a Live evidence field.

Mandatory Live metrics include:

``` text
orders_planned
orders_submitted
orders_acknowledged
orders_rejected
orders_unknown
partial_fills
fills
cancels
amends
duplicate_submit_prevented
fees_paid
funding_paid_or_received
realized_pnl
unrealized_pnl
margin_utilization
reconciliation_divergences
autonomous_recoveries
degradation_transitions
kill_switch_events
owner_interventions
```

## 11.15 Full-autonomy observability and audit trail

The autonomous runtime must expose enough telemetry for oversight without
creating a second decision authority.

Required observability domains:

- market-data health;
- private account-stream health;
- clock synchronization;
- decision latency;
- order lifecycle latency;
- rejection and retry taxonomy;
- position and margin state;
- risk and safety vetoes;
- reconciliation status;
- persistence and journal status;
- evidence cursor health;
- authorization and credential status;
- operating-state transitions.

The dashboard remains read-only:

``` text
DASHBOARD_TRADING_AUTHORITY=false
DASHBOARD_MAY_REQUEST_OWNER_CONTROL_ACTION=true_only_via_authenticated_control_plane
DASHBOARD_DIRECT_ORDER_SUBMIT=false
```

All economically relevant events require an append-only audit chain bound
to repository SHA, config digest, runtime authorization, account identity,
canonical intent ID, order ID and persistence commit.

## 11.16 Autonomy failure-injection program

Before autonomous Live status, governed failure injection must prove at
least:

1. process crash before submit;
2. process crash after submit before acknowledgement persistence;
3. timeout with unknown submit result;
4. duplicate venue event;
5. out-of-order venue event;
6. partial fill followed by disconnect;
7. cancel acknowledgement loss;
8. restart with open order;
9. restart with open position;
10. stale public market data;
11. stale private account data;
12. rate limiting and bounded backoff;
13. clock drift;
14. credential revocation;
15. exchange maintenance;
16. local persistence write failure;
17. evidence materialization failure;
18. writer conflict / split-brain attempt;
19. kill-switch activation during open position;
20. reconciliation divergence.

Failure injection must never bypass risk, safety or venue restrictions and
must use Testnet, simulation or isolated fault harnesses unless an
explicit Live canary contract authorizes the exact scenario.

## 11.17 Autonomy closure standard

Peak_Trade may claim `FULLY_AUTONOMOUS_LIVE_TRADING_READY=true` only when:

``` text
CANONICAL_STATEFUL_CORE_PROVEN=true
SIMULATED_LIFECYCLE_PROVEN=true
TESTNET_LIFECYCLE_PROVEN=true
LIVE_PRIVATE_READ_ONLY_PROVEN=true
LIVE_ORDER_LIFECYCLE_PROVEN=true
LIVE_RECONCILIATION_PROVEN=true
LIVE_RESTART_PROVEN=true
LIVE_UNKNOWN_SUBMIT_RECOVERY_PROVEN=true
LIVE_DUPLICATE_ORDER_PREVENTION_PROVEN=true
LIVE_PARTIAL_FILL_RECOVERY_PROVEN=true
LIVE_KILL_SWITCH_PROVEN=true
LIVE_AUTONOMOUS_DEGRADATION_PROVEN=true
LIVE_AUTONOMOUS_RECOVERY_PROVEN=true
LIVE_ACCOUNTING_RECONSTRUCTION_PROVEN=true
LIVE_EVIDENCE_VERIFIED=true
OWNER_INTERVENTION_REQUIRED_FOR_ROUTINE_OPERATION=false
OWNER_INTERVENTION_REQUIRED_FOR_SCOPE_OR_LIMIT_CHANGE=true
CORE_LOGIC_PARITY_ACROSS_MODES=true
```

This readiness claim still does not activate Live. Activation requires a
separate state transition:

``` text
FULLY_AUTONOMOUS_LIVE_TRADING_READY=true
LIVE_AUTHORIZATION_VALID=true
OWNER_LIVE_GO=true
LIVE_ACTIVATION_CAPABILITY_PASS=true
→ FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE=true
```

## 11.18 Final autonomous Live operating contract

The final target state is:

``` text
FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE=true
CANONICAL_DECISION_CORE_ACTIVE=true
LIVE_EXECUTION_ACTIVE=true
AUTONOMOUS_RECONCILIATION_ACTIVE=true
AUTONOMOUS_RECOVERY_ACTIVE=true
PERSISTENT_KILL_SWITCH_ACTIVE=true
RISK_AND_SAFETY_ALWAYS_ENFORCED=true
OWNER_OVERSIGHT_AVAILABLE=true
OWNER_ROUTINE_INTERVENTION_REQUIRED=false
AUTONOMOUS_SCOPE_EXPANSION=false
AUTONOMOUS_RISK_LIMIT_INCREASE=false
AUTONOMOUS_VENUE_ENABLEMENT=false
AUTONOMOUS_CREDENTIAL_SCOPE_CHANGE=false
```

The system may autonomously trade, manage orders, reconcile, restart,
recover and degrade only within the exact ratified scope. Any requested
change to venue, capital, leverage, instruments, active-set size, strategy
authority or risk limits remains an Owner-controlled governance event.

## 11.19 Mandatory capability sequence for full autonomy

The Phase 11 implementation sequence is dependency-binding:

``` text
11.1 = Execution-domain and order-lifecycle contracts
11.2 = Credential, authorization and account-identity boundary
11.3 = Private read-only venue integration and reconciliation
11.4 = Testnet execution adapter and lifecycle closure
11.5 = Testnet restart, recovery and kill-switch closure
11.6 = Long-running autonomous Testnet evidence
11.7 = Live private read-only and shadow reconciliation
11.8 = Live dry-run order-plan parity
11.9 = Live canary execution
11.10 = Live bounded single-future continuity
11.11 = Live autonomous recovery and degradation evidence
11.12 = Fully autonomous Live readiness ratification
11.13 = Separate Owner-authorized Live activation
```

Each capability must consume the predecessor's canonical state and
evidence directly. No stage may create a parallel decision core, separate
accounting model, hidden execution policy or mode-specific Alpha logic.

------------------------------------------------------------------------

# 13. Failure Semantics

The runtime must classify failures explicitly.

  -----------------------------------------------------------------------
  Failure class                       Required behavior
  ----------------------------------- -----------------------------------
  Missing market truth                Alpha blocked; protection paths
                                      preserved.

  Duplicate observation               No confirmation or scope advance.

  Out-of-order observation            Reject or quarantine; no silent
                                      reorder unless contract explicitly
                                      allows it.

  Missing confirmation state          Hard stop or safe state recovery;
                                      no reset-to-zero continuation.

  Missing durable decision state      Hard stop or governed recovery;
  after prior commit                  silent reinitialization forbidden.

  Corrupt scope state                 Alpha blocked; existing position
                                      protection preserved.

  Config digest mismatch              Hard stop before Alpha.

  Repository SHA mismatch             Authorization/evidence invalid
                                      until reissued.

  Writer conflict                     Hard stop.

  Partial checkpoint                  Recover from journal/last committed
                                      version; no mixed state.

  Reconciliation mismatch             Exit-only, reduce-only or hard stop
                                      according to canonical contract.

  Evidence verifier failure           Capability/session fails; no
                                      activation progression.

  Rate limit / HTTP 429               Bounded backoff; no zero-interval
                                      retry burst.

  Network loss                        Bounded reconnect; stale-data gate;
                                      no fabricated observations.

  Real execution adapter reachable    Hard stop and security defect.

  Credential access detected          Hard stop and security defect.

  Evidence materialization failure    Preserve runtime commit; persist
  after valid runtime commit          pending-evidence recovery cursor;
                                      no duplicate economics.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 14. Confirm-Token and Authorization Handling

The Owner must not be required to invent or manually expose confirm
tokens.

Cursor must:

1.  find and use the repository-canonical mint/issuance path;
2.  only generate a cryptographically secure token in memory if the
    canonical contract permits it;
3.  enter it only through hidden prompt/stdin;
4.  never print, log, persist or commit plaintext;
5.  never place plaintext in shell history, process arguments or
    evidence;
6.  expose only digest, token ID, scope, bindings and status;
7.  request manual entry only when repository-enforced design makes
    secure automation technically impossible;
8.  report that condition with code/contract evidence as `HARD_STOP`.

Required output:

``` text
CONFIRM_TOKEN_CANONICAL_PATH_USED=true
CONFIRM_TOKEN_PLAINTEXT_EXPOSED=false
CONFIRM_TOKEN_PERSISTED=false
CONFIRM_TOKEN_SHELL_HISTORY=false
AUTHORIZATION_SCOPE_MATCH=true
AUTHORIZATION_SHA_MATCH=true
```

------------------------------------------------------------------------

# 15. Local Git and Cursor Execution Standard

All Git operations must use the real local repository and local
terminal.

Forbidden:

``` text
Cursor Sandbox Git
emulated Git without .git access
ignoring worktree/index/lock errors
```

Every Cursor assignment must begin with:

``` text
Arbeite ausschließlich im echten lokalen Repository über das lokale Terminal.
Verwende keine Cursor-Sandbox für Git-Operationen.
Prüfe Repository Root, .git, Branch, HEAD, origin/main und Worktree vor jeder Mutation.
Stoppe fail-closed bei jeder Abweichung.
Erhalte alle untracked Evidence-Verzeichnisse unverändert.
```

Standard preflight:

``` bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
git status --short
git branch --show-current
git rev-parse HEAD
git fetch origin --prune
git rev-parse origin/main
git diff --stat origin/main...HEAD
```

Expected:

``` text
BRANCH=main
HEAD=origin/main
TRACKED_WORKTREE_CLEAN=true
UNTRACKED_EVIDENCE_PRESERVED=true
```

Any deviation not explicitly authorized is a hard stop.

------------------------------------------------------------------------



### 15.1 Operational Execution Clarification (Binding)

The following operational rules are mandatory and override any ambiguous
execution behavior.

#### Sandbox policy

The known Cursor Sandbox Git environment and any local sandbox
environment that cannot provide direct access to the real repository are
considered non-authoritative execution environments.

Mandatory rules:

```text
SANDBOX_GIT_EXECUTION_ALLOWED=false
SANDBOX_FALLBACK_ALLOWED=false
REAL_LOCAL_TERMINAL_REQUIRED=true
REAL_LOCAL_REPOSITORY_REQUIRED=true
REAL_DOT_GIT_REQUIRED=true
```

If a sandbox reports missing `.git`, permission errors, virtualized Git
state or equivalent sandbox limitations, Cursor shall immediately switch
to the real local terminal workflow rather than repeatedly attempting
sandbox execution.

Such sandbox failures alone are not considered repository failures.

#### Cursor workflow continuity

After every Cursor result, exactly one of the following must happen:

1. HARD_STOP with explicit technical justification; or
2. the next complete executable Cursor command.

Summaries without a next executable command are forbidden unless a true
HARD_STOP exists.

#### Merge workflow

If a PR has already been reviewed, CI has passed, the expected HEAD SHA
matches, no new commits are present and the PR is mergeable, the next
Cursor command shall be the appropriate Owner merge command.

Repeated full review, repeated read-only inspection or repeated diff
inspection are forbidden unless new evidence, a changed SHA or a genuine
blocking condition has appeared.

Only the minimum transaction checks required for a safe merge may be
revalidated immediately before merge.




### 15.2 Canonical Runbook Bootstrap Contract

Every new Cursor chat shall begin by establishing this runbook as the
single semantic implementation authority for that chat.

Mandatory bootstrap:

```text
RUNBOOK_BOOTSTRAP_REQUIRED=true
RUNBOOK_READ_COMPLETE=true
RUNBOOK_SEMANTIC_MAP_ESTABLISHED=true
RUNBOOK_USED_AS_SINGLE_IMPLEMENTATION_AUTHORITY=true
NO_PARALLEL_SEMANTIC_MODEL=true
```

Operational rule:

- At the beginning of every new Cursor chat, attach or reference the current
  canonical runbook.
- Cursor shall ingest the complete runbook before performing any repository
  mutation.
- All later capability implementations, reviews, merges and analyses shall
  use the runbook as the primary semantic reference.
- If the runbook is unavailable in a new chat, Cursor shall request it before
  continuing with implementation work.
- No implementation may silently continue using assumptions from previous
  chats.

This requirement exists because chat context is not guaranteed to persist
across independent Cursor conversations. Therefore every new chat must
explicitly establish the current canonical runbook before implementation.


# 16. Cursor Assignment Contract

Every capability command must include:

``` text
OWNER_GO=true
OPERATOR_AUTHORIZATION_EXPLICIT=true
CAPABILITY_ID=<id>
EXPECTED_ORIGIN_MAIN_SHA=<sha>
CORE_LOGIC_CHANGE_ALLOWED=false
LIVE_TRADING_ALLOWED=false
TESTNET_ALLOWED=false
PAPER_EXCHANGE_ORDERS_ALLOWED=false
EXCHANGE_CREDENTIAL_USE_ALLOWED=false
REAL_CAPITAL_MOVEMENT_ALLOWED=false
NETWORK_SESSION_ALLOWED=<true|false>
AUTHORIZATION_CONSUMPTION_ALLOWED=<true|false>
RULESET_MUTATION_ALLOWED=false
NOTION_MUTATION_ALLOWED=<true|false>
```

Mandatory output:

``` text
STATUS
VERDICT
REVIEW_MODE
CAPABILITY_ID
OWNER_GO
EXPECTED_ORIGIN_MAIN_SHA
ACTUAL_ORIGIN_MAIN_SHA
ACTUAL_HEAD_SHA_BEFORE
ACTUAL_BRANCH_BEFORE
HEAD_EQUALS_ORIGIN_MAIN_BEFORE
TRACKED_WORKTREE_CLEAN_BEFORE
UNTRACKED_EVIDENCE_PRESERVED
FILES_CHANGED
CORE_LOGIC_CHANGED
CONFIG_CHANGED
CONFIG_CONSUMER_TRACE
STATE_OWNERS
PERSISTENCE_CHANGED
ATOMICITY_MODEL
RESTART_SEMANTICS_PROVEN
PRODUCTIVE_CALLER_ADDED
RUNTIME_REACHABLE
ACTIVATION_CHANGED
LIVE_PATH_CHANGED
TESTNET_PATH_CHANGED
EXCHANGE_CREDENTIAL_PATH_CHANGED
TESTS_RUN
TESTS_PASS
FAILURE_INJECTION_RESULTS
EVIDENCE_CREATED
EVIDENCE_VERIFIED
CLAIMS_MATCH_EVIDENCE
DOCS_UPDATED
NOTION_UPDATED
BRANCH_CREATED
COMMIT_SHA
PR_NUMBER
CONFIRM_TOKEN_CANONICAL_PATH_USED
CONFIRM_TOKEN_PLAINTEXT_EXPOSED
HARD_STOP
HARD_STOP_REASON
NEXT_SAFE_STEP
```

------------------------------------------------------------------------

# 17. PR and Merge Standard

## 17.1 Capability PR

A PR must contain one complete capability or one independently provable
closure step.

No cosmetic micro-slices without runtime-closure value.

## 17.2 PR description

Mandatory sections:

-   problem;
-   current runtime truth;
-   target state;
-   call graph before/after;
-   state ownership;
-   config ownership;
-   persistence and atomicity;
-   restart semantics;
-   failure semantics;
-   safety invariants;
-   tests;
-   failure injection;
-   evidence;
-   claim semantics;
-   core logic change classification;
-   activation state;
-   rollback;
-   out of scope.

## 17.3 Merge

Ruleset mutation requires separate explicit Owner-Merge-GO.

Canonical merge transaction:

``` text
snapshot ruleset
→ verify required checks and exact PR head SHA
→ verify no new commit
→ verify only blocker
→ temporarily disable only when explicitly authorized
→ squash merge
→ restore exact ruleset
→ verify ruleset active
→ fast-forward local main
→ verify HEAD=origin/main
→ verify tracked worktree clean
→ verify untracked evidence preserved
```

No runtime, config, authorization or network-session mutation during the
merge transaction.

------------------------------------------------------------------------

# 18. Repository Ratification and Canonical Status Transition

This document remains non-runtime-authorizing until repository
ratification is complete.

Required transition:

``` text
DOCUMENT_CLASS=PROPOSED_CANONICAL_MASTER_RUNBOOK
STATUS=OWNER_REVIEWED_PENDING_REPOSITORY_RATIFICATION
→ repository placement
→ exact diff review
→ Owner ratification
→ merge
→ repository SHA and document digest binding
→
DOCUMENT_CLASS=CANONICAL_MASTER_RUNBOOK
STATUS=CANONICAL_WORKING_AUTHORITY
```

Required canonical metadata after merge:

``` text
RATIFIED_BY_OWNER=true
REPOSITORY_PATH=<canonical path>
REPOSITORY_SHA=<merge sha>
DOCUMENT_SHA256=<digest>
VERIFIED_AT=<timestamp>
AUTHORITY_EFFECT=IMPLEMENTATION_AND_OPERATIONAL_SEMANTIC_AUTHORITY
RUNTIME_AUTHORIZATION_EFFECT=NONE
STALE_IF_HEAD_DIFFERS=true
```

The document must never authorize activation, network sessions,
authorization consumption, Testnet or Live merely by being merged.

------------------------------------------------------------------------

# 19. Documentation and Evidence Freshness

Every current-truth document must include:

``` text
DOCUMENT_CLASS
REPOSITORY_SHA
EVIDENCE_SHA_OR_MANIFEST
VERIFIED_AT
RUNTIME_STATE
ACTIVATION_STATE
AUTHORITY_EFFECT
STALE_IF_HEAD_DIFFERS=true
```

Target documents must be marked:

``` text
DOCUMENT_CLASS=TARGET_ARCHITECTURE
NON_AUTHORIZING=true
```

Historical documents must be marked:

``` text
DOCUMENT_CLASS=HISTORICAL
NON_CURRENT_RUNTIME_TRUTH=true
```

No document may use unqualified terms such as:

-   complete;
-   operational;
-   production-ready;
-   fully integrated;
-   end-to-end proven;
-   active;
-   live-ready.

Evidence packages must distinguish:

``` text
CODE_PATH
RUNTIME_REACHABILITY
STATE_CONTINUITY
RESTART
OBSERVED_OUTCOME
ECONOMIC_RECONSTRUCTION
ACTIVATION
```

------------------------------------------------------------------------

# 20. Audit and Drift Prevention

Run a forensic completeness audit:

-   after each major state/persistence capability;
-   after every activation-relevant merge;
-   after any core/config authority change;
-   after every three ordinary capability merges at the latest.

Mandatory audit questions:

1.  Which components exist only as code or DTOs?
2.  Which are bound but not productively reachable?
3.  Which are reachable but not stateful?
4.  Which state is not persisted?
5.  Which persisted state is not restart-loaded?
6.  Which restart path is not digest-equivalent?
7.  Which config values remain hardcoded or ambiguous?
8.  Which evidence claims exceed observed telemetry?
9.  Which Exit producers remain stubs?
10. Which research or legacy components can create parallel authority?
11. Which Runtime paths can reach real execution or credentials?
12. Which documents are stale relative to current HEAD?
13. Which deferred Owner requirements lack a review trigger?
14. Which capability no longer contributes to the critical trading path?

New findings must be classified as one of:

``` text
WIRING_GAP
STATE_PERSISTENCE_GAP
STATE_IDENTITY_GAP
RESTART_GAP
ATOMICITY_GAP
CONFIG_DRIFT
EVIDENCE_GAP
EVIDENCE_CLAIM_DEFECT
DOCUMENTATION_DRIFT
CORE_LOGIC_DEFECT
LEGACY_PARALLEL_AUTHORITY
INTENTIONAL_SAFETY_BARRIER
DEFERRED_REQUIRED_CAPABILITY
INSUFFICIENT_EVIDENCE
```

Unknown findings do not invalidate the runbook. They enter the Gap
Register and are dependency-positioned before the next blocked
capability.

------------------------------------------------------------------------

# 21. Program Definition of Done

The no-order system finish program is complete only when:

``` text
DOCUMENTATION_RUNTIME_DRIFT=false
CONFIG_RUNTIME_DRIFT=false_for_in_scope_runtime_values
DASHBOARD_AUTHORITY=false
UNIVERSE_TRADING_AUTHORITY_EXPLICIT=true
SINGLE_SELECTED_FUTURE_RUNTIME_CLOSED=true
RECONCILIATION_PRODUCTIVE=true
RECONCILIATION_BEFORE_ALPHA=true
C1_PRODUCTIVELY_BOUND=true
C2_PRODUCTIVELY_BOUND=true
C3_PRODUCTIVELY_BOUND=true
CONFIRMATION_STATE_PERSISTED=true
CONFIRMATION_SESSION_ID_STABLE=true
DYNAMIC_SCOPE_PRODUCTIVELY_BOUND=true
DYNAMIC_SCOPE_STATE_PERSISTED=true
DECISION_PATH_RESTART_PROVEN=true
MASTER_V2_RUNTIME_REACHABLE=true
DOUBLE_PLAY_AUTHORITY_UNAMBIGUOUS=true
RISK_BOUND=true
SAFETY_BOUND=true
EXIT_POLICY_PRODUCERS_BOUND=true
ENTRY_END_TO_END_EVIDENCE_PROVEN=true
EXIT_END_TO_END_EVIDENCE_PROVEN=true
NONZERO_FEE_EVIDENCE_PROVEN=true
NONZERO_SLIPPAGE_EVIDENCE_PROVEN=true
FUTURES_ACCOUNTING_RECONSTRUCTION_PROVEN=true
PORTFOLIO_STATE_PERSISTED=true
EVIDENCE_VERIFIED=true
EVIDENCE_CLAIMS_MATCH_TELEMETRY=true
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE=true
SIMULATED_EXECUTION_ACTIVE=true
VOL_MAX_AGE_ENFORCEMENT=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
LIVE_ORDERS=false
TESTNET_ORDERS=false
PAPER_EXCHANGE_ORDERS=false
EXCHANGE_CREDENTIAL_USE=false
REAL_CAPITAL_MOVEMENT=false
```

Live and Testnet completion are not required for this no-order Definition
of Done. They are governed by the separate, dependency-linked full-autonomy
Definition of Done in Phase 11.17 and may not weaken or reinterpret this
no-order closure standard.

------------------------------------------------------------------------

# 22. Immediate Next Capability

The next implementation step after repository placement, exact-SHA
validation and Owner ratification of this runbook is:

``` text
CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1
```

The dependency order is mandatory:

``` text
6.1 = C1/C2/C3 productive binding + stable confirmation persistence
6.2 = Dynamic Scope persistence
6.3 = Decision config ownership and consumer closure
6.4 = Full decision-path atomic restart closure
6.5 = Exit-policy producer binding
7.1 = Deterministic simulated lifecycle evidence + separate public-MD continuity evidence
7.2 = Single-future stateful no-order activation
```

Confirmation and Dynamic Scope must remain separate capabilities unless
a new forensic design proves that a combined transaction is smaller,
safer and independently verifiable.

No implementation may begin by activating the current Cap5 host.

No threshold, scope distance, Master V2 rule, Double Play rule,
Bull/Bear rule, Risk rule or Safety rule may be changed as part of the
binding work.

------------------------------------------------------------------------


# 22.1 Semantic Integration Contract

The runbook must be applied as one homogeneous system contract rather than as isolated capability documents.

Mandatory integration rules:

``` text
ONE_CANONICAL_TRADING_PATH=true
ONE_DECISION_AUTHORITY_CHAIN=true
ONE_STATE_OWNER_PER_STATE_ROOT=true
ONE_CONFIG_OWNER_PER_RUNTIME_VALUE=true
ONE_PERSISTENCE_CONTINUITY_MODEL=true
ONE_RESTART_SEMANTICS=true
ONE_EVIDENCE_CLAIM_VOCABULARY=true
NO_PARALLEL_RUNTIME_AUTHORITY=true
NO_CAPABILITY_LOCAL_SEMANTIC_DRIFT=true
```

Each capability from 6.1 onward must begin from the actual productive predecessor state and must terminate in a state that is directly consumable by the next capability without adapters that create new authority, hidden defaults or duplicate state.

Required handoff contract for every capability:

``` text
INPUT_STATE_ROOTS_DECLARED=true
OUTPUT_STATE_ROOTS_DECLARED=true
PREDECESSOR_DIGEST_BOUND=true
SUCCESSOR_CONSUMER_IDENTIFIED=true
CALL_GRAPH_EDGE_CLOSED=true
STATE_HANDOFF_PROVEN=true
CONFIG_HANDOFF_PROVEN=true
RESTART_HANDOFF_PROVEN=true
EVIDENCE_HANDOFF_PROVEN=true
CORE_LOGIC_CHANGE=false
```

A capability may not be considered closed when its tests pass in isolation but its output is not consumed by the productive successor path.

The effective implementation sequence is therefore:

``` text
Read-only Preflight 6.0
→ 6.1 Confirmation/C1 binding
→ 6.2 Dynamic Scope persistence
→ 6.3 Config ownership
→ 6.4 Atomic restart closure
→ 6.5 Exit-policy producer binding
→ 7.1 Simulated lifecycle evidence
→ 7.2 Stateful no-order activation
```

The read-only Preflight 6.0 is preparation for 6.1 and is not a separate blocking program phase.


# 23. Canonical Closing Principle

Peak_Trade is finished only when its trading logic does not merely
exist, but operates as one coherent state machine:

``` text
Observed
→ Accepted
→ Confirmed
→ Scoped
→ Decided
→ Risk-checked
→ Safety-checked
→ Simulated
→ Accounted
→ Persisted
→ Reconciled
→ Restarted
→ Reconstructed
→ Evidenced
```

The central rule remains:

``` text
Code existence is not runtime truth.
Runtime reachability is not state continuity.
State continuity is not restart proof.
Path reachability is not observed outcome.
Observed outcome is not verified evidence.
Host readiness is not activation authority.
Simulation activation is not Live authorization.
Live readiness is not Live activation.
Full autonomy is bounded autonomy under ratified risk and safety authority.
```

The immediate target is a complete, realistic and operationally trustworthy
trading runtime with all exchange-order and real-capital paths still
fail-closed. The subsequent Phase 11 target is a separately authorized,
fully autonomous Live runtime that consumes the same canonical trading core
and remains bounded by persistent risk, safety, reconciliation and Owner
authority.

# APPENDIX A --- Trading Logic Preservation Contract (NEW)

## Trading-first principle

Peak_Trade is first and foremost a trading engine. Governance,
documentation and capabilities exist only to complete, protect and
verify the canonical trading path. No governance work may delay or
replace closure of the productive trading runtime.

## Read-Only Preflight 6.0 --- Canonical Trading Logic Authority and Precedence Freeze

Before the first Capability 6.1--6.5 mutation, execute this read-only preflight as part of Capability 6.1 preparation:

CAPABILITY_6_0_CANONICAL_TRADING_LOGIC_AUTHORITY_AND_CALL_ORDER_FREEZE_V1

This preflight does not replace, renumber or delay Capability 6.1. It freezes the existing canonical decision authority, precedence and productive callers while explicitly permitting the insertion of missing wiring, persistence and restart edges that do not alter decision semantics.

Required outputs:

-   PRODUCTIVE_SYMBOLS_ENUMERATED=true
-   PRODUCTIVE_CALLERS_ENUMERATED=true
-   CALL_ORDER_FROZEN=true_for_existing_decision_precedence
-   MISSING_WIRING_EDGES_MAY_BE_INSERTED_WITHOUT_PRECEDENCE_CHANGE=true
-   STATE_OWNERSHIP_FROZEN=true
-   CONFIG_CONSUMERS_FROZEN=true
-   MASTER_V2_AUTHORITY_EXACT=true
-   DOUBLE_PLAY_AUTHORITY_EXACT=true
-   BULL_BEAR_AUTHORITY_EXACT=true
-   DYNAMIC_SCOPE_AUTHORITY_EXACT=true
-   COMPOSITION_AUTHORITY_EXACT=true
-   RISK_AUTHORITY_EXACT=true
-   SAFETY_AUTHORITY_EXACT=true
-   EXIT_PRECEDENCE_EXACT=true

## Core Logic Preservation Contract

Every capability touching runtime wiring must additionally prove:

-   GOLDEN_VECTOR_PARITY_PASS=true
-   CALL_ORDER_PARITY_PROVEN=true
-   INPUT_OUTPUT_PARITY_PROVEN=true
-   STATE_TRANSITION_PARITY_PROVEN=true
-   DECISION_REASON_PARITY_PROVEN=true
-   RISK_PARITY_PROVEN=true
-   SAFETY_PARITY_PROVEN=true
-   EXIT_PRECEDENCE_PARITY_PROVEN=true

If any parity check fails:

CORE_LOGIC_CHANGE=true OWNER_RATIFICATION_REQUIRED=true
CAPABILITY_HARD_STOP=true

## Persistence Restrictions

Capabilities 6.1--6.4 must not introduce a parallel Master V2 or Double
Play state model.

Required:

-   MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false
-   DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false
-   SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY=true

Every persisted field shall be classified as exactly one of:

-   PERSIST_DIRECTLY
-   REBUILD_DETERMINISTICALLY
-   EPHEMERAL
-   EVIDENCE_ONLY
-   FORBIDDEN_TO_PERSIST

## Deterministic Evidence Protection

Trading-actionability fixtures may control only market inputs and time. Failure-injection fixtures may additionally control faults, persistence boundaries, network conditions and recovery conditions, but may not inject decisions, intents or fills.

Forbidden:

-   FORCED_INTENT_ALLOWED=false
-   MASTER_V2_BYPASS_ALLOWED=false
-   DOUBLE_PLAY_BYPASS_ALLOWED=false
-   COMPOSITION_BYPASS_ALLOWED=false
-   RISK_BYPASS_ALLOWED=false
-   SAFETY_BYPASS_ALLOWED=false
-   DIRECT_FILL_INJECTION_ALLOWED=false

## Reset Semantics

A runtime restart alone must never reset trading state.

Allowed reset reasons:

-   FIRST_EVER_STATE
-   OWNER_AUTHORIZED_RESET
-   INSTRUMENT_IDENTITY_CHANGE
-   CANONICAL_INVALIDATION_TRANSITION
-   STATE_VERSION_MIGRATION
-   GOVERNED_RECOVERY

Each reset requires reason, authority, previous digest and new digest.
