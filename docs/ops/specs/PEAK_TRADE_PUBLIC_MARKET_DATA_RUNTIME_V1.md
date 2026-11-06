# PEAK_TRADE_PUBLIC_MARKET_DATA_RUNTIME_V1

```text
DOCUMENT_CLASS=IMPLEMENTATION_SPEC
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
OWNER=ops.peak_trade_public_market_data_runtime_v1
BASELINE_SHA=3bc330f27d5fd6816357593b691e5f5976ffad27
```

Observation-only OKX EEA Public Data Plane: official-current Public WebSocket binding,
Public REST bootstrap/history/gap-fill/recovery, canonical market facts, tiered semantic
durability, historical query/replay, and thin governed consumer adapters.

Policy ratification: `config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json`.

Does not modify Cap 2.3 selection, MV2/DP, Pretrade, Execution, Private State Plane, POST,
or external-effect authorization.
