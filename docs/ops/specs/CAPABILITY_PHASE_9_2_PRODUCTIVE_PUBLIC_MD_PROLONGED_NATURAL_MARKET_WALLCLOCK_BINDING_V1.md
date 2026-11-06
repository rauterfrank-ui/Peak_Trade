---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1
status: active
scope: Phase 9.2 prolonged natural-market wallclock binding; no session activation
capability: PHASE_9_2_PRODUCTIVE_PUBLIC_MD_PROLONGED_NATURAL_MARKET_WALLCLOCK_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Productive Public-MD Prolonged Natural-Market Wallclock Binding V1

## Problem / Root Cause

Phase 9.2 ladder step `PROLONGED_NATURAL_MARKET_SESSION` had Step-3/Step-4
wallclock binding surfaces and smoke/Step-4 safety budgets, but no Cap-style
productive Step-5 binding package with explicit prolonged duration, disk,
evidence-growth, and claim-separation contracts. Improvised harnesses and
outcome overclaims from mere reachability are forbidden.

## Goal

Bind existing canonical surfaces so session
`phase_9_2_public_md_prolonged_natural_market_session_v1` becomes executable later:

```text
ACTIVE Session-GO (Step-5 identity)
+ Owner-GO
+ Owner-Session-GO
+ fresh single-use Step-5 authorization
+ confirm-token (file|env|hidden-PTY)
+ wallclock runner
+ pacing / retry / backoff / heartbeat / stale owners
+ disk preflight + evidence growth bounds
+ evidence bundle + verifier claims
```

```text
CORE_LOGIC_CHANGE=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
NETWORK_SESSION_STARTED=false
PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED=false
CAPABILITY_CLOSED=false
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
NO_PERMANENT_UNSCOPED_ENABLE_FLAG=true
NO_IMPROVISED_HARNESS=true
RECONNECT_PATH_STATUS=NOT_NATURALLY_OCCURRED_CLASSIFIED ≠ RECONNECT_OBSERVED=true
```

This capability implements binding readiness and offline claim/duration/disk
proofs. It does **not** authorize or execute a real Public-MD network session,
and does not issue or consume authorization or confirm tokens.

## Duration / bounds

```text
MIN_WALLCLOCK_DURATION_SECONDS=7200
DEFAULT_WALLCLOCK_DURATION_SECONDS=7200
MAX_WALLCLOCK_DURATION_SECONDS=21600
DURATION_AUTHORITY=MONOTONIC_CLOCK
```

Pacing/retry/backoff/heartbeat/stale numerics reuse smoke/Step-4 values (no drift).

## Reuse / Authority Matrix

| Concern | Canonical owner |
| --- | --- |
| Wallclock runner | `run_productive_wallclock_session_v1` |
| Pacing / 429 policy | `public_md_rate_limit_policy_v1` |
| Transport | `eea_public_md_transport_v1` |
| Session runtime | `session_runtime_v1` |
| Staleness gate | `heartbeat_staleness_v1.StalenessTrackerV1` |
| Bundle verifier | `bundle_verifier_v1` |
| Confirm-token path | paper_shadow `confirm_token_v1` + Step-5 Hidden-PTY binder |
| Session-GO (Step-5) | owned by this binding package (`session_go_v1`) |
| Step-3 / Step-4 patterns | restart + rate-limit reconnect binding packages |

`PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED=false`

## Entrypoint

`scripts&#47;ops&#47;run_phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.py`

Commands: `preflight`, `materialize-evidence`, `gate`, `prove-claim-semantics`,
`prove-disk-bounds`, `assemble-session-request`
(`--request-real-network` refused outside gate evaluation; never starts a session).

## Activation state

```text
PROLONGED_NATURAL_MARKET_BINDING_IMPLEMENTED=true
REAL_NETWORK_SESSION_NOT_STARTED=true
PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED=false
CAPABILITY_CLOSED=false
PHASE_9_2_STATUS=PARTIALLY_COMPLETE
```

A later separately authorized governed session with verifier PASS closes the
ladder step. Documentation/merge alone does not.

## Out of scope

- Real Public-MD session execution in this PR
- Authorization / confirm-token issuance or consumption
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
- Adverse/stale ladder step (Step 6) and multi-session campaign (Step 7)
- Permanent unscoped enable flag
- New pacing/retry/backoff/heartbeat/stale numeric thresholds
