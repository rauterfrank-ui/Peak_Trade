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
OKX_MODELED_ENDPOINT_COUNT=3
OKX_MODELED_FIELD_COUNT=3
OKX_FEATURE_COUNT=1
OKX_RESPONSE_SHAPE_COUNT=0
OKX_PRODUCT_TYPE_CENSUS_COMPLETE=true
```

## Product types (Peak_Trade evidence)

| product_type | status | canonical_support | runtime_reachability |
| --- | --- | --- | --- |
| FUTURES | CURRENT_MODEL | venue/okx | CURRENT |
| SWAP | CURRENT_MODEL | venue/okx | CURRENT |
| XPERP_as_ruleType_or_instId_family | CURRENT_MODEL | venue/okx | CURRENT |

## Hosts

| id | name | status | epistemic |
| --- | --- | --- | --- |
| _(none)_ | _ | _ | _ |

## Auth / signing (no secrets)

Scheme `HMAC-SHA256`; signer `sign_okx_request_v1`; demo header `x-simulated-trading`; auth_inventory_complete=true. Credential values are not recorded.

## Features

| id | category | status | auth |
| --- | --- | --- | --- |
| OKX_FEATURE:quote_identity_from_quoteCcy_or_instId | instrument_identity | CURRENT_NONCANONICAL |  |

## Endpoints

| id | method | path | domain | mutation | status |
| --- | --- | --- | --- | --- | --- |
| VENUE_ENDPOINT:okx_account_positions | GET | /api/v5/account/positions | account | READ_AUTH | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_public_instruments | GET | /api/v5/public/instruments | public | READ | CURRENT_NONCANONICAL |
| VENUE_ENDPOINT:okx_trade_order | POST | /api/v5/trade/order | trade | MUTATING | CURRENT_NONCANONICAL |

## Fields

| id | field | identity_role | status |
| --- | --- | --- | --- |
| VENUE_FIELD:instId | instId | instrument_id | STATUS=FORENSIC_RAW |
| VENUE_FIELD:quoteCcy | quoteCcy | quote_currency | STATUS=FORENSIC_RAW |
| VENUE_FIELD:uly | uly | underlying_base_fallback_only | STATUS=FORENSIC_RAW |

## XPERP / uly / quote identity (not census scope)

See contradiction `C-OKX-QUOTE-ULY-001` and feature `OKX_FEATURE:quote_identity_from_quoteCcy_or_instId`.
