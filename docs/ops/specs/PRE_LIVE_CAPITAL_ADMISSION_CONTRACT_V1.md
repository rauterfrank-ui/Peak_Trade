---
docs_token: DOCS_TOKEN_PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_V1
status: active
scope: Pre-live typed Capital Admission seam; Treasury HTTP isolation preserved; no POST; no arming; no Permission-GET
capability: PRE_LIVE_CAPITAL_ADMISSION_CONTRACT_AND_TREASURY_HTTP_ISOLATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-05
---

# Pre-Live Capital Admission Contract V1

## Goal

Insert a typed fail-closed Capital Admission seam before productive
Venue-Capital use by STEP-29P / Sizing. Preserve Treasury HTTP isolation.
Do not arm Live. Do not POST. Do not perform a productive venue GET.

```text
CAPITAL_ADMISSION_IMPLEMENTED=true
CAPITAL_ADMISSION_JOIN_SEAM=join_capital_admission_into_admission_inputs_v1
OBSERVED_CAPITAL != RISK_ADMISSIBLE_CAPITAL
RISK_ADMISSIBLE_GRANTED=false
LIVE_VENUE_CAPITAL_MAY_BIND_STEP_29P=false
CAPITAL_ADMISSION_ALONE_CAN_ADMIT=false
CAPITAL_ADMISSION_CAN_OVERRIDE_OTHER_GATES=false
FRESH_GET_ALONE_NOT_CAPITAL_AUTHORITY=true
LIVE_ACCOUNT_BOUND_ALONE_NOT_CAPITAL_AUTHORITY=true
OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY=true
TREASURY_MUTATION_REACHABLE_FROM_TRADING=false
TREASURY_SEPARATION_GATE_WIRED=false
PL_TF_001_STATUS=CLOSED_TYPED_ADMISSION_SEAM
PL_TF_002_STATUS=FROZEN_PENDING_NETWORK_EVIDENCE
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
```

## Semantic model (Current HEAD)

Current STEP-29P consumes injected `OFFLINE_ALGEBRA` decimals. Canary
`details[].availEq` is an observation domain, not STEP-29P authority.
Account-level `availEq` / `availBal` / `totalEq` / `eq` / `adjEq` /
`cashBal` are not risk-capital authority.

```text
OBSERVED -> typed admission envelope -> RISK_ADMISSIBLE (policy-frozen, never granted)
```

Economic policy (which equity size, haircuts, reserve, depletion, rolling
buffer, scope_capital derivation) remains Owner-frozen. This persist
does not invent those numbers.

## Statuses

```text
TRUSTED_PRESENT = typed observation envelope valid; not risk-admissible
MISSING
MALFORMED
STALE
CONTRADICTORY
WRONG_CONTEXT
NOT_REQUIRED_OFFLINE
```

Missing, malformed, stale, contradictory, wrong account/instrument,
historical, fixture, replay, offline-algebra-as-live, optimistic field
fallback, automatic balance-increase, and stale-higher-after-decrease
fail closed.

## Remaining boundaries

```text
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=LIVE_ENABLED
PL_TF_002=TRADING_KEY_EFFECTIVE_TREASURY_CAPABILITY_NOT_VENUE_PROVEN
VENUE_PERMISSION_UNKNOWN=true
HTTP_TREASURY_MUTATION_REACHABILITY=false
FROZEN_PENDING_OWNER_POLICY=live 29P capital substitution, haircuts, reserve, depletion
FROZEN_PENDING_NETWORK_EVIDENCE=productive venue GET, NE-TF-001 permission GET
```

Treasury Full Feature remains separate. `treasury_separation_gate` remains
an unwired helper because endpoint allowlisting is the HTTP authority.

## Non-claims

```text
This seam does not admit Live
This seam does not mint RISK_ADMISSIBLE capital
Injected/fixture evidence is not Current-Live proof
FULL_CORE_OFFLINE_E2E_PROVEN is not FULL_CORE_SYSTEM_E2E_PROVEN
PDF TARGET_AUTHORITY=NONE
No POST
No productive venue GET
No Permission-GET
```
