---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1
status: active
scope: Phase 9.2 real Public-MD restart/recovery wallclock binding; no session activation
capability: PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_REAL_NETWORK_WALLCLOCK_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Productive Public-MD Restart/Recovery Real-Network Wallclock Binding V1

## Problem / Root Cause

PRs #5665–#5668 closed the offline restart contract, productive entrypoint,
Session-GO gate and post-unlock invocation, but the productive path still
hard-blocked real Public-MD (`REAL_NETWORK_REQUESTED_BUT_IMPLEMENTATION_DEFAULT_FORBIDS`
/ fake-MD-only orchestration). The Phase-9.2 ladder next step
`RESTART_RECOVERY_SESSION` therefore could not be executed as a real
Public-MD wallclock PRE→exit82→POST campaign without inventing a parallel
runner.

## Goal

Bind the existing canonical surfaces so that session
`phase_9_2_public_md_restart_recovery_session_v1` becomes executable later:

```text
ACTIVE Session-GO
+ Owner-GO
+ Owner-Session-GO
+ per-segment single-use authorization
+ confirm-token (file|env|stdin)
+ wallclock runner
+ restart/recovery contract/harness/verifier
```

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
RESTART_RECOVERY_LADDER_STEP_CLOSED=false
READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION=true
NO_PERMANENT_UNSCOPED_ENABLE_FLAG=true
```

This capability implements binding readiness and offline negative proofs. It
does **not** authorize or execute a real Public-MD network session.

## Reuse / Authority Matrix

| Concern | Canonical owner |
| --- | --- |
| PRE segment harness | PR #5665 `run_pre_restart_segment_v1` |
| POST segment harness | PR #5665 `run_post_restart_segment_v1` |
| Bundle verifier | PR #5665 `verify_restart_bundle_v1` |
| Segment authorization envelopes | PR #5666 `segment_authorization_v1` |
| Productive entrypoint identity | PR #5666 `PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1` |
| Session-GO gate | PR #5667 `evaluate_session_go_gate_v1` |
| Post-unlock pattern | PR #5668 (gate→consume→lock→runner) |
| Wallclock runner | `run_productive_wallclock_session_v1` |
| Confirm-token path | paper_shadow confirm_token_v1 / env|file|stdin |
| Cap 6.4 / checkpoint / recon | existing restart state_root_adapter + harness |

`PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED=false`

## Segment model

```text
PRE_RESTART (own process + single-use auth + lock)
→ controlled completion exit 82 = CONTROLLED_SEGMENT_TRANSITION
→ POST_RESTART (new process + new single-use auth + lock)
→ reconciliation before alpha
→ bundle verify
```

Same-process POST is rejected. Auth reuse and identical PRE/POST auth fail closed.
Fake-MD observations cannot satisfy real session claims.

## Entrypoint

`scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.py`

Commands: `preflight`, `materialize-evidence`, `gate`, `execute-segment`
(`--request-real-network` refused by this CLI).

## Activation state

```text
REAL_PUBLIC_MD_RESTART_BINDING_IMPLEMENTED=true
REAL_NETWORK_SESSION_NOT_STARTED=true
RESTART_RECOVERY_LADDER_STEP_CLOSED=false
PHASE_9_2_STATUS=PARTIALLY_COMPLETE
```

A later separately authorized governed session with verifier PASS closes the
ladder step. Documentation/merge alone does not.

## Out of scope

- Real Public-MD session execution in this PR
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety / Exit changes
- Notion or ruleset mutation
- Permanent unscoped enable flag
