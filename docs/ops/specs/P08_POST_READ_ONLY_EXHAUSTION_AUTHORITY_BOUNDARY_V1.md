---
docs_token: DOCS_TOKEN_P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1
status: active
scope: Offline P08 post-read-only-exhaustion authority-boundary adjudication; no POST; no P08 close
capability: P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-03
---

# P08 Post-Read-Only-Exhaustion Authority Boundary V1

## Goal

After `P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED`, determine the exact
next authority boundary required to make
`TARGET_POSITION_NONZERO_PROVEN=true` possible. Do not create the required
state. Do not repeat equivalent unfiltered `&#47;account&#47;positions`
empty-envelope probes.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_EXECUTED_THIS_PERSIST=false
ORDER_PERFORMED=false
POSITION_CREATION_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
PREREQUISITE_08_CLOSED=false
TARGET_POSITION_ZERO_PROVEN=false
TARGET_POSITION_NONZERO_PROVEN=false
G_POSMODE_SUBMIT_BODY_PROVEN=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EMPTY_DATA_IS_ZERO=false
P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED
P08_NEXT_AUTHORITY_RESULT=EXTERNAL_STATE_APPEARANCE_SUFFICIENT
MINIMUM_HIGHER_AUTHORITY=EXTERNAL_MANUAL_POSITION_APPEARANCE
```

## Authority

Reuses `classify_target_position_state_v1`,
`classify_position_observation_v1`, Z2DN source-irrelevant observation
policy, Z2DP create-readiness evidence, P08 empty-data and read-only
packs, Route-C G-POSMODE fail-closed census, and standing live-canary
constants. Does not authorize POST, flatten, P09 work, funding, whitelist
mutation, Live, Testnet, or Canary execute.

## Closure condition

Canonical P08 close remains CASE_A on unfiltered
`GET &#47;api&#47;v5&#47;account&#47;positions`: HTTP 200, OKX 0, exactly one
target-instrument row, canonically nonzero `pos`. Empty `data[]` is not
zero. Absent target row is not zero. Zero row does not close P08. Source
of the row is irrelevant if the observation is proven.

## Minimum higher authority

Testnet cannot satisfy P08 because P08 is bound to `eea.okx.com` live-canary
credentials. First-party Canary&#47;Live create remains blocked by
G-POSMODE submit-body UNPROVEN plus standing `LIVE_ENABLED=false` /
`SUBMIT_UNLOCKED=false`. External manual venue appearance is the lowest
semantically capable and technically supported class.

## Out of scope

- POST &#47; order submit &#47; position creation &#47; flatten
- Repeating unfiltered, instId, or instType `&#47;account&#47;positions`
- Funding GET &#47; transfer &#47; credential or whitelist mutation
- Consuming the drafted future Owner-GO
- Merge
- Master V2 &#47; Double Play Core mutation

## Productive owners

| Surface | Owner |
| --- | --- |
| Closure-condition proof | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;closure_condition_v1.py` |
| Mechanism census | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;mechanism_census_v1.py` |
| Readiness snapshot | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;readiness_v1.py` |
| Authority-boundary selector | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;authority_boundary_v1.py` |
| Future-GO draft | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;future_go_draft_v1.py` |
| Evidence persist | `src&#47;ops&#47;section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1&#47;persist_v1.py` |

## Bound pack

```text
EVIDENCE_PACK=evidence/ops/section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1/20260903T212800Z/
OWNER_GO_CONSUMED=true
GET_REQUEST_COUNT=0
POST_COUNT=0
P08_CLOSED=false
P08_NEXT_AUTHORITY_RESULT=EXTERNAL_STATE_APPEARANCE_SUFFICIENT
MINIMUM_HIGHER_AUTHORITY=EXTERNAL_MANUAL_POSITION_APPEARANCE
STATE_APPEARANCE_MECHANISM_COUNT=15
VIABLE_MECHANISM_COUNT=1
FUTURE_EXECUTION_GO_DRAFT_STATUS=COMPLETE
FUTURE_GO_AUTHORIZES_POST=false
FLATTEN_REQUIRES_SEPARATE_OWNER_GO=true
```
