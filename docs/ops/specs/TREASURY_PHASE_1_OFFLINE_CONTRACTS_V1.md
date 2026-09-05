---
docs_token: DOCS_TOKEN_TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1
status: active
scope: Treasury Phase-1 offline domain contracts; durable intent; lifecycle; idempotency; provenance; capital-state boundary; no network; no mutation
capability: TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-05
---

# Treasury Phase 1 Offline Contracts V1

## Goal

Provide the typed Treasury domain-contract slice after the Phase-0 census
and closed PL-TF-001 Capital Admission seam. Do not move funds. Do not send
network requests. Do not arm Live.

```text
TREASURY_PHASE_1_STATUS=CLOSED_OFFLINE_CONTRACTS
TREASURY_PHASE_2_STATUS=NOT_STARTED
DURABLE_INTENT_BEFORE_REMOTE_MUTATION=true
VENUE_IDEMPOTENCY_GUARANTEE=NOT_PROVEN
OUTCOME_UNKNOWN_IS_FAILURE=false
OUTCOME_UNKNOWN_SAFE_TO_RETRY=false
OBSERVED_CAPITAL != RISK_ADMISSIBLE_CAPITAL
RECONCILED_CAPITAL != RISK_ADMISSIBLE_CAPITAL
CAPITAL_ADMISSION_AUTHORITY=capital_admission_contract_v1
SECOND_CAPITAL_AUTHORITY_ADDED=false
TREASURY_MUTATION_REACHABLE_FROM_TRADING=false
TREASURY_SEPARATION_GATE_WIRED=false
PL_TF_002_STATUS=FROZEN_PENDING_NETWORK_EVIDENCE
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
```

## Domain boundary

Treasury mutation authority is not trading execution authority.
Treasury observer is not Treasury mutator. `LIVE_ENABLED`, `LIVE_ARMED`,
`WIRE_SEND_PERMITTED`, trading owner permits, strategy decisions, Double
Play state, planner results, learner output, scheduler ticks, and generic
execution tokens cannot authorize Treasury mutation.

Typed `MUTATION_PERMIT_TYPED_OFFLINE` exists only as an offline contract
class. It cannot mint wire, Live, or funds-movement authority in Phase 1.

## Operation kinds

- `DEPOSIT_OBSERVATION` — passive observation; not mutation; not address retrieval
- `DEPOSIT_ADDRESS_RETRIEVAL` — distinct non-mutation capability class; still cannot generate a live address in Phase 1
- `WITHDRAWAL` — mutation-class; amount must be finite and positive
- `INTERNAL_TRANSFER` — mutation-class even without a chain transaction

## Lifecycle

```text
INTENT_RECORDED
REMOTE_ATTEMPT_RECORDED
REMOTE_PENDING
REMOTE_TERMINAL_SUCCESS
REMOTE_TERMINAL_FAILURE
OUTCOME_UNKNOWN
RECONCILIATION_REQUIRED
ECONOMIC_EFFECT_RECONCILED
```

`OUTCOME_UNKNOWN` is not `FAILED` and is not `SAFE_TO_RETRY`.
Terminal venue success is not `TREASURY_RECONCILED` and not
`RISK_ADMISSIBLE`. Reconciled Treasury effect is not Capital Admission.

## Capital boundary

Reuses `capital_admission_contract_v1`. Does not invent equity, haircut,
reserve, or scope_capital formulas. Observed increase is not automatic
risk-admissible increase.

## Non-claims

```text
PRODUCTIVE_DEPOSIT_PATH=false
PRODUCTIVE_WITHDRAWAL_PATH=false
PRODUCTIVE_INTERNAL_TRANSFER_PATH=false
TRANSFER_RECONCILIATION=false
CURRENT_END_TO_END_TREASURY_GATE=false
TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN=false
PDF TARGET_AUTHORITY=NONE
No POST
No productive venue GET
No Permission-GET
```
