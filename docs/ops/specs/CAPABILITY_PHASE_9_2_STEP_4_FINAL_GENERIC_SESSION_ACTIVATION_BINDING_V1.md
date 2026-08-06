---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_FINAL_GENERIC_SESSION_ACTIVATION_BINDING_V1
status: active
scope: Phase 9.2 Step-4 final generic session activation binding; no real network session
capability: PHASE_9_2_STEP_4_FINAL_GENERIC_SESSION_ACTIVATION_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-4 Final Generic Session Activation Binding V1

## Forensic gap (after PR #5759)

The implementation capability proved the productive call graph structurally, but
kept a hardcoded runtime refuse:

```text
RUNTIME_SESSION_REQUIRES_SEPARATE_OWNER_GO_AFTER_IMPLEMENTATION_MERGE
SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED=false (permanent)
CLI GOVERNED_EXECUTION_BINDING_ONLY_REQUIRED for network-allowed issuance path
```

Identical Step-4 sessions still needed another implementation PR.

## Closed by this capability

1. Final generic activation binding integrated into the PR-5759 runtime entry.
2. Ephemeral SHA-/config-/capability-/session-bound single-use grant.
3. Atomic reserve→consume journal (crash burns authorization; replay rejected).
4. Owner-GO + Operator Authorization + NETWORK_SESSION_GO required each session.
5. Canonical Hidden-PTY / confirm-token digest validation reused.
6. Productive runner invoke bound (mocked/dry in this capability; real network
   only under a later separately authorized NETWORK_SESSION_GO session).
7. Evidence materialization + verifier bound.
8. Permanent defaults remain false — no constant flip, no unscoped enable.

## Required future session procedure (no code/PR/constant change)

```text
Owner-GO
→ Operator Authorization
→ NETWORK_SESSION_GO
→ SHA-/Config-/Capability-bound single-use authorization
→ canonical Hidden-PTY confirm token
→ exactly one Step-4 session
→ atomic consume
→ evidence + verifier
```

## Boundaries

```text
DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED=false
PERMANENT_UNSCOPED_ENABLE=false
NETWORK_SESSION_NOT_EXECUTED_BY_THIS_CAPABILITY=true
NO_AUTHORIZATION_FOR_REAL_SESSION_ISSUED=true
PUBLIC_MARKET_DATA_GET_ONLY=true
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```
