---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_C1_DISTINCT_MARKET_OBSERVATION_ACCEPTOR_V1
status: active
scope: additive pure domain C1; non-authorizing; no runtime activation
capability: MASTER_V2_DOUBLE_PLAY_C1_DISTINCT_MARKET_OBSERVATION_ACCEPTOR_V1
architecture_spec: MASTER_V2_DOUBLE_PLAY_ARCHITECTURE_DESIGN
last_updated: 2026-07-31
---

# Master V2 Double Play C1 — Distinct Market Observation Acceptor V1

## 1. Purpose

Capability slice **C1** introduces a pure, deterministic acceptor that decides whether a normalized public market observation is a new **DISTINCT** market observation for strategy-advance purposes.

Component: `DistinctMarketObservationAcceptorV1`  
Purity: `PURE_DETERMINISTIC_NO_IO`

This slice does **not** activate runtime, confirmation, volatility, timers, strategy evaluation, risk, safety, portfolio mutation, orders, testnet, or live trading.

## 2. Domain Types

| Type | Role |
| --- | --- |
| `MarketObservationEpoch` | Opaque non-negative epoch; advances by exactly 1 only on DISTINCT |
| `InstrumentObservationKeyV1` | Ownership key: venue + canonical_instrument_id + venue_instrument_id |
| `ObservationIdentityV1` | Distinctness authority identity |
| `ObservationTransportMetadataV1` | Receive/poll/runtime transport metadata (non-authority) |
| `ObservationCandidateV1` | Evaluator input (may carry invalid market fields) |
| `ObservationAcceptanceStateV1` | Immutable instrument-bound state |
| `ObservationAcceptanceResultV1` | Classification + advance decision + before/after state |
| `ObservationClassification` | DISTINCT / DUPLICATE / OUT_OF_ORDER / IDENTITY_CONFLICT / INVALID_EVENT_TIME / INVALID_MARK / TRANSPORT_ONLY_DUPLICATE |

### MarketObservationEpoch invariants

- `value >= 0`
- no implicit `RuntimeCycleIndex` conversion
- no implicit `DecisionEpoch` conversion
- no advance from receive time, poll rate, or wallclock

### ObservationIdentityV1 distinctness fields

- `venue`
- `canonical_instrument_id`
- `venue_instrument_id`
- `venue_event_time`
- `mark_price`

### Explicitly NOT distinctness authority

- `receive_time`
- `runtime_cycle_index`
- `poll_attempt`
- `wallclock_now`
- `heartbeat_sequence`
- `transport_latency`

## 3. Identity Rules

1. Identity is derived from already-normalized public market data (`NormalizedPublicMarketDataV1` mapping helper).
2. Venue event time is the only event-time authority. Receive time must not substitute a missing venue event time.
3. Mark price must be finite and `> 0`.
4. Instrument binding is mandatory for ownership: a foreign instrument against a bound state is `IDENTITY_CONFLICT`, never a shared DISTINCT advance.
5. Same venue/instrument/event identity with conflicting mark is `IDENTITY_CONFLICT`.

## 4. Classification Priority

First match wins after constructing the candidate:

1. `INVALID_EVENT_TIME`
2. `INVALID_MARK`
3. `IDENTITY_CONFLICT` (venue / instrument / canonical mapping / mark conflict)
4. `OUT_OF_ORDER`
5. `TRANSPORT_ONLY_DUPLICATE`
6. `DUPLICATE`
7. `DISTINCT`

Only `DISTINCT` sets `strategy_advance_allowed=true`.

## 5. State Invariants

Initial state:

- `last_accepted_observation_identity=None`
- `market_observation_epoch=0`

On DISTINCT:

- update `last_accepted_observation_identity`
- advance `market_observation_epoch` by exactly 1
- bind `bound_instrument_key` to the accepted instrument key

On all non-DISTINCT classifications:

- `state_after == state_before`
- `strategy_advance_allowed=false`
- `NO_STATE_MUTATION=true`

## 6. Atomicity

Evaluator purity:

- `EVALUATOR_MUTATES_EXTERNAL_STATE=false`
- `CALLER_COMMIT_REQUIRED=true`

Additive commit helper `commit_observation_acceptance_v1`:

- manages only C1 state
- compare-before/after snapshot semantics
- rejects partial writes

Commit group:

- `last_accepted_observation_identity`
- `market_observation_epoch`

Forbidden:

- `PARTIAL_COMMIT_ALLOWED=false`
- `EPOCH_ADVANCE_WITHOUT_IDENTITY_COMMIT_ALLOWED=false`
- `IDENTITY_COMMIT_WITHOUT_EPOCH_ADVANCE_ALLOWED=false`

## 7. Multi-Instrument Isolation

Even under current single-instrument productive scope (`SINGLE_INSTRUMENT_OKX_EEA_PUBLIC_MARK_DATA`), state is instrument-keyed:

- venue
- canonical_instrument_id
- venue_instrument_id

There is no global shared epoch across instruments. Cross-instrument evaluation against a bound state yields `IDENTITY_CONFLICT`.

## 8. Existing Field Mapping

| EXISTING_FIELD | TARGET_IDENTITY_FIELD | AUTHORITY | VALIDATION | DISTINCTNESS_RELEVANCE |
| --- | --- | --- | --- | --- |
| `venue` | `venue` | VenueInstrumentMappingV1 / NormalizedPublicMarketDataV1 | non-empty str | yes |
| `canonical_instrument_id` | `canonical_instrument_id` | canonical instrument authority | non-empty str | yes |
| `venue_instrument_id` | `venue_instrument_id` | venue transport identity | non-empty str | yes |
| `event_ts_unix` | `venue_event_time` | PublicMarkPriceV1 venue event timestamp | finite, `> 0` | yes |
| `mark_px` | `mark_price` | PublicMarkPriceV1 markPx | finite, `> 0` | yes |
| `receive_ts_unix` | transport `receive_time` | transport receive clock | optional transport meta | no |
| poll / runtime / heartbeat / latency | transport metadata | caller-supplied transport | optional | no |

No second observation authority is introduced. No new venue source. No new transport logic.

## 9. Slice Boundaries (C1)

Allowed:

- additive pure domain module under `src&#47;trading&#47;market_state&#47;`
- additive commit helper for C1 state only
- additive trading_epoch compatibility validator proving alias target `MarketObservationEpoch` and rejecting runtime-cycle assignment
- unit / property / determinism tests
- this technical specification

Not allowed / explicitly not done:

- session runtime hot-path wiring
- hardening bridge cutover
- confirmation / directional assessment / volatility changes
- PT1M bar builder
- clock or timer migration
- double-play state change
- entry/exit / risk / safety / portfolio changes
- config / parameter / governance redefinition
- runtime activation, orders, testnet, live

Compatibility note:

- `trading_epoch` may alias conceptually to `MarketObservationEpoch`
- productive callers are **not** migrated in C1
- `runtime_cycle_assignment_rejected=true`

## 10. Later Slice Dependencies (not started)

| Slice | Depends on C1 | Status in this PR |
| --- | --- | --- |
| C2 | Accepted DISTINCT observation stream / epoch ownership | not started |
| C3 | Observation-gated confirmation inputs | not started |
| C4 | Volatility / bar coupling to observation epoch | not started |
| C5 | Timer / clock migration around observation epoch | not started |
| C6 | Strategy evaluator advance wiring | not started |
| C7 | Risk / safety observation gates | not started |
| C8 | Portfolio / runtime integration | not started |
| C9 | End-to-end activation / promotion surfaces | not started |

`C2_STARTED=false` … `C9_STARTED=false`

## 11. Reason Codes

Stable machine-readable reason codes include:

- `observation_accepted_distinct`
- `observation_accepted_distinct_initial`
- `observation_duplicate`
- `observation_transport_only_duplicate`
- `observation_out_of_order`
- `observation_identity_conflict_venue`
- `observation_identity_conflict_instrument`
- `observation_identity_conflict_canonical_mapping`
- `observation_identity_conflict_mark`
- `observation_invalid_event_time_missing`
- `observation_invalid_event_time_non_finite`
- `observation_invalid_event_time_non_positive`
- `observation_invalid_mark_missing`
- `observation_invalid_mark_non_finite`
- `observation_invalid_mark_non_positive`

Programming/contract faults (for example commit compare mismatch, runtime-cycle assignment) raise errors and are not swallowed as ordinary market classifications.

## 12. Test Ownership

Canonical tests:

- `tests&#47;trading&#47;market_state&#47;test_distinct_market_observation_acceptor_v1.py`

Covers initial state, DISTINCT/DUPLICATE/TRANSPORT_ONLY/OUT_OF_ORDER/IDENTITY_CONFLICT/INVALID_*, multi-instrument isolation, atomicity, epoch monotonicity properties, poll-rate independence, serialization roundtrip, and trading_epoch compatibility rejection of runtime cycles.
