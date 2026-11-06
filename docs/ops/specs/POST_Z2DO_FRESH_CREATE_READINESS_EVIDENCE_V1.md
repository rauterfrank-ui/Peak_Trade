---
docs_token: DOCS_TOKEN_POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1
status: active
scope: GET-only fresh Route-C create-readiness venue evidence; no POST; no live wire
capability: POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# Post-Z2DO Fresh Create-Readiness Evidence V1

## Goal

Collect one bounded read-only GET package on the Route-C Create credential
class and adjudicate whether the architecturally complete create path could
later be eligible for a separate risk-bearing Owner-GO.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
CURRENT_PRODUCTIVE_WIRE_REACHABLE=false
CREATE_PATH_CURRENTLY_AUTHORIZED=false
CREATE_PATH_ARCHITECTURALLY_COMPLETE=true
PREREQUISITE_08_CLOSED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

Master V2 &#47; Double Play remain sole Trading &#47; Decision Authority.
STEP-29P remains sole Risk &#47; Sizing Authority. STEP-29Q remains PLAN_ONLY.
This package does not choose a trade quantity and does not replace 29P with
venue max-available.

Credential class:
`LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY`.
SecretRef:
`secretref:&#47;&#47;vault&#47;peak-trade&#47;live-canary-minimum-exposure&#47;okx`.
No Shadow-Recon substitution.

## Out of scope

- POST &#47; order submit &#47; position creation &#47; flatten
- Leverage SET &#47; account-mode SET &#47; position-mode SET
- Funding GET (`&#47;api&#47;v5&#47;asset&#47;balances`) — not required by the
  Create-readiness AVAILABLE_MARGIN contract
- Manufacturing `posSide=net`
- Live &#47; Testnet &#47; Canary activation
- Merge

## Productive owners

| Surface | Owner |
| --- | --- |
| Package executor | `src&#47;ops&#47;section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1&#47;execute_v1.py` |
| Adjudication | `src&#47;ops&#47;section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1&#47;adjudicate_v1.py` |
| HTTP client | `LiveCanaryHttpClientV1` |
| Signer | `build_okx_live_canary_auth_headers_v1` |
| Position classifier | `classify_target_position_state_v1` |
| Category-C observer | `observe_category_c_open_algo_pending_v1` |

## Fresh observation pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/20260903T114921Z/
GET_REQUEST_COUNT=12
PUBLIC_GET_COUNT=3
PRIVATE_GET_COUNT=9
FUNDING_GET_PERFORMED=false
POST_PERFORMED=false
HOST=eea.okx.com
CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY
```

## Safety claims

```text
CREATE_ACCOUNT_IDENTITY_READY=true
POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN
POSITION_MODE_FAIL_CLOSED=true
POSITION_MODE_READY=false
PRETRADE_GATES_READY=false
FUNDING_EXPOSURE_READY=false
VENUE_NONZERO_CAPACITY=PROVEN_ZERO
CURRENT_ROUTE_C_QUANTITY_ADMISSIBILITY=BLOCKED_BY_VENUE_CAPACITY
PREREQUISITE_08_CLOSED=false
CREATE_READINESS_AFTER_FRESH_EVIDENCE=BLOCKED_BY_MULTIPLE_GAPS
CREATE_PATH_ARCHITECTURALLY_COMPLETE=true
CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=false
CURRENT_PRODUCTIVE_WIRE_REACHABLE=false
CREATE_PATH_CURRENTLY_AUTHORIZED=false
```
