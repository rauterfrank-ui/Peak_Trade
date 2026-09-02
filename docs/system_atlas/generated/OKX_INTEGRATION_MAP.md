<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

# OKX Integration Map

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

OKX is a first-class venue domain. XPERP is one product/instrument family, not the organizing center.

`OKX_CENSUS_COMPLETE=true`  
`OKX_CENSUS_SCOPE=current_origin_main_tree_literal_path_and_host_search plus bounded git name-search for *okx* plus forensic persistence inventories plus docs&#47;audits&#47;OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md plus config&#47;config.toml [exchange.okx_europe_eea]; not exhaustive blob-history of every deleted non-okx-named module; in-repo fixture&#47;docs&#47;tests&#47;config&#47;product-type inventories closed. External&#47;temp forensic corpus is NOT_STARTED.`

```text
OKX_RAW_API_PATH_HIT_COUNT=70
OKX_UNIQUE_ENDPOINT_CANDIDATE_COUNT=49
OKX_MODELED_ENDPOINT_COUNT=50
OKX_GREP_NOISE_COUNT=21
OKX_UNCLASSIFIED_ENDPOINT_COUNT=0
OKX_FIELD_TOKEN_COUNT=42
OKX_MODELED_FIELD_COUNT=40
OKX_UNCLASSIFIED_MATERIAL_FIELD_COUNT=0
OKX_FIXTURE_CANDIDATE_COUNT=147
OKX_CONFIRMED_FIXTURE_COUNT=16
OKX_RAW_RESPONSE_COUNT=2
OKX_DISTINCT_RESPONSE_SHAPE_COUNT=6
OKX_UNCLASSIFIED_FIXTURE_COUNT=0
OKX_FIXTURE_BYTES_OR_STRUCTURE_INSPECTED_COUNT=147
OKX_UNINSPECTED_MATERIAL_FIXTURE_COUNT=0
OKX_PRODUCT_TYPE_CENSUS_COMPLETE=true
```

## Product types (Peak_Trade evidence)

| product_type | status | canonical_support | runtime_reachability |
| --- | --- | --- | --- |
| SWAP | IMPLEMENTED | PRODUCTIVE_GFU_SUPPORTED_INST_TYPES | GFU_AND_PUBLIC_MD |
| FUTURES | IMPLEMENTED | PRODUCTIVE_GFU_SUPPORTED_INST_TYPES | GFU_SUPPORTED |
| SPOT | UNSUPPORTED |  | EXPLICIT_GFU_REJECT |
| MARGIN | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | NONE_AS_OKX_INSTTYPE |
| OPTION | SEARCHED_BUT_NO_EVIDENCE_FOUND |  | NONE_AS_OKX_INSTTYPE |
| xperp | PARTIALLY_IMPLEMENTED | NOT_A_SEPARATE_INSTTYPE | CANARY_HARDCODED_NOT_GFU_MEMBERSHIP_PROVEN |

## Hosts

| id | name | status | epistemic |
| --- | --- | --- | --- |
| OKX_HOST:aws_okx_com | aws.okx.com | OPEN | STATUS=FORENSIC_RAW |
| OKX_HOST:eea_okx_com | eea.okx.com | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |
| OKX_HOST:openapi_okx_com | openapi.okx.com | OPEN | STATUS=FORENSIC_RAW |
| OKX_HOST:static_okx_com | static.okx.com | OPEN | STATUS=FORENSIC_RAW |
| OKX_HOST:tr_okx_com | tr.okx.com | HISTORICAL_ONLY | STATUS=FORENSIC_RAW |
| OKX_HOST:us_okx_com | us.okx.com | HISTORICAL_ONLY | STATUS=FORENSIC_RAW |
| OKX_HOST:wseeapap | wseeapap.okx.com:8443 | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |
| OKX_HOST:www_okx_com | www.okx.com | CURRENT_NONCANONICAL | STATUS=FORENSIC_RAW |

## Auth / signing (no secrets)

Scheme `HMAC-SHA256`; signer `sign_okx_request_v1`; demo header `x-simulated-trading`; auth_inventory_complete=true. Credential values are not recorded.

## Features

| id | category | status | auth |
| --- | --- | --- | --- |
| OKX_FEATURE:account_balance | account | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:account_config | account | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:account_positions | positions | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:algo_order | algo_orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:asset_balances | assets | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:asset_transfer | assets | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:asset_withdrawal | assets | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:cancel_order | orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:candles | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:close_position | orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:demo_simulated_trading_header | authentication | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:execution_adapter_mocks_only | execution_adapter | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:fills | orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:funding_rate_history | funding | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:history_candles | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:history_mark_price_candles | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:hmac_auth | authentication | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:orderbook | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:orders_pending | orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:place_order | orders | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:position_tiers_mmr | risk_margin | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:price_limit | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:public_instruments | instrument_discovery | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:public_mark_price | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:public_time | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:quote_identity_from_quoteCcy_or_instId | instrument_identity | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:rubik_open_interest | research | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:set_leverage | leverage | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:subaccount_list | account | CURRENT_NONCANONICAL | True |
| OKX_FEATURE:tickers | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:trades | market_data | CURRENT_NONCANONICAL |  |
| OKX_FEATURE:websocket_hosts_configured | websocket | CURRENT_NONCANONICAL | OPEN |
| OKX_FEATURE:xperp_instid_pattern | instrument_identity | CURRENT_NONCANONICAL |  |

## Endpoints

| id | method | path | domain | mutation | status |
| --- | --- | --- | --- | --- | --- |
| VENUE_ENDPOINT:okx_account_account_position_risk | GET | /api/v5/account/account-position-risk | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_adjust_leverage_info | GET | /api/v5/account/adjust-leverage-info | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_balance | GET | /api/v5/account/balance | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_bills | GET | /api/v5/account/bills | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_config | GET | /api/v5/account/config | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_instruments | GET | /api/v5/account/instruments | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_leverage_info | GET | /api/v5/account/leverage-info | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_max_avail_size | GET | /api/v5/account/max-avail-size | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_max_size | GET | /api/v5/account/max-size | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_positions | GET | /api/v5/account/positions | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_positions_history | GET | /api/v5/account/positions-history | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_set_isolated_mode | POST | /api/v5/account/set-isolated-mode | account | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_set_leverage | POST | /api/v5/account/set-leverage | account | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_set_position_mode | POST | /api/v5/account/set-position-mode | account | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_account_trade_fee | GET | /api/v5/account/trade-fee | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_asset_balances | GET | /api/v5/asset/balances | asset | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_asset_currencies | GET | /api/v5/asset/currencies | asset | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_asset_transfer | POST | /api/v5/asset/transfer | asset | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_asset_withdrawal | POST | /api/v5/asset/withdrawal | asset | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_books | GET | /api/v5/market/books | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_candles | GET | /api/v5/market/candles | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_history_candles | GET | /api/v5/market/history-candles | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_history_index_candles | GET | /api/v5/market/history-index-candles | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_history_mark_price_candles | GET | /api/v5/market/history-mark-price-candles | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_index_tickers | GET | /api/v5/market/index-tickers | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_ticker | GET | /api/v5/market/ticker | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_tickers | GET | /api/v5/market/tickers | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_market_trades | GET | /api/v5/market/trades | market | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_funding_rate_history | GET | /api/v5/public/funding-rate-history | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_instruments | GET | /api/v5/public/instruments | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_mark_price | GET | /api/v5/public/mark-price | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_position_tiers | GET | /api/v5/public/position-tiers | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_price_limit | GET | /api/v5/public/price-limit | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_time | GET | /api/v5/public/time | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_rubik_stat_contracts_open_interest_history | GET | /api/v5/rubik/stat/contracts/open-interest-history | rubik | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_amend_order | POST | /api/v5/trade/amend-order | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_batch_orders | POST | /api/v5/trade/batch-orders | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_cancel_batch_orders | POST | /api/v5/trade/cancel-batch-orders | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_cancel_order | POST | /api/v5/trade/cancel-order | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_close_position | POST | /api/v5/trade/close-position | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_fills | GET | /api/v5/trade/fills | trade | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_order | POST | /api/v5/trade/order | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_order_algo | POST | /api/v5/trade/order-algo | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_order_get | GET | /api/v5/trade/order | trade | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_order_precheck | POST | /api/v5/trade/order-precheck | trade | MUTATING | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_orders_algo_pending | GET | /api/v5/trade/orders-algo-pending | trade | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_orders_history | GET | /api/v5/trade/orders-history | trade | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_orders_pending | GET | /api/v5/trade/orders-pending | trade | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_users_self_verify | GET | /api/v5/users/self/verify | users | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_users_subaccount_list | GET | /api/v5/users/subaccount/list | users | READ_AUTH | CURRENT_NONCANONICAL |

## Fields

| id | field | identity_role | status |
| --- | --- | --- | --- |
| VENUE_FIELD:askPx | askPx | ask_price | STATUS=FORENSIC_RAW |
| VENUE_FIELD:availBal | availBal | available_balance | STATUS=FORENSIC_RAW |
| VENUE_FIELD:avgPx | avgPx | average_price | STATUS=FORENSIC_RAW |
| VENUE_FIELD:baseCcy | baseCcy | base_currency | STATUS=FORENSIC_RAW |
| VENUE_FIELD:bidPx | bidPx | bid_price | STATUS=FORENSIC_RAW |
| VENUE_FIELD:clOrdId | clOrdId | client_order_id | STATUS=FORENSIC_RAW |
| VENUE_FIELD:code | code | okx_response_code | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ctMult | ctMult | contract_multiplier | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ctType | ctType | contract_type | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ctVal | ctVal | contract_value | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ctValCcy | ctValCcy | contract_value_currency | STATUS=FORENSIC_RAW |
| VENUE_FIELD:expTime | expTime | expiry_timestamp | STATUS=FORENSIC_RAW |
| VENUE_FIELD:instFamily | instFamily | okx_instrument_family | STATUS=FORENSIC_RAW |
| VENUE_FIELD:instId | instId | instrument_id | STATUS=FORENSIC_RAW |
| VENUE_FIELD:instType | instType | product_type | STATUS=FORENSIC_RAW |
| VENUE_FIELD:last | last | OPEN | STATUS=FORENSIC_RAW |
| VENUE_FIELD:lever | lever | leverage | STATUS=FORENSIC_RAW |
| VENUE_FIELD:lotSz | lotSz | lot_size | STATUS=FORENSIC_RAW |
| VENUE_FIELD:markPx | markPx | mark_price | STATUS=FORENSIC_RAW |
| VENUE_FIELD:mgnMode | mgnMode | margin_mode | STATUS=FORENSIC_RAW |
| VENUE_FIELD:minSz | minSz | min_size | STATUS=FORENSIC_RAW |
| VENUE_FIELD:mmr | mmr | maintenance_margin_ratio_venue_field | STATUS=FORENSIC_RAW |
| VENUE_FIELD:msg | msg | okx_response_message | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ordId | ordId | order_id | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ordType | ordType | order_type | STATUS=FORENSIC_RAW |
| VENUE_FIELD:pos | pos | OPEN | STATUS=FORENSIC_RAW |
| VENUE_FIELD:posMode | posMode | position_mode | STATUS=FORENSIC_RAW |
| VENUE_FIELD:posSide | posSide | position_side | STATUS=FORENSIC_RAW |
| VENUE_FIELD:px | px | price | STATUS=FORENSIC_RAW |
| VENUE_FIELD:quoteCcy | quoteCcy | quote_currency | STATUS=FORENSIC_RAW |
| VENUE_FIELD:reduceOnly | reduceOnly | reduce_only_flag | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ruleType | ruleType | rule_type_xperp_observed | STATUS=FORENSIC_RAW |
| VENUE_FIELD:settleCcy | settleCcy | settlement_currency | STATUS=FORENSIC_RAW |
| VENUE_FIELD:side | side | OPEN | STATUS=FORENSIC_RAW |
| VENUE_FIELD:state | state | order_or_account_state | STATUS=FORENSIC_RAW |
| VENUE_FIELD:sz | sz | size | STATUS=FORENSIC_RAW |
| VENUE_FIELD:tdMode | tdMode | trade_mode | STATUS=FORENSIC_RAW |
| VENUE_FIELD:tickSz | tickSz | tick_size | STATUS=FORENSIC_RAW |
| VENUE_FIELD:ts | ts | timestamp | STATUS=FORENSIC_RAW |
| VENUE_FIELD:uly | uly | underlying_base_fallback_only | STATUS=FORENSIC_RAW |

## XPERP / uly / quote identity (not census scope)

See contradiction `C-OKX-QUOTE-ULY-001` and feature `OKX_FEATURE:quote_identity_from_quoteCcy_or_instId`.
