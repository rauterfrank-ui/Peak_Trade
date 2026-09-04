---
docs_token: DOCS_TOKEN_SEND_TIME_POSITION_REOBSERVATION_V1
status: active
scope: Offline SEND_TIME_POSITION_REOBSERVATION contract; no GET; no POST
capability: SEND_TIME_POSITION_REOBSERVATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-04
---

# SEND_TIME_POSITION_REOBSERVATION Offline Contract V1

## Goal

Close the named residual `SEND_TIME_POSITION_REOBSERVATION` as an offline
CASE_B contract. Bind the canonical target-instrument position reobservation
to the flatten pre-send permit decision. Reuse
`classify_target_position_state_v1` and the ratified 5000 ms local-monotonic
freshness contract. Deny empty `data[]` as zero. Deny historical P08 slices.
Deny fake producers counted as a runtime GET. Do not GET. Do not POST. Do not
flatten. Do not unlock Live or Canary. Do not issue a runtime permit. Do not
authorize a network session. Do not claim `PROVEN_AT_SEND`.

```text
CORE_LOGIC_CHANGE=false
ACTIVATION_STATE=not_activated
POST_PERFORMED=false
GET_PERFORMED_THIS_PERSIST=false
PRIVATE_AUTH_USED=false
RUNTIME_GET_REQUIRED=false
RUNTIME_GET_PERFORMED=false
POSITION_GET_REQUIRED_THIS_PERSIST=false
POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO=false
ORDER_PERFORMED=false
LIVE_AUTHORIZED=false
CANARY_AUTHORIZED=false
SUBMIT_UNLOCKED=false
APT_CLOSED=true
CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT
SEND_TIME_POSITION_REOBSERVATION=PASS_OFFLINE_CONTRACT
SEND_TIME_POSITION_REOBSERVATION_OFFLINE_CONTRACT=PASS_OFFLINE_CONTRACT
SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN=false
PREREQUISITE_18_PROVEN_AT_SEND=false
PREREQUISITE_19_PROVEN_AT_SEND=false
PREREQUISITE_21_PROVEN_AT_SEND=false
PREREQUISITE_24_PROVEN_AT_SEND=false
STPR_FLATTEN_EXECUTE_AUTHORIZED=false
STPR_NETWORK_SESSION_AUTHORIZED=false
STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT=true
STPR_DOES_NOT_SET_LIVE_AUTHORIZED=true
LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_SEND_TIME_POSITION_REOBSERVATION
EARLIEST_UNRESOLVED_DEPENDENCY=BOUNDED_RUNTIME_PERMIT_ISSUANCE
STPR_DOES_NOT_GRANT_EXECUTION_READINESS=true
EXECUTION_READY=false
BOUNDED_RUNTIME_PERMIT_ISSUANCE=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE=true
FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE=true
```

## Canonical semantics

`SEND_TIME_POSITION_REOBSERVATION` is the named residual after
`AUTHENTICATED_PRODUCTIVE_TRANSPORT`. The evaluation point is
`IMMEDIATELY_BEFORE_FLATTEN_SEND_PERMIT_DECISION` from the ratified
position-observation freshness contract. That is the pre-send permit
decision, not urllib wire send, not HMAC timestamp, and not venue `uTime`.

The observation object is the canonical target-instrument position row
classified by `classify_target_position_state_v1` on
`SUI-USD_UM_XPERP-310404`. Empty `data[]` is not zero. An absent target row
is not zero. An explicit zero row is a distinct deny. A later send still
needs a fresh observation inside the 5000 ms local-monotonic window; this
persist does not perform that GET.

The intended endpoint for a later authorized read is
`GET &#47;api&#47;v5&#47;account&#47;positions`. This persist names that endpoint and does
not invoke it. `NETWORK_SESSION` remains a separate remaining higher
authority. A GET now cannot prove send-time freshness because flatten
execute is unauthorized and the max age is 5000 ms.

The name is not self-authorizing runtime or execution authority. Historical
P08 CASE_A nonzero proof is not current send-time proof. Offline PASS does
not lift `PREREQUISITE_18&#47;19&#47;21&#47;24` to `PROVEN_AT_SEND=true`.

## Proof vs later runtime value

This persist proves the reobservation **evaluation gates** exist and deny on
missing/unproven APT, unbound remaining set, instrument mismatch, missing
observation, empty data treated as zero, target not observed, explicit zero,
malformed payload, stale freshness, historical slice reuse, authenticated GET
producer, fake producer counted as GET, runtime-observation claims,
`PROVEN_AT_SEND` claims, live-authorized substitution, runtime-permit /
flatten / network / GET / POST claims, this implementation GO used as
flatten-execute, remaining-set mismatch, and predecessor lineage mismatch.

A later send still needs bounded runtime permit issuance, flatten-execute
Owner-GO, network-session authorization, and an authorized private GET
inside the freshness window. This persist does not issue that permit and
does not authorize flatten execute.

## Out of scope

- Private GET / POST / flatten / position mutation
- Live / Testnet / Canary execute
- `LIVE_AUTHORIZED=true` / `LIVE_ENABLED` / `LIVE_ARMED` activation
- Network session authorization
- Runtime permit issuance
- Claiming `SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN=true`
- Claiming `PROVEN_AT_SEND=true` for prerequisites 18, 19, 21, or 24
- Merge
- Master V2 / Double Play Core mutation
