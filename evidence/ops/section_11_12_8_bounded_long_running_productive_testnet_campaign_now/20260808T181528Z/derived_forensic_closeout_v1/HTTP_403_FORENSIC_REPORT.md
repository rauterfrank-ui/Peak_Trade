# HTTP 403 Forensic Report — §11.12.8 Run `20260808T181528Z`

```text
DOCUMENT_CLASS=DERIVED_FORENSIC_REPORT
RUNTIME_AUTHORIZATION_EFFECT=NONE
NETWORK_EFFECT=NONE
ORDER_EFFECT=NONE
LIVE_ORDER_EFFECT=NONE
PRIMARY_EVIDENCE_IMMUTABLE=true
ORIGIN_MAIN_SHA=43f9517b4ea2c501490fe4aacb424741d2311c71
GENERATED_AT_UTC=2026-08-08T19:38:07Z
```

## Executive classification

`HTTP_403_CLASSIFICATION=TRANSPORT_OR_GATEWAY_HTTP_403_NON_JSON_BODY_NOT_EXCHANGE_SEMANTIC_REJECT`

Top cause: `C403_TRANSPORT_GATEWAY_OR_WAF_DENIAL_NON_JSON_BODY` (`CONFIDENCE=HIGH`).

This is a **transport/gateway HTTP 403** with a **non-JSON** body sentinel (`_raw_unparsed`). It is **not** an OKX exchange-semantic order reject (`code`/`sCode` absent). Therefore `ORDER_REJECT_COUNT=0` is correct. No ACK, fill, or exchange order ID was fabricated.

## Confirmed facts from sealed primary evidence

| Fact | Value |
| --- | --- |
| Host/base | `https://eea.okx.com` |
| Live hosts blocked | true |
| Endpoint (inferred allowlist + venue-native order) | `POST &#47;api&#47;v5&#47;trade&#47;order` |
| Instrument | `BTC-USDT-SWAP` |
| Wire sent | true |
| HTTP status | 403 |
| Exchange code / sCode | null / null |
| Classification recorded | `EXCHANGE_RESPONSE_INCONCLUSIVE` |
| Cycles | 60 |
| Duration seconds | 3600.494202666 |
| LIVE_ORDER_EFFECT | NONE |
| SECTION_11_13_STARTED | false |

## Evidence gaps (do not invent)

- Response **headers** not persisted
- Request **timestamp** / sign prehash not persisted
- Numeric `body_bytes` value not retained in sealed effect (only key name in `raw_keys`)
- Simulation header presence not attested in sealed evidence (code path includes it)

## Why ORDER_REJECT_COUNT stayed 0

Mapper ACK requires `code==0` and `sCode==0` and `ordId`. Mapper REJECT requires non-zero exchange/`sCode`. HTTP 403 without those fields is inconclusive/transport-class, not REJECT.

## Offline structural checks (no network)

- Testnet host allowlist + live hard-block present in `bound_testnet_http_client_v1.py`
- Auth header names set: `OK-ACCESS-KEY|SIGN|TIMESTAMP|PASSPHRASE`
- Simulation header constants: `x-simulated-trading: 1`
- Sign prehash: `timestamp + METHOD + path + body`

## Root vs precision

| Item | Code change? | External account/credential check? |
| --- | --- | --- |
| HTTP 403 root | **No** | **Yes** |
| `_raw_unparsed` classified as body_parsed/INCONCLUSIVE | **Yes** (forensic precision only) | No |

## NEXT_CANONICAL_STEP

`OWNER_GO_RESOLVE_EXTERNAL_OKX_TESTNET_ACCOUNT_OR_CREDENTIAL_BLOCKER_AND_RETRY_TARGETED_PROOF`

Rationale: highest-confidence blocker is external (account/credential/permission/IP/WAF). After operator resolves Demo trade-capable binding, a **targeted** Testnet proof is required. §11.12.8 remains open; §11.13 unstarted.
