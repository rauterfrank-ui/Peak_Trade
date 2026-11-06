---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_5_FINAL_GENERIC_SESSION_AUTHORIZATION_CONSUME_AND_NETWORK_START_BINDING_V1
status: active
scope: Phase 9.2 Step-5 final generic authorization consume and network-start binding; no real network session
capability: PHASE_9_2_STEP_5_FINAL_GENERIC_SESSION_AUTHORIZATION_CONSUME_AND_NETWORK_START_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-5 Final Generic Authorization Consume And Network Start Binding V1

## Forensic gap (after PR #5763 / #5764)

Step-5 execution and activation wiring proved digests, gates and fetcher wiring,
but kept a hardcoded runtime refuse:

```text
AUTHORIZATION_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY
CONFIRM_TOKEN_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY
LATER_SESSION_CAPABILITY_REQUIRED_FOR_CONSUME_AND_START
```

Identical prolonged natural-market sessions still needed another implementation PR.

## Closed by this capability

1. Final generic consume/start binding integrated into the Step-5 productive path.
2. Canonical authorization issuance owner rebound (no parallel issuer).
3. Canonical Hidden-PTY confirm-token handoff rebound (no argv/env plaintext).
4. Atomic reserve→consume journal for SHA-/config-/contract-/scope-/duration-bound grants.
5. Existing Step-5 governed executor productively reachable after consume.
6. Network-start edge productively bound via existing prolonged Public-MD executor.
7. Evidence materialization + verifier bound.
8. Permanent defaults remain false — no constant flip, no unscoped enable.

## Required future session procedure (no code/PR/constant change)

```text
Owner-GO
→ Operator Authorization
→ NETWORK_SESSION_GO
→ SHA-/Config-/Contract-/Capability-bound single-use authorization
→ canonical Hidden-PTY confirm token
→ atomic consume
→ exactly one Step-5 prolonged Public-MD session
→ evidence + verifier
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false
AUTHORIZATION_ISSUANCE_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CONFIRM_TOKEN_ISSUANCE_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
NETWORK_SESSION_NOT_EXECUTED_BY_THIS_CAPABILITY=true
PUBLIC_MARKET_DATA_GET_ONLY=true
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Entrypoints

- Binding CLI:
  `scripts&#47;ops&#47;run_phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.py`
- Step-5 execution CLI:
  `scripts&#47;ops&#47;run_phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.py`
- Config:
  `config&#47;ops&#47;phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.json`
