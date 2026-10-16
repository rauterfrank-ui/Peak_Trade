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

This is the sole recommended local operator entrypoint for canonical runtime
operations under the O8 activation contract. **Presentation HTTP/dashboard
supervision (legacy O2) is retired** — `peak_trade_runtime.py` is fail-closed
(exit 2) until a non-presentation operator surface is explicitly re-authorized.

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

Retired presentation entrypoints (fail-closed; do not start HTTP dashboards):

```text
scripts/run_web_dashboard.py
scripts/serve_live_dashboard.py
scripts/webui/local_market_dashboard.sh
scripts/webui/review_server.sh
src/webui/   (removed — archive read models live under src/ops/workflow_archive_readmodel_projections_v1/)
src/live/web/   (removed)
```

Archive / read-model refresh (non-HTTP, productive):

```text
scripts/ops/refresh_okx_market_dashboard_v1.py
```

O8 `legacy_path_policy.deletion_allowed` stays `false` (fail-closed against
ad-hoc legacy deletion). Governed presentation retirement removed duplicate
launchers and the O2 supervisor package:

```text
src/ops/canonical_local_launcher_and_process_supervision_v1/   (removed)
```

Removed duplicate (must not be reintroduced):

```text
scripts/live_web_server.py
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
