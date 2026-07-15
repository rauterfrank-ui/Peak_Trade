# Strategy Signal Canonical Consumer Architecture Authorization v1

```text
DOCUMENT_TYPE=ARCHITECTURE_AUTHORIZATION
DOCUMENT_VERSION=1
STATUS=AUTHORIZED_NEGATIVE
GO_TOKEN=GO_STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1

PREVIOUS_SELECTION=D
PREVIOUS_IMPLEMENTATION_BLOCKED=true
PREVIOUS_CONSUMER_STATUS=NO_SAFE_EXISTING_CANONICAL_CONSUMER

ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_AUTHORIZATION_NAME=NO_SAFE_ARCHITECTURE_AUTHORIZABLE

AUTHORIZED_CANONICAL_CONSUMER_STAGE=NONE
AUTHORIZED_CONSUMER_OWNER_FILE=NONE
AUTHORIZED_CONSUMER_OWNER_SYMBOL=NONE

STRATEGY_VALUE_SEMANTICS_RESOLVED=false
STRATEGY_IDENTITY_BINDING_RESOLVED=true
STRATEGY_VERSION_BINDING_RESOLVED=true
STRATEGY_PROVENANCE_BINDING_RESOLVED=true
STRATEGY_DIGEST_BINDING_RESOLVED=true
CMC_CONSISTENCY_BINDING_RESOLVED=false
FAIL_CLOSED_RULES_RESOLVED=false
REAL_CANONICAL_EFFECT_PROVEN=false

RAW_SIGNAL_DIRECT_AUTHORITY=false
PROVENANCE_ONLY_BINDING=false
NEW_PARALLEL_DECISION_STAGE=false
NEW_TOTAL_DECISION_OWNER=false

SLICE_2_IMPLEMENTATION_AUTHORIZED=false
SLICE_2_IMPLEMENTATION_BLOCKED=true
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE

SEPARATE_FUTURE_ARCHITECTURE_AUTHORIZATION_REQUIRED=false
SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true
SEPARATE_ARCHITECTURE_AUTHORIZATION_SUPERSEDES_SELECTION_D_BLOCK=false

CANONICAL_REPLAY_INPUT_BUILDER_SYMBOL=build_integrated_offline_replay_input_v1
CANONICAL_TOTAL_DECISION_OWNER_SYMBOL=run_integrated_offline_trading_logic_replay_v1
CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true
CANONICAL_TOTAL_DECISION_OWNER_COUNT=1

CORE_CODE_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
DOCUMENTATION_ONLY=true
MISSION_COMPLETE=false
ECONOMIC_VALIDITY_CLAIMED=false
PROMOTION_CLAIMED=false
```

## Purpose

This document is the **separate architecture authorization** required by
[`STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md`](STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md)
after Selection **D**.

It does **not** silently override Selection D. It answers the open gate:

```text
SEPARATE_FUTURE_ARCHITECTURE_AUTHORIZATION_REQUIRED=true
```

under operator GO:

```text
GO_STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_AUTHORIZATION_V1
```

## Binding baseline (ratified on main; not rediscovered)

```text
PREVIOUS_SELECTION=D
NO_SAFE_EXISTING_CANONICAL_CONSUMER=true
SLICE_2_IMPLEMENTATION_BLOCKED=true
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
PROVENANCE_ONLY_BINDING_ALLOWED=false
PARALLEL_CANONICAL_STAGE_ALLOWED=false
DIRECT_DIRECTIONAL_ASSESSMENT_BINDING_ALLOWED=false
DIRECT_ENTRY_EXIT_BINDING_ALLOWED=false
DIRECT_POSITION_BINDING_ALLOWED=false
DIRECT_REVERSAL_BINDING_ALLOWED=false
DIRECT_SIZING_BINDING_ALLOWED=false
DIRECT_ORDER_BINDING_ALLOWED=false
```

Canonical owners remain:

| Concern | Owner |
|---------|-------|
| Replay input builder | `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` → `build_integrated_offline_replay_input_v1` |
| Total decision owner | `src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py` → `run_integrated_offline_trading_logic_replay_v1` |
| Strategy binding contract | `src/backtest/strategy_signal_binding_v1.py` → `StrategySignalBindingResultV1` |
| Prior closeout | `docs/governance/STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md` |
| Parent runbook | `docs/governance/Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md` |

## Examined authorization classes (this GO)

### A. REUSE_FIRST_EXTENSION_OF_EXISTING_CANONICAL_STAGE

**Not authorizable.**

Ratified baseline: no existing Master-V2 stage safely consumes
`StrategySignalBindingResultV1.signals`. Extending Directional Assessment,
Suitability, Entry/Exit, Composition, Survival, or PolicySignal slots would
either invent colliding semantics, grant forbidden `DIRECT_*` authority, or
become provenance-only.

```text
ARCHITECTURE_CLASS_A_STATUS=REJECTED
```

### B. NEW_BOUND_INPUT_CONTRACT_WITHIN_EXISTING_CANONICAL_STAGE

**Not authorizable.**

A new typed input inside an existing stage still requires a unique
strategy-value ontology for `{-1,0,1}`. Ratified taxonomy shows
strategy-dependent encodings (persistent long/short state vs entry/exit
events vs filters). No lossless shared semantics exist without inventing a
new ontology or parallel decision authority.

```text
ARCHITECTURE_CLASS_B_STATUS=REJECTED
STRATEGY_VALUE_SEMANTICS_RESOLVED=false
```

### C. NO_SAFE_ARCHITECTURE_AUTHORIZABLE

**Selected and authorized as the negative outcome of this GO.**

```text
ARCHITECTURE_AUTHORIZATION_DECISION=C
ARCHITECTURE_AUTHORIZATION_NAME=NO_SAFE_ARCHITECTURE_AUTHORIZABLE
SLICE_2_IMPLEMENTATION_AUTHORIZED=false
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
```

## What this authorization does and does not change

### Changes

```text
SEPARATE_ARCHITECTURE_AUTHORIZATION_EXECUTED=true
SEPARATE_FUTURE_ARCHITECTURE_AUTHORIZATION_REQUIRED=false
ARCHITECTURE_AUTHORIZATION_DECISION=C
```

The Selection-D **implementation block** remains in force:

```text
PREVIOUS_SELECTION=D
SLICE_2_IMPLEMENTATION_BLOCKED=true
SLICE_2_IMPLEMENTATION_AUTHORIZED=false
NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE
```

### Does not change / invent

- no authorized consumer stage, file, or symbol
- no strategy-value semantics for `-1` / `0` / `+1`
- no Slice-2 implementation contract
- no Core / Risk / Safety / Runtime / Order mutation
- no Economic Validity or Promotion claim
- no mission-complete claim

## Future work boundary

Any later attempt to feed strategy **values** into Master-V2 requires a
**new, separately named** architecture GO (for example a strategy-signal
ontology redesign or a family-scoped non-value path). It must not treat
this document as an implementation green light, and must not reopen
Selection D as if the consumer already existed.

## Non-claims

```text
MISSION_COMPLETE=false
SLICE_2_IMPLEMENTATION_AUTHORIZED=false
ECONOMIC_VALIDITY_CLAIMED=false
PROMOTION_CLAIMED=false
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
CORE_CODE_EFFECT=NONE
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
ORDER_EFFECT=NONE
```
