---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_ISOLATED_LANE_INSTANCE_TOPOLOGY_CONTRACT_V1
status: active
scope: Non-trading lane-instance topology mapping governed same-universe MF POLICY_A membership onto at most five isolated Single-Future lane identities; no productive MF join; no five-lane runtime; no execution concurrency
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

# CURRENT MF N=5 Isolated Lane-Instance Topology Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_LANE_TOPOLOGY
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=CURRENT_MF_N5_ISOLATED_LANE_INSTANCE_TOPOLOGY_V1
CONTRACT_ID=CURRENT_MF_N5_ISOLATED_LANE_INSTANCE_TOPOLOGY_CONTRACT_V1
AUTHORITY_EFFECT=NONE
LANE_TOPOLOGY_RANKING_AUTHORITY=false
LANE_TOPOLOGY_MEMBERSHIP_AUTHORITY=false
LANE_TOPOLOGY_CAP23_SELECTION_AUTHORITY=false
LANE_TOPOLOGY_CAP24_BINDING_AUTHORITY=false
LANE_TOPOLOGY_TRADING_AUTHORITY=false
LANE_TOPOLOGY_EXECUTION_AUTHORITY=false
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
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
PURE_RANK_REORDER_CAUSES_LANE_MOVE=false
ONE_INSTRUMENT_PER_LANE=true
ONE_LANE_PER_INSTRUMENT=true
DURABLE_TOPOLOGY_PERSISTENCE_IMPLEMENTED=false
ATLAS_AUTHORITY=NONE
```

Typed mapping:
`src&#47;ops&#47;current_mf_n5_isolated_lane_instance_topology_v1&#47;topology_v1.py`.

This persist does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, and does
**not** change Cap 2.3, Cap 2.4, Master V2, or Double Play.

## 1. Purpose

Represent up to five mutually isolated Single-Future lane instances from
the existing same-universe MF POLICY_A membership.

```text
MF_MEMBERSHIP_CONTEXT_V1
AT_MOST_N=5
        │
        ▼
bounded lane-instance topology
        │
   ┌────┼────┬────┬────┐
   ▼    ▼    ▼    ▼    ▼
LANE_1 LANE_2 LANE_3 LANE_4 LANE_5
   │    │    │    │    │
occupied lanes consume existing #6592 governed pin
   │
Cap23 remains sole N=1 selection writer
```

Target architecture remains five isolated Single-Future cores, not one
Multi-Future trading core. This contract stops before productive
orchestration and runtime activation.

## 2. Lane identity

CURRENT reusable isolation key remains Cap23 `lane_state_root`.
No pre-existing opaque five-lane identifier existed on origin&#47;main.

This contract introduces bounded opaque lane IDs:

```text
LANE_1 LANE_2 LANE_3 LANE_4 LANE_5
```

Lane ID does not encode rank, instrument, direction, strategy, or
execution priority. Rank order is not lane identity.

Each lane has a reserved state_root namespace:

```text
{topology_state_root_base}&#47;{lane_id}
```

resolved by the existing `lane_state_root_key` primitive.

## 3. Cardinality

```text
MAX_LANE_COUNT=5
ACTIVE_LANES=0..5
NO_PADDING=true
```

Unused lanes remain `EMPTY`. Empty lanes are not filled from another
universe or from ranking candidates outside the governed membership.

## 4. Membership versus lane mapping

Membership admission, removal, hysteresis, and challenger eligibility
remain upstream MF POLICY_A &#47; rotation semantics.

This layer consumes only the governed resulting membership and an optional
explicit prior topology. It does not call Cap23 `_pick_top_eligible` and
does not fabricate `SingleSelectedFutureSelectionV1`.

## 5. Assignment policy

```text
INITIAL_ASSIGNMENT_POLICY=BOOTSTRAP_PREFIX_FILL_LOWEST_LANE_IDS_FROM_MEMBERSHIP_ORDER
RETAINED_MEMBER_POLICY=KEEP_EXISTING_LANE_ID
EXIT_POLICY=RELEASE_LANE_TO_EMPTY
ENTRY_POLICY=ASSIGN_DETERMINISTIC_AVAILABLE_LANE
FREE_LANE_ASSIGNMENT_POLICY=LOWEST_EMPTY_LANE_ID_IN_LANE_1_TO_LANE_5_ORDER_THEN_ENTERED_ORDER_FROM_CURRENT_MEMBERSHIP_DELTA
```

A pure Cap22 ranking reorder of an unchanged membership set must not move
incumbent instruments between lanes.

Released-lane reuse is the consequence of filling the lowest empty
`LANE_1..LANE_5` slot. It is not ranking-based migration.

## 6. Restart

Lane assignment cannot be reconstructed from membership order or ranking
order, because rank is not lane identity.

```text
RESTART_RECONSTRUCTION_POLICY=FAIL_CLOSED_WITHOUT_EXPLICIT_PRIOR_TOPOLOGY_NO_MEMBERSHIP_OR_RANKING_RECONSTRUCTION
DURABLE_TOPOLOGY_PERSISTENCE_IMPLEMENTED=false
```

A non-bootstrap membership without an explicit prior topology fails
closed. This contract does not invent a durable topology store.

## 7. Universe isolation

Every occupied lane remains bound to the same productive Cap22
universe&#47;ranking identity that produced the membership:

```text
universe_snapshot_id
ranking_snapshot_id
integrity_digest
```

Instrument identity alone is not sufficient to cross a universe or
context boundary. Duplicate instrument occupancy fails closed.

## 8. State isolation

Lane-namespaced (already reusable via `state_root`):

- Cap23 selection persistence
- Cap24 consumption of that selection root
- per-lane runtime cursors that already live under that root

Global and must not be duplicated by this topology:

- account equity
- `MAX_POSITIONS_EFFECTIVE=1`
- execution host &#47; send
- order lifecycle
- cycle occupancy
- kill switch
- shared Cap22 ranking snapshot
- shared Cap21 universe snapshot

## 9. Pin consumption

Each occupied lane may build a valid existing #6592
`GovernedCap23InstrumentPinV1` for its assigned member and
`lane_state_root`. Cap23 remains the sole writer of
`SingleSelectedFutureSelectionV1`. The unpinned Cap23 default path is
unchanged.

## 10. Non-goals

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
NO_DURABLE_TOPOLOGY_STORE
```
