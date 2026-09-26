# OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1

```text
DOCUMENT_CLASS=IMPLEMENTATION_SPEC
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
OWNER=ops.okx_eea_private_account_state_runtime_v1
BASELINE_SHA=150ddb069e75263e995bafd4e2edbead9a0d563a
```

Observation-only OKX EEA Private State Plane: ratified Private REST GET baseline/recovery,
authenticated Private WebSocket observation (login/subscribe/heartbeat only),
normalized account/balance/position/order/fill state, quality/provenance/reconciliation,
durable readmodel/restart, and thin adapters into existing governed pretrade seams.

Policy ratification: `config/governance/okx_eea_private_account_state_runtime_v1_policy_v1.json`.

Credential class: `OKX_EEA_PRIVATE_OBSERVATION_READ_V1` (GET + WS observation only; no POST;
no WS order send/amend/cancel; no trade-credential fallback).

Does not modify Cap 2.3 selection, MV2/DP, Pretrade fresh-GET authority, Execution POST/wire,
account-equity sizing authority, or external-effect authorization.
