---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_OCCUPIED_LANE_PIN_CONSUMER_JOIN_CONTRACT_V1
status: active
scope: Non-productive consume-recovered-topology then occupied-lane pin-build orchestration; no Cap23 write; no productive MF join; no five-lane runtime
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

# CURRENT MF N=5 Occupied-Lane Pin Consumer Join Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_OCCUPIED_LANE_PIN_CONSUMER
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_CURRENT_MF_N5_OCCUPIED_LANE_PIN_CONSUMER_JOIN_V1
CONTRACT_ID=CURRENT_MF_N5_OCCUPIED_LANE_PIN_CONSUMER_JOIN_CONTRACT_V1
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
PIN_BUILDER_OWNER=ops.current_mf_n5_isolated_lane_instance_topology_v1
RECOVERED_CONSUMER_OWNER=ops.current_mf_n5_recovered_topology_consumer_join_v1
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
`src&#47;ops&#47;current_mf_n5_occupied_lane_pin_consumer_join_v1&#47;consumer_v1.py`.

Recovered-topology consume remains:
`src&#47;ops&#47;current_mf_n5_recovered_topology_consumer_join_v1&#47;consumer_v1.py`.

Occupied-lane pin builder remains:
`src&#47;ops&#47;current_mf_n5_isolated_lane_instance_topology_v1&#47;topology_v1.py`.

This join does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, does
**not** write Cap 2.3 or Cap 2.4, and does **not** change Master V2 or
Double Play.

## 1. Purpose

Close the occupied-lane pin consumer seam on the current topology
returned by `#6595`:

```text
consume_recovered_isolated_lane_topology_v1(...)
        │
        ▼
current IsolatedLaneTopologyV1
        │
        ▼
build_occupied_lane_pins_v1(
  topology=<that exact object>,
  ranking_snapshot=<same current ranking object>
)
        │
        ▼
STOP — return dict[lane_id, GovernedCap23InstrumentPinV1]
```

The consumer sequences existing owners. It does not become a mapping
owner, persistence owner, pin owner, ranking owner, membership owner, or
selection owner.

## 2. Provenance

Pins MUST be built from the topology object returned by
`consume_recovered_isolated_lane_topology_v1` and the same
`ranking_snapshot` object supplied to that consume.

Recovered prior topology is not a pin-builder input. Alternate ranking,
relabel, fallback map, and partial pin-map authority are forbidden.

Same-universe ranking advance is already restamped onto the consume
return. Pin identity follows that current stamp.

## 3. Pin map

Keys are occupied `LANE_1..LANE_5` identities only. Empty lanes do not
acquire pins. Zero occupied lanes return `{}`. Values are existing
`GovernedCap23InstrumentPinV1` objects. This join does not invent a pin
type.

## 4. Writer dependency

The caller supplies an already-held
`DurableLaneAssignmentSingleWriterV1`. This module does not acquire or
release the writer lock and does not invent a second lock owner. The
writer is passed through to the recovered-topology consumer only.

## 5. Fail closed

Universe, ranking, digest, and state-root mismatch fail closed with the
existing pin-builder / adapter / recovered-consumer codes. This join
does not catch, remap, or convert those failures into an empty or
partial pin map.

Pin-builder failure after a successful consume does not roll back the
`#6595` checkpoint. This join does not own persistence rollback.

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
NO_CAP23_PRODUCE
NO_CAP23_PERSIST
NO_CAP24_SEMANTIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_LANE_MAPPING_OWNER_CHANGE
NO_PIN_ADAPTER_OWNER_CHANGE
NO_RECOVERED_CONSUMER_OWNER_CHANGE
NO_MF_SINGLE_EGRESS_REWIRE
NO_MEMBERSHIP_RUNTIME_CHANGE
```
