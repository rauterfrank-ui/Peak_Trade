---
docs_token: DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_CURRENT_ORIGIN_MAIN_BOUND_GET_ONLY_PRETRADE_ACCOUNT_NETWORK_AND_INSTRUMENT_READINESS_V1
status: active
scope: §11.14 current-origin&#47;main bound GET-only pretrade account, network and instrument readiness; no POST; no submit; no Owner-GO consumption; no Live&#47;canary arming mutation; no Master Runbook SSOT rewrite
capability: SECTION_11_14_LIVE_HANDOFF_CURRENT_ORIGIN_MAIN_BOUND_GET_ONLY_PRETRADE_ACCOUNT_NETWORK_AND_INSTRUMENT_READINESS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-07
---

# Section 11.14 Current Origin Main Bound GET-Only Pretrade Readiness V1

## Goal

Close the Class-A gap that existing GET surfaces cannot be invoked against
current `origin&#47;main` without consuming a frozen Owner-GO and&#47;or
rewriting an obsolete `EXPECTED_ORIGIN_MAIN_SHA`, and that canary submit
transport mixes GET with POST.

This derived spec is **not** SSOT. It does **not** rewrite Master Runbook
§11.14 semantics. It does **not** authorize submit, POST, capture, restart,
or Owner-Execution-GO.

```text
CORE_LOGIC_CHANGE=true
ACTIVATION_STATE=not_activated
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
POST_ALLOWED=false
OWNER_GO_REQUIRED=false
OWNER_GO_CONSUMED=false
GET_ONLY=true
POST_PERFORMED=false
LIVE_SUBMIT_EXECUTED=false
OWNER_EXECUTION_AUTHORIZED=false
MUTATING_EXECUTION_ALLOWED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
MAP_OF_TRUTH_AUTHORITY=NONE
```

## Surface properties

- Current `origin&#47;main` SHA is recorded as evidence, not as a hardcoded
  obsolete SHA gate.
- No consumed Owner-GO is required or accepted as runtime arming.
- Method allowlist is GET only. POST is fail-closed before wire.
- Endpoint path allowlist is explicit.
- Raw GET log and adjudicated predicates are persisted separately.
- Historical evidence is rejected as CURRENT.
- Missing or invalid responses are `INDETERMINATE` or `FAIL_CLOSED`, never
  implicit PASS.
- Standing fee and slippage policy are bound by the successor envelope
  workpackage; this GET-only surface now allowlists `trade-fee` as a
  read-only input and still does **not** authorize submit.

## Endpoint allowlist

- `&#47;api&#47;v5&#47;public&#47;instruments`
- `&#47;api&#47;v5&#47;market&#47;ticker`
- `&#47;api&#47;v5&#47;public&#47;price-limit`
- `&#47;api&#47;v5&#47;account&#47;config`
- `&#47;api&#47;v5&#47;account&#47;balance`
- `&#47;api&#47;v5&#47;account&#47;positions`
- `&#47;api&#47;v5&#47;account&#47;leverage-info`
- `&#47;api&#47;v5&#47;account&#47;max-size`
- `&#47;api&#47;v5&#47;account&#47;trade-fee`

## Rejected existing surfaces for this workpackage

- §11.14 `private_read_only_gets_v1` — Owner-GO plus obsolete SHA plus POST-capable client
- P08 read-only closure — frozen SHA / frozen GO
- §11.13.2 execute CLI — Owner-GO; incomplete pretrade allowlist
- Canary `submit_transport_v1` / `LiveCanaryHttpClientV1` — GET+POST mixed

Reusable without invoking those runners: observation parsers, query-path
builders, SecretRef loader, GET signing primitive, instrument binding, and
the §11.13.2 GET-only HTTP pattern.

## Safety

```text
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
POST_ALLOWED=false
OWNER_EXECUTION_AUTHORIZED=false
MAX_SUBMIT_ATTEMPTS=1
MAX_SUCCESSFUL_SUBMITS=1
RETRY_AFTER_TIMEOUT=false
```
