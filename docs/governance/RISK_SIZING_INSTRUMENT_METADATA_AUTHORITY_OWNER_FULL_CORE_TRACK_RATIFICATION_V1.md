# Risk Sizing — Full-Core Instrument Metadata Authority Owner Ratification v1

**Status:** BINDING scoped Owner-GO ratification + Full-Core producer/handoff (no Companion)  
**Date:** 2026-09-25  
**Obligation:** `OBL_B05_INSTRUMENT_METADATA_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1`  
**Machine contract:** [`config/governance/risk_sizing_instrument_metadata_authority_owner_full_core_track_ratification_v1.json`](../../config/governance/risk_sizing_instrument_metadata_authority_owner_full_core_track_ratification_v1.json)  
**Baseline:** `origin&#47;main @ 643f7fb6fab3af320aa1cef33d7512e82a0505bb`

```
RISK_SIZING_INSTRUMENT_METADATA_AUTHORITY_OWNER_FULL_CORE_TRACK_RATIFICATION_V1=true
OWNER_GO=OWNER_GO_RATIFY_B05_INSTRUMENT_METADATA_AUTHORITY_OWNER_FULL_CORE_TRACK_V1
OWNER_GO_STATUS=CONSUMED
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
FULL_CORE_INSTRUMENT_METADATA_AUTHORITY_OWNER_RATIFIED=true
INSTRUMENT_METADATA_AUTHORITY_OWNER=ops.governed_productive_instrument_metadata_authority_producer_v1
QUANTITY_UNIT_SEMANTICS_CLASS_RATIFIED=CONTRACTS_SZ_LOT_STEP
DIMENSION_ID=COMPLETE_INSTRUMENT_QUANTITY_CONSTRAINT_METADATA
UNIT_CLASS=INSTRUMENT_CONSTRAINT_BUNDLE
SCOPE_TRACK=FULL_CORE
INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=false
GOVERNED_PRODUCER_CREATED=true
PRODUCER_IMPLEMENTATION_PRESENT=true
OBSERVATION_IS_NOT_AUTHORITY=true
COMPANION_INSTRUMENT_METADATA_HANDOFF_AUTHORIZED=false
C2_INSTRUMENT_METADATA_DOMAIN_VERDICT=PARTIAL
CONVERSION_READY=false
```

## Semantic adjudication (consumed)

**Required function:** venue-bound **complete instrument quantity constraint metadata** for C2 Fraction→Units (future Companion) and for Full-Core CRS lot/multiplier/notional math.

**Ratified quantity unit class:** `CONTRACTS_SZ_LOT_STEP` (OKX linear/swap: `sz` in contracts; `ctVal` scales notional; `lotSz`/`minSz` admissibility).

Forensic consumer basis:

1. `capital_risk_sizing_v1.InstrumentQuantityConstraintsV1` — `contract_multiplier`, `lot_size`, `minimum_quantity`, `instrument_metadata_version` (fail-closed validation).
2. `current_productive_exact_object_flatten_plan_v1` — `lotSz`, `minSz`, `tickSz` with strict `instId` match (observation transport, not authority).
3. `fresh_pretrade_runtime_get_v1` — `INSTRUMENT_STATE` on `GET &#47;api&#47;v5&#47;public&#47;instruments`.
4. Cap24 `BoundInstrumentV1` — identity only; metadata producer must not reselect.

## Owner decision (consumed)

For the **Full-Core track** only, B05 `INSTRUMENT_METADATA_AUTHORITY_OWNER` is ratified to:

`ops.governed_productive_instrument_metadata_authority_producer_v1`

## Full-Core handoff (this WP)

- Governed producer: `current_productive_okx_instruments_row_producer_v1` (OKX instruments row → `InstrumentQuantityConstraintsV1`, fail-closed).
- Enter-live-29p join requires injected `instruments_payload`; no `default_offline_replay_instrument_v0` on `LIVE_ACCOUNT_BOUND` rebind.

## Explicit non-claims

- No Companion Shadow/Live instrument-metadata handoff
- No Fraction→Units conversion activation
- No repo-wide `CANONICAL_RISK_SIZING_OWNER`
- No Cap24 selection/ranking change
- Chain closure (`INSTRUMENT_METADATA_AUTHORITY_CHAIN_CLOSED=true`) **not** claimed

## C2 mechanical reevaluation

Companion census: `INSTRUMENT_QUANTITY_METADATA` → **PARTIAL** (Full-Core owner + producer/handoff; Companion path still absent).  
`C2_STATUS` remains **UNRESOLVED**; `CONVERSION_READY` remains **false**.
