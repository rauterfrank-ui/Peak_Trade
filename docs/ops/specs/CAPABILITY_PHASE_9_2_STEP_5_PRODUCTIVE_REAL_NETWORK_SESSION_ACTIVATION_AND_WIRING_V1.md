---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_5_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_AND_WIRING_V1
status: active
scope: Phase 9.2 Step-5 productive real-network session activation and wiring; no real network session
capability: PHASE_9_2_STEP_5_PRODUCTIVE_REAL_NETWORK_SESSION_ACTIVATION_AND_WIRING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-06
---

# Capability — Phase 9.2 Step-5 Productive Real-Network Session Activation And Wiring V1

## Forensic gap (after PR #5763)

The Step-5 execution capability provided the governed entrypoint, contract
digests, and offline fail-closed gates, but stopped before productive
activation:

```text
NETWORK_SESSION_ALLOWED=false
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY
SEPARATE_OWNER_GO_REQUIRED_FOR_STEP5_SESSION
REAL_NETWORK_FETCHER_NOT_WIRED_IN_THIS_CAPABILITY
```

Authorization and confirm-token issuance/consumption remained unreachable
for a later bounded Public-MD session.

## Closed by this capability

1. Canonical Public-MD fetcher (`make_real_eea_public_md_fetcher_v1`) wired
   into the Step-5 prolonged executor path.
2. Ephemeral `NETWORK_SESSION_GO` binding (parameter-only; default false;
   not from env/config/persistence).
3. Step-4-pattern SHA / config / capability / session / token scope gate
   reused via Step-5 authorization and hidden-PTY adapters.
4. Fail-closed before fetcher when any required binding is missing.
5. Offline failure-injection + simulated full-gate fetcher-once proof.
6. Evidence + verifier. No network session start. No auth/token issuance
   or consumption in this capability.

## Required future session procedure (no further wiring PR)

```text
Owner-GO
→ Operator Authorization
→ NETWORK_SESSION_GO
→ SHA-/Config-/Capability-bound single-use authorization
→ canonical Hidden-PTY confirm token
→ atomic consume (later session capability)
→ exactly one Step-5 prolonged Public-MD session
→ evidence + verifier
```

## Boundaries

```text
NETWORK_SESSION_ALLOWED=false
NETWORK_SESSION_GO_DEFAULT=false
NETWORK_SESSION_GO_PERSISTED=false
AUTHORIZATION_ISSUANCE_ALLOWED=false
AUTHORIZATION_CONSUMPTION_ALLOWED=false
CONFIRM_TOKEN_ISSUANCE_ALLOWED=false
CONFIRM_TOKEN_CONSUMPTION_ALLOWED=false
NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY=false
PUBLIC_MARKET_DATA_GET_ONLY=true
CORE_LOGIC_CHANGE=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

## Entrypoints

- Activation CLI:
  `scripts&#47;ops&#47;run_phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.py`
- Step-5 execution CLI (unchanged role; now activation-aware):
  `scripts&#47;ops&#47;run_phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.py`
- Config:
  `config&#47;ops&#47;phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.json`
