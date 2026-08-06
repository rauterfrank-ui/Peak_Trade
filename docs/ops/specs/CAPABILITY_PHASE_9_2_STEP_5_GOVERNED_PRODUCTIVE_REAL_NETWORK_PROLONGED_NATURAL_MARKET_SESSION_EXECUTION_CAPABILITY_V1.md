---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1
status: active
scope: Phase 9.2 Step-5 governed productive prolonged natural-market session execution; no real network session
capability: PHASE_9_2_STEP_5_GOVERNED_PRODUCTIVE_REAL_NETWORK_PROLONGED_NATURAL_MARKET_SESSION_EXECUTION_CAPABILITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-5 Governed Productive Prolonged Natural-Market Session Execution V1

## Problem

The merged Step-5 binding stand provides the prolonged natural-market session
contract, binding config digests, GET-only proofs, and Binding-CLI commands, but
has no separate governed productive execution entrypoint.

## Current runtime truth

```text
STEP5_BINDING_PRESENT=true
STEP5_EXECUTION_ENTRYPOINT_BEFORE=false
NETWORK_SESSION_STARTED=false
PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED=false
```

## Target state

Separate package / config / CLI / tests / evidence that implements:

```text
Governed Step-5 Session Request
→ exact repository SHA validation
→ exact session-contract digest validation
→ exact binding-config digest validation
→ authorization artifact validation
→ hidden confirm-token handoff
→ authorization/token scope validation
→ single-use consumption boundary
→ execution permit validation
→ bounded prolonged Public-MD executor
→ pacing / retry / backoff / reconnect control
→ heartbeat / staleness / interrupt / recovery handling
→ bounded disk/evidence writer
→ terminal classification
→ manifest assembly
→ verifier
```

## Call graph before / after

Before:

```text
Binding CLI only
→ assemble-session-request / gate / claim / disk proofs
→ NO productive execution entrypoint
```

After:

```text
Execution CLI (separate)
→ preflight / assemble-execution-request
→ request-real-network (offline fail-closed)
→ execute-governed-session (offline fail-closed)
→ verify-session / materialize-terminal-evidence
→ productive prolonged Public-MD executor (contract-driven)
```

Binding CLI path remains unchanged and binding-only.

## Authorization / token binding

Bindings required:

* capability / scope
* repository SHA
* session-contract digest
* binding-config digest
* planned duration (7200)
* network mode PUBLIC_MD_GET_ONLY
* public-MD allowlist + GET-only
* evidence root
* expiry
* single-use state

Confirm token: canonical issuance path only; hidden PTY/stdin handoff; never
argv / env fallback / shell history / logs / evidence plaintext.

This capability does **not** issue or consume authorization or confirm tokens.

## Session contract

Consumes:

* `config/ops/phase_9_2_public_md_prolonged_natural_market_session_contract_v1.json`
* `config/ops/phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.json`

```text
PLANNED_SESSION_DURATION_SECONDS=7200
MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS=7200
```

No silent defaults. Missing required fields →
`HARD_STOP_REASON=STEP5_EXECUTION_CONTRACT_INCOMPLETE_<FIELD>`.

## Pacing / retry / backoff / reconnect

All budgets are read from the canonical Step-5 session contract (smoke/Step-4
numeric reuse already bound there). Executor enforces positive intervals and
bounded retry/backoff/reconnect/heartbeat/staleness.

## Evidence and verifier

Terminal evidence under
`docs/evidence/capability_phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1`
with manifest digest verification and claims-vs-telemetry checks.

## Failure semantics

Explicit terminal classes: PASS, HARD_STOP, INTERRUPTED, STALE_DATA_STOP,
RATE_LIMIT_EXHAUSTED, RECONNECT_EXHAUSTED, NETWORK_FAILURE, CONTRACT_MISMATCH,
AUTHORIZATION_FAILURE, CONFIRM_TOKEN_FAILURE, EVIDENCE_FAILURE,
DISK_BOUND_FAILURE.

## Safety invariants

```text
PUBLIC_MD_GET_ONLY=true
PRIVATE_ENDPOINT_REACHABLE=false
AUTH_HEADER_REACHABLE=false
EXCHANGE_CREDENTIAL_PATH_REACHABLE=false
ORDER_SUBMIT_PATH_REACHABLE=false
REAL_EXECUTION_ADAPTER_CONSTRUCTED=false
ORDER_SIDE_EFFECT_OCCURRED=false
NETWORK_SESSION_ALLOWED=false
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Tests

Focused offline tests cover CLI surfaces, digest/scope/expiry/reuse failures,
token argv/env rejection, GET-only boundary, pacing/retry/429/reconnect/
heartbeat/staleness/interrupt, session lock, duplicates, disk bounds, manifest
digest, claims-vs-telemetry, idempotent evidence, and blocked network.

## Core-logic classification

```text
CORE_LOGIC_CHANGE=false
TRADING_LOGIC_CHANGED=false
MASTER_V2_CHANGED=false
DOUBLE_PLAY_CHANGED=false
RISK_CHANGED=false
SAFETY_CHANGED=false
```

## Activation state

```text
NETWORK_SESSION_STARTED=false
AUTHORIZATION_ISSUED=false
AUTHORIZATION_CONSUMED=false
CONFIRM_TOKEN_ISSUED=false
CONFIRM_TOKEN_CONSUMED=false
SESSION_LADDER_STEP_CLOSED=false
CAPABILITY_CLOSED=false
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
```

## Rollback

Revert the Step-5 execution package, config, CLI, tests, and docs/evidence.
Binding surfaces remain intact.

## Out of scope

* REAL_NETWORK_SESSION_START
* AUTHORIZATION_ISSUANCE / CONSUMPTION
* CONFIRM_TOKEN_ISSUANCE / CONSUMPTION
* STEP5_SESSION_EXECUTION under Owner network GO
* MERGE / RULESET_MUTATION / Notion / Dashboard / Core trading logic
