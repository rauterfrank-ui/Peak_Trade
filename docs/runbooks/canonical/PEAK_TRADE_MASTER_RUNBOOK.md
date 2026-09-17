# Peak_Trade Master Runbook — CURRENT Operational SSOT

```text
DOCUMENT_CLASS=CANONICAL_MASTER_RUNBOOK
DOCUMENT_ROLE=CURRENT_OPERATIONAL_SSOT
AUTHORITY_EFFECT=IMPLEMENTATION_AND_OPERATIONAL_SEMANTIC_AUTHORITY
RUNTIME_AUTHORIZATION_EFFECT=NONE
NO_PARALLEL_SEMANTIC_MODEL=true
BOUND_ORIGIN_MAIN_SHA=4c5e0adfb3fbd724d895f64bf532158e8c6f1d0e
STALE_IF_HEAD_DIFFERS=true
```

This document is the Owner-ratified CURRENT operational single source of
truth for Peak_Trade. It describes what the system is now.

Historical development chronology has no operational authority.
Development diary material lives outside this repository SSOT.

This document does not authorize Live trading, Testnet execution, venue
POST, credential use, real-capital movement, continuous productive runs,
or trading-logic mutation. Explicit scoped Owner-GO is required for those
actions where CURRENT gates permit them at all.

```text
IMPLEMENTED != ACTIVATED
ACTIVATED != AUTHORIZED
AUTHORIZED != EXECUTED
EXECUTED != PROVEN
CONTRACT_PRESENT != READY
FIXTURE_PASS != PRODUCTIVE_EVIDENCE
```

------------------------------------------------------------------------

## CURRENT System Identity

Peak_Trade is a futures-only trading engine.

```text
SYSTEM=Peak_Trade
MARKET_SCOPE=FUTURES_ONLY
CURRENT_SELECTION_MODE=SINGLE_SELECTED_FUTURE
CURRENT_MAX_POSITIONS=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
DECISION_CORE=Master_V2_plus_Double_Play
DASHBOARD_ROLE=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
```

```text
CURRENT_CLEAN_TRADING_CORE_STATUS=CLOSED
EARLIEST_REMAINING_CORE_GAP=NONE
TRADING_LOGIC_RECONSTRUCTION_REQUIRED=false
FURTHER_CORE_ANALYSIS_REQUIRED=false
```

The CURRENT Clean Trading Core chain is closed and must not be treated as
open reconstruction work:

```text
Single Selected Future
→ finalized/fresh C1
→ Dynamic/Directional Scope
→ Bull/Bear State Switch / SideState
→ Confirmation
→ Master V2 + Double Play
→ Entry/Exit eligibility
→ exactly-one governed cycle
→ bounded continuous progression
```

Master V2 and Double Play are CURRENT decision owners. Their trading
semantics must not be modified by autonomous agents. Wiring, joining,
admission, and orchestration around them do not reopen core reconstruction.

Canonical Python runtime:

```text
CANONICAL_PYTHON_LAUNCHER=scripts/pt
CANONICAL_PYTHON_INTERPRETER=.venv/bin/python
REQUIRES_PYTHON=>=3.10
```

Navigation without semantics: `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`.

------------------------------------------------------------------------

## CURRENT Architecture and Authority Graph

Runtime truth is owned by code, config, persistence, tests, and sealed
evidence on current `origin/main`. This runbook owns operational semantic
interpretation. Chat memory is not authority.

### Primary semantic identities

```text
full_core_live_path_authority_v1
capital_risk_admissibility_owner_v1
canonical_order_intent_owner_v1
stateful_no_order_host_join_v1
send_capable_adapter_v1
governed_continuous_cycle_orchestrator_v1
```

### Domain ownership (CURRENT)

| Domain | CURRENT owner role |
| --- | --- |
| Universe | Governed futures universe producer |
| Ranking | Productive ranking producer |
| Single Selected Future | `CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1` (compat id; selection owner) |
| Instrument binding | `CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1` (compat id; binding owner) |
| Decision | Master V2 + Double Play integrated decision path |
| SideState / EntryExit | Double Play SideState / EntryExit owners |
| Risk / capital admissibility | `capital_risk_admissibility_owner_v1` |
| Safety | Offline safety-kernel boundary owner |
| Order intent | `canonical_order_intent_owner_v1` |
| Host join | `stateful_no_order_host_join_v1` |
| Send-capable adapter | `send_capable_adapter_v1` |
| Wire-send / external-effect boundary | `LIVE_EXECUTION_BOUNDARY` |
| Full-Core live-path authority | `full_core_live_path_authority_v1` |
| Bounded continuous sequencing | `governed_continuous_cycle_orchestrator_v1` |
| Persistence | Durable single-writer state owners |
| Observability / Landscape Dashboard | Read-only consumer; `AUTHORITY_EFFECT=NONE` |
| Treasury | Required for full autonomy; not a trading-decision owner |

### Authority chain

```text
Governed Futures Universe
→ Productive Ranking
→ Persisted Single Selected Future
→ Native Instrument Binding
→ Public / finalized market observation (C1)
→ Dynamic Scope + Directional Scope
→ Bull/Bear State Switch + SideState
→ Confirmation
→ Master V2 + Double Play
→ Survival / Suitability / Composition
→ capital_risk_admissibility_owner_v1
→ Safety boundary
→ canonical_order_intent_owner_v1
→ Host join / send-capable adapter / execution boundary
```

Forbidden authority inversions:

```text
Dashboard → Decision
Research strategy → Direct Intent / Fill / Order
Execution → Rerank or Reselect instrument
Ranking → Bypass Single Selected Future persistence
Wire-send → Imply External Effect without separate authorization
Standing LIVE_* predicates → Imply POST / External Effect
```

Execution must not rerank or reselect. Selection and binding remain upstream
owners.

------------------------------------------------------------------------

## CURRENT Trading Core

### Single Selected Future binding

CURRENT mode is single selected future with `MAX_POSITIONS_EFFECTIVE=1`.
Multi-future runtime is unauthorized. Selection and instrument binding are
persisted and consumed by runtime; execution consumers may not change the
selected instrument.

### Master V2

Master V2 is the CURRENT primary market-state / trading-decision core.
It is closed as part of the Clean Trading Core. Do not reopen it as
reconstruction work. Do not mutate its trading semantics without explicit
Owner authorization that names trading-logic change.

### Double Play

Double Play owns SideState and Entry/Exit composition on the CURRENT path.
It is closed as part of the Clean Trading Core. Do not reopen it as
reconstruction work. Do not mutate its trading semantics without explicit
Owner authorization that names trading-logic change.

### Bull/Bear State Switch

Direction state is governed by the Bull/Bear state switch and related
SideState semantics. Invalid or ambiguous restore remains fail-closed.
Agents must not invent alternate direction owners.

### Dynamic Scope

Dynamic Scope is CURRENT durable decision state on the productive path.
Scope values are owned by their config/persistence owners. Forbidden
defaults and silent numeric mutation are not allowed.

### Directional Scope

Directional Scope is CURRENT state that must remain consistent with
SideState / direction semantics. Rebuild and restore rules are fail-closed.

### SideState

SideState is durable decision state required for restart-safe trading
continuity. It is owned by Double Play SideState surfaces. Agents must not
create a second SideState owner.

### Confirmation

Confirmation (including C1/C2/C3 productive binding semantics) is CURRENT
durable state. Fresh finalized C1 observations gate governed cycle
progression. Agents must not force confirmation or fabricate C1 freshness.

### Entry/Exit

Entry and Exit eligibility are produced by the Master V2 + Double Play path
and downstream risk/safety/intent owners. FORCE_ENTER is forbidden.
Exit/reduce semantics remain governed by their CURRENT owners and must not
be blanket-suppressed by unauthorized adapters.

### Exactly-one governed cycle

CURRENT semantic capability: exactly one governed cycle per authorized
consume instance. One accepted fresh finalized C1 drives at most one cycle
invocation under the cycle authorization token. Partial failure,
authorization mismatch, occupancy violations, and stale/equal C1 fail closed.

Historical label `EH.S5` / `S5` is compatibility/navigation only.

### `governed_continuous_cycle_orchestrator_v1`

CURRENT semantic capability: bounded continuous progression that repeatedly
instantiates existing exactly-one governed cycles under a distinct continuous
authorization, with hard cycle and duration bounds.

```text
PRIMARY_SEMANTIC_IDENTITY=governed_continuous_cycle_orchestrator_v1
CONTINUOUS_RUN_AUTHORIZED=false
RUNTIME_OWNER_GO=OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_V1
RUNTIME_OWNER_GO_STATUS=DEFINED_NOT_CONSUMED
```

Continuous authorization is not cycle authorization, not GET authorization,
not permit mint, and not POST authorization. Historical label `EH.S6` / `S6`
is compatibility/navigation only.

------------------------------------------------------------------------

## CURRENT Data and Input Contracts

Required CURRENT input classes:

- Public market-data observations with event-time identity and ordering
- Finalized/fresh C1 observation acceptance for governed progression
- Native instrument metadata required by binding and sizing
- Account / margin / capital observations only through governed producers
  when a capability path consumes them
- Config values from explicit owners; no silent defaults for decision-critical
  numerics

Fail-closed when:

- required observation identity/freshness is missing or stale
- instrument binding is absent or mismatched
- config owner is unbound for a required decision key
- an input would require unauthorized network/credential use

Volatility numeric max-age enforcement remains a separate gate and must not
be assumed active unless CURRENT config/code prove it.

------------------------------------------------------------------------

## CURRENT State and Persistence Contracts

State categories:

```text
DURABLE_SOURCE_STATE
DURABLE_DECISION_STATE
DERIVED_REBUILDABLE_STATE
EPHEMERAL_CONNECTION_STATE
EVIDENCE_ONLY_STATE
```

Required durable decision state includes at least:

- Single Selected Future + instrument binding
- Confirmation / C1 cursor semantics
- Dynamic Scope and Directional Scope
- SideState and Entry/Exit mapping state
- Risk reservations / exposure locks where CURRENT path persists them
- Kill-switch / safety durable control state
- Authorization references (never plaintext secrets)
- Evidence cursor / audit chain bindings

Invariants:

```text
SINGLE_WRITER=true
ATOMIC_CHECKPOINT_REQUIRED=true
RESTART_MUST_RESTORE_OR_FAIL_CLOSED=true
DERIVED_STATE_MUST_NOT_BECOME_SECOND_SSOT=true
```

Forbidden:

- dual writers for the same durable decision surface
- treating rebuildable projections as authority
- silently rewriting sealed evidence

------------------------------------------------------------------------

## CURRENT Risk and Capital Admissibility

```text
RISK_SIZING_OWNER=capital_risk_admissibility_owner_v1
```

Risk/capital admissibility runs before order-intent externalization on the
Full-Core path. Missing, unbound, stale, wrong-instrument, or non-positive
typed capital inputs fail closed.

Compatibility claim/deny tokens such as `STEP_29P` may appear in CURRENT
code paths. They are not independent architecture owners. See CURRENT
Compatibility Identifiers.

Ordering invariant:

```text
Decision eligibility
→ capital_risk_admissibility_owner_v1
→ Safety boundary
→ canonical_order_intent_owner_v1
```

Post-replay host consumption must not re-invoke a second risk owner.

------------------------------------------------------------------------

## CURRENT Order-Intent and Execution Boundaries

```text
ORDER_INTENT_OWNER=canonical_order_intent_owner_v1
HOST_JOIN_OWNER=stateful_no_order_host_join_v1
SEND_CAPABLE_ADAPTER_OWNER=send_capable_adapter_v1
WIRE_SEND_OWNER=LIVE_EXECUTION_BOUNDARY
PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY=full_core_live_path_authority_v1
```

Order intent is produced only by its owner. Translators/adapters are not
decision owners.

Compatibility status token:

```text
STEP_29Q_STATUS=PLAN_ONLY
```

`PLAN_ONLY` means CURRENT intent planning status on the governed path. It
does not authorize venue POST or external effect.

Standing Full-Core predicates on current `origin/main` constants:

```text
LIVE_ENABLED=true
LIVE_ARMED=true
WIRE_SEND_PERMITTED=true
SUBMISSION_AUTHORIZED=true
LIVE_AUTHORIZED=true
PRODUCTIVE_WIRE_SEND_REACHABLE=true
```

Non-implications (binding):

```text
LIVE_ENABLED != LIVE_ARMED implication beyond standing field
LIVE_ARMED != risk admissible
WIRE_SEND_PERMITTED != automatic send
SUBMISSION_AUTHORIZED != POST
LIVE_AUTHORIZED != STEP_29Q lift
LIVE_AUTHORIZED != POST
LIVE_AUTHORIZED != EXTERNAL_EFFECT
PRODUCTIVE_WIRE_SEND_REACHABLE != EXTERNAL_EFFECT_AUTHORIZED
```

External-effect standing boundary on current `origin/main` constants:

```text
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
POST_ALLOWED=false
```

Permit mint, envelope-bound single-use send, and venue POST require their
own scoped Owner-GO and CURRENT gate satisfaction. This runbook consumes
none of those authorizations.

------------------------------------------------------------------------

## CURRENT Safety Invariants

Fail-closed is default.

Mandatory CURRENT invariants:

```text
SINGLE_SELECTED_FUTURE=true
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
EXECUTION_MUST_NOT_RERANK=true
EXECUTION_MUST_NOT_RESELECT=true
MASTER_V2_DOUBLE_PLAY_SEMANTICS_LOCKED_WITHOUT_OWNER_GO=true
FORCE_ENTER=false
DASHBOARD_AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT_OF_THIS_DOCUMENT=NONE
```

Additional required controls:

- physical separation between decision intent and external venue mutation
- credential material never printed; references only
- kill-switch durable and enforceable
- authorization-token separation (persist GO ≠ runtime GO ≠ GET GO ≠
  cycle GO ≠ continuous GO ≠ permit GO ≠ POST GO)
- event-time / identity / ordering must be preserved for evidence claims
- evidence ladders must not over-claim (Entry/Exit/Fee/Slippage/Risk/Safety)
- unknown or unclassified required state → deny

Modes must remain distinct:

```text
SHADOW | INTERNAL_SIMULATED_EXECUTION | PAPER_EXCHANGE | TESTNET | LIVE
```

Do not equate offline/simulated activation with Live/Testnet authorization.

------------------------------------------------------------------------

## CURRENT Autonomy Boundaries

Full autonomy is a program target, not a CURRENT license to act.

Autonomous agents MAY:

- read this SSOT and CURRENT code/config/tests/evidence
- propose bounded docs/code changes only when Owner-authorized
- preserve fail-closed behavior and evidence integrity

Autonomous agents MUST NOT:

- treat historical Cap/Phase/Step/Section/EH/Z2/Pxx/Dxx labels as CURRENT
  instructions
- reopen Clean Trading Core reconstruction
- mutate Master V2 / Double Play trading semantics without explicit
  trading-logic Owner-GO
- activate continuous run (`governed_continuous_cycle_orchestrator_v1`)
  without consuming the distinct continuous runtime Owner-GO under CURRENT
  gates
- mint permits, POST, wire-send, load exchange credentials, move capital,
  or start unauthorized network sessions
- create a parallel SSOT or second authority graph
- infer authorization from implementation presence

Learning Loop / promotion:

```text
RESEARCH_OR_CANDIDATE_SIGNAL != RUNTIME_AUTHORITY
PROMOTION_REQUIRED_BEFORE_RUNTIME_AUTHORITY=true
UNPROMOTED_STRATEGY_DIRECT_INTENT=FORBIDDEN
```

Treasury CURRENT role:

```text
TREASURY_CLASSIFICATION=REQUIRED_FOR_FULL_AUTONOMY
TREASURY_IS_TRADING_DECISION_OWNER=false
```

------------------------------------------------------------------------

## CURRENT Operating and Activation State

Bound baseline for this SSOT revision:

```text
BOUND_ORIGIN_MAIN_SHA=4c5e0adfb3fbd724d895f64bf532158e8c6f1d0e
```

Every later mutation task must revalidate actual `origin/main`.

CURRENT operating facts:

```text
CURRENT_CLEAN_TRADING_CORE_STATUS=CLOSED
EARLIEST_REMAINING_CORE_GAP=NONE
TRADING_LOGIC_RECONSTRUCTION_REQUIRED=false
FURTHER_CORE_ANALYSIS_REQUIRED=false
STATEFUL_NO_ORDER_HOST_JOIN_OWNER=stateful_no_order_host_join_v1
SEND_CAPABLE_ADAPTER_OWNER=send_capable_adapter_v1
FULL_CORE_LIVE_PATH_AUTHORITY=full_core_live_path_authority_v1
CONTINUOUS_ORCHESTRATOR=governed_continuous_cycle_orchestrator_v1
CONTINUOUS_RUN_AUTHORIZED=false
STEP_29Q_STATUS=PLAN_ONLY
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
POST_ALLOWED=false
```

Standing predicates may be true without authorizing external effect.
Agents must re-read CURRENT constants before any activation-class work.

Default fail-closed for unauthorized programs unless CURRENT evidence plus
explicit scoped Owner-GO says otherwise for that exact scope:

```text
TESTNET_PROGRAM_DEFAULT=fail_closed_without_scoped_Owner_GO
LIVE_EXTERNAL_EFFECT_DEFAULT=fail_closed_without_scoped_Owner_GO
```

------------------------------------------------------------------------

## CURRENT Observability and Landscape Dashboard

Observability exists for oversight, not decision authority.

Required domains include market-data health, decision/order latency,
rejection taxonomy, position/margin state, risk/safety vetoes,
reconciliation, persistence/journal health, evidence cursor health, and
authorization/credential status metadata (never secrets).

Landscape Dashboard / WebUI:

```text
DASHBOARD_ROLE=READ_ONLY_CONSUMER
DASHBOARD_AUTHORITY_EFFECT=NONE
DASHBOARD_TRADING_INPUT=false
DASHBOARD_DIRECT_ORDER_SUBMIT=false
DASHBOARD_IS_SSOT=false
```

Permitted:

```text
Runtime SSOT → Persistence / Evidence → Read Model → Dashboard
```

Forbidden:

```text
Dashboard → Runtime Decision / Intent / Order
```

------------------------------------------------------------------------

## CURRENT Compatibility Identifiers

Historical identifiers below may appear in CURRENT code, persistence,
claim keys, module paths, or evidence paths. They are not CURRENT phase
pointers, architecture owners, next actions, or unfinished development
steps.

```text
CLASS=HISTORICAL_COMPATIBILITY_ONLY
AUTHORITY_EFFECT=NONE
```

| Identifier | Compatibility role |
| --- | --- |
| `STEP_29P` | Claim/deny/consumer tokens on capital/risk admissibility path |
| `STEP_29Q` | Order-intent / plan status tokens; CURRENT status `PLAN_ONLY` |
| `PLAN_ONLY` | CURRENT plan-status literal consumed by governed cycle checks |
| `CAP_7_2` | Historical host/activation naming in paths and evidence |
| `CAP_11_1` | Historical send-capable adapter naming in paths/modules |
| `SECTION_11_13_5_*` | Scoped canary venue-proof evidence domain labels |
| `SECTION_11_14_*` | Historical canary lifecycle evidence ladder labels |
| `EH.S5` / `S5` | Navigation label for exactly-one governed cycle |
| `EH.S6` / `S6` | Navigation label for bounded continuous orchestrator |
| `CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1` | Selection owner string still wired |
| `CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1` | Binding owner string still wired |
| Historically named file/module/evidence paths | Location compatibility only |

Do not rename persisted/API/claim tokens merely for documentation style.

Primary CURRENT identities remain the semantic owners listed above, not
these compatibility labels.

------------------------------------------------------------------------

## CURRENT Productive Boundary

Exactly one CURRENT productive boundary:

```text
CLEAN_TRADING_CORE=CLOSED
EARLIEST_REMAINING_CORE_GAP=NONE
```

Remaining productive/runtime/activation/external-effect boundary
(not a Trading-Core reconstruction gap):

```text
CURRENT_PRODUCTIVE_BOUNDARY=EXTERNAL_EFFECT_AND_BOUNDED_CONTINUOUS_RUN_FAIL_CLOSED
PRODUCTIVE_LIVE_NEXT_POINTER_AUTHORITY=full_core_live_path_authority_v1
CONTINUOUS_RUN_AUTHORIZED=false
RUNTIME_OWNER_GO_STATUS=DEFINED_NOT_CONSUMED
EXTERNAL_EFFECT_AUTHORIZED=false
REAL_VENUE_POST_ALLOWED=false
POST_ALLOWED=false
STEP_29Q_STATUS=PLAN_ONLY
PERMIT_MINT_AUTHORIZED_BY_THIS_DOCUMENT=false
VENUE_POST_AUTHORIZED_BY_THIS_DOCUMENT=false
OWNER_GO_CONSUMED_BY_THIS_DOCUMENT=false
```

Interpretation for autonomous agents:

1. Clean Trading Core work is closed. Do not continue core reconstruction.
2. Standing LIVE_* / wire-send / submission predicates are not POST rights.
3. Bounded continuous progression exists as semantic capability but is not
   authorized to run (`CONTINUOUS_RUN_AUTHORIZED=false`).
4. Any further productive advance requires a new scoped Owner-GO that names
   the exact boundary (continuous run, permit, POST, network session, or
   other CURRENT gate) and must revalidate `origin/main` first.
5. If a required CURRENT field cannot be proven from code/config/tests,
   treat it as `UNKNOWN_FAIL_CLOSED` — never resurrect historical next-step
   pointers.

```text
IMMEDIATE_NEXT_FROM_HISTORY=FORBIDDEN
CANONICAL_NEXT_FROM_HISTORY=FORBIDDEN
NEXT_SAFE_STEP_FROM_HISTORY=FORBIDDEN
EARLIEST_UNRESOLVED_FROM_HISTORY=FORBIDDEN
```

------------------------------------------------------------------------

## Closing Principle

Peak_Trade is a trading engine with a closed CURRENT Clean Trading Core and
fail-closed productive external-effect boundaries.

Preserve trading semantics. Preserve authority ownership. Preserve evidence
integrity. Prefer the smallest Owner-authorized change that advances a
CURRENT productive boundary without reopening chronology as authority.
