---
docs_token: DOCS_TOKEN_MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1
status: active
scope: additive pure domain time/sample/epoch semantics; non-authorizing; no runtime activation
capability: MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1
architecture_spec: MASTER_V2_DOUBLE_PLAY_ARCHITECTURE_DESIGN
last_updated: 2026-07-31
---

# Master V2 — Time / Sample / Epoch Semantics V1

## 1. Purpose

Capability **MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1** fully decouples productive
Master-V2 / Double-Play market time semantics from RuntimeCycle and polling by
providing canonical Time, Sample, and Epoch domains.

This slice does **not** change trading authority, decision logic, thresholds,
parameters, Survival / Suitability / Composition taxonomies, or activate
runtime / orders / testnet / live.

```
TIME_SAMPLE_SEMANTICS_COMPLETE=true
DISTINCT_OBSERVATION_POLICY_COMPLETE=true
DUPLICATE_SAMPLE_POLICY_COMPLETE=true
OUT_OF_ORDER_POLICY_COMPLETE=true
EVENT_TIME_CANONICAL=true
POLL_RATE_INDEPENDENT=true
OFFLINE_RUNTIME_EQUIVALENCE=true
DETERMINISTIC_REPLAY_PASS=true
NO_DECISION_AUTHORITY_CHANGED=true
NO_PARAMETER_CHANGE=true
RUNTIME_WIRING_INCLUDED=false
PARAMETER_CHANGE_INCLUDED=false
VOLATILITY_CHANGE_INCLUDED=false
READY_FOR_RUNTIME_ACTIVATION=false
PROMOTION_AUTHORITY=false
```

## 2. Primary Owner

| Surface | Owner |
| --- | --- |
| Domain module | `src&#47;trading&#47;market_state&#47;time_sample_epoch_semantics_v1.py` |
| Contract tests | `tests&#47;trading&#47;market_state&#47;test_time_sample_epoch_semantics_v1.py` |
| Distinct acceptor (reuse) | C1 `DistinctMarketObservationAcceptorV1` |
| Confirmation progress (reuse) | C2 `DirectionalConfirmationProgressV1` |

## 3. Domain Separation

| Domain | Type | Authority |
| --- | --- | --- |
| Market Sample | `MarketSampleIdentityV1` | C1 distinctness fields; Event-Time identity |
| Decision Epoch | `DecisionEpochV1` | Opaque; never advances confirmation |
| Runtime Cycle | `RuntimeCycleIndexV1` | Opaque; never synthesizes market Event-Time |
| Event Time | `EventTimeInstantV1` | Canonical market time domain |
| Wallclock | `WallclockInstantV1` / duration / anchors | Cooldown / time-exit **foundation only** |

## 4. Policies (reuse C1)

1. **Canonical Market Sample Identity** — venue + instruments + Event-Time + mark.
2. **Distinct Observation Contract** — productive C1 evaluate/commit path.
3. **Duplicate Sample Policy** — DUPLICATE / TRANSPORT_ONLY_DUPLICATE never advance.
4. **Out-of-Order Sample Policy** — fail-closed; no advance; no state mutation.
5. **Confirmation advance** — exclusively on DISTINCT + `strategy_advance_allowed`.
6. **Polling** — must never invent venue Event-Time from receive / poll / runtime / wallclock.
7. **Event-Time lookback** — feature windows use Event-Time, not poll rate.
8. **Wallclock foundation** — cooldown / time-exit anchors persist deterministically but are **not** bound to Entry/Exit policy in this slice.

## 5. Conscious Non-Goals

- No Entry/Exit / Survival / Suitability / Composition decision changes
- No parameter or threshold mutation
- No runtime / live / order activation
- No governance mutation outside this capability allowlist entry

## 6. Test Ownership

Canonical tests cover:

- duplicate samples
- out-of-order samples
- replay equality / deterministic fingerprints
- confirmation progress only on DISTINCT
- poll-rate independence
- offline/runtime sample identity equivalence
- wallclock foundation persistence (no trading binding)
