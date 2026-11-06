# MASTER_V2 Double Play Runtime Typed Volatility Presence Gate v1

---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive Double-Play typed presence gate; closes typed cutover without Direct-Typed consumers
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_WIRING: true
DOUBLE_PLAY_TYPED_CUTOVER: true
GLOBAL_TYPED_ONLY_ENFORCEMENT: false
NUMERIC_MAX_AGE_DECIDED: false
PARAMETER_EFFECT: false
HARD_STOP: true
---

> **Productive Double-Play typed cutover (OPTION_2 presence gate).** Scope,
> Boundary, and Entry authority run only when
> `CanonicalMarketContextV1.canonical_volatility_estimate` is present, validated,
> and atomically synchronized with the legacy float. The adapted float remains
> the numeric input for existing consumers. Exit &#47; risk &#47; safety authority is
> preserved. Offline Replay 0.02 &#47; Research 0.2 &#47; Scenario paths stay unchanged.

## Machine summary

```
CAPABILITY_ID=MASTER_V2_DOUBLE_PLAY_RUNTIME_TYPED_VOLATILITY_PRESENCE_GATE_V1
PRESENCE_GATE_OWNER=evaluate_double_play_runtime_typed_volatility_presence_gate_v1
ELIGIBILITY_OWNER=evaluate_typed_volatility_binding_eligibility_v1
PRODUCTIVE_RUNTIME_CALLER=hardening_cycle_bridge_v2.run_hardened_bridge_cycle_v2
BINDING_OWNER=bind_typed_canonical_volatility_estimate_into_market_context_v1
LEGACY_ADAPTATION=adapt_canonical_volatility_estimate_to_legacy_float_v1
FLOAT_RESOLUTION=resolve_legacy_volatility_float_for_consumer_v1
REASON_CODE_TYPED_MISSING=TYPED_VOLATILITY_ESTIMATE_MISSING
DOUBLE_PLAY_TYPED_CUTOVER=true
GLOBAL_TYPED_ONLY_ENFORCEMENT=false
NUMERIC_MAX_AGE_DECIDED=false
SECOND_ESTIMATOR_CREATED=false
SECOND_ADAPTER_CREATED=false
SECOND_VALIDATOR_CREATED=false
LOCAL_TYPED_VALUE_EXTRACTION_CREATED=false
LIVE_AUTHORIZATION=false
HARD_STOP=true
```

## Semantics

1. **Presence gate (productive only)** — Before productive Double-Play
   scope &#47; boundary &#47; entry evaluation,
   `canonical_volatility_estimate is not None` and existing typed validation plus
   typed&#47;float consistency must succeed. Reuses
   `evaluate_typed_volatility_binding_eligibility_v1`; the eligibility result is
   never discarded.

2. **Typed absent + legacy float present** — Fail-closed with
   `TYPED_VOLATILITY_ESTIMATE_MISSING`. No new entry, no scope initialization from
   the float, no dynamic boundary update from the float, no alpha state
   progression. `feature_regime` volatility remains NON_ALIAS and cannot authorize
   productive Double Play when typed is absent.

3. **Exit &#47; risk &#47; safety independence** — Safety Exit, Hard-Risk Reduce,
   Position Reconciliation, and Mandatory Exit&#47;Reduce remain executable when an
   open position or protection signal requires them. The gate blocks alpha
   authority, not protection authority.

4. **Lifecycle** — Warmup &#47; restart without estimate &#47; duplicate without prior &#47;
   out-of-order &#47; history gap &#47; persistence &#47; materialization failures remain
   fail-closed until a valid typed estimate is bound. Duplicate&#47;cycle reuse with a
   valid prior keeps existing reuse semantics. Non-enforcing max-age policy
   evidence may be attached; `UNRESOLVED_MAX_AGE` is diagnostic only — no
   numeric threshold and no Alpha enforcement by age.

5. **Isolation** — Opt-in via
   `require_productive_typed_volatility_presence_gate=True` on the productive
   bridge path only. Offline Replay default 0.02, Research 0.2, Scenario HIGH_VOL
   0.08, and explicit quarantine paths remain unchanged. No global typed-only rule.

## Owners

| Artifact | Path |
|---|---|
| Presence gate | `src&#47;trading&#47;master_v2&#47;double_play_runtime_typed_volatility_presence_gate_v1.py` |
| Productive caller | `src&#47;ops&#47;wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2&#47;hardening_cycle_bridge_v2.py` |
| Spec | this document |
| Tests | `tests&#47;trading&#47;master_v2&#47;test_double_play_runtime_typed_volatility_presence_gate_v1.py` |

## Explicit non-goals

- no numeric max-age **threshold** decision &#47; Alpha enforcement by age
- no global typed-only enforcement
- no Direct-Typed consumer refactor in Scope &#47; Rules &#47; Bridge
- no second estimator &#47; binder &#47; adapter &#47; validator
- no Replay 0.02 &#47; Research 0.2 &#47; Scenario mutation
- no Live &#47; Testnet &#47; order routing
- no Survival-Ratio &#47; Suitability &#47; ATR &#47; feature_regime semantic change
