---
docs_token: DOCS_TOKEN_TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_FOUNDATION_V1
status: active
scope: Treasury Phase-2 read-only reconciliation foundation; typed join to capital_admission_contract_v1; no network; no mutation
capability: TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_FOUNDATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Treasury Phase 2 Read-Only Reconciliation Foundation V1

## Goal

Begin Treasury Phase 2 with the smallest complete read-only reconciliation
foundation: typed venue observation → reconciliation class → existing
`capital_admission_contract_v1` seam. No HTTP. No mutation. No
risk-admissible mint.

```text
TREASURY_PHASE_2_STATUS=READ_ONLY_FOUNDATION_BOUND
TREASURY_PHASE_2_READ_ONLY_RECONCILIATION=true
NETWORK_ALLOWED=false
TREASURY_MUTATION_AUTHORIZED=false
RISK_ADMISSIBLE_MINT_FROM_TREASURY=false
CAPITAL_ADMISSION_AUTHORITY=capital_admission_contract_v1
JOIN_SEAM_ID=TREASURY_PHASE_2_READ_ONLY_RECONCILIATION_TO_CAPITAL_ADMISSION_V1
```

## Reconciliation classes (Phase-2)

Distinct from Phase-1 lifecycle state names:

```text
OBSERVED
RECONCILED
AMBIGUOUS
STALE
UNKNOWN
```

`OBSERVED != RECONCILED != RISK_ADMISSIBLE`

## Non-claims

```text
PRODUCTIVE_DEPOSIT_PATH=false
PRODUCTIVE_WITHDRAWAL_PATH=false
PRODUCTIVE_INTERNAL_TRANSFER_PATH=false
CURRENT_END_TO_END_TREASURY_GATE=false
No POST
No venue GET
No Permission-GET
PDF TARGET_AUTHORITY=NONE
```
