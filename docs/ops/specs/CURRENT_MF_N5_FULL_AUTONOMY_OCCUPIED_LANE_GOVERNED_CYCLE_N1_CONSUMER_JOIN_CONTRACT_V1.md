---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_GOVERNED_CYCLE_N1_CONSUMER_JOIN_CONTRACT_V1
status: active
scope: Consume S8 occupied-lane governed-cycle roots and invoke the existing one-cycle orchestrator lane-local with NON-V5 EG and S7 T2 to PRE_EXTERNAL_EFFECT or HOLD; no Cap61 live bind; no host; no productive MF join; no cardinality raise
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
HARD_STOP: true
---

# CURRENT MF N=5 Full-Autonomy Occupied-Lane Governed-Cycle N=1 Consumer Join Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_FULL_AUTONOMY_GOVERNED_CYCLE_N1_CONSUMER
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_GOVERNED_CYCLE_N1_CONSUMER_JOIN_V1
CONTRACT_ID=CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_GOVERNED_CYCLE_N1_CONSUMER_JOIN_CONTRACT_V1
SLICE_ID=GOVERNED_CYCLE_N1_CONSUMER_JOIN_TO_PRE_EXTERNAL_EFFECT
S8_CONSUMED=true
GOVERNED_CYCLE_INVOKED=true
EG_V5_USED=false
T2_S7_USED=true
MAY_INVOKE_GOVERNED_CYCLE=true
NATIVE_ID_SOURCE=BoundInstrumentV1.venue_native_id
FIRST_TRADING_DECISION_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
CONSUMPTION_SEAM=invoke_run_current_productive_governed_cycle_v1
INVOCATION_CONTEXT=BOUNDED_TEST_HARNESS_LANE_ISOLATED
CAP61_CYCLE_STATE_ROOT_BOUND=false
MAY_BIND_CAP61_STATE_ROOT=false
ATOMICITY_SEMANTICS=NON_ATOMIC_DIRECT_WRITE_TEXT
ATOMICITY_CLAIMED_SATISFIED=false
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
JOIN_RANKING_AUTHORITY=false
JOIN_SELECTION_AUTHORITY=false
JOIN_CAP23_SELECTION_AUTHORITY=false
JOIN_CAP24_BINDING_AUTHORITY=false
JOIN_TRADING_AUTHORITY=false
JOIN_RUNTIME_ACTIVATION_AUTHORITY=false
JOIN_EXECUTION_AUTHORITY=false
JOIN_PERSISTENCE_AUTHORITY=false
JOIN_FULL_AUTONOMY_HOST_AUTHORITY=false
HOST_JOIN=false
MF_PRODUCTIVE_JOIN=false
PRODUCTIVE_RUNTIME_CARDINALITY=1_UNJOINED
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
ATLAS_AUTHORITY=NONE
```

S8 producer remains:
`src&#47;ops&#47;current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1&#47;addressing_join_v1.py`.

Existing governed-cycle consumer remains:
`src&#47;ops&#47;full_core_live_path_composition_root_v1&#47;current_productive_governed_cycle_orchestrator_v1.py`.

Existing S7 T2 remains:
`compose_occupied_lane_mv2_dp_durable_cycle_v1`.

Existing cursor owner remains:
`src&#47;ops&#47;full_core_live_path_composition_root_v1&#47;current_productive_sidestate_confirmation_cursor_v1.py`.

This slice implements
`invoke_occupied_lane_governed_cycle_n1_consumer_v1`. It consumes S8
`(cursor_store_root, lock_root, evidence_root)` and invokes the existing
governed cycle lane-local. EG dispatch is `non_v5_eg_dispatch_v1`. T2 is
S7. `native_id` is `BoundInstrumentV1.venue_native_id` only. Cap61 stays
`state_root=None` / `persist=False`. Missing cursor bootstraps via S7 or
follows the existing fail-closed load path. Optional 29P / venue-plan /
envelope compose uses the same BoundInstrumentV1 and stops at
PRE_EXTERNAL_EFFECT. This slice does **not** set `MF_PRODUCTIVE_JOIN` or
change `PRODUCTIVE_RUNTIME_CARDINALITY`.

## 1. Purpose

```text
bind_occupied_lane_governed_cycle_store_roots_v1
        │
        ▼
invoke_occupied_lane_governed_cycle_n1_consumer_v1
  native_id = BoundInstrumentV1.venue_native_id
  missing cursor → S7 bootstrap or existing fail-closed
        │
        ▼
run_current_productive_governed_cycle_v1
  cursor_store_root / lock_root / evidence_root from S8
  eg_cycle_dispatch = non_v5_eg_dispatch_v1
  t2_cycle_dispatch = compose_occupied_lane_mv2_dp_durable_cycle_v1
        │
        ▼
optional identity-preserving 29P / venue-plan / envelope
        │
        ▼
PRE_EXTERNAL_EFFECT | HOLD_CLOSED | COMPLETED
  POST_COUNT=0
  PERMIT_CREATED=false
        │
        ▼
STOP — no MF_PRODUCTIVE_JOIN; no 1_UNJOINED → 1_JOINED
```

## 2. Non-goals

```text
NO_V5
NO_CAP21_TO_CAP24
NO_CAP23_REINVOKE
NO_CAP24_REINVOKE
NO_RERANK
NO_RESELECT
NO_CAP61_STATE_ROOT_BIND
NO_CAP61_PERSIST
NO_HOST_JOIN
NO_LIVE_EXECUTION_PORT
NO_CONTINUOUS_RUN
NO_NETWORK_GET
NO_EXECUTE_NETWORK
NO_PERMIT_MINT
NO_POST
NO_EXTERNAL_EFFECT
NO_MF_PRODUCTIVE_JOIN
NO_PRODUCTIVE_RUNTIME_CARDINALITY_CHANGE
NO_MAX_POSITIONS_CHANGE
NO_MULTI_FUTURE_RUNTIME
NO_EXECUTION_CONCURRENCY
NO_N_GT_1_ACTIVATION
NO_ATOMICITY_UPGRADE
NO_NEW_STATE_OWNER
NO_CURSOR_SCHEMA_CHANGE
NO_RUNBOOK_REWRITE
```

## 3. Cursor / Cap61

```text
CURSOR_OWNER=ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1
SINGLE_WRITER=true
S7_IS_WRAPPER=true
DISK_PATH_RULE={lane_state_root}/current_productive_sidestate_confirmation_cursor_v1.json
N1_GLOBAL_CURSOR_REJECTED=true
CAP61_CYCLE_STATE_ROOT_BOUND=false
ATOMICITY_SEMANTICS=NON_ATOMIC_DIRECT_WRITE_TEXT
ATOMICITY_CLAIMED_SATISFIED=false
```

The inherited Runbook `ATOMIC_CHECKPOINT_REQUIRED=true` versus CURRENT
cursor `NON_ATOMIC_DIRECT_WRITE_TEXT` is not repaired here and is not
claimed satisfied.
