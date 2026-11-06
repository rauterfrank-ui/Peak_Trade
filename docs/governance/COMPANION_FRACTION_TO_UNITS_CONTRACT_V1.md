# Companion Fraction→Units Contract v1

**Contract:** `COMPANION_FRACTION_TO_UNITS_CONTRACT_V1`  
**Binding:** `COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1`  
**Machine contract:** [`config/governance/companion_fraction_to_units_contract_v1.json`](../../config/governance/companion_fraction_to_units_contract_v1.json)

Dependency-closure ratification only. **No** Shadow/Live runtime conversion in this contract.

## Inputs (read-only, authority-preserving)

| Input | Owner | Class / unit |
|-------|--------|----------------|
| Capital base | `ops.governed_productive_account_equity_authority_producer_v1` | `RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING` |
| Reference price | `ops.governed_productive_reference_price_authority_producer_v1` | `mark_price` |
| Instrument metadata | `ops.governed_productive_instrument_metadata_authority_producer_v1` | OKX row → `InstrumentQuantityConstraintsV1` (LINEAR futures) |

Forbidden: `start_balance`, `candle.close`, offline defaults, portfolio-monitor balance.

## Algebra (LINEAR futures)

```text
capital_allocation = account_equity_available_for_sizing × position_fraction
notional_per_unit = reference_price × contract_multiplier
quantity_pre_norm = capital_allocation / notional_per_unit
```

`LEVERAGE_ROLE=NONE`. Inverse contracts: fail-closed.

Dimensional alignment: `capital_risk_sizing_v1._linear_notional_per_unit` and capital-cap quantity derivation.

## Normalization

- **Pre-normalization quantity:** Companion contract / algebra module  
- **Lot floor:** reuse `capital_risk_sizing_v1._floor_to_lot` (same primitive as CRS; not a second normalization authority)  
- **Full-Core venue plan mapping:** `venue_translation_v1` (does not own lot/size on Companion `signal_to_orders` handoff)

## Policies

```text
MISSING_INPUT_POLICY=FAIL_CLOSED
INVALID_INPUT_POLICY=FAIL_CLOSED
AUTHORITY_ADDED=false
```
