# OKX Integration Read-Only Audit — 2026-07-17

**Status:** COMPLETE for public/static surfaces; PARTIAL for private account state (credentials ABSENT; no live private client in repo)  
**Authority:** `EXPLICIT_OPERATOR_DECISION` (P3 OKX validation)  
**Machine SSOT:** [`config/governance/okx_audit_authority_ssot_v1.json`](../../config/governance/okx_audit_authority_ssot_v1.json)

```
OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17=true
BASE_SHA=0f36c93f76a08ae306a49b294ef300aa3e8dcc5c
AUDIT_UTC=2026-07-17T15:18:32Z
PERMISSION_MODE=read_only
SECRET_VALUES_READ=false
CREDENTIAL_VALUES_READ=false
OKX_MUTATIONS_PERFORMED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
OKX_ENVIRONMENT=mixed_public_prod_md_plus_eea_demo_prod_bindings_offline
```

## 1. Scope and method

Strict read-only forensic audit of the Peak_Trade OKX integration surface on `origin/main` at `BASE_SHA` above.

- Worktree was clean; no trading-core, execution-semantics, economic-gate, or GitHub-settings mutation.
- No order/amend/cancel/transfer/leverage/margin/position-mode/subaccount/withdrawal calls.
- No private Nutzdaten dumps; open orders/algos/positions only as BOOLEAN/COUNT/`NOT_VERIFIABLE`.
- Credential checks are presence-only (`PRESENT` / `ABSENT` / `NOT_VERIFIABLE`); values never read, hashed, masked, or persisted.
- Private REST/WS probes skipped when not unambiguously safe or when credentials ABSENT.
- Runtime Bridge remains `BOUND_NOT_ACTIVATED`.

## 2. Repo authority inventory

### 2.1 Canonical owners (reuse-before-new)

| Layer | Owner | Productive network I/O |
|---|---|---|
| Venue / instrument SSOT | `src/ops/bounded_futures_testnet_venue_binding_v0.py` | No |
| Adapter lifecycle / reconciliation FSM | `src/ops/okx_europe_adapter_lifecycle_contract_v0.py` | No (`NETWORK_CALL_COUNT=0`) |
| AWS shadow/paper/testnet structural binding | `src/ops/aws_shadow_paper_testnet_okx_europe_compatibility_contract_v0.py` | No |
| Config profile | `config/config.toml` → `[exchange.okx_europe_eea]` (`enabled=false`) | N/A |
| Public futures market-data ingest | `scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py` | Yes — public GET allowlist on `https://www.okx.com` |
| Research public fetchers | `src&#47;research&#47;okx_*` / panel materializers | Yes — public GET / CDN archive |
| Mock execution adapter (legacy) | `src/execution/adapters/providers/okx_v1.py` | No (offline mocks) |

### 2.2 Explicitly absent / non-implemented live clients

| Surface | Status |
|---|---|
| Signed private REST trade/account client | **Absent** (policy strings only in lifecycle SSOT) |
| Live OKX WebSocket client (public/private) | **Absent** as repo client; hosts only in config/contracts |
| Live order placement / cancel path | **Forbidden** / offline-inert (`AUTOMATIC_ORDER_RESEND_ALLOWED=false`) |

### 2.3 Environment / host bindings

| Binding | Value | Class |
|---|---|---|
| Research public MD base | `https://www.okx.com` | production public MD |
| EEA REST host | `https://eea.okx.com` | EEA venue target |
| EEA public WS | `wss:&#47;&#47;wseeapap.okx.com:8443&#47;ws&#47;v5&#47;public` | demo/public WS |
| EEA private WS | `wss:&#47;&#47;wseeapap.okx.com:8443&#47;ws&#47;v5&#47;private` | config only; not probed with login |
| Simulation header | `x-simulated-trading: 1` | demo routing (used once on public GET instruments only) |
| Exchange enabled | `false` | fail-closed |
| Validate only | `true` | fail-closed |
| Production instrument | `ETH-USD_UM_XPERP-310404` | futures X-Perp |
| Demo instrument | `ETH-USD_UM_XPERP-310328` | futures X-Perp |

### 2.4 Credential env var names (values never read)

| Name | Presence (process env) |
|---|---|
| `OKX_EEA_PUBLIC_API_KEY` | `ABSENT` |
| `OKX_EEA_READONLY_API_KEY` | `ABSENT` |
| `OKX_EEA_READONLY_API_SECRET` | `ABSENT` |
| `OKX_EEA_READONLY_API_PASSPHRASE` | `ABSENT` |
| `OKX_EEA_TRADE_API_KEY` | `ABSENT` |
| `OKX_EEA_TRADE_API_SECRET` | `ABSENT` |
| `OKX_EEA_TRADE_API_PASSPHRASE` | `ABSENT` |
| `OKX_API_KEY` (legacy deny surface) | `ABSENT` |
| `OKX_API_SECRET` (legacy deny surface) | `ABSENT` |

No `.env` / `.secrets` files present in workspace root at audit time.

### 2.5 Allowed read-only probes (executed)

- `GET &#47;api&#47;v5&#47;public&#47;time` — `www.okx.com`, `eea.okx.com`
- `GET &#47;api&#47;v5&#47;public&#47;instruments` — SWAP/SPOT/FUTURES as applicable
- `GET &#47;api&#47;v5&#47;market&#47;ticker?instId=ETH-USDT-SWAP` — `www.okx.com`
- Public WebSocket subscribe `tickers` / `ETH-USDT-SWAP` — global + EEA public hosts; ping/pong; unsubscribe/close
- One public `GET ...&#47;instruments?instType=FUTURES` with `x-simulated-trading: 1` (no auth headers) to verify demo instrument visibility

### 2.6 Explicitly forbidden mutations (not performed)

Order place/amend/cancel, algo order channels, transfer, withdrawal, leverage set, margin mode, position mode, subaccount mutations, private WS login-side mutations, credential rotation, scheduler/trading activation, Runtime Bridge activation.

## 3. Live / static findings

### 3.1 REST public

| Probe | Result |
|---|---|
| `www` public time | `MATCH` (HTTP 200, code `0`) |
| `www` SWAP instruments | `MATCH` (count=427) |
| `www` SPOT instruments metadata | reachable (count=1308); **not** a productive Spot binding |
| `www` ticker `ETH-USDT-SWAP` | `MATCH` |
| `eea` public time | `MATCH` |
| `eea` SWAP instruments | `MATCH` (count=427) |
| `eea` FUTURES prod `ETH-USD_UM_XPERP-310404` | `MATCH` (exact id present without sim header) |
| `eea` FUTURES demo `ETH-USD_UM_XPERP-310328` | `MATCH` (exact id present **with** sim header; absent without) |

`REST_PUBLIC_REACHABLE=true`  
`REST_PRIVATE_AUTHENTICATED=false` (credentials ABSENT; no private client; private endpoints not called)

### 3.2 WebSocket

| Probe | Result |
|---|---|
| Global public WS connect/subscribe/data/heartbeat/close | `MATCH` (`wss:&#47;&#47;ws.okx.com:8443&#47;ws&#47;v5&#47;public`) |
| EEA public WS connect/subscribe/data/heartbeat/close | `MATCH` (`wss:&#47;&#47;wseeapap.okx.com:8443&#47;ws&#47;v5&#47;public`) |
| Private WS authenticated session | `NOT_VERIFIABLE` (no repo private client; credentials ABSENT; login not attempted) |

Reconnect storm / long-soak not exercised (bounded audit). Fail-closed reconnect policy exists as offline contract text only.

### 3.3 Reconciliation / fail-closed (static + contract constants)

| Check | Result |
|---|---|
| Lifecycle `NETWORK_CALL_COUNT` | `0` |
| `UNKNOWN_REMOTE_STATE_FAIL_CLOSED` | `true` |
| `AUTOMATIC_ORDER_RESEND_ALLOWED` | `false` |
| `RUNTIME_GO_READY` | `false` |
| `PROMOTION_ALLOWED` | `false` |
| Venue binding network/orders | forbidden |
| Implicit order freigabe on unknown remote state | blocked by contract |
| Dynamic live reconciliation against private account/orders/positions | `NOT_VERIFIABLE` (no private auth) |

`RECONCILIATION_VERIFIED=static_contract_only`  
`FAIL_CLOSED_VERIFIED=true` (static owners)  
`RUNTIME_BRIDGE_ACTIVATED=false` (`BOUND_NOT_ACTIVATED`)

### 3.4 Futures-only / BTC / Spot

| Check | Result |
|---|---|
| Repo venue + lifecycle forbid BTC/XBT + Spot markers | `MATCH` |
| Research ingest forbid `btc`/`spot` substrings; SWAP futures MD | `MATCH` |
| Productive EEA binding instrument | ETH X-Perp futures only | `MATCH` |
| Live venue offers BTC-like SWAP metadata | count=3 (catalog only; not bound) |
| Live venue offers Spot catalog | count=1308 (catalog only; not bound) |
| Mock adapter `markets=["spot","perp"]` | `DRIFT` (legacy mock capability advert; not EEA live binding) |
| Index candle pair `ETH-USDT` in public MD join | documented index join — not Spot order binding |

`FUTURES_ONLY_MATCH=true` (productive binding/policy)  
`BTC_EXCLUSION_MATCH=true` (productive binding/policy)  
`SPOT_EXPOSURE_DETECTED=false` (no productive Spot trading binding)

### 3.5 Open orders / algos / positions

| Surface | Result |
|---|---|
| Open orders | `NOT_VERIFIABLE` |
| Open algo orders | `NOT_VERIFIABLE` |
| Open positions | `NOT_VERIFIABLE` |

No private account endpoints called. Nothing cancelled or closed.

## 4. Soll/Ist matrix

| ID | Expected | Classification |
|---|---|---|
| `venue_exchange_enabled_false` | `[exchange.okx_europe_eea].enabled=false` | `MATCH` |
| `venue_binding_eth_xperp_offline` | offline ETH X-Perp SSOT | `MATCH` |
| `lifecycle_fail_closed_offline` | unknown-remote fail-closed; no auto-resend | `MATCH` |
| `public_rest_www_reachable` | public time/instruments/ticker | `MATCH` |
| `public_rest_eea_reachable` | public time + FUTURES instruments | `MATCH` |
| `eea_production_xperp_instrument` | `ETH-USD_UM_XPERP-310404` live | `MATCH` |
| `eea_demo_xperp_instrument` | `ETH-USD_UM_XPERP-310328` via sim header | `MATCH` |
| `public_websocket_reachable` | public subscribe lifecycle | `MATCH` |
| `futures_only_btc_exclusion_policy` | static policy enforcement | `MATCH` |
| `runtime_bridge_bound_not_activated` | bridge not activated | `MATCH` |
| `mock_okx_adapter_spot_markets_flag` | futures-only productive surface | `DRIFT` |
| `private_account_state_readable` | readonly account/orders/positions | `NOT_VERIFIABLE` |
| `open_orders_absence_confirmed` | zero open orders affirmable | `NOT_VERIFIABLE` |
| `open_positions_absence_confirmed` | zero open positions affirmable | `NOT_VERIFIABLE` |

**Counts**

| Metric | Value |
|---|---|
| Repo expected components scored | 14 |
| MATCH | 10 |
| DRIFT | 1 |
| MISSING | 0 |
| ACCESS_DENIED | 0 |
| NOT_VERIFIABLE | 3 |

## 5. Safety conclusion

| Flag | Value | Rationale |
|---|---|---|
| `CREDENTIAL_VALUES_READ` | `false` | presence-only |
| `OKX_MUTATIONS_PERFORMED` | `false` | GET/public WS only |
| `LIVE_AUTHORIZED` | `false` | unchanged |
| `ORDERS_ENABLED` | `false` | unchanged |
| `RUNTIME_BRIDGE_ACTIVATED` | `false` | `BOUND_NOT_ACTIVATED` |
| `TRADING_CORE_CHANGED` | `false` | docs/governance only |
| `EXECUTION_SEMANTICS_CHANGED` | `false` | docs/governance only |
| `ECONOMIC_GATE_CHANGED` | `false` | docs/governance only |
| `GITHUB_SETTINGS_MUTATED` | `false` | no settings API use |

## 6. Next action

`OPERATOR_SUPPLY_OKX_EEA_READONLY_CREDENTIALS_FOR_PRIVATE_RO_PROBE_OR_ACCEPT_PARTIAL_PRIVATE_NOT_VERIFIABLE`

Private authenticated REST/WS, account mode, position mode, and open order/position counts remain `NOT_VERIFIABLE` until readonly credentials are present in the audit environment **and** a guaranteed non-mutating probe path is approved. Trade-scoped credentials must not be used for this audit class.
