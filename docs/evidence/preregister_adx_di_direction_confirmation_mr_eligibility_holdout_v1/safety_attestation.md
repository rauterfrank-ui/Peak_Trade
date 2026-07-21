# Safety attestation — ADX DI holdout preregistration v1

- `SLICE_CLASS=DEFINITION_ONLY`
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

Holdout split digest derived exclusively from existing SSOT registry metadata
(acquisition opaque exclusion, dataset_split_policy, bollinger sealed-panel archive).
No sealed holdout raw/derived panel content was read, materialized, or hashed.
