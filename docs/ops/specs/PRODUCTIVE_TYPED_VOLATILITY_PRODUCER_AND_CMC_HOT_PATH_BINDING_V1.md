# Productive Typed Volatility Producer and CMC Hot-Path Binding v1

---
docs_token: DOCS_TOKEN_PRODUCTIVE_TYPED_VOLATILITY_PRODUCER_AND_CMC_HOT_PATH_BINDING_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive wallclock PT1M finalizer → typed producer → CMC bind wiring
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
CORE_LOGIC_CHANGE: false
NUMERIC_MAX_AGE_ENFORCING: false
HARD_STOP: true
---

## Machine summary

```
CAPABILITY_ID=PRODUCTIVE_TYPED_VOLATILITY_PRODUCER_AND_CMC_HOT_PATH_BINDING_V1
ROOT_CAUSE=wallclock_hardening_binding_v2 omitted finalized_pt1m_* → permanent WARMUP
PT1M_FINALIZER=canonical_volatility_pt1m_mark_observation_finalizer_v1
PRODUCER=canonical_volatility_typed_runtime_producer_scaffold_v1
CMC_BINDING=canonical_volatility_productive_runtime_cmc_typed_binding_v1
PRESENCE_GATE=double_play_runtime_typed_volatility_presence_gate_v1
NO_PROXY_PROMOTION=true
NO_NEW_VOLATILITY_FORMULA=true
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING=false
CORE_LOGIC_CHANGE=false
```

## Closed edge

```
Public mark observation
  → CanonicalVolatilityPt1mMarkObservationFinalizerV1
  → finalized PT1M mark sample (bucket close only)
  → run_hardened_bridge_cycle_v2(finalized_pt1m_*)
  → CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1
  → CanonicalMarketContextV1.canonical_volatility_estimate
  → Double-Play typed presence gate
```

## Explicit non-goals

- no formula / window / ddof / unit / annualization / timeframe change
- no proxy float promotion
- no numeric max-age enforcement
- no Master V2 / Double Play / Bull-Bear / Confirmation / Scope / Risk / Safety mutation
- no Live / Testnet / order / credential path
