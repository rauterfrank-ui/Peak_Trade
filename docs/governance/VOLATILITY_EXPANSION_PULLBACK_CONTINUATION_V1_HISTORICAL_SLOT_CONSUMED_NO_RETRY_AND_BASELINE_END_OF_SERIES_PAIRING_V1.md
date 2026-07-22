# VEPC v1 — Historical slot CONSUMED_NO_RETRY + baseline end-of-series pairing

## Status

`GOVERNANCE_DECISION_RECORDED`

## Binding decisions

1. Historical VEPC development slot status: `CONSUMED_NO_RETRY`
2. Accounting defect does **not** authorize evaluation retry or replacement run
3. Historical fail-closed result is **not** rewritten
4. Canonical end-of-series policy for productive roundtrip/ledger pairing:
   `END_OF_INSTRUMENT_LIQUIDATION` then `END_OF_PANEL_LIQUIDATION`
   (after protective / regime / time exits; first-event-wins; close price;
   canonical fee/slippage/timestamp primitives; no second PnL truth)
5. Baseline declarative pairing must use that same policy (minimal shared-evaluator fix)

## Historical attempt (normative; no re-execution)

- Base SHA at attempt: `932e3ded5331a95c4cb574c01188fd29286b8677`
- Window: `2026-07-22T22:03:29Z` → `2026-07-22T22:04:02Z` (exit 2)
- Reason: `UNEXPECTED:ValueError:UNPAIRABLE_ENTRY_NO_EXIT:okx:linear_perpetual:AGLD:USDT:USDT:perp:10575`
- Root cause class: baseline declarative pairing lacked EOI/EOP while TIME_EXIT unreachable
- Treatment strategy-emitted exit path was not the first failure surface
- CLI reported `runner_started=false` (pre-#5464 accounting defect); normative runner start still counts toward the single slot

## Explicit non-actions

- NO Development evaluation re-execution
- NO retry / Ersatzlauf
- NO holdout access
- NO strategy-parameter change
- NO dataset change
- NO treatment-semantics change
- NO second PnL truth
- NO rewrite of prior terminal evidence for VCB/VEP/VDB/VDBX/VCEB
- NO merge in this slice

## Machine SSOT consequences

- Measurement contract / entry-point binding / backlog / program record slot consumed
- `EVALUATION_RETRY_AUTHORIZED=false`
- Lane awaits explicit successor hypothesis under separate operator GO
- Shared productive evaluator declarative path implements EOI/EOP for future non-retry infrastructure use only

docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_PULLBACK_CONTINUATION_V1_HISTORICAL_SLOT_CONSUMED_NO_RETRY_AND_BASELINE_END_OF_SERIES_PAIRING_V1
STATUS: GOVERNANCE_DECISION_RECORDED_CONSUMED_NO_RETRY_PLUS_BASELINE_EOI_EOP_PAIRING
scope: research, offline-only, governance-decision, non-evaluating
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
