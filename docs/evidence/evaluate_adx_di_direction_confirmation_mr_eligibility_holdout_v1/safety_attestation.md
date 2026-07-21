# Safety attestation — ADX DI holdout evaluation v1

- `RESULT_CLASS=ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN`
- `HOLDOUT_EXECUTED=true`
- `HOLDOUT_RUN_COUNT=1` (consumed single authorized run; no retry)
- `HOLDOUT_DATA_ACCESSED=true`
- `EVALUABLE=false`
- `TECHNICAL_FAILURE=true`
- `REASON=UNEXPECTED_FAILURE_AFTER_DATA_ACCESS:ValueError:mv2_replay_engine_signal_binding_failed:mv2_replay_signal_index_mismatch`
- `NO_RETRY=true`
- `NO_POST_RESULT_TUNING=true`
- `ECONOMIC_GATE_OPENED=false`
- `PROMOTION_ELIGIBLE=false`
- `RUNTIME_ACTIVATED=false`
- `ORDERS_SENT=false`
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`

The single authorized holdout run opened sealed panel data and failed during
MV2 replay signal-index binding before economic metrics could be produced.
Per preregistration, the run is terminal and must not be repeated.
