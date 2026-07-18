# Safety Invariants

```text
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
ORDERS_ENABLED=false
STRATEGY_PARAMETERS_CHANGED=false
SECOND_AUTHORITY_INTRODUCED=false
ENTRY_SIDE_CURRENT=NONE
BOLLINGER_SIDE_ACTIVATED=false
LEGACY_CAN_REACH_ORDER_INTENT=false
LEGACY_CAN_REACH_EXECUTION=false
ECONOMIC_VALIDITY_CLAIMED=false
TESTNET=false
SCHEDULER=false
EXTERNAL_SERVICES=false
```

- Classic / legacy bypass remains quarantined.
- Execution eligibility remains false on offline controls.
- Fix only restores market-context DA input + entry_side-aware suitability timing.
- No Risk/Sizing/Execution/Live gate relaxation.
