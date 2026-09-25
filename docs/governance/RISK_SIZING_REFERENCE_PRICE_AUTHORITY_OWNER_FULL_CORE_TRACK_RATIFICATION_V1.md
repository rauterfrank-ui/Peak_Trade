# Risk Sizing — Full-Core Reference Price Authority Owner Ratification v1

**Status:** BINDING scoped Owner-GO ratification (docs + static contract + owner slot constants only)  
**Date:** 2026-09-25  
**Obligation:** `OBL_B05_REFERENCE_PRICE_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_reference_price_authority_owner_full_core_track_ratification_v1.json`](../../config/governance/risk_sizing_reference_price_authority_owner_full_core_track_ratification_v1.json)  
**Baseline:** `origin/main @ 0650146df80cab0108d32ff8dd72a2d6ca042874`

```
RISK_SIZING_REFERENCE_PRICE_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1=true
OWNER_GO=OWNER_GO_RATIFY_B05_REFERENCE_PRICE_AUTHORITY_OWNER_FULL_CORE_TRACK_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
FULL_CORE_REFERENCE_PRICE_AUTHORITY_OWNER_RATIFIED=true
REFERENCE_PRICE_AUTHORITY_OWNER=ops.governed_productive_reference_price_authority_producer_v1
PRICE_SEMANTICS_CLASS_RATIFIED=mark_price
DIMENSION_ID=INSTRUMENT_VENUE_TIME_BOUND_CONVERSION_REFERENCE_PRICE
UNIT_CLASS=PRICE_QUOTE_PER_INSTRUMENT_UNIT
SCOPE_TRACK=FULL_CORE
REFERENCE_PRICE_AUTHORITY_CHAIN_CLOSED=false
GOVERNED_PRODUCER_CREATED=false
PRODUCER_IMPLEMENTATION_PRESENT=false
OBSERVATION_IS_NOT_AUTHORITY=true
INDEX_PX_NOT_REFERENCE_PRICE_AUTHORITY=true
COMPANION_REFERENCE_PRICE_HANDOFF_AUTHORIZED=false
C2_REFERENCE_PRICE_DOMAIN_VERDICT=PARTIAL
CONVERSION_READY=false
```

## Semantic adjudication (consumed)

**Required function:** instrument-venue-time-bound **conversion reference price** for C2 Fraction→Units (future Companion) and for Full-Core CRS notional/stop-distance math (subordinate MV2+DP consumer).

**Ratified `price_semantics_class`:** `mark_price` (Full-Core track only).

Deduction basis (not name matching):

1. Full-Core productive enter-live join binds `reference_price` exclusively from `market_context.mark_price` (`current_productive_enter_live_29p_join_v1.py`).
2. Authority freeze forbids candle.close, fill, CMC, and offline default elevation; forbids implicit mark/index/last synonymization.
3. MV2 `INDEX_PX` is a separate join surface; contracts forbid substituting mark with INDEX_PX for MV2 helpers. Using `index_price` as conversion reference would change Full-Core CRS wiring without Owner-GO.

## Owner decision (consumed)

For the **Full-Core track** only, B05 `REFERENCE_PRICE_AUTHORITY_OWNER` is ratified to:

`ops.governed_productive_reference_price_authority_producer_v1`

with **`mark_price`** as the explicit semantics class.

## Explicit non-claims

- No Companion Shadow/Live reference-price handoff to `signal_to_orders`
- No Fraction→Units conversion activation
- No Instrument Metadata owner assignment
- No repo-wide `CANONICAL_RISK_SIZING_OWNER`
- No INDEX_PX elevation to reference-price authority
- No MV2+Double-Play trading-decision semantic change
- Ratification does **not** assert `GOVERNED_PRODUCER_CREATED=true`

## C2 mechanical reevaluation

Companion C2 census: `REFERENCE_PRICE` → **PARTIAL** (Full-Core owner + semantics ratified; Companion path still `REQUIRED_INPUT_MISSING`).  
`C2_STATUS` remains **UNRESOLVED**; `CONVERSION_READY` remains **false**.
