<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# OKX Feature Matrix

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

| FEATURE | FIRST_PROVEN_OCCURRENCE | CURRENT_IMPLEMENTATION | HISTORICAL_IMPLEMENTATION | PRODUCT_TYPES | ENDPOINTS | AUTH | CURRENT_STATUS | CANONICAL_SUPPORT | RUNTIME_REACHABLE | TESTED | FORENSIC_EVIDENCE | OPEN_GAPS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| account_balance | OPEN | GET /api/v5/account/balance | OPEN | n/a | GET /api/v5/account/balance | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| account_config | OPEN | GET /api/v5/account/config | OPEN | n/a | GET /api/v5/account/config | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| account_positions | OPEN | GET /api/v5/account/positions | OPEN | FUTURES | GET /api/v5/account/positions | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| algo_order | OPEN | POST /api/v5/trade/order-algo | OPEN | FUTURES | POST /api/v5/trade/order-algo | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| asset_transfer | OPEN | POST /api/v5/asset/transfer | OPEN | n/a | POST /api/v5/asset/transfer | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| asset_withdrawal | OPEN | POST /api/v5/asset/withdrawal | OPEN | n/a | POST /api/v5/asset/withdrawal | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| cancel_order | OPEN | POST /api/v5/trade/cancel-order | OPEN | FUTURES | POST /api/v5/trade/cancel-order | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| candles | OPEN | GET /api/v5/market/candles | OPEN | FUTURES,SWAP | GET /api/v5/market/candles |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| close_position | OPEN | POST /api/v5/trade/close-position | OPEN | FUTURES | POST /api/v5/trade/close-position | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| demo_simulated_trading_header | OPEN | x-simulated-trading | OPEN | n/a | x-simulated-trading | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| execution_adapter_mocks_only | OPEN | src/execution/adapters/providers/okx_v1.py | OPEN | n/a | src/execution/adapters/providers/okx_v1.py |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| fills | OPEN | GET /api/v5/trade/fills | OPEN | FUTURES | GET /api/v5/trade/fills | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| funding_rate_history | OPEN | GET /api/v5/public/funding-rate-history | OPEN | SWAP | GET /api/v5/public/funding-rate-history |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| history_candles | OPEN | GET /api/v5/market/history-candles | OPEN | FUTURES,SWAP | GET /api/v5/market/history-candles |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| history_mark_price_candles | OPEN | GET /api/v5/market/history-mark-price-candles | OPEN | FUTURES,SWAP | GET /api/v5/market/history-mark-price-candles |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| hmac_auth | OPEN | OK-ACCESS-* HMAC-SHA256 | OPEN | n/a | OK-ACCESS-* HMAC-SHA256 | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| orderbook | OPEN | GET /api/v5/market/books | OPEN | OPEN | GET /api/v5/market/books |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| orders_pending | OPEN | GET /api/v5/trade/orders-pending | OPEN | FUTURES | GET /api/v5/trade/orders-pending | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| place_order | OPEN | POST /api/v5/trade/order | OPEN | FUTURES | POST /api/v5/trade/order | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| position_tiers_mmr | OPEN | GET /api/v5/public/position-tiers | OPEN | FUTURES | GET /api/v5/public/position-tiers |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| price_limit | OPEN | GET /api/v5/public/price-limit | OPEN | FUTURES | GET /api/v5/public/price-limit |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| public_instruments | OPEN | GET /api/v5/public/instruments | OPEN | FUTURES,SWAP | GET /api/v5/public/instruments |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| public_mark_price | OPEN | GET /api/v5/public/mark-price | OPEN | FUTURES,SWAP | GET /api/v5/public/mark-price |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| public_time | OPEN | GET /api/v5/public/time | OPEN | n/a | GET /api/v5/public/time |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| quote_identity_from_quoteCcy_or_instId | OPEN | _extract_base_quote | OPEN | FUTURES,SWAP,XPERP | _extract_base_quote |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| rubik_open_interest | OPEN | GET /api/v5/rubik/stat/contracts/open-interest-history | OPEN | FUTURES,SWAP | GET /api/v5/rubik/stat/contracts/open-interest-history |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| set_leverage | OPEN | POST /api/v5/account/set-leverage | OPEN | FUTURES | POST /api/v5/account/set-leverage | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| subaccount_list | OPEN | GET /api/v5/users/subaccount/list | OPEN | n/a | GET /api/v5/users/subaccount/list | True | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| tickers | OPEN | GET /api/v5/market/tickers | OPEN | FUTURES,SWAP | GET /api/v5/market/tickers |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| trades | OPEN | GET /api/v5/market/trades | OPEN | FUTURES,SWAP | GET /api/v5/market/trades |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| websocket_hosts_configured | OPEN | wseeapap.okx.com:8443 | OPEN | OPEN | wseeapap.okx.com:8443 | OPEN | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |
| xperp_instid_pattern | OPEN | SUI-USD_UM_XPERP-310404 style ids | OPEN | XPERP | SUI-USD_UM_XPERP-310404 style ids |  | CURRENT_NONCANONICAL | OPEN | OPEN | OPEN | bounded | census_not_complete |

