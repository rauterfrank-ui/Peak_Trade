---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_DURABLE_LANE_ASSIGNMENT_PERSISTENCE_CONTRACT_V1
status: active
scope: Fail-closed durable custody and recovery of an already-governed #6593 IsolatedLaneTopologyV1; no lane mapping; no productive MF join; no five-lane runtime
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

# CURRENT MF N=5 Durable Lane-Assignment Persistence Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_LANE_ASSIGNMENT_PERSISTENCE
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=CURRENT_MF_N5_DURABLE_LANE_ASSIGNMENT_PERSISTENCE_V1
CONTRACT_ID=CURRENT_MF_N5_DURABLE_LANE_ASSIGNMENT_PERSISTENCE_CONTRACT_V1
AUTHORITY_EFFECT=NONE
PERSISTENCE_RANKING_AUTHORITY=false
PERSISTENCE_MEMBERSHIP_AUTHORITY=false
PERSISTENCE_LANE_MAPPING_AUTHORITY=false
PERSISTENCE_CAP23_SELECTION_AUTHORITY=false
PERSISTENCE_CAP24_BINDING_AUTHORITY=false
PERSISTENCE_TRADING_AUTHORITY=false
PERSISTENCE_EXECUTION_AUTHORITY=false
LANE_MAPPING_OWNER=ops.current_mf_n5_isolated_lane_instance_topology_v1
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
FIVE_LANE_CONTINUOUS_HOST_JOIN=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
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

Typed custody:
`src&#47;ops&#47;current_mf_n5_durable_lane_assignment_persistence_v1&#47;persistence_v1.py`.

Lane mapping remains:
`src&#47;ops&#47;current_mf_n5_isolated_lane_instance_topology_v1&#47;topology_v1.py`.

This persist does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, and does
**not** change Cap 2.3, Cap 2.4, Master V2, or Double Play.

## 1. Purpose

Record and recover the exact already-governed `#6593` lane-topology state
so a non-bootstrap restart can supply explicit prior topology.

```text
#6593 validated IsolatedLaneTopologyV1
        │
        ▼
durable checkpoint (this contract)
        │
        ▼
recover exact IsolatedLaneTopologyV1
        │
        ▼
STOP — explicit prior_topology only
```

Persistence records state. Persistence does not decide state.

The authoritative transition remains:

```text
prior governed topology
+ current governed MF membership
→ ops.current_mf_n5_isolated_lane_instance_topology_v1
→ next governed topology
```

This layer must not independently select, rank, rotate, remap, infer lane
identity from ranking or membership order, fabricate Cap23 DTOs, bind
Cap24, invoke Master V2 / Double Play, or submit orders.

## 2. Reused primitive

CURRENT governed checkpoint pattern reused from Cap 2.1 / 2.2 / 2.3 and
dynamic-scope persistence:

```text
single-writer lock
stage → per-file atomic replace (tmp + os.replace + fsync)
MANIFEST.sha256
commit marker
fail-closed load
```

No new storage subsystem. Existing Cap 2.1 / 2.2 / 2.3 snapshot stores are
not reused as the lane-assignment SSOT (`INCOMPATIBLE_AUTHORITY`).

```text
ATOMICITY=PER_FILE_REPLACE_PLUS_STAGING_THEN_PUBLISH
BUNDLE_CRASH=FAIL_CLOSED_ON_MANIFEST_OR_MARKER_MISMATCH
PREVIOUS_CHECKPOINT_SURVIVAL_MID_PUBLISH=NOT_GUARANTEED
```

## 3. Durable object

Minimum payload is an envelope around the exact `#6593`
`IsolatedLaneTopologyV1.to_dict()` result:

- persistence schema&#47;version identity
- persistence owner (custody only)
- lane-mapping owner (unchanged)
- topology identity fields already owned by `#6593`
  (`topology_state_root_base`, exact `LANE_1..LANE_5` slots,
  occupied&#47;empty, instrument identity, universe&#47;ranking provenance)
- integrity digest over the canonical topology object
- commit marker bound to that digest

Global runtime state is excluded: equity, balances, `MAX_POSITIONS`,
execution occupancy, orders, live admission, permits, network, kill-switch,
Master-V2 / Double-Play trading state.

```text
RECOVERED_TOPOLOGY == EXACT_PREVIOUS_GOVERNED_TOPOLOGY
RECOVERED_MEMBERSHIP == SAME_SET_OF_INSTRUMENTS  # insufficient
```

## 4. Storage location and identity continuity

Checkpoint root:

```text
{topology_state_root_base}&#47;durable_lane_assignment_v1&#47;
```

`topology_state_root_base` remains caller-supplied `#6593` identity. This
layer does not generate a replacement base. Per-lane namespace
`{topology_state_root_base}&#47;{lane_id}` is unchanged.

One current checkpoint per base. In-place replace. No multi-checkpoint
selection.

## 5. Bootstrap versus restart

These modes are distinct. Persistence does not infer them from membership
order or ranking.

```text
BOOTSTRAP
  no prior commit marker and no checkpoint
  → return None
  prior artifacts present
  → fail closed (must not become bootstrap)

RESTART
  valid committed checkpoint
  → return exact IsolatedLaneTopologyV1
  missing, malformed, unsupported version, digest mismatch,
  universe/provenance/state-root mismatch, or corrupt payload
  → fail closed
  MUST NOT return None / bootstrap
```

Presence discriminator reuses the CURRENT dynamic-scope rule:
commit marker or checkpoint file means a prior commit exists.

## 6. Universe isolation

A recovered topology from universe&#47;context X is not accepted as prior
topology for universe&#47;context Y. Instrument IDs matching across contexts
are insufficient.

Recovery fails closed on universe, ranking-snapshot, ranking-digest, or
`topology_state_root_base` mismatch against caller-supplied expected
bindings.

## 7. Recovery stop condition

Recovery validates and returns `IsolatedLaneTopologyV1`. It must not call
`apply_isolated_lane_topology_v1`.

No Membership processing. No Cap23 invocation. No Cap24 invocation.
No Trading-Core invocation.

## 8. Non-goals

```text
NO_PRODUCTIVE_MF_HOST_JOIN
NO_FIVE_LANE_CONTINUOUS_RUNTIME
NO_EXECUTION_CONCURRENCY
NO_MAX_POSITIONS_CHANGE
NO_ORDER_SUBMISSION
NO_POST_NETWORK_PERMIT_CHANGE
NO_CAP23_SEMANTIC_CHANGE
NO_CAP24_SEMANTIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_LANE_MAPPING_OWNER_CHANGE
```
