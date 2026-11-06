---
docs_token: DOCS_TOKEN_TREASURY_EXTERNAL_CAPITAL_DECREASE_S2_ADMISSION_RUNTIME_JOIN_V1
status: active
scope: S2 — external capital decrease observation → productive capital admission runtime join
capability: TREASURY_EXTERNAL_CAPITAL_DECREASE_S2_ADMISSION_RUNTIME_JOIN_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Treasury External Capital Decrease S2 Admission Runtime Join V1

## Goal

Close **S2** only: join S1 `TreasuryVenueObservationV1` (external capital
decrease binding) into the current productive capital admission runtime seam
(`join_capital_admission_into_admission_inputs_v1` / `capital_admission_contract_v1`).
Conservative decrease must not mint risk-admissible capital or restore stale
higher capital optimistically.

```text
JOIN_SEAM_ID=TREASURY_EXTERNAL_CAPITAL_DECREASE_S2_ADMISSION_RUNTIME_JOIN_V1
UPSTREAM_S1_EDGE_SEAM_ID=EXTERNAL_CAPITAL_DECREASE_TO_TREASURY_PHASE_2_VENUE_OBSERVATION_V1
CAPITAL_ADMISSION_OWNER=capital_admission_contract_v1
JOIN_CLASS=TYPED_RUNTIME_JOIN_NOT_OWNER
DEPOSIT_E5_TOUCHED=false
DEPOSIT_INCREASE_SEMANTICS_ENABLED=false
TREASURY_MUTATION_AUTHORIZED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Authority

Capital admission remains owned by `capital_admission_contract_v1`. Phase-2
reconciliation join remains the treasury→admission evaluator. S2 adds a typed
fail-closed contract conjunct and a single productive runtime join entrypoint;
it does not create a parallel capital authority.

## Non-claims

```text
No deposit / E5 increase semantics
No AVAILABLE_FOR_SIZING or STEP-29P mint
No Treasury mutation, POST, or withdrawal send
No account-equity orchestration (E4) in this package
No Master-V2 / Double-Play / Top-5 / learning-loop changes
PDF TARGET_AUTHORITY=NONE
```
