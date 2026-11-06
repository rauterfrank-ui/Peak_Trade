---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_RECOVERED_TOPOLOGY_CONSUMER_JOIN_CONTRACT_V1
status: active
scope: Non-productive recover→apply→persist orchestration of recovered IsolatedLaneTopologyV1 into the existing #6593 mapping owner; no lane mapping; no productive MF join; no five-lane runtime
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

# CURRENT MF N=5 Recovered Topology Consumer Join Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_RECOVERED_TOPOLOGY_CONSUMER
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_CURRENT_MF_N5_RECOVERED_TOPOLOGY_CONSUMER_JOIN_V1
CONTRACT_ID=CURRENT_MF_N5_RECOVERED_TOPOLOGY_CONSUMER_JOIN_CONTRACT_V1
AUTHORITY_EFFECT=NONE
CONSUMER_RANKING_AUTHORITY=false
CONSUMER_MEMBERSHIP_AUTHORITY=false
CONSUMER_MAPPING_AUTHORITY=false
CONSUMER_PERSISTENCE_AUTHORITY=false
CONSUMER_CAP23_SELECTION_AUTHORITY=false
CONSUMER_CAP24_BINDING_AUTHORITY=false
CONSUMER_TRADING_AUTHORITY=false
CONSUMER_EXECUTION_AUTHORITY=false
LANE_MAPPING_OWNER=ops.current_mf_n5_isolated_lane_instance_topology_v1
PERSISTENCE_OWNER=ops.current_mf_n5_durable_lane_assignment_persistence_v1
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
FIVE_LANE_CONTINUOUS_HOST_JOIN=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
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

Typed orchestrator:
`src&#47;ops&#47;current_mf_n5_recovered_topology_consumer_join_v1&#47;consumer_v1.py`.

Lane mapping remains:
`src&#47;ops&#47;current_mf_n5_isolated_lane_instance_topology_v1&#47;topology_v1.py`.

Durable custody remains:
`src&#47;ops&#47;current_mf_n5_durable_lane_assignment_persistence_v1&#47;persistence_v1.py`.

This join does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, and does
**not** change Cap 2.3, Cap 2.4, Master V2, or Double Play.

## 1. Purpose

Close the recovered-topology consumer seam:

```text
recover IsolatedLaneTopologyV1 | None
        │
        ▼
apply_isolated_lane_topology_v1(prior_topology=...)
        │
        ▼
persist validated IsolatedLaneTopologyV1
        │
        ▼
STOP — return topology
```

The consumer sequences existing owners. It does not become a mapping
owner, persistence owner, ranking owner, membership owner, or selection
owner.

## 2. Mode derivation

```text
membership.bootstrap=true  → recovery_mode=BOOTSTRAP
membership.bootstrap=false → recovery_mode=RESTART
```

Mode is not inferred from commit absence. Missing restart therefore
cannot become `prior_topology=None` via a bootstrap recover.

## 3. Bootstrap

```text
recover(topology_state_root_base, BOOTSTRAP)
  no expected_universe_snapshot_id
  no expected_ranking_snapshot_id
  no expected_ranking_integrity_digest
→ None
→ apply(prior_topology=None)
→ persist
→ return
```

Prior artifacts present fail closed at recover
(`LANE_ASSIGNMENT_BOOTSTRAP_WITH_PRIOR_COMMIT`). Apply is not invoked.

## 4. Restart

```text
recover(
  topology_state_root_base,
  RESTART,
  expected_universe_snapshot_id=ranking_snapshot["universe_snapshot_id"],
)
  expected_ranking_snapshot_id omitted
  expected_ranking_integrity_digest omitted
→ exact IsolatedLaneTopologyV1
→ apply(prior_topology=<that object>)
→ persist
→ return
```

Same-universe ranking advance is handled by the mapping owner restamping
provenance. Recover must not bind current ranking identity.

Restart recover returning `None` is fail closed. Lane identity is not
reconstructed from membership order or ranking.

## 5. Writer dependency

The caller supplies an already-held
`DurableLaneAssignmentSingleWriterV1`. This module does not acquire or
release the writer lock and does not invent a second lock owner.

## 6. Fail closed

Missing restart, bootstrap-with-prior, partial write, corrupt / malformed
/ schema / digest failure, universe or state-root mismatch, and
bootstrap/commit disagreement propagate as the underlying owner error.
No catch converts those failures into `prior_topology=None`.

## 7. Non-goals

```text
NO_PRODUCTIVE_MF_HOST_JOIN
NO_FIVE_LANE_CONTINUOUS_RUNTIME
NO_FIVE_LANE_RUNTIME_CREATED
NO_EXECUTION_CONCURRENCY
NO_MAX_POSITIONS_CHANGE
NO_ORDER_SUBMISSION
NO_POST_NETWORK_PERMIT_CHANGE
NO_CAP23_SEMANTIC_CHANGE
NO_CAP24_SEMANTIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_LANE_MAPPING_OWNER_CHANGE
NO_PIN_CONSUMPTION
NO_MF_SINGLE_EGRESS_REWIRE
```
