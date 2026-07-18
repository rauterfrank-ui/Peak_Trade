# OPTION_D Invariant Matrix

| Invariant | Result | Evidence |
|-----------|--------|----------|
| Bollinger may emit signals but not activate canonical Entry Side | **PASS** | OBL_B07 EVENT_ONLY; adapter forces `entry_side=NONE` |
| `transition_state` sole Direction&#47;State&#47;Switch authority | **PASS** | Classic path never calls it; quarantine SSOT |
| Composition matrix does not activate Bollinger side without GO | **PASS** | Matrix selects system side from assessments; Bollinger carrier remains NONE |
| `build_canonical_order_intent_v1` gets no orderfähiges Intent from Bollinger NONE | **PASS** | Directional cycle `None` on ENTRY_EXIT without side; order-intent tests green |
| Bypass cannot reinterpret `ENTRY_SIDE=NONE` into LONG&#47;SHORT carrier | **PASS** | Bypass never reads&#47;writes `entry_side` field |
| No Classic&#47;Legacy path elevates OPTION_D | **PASS** | `CLASSIC_LONG_PROPAGATES_TO_INTEGRATED=false` |
| No truthiness&#47;enum conversion NONE→active side on Integrated path | **PASS** | Carrier enum explicit; resolver returns `None` for NONE |
| Backtest&#47;Replay&#47;Bridge fail-closed for canonical side | **PASS** | Integrated flat path; bridge `BOUND_NOT_ACTIVATED` |
| Runtime Bridge not activated | **PASS** | `INTEGRATION_STATUS_BOUND_NOT_ACTIVATED`, `authority_effect=NONE` |
| Orders blocked | **PASS** | `LIVE_AUTHORIZED=false`, `ORDERS_ENABLED=false` |

```text
OPTION_D_INVARIANTS_PASS=true
```
