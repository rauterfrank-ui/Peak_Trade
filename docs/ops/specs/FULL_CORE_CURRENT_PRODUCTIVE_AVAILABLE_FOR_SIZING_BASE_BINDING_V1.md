---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1
status: active
scope: Bind numeric CURRENT_PRODUCTIVE AVAILABLE_FOR_SIZING BASE from typed Treasury reconciled observation after C08 base candidacy; no Treasury risk/sizing mint; STEP-29P unchanged
capability: FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Full Core Current Productive Available For Sizing Base Binding V1

Consumes Owner-GO `OWNER_GO_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1`.

```text
WP_ID=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_BINDING_V1
BASE_BINDING_IMPLEMENTED=true
OBSERVATION_SCHEMA_CLASS=NON_FORBIDDEN_NON_EQ_NON_STOCK_USDC_CURRENT_PRODUCTIVE_OBSERVATION_V1
EXACT_ALLOWED_NUMERIC_SOURCE=TreasuryVenueObservationV1.venue_balance_raw_via_treasury_phase_2_reconciled_venue_balance
UPSTREAM_VENUE_FIELD=funding_availBal_usdc
BASE_SLOT=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE
C08_BASE_CANDIDACY_REQUIRED=true
NUMERIC_BASE_MODULE_STATUS=UNBOUND
NETWORK_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
TREASURY_RISK_ADMISSIBLE_MINT=false
TREASURY_AVAILABLE_FOR_SIZING_MINT=false
STEP_29P_POLICY_CHANGED=false
```

## Wiring

Treasury venue observation → Phase-2 reconciliation → capital admission → E4 → C08 base candidacy → **typed observation** → numeric BASE fact → existing CT producer algebra (U04/P01/eligibility still required for produce).

Positive sizing capacity still requires STEP-29P admit; Treasury does not mint risk-admissible or AVAILABLE_FOR_SIZING.

## Next blocker

```text
EARLIEST_NEW_REAL_BLOCKER=CURRENT_PRODUCTIVE_CT_SIZING_PRODUCE_BLOCKED_U04_P01_ELIGIBILITY_INPUTS_UNBOUND
```
