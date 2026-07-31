---
docs_token: DOCS_TOKEN_MASTER_V2_C3_DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1
status: active
scope: additive pure domain C3; confirmation integration; non-authorizing; no runtime activation
capability: DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1
architecture_spec: MASTER_V2_DOUBLE_PLAY_ARCHITECTURE_DESIGN
last_updated: 2026-07-31
---

# Master V2 Double Play C3 — Directional Assessment Confirmation Integration V1

## 1. Purpose

Capability slice **C3** integrates C1 observation acceptance results into the C2
confirmation-progress mechanism and maps the resulting side-isolated cursor onto
the existing Master V2 Directional Assessment status contract.

```
CAPABILITY_ID=DIRECTIONAL_ASSESSMENT_CONFIRMATION_INTEGRATION_V1
INPUT_AUTHORITY=C1
PROGRESS_AUTHORITY=C2
STATE_OWNER=C3
BULL_BEAR_ISOLATED=true
PERSISTENCE_BOUNDARY=CALLER_OWNED_IN_MEMORY_EXPLICIT_REPLAY_CARRIER
IMPLICIT_RESUME_ALLOWED=false
POLL_RATE_INDEPENDENT=true
RUNTIME_WIRING_INCLUDED=false
PARAMETER_CHANGE_INCLUDED=false
VOLATILITY_CHANGE_INCLUDED=false
PARALLEL_CONFIRMATION_AUTHORITY_FORBIDDEN=true
```

Component: `DirectionalAssessmentConfirmationIntegrationV1`  
Purity: `PURE_DETERMINISTIC_NO_IO`

## 2. Authority Boundaries

| Authority | Owner | C3 role |
| --- | --- | --- |
| Distinct market observation | C1 | sole observation authority; consumed as atomic result |
| Confirmation progress cursor | C2 | sole progress evaluator |
| Side-state carrier | C3 | owns Bull/Bear `ConfirmationProgressStateV1` pair |
| Downstream status contract | `DirectionalAssessmentV1.status` | unchanged enum / fields |
| Legacy trading_epoch counter | quarantined | not productive confirmation authority |
| Lossy cross-side projector | quarantined | raises if called |

## 3. State Carrier

`DirectionalConfirmationSideStateCarrierV1`:

- `bull_confirmation_state: ConfirmationProgressStateV1` (`side=LONG`)
- `bear_confirmation_state: ConfirmationProgressStateV1` (`side=SHORT`)

Session binding fields (per side state):

- `session_id`
- `venue`
- `InstrumentObservationKeyV1`
- `ConfirmationSideV1`

Initialization exclusively via `initial_confirmation_progress_state_v1` /
`initial_directional_confirmation_side_state_carrier_v1`.

## 4. Rules

### Initialization Rule

New sessions start empty OBSERVE on both sides. No implicit resume across process
or session boundaries (`IMPLICIT_RESUME_ALLOWED=false`).

### Advance Rule

C2 may evaluate/progress only when C1 reports `DISTINCT` +
`strategy_advance_allowed=true` and `MarketObservationEpoch == prior + 1`.

### Reset Rule

`ConfirmationAssessmentSignalV1.OBSERVE` → reset OBSERVE, count=0,
`candidate_started_at_epoch=None`.

### Idempotency Rule

Identical acceptor-result fingerprint → `IDEMPOTENT_REPLAY`, no progress.

### Bull/Bear Isolation Rule

Long updates mutate only bull state; short updates mutate only bear state.
Opposite side remains value-identical.

## 5. Signal Mapping

Existing DA signal strength and thresholds are reused unchanged:

| Signal strength | C2 assessment signal |
| --- | --- |
| `< candidate_signal_threshold` | `OBSERVE` |
| `>= candidate` and `< confirmation` | `CANDIDATE` |
| `>= confirmation_signal_threshold` | `CONFIRMED` |

`confirmation_threshold` passed to C2 equals existing `policy.confirmation_epochs`
(no value change).

## 6. Status Mapping

| C2 `ConfirmationAssessmentStateV1` | `DirectionalAssessmentStatus` |
| --- | --- |
| OBSERVE | OBSERVE |
| CANDIDATE | CANDIDATE |
| CONFIRMED | CONFIRMED |
| INVALID | INVALID |

Gate / binding failures map to existing `INVALID` / `BLOCKED`. No new `REJECTED`
status is introduced.

## 7. Failure Matrix

| Condition | Effect |
| --- | --- |
| NON_DISTINCT | no progress; prior state status |
| IDEMPOTENT_REPLAY | no progress; identical result |
| SESSION/VENUE/INSTRUMENT/SIDE mismatch | fail-closed BLOCKED/INVALID |
| EPOCH_GAP / EPOCH_REGRESSION | fail-closed |
| RuntimeCycle / ReceiveTime / DecisionEpoch as epoch | explicit reject helpers |
| Parallel legacy confirmation authority | `ParallelConfirmationAuthorityErrorV1` |

## 8. Productive Wiring

`run_integrated_offline_trading_logic_replay_v1` evaluates Bull and Bear exclusively
via:

`evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1`

When C3 carrier / C1 result are omitted, offline replay resolves:

- initial empty OBSERVE carrier
- explicit NON_DISTINCT acceptor placeholder

It never invents DISTINCT and never consults
`DirectionalConfirmationStateV1` for status.

## 9. Downstream Compatibility

Unchanged consumers:

- Survival Assessment
- Suitability Binding
- Double-Play Composition Matrix
- Switch / Transition State
- Entry / Exit policy

For equal final `DirectionalAssessmentV1.status` values, downstream semantics remain
unchanged.

## 10. Parallel Authority Elimination

Evidence that no parallel confirmation authority remains:

1. Productive replay AST must not call `evaluate_directional_assessment_v1`
2. Productive replay must call the C3 bull/bear integrator
3. `project_directional_confirmation_state_from_assessments_v1` raises
   `LEGACY_LOSSY_CROSS_SIDE_PROJECTOR_AUTHORITY_FORBIDDEN`
4. Bar-sequence projection reads `directional_confirmation_progress_after` only
5. `assert_c3_confirmation_authority_exclusive_v1` fail-closed on legacy enablement

## 11. Conscious Non-Goals

C3 does **not**:

- wire runtime / wallclock bridges
- mutate configs or thresholds
- change volatility
- rebuild Survival / Suitability / Composition / Switch semantics
- authorize orders, testnet, or live trading
- implement C4 (see `MV2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1.md`)

## 12. Test Ownership

Canonical tests:

- `tests&#47;trading&#47;master_v2&#47;test_directional_assessment_confirmation_integration_v1.py`

Plus C1/C2/DA/replay/double-play regressions.

Post-C3 binding ownership continues in C4:
`POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1`.
