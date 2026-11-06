---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_SESSION_START_INVOKE_EDGE_IMPLEMENTATION_V1
status: active
scope: Phase 9.2 Step-6 productive Real-Network session start-invoke edge; no session activation
capability: PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_SESSION_START_INVOKE_EDGE_IMPLEMENTATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-07
---

# Capability — Phase 9.2 Step-6 Productive Real-Network Session Start Invoke Edge Implementation V1

## Problem / Root Cause

Forensic gap analysis confirmed that after PR #5780 the session-owner
package owns may-start gates, Hidden-PTY, stale control, evidence and
verifier wiring, but the productive start-invoke edge was absent:

```text
NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY=true
PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_PRESENT=false
```

AST proved zero Step-6 callsites to `run_productive_wallclock_session_v1`.

## Goal

```text
execute_governed_step6_session_v1 present under TARGET_SESSION_CAPABILITY_ID
+ exactly-one run_productive_wallclock_session_v1 callsite
+ governed_stale_data_control overrides reach wallclock kwargs
+ canonical Public-MD fetcher bound
+ Binding/Path/offline fail-closed paths unchanged and non-starting
+ NETWORK_SESSION_STARTED=false in this capability
+ PHASE_9_2_STEP_6_STATUS=OPEN
+ READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION=true
```

## Productive call graph

```text
explicit session Owner
→ capability / SHA / authorization validation
→ Owner-GO
→ NETWORK_SESSION_GO
→ Real-TTY
→ canonical Hidden Confirm acquisition/consume
→ session_execution_may_start
→ exactly-one productive wallclock invocation
→ governed stale-data control
→ Public-MD-only fetcher
→ evidence ownership/seal path
→ productive verifier
```

## Out of scope

- Real Step-6 Public-MD session execution in this PR
- Desktop runbook sync
- Weakening Binding-only or Path-implementation forbid constants
- Live / Testnet / Paper exchange orders / credentials / capital
- Master V2 / Double Play / Bull-Bear / Dynamic Scope / Risk / Safety
- Step-6 ladder closeout / Step-7 start
