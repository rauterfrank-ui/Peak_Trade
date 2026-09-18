---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_RANKING_DOMAIN_OCCUPIED_LANE_CAP23_N1_PRODUCE_JOIN_CONTRACT_V1
status: active
scope: Non-productive Ranking-domain occupied-lane pin consume then isolated Cap23 N=1 produce/persist; no Cap24; no productive MF join; no five-lane runtime
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

# CURRENT MF N=5 Ranking-Domain Occupied-Lane Cap23 N=1 Produce Join Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_RANKING_DOMAIN_CAP23_PRODUCE_JOIN
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_CURRENT_MF_N5_RANKING_DOMAIN_OCCUPIED_LANE_CAP23_N1_PRODUCE_JOIN_V1
CONTRACT_ID=CURRENT_MF_N5_RANKING_DOMAIN_OCCUPIED_LANE_CAP23_N1_PRODUCE_JOIN_CONTRACT_V1
AUTHORITY_EFFECT=NONE
JOIN_RANKING_AUTHORITY=false
JOIN_MEMBERSHIP_AUTHORITY=false
JOIN_MAPPING_AUTHORITY=false
JOIN_PERSISTENCE_AUTHORITY=false
JOIN_PIN_AUTHORITY=false
JOIN_CAP23_SELECTION_AUTHORITY=false
JOIN_CAP24_BINDING_AUTHORITY=false
JOIN_TRADING_AUTHORITY=false
JOIN_EXECUTION_AUTHORITY=false
LANE_MAPPING_OWNER=ops.current_mf_n5_isolated_lane_instance_topology_v1
PIN_CONSUMER_OWNER=ops.current_mf_n5_occupied_lane_pin_consumer_join_v1
CAP23_SELECTION_OWNER=ops.single_selected_future_policy_v1
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
FIVE_LANE_CONTINUOUS_HOST_JOIN=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
HOST_JOIN=false
MF_SINGLE_EGRESS_REWIRED=false
PARALLEL_AUTHORITY_CREATED=false
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
`src&#47;ops&#47;current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1&#47;produce_join_v1.py`.

Occupied-lane pin consume remains:
`src&#47;ops&#47;current_mf_n5_occupied_lane_pin_consumer_join_v1&#47;consumer_v1.py`.

Cap 2.3 N=1 produce/persist remains:
`src&#47;ops&#47;single_selected_future_policy_v1&#47;producer_v1.py`.

This join does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, does
**not** call Cap 2.4, and does **not** change Master V2 or Double Play.

## 1. Purpose

Close the Ranking-domain occupied-lane Cap 2.3 N=1 produce/persist seam
on the pin map returned by `#6596`:

```text
consume_occupied_lane_pins_v1(...)
        │
        ▼
dict[lane_id, GovernedCap23InstrumentPinV1]
        │
        ▼
for each occupied LANE_1..LANE_5:
  existing lane_state_root
  + governed_pin
  → run_single_selected_future_policy_v1
        │
        ▼
STOP — dict[lane_id, SingleSelectedFutureSelectionV1]
```

The join sequences existing owners. It does not become a ranking owner,
membership owner, mapping owner, pin owner, or selection owner. Cap 2.3
remains `LAST_RANKING_UNIVERSE_AUTHORITY` and the sole writer of
`SingleSelectedFutureSelectionV1`.

N=5 here means up to five independently prepared Ranking-domain N=1
lane selections. It does not mean five productively active Futures,
five concurrent positions, or five executing lanes.

## 2. Provenance and isolation

Pins MUST come from `consume_occupied_lane_pins_v1` using the same
`ranking_snapshot` object later passed to Cap 2.3.

Each occupied lane uses its existing namespaced `lane_state_root`
(`{topology_state_root_base}&#47;{lane_id}`). Lane/root mismatch fails
closed with the existing Cap 2.3 pin lane-binding code. Previous
selection, hysteresis, min-holding, and replacement-pending state are
loaded only from that root (`load_previous_from_state=True`).

## 3. Result map

Keys are occupied `LANE_1..LANE_5` identities only, in existing
`LANE_IDS` order. Empty lanes do not invoke Cap 2.3. Zero occupied
lanes return `{}`. Values are existing `SingleSelectedFutureSelectionV1`
objects, including Cap 2.3 domain denies such as `NO_SELECTION`.

Persisted Cap 2.3 files remain under each occupied `lane_state_root`.

## 4. Writer dependency

The caller supplies an already-held
`DurableLaneAssignmentSingleWriterV1`. This module does not acquire or
release that lock. Cap 2.3 remains the owner of its per-root selection
writer.

## 5. Fail closed

`#6596` / pin / root exceptions propagate. This join does not catch,
remap, or convert them into an empty or partial result map.

A complete Cap 2.3 SSF, including `ok=false` / `NO_SELECTION`, is a
finished isolated N=1 result. It is stored under that lane key.
Remaining occupied lanes continue.

Cap 2.3 `selection is None` fails closed with
`RankingDomainOccupiedLaneCap23ProduceJoinError`. No partial dict is
returned. Already-written foreign Cap 2.3 roots are not rolled back.
This join does not own Cap 2.3 persistence rollback.

Cap 2.3 raises: propagate.

## 6. Non-goals

```text
NO_PRODUCTIVE_MF_HOST_JOIN
NO_FIVE_LANE_CONTINUOUS_RUNTIME
NO_FIVE_LANE_RUNTIME_CREATED
NO_EXECUTION_CONCURRENCY
NO_MAX_POSITIONS_CHANGE
NO_ORDER_SUBMISSION
NO_POST_NETWORK_PERMIT_CHANGE
NO_CAP23_SEMANTIC_CHANGE
NO_CAP24_INVOCATION
NO_BOUND_INSTRUMENT_CONSTRUCTION
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_MULTI_FUTURE_CAP23
NO_PIN_AS_SELECTION_AUTHORITY
NO_MEMBERSHIP_HANDOFF_AUTHORITY
NO_MF_SINGLE_EGRESS_REWIRE
```
