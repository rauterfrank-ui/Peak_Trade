# MASTER_V2 Canonical Volatility Typed Runtime Producer Scaffold v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1
STATUS: CAPABILITY_AVAILABLE
scope: typed runtime producer scaffold + mark history host; non-authorizing; no cutover
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: false
RUNTIME_PRODUCER_CUTOVER: false
HOT_PATH_BINDING: false
PARAMETER_EFFECT: false
TRADING_LOGIC_EFFECT: false
HARD_STOP: true
---

> **Non-authorizing scaffold.** Provides a production-near typed runtime producer
> for `CanonicalVolatilityEstimateV1` that is **not** wired into Master-V2 &#47;
> Double-Play hot path. Reuses existing sample, event-time, materializer (P1),
> and typed-factory (P2) authorities. Does **not** decide parameter values,
> numeric max-age, cutover, or productive `bind_typed` consumption.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1
PRODUCER_OWNER=trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1
HISTORY_OWNER=trading.master_v2.canonical_volatility_runtime_mark_history_v1
ESTIMATOR_OWNER=trading.master_v2.canonical_volatility_estimate_materializer_v1
TYPED_FACTORY_OWNER=trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1
SAMPLE_AUTHORITY=accept_distinct_market_sample_v1
EVENT_TIME_AUTHORITY=EventTimeInstantV1
SINGLE_CANONICAL_VOLATILITY_ESTIMATOR=true
SINGLE_TYPED_FACTORY=true
SINGLE_SAMPLE_ACCEPTANCE_AUTHORITY=true
SINGLE_EVENT_TIME_AUTHORITY=true
NO_SECOND_BINDING_ADAPTER=true
NO_FLOAT_ONLY_RUNTIME_OUTPUT=true
NO_SILENT_FALLBACK=true
NO_NUMERIC_FLOOR=true
NO_RUNTIME_CUTOVER=true
NO_DOUBLE_PLAY_WIRING=true
NO_PARAMETER_VALUE_DECISION=true
FAIL_CLOSED=true
PRODUCTIVE_BIND_TYPED_CALLER=false
CMC_RUNTIME_WIRING=false
DOUBLE_PLAY_RUNTIME_WIRING=false
P7_REPLACED=false
NUMERIC_MAX_AGE_DECIDED=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
READY_FOR_TYPED_RUNTIME_PRODUCER_CAPABILITY=true
READY_FOR_RUNTIME_PRODUCER_CUTOVER=false
READY_FOR_RUNTIME_WIRING=false
READY_FOR_PARAMETER_RESEARCH=false
```

## Authority reuse

| Surface | Owner (reuse) |
|---|---|
| Estimator &#47; materializer P1 | `canonical_volatility_estimate_materializer_v1` |
| Typed factory P2 | `canonical_volatility_estimate_typed_consumption_contract_v1` |
| Sample distinctness | `accept_distinct_market_sample_v1` |
| Event time | `EventTimeInstantV1` &#47; `MarketSampleIdentityV1` |
| Semantics contract | `canonical_volatility_estimate_feature_contract_v1` |
| History host (this capability) | `canonical_volatility_runtime_mark_history_v1` |
| Producer scaffold (this capability) | `canonical_volatility_typed_runtime_producer_scaffold_v1` |

No second estimator, sample authority, event-time authority, or binding adapter.

## History ownership

`CanonicalVolatilityRuntimeMarkHistoryHostV1` stores only distinct accepted
finalized PT1M `mark_price` samples for one venue &#47; instrument binding:

- venue, instrument ids, market sample identity
- canonical event time, optional receive_time
- finalized mark_price, sample digest
- ordered PT1M history, last accepted event time, history digest

Polling &#47; runtime cycles never synthesize samples. Duplicates do not advance
history or `observation_count`. Out-of-order samples follow the existing sample
authority (fail-closed, no advance). No mid-price history, no wallclock
`feature_regime` producer, no gap fill, no synthetic bars.

## Persistence boundary

Capability-owned JSON persistence under the sample authority:

- schema &#47; contract version required
- venue &#47; instrument isolated
- event-time order preserved
- digests stored and recomputed fail-closed
- atomic temp + fsync + replace
- corrupt &#47; incomplete &#47; incompatible payloads rejected
- restart reconstructs identical history digests and re-materializable estimates

Not a global second market-state authority. No new database platform. No
best-effort recovery with invented values. No automatic default volatility reset.

## Producer call graph

```
finalized PT1M mark sample
  → validate_finalized_mark_sample_fields_v1 (fail-closed)
  → accept_distinct_market_sample_v1 (existing sample authority)
  → history host advance on DISTINCT only
  → optional atomic persistence
  → warmup if prices < 61
  → PT1M contiguity guard on trailing window
  → materialize_typed_canonical_volatility_estimate_v1 (P2)
       → compute_canonical_volatility_estimate_from_mark_prices_v1 (P1)
       → derive_return_observation_count_from_closed_window_v1
       → build_canonical_volatility_estimate_v1 + source_digest
  → TypedRuntimeProducerOutputPortV1 (non-productive handoff port)
```

`as_of_event_time` is derived exclusively from the accepted
`EventTimeInstantV1`. `fallback_used` remains false. No float-only alternative
output.

## Warmup and reject outcomes

| Outcome | Meaning |
|---|---|
| `WARMUP` | Distinct accepted; fewer than 61 prices; no estimate |
| `PRODUCED` | Trailing contiguous window materializes typed estimate |
| `DUPLICATE_NOOP` | Duplicate &#47; transport-only duplicate; history unchanged |
| `OUT_OF_ORDER_REJECTED` | Existing out-of-order policy; no advance |
| `INVALID_SAMPLE_REJECTED` | Non-final, NaN&#47;inf&#47;null&#47;&lt;=0, identity mismatch |
| `HISTORY_GAP_REJECTED` | Trailing window gap &gt; PT1M; no estimate |
| `PERSISTENCE_REJECTED` | Atomic persistence failure |
| `MATERIALIZATION_REJECTED` | P1 &#47; P2 fail-closed rejection |

Runtime cycle without a new sample invents no estimate and does not mint a new
sample digest.

## observation_count provenance

`derive_return_observation_count_from_closed_window_v1` closes the assessment
gap where `observation_count` was only the `MINIMUM_RETURN_OBSERVATIONS`
constant. The typed factory now derives the count from the closed log-return
window actually used by the materializer. Estimator unit &#47; horizon &#47; scaling &#47;
identity are unchanged. No parallel factory path.

## Digest chain

```
sample_digest ← MarketSampleIdentityV1 canonical fingerprint
history_digest ← ordered history records + schema owner
source_digest ← typed compute_source_digest_v1 (carrier fields + mark prices)
```

Identical inputs → stable digests. Different price histories → different
`source_digest` &#47; `history_digest`. Duplicates change neither.

## Explicit non-goals

- no runtime cutover &#47; Double-Play wiring
- no productive call to `bind_typed_canonical_volatility_estimate_*`
- no `CanonicalMarketContextV1` mutation on a productive runtime path
- no DynamicScopeRules &#47; Survival &#47; Suitability &#47; Composition &#47; Entry&#47;Exit wiring
- no P7 replacement &#47; legacy path global rejection
- no numeric max-age decision
- no parameter-value decision (`0.2` &#47; `0.02` &#47; `1.0` &#47; `1e-9` not introduced
  as runtime fallback or floor)
- no Live &#47; Testnet &#47; Shadow &#47; order config mutation

## Owners

| Artifact | Path |
|---|---|
| History host | `src&#47;trading&#47;master_v2&#47;canonical_volatility_runtime_mark_history_v1.py` |
| Producer scaffold | `src&#47;trading&#47;master_v2&#47;canonical_volatility_typed_runtime_producer_scaffold_v1.py` |
| Typed factory extension | `src&#47;trading&#47;master_v2&#47;canonical_volatility_estimate_typed_consumption_contract_v1.py` |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_typed_runtime_producer_scaffold_v1.py` |
| Spec | this document |

## Forbidden without separate GO

- Runtime producer cutover
- Hot-path &#47; Double-Play wiring
- Productive CMC bind
- Parameter research or value recommendation
- Live &#47; testnet &#47; orders authorization
