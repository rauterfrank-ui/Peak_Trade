# Safety attestation — ADX DI holdout preregistration v2

- `SLICE_CLASS=DEFINITION_ONLY`
- `HYPOTHESIS_ID=ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2`
- `NEW_EVALUATION_NOT_RERUN=true`
- `V1_TERMINAL_PRESERVED=true`
- `V1_RESULT_CLASS=ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN`
- `V1_RUN_COUNT=1/1` (unchanged)
- `HOLDOUT_EXECUTED=false`
- `HOLDOUT_DATA_ACCESSED=false`
- `SEALED_HOLDOUT_CONTENT_INSPECTED=false`
- `HOLDOUT_RUN_COUNT=0`
- `HOLDOUT_RUN_LIMIT=1`
- `EVALUATION_AUTHORIZED=false`
- `BACKTEST_AUTHORIZED=false`
- `PROMOTION_ELIGIBLE=false`
- `ECONOMIC_GATE_OPENED=false`
- `RUNTIME_ACTIVATED=false`
- `ORDERS_SENT=false`
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false`
- `DOUBLE_PLAY_AUTHORITY_CHANGED=false`
- `RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false`

Holdout split digest derived exclusively from existing SSOT registry metadata
(acquisition opaque exclusion, dataset_split_policy, bollinger sealed-panel archive).
No sealed holdout raw/derived panel content was read, materialized, or hashed.
V1 was not reopened, rewritten, or re-executed.
