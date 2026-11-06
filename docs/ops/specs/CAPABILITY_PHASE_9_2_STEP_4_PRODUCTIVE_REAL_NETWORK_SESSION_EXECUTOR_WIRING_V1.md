---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_WIRING_V1
status: active
scope: Phase 9.2 Step-4 productive session executor wiring; no session activation
capability: PHASE_9_2_STEP_4_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_WIRING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-05
---

# Capability — Phase 9.2 Step-4 Productive Real-Network Session Executor Wiring V1

## Goal

Bind Gate → Authorization → Confirm-token path → canonical
`run_productive_wallclock_session_v1` → existing rate-limit/reconnect/staleness
owners → Step-4 evidence schema, so a later separately authorized governed
real Public-MD session can execute.

```text
READY_FOR_PRODUCTIVE_SESSION_EXECUTION=true
PRODUCTIVE_SESSION_REACHABLE=true
NETWORK_SESSION_STARTED=false
FAULT_SESSION_STARTED=false
RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED=false
RECONNECT_PATH_PRODUCTIVELY_OBSERVED=false
RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED=false
```

This capability does **not** start a real Public-MD or fault session.

## Entrypoint

`scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py`

New command: `execute-productive-session --execute` (requires Session-GO + Owner flags).
`--request-real-network` remains fail-closed in this wiring capability.

## Package owner

`src/ops/phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1/productive_executor_v1.py`

## Out of scope

- Real network / fault session execution
- Live / Testnet / Paper orders / credentials / capital
- Core trading logic / thresholds / dashboard / presentation / Notion / rulesets
