---
docs_token: DOCS_TOKEN_MASTER_V2_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1
status: active
scope: additive pure domain C2; mechanism-only; non-authorizing; no runtime activation
capability: MASTER_V2_DOUBLE_PLAY_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1
architecture_spec: MASTER_V2_DOUBLE_PLAY_ARCHITECTURE_DESIGN
last_updated: 2026-07-31
---

# Master V2 Double Play C2 — Directional Confirmation Progress V1

## 1. Purpose

Capability slice **C2** introduces a pure, deterministic confirmation-progress
mechanism that consumes C1 `ObservationAcceptanceResultV1` values and advances a
session-bound confirmation cursor exclusively on contiguous accepted DISTINCT
`MarketObservationEpoch` steps.

Component: `DirectionalConfirmationProgressV1`  
Purity: `PURE_DETERMINISTIC_NO_IO`  
Capability ID: `MASTER_V2_DOUBLE_PLAY_C2_DIRECTIONAL_CONFIRMATION_PROGRESS_V1`

Explicit slice flags:

- `RUNTIME_WIRING=false`
- `CONFIG_CHANGE=false`
- `DECISION_EPOCH_AUTHORITY=false`
- `VOLATILITY_SCOPE=false`
- `PARAMETER_RESEARCH=false`
- `IMPLICIT_RESUME_ALLOWED=false`

## 2. Authority Boundaries

| Authority | Owner | C2 role |
| --- | --- | --- |
| Distinct market observation acceptance | C1 `DistinctMarketObservationAcceptorV1` | sole observation authority; C2 never reclassifies market events |
| Confirmation progress cursor | C2 `evaluate_confirmation_progress_v1` | advances only when C1 reports DISTINCT + `strategy_advance_allowed=true` and epoch is prior+1 |
| DecisionEpoch | not owned by C2 | forbidden as confirmation-advance epoch |
| RuntimeCycle / receive time / poll rate | transport / runtime | never advance confirmation |

`MARKET_OBSERVATION_EPOCH` is the only confirmation-advance epoch.

## 3. State Model

### Types

| Type | Role |
| --- | --- |
| `ConfirmationSideV1` | LONG / SHORT |
| `ConfirmationAssessmentStateV1` | OBSERVE / CANDIDATE / CONFIRMED / INVALID |
| `ConfirmationAssessmentSignalV1` | OBSERVE / CANDIDATE / CONFIRMED |
| `ConfirmationProgressReasonCodeV1` | machine-readable progress / reject reasons |
| `ConfirmationProgressStateV1` | immutable session-bound progress state |
| `ConfirmationProgressInputV1` | pure evaluator input |
| `ConfirmationProgressResultV1` | atomic before/after result |

### ConfirmationProgressStateV1 fields

- `session_id`
- `venue`
- `instrument` (`InstrumentObservationKeyV1`)
- `side`
- `assessment_state`
- `latest_accepted_market_observation_epoch`
- `candidate_started_at_epoch`
- `distinct_confirmation_observation_count`
- `last_processed_acceptor_result_fingerprint`

### Invariants

- `session_id` and `venue` non-empty
- `count >= 0`
- OBSERVE ⇒ count == 0 and `candidate_started_at_epoch is None`
- CANDIDATE ⇒ count >= 1 and `candidate_started_at_epoch != None`
- CONFIRMED ⇒ count >= 1 and `candidate_started_at_epoch != None`
- INVALID is never silently treated as a valid progress state
- latest epoch non-negative per C1 `MarketObservationEpoch`

Initial state (`initial_confirmation_progress_state_v1`):

- assessment OBSERVE
- count 0
- epoch start `MarketObservationEpoch(0)` unless an explicit C1-aligned epoch is supplied

## 4. Progress Rules

Confirmation may advance only when all of the following hold:

1. C1 classification is DISTINCT
2. `strategy_advance_allowed == true`
3. current `MarketObservationEpoch` is exactly prior + 1
4. session, venue, instrument, and side match the prior state
5. acceptor-result fingerprint was not already processed
6. prior-state invariants are valid

Non-distinct C1 classifications:

- complete state unchanged
- `confirmation_advanced=false`
- `state_changed=false`
- no epoch-cursor advance
- reason `NON_DISTINCT_NOOP`

## 5. Transition Matrix

| Prior | Signal | Effect |
| --- | --- | --- |
| OBSERVE | OBSERVE | stay OBSERVE; count 0; epoch cursor advances |
| OBSERVE | CANDIDATE | → CANDIDATE; count 1; `candidate_started_at_epoch=current` |
| OBSERVE | CONFIRMED | count 1; → CONFIRMED iff threshold <= 1 else → CANDIDATE |
| CANDIDATE | CANDIDATE | count +1; → CONFIRMED iff count_after >= threshold else stay CANDIDATE |
| CANDIDATE | CONFIRMED | count +1; → CONFIRMED iff count_after >= threshold else stay CANDIDATE |
| CANDIDATE | OBSERVE | reset OBSERVE; count 0; `candidate_started_at_epoch=None` |
| CONFIRMED | CONFIRMED or CANDIDATE | hold CONFIRMED; count stable (`CONFIRMED_COUNT_POLICY=HOLD_STABLE`) |
| CONFIRMED | OBSERVE | reset OBSERVE; count 0; `candidate_started_at_epoch=None` |

`confirmation_threshold` is an explicit mechanism-test policy input only. C2 does
not bind configs and does not recommend productive threshold values.

## 6. Failure-Reason Matrix

| Reason | fail_closed | state mutation |
| --- | --- | --- |
| `NON_DISTINCT_NOOP` | false | none |
| `IDEMPOTENT_REPLAY` | false | none |
| `EPOCH_GAP` | true | none |
| `EPOCH_REGRESSION` | true | none |
| `SESSION_MISMATCH` | true | none |
| `INSTRUMENT_MISMATCH` | true | none |
| `VENUE_MISMATCH` | true | none |
| `SIDE_MISMATCH` | true | none |
| `STATE_INCONSISTENT` | true | none |
| `RUNTIME_CYCLE_NOT_OBSERVATION` | true | none |
| `RECEIVE_TIME_NOT_EPOCH` | true | none |
| `DECISION_EPOCH_FORBIDDEN` | true | none |
| `INVALID_THRESHOLD` | true | none |
| `INVALID_SIGNAL` | true | none |

Accepted-distinct success reasons:

- `ACCEPTED_DISTINCT_PROGRESS`
- `ACCEPTED_DISTINCT_RESET`
- `ACCEPTED_DISTINCT_CONFIRMED`
- `ACCEPTED_DISTINCT_HOLD_CONFIRMED`

## 7. Idempotency

Replaying the same acceptor-result fingerprint:

- complete state unchanged
- reason `IDEMPOTENT_REPLAY`
- not fail-closed
- no confirmation advance

## 8. Atomicity

- Result always carries full `state_before` / `state_after`
- Reject and fail-closed paths keep `state_after == state_before`
- No partial mutation
- No store or commit side effects in C2

## 9. Session / Restart Semantics

- State is strictly bound to `session_id`
- Session mismatch is fail-closed
- No restore/resume authority in C2
- No implicit loading of prior session states
- New sessions start only via `initial_confirmation_progress_state_v1`
- Serialization (`to_dict` / `from_dict`) is versioned data reconstruction only;
  restore is not resume authorization (`IMPLICIT_RESUME_ALLOWED=false`)

## 10. Poll-Rate Independence

Confirmation progress depends only on contiguous accepted DISTINCT
`MarketObservationEpoch` steps from C1. Variations of:

- runtime cycle index
- poll attempt
- receive time

do not advance confirmation when C1 does not accept a new DISTINCT observation.

Dedicated reject helpers prove:

- `RUNTIME_CYCLE_NOT_OBSERVATION`
- `RECEIVE_TIME_NOT_EPOCH`
- `DECISION_EPOCH_FORBIDDEN`

## 11. Conscious Non-Goals

C2 does **not**:

- wire into session runtime hot paths
- mutate configs or recommend productive thresholds
- implement DecisionEpoch
- perform volatility work
- start C3+ slices
- authorize orders, risk, safety, portfolio, testnet, or live trading
- introduce a second observation authority

## 12. Public Functions

- `initial_confirmation_progress_state_v1(...)`
- `evaluate_confirmation_progress_v1(input) -> result`
- `confirmation_progress_fingerprint_v1(...)`
- `reject_runtime_cycle_confirmation_advance_v1(...)`
- `reject_receive_time_confirmation_advance_v1(...)`
- `reject_decision_epoch_confirmation_advance_v1(...)`

## 13. Test Ownership

Canonical tests:

- `tests&#47;trading&#47;market_state&#47;test_directional_confirmation_progress_v1.py`

Implementation location (boundary-admissible, co-located with C1):

- `src&#47;trading&#47;market_state&#47;directional_confirmation_progress_v1.py`

Note: Placement under `market_state` (not `master_v2`) keeps
`CONFIG_CHANGE=false` while remaining admissible under the economic/diagnostic
optimization boundary guard, matching the C1 observation-authority package.

Covers initial state, contiguous distinct progress, non-distinct no-ops,
idempotency, epoch gap/regression, session/instrument/venue/side isolation,
LONG/SHORT isolation, poll/runtime/receive independence, DecisionEpoch reject,
transition matrix, serialization roundtrip, property tests, and determinism.
