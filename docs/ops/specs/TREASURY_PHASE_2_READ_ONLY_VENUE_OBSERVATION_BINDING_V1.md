---
docs_token: DOCS_TOKEN_TREASURY_PHASE_2_READ_ONLY_VENUE_OBSERVATION_BINDING_V1
status: active
scope: E1 binding — deposit/capital-increase read-only funding GET → TreasuryVenueObservationV1
capability: TREASURY_PHASE_2_READ_ONLY_VENUE_OBSERVATION_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Treasury Phase 2 Read-Only Venue Observation Binding V1

## Goal

Close edge **E1** only: productive read-only funding balance GET (reusing
`offline_funding_balance_read_producer_v1`) → typed `TreasuryVenueObservationV1`
for Treasury Phase-2 reconciliation. No sizing mint. No capital admission mint
in this package.

```text
EDGE_SEAM_ID=DEPOSIT_CAPITAL_INCREASE_TO_TREASURY_PHASE_2_VENUE_OBSERVATION_V1
FUNDING_BALANCE_READ_OWNER=ops.offline_funding_balance_read_producer_v1
TREASURY_PHASE_2_OWNER=ops.treasury_phase_2_read_only_reconciliation_v1
OBSERVED_BALANCE_ALONE_CONFIRMS_DEPOSIT=false
NETWORK_EXECUTION_AUTHORIZED=false
TREASURY_MUTATION_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Authority

Treasury remains evidence/reconciliation only. Deposit-history semantics are
supplied via `TreasuryCapitalDepositObservationContextV1` and are **not**
derived from funding balance deltas alone.

## Non-claims

```text
No AVAILABLE_FOR_SIZING mint
No STEP_29P mint
No capital_admission_contract_v1 evaluation in this package
No POST / transfer / withdrawal
Productive urllib wire send remains forbidden (RecordingFakeCanaryTransport in tests)
```
