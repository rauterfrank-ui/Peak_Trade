---
docs_token: DOCS_TOKEN_SECTION_11_14_PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC_V1
status: active
scope: §11.14 Owner Productive Wire-Send authority contract and future send-orchestrator/bind specification; schema defined; not issued; orchestrator not implemented; no POST; no session arming; no GET
capability: SECTION_11_14_PRODUCTIVE_WIRE_SEND_OWNER_CONTRACT_AND_ORCHESTRATOR_SPEC_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-08
---

# Section 11.14 Productive Wire-Send Owner Contract And Orchestrator Spec V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
AUTHORITY=NONE
MAP_OF_TRUTH_AUTHORITY=NONE
ATLAS_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
SECTION_11_14_AUTHORIZED=false
SECTION_11_14_COMPLETE=false
SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED=false
LIVE_ENABLED=false
LIVE_ARMED=false
CANARY_AUTHORIZED=false
POST_ALLOWED=false
OWNER_EXECUTION_AUTHORIZED=false
OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_ISSUED=false
OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_ACCEPTED=false
OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_CONSUMED=false
PRODUCER_IMPLEMENTED=false
ORCHESTRATOR_IMPLEMENTED=false
SEND_CAPABLE_BIND_IMPLEMENTED=false
GET_PERFORMED=false
POST_PERFORMED=false
LIVE_SUBMIT_EXECUTED=false
WIRE_SEND_EXECUTED=false
POSITION_MUTATION_EXECUTED=false
FLATTEN_EXECUTED=false
DURABLE_CONSUMED=false
SESSION_ARMING_EXECUTED=false
NETWORK_SESSION_AUTHORIZED=false
RESTART_EXECUTED=false
CRASH_TEST_EXECUTED=false
SUBMIT_ATTEMPT_COUNT=0
AUTOMATIC_RESUBMIT=false
RETRY_ALLOWED=false
SECOND_SUBMIT_ALLOWED=false
```

This spec is not SSOT. The Master Runbook persist is SSOT.

This slice defines a named Owner contract and the future orchestrator/bind
interface required to cross `PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR`.
It does **not** issue that authority. It does **not** implement send.

## A. Authority census (this package)

```text
EXISTING_SECTION_11_14_WIRE_SEND_OWNER_SCHEMA=false
EXISTING_REUSABLE_AUTHORITY_SCHEMA=OWNER_NETWORK_SESSION_AUTHORITY_V1_PARTIAL_PREDECESSOR_ONLY
NEW_OWNER_CONTRACT_REQUIRED=true
PROPOSED_OWNER_CONTRACT_NAME=OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1
```

| AUTHORITY_OR_GATE | SYMBOL_OR_SCHEMA | SOURCE_PATH | PRODUCER | CONSUMER | CURRENT_STATE | CURRENT_SEMANTICS | REUSABLE_FOR_11_14_WIRE_SEND | REASON |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| flatten execution | `OWNER_FLATTEN_ISSUANCE_V1` / `OWNER_FLATTEN_GO_CONTRACT_SCHEMA_V1` | `issuance_v1.py` | `issue_owner_flatten_authority_v1` | `evaluate_flatten_go_candidate_v1` / harness | schema defined; persist `OWNER_FLATTEN_GO_PRESENT=false` | flatten execution only | false | cannot authorize network session or wire send |
| network session | `OWNER_NETWORK_SESSION_AUTHORITY_V1` | `network_session_authority_v1.py` | `issue_owner_network_session_authority_v1` | `verify_owner_network_session_authority_v1` / harness | artifact issued=true consumed=false | authorize productive network-session identity; `WIRE_SEND_NOT_AUTHORIZED_BY_THIS_REPAIR=true` | partial | required predecessor; not a send grant |
| session arming | `SESSION_ARMING_STANDING` / harness `session_armed` | `constants_v1.py` / `execution_harness_v1.py` | none named | harness `SESSION_NOT_ARMED` | standing=false; tests may pass parameter true | parameter gate, not Owner schema | false | no `OWNER_SESSION_ARMING` schema |
| network_session_authorized | instance flag | `AuthenticatedGatedProductiveFlattenTransportV1` | class never sets true | `send()` / no-send adapter | false | independent of issued session artifact | false | issued ≠ authorized |
| productive send / wire send | none named in this package | harness deny `PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR` | none | DENY | not implemented | scope boundary | false | `EXISTING_SECTION_11_14_WIRE_SEND_OWNER_SCHEMA=false` |
| HTTP POST | `open_productive_flatten_urllib_post_v1` | §11.13.5 transport | not invoked from §11.14 | urllib | not reached | POST `/api/v5/trade/order` | false as 11.14 grant | inner send class reusable; not a harness transport |
| live/canary submit standing | `LIVE_ENABLED` `LIVE_ARMED` `POST_ALLOWED` `CANARY_AUTHORIZED` | live-order constants | none | constructors abort if true | all false | flip aborts current path | false | not a release key |
| durable consume | `persist_flatten_durable_consume_v1` | `durable_consume_v1.py` | harness after post_count on wrapper path | restart/replay | unconsumed on productive_bind deny | consume ≠ send grant | false | consume after successful send only |
| Full-Core wire-send owner | `I_WIRE_SEND_OWNER=LIVE_EXECUTION_BOUNDARY` | Full-Core composition root | n/a | Full-Core identity | composition-root label | not §11.14 flatten send | false | different ontology |
| no-send bind | `PRODUCTIVE_TRANSPORT_BIND_NO_SEND` | `productive_transport_bind_v1.py` | `prepare_productive_flatten_transport_bind_v1` | harness | constructible | `send_permitted=false` | false as send bind | reuse would change NO_SEND semantics |

Epistemic class of the table: `FORENSIC_RAW` for source symbols and current states; `ADJUDICATED` for `REUSABLE_FOR_11_14_WIRE_SEND`.

## B. New Owner contract

Preferred name does not collide with an existing canonical schema in this package.

```text
schema_version=owner_productive_wire_send_authority.v1
authority_type=OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1
authority_source=CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND_ISSUANCE
action=AUTHORIZE_PRODUCTIVE_WIRE_SEND
purpose=SECTION_11_14_PRODUCTIVE_WIRE_SEND
confirm_token_expected=I_AUTHORIZE_SECTION_11_14_PRODUCTIVE_WIRE_SEND
section=11.14
ISSUED=false
ACCEPTED=false
CONSUMED=false
PRODUCER_IMPLEMENTED=false
single_use=true
retry_allowed=false
second_submit_allowed=false
bound_origin_main_sha=565cee16783ba0a3f1aea606626bf6418bad21e8
bound_instrument_id=SUI-USD_UM_XPERP-310404
bound_exact_envelope_id=76f0ad245070206d7fe8807fca8d130dbdedbdc3969e7ba42f23ca88901c164a
expiry_semantics=NONE_DEFINED_IN_SIBLING_11_14_AUTHORITIES
issued_at=REQUIRED_NONEMPTY_NO_TTL
```

`bound_origin_main_sha` is the frozen envelope bind already used by
`OWNER_FLATTEN_ISSUANCE_V1` and `OWNER_NETWORK_SESSION_AUTHORITY_V1`. It is
**not** a claim that Git `origin/main` equals that SHA. Current Git
`origin/main` at this persist is independently `dd13d0308a24d3be3446e3bea9e7d962b6eaf7b1`.
Class: `CURRENT_CANONICAL` for the envelope bind; `FORENSIC_RAW` for Git HEAD.

### Authority-id / hash semantics

Identity hash fields exclude `issued`, `issued_at`, `consumed`, and
`confirm_token`, matching the sibling network-session contract:

```text
schema_version
authority_type
section
purpose
action
origin_main_sha
exact_envelope_id
instrument_id
single_use
```

Malformed, unknown, or mismatched `authority_id` must fail-closed. Replay of a
consumed artifact must fail-closed. SHA / envelope / instrument mismatch must
fail-closed.

### Required predecessor authorities

```text
OWNER_FLATTEN_ISSUANCE_V1 accepted
OWNER_NETWORK_SESSION_AUTHORITY_V1 issued AND accepted AND consumed=false
```

Not predecessor Owner schemas (none exist or they are standing predicates):

```text
OWNER_SESSION_ARMING = NONE_NAMED
LIVE_ENABLED / LIVE_ARMED / POST_ALLOWED / CANARY_AUTHORIZED = MUST_REMAIN_FALSE
```

Issuing `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1` MUST NOT consume the
predecessor artifacts.

### Explicit non-equivalence

```text
OWNER_NETWORK_SESSION_AUTHORITY_V1
≠ OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1
≠ SESSION_ARMING
≠ NETWORK_SESSION_AUTHORIZED
≠ FLATTEN_EXECUTION_AUTHORITY
≠ SEND_PERMISSION
≠ WIRE_SEND
≠ DURABLE_CONSUME
```

### Forbidden implicit transitions

Issuing `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1` MUST NOT automatically:

- set `network_session_authorized=true`
- arm session
- set `LIVE_ENABLED=true`
- set `LIVE_ARMED=true`
- set `POST_ALLOWED=true`
- set `CANARY_AUTHORIZED=true`
- execute GET
- execute POST
- invoke `inner.send`
- consume this authority
- consume durable flatten state
- mutate position

Mechanism expected-values in this spec are not issued authority. Chat, env, CLI
flags, and standing Live flags are not authority.

## C. Orchestrator / bind spec (not implemented)

```text
SECTION_11_14_PRODUCTIVE_SEND_ORCHESTRATOR_EXISTS=false
NEW_ORCHESTRATOR_REQUIRED=true
PROPOSED_ORCHESTRATOR_SYMBOL=ProductiveWireSendOrchestratorV1
NEW_SEND_CAPABLE_BIND_REQUIRED=true
PROPOSED_SEND_CAPABLE_BIND_SYMBOL=ProductiveTransportBindSendCapableV1
PROPOSED_SEND_CAPABLE_ADAPTER_SYMBOL=ProductiveFlattenSubmitSendAdapterV1
EXISTING_11_13_5_TRANSPORT_REUSABLE=true_as_inner_send_class_only
NO_SEND_ADAPTER_SEMANTICS_CHANGED=false
```

Current interface mismatch (`FORENSIC_RAW`):

```text
harness FlattenSubmitTransportV1.post(*, endpoint, body)
AuthenticatedGatedProductiveFlattenTransportV1.send(LiveCanaryHttpRequestV1)
ConstructiveProductiveFlattenSubmitAdapterV1.post never calls inner.send
inner has no post()
```

`ConstructiveProductiveFlattenSubmitAdapterV1` remains the constructive
NO_SEND adapter. Reuse as a send adapter would change its canonical semantics.
A future send-capable type must be a **new** type.

Future send-capable adapter (spec only) must:

1. Accept harness `post(endpoint, body)`.
2. Reject `/api/v5/trade/close-position`.
3. Allowlist endpoint `/api/v5/trade/order` only.
4. Build `LiveCanaryHttpRequestV1` with `method=POST`, host `eea.okx.com`,
   endpoint `/api/v5/trade/order`, HMAC headers, `body_text` from the flatten
   envelope/body.
5. Attach `FlattenPreSendGateReceiptV1` to the inner transport **before**
   `send`.
6. Invoke `AuthenticatedGatedProductiveFlattenTransportV1.send` only after the
   gate order below has passed, including `network_session_authorized is True`
   on that inner instance.

### Where existing 11.13.5 checks remain

Inside `AuthenticatedGatedProductiveFlattenTransportV1.send` (`FORENSIC_RAW`):

1. typed `FlattenPreSendGateReceiptV1` attached and allowed
2. request matches receipt
3. HMAC header presence (`OK-ACCESS-*`)
4. signing component identity
5. host allowlist `eea.okx.com`
6. endpoint allowlist `/api/v5/trade/order`
7. duplicate-post / lease consumed fail-closed
8. **then** receipt lease is consumed
9. **then** `network_session_authorized` is checked
10. **then** urllib POST

Hazard (`FORENSIC_RAW`): lease consume happens **before** the
`network_session_authorized` check. A future orchestrator MUST fail-closed
**before** calling `inner.send` when `network_session_authorized is not True`.
Whether the inner `send()` order is repaired is `OPEN_OR_CONTRADICTORY` and
is **not** this workpackage.

### Where future §11.14 checks must sit

The current harness `productive_bind` branch, after flatten GO acceptance and
after `verify_owner_network_session_authority_v1` issued=true, currently
appends `PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR` and keeps
`NETWORK_SESSION_AUTHORIZED=false`. That deny is the insertion point for the
future orchestrator. Class: `ADJUDICATED`.

Fail-closed remains in this slice:

- `PRODUCTIVE_TRANSPORT_BIND_NO_SEND`
- constructive adapter forbidden as harness `transport`
- standing Live flags false
- dry-run zeros session/transport
- CLI `session_armed=False` on the flatten execution runner

## D. Required gate order

Proven current execute-path order before the wire-send deny (`FORENSIC_RAW`):

1. flatten authority accepted (`evaluate_flatten_go_candidate_v1`)
2. capture ready; durable not consumed; retry/second-submit forbidden
3. `session_armed is True` else `SESSION_NOT_ARMED`
4. productive bind remains `NO_SEND`
5. `OWNER_NETWORK_SESSION_AUTHORITY_V1` issued/accepted
6. deny `PRODUCTIVE_WIRE_SEND_NOT_IMPLEMENTED_IN_THIS_REPAIR`

Future insertion replacing step 6, only where proven:

| # | Gate | Status |
| --- | --- | --- |
| 1 | flatten authority valid | proven before productive_bind |
| 2 | network-session authority issued/accepted | proven inside productive_bind |
| 3 | productive wire-send authority issued/accepted | **specified here; not implemented** |
| 4 | session arming | proven as `SESSION_NOT_ARMED` before productive_bind; no Owner arming schema |
| 5 | `network_session_authorized` | inner default false; checked inside `send()` after lease consume; outer pre-check required by hazard |
| 6 | live/post/canary standing predicates | must remain false; True aborts constructors |
| 7 | fresh-pre-submit GET | `OPEN_OR_CONTRADICTORY` |
| 8 | envelope/order freshness | frozen envelope asserted; reprice not current blocker; whether send must re-GET/reprice is `OPEN_OR_CONTRADICTORY` |
| 9 | send-capable bind | missing; specified as new type |
| 10 | receipt/HMAC/host/endpoint allowlist | inside 11.13.5 `send`; order vs wire-send authority check `OPEN_OR_CONTRADICTORY` |
| 11 | `inner.send` | not reached |
| 12 | durable consume | `OPEN_OR_CONTRADICTORY` whether HTTP response, ACK capture, or fill is the positive send semantic |

`PRE_SUBMIT_FRESH_GET_REQUIRED=true` is a flatten-issuance **field**. The harness
execute path does not GET. Class: `OPEN_OR_CONTRADICTORY`.

Consume point specified: `AFTER_POSITIVELY_ADJUDICATED_SUCCESSFUL_SEND_SEMANTICS`.
The exact success object (HTTP 200 vs venue ACK vs fill) is
`OPEN_OR_CONTRADICTORY`. Consume before that point is forbidden.

## E. Security / fail-closed invariants

- Authority verification before transport invocation.
- No hidden Boolean promotion (`issued` ≠ `authorized` ≠ `armed` ≠ `send`).
- No authority conflation.
- No automatic arming.
- No POST during issuance.
- No POST during bind construction.
- No POST during validation.
- No consume before positively adjudicated successful send semantics.
- Replay fail-closed.
- Mismatched SHA / envelope / instrument fail-closed.
- Stale / unknown / malformed authority fail-closed.
- Existing `LIVE_*` / `POST_ALLOWED` / `CANARY_AUTHORIZED` false remains the
  safe default; flipping them aborts current constructors.

## Non-execution

This workpackage does not mint `OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1`.
It does not implement `ProductiveWireSendOrchestratorV1`,
`ProductiveTransportBindSendCapableV1`, or
`ProductiveFlattenSubmitSendAdapterV1`.

```text
HARD_STOP=true
NEXT_OWNER_GO_REQUIRED=OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1_MINT_GO
PROPOSED_NEXT_SLICE=SECTION_11_14_OWNER_PRODUCTIVE_WIRE_SEND_AUTHORITY_V1_MINT
NEXT_SLICE_AUTHORIZED=false
```

A later mint GO would still **not** authorize session arming, GET, POST,
`inner.send`, or durable consume.
