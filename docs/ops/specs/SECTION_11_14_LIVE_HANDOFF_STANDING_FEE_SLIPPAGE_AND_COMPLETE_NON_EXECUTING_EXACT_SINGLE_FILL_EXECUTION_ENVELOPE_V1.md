---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_STANDING_FEE_SLIPPAGE_AND_COMPLETE_NON_EXECUTING_EXACT_SINGLE_FILL_EXECUTION_ENVELOPE_V1
status: active
scope: §11.14 standing fee&#47;slippage policy bind and non-executing exact-single-fill execution envelope; GET-only trade-fee allowlist reuse; no POST; no submit; no wire send; no Owner execution authorization; no Live&#47;canary arming mutation
capability: SECTION_11_14_LIVE_HANDOFF_STANDING_FEE_SLIPPAGE_AND_COMPLETE_NON_EXECUTING_EXACT_SINGLE_FILL_EXECUTION_ENVELOPE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-07
---

# Section 11.14 Standing Fee Slippage And Complete Non-Executing Exact Single Fill Execution Envelope V1

## Goal

Bind current standing fee and slippage policy for the exact-single
`SUI-USD_UM_XPERP-310404` LIMIT BUY path and complete the non-executing
execution envelope as far as repository authority allows. This does **not**
authorize Live submit.

```text
CORE_LOGIC_CHANGE=true
ACTIVATION_STATE=not_activated
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
POST_ALLOWED=false
OWNER_EXECUTION_AUTHORIZED=false
LIVE_EXECUTION_AUTHORIZED=false
LIVE_SUBMIT_EXECUTED=false
WIRE_SEND_EXECUTED=false
POSITION_MUTATION_EXECUTED=false
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false
RESTART_EXECUTED=false
GET_ONLY=true
POST_PERFORMED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
MAP_OF_TRUTH_AUTHORITY=NONE
```

## Standing fee policy (current)

```text
CURRENT_STANDING_FEE_POLICY_BOUND=true
CURRENT_FEE_POLICY_SOURCE=GET &#47;api&#47;v5&#47;account&#47;trade-fee?instType=FUTURES&instFamily=SUI-USD_UM_XPERP
CURRENT_FEE_POLICY_VALUE_OR_MODEL=conservative_debit_rate=max(debit(taker),debit(maker)); amount=rate*qty*ctVal*worst_fill_px
CURRENT_FEE_POLICY_UNIT=FRACTION_OF_NOTIONAL_AND_USDC_INTERNAL_AMOUNT
CURRENT_FEE_POLICY_FRESHNESS=REQUIRED_CURRENT_GET_PER_PRETRADE_DECISION
SIGN=VENUE_NEGATIVE_IS_DEBIT
DELIVERY_FIELD=OBSERVABLE_NOT_PART_OF_ENTRY_FILL
ROUND_TRIP_FEE_RESERVE=NOT_THIS_FILL
HISTORICAL_BTC_Z2N_RATES=NOT_CURRENT
RESEARCH_BACKTEST_FEE=NOT_CURRENT
EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN
NOTIONAL_ALGEBRA_ROLE=PEAK_TRADE_INTERNAL_NOTIONAL_ENVELOPE_NOT_OEM_OKX_FEE_FORMULA
MAKER_TAKER_ASSUMPTION=FAIL_CLOSED_UNCERTAINTY_RESOLVED_AS_CONSERVATIVE_MAX_DEBIT
```

Numeric rates are standing-policy inputs only when a current trade-fee GET
for the bound SUI family is present. Historical BTC `takerUSDC=-0.0005` is
not current SUI authority.

## Standing slippage policy (current)

```text
CURRENT_STANDING_SLIPPAGE_POLICY_BOUND=true
CURRENT_SLIPPAGE_POLICY_SOURCE=LIMIT_WORST_FILL_EQUALS_LIMIT_PX
CURRENT_SLIPPAGE_POLICY_VALUE_OR_MODEL=worst_fill_price=limit_px; BUY limit is quantized ROUND_DOWN from current ticker last|askPx
CURRENT_SLIPPAGE_POLICY_UNIT=QUOTE_PRICE_AND_FRACTION_OF_REFERENCE
PRICE_LIMIT_BAND=SEPARATE_GATE_NOT_SLIPPAGE
HISTORICAL_0_0008=NOT_CURRENT
COVER_USDC_SLP_TOB_FLOOR_TICK=NOT_THIS_FILL_WORST_PRICE
```

## Envelope versus authorization

```text
EXACT_EXECUTION_ENVELOPE_COMPLETE=true_when_all_bound_inputs_present
TECHNICAL_EXECUTION_READY=true_when_envelope_complete_and_required_pretrade_predicates_pass
OWNER_EXECUTION_AUTHORIZED=false
LIVE_EXECUTION_AUTHORIZED=false
```

These four statements are not synonymous. Technical completeness does not
create execution authority. `clOrdId` remains
`UNKNOWN_REQUIRES_FUTURE_EXECUTION_OWNER_GO`. Offline plan serialization
stops before wire.

## Capture compatibility

Optional envelope provenance fields may be attached to a later
contemporaneous capture record. Required restart-identity fields
(`clOrdId`, `ordId`, `instId`, `posSide`, `pos`) are not rewritten.
No productive capture is executed. No restart is executed.
