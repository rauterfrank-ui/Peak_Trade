---
docs_token: DOCS_TOKEN_TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1
status: active
scope: E4 binding — TreasuryCapitalAdmissionJoinV1 → account-equity orchestration ingress
capability: TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Treasury Capital Admission to Account Equity Orchestration V1

## Goal

Close edge **E4** only: typed handoff from `TreasuryCapitalAdmissionJoinV1`
(capital_admission_contract_v1 output within Treasury Phase-2) into
`AccountEquityOrchestrationIngressV1` for
`governed_productive_account_equity_authority_producer_v1`. No STEP-29P mint.
No AVAILABLE_FOR_SIZING mint. No venue GET in this package.

```text
EDGE_SEAM_ID=TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_V1
CAPITAL_ADMISSION_AUTHORITY=capital_admission_contract_v1
ACCOUNT_EQUITY_AUTHORITY=ops.governed_productive_account_equity_authority_producer_v1
NETWORK_ALLOWED=false
STEP_29P_MINT_AUTHORIZED=false
AVAILABLE_FOR_SIZING_MINT_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Authority

Capital Admission remains the capital envelope owner. Account-equity authority
remains the equity orchestration owner. This package only forwards typed ingress;
it does not re-evaluate admission, mint risk-admissible capital, or execute
29P GET/sizing.

Reconciled capital **increase** with `CAPITAL_INCREASE_NOT_AUTO_ADMITTED` is
admitted to orchestration ingress only (deferral), not to sizing.

## Non-claims

```text
No STEP_29P evaluation
No portfolio reservation
No Master-V2 / Double-Play touch
No Treasury mutation
No parallel account-equity authority
```
