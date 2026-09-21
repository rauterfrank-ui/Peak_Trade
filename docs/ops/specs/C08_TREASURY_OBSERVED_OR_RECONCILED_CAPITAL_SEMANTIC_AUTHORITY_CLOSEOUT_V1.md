---
docs_token: DOCS_TOKEN_C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_SEMANTIC_AUTHORITY_CLOSEOUT_V1
status: active
scope: C08 treasury capital semantic authority closeout before productive sizing-source binding; split OBSERVED vs RECONCILED vs RISK_ADMISSIBLE; increase/decrease asymmetry; adversarial matrix; no runtime binding
capability: C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_SEMANTIC_AUTHORITY_CLOSEOUT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# C08 Treasury Observed Or Reconciled Capital Semantic Authority Closeout V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook **CURRENT Treasury Phase Bindings**
(`C08_SEMANTIC_CLOSEOUT_*` tokens).

Consumes Owner-GO
`OWNER_GO_C08_SEMANTIC_AUTHORITY_CLOSEOUT_BEFORE_PRODUCTIVE_SIZING_SOURCE_BINDING_V1`.

```text
WP_ID=C08_SEMANTIC_AUTHORITY_CLOSEOUT_BEFORE_PRODUCTIVE_SIZING_SOURCE_BINDING_V1
C08_SURFACE_EXISTS=true
C08_CURRENT_BINDING=UNBOUND
C08_CURRENT_CLASSIFICATION=NOT_PROVEN
C08_SEMANTIC_CLOSEOUT=CLOSED
C08_PRODUCTIVE_BINDING_AUTHORIZED=false
C08_PRODUCTIVE_BINDING_IMPLEMENTED=false
C08_SEMANTIC_AUTHORITY_CLOSEOUT_CONTRACT_AUTHORITY_EFFECT=NONE
PDF_AUTHORITY=NONE
NETWORK_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Census candidate (transport label only)

```text
C08_CANDIDATE=C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL
C08_CURRENT_PRODUCER=ops.treasury_phase_2_read_only_reconciliation_v1;ops.treasury_productive_read_only_venue_observation_v1;ops.offline_funding_balance_read_producer_v1
C08_PROPOSED_CONSUMER=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1_BASE_SLOT_UNBOUND
```

The census fingerprint **must not** be read as merged OBSERVED-or-RECONCILED sizing
authority. This closeout splits capital classes.

## Authority owners (unchanged)

```text
CURRENT_SIZING_OWNER=capital_risk_admissibility_owner_v1
CURRENT_RISK_ADMISSIBILITY_OWNER=capital_risk_admissibility_owner_v1
CURRENT_ACCOUNT_EQUITY_OWNER=ops.governed_productive_account_equity_authority_producer_v1
TREASURY_OWNER=ops.treasury_phase_2_read_only_reconciliation_v1
CAPITAL_ADMISSION_OWNER=capital_admission_contract_v1
EXECUTION_OWNER=canonical_order_intent_owner_v1
CURRENT_ALLOWED_SIZING_INPUT=RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING
```

## Capital classes (non-negotiable separation)

| Class | Definition | Producer / owner | May increase sizing capacity | May decrease or block |
| --- | --- | --- | --- | --- |
| TREASURY_OBSERVED_CAPITAL | Phase-2 observation / reconciliation class OBSERVED; no reconciled economic effect | `ops.treasury_phase_2_read_only_reconciliation_v1` | **No** | **Yes** (fail-closed / admission deny) |
| TREASURY_RECONCILED_CAPITAL | Phase-2 class RECONCILED; capital admission evaluated; orchestration ingress may consume | `capital_admission_contract_v1` + Treasury join | **No** alone (`CAPITAL_INCREASE_NOT_AUTO_ADMITTED`) | **Yes** |
| RISK_ADMISSIBLE_CAPITAL | STEP-29P `evaluate_step_29p_capital_risk_admissibility_v1` on typed AVAILABLE_FOR_SIZING claim | `capital_risk_admissibility_owner_v1` | **Yes** (only class) | **Yes** |

Treasury does **not** mint `RISK_ADMISSIBLE`. Reconciliation does **not** substitute
for risk admissibility. Observation does **not** increase productive sizing capacity.

## C08 semantic contract (future binding boundary)

```text
C08_INPUT_CLASS=TREASURY_ACCOUNT_EQUITY_ORCHESTRATION_INGRESS_V1_RECONCILED_BASE_CANDIDATE_EVIDENCE
C08_INCREASE_ELIGIBILITY=NONE_FROM_TREASURY_OBSERVED_OR_RECONCILED_ALONE;PRODUCTIVE_SIZING_CAPACITY_INCREASE_REQUIRES_STEP_29P_RISK_ADMISSIBLE
C08_DECREASE_ELIGIBILITY=CONSERVATIVE_BLOCK_OR_DECREASE_VIA_CAPITAL_ADMISSION_AND_TREASURY_FAIL_CLOSED;CREDIBLE_EXTERNAL_DEPLETION_SIGNAL_VIA_TREASURY_PHASE_2_DECREASE_BINDING;NO_TREASURY_MINT_OF_RISK_ADMISSIBLE_FOR_DECREASE
C08_RECONCILIATION_REQUIREMENT=FUTURE_BASE_CANDIDACY_REQUIRES_TreasuryReconciliationClassV1_RECONCILED;OBSERVED_UNKNOWN_STALE_AMBIGUOUS_INSUFFICIENT_FOR_BASE_CANDIDACY
C08_RISK_ADMISSIBILITY_REQUIREMENT=MANDATORY_SEPARATE_OWNER capital_risk_admissibility_owner_v1;evaluate_step_29p_capital_risk_admissibility_v1;TREASURY_CANNOT_MINT_OR_SUBSTITUTE
C08_UNKNOWN_BEHAVIOR=FAIL_CLOSED
C08_STALE_BEHAVIOR=FAIL_CLOSED
C08_ABSENT_BEHAVIOR=FAIL_CLOSED
C08_CONFLICTED_BEHAVIOR=FAIL_CLOSED
```

Future productive binding may attach **RECONCILED** orchestration ingress evidence toward
the **unbound** BASE slot of `CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_V1` only
under a separate Owner-GO. It still does not bypass STEP-29P risk admissibility for
capacity **increase**.

## E4 / #6672–#6673 regression (semantic preservation)

Orchestration ingress and host evaluation semantics remain:

```text
USDC_ROW_STATUS=ABSENT_NOT_ZERO
RECONCILIATION_STATUS=UNKNOWN
UNKNOWN_PRESERVED=true
TREASURY_CAPITAL_ADMITTED=false
OBSERVED_EQUITY_MINTED=false
RECONCILED_EQUITY_MINTED=false
RISK_ADMISSIBLE_MINT=false
SIZING_CAPACITY_INCREASE=false
```

## Non-claims

```text
No C08 runtime wiring
No STEP_29P formula change
No AVAILABLE_FOR_SIZING mint in this WP
No Treasury mutation or network
No parallel sizing or risk owner
No authority graph owner transfer
```

## Next blocker

```text
EARLIEST_NEW_REAL_BLOCKER=C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL_PRODUCTIVE_SIZING_SOURCE_NOT_BOUND
NEXT_OWNER_GO_REQUIRED=OWNER_GO_C08_PRODUCTIVE_SIZING_SOURCE_BINDING_AFTER_SEMANTIC_CLOSEOUT_V1
```
