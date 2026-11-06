---
docs_token: DOCS_TOKEN_TREASURY_PHASE_2_READ_ONLY_EXTERNAL_CAPITAL_DECREASE_OBSERVATION_BINDING_V1
status: active
scope: S1 — external capital decrease read-only funding GET → TreasuryVenueObservationV1
capability: TREASURY_PHASE_2_READ_ONLY_EXTERNAL_CAPITAL_DECREASE_OBSERVATION_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Treasury Phase 2 Read-Only External Capital Decrease Observation Binding V1

## Goal

Close **S1** only: productive read-only funding balance GET (reusing
`offline_funding_balance_read_producer_v1`) → typed `TreasuryVenueObservationV1`
with conservative `TreasuryExternalDepletionSignalV1` mapping for external
capital decrease. No sizing mint. No capital admission evaluation in this package.

```text
EDGE_SEAM_ID=EXTERNAL_CAPITAL_DECREASE_TO_TREASURY_PHASE_2_VENUE_OBSERVATION_V1
FUNDING_BALANCE_READ_OWNER=ops.offline_funding_balance_read_producer_v1
TREASURY_PHASE_2_OWNER=ops.treasury_phase_2_read_only_reconciliation_v1
OBSERVED_BALANCE_ALONE_CONFIRMS_DEPLETION=false
OBSERVED_BALANCE_ALONE_CONFIRMS_EXTERNAL_WITHDRAWAL=false
NETWORK_EXECUTION_AUTHORIZED=false
TREASURY_MUTATION_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
PRODUCTIVE_WITHDRAWAL_PATH=false
NO_WITHDRAW_POST=true
```

## Authority

Treasury remains evidence/reconciliation only. Withdrawal-history semantics are
supplied via `TreasuryExternalCapitalDecreaseObservationContextV1` and are **not**
derived from funding balance deltas alone. Account bills / ledger GET surfaces
remain noncanonical for this binding (no bills normalization).

## Non-claims

```text
No AVAILABLE_FOR_SIZING mint
No STEP_29P mint
No capital_admission_contract_v1 evaluation in this package
No POST / transfer / withdrawal send
No deposit-history semantic reuse for withdrawal claims
Productive urllib wire send remains forbidden (RecordingFakeCanaryTransport in tests)
```
