# Canonical Runtime Operator Entrypoint — O8 Activation

**DOCUMENT_CLASS:** `DERIVED_OPERATOR_ACTIVATION_GUIDANCE`  
**CAPABILITY_ID:** `CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1`  
**MASTER_RUNBOOK_IS_ONLY_SSOT:** `true`  
**SECOND_SSOT_ALLOWED:** `false`  
**RUNTIME_AUTHORIZATION_EFFECT:** `NONE`

## Canonical operator entrypoint

```text
scripts/ops/peak_trade_runtime.py
```

This is the sole recommended local operator entrypoint for supervised
dashboard-only runtime operations under the O8 activation contract.

Canonical subcommands:

```text
preflight
start
status
health
logs
stop
restart
recover
verify
```

## Authority boundary

```text
CORE_LOGIC_CHANGED=false
LIVE_TRADING_AUTHORIZED=false
TESTNET_AUTHORIZED=false
PAPER_EXCHANGE_ORDERS_AUTHORIZED=false
CREDENTIALS_AUTHORIZED=false
DASHBOARD_TRADING_AUTHORITY=false
READ_MODEL_AUTHORITY_EFFECT=NONE
```

`logs` and `verify` are read-only. They must not start or stop processes,
consume authorization, open network sessions, or read token/credential files.

## Compatibility and legacy policy

Required compatibility paths remain present and callable:

```text
scripts/run_web_dashboard.py
scripts/ops/refresh_okx_market_dashboard_v1.py
```

Non-canonical observer stacks remain present and must not be deleted by O8:

```text
scripts/serve_live_dashboard.py
scripts/live_web_server.py
src/live/web/app.py
```

Operator recommendation deauthorization (documentation/operator pointers only):

```text
ad-hoc nohup/setsid/script launch fragments as operator procedure
manual dual-entry recommendation of non-canonical live web hosts
```

O8 does not delete files and does not change legacy runtime behavior.

## Rollback

Rollback reverses activation docs/contract pointers only. O1–O7 code and
O7 evidence must remain intact. Legacy callability remains preserved.

Machine-readable contract:

```text
config/ops/canonical_runtime_operations_activation_contract_v1.json
```
