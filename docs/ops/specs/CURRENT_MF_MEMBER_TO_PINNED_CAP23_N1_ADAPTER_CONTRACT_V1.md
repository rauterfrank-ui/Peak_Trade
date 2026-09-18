---
docs_token: DOCS_TOKEN_CURRENT_MF_MEMBER_TO_PINNED_CAP23_N1_ADAPTER_CONTRACT_V1
status: active
scope: Additive governed Cap23 N=1 pin constraint from one same-universe Cap22 member identity; no five-lane runtime; no MF productive join; no execution concurrency
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

# CURRENT MF-Member to Pinned Cap23 N=1 Adapter Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_PIN_ADAPTER
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=CURRENT_MF_MEMBER_TO_PINNED_CAP23_N1_ADAPTER_CONTRACT_V1
CONTRACT_ID=CURRENT_MF_MEMBER_TO_PINNED_CAP23_N1_ADAPTER_CONTRACT_V1
AUTHORITY_EFFECT=NONE
PIN_IS_SELECTION_AUTHORITY=false
ADAPTER_MAY_WRITE_CAP23_SELECTION=false
ADAPTER_MAY_RERANK=false
ADAPTER_MAY_RESELECT=false
MF_PRODUCTIVE_JOIN=false
FIVE_LANE_RUNTIME_CREATED=false
EXECUTION_CONCURRENCY_AUTHORIZED=false
MAX_POSITIONS_EFFECTIVE=1
MF_SINGLE_EGRESS_REWIRED=false
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

Typed pin object: `src&#47;ops&#47;single_selected_future_policy_v1&#47;governed_pin_v1.py`.

Typed adapter (pin factory only):
`src&#47;ops&#47;current_mf_member_to_pinned_cap23_n1_adapter_v1&#47;adapter_v1.py`.

Cap 2.3 remains the sole writer of `SingleSelectedFutureSelectionV1`.

This persist does **not** rewire `MF_SINGLE_EGRESS_V1`, does **not** join
MF runtime, does **not** create five isolated executing lanes, and does
**not** change Master V2 or Double Play.

## 1. Purpose

Allow one canonical instrument identity from the reusable POLICY_A N&lt;=5
membership **concept** to constrain one isolated Cap 2.3 N=1 lane, using
the **same** productive Cap 2.2 ranking snapshot from which that member
was derived.

```text
same-universe Cap22 full snapshot
+ canonical instrument_id
+ isolated lane state_root
→ non-authoritative GovernedCap23InstrumentPinV1
→ Cap23 produce_single_selected_future_v1 (optional pin)
→ existing SingleSelectedFutureSelectionV1
→ existing Cap24 BoundInstrumentV1
```

Default Cap 2.3 call with `governed_pin=None` remains the CURRENT global
first-eligible path.

## 2. Universe isolation

Canonical same-universe proof reuses existing Cap 2.2 fields:

```text
CANONICAL_UNIVERSE_IDENTITY_SOURCE=ProductiveFuturesRankingSnapshotV1.universe_snapshot_id
PIN_UNIVERSE_BINDING=universe_snapshot_id+ranking_snapshot_id+integrity_digest
```

A pin is valid only when all of the following match the **full** Cap 2.2
snapshot consumed by that Cap 2.3 call:

- `universe_snapshot_id`
- `ranking_snapshot_id`
- `integrity_digest`
- canonical instrument present and `ELIGIBLE` in that snapshot
- unique `venue_native_id` resolved from that same snapshot row
- `lane_state_root` binding

Instrument identity alone is not sufficient.

No second ranking may be used as replacement, fallback, underfill,
challenger, alternate pin, or recovery candidate. No ranking snapshots
from different universes may be merged or compared to create selection
authority.

## 3. Pin versus existing Cap 2.3 policy

The pin replaces only the candidate **proposal** (`_pick_top_eligible`
when unpinned). After a valid pin resolves one full-snapshot row, existing
Cap 2.3 policy is unchanged:

```text
PIN_VS_PREVIOUS_SELECTION=EXISTING_CAP23_SWITCH_LOGIC
PIN_VS_HYSTERESIS=PRESERVED
PIN_VS_MIN_HOLDING=PRESERVED
PIN_VS_REPLACEMENT_PENDING=PRESERVED
PIN_VS_OPEN_POSITION=PRESERVED
```

The pin does not force an immediate instrument switch when min-holding,
hysteresis, open-position, or `REPLACEMENT_PENDING` / `SELECTED_EXIT_ONLY`
would retain or degrade the previous instrument on that lane.

## 4. Non-goals

```text
NO_FILTERED_RANKING_SNAPSHOT
NO_ADAPTER_WRITTEN_CAP23_DTO
NO_CAP24_MUTATION
NO_MASTER_V2_MUTATION
NO_DOUBLE_PLAY_MUTATION
NO_MAX_POSITIONS_CHANGE
NO_EXECUTION_CONCURRENCY
NO_AS05_CONTINUATION
NO_MF_SINGLE_EGRESS_REWIRE
```
