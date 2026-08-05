---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1
status: active
scope: Phase 9.2 rate-limit/reconnect wallclock binding; no session activation
capability: PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RATE_LIMIT_RECONNECT_WALLCLOCK_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Productive Public-MD Rate-Limit/Reconnect Wallclock Binding V1

## Problem / Root Cause

Phase 9.2 ladder step `RATE_LIMIT_RECONNECT_SESSION` had runtime components for
pacing, HTTP 429/backoff, reconnect, and staleness on the wallclock path, but no
Cap-style productive binding package analogous to the Step-3 restart wallclock
binding. Offline preflight proofs and incidental smoke/one-hour reconnect
telemetry cannot close Step 4. Improvised harnesses are forbidden.

## Goal

Bind existing canonical surfaces so session
`phase_9_2_public_md_rate_limit_reconnect_session_v1` becomes executable later:

```text
ACTIVE Session-GO (Step-4 identity)
+ Owner-GO
+ Owner-Session-GO
+ single-use authorization
+ confirm-token (file|env|stdin)
+ wallclock runner
+ pacing / 429 / reconnect / stale owners
+ evidence bundle + verifier claims
```

```text
CORE_LOGIC_CHANGE=false
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
NETWORK_SESSION_STARTED=false
FAULT_SESSION_STARTED=false
RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED=false
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
GOVERNED_FAULT_PATH_BOUND=true
NO_PERMANENT_UNSCOPED_ENABLE_FLAG=true
NO_IMPROVISED_HARNESS=true
```

This capability implements binding readiness and offline governed fault-path
proofs (deterministic injected fetcher / state-machine / staleness). It does
**not** authorize or execute a real Public-MD network session or a live fault
session.

## Reuse / Authority Matrix

| Concern | Canonical owner |
| --- | --- |
| Wallclock runner | `run_productive_wallclock_session_v1` |
| Pacing / 429 policy | `public_md_rate_limit_policy_v1` |
| Transport 429 + Retry-After | `eea_public_md_transport_v1` |
| Reconnect state | `session_runtime_v1` / `WallclockSessionState.RECONNECTING` |
| Staleness gate | `heartbeat_staleness_v1.StalenessTrackerV1` |
| Rate-limit metric hygiene | `rate_limit_metric_v1` |
| Bundle verifier | `bundle_verifier_v1` |
| Confirm-token path | paper_shadow confirm_token_v1 / env\|file\|stdin |
| Session-GO (Step-4) | owned by this binding package (`session_go_v1`) |
| Budgets | reuse Phase-9.2 smoke safety values (no new thresholds) |

`PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED=false`

## Fault / session mechanism (binding only)

```text
Deterministic offline injection via EeaPublicMdTransportV1.fetcher
→ RATE_LIMIT_HTTP_429 classified + Retry-After / exponential backoff
→ session HTTP 429 budget abort
→ reconnectable transport classification + RUNNING↔RECONNECTING transitions
→ StalenessTrackerV1 → STALE_DATA killstate
```

No venue-limit probing. No improvisational disconnect. Fault-session execution
remains separately authorized after merge.

## Entrypoint

`scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py`

Commands: `preflight`, `materialize-evidence`, `gate`, `prove-fault-path`
(`--request-real-network` refused outside gate evaluation; never starts a session).

## Activation state

```text
RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED=true
GOVERNED_FAULT_PATH_BOUND=true
REAL_NETWORK_SESSION_NOT_STARTED=true
FAULT_SESSION_STARTED=false
RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED=false
PHASE_9_2_STATUS=PARTIALLY_COMPLETE
```

A later separately authorized governed session with verifier PASS closes the
ladder step. Documentation/merge alone does not.

## Out of scope

- Real Public-MD session execution in this PR
- Live fault-session execution / venue-limit excess
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety / Exit changes
- Dashboard / presentation / Notion / ruleset mutation
- Permanent unscoped enable flag
- New numeric thresholds (reuse existing smoke/wallclock safety budgets)
