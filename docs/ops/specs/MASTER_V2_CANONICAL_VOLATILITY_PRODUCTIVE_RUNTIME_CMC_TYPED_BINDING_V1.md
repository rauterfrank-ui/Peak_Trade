# MASTER_V2 Canonical Volatility Productive Runtime CMC Typed Binding v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_PRODUCTIVE_RUNTIME_CMC_TYPED_BINDING_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive Producer→bind_typed→CMC edge; typed cutover closed by presence-gate capability
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: true
CMC_RUNTIME_WIRING: true
PRODUCTIVE_BIND_TYPED_CALLER: true
DOUBLE_PLAY_TYPED_CUTOVER: false
GLOBAL_TYPED_ONLY_ENFORCEMENT: false
NUMERIC_MAX_AGE_DECIDED: false
PARAMETER_EFFECT: false
HARD_STOP: true
---

> **Productive CMC typed transport edge (OPTION_2).** Hosts exactly one
> `CanonicalVolatilityTypedRuntimeProducerScaffoldV1`, feeds finalized PT1M
> mark samples, and on `PRODUCED` binds via the existing
> `bind_typed_canonical_volatility_estimate_into_market_context_v1` into
> `CanonicalMarketContextV1`. Does **not** decide numeric max-age, promote
> defaults, or replace competing producers. Double-Play typed cutover authority
> is owned by
> `MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1`
> (this module remains `DOUBLE_PLAY_TYPED_CUTOVER=false` and always returns
> typed binding eligibility for that gate to consume).

## Machine summary

```
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_PRODUCTIVE_RUNTIME_CMC_TYPED_BINDING_V1
PRODUCTIVE_RUNTIME_CALLER=hardening_cycle_bridge_v2.run_hardened_bridge_cycle_v2
PRODUCER_OWNER=CanonicalVolatilityTypedRuntimeProducerScaffoldV1
BINDING_OWNER=bind_typed_canonical_volatility_estimate_into_market_context_v1
TYPED_FACTORY=materialize_typed_canonical_volatility_estimate_v1
VALIDATION_BOUNDARY=validate_canonical_volatility_estimate_v1
LEGACY_ADAPTATION=adapt_canonical_volatility_estimate_to_legacy_float_v1
MAX_AGE_STATUS=UNRESOLVED_MAX_AGE
SECOND_ESTIMATOR_CREATED=false
SECOND_BINDING_AUTHORITY_CREATED=false
SECOND_ADAPTATION_AUTHORITY_CREATED=false
STATIC_RUNTIME_FALLBACK_USED=false
GLOBAL_TYPED_ONLY_ENFORCEMENT=false
DOUBLE_PLAY_TYPED_CUTOVER=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
READY_FOR_RUNTIME_CMC_TYPED_TRANSPORT=true
READY_FOR_DOUBLE_PLAY_TYPED_CUTOVER=false
READY_FOR_TYPED_ONLY_RUNTIME_ENFORCEMENT=false
READY_FOR_NUMERIC_MAX_AGE_POLICY=false
READY_FOR_PARAMETER_RESEARCH=false
```

## Productive call graph

```
finalized PT1M mark sample (optional per cycle)
  → CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1
       → CanonicalVolatilityTypedRuntimeProducerScaffoldV1.ingest_finalized_pt1m_mark_sample_v1
            → sample authority + history + P1/P2
  → on PRODUCED (or process-internal reuse via output port):
       validate_canonical_volatility_estimate_v1
       → bind_typed_canonical_volatility_estimate_into_market_context_v1
            → adapt_validated_typed_estimate_to_legacy_float_v1
            → CMC.canonical_volatility_estimate + CMC.volatility_estimate (atomic)
  → HardenedBridgeSessionStateV2 / run_hardened_bridge_cycle_v2
       → build_integrated_offline_replay_input_v1 / Double Play consumers (float)
```

Cycles without a new finalized PT1M sample call
`on_runtime_cycle_without_sample_v1` and may reuse a previously PRODUCED
estimate via the producer output port. Reject outcomes
(`OUT_OF_ORDER`, `HISTORY_GAP`, `PERSISTENCE`, `MATERIALIZATION`, `INVALID`)
perform no CMC typed binding. Warmup / restart-without-estimate leave the
typed cutover path fail-closed. `UNRESOLVED_MAX_AGE` is telemetry only — not
freshness approval.

## Restart

History restores through the existing persistence contract. The estimate is
**not** rematerialized. Typed cutover remains fail-closed until the next
regular `PRODUCED` outcome. No rematerialize API is added here.

## Explicit non-goals

- no numeric max-age policy (`C1_G10` remains open)
- no global typed-only enforcement (`G3` explicit legacy remains admissible offline)
- no competing producer mutation (`G15`)
- no Double-Play typed cutover
- no Replay 0.02 / Research 0.2 mutation
- no Live / Testnet / order routing
- no parameter research

## Owners

| Artifact | Path |
|---|---|
| Binding host | `src&#47;trading&#47;master_v2&#47;canonical_volatility_productive_runtime_cmc_typed_binding_v1.py` |
| Productive caller | `src&#47;ops&#47;wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2&#47;hardening_cycle_bridge_v2.py` |
| Spec | this document |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_canonical_volatility_productive_runtime_cmc_typed_binding_v1.py` |
