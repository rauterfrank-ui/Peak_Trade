# Risk / Sizing Units &#47; Dimensions Contract v0

**Status:** BINDING inventory &#47; units-dimensions declaration (docs + static contract only)  
**Date:** 2026-07-17  
**Obligation:** `OBL_B05_RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0`  
**Machine contract:** [`config/governance/risk_sizing_units_dimensions_contract_v0.json`](../../config/governance/risk_sizing_units_dimensions_contract_v0.json)  
**Related (unchanged):** [`RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md`](RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md) — owner&#47;bypass surface freeze remains 5&#47;5

```
RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0=true
INVENTORY_ONLY=true
UNITS_DIMENSIONS_DECLARATION_ONLY=true
NO_SIZING_MATH_CHANGE=true
NO_DEFAULT_HARMONIZATION=true
NO_PERCENT_DECIMAL_CONVERSION=true
NO_AUTHORITY_ASSIGNMENT=true
NO_OWNER_BYPASS_ALLOWLIST_MUTATION=true
NO_REWIRE=true
NO_DELEGATION=true
NO_DECOMMISSION=true
CONSOLIDATION_STATUS=NOT_STARTED
CANONICAL_RISK_SIZING_OWNER=UNRESOLVED
CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
EXPECTED_PRIMARY_OWNER_COUNT=5
EXPECTED_COMPANION_EDGE_COUNT=2
```

## Purpose

Declarative, fail-closed **units &#47; dimensions** pins for the five inventoried productive Risk&#47;Sizing decision owners and their primary callables. This slice does **not**:

- assign `CANONICAL_RISK_SIZING_OWNER` or execution authority
- change sizing formulas, defaults, rounding, percent&#47;decimal conversion, or caller behavior
- add&#47;remove&#47;rename owner or bypass allowlist entries
- activate runtime bridge, live, shadow, testnet, or orders

## Closed dimension catalog

Only these tokens are legal. Unknown tokens fail closed.

- `ACCOUNT_EQUITY_CCY`
- `AVAILABLE_CAPITAL_CCY`
- `RISK_BUDGET_CCY`
- `MAX_NOTIONAL_CCY`
- `POSITION_NOTIONAL_CCY`
- `PRICE_CCY_PER_UNIT`
- `STOP_DISTANCE_CCY_PER_UNIT`
- `STOP_DISTANCE_FRACTION`
- `QUANTITY_BASE_UNITS`
- `SIGNED_QUANTITY_BASE_UNITS`
- `SIGNAL_DIMENSIONLESS_SIGNED`
- `FRACTION_DECIMAL_0_1`
- `PERCENT_0_100`
- `LEVERAGE_MULTIPLIER`
- `LOT_SIZE_BASE_UNITS`
- `POSITION_COUNT_INTEGER`
- `BOOLEAN_GATE`
- `ENUM_POLICY`
- `UNKNOWN_OR_AMBIGUOUS`

`PERCENT_0_100` and `FRACTION_DECIMAL_0_1` are **not** equivalent. Known conflicts (e.g. `PositionSizerConfig` percent vs `calc_position_size` fraction; `max_position_notional_pct` name vs unit usage) are pinned in the machine contract.

## Primary owners (exactly 5)

Same IDs as `risk_sizing_owner_and_bypass_surface_contract_v1`:

1. `src.governance.capital_risk_sizing_v1`
2. `src.risk.position_sizer`
3. `src.core.position_sizing`
4. `backtest.offline_evaluation_sizing_contract_v1`
5. `src.execution.pipeline.execute_from_signals`

## Companion edges (exactly 2; not primary owners)

| edge_id | path | note |
|---|---|---|
| `COMPANION_SHADOW_POSITION_FRACTION` | `src/live/shadow_session.py` | Config field `FRACTION_DECIMAL_0_1`; passed as absolute `position_size` |
| `COMPANION_LIVE_SESSION_POSITION_FRACTION` | `src/execution/live_session.py` | Same pattern; not a sixth owner&#47;bypass |

## Notable pins

| Surface | Dimension pin |
|---|---|
| `PositionSizerConfig.risk_pct` | `PERCENT_0_100` |
| `calc_position_size` risk &#47; max_position_pct | `FRACTION_DECIMAL_0_1` |
| `FixedFractionSizer.fraction` | `FRACTION_DECIMAL_0_1` |
| CRS budgets | currency dimensions |
| CRS `final_quantity` | `QUANTITY_BASE_UNITS` (side separate) |
| CRS `leverage_ceiling` | `LEVERAGE_MULTIPLIER` — declared&#47;pass-through, currently not applied in quantity chain |
| `execute_from_signals` `max_position_notional_pct` | `UNKNOWN_OR_AMBIGUOUS` |
| Shadow&#47;Live `position_fraction` (config) | `FRACTION_DECIMAL_0_1` |

## Safety invariants

- Economic gate remains fail-closed
- `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false`
- Runtime bridge not activated
- Owner count 5 and bypass count 5 remain unchanged on the surface contract
- Legacy Order Intent surface contracts remain separate and unchanged

## Next

Caller→owner topology is frozen separately in [`RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md`](RISK_SIZING_CALLER_OWNER_TOPOLOGY_CONTRACT_V0.md) (`OBL_B05_CALLER_TO_OWNER_TOPOLOGY_CONTRACT_V0`). Authority assignment, rewire, and decommission remain Operator-GO gated.
