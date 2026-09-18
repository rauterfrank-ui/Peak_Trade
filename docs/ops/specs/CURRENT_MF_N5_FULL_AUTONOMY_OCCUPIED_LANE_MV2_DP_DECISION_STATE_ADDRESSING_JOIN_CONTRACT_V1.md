---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_CONTRACT_V1
status: active
scope: S4 bounded lane-isolated invoke of the existing N=1 MV2+DP cycle from the S3 seam; no persist; no restore; no Cap61 live bind; no host; no productive MF join; no S5
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-18
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
HARD_STOP: true
---

# CURRENT MF N=5 Full-Autonomy Occupied-Lane MV2/DP Decision-State Addressing Join Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_FULL_AUTONOMY_MV2_DP_DECISION_STATE_ADDRESSING
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_V1_S4_CONSUMER_INVOKE
CONTRACT_ID=CURRENT_MF_N5_FULL_AUTONOMY_OCCUPIED_LANE_MV2_DP_DECISION_STATE_ADDRESSING_JOIN_CONTRACT_V1
SLICE_ID=S4_LANE_ADDRESSED_CONSUMER_INVOKE
S2_IMPLEMENTED=true
S3_IMPLEMENTED=true
S4_IMPLEMENTED=true
S5_IMPLEMENTED=false
RESOLUTION_RULE=occupied_lane_id -> IsolatedLaneSlotV1.lane_state_root
OCCUPIED_LANES_ONLY=true
UNIQUE_MUTABLE_ROOTS_ENFORCED=true
GLOBAL_N1_CURSOR_REJECTED=true
FIRST_DECISION_STATE_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
CONSUMPTION_SEAM=pre_invoke_run_current_productive_master_v2_runtime_cycle_v1
CONSUMER_CYCLE_TAKES_STORE_ROOT=false
CURSOR_FILENAME_SHARED_ACROSS_LANES=true
CAP61_CYCLE_STATE_ROOT_BOUND=false
INVOCATION_CONTEXT=BOUNDED_TEST_HARNESS_LANE_ISOLATED
CONSUMER_INVOKED=true
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
LANE_MAPPING_OWNER=ops.current_mf_n5_isolated_lane_instance_topology_v1
PAIR_MAP_PRODUCER_OWNER=ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1
ADDRESSING_CONSUMER_OWNER=ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1
CURSOR_OWNER=ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1
CAP61_CONFIRMATION_OWNER=ops.stateful_confirmation_and_c1_productive_binding_v1
FULL_AUTONOMY_HOST_OWNER=stateful_no_order_host_join_v1
PAIR_MAP_PRODUCER=compose_occupied_lane_mv2_dp_handoff_v1
PAIR_MAP_OBJECT=dict[lane_id, (IsolatedLaneSlotV1, BoundInstrumentV1)]
PAIR_MAP_SLOT_TYPE=IsolatedLaneSlotV1
SLOT_IDENTITY=lane_id
SLOT_STATE_ROOT_RESOLVER=lane_state_root_for
INTENDED_PER_LANE_STORE_ROOT=IsolatedLaneSlotV1.lane_state_root
N1_GLOBAL_CURSOR_LANE_SAFE=false
CURSOR_BUNDLE_TYPE=CurrentProductiveSideStateConfirmationCursorV1
CURSOR_HAS_LANE_ID_FIELD=false
CURSOR_SCHEMA_CHANGED=false
NEW_CURSOR_LANE_ID_FIELD=false
SAME_TRADING_CONFIGURATION_ACROSS_LANES=true
SHARED_MUTABLE_STATE_ACROSS_LANES=false
NEW_STATE_OWNER_CREATED=false
S2_JOIN_SYMBOL=resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1
S2_INTENDED_EGRESS=dict[lane_id, str]
S3_JOIN_SYMBOL=bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1
S3_INTENDED_EGRESS=dict[lane_id, (BoundInstrumentV1, store_root, cursor_address)]
S4_JOIN_SYMBOL=invoke_occupied_lane_mv2_dp_decision_state_consumer_v1
S4_INTENDED_EGRESS=dict[lane_id, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1]
S4_IMPLEMENTED=true
S5_IMPLEMENTED=false
NEW_COLLECTION_DTO_CREATED=false
NEW_TOP5_HANDOFF_DTO_CREATED=false
NEW_MULTI_BOUND_AUTHORITY_DTO_CREATED=false
NEW_MV2_DP_INGRESS_DTO_CREATED=false
NEW_CURSOR_SCHEMA_CREATED=false
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
FIVE_LANE_CONTINUOUS_HOST_JOIN=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
HOST_JOIN=false
MF_SINGLE_EGRESS_REWIRED=false
PARALLEL_AUTHORITY_CREATED=false
PREPARED_BOUND_CARDINALITY=0..5
PRODUCTIVE_RUNTIME_CARDINALITY=1_UNJOINED
CAP23_CHANGE_REQUIRED=false
CAP24_CHANGE_REQUIRED=false
MASTER_V2_CHANGE_REQUIRED=false
DOUBLE_PLAY_CHANGE_REQUIRED=false
FULL_AUTONOMY_HOST_CHANGE_REQUIRED=false
CURSOR_OWNER_CHANGE_REQUIRED=false
THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER=true
MAY_PERSIST_CURSOR=false
MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK=false
MAY_BIND_CAP61_STATE_ROOT=false
MAY_CAP61_PERSIST=false
MAY_CAP62_PERSIST=false
MAY_G17_CHECKPOINT=false
MAY_EXIT_POLICY_PERSIST=false
UNIVERSE_ISOLATION=HARD
CROSS_UNIVERSE_SELECTION=false
CROSS_UNIVERSE_PIN=false
CROSS_UNIVERSE_REPLACEMENT=false
CROSS_UNIVERSE_FALLBACK=false
CROSS_UNIVERSE_CANDIDATE_BORROWING=false
CROSS_UNIVERSE_RERANKING=false
MULTI_UNIVERSE_MERGE=false
INSTRUMENT_ID_ALONE_SUFFICIENT=false
ATLAS_AUTHORITY=NONE
```

S2 typed resolver:
`src&#47;ops&#47;current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1&#47;addressing_join_v1.py`.

S2 typed constants:
`src&#47;ops&#47;current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1&#47;constants_v1.py`.

Closed pair-map producer remains:
`src&#47;ops&#47;current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1&#47;handoff_join_v1.py`.

Lane topology and slot types remain:
`src&#47;ops&#47;current_mf_n5_isolated_lane_instance_topology_v1&#47;topology_v1.py`.

Existing cursor bundle owner remains:
`src&#47;ops&#47;full_core_live_path_composition_root_v1&#47;current_productive_sidestate_confirmation_cursor_v1.py`.

Existing trading-decision consumer remains the named N=1 cycle, invoked
only through the S4 bounded harness:
`src&#47;ops&#47;full_core_live_path_composition_root_v1&#47;current_productive_master_v2_runtime_cycle_v1.py`.

This slice implements
`invoke_occupied_lane_mv2_dp_decision_state_consumer_v1` from the closed
S3 seam. It does **not** persist or load the cursor, does **not** restore
the cursor from disk or from `incoming_cursor`, does **not** set Cap61
`state_root`, does **not** persist Cap61/Cap62/G17/Exit, does **not**
reinvoke Cap 2.3 or Cap 2.4, does **not** join the Full-Autonomy host,
does **not** change Master V2 or Double Play trading semantics, does
**not** change cursor schema or add `lane_id`, does **not** create a
second state owner, does **not** start S5, does **not** create a
productive MF join, and does **not** create five isolated executing
lanes. `CONSUMER_INVOKED=true` means bounded/test-harness lane-isolated
invocation only.

## 1. Purpose

Invoke the existing N=1 MV2+DP cycle lane-isolated from the closed S3
seam. Forensic consumer facts remain:

```text
CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
CONSUMER_CYCLE_TAKES_STORE_ROOT=false
CONSUMER_CYCLE_CURSOR_PARAM=incoming_cursor
CAP61_CYCLE_STATE_ROOT=None
CAP61_CYCLE_PERSIST=false
DISK_STORE_ROOT_USED_ONLY_BY_PERSIST_LOAD_WRAPPERS=true
```

The cycle does not take `store_root`. Lane addressing is the S3 seam
(`IsolatedLaneSlotV1.lane_state_root` plus shared cursor filename). S4
calls the cycle with that lane's `BoundInstrumentV1` and
`incoming_cursor=None`. Persist and restore remain out of scope.

```text
compose_occupied_lane_mv2_dp_handoff_v1
        │
        ▼
dict[lane_id, (IsolatedLaneSlotV1, BoundInstrumentV1)]
        │
        ▼
S2 RESOLVER — occupied lanes only
  store_root = IsolatedLaneSlotV1.lane_state_root
        │
        ▼
S3 CONSUMPTION SEAM BIND — immediately before
  run_current_productive_master_v2_runtime_cycle_v1
  bound_instrument + store_root + cursor_address
        │
        ▼
S4 BOUNDED HARNESS INVOKE — occupied lanes only
  same N=1 MV2+DP market/trading configuration
  per-lane BoundInstrumentV1
  incoming_cursor=None
  persist not called
  Cap61 state_root remains None
  CONSUMER_INVOKED=true means BOUNDED_TEST_HARNESS_LANE_ISOLATED
        │
        ▼
STOP — no persist; no restore; no Cap61 live bind; no host; no S5
```

`#6602` already closed PAIR_MAP_STOP. `#6605` already closed S3.
This slice does not reopen those owners. Ranking authority already ended
at `#6597`.

All occupied slots, at most five, must use the same canonical Master V2 +
Double Play configuration and semantics as the existing N=1 slot.
Configuration equality is not shared mutable state. Each lane requires
disjoint addressing through its existing `IsolatedLaneSlotV1.lane_state_root`.

```text
PAIR_MAP_STOP != consumer invoke
lane_state_root addressing != Cap61 live bind
same trading configuration != shared mutable state
N=1 global cursor path != per-lane store_root
0..5 prepared bounds != Five-Lane runtime authorized
0..5 prepared bounds != MAX_POSITIONS_EFFECTIVE raise
FIRST_TRADING_DECISION_CONSUMER remains run_current_productive_master_v2_runtime_cycle_v1
THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER=true
CONSUMER_INVOKED=true
INVOCATION_CONTEXT=BOUNDED_TEST_HARNESS_LANE_ISOLATED
MAY_PERSIST_CURSOR=false
MAY_LOAD_OR_RESTORE_CURSOR_FROM_DISK=false
MAY_BIND_CAP61_STATE_ROOT=false
HOST_JOIN=false
MF_PRODUCTIVE_JOIN=false
```

## 2. State-surface census

**canonical authority:** Master Runbook names SideState, Dynamic Scope,
Directional Scope, and Confirmation as durable decision state. Agents
must not invent a second owner.

**already adjudicated:** PAIR_MAP_STOP carries `lane_state_root` as
addressing only. `#6602` did not persist MV2&#47;DP state, restore the
cursor, or set Cap61 `state_root`.

**forensic raw evidence (FIRST_TRADING_DECISION_CONSUMER):**

Cursor bundle is the cycle-crossing object
`CurrentProductiveSideStateConfirmationCursorV1`. It has no `lane_id`
field. Embedded cycle-crossing surfaces:

```text
SideState
RuntimeScopeState
CanonicalScopeSnapshotV1 (existing_scope / Dynamic Scope snapshot)
ScopeConfirmationStateV1
CanonicalConfirmationStateV1 (Cap61 confirmation state)
```

N=1 productive cursor store remains the global relative path
`evidence&#47;ops&#47;full_core_current_productive_sidestate_confirmation_cursor_current_v1`.
That path is not lane-safe. Intended per-lane store_root is the existing
`IsolatedLaneSlotV1.lane_state_root`.

The consumer constructs Cap61 with `state_root=None` and commits with
`persist=False`. Cap61 disk, Cap62 disk, G17 checkpoint, and Exit-policy
persist exist as durable siblings. The cycle does not consume them as a
required cycle-crossing store.

HostExitPolicyBindingV1 is ephemeral this-cycle. Optional G17 producer is
in-memory when passed. ScopeCooldown and composition-direction are reset
each cycle on this consumer and are not cursor-carried.

**interpretation:** S4 invokes the named consumer from the S3 seam in a
bounded test harness only. It does not persist, restore, live-bind Cap61,
join the host, authorize productive MF, or start S5.

## 3. Slot context

Slot identity remains occupied `lane_id` from `LANE_IDS`.

Slot state root remains
`lane_state_root_for(topology_state_root_base, lane_id)` →
`{topology_state_root_base}&#47;{lane_id}`, already carried on
`IsolatedLaneSlotV1.lane_state_root`.

This contract does not invent a second lane identity, a new cursor
schema, or a new state store. S4 reuses the existing field as the
store_root string at the pre-cycle seam and records it on the invocation
result. The cycle does not take `store_root`; disk addressing remains
`{store_root}&#47;{CURSOR_FILENAME}` and is not performed here.

## 4. S1 versus S2 versus S3 versus S4 versus S5

```text
S1_CONTRACT_BIND=closed
S2_JOIN_SYMBOL=resolve_occupied_lane_mv2_dp_decision_state_store_roots_v1
S2_IMPLEMENTED=true
S3_JOIN_SYMBOL=bind_occupied_lane_mv2_dp_decision_state_consumption_seam_v1
S3_IMPLEMENTED=true
S3_INTENDED_EGRESS=dict[lane_id, (BoundInstrumentV1, store_root, cursor_address)]
S4_JOIN_SYMBOL=invoke_occupied_lane_mv2_dp_decision_state_consumer_v1
S4_IMPLEMENTED=true
S4_INTENDED_EGRESS=dict[lane_id, OccupiedLaneMv2DpDecisionStateConsumerInvocationV1]
S5_IMPLEMENTED=false
FIRST_DECISION_STATE_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
CONSUMPTION_SEAM=pre_invoke_run_current_productive_master_v2_runtime_cycle_v1
INVOCATION_CONTEXT=BOUNDED_TEST_HARNESS_LANE_ISOLATED
CONSUMER_INVOKED=true
RESOLUTION_RULE=occupied_lane_id -> IsolatedLaneSlotV1.lane_state_root
```

S4 invokes the named consumer from the S3 seam in a bounded test harness.
It does not authorize persist, restore, Cap61 live bind, host, Master V2
or Double Play mutation, productive MF join, or S5.

## 5. Non-goals

```text
NO_S5
NO_CURSOR_PERSIST
NO_CURSOR_LOAD_OR_RESTORE_FROM_DISK
NO_CAP61_STATE_ROOT_BIND
NO_CAP61_PERSIST
NO_CAP62_PERSIST
NO_G17_CHECKPOINT
NO_EXIT_POLICY_PERSIST
NO_CURSOR_SCHEMA_CHANGE
NO_CURSOR_LANE_ID_FIELD
NO_NEW_STATE_OWNER
NO_PRODUCTIVE_MF_HOST_JOIN
NO_FIVE_LANE_CONTINUOUS_RUNTIME
NO_FIVE_LANE_RUNTIME_CREATED
NO_EXECUTION_CONCURRENCY
NO_MAX_POSITIONS_CHANGE
NO_ORDER_SUBMISSION
NO_POST_NETWORK_PERMIT_CHANGE
NO_CAP23_REINVOKE
NO_CAP23_SEMANTIC_CHANGE
NO_CAP24_REINVOKE
NO_CAP24_SEMANTIC_CHANGE
NO_WALLCLOCK_SESSION_BIND_THROUGH
NO_MASTER_V2_SEMANTIC_CHANGE
NO_DOUBLE_PLAY_SEMANTIC_CHANGE
NO_C1_CYCLE
NO_STEP_29P
NO_STEP_29Q
NO_NEW_COLLECTION_DTO
NO_NEW_TOP5_HANDOFF_DTO
NO_MULTI_BOUND_AUTHORITY_DTO
NO_NEW_MV2_DP_INGRESS_DTO
NO_MF_SINGLE_EGRESS_REWIRE
NO_PRODUCTIVE_MF_CONSUMER_JOIN
NO_HOST_JOIN
```
