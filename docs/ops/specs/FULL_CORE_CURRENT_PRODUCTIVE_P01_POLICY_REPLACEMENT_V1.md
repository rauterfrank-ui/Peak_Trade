---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1
status: active
scope: Full-Core CURRENT_PRODUCTIVE P01 policy replacement; explicit DOES_NOT_APPLY by architectural redundancy; missing remains UNKNOWN; same-epoch U01 plus details[ccy=USDC].availEq GET; CU mint without U04 double-count; 29P reevaluation; first real blocker Live Account Bound and instrument scope; no POST; no Live enable
capability: FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-15
---

# Full Core Current Productive P01 Policy Replacement V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.CX.
Consumes Owner-GO
`CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1`.
Atlas remains `NAVIGATION_ONLY` / `AUTHORITY=NONE`.

P01 is a Peak_Trade-governed risk/sizing term, not a venue fact. Fresh
venue GETs may supply current account/capital evidence and must not
decide P01 `APPLIES`/`DOES_NOT_APPLY` from themselves. Historical P01
reconstruction is out of scope.

The current productive architecture already nets venue free margin in
`details[ccy=USDC].availEq` (including in-use / open-order reservation)
and applies Peak_Trade conservatism in STEP-29P capital/order/risk/
exposure/venue caps and `max_positions`. No independent monetary
haircut remains at the capital-input layer. Therefore the new
CURRENT_PRODUCTIVE P01 policy is explicit `DOES_NOT_APPLY`. Basis =
architectural redundancy, not historical absence.

Missing, empty, stale, or invalid directives remain
`UNKNOWN_FAIL_CLOSED`. Empty evaluator output is not `DOES_NOT_APPLY`.
`P01_RUNTIME_INSTANCE_PRESENT` remains false. Reconstruction runtime
instance is not flipped.

```text
OWNER_GO=CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_AND_29P_CONTINUATION_V1
OWNER_GO_STATUS=CONSUMED
P01_POLICY_DECISION=DOES_NOT_APPLY
P01_DECISION_BASIS=ARCHITECTURAL_REDUNDANCY_NOT_HISTORICAL_ABSENCE
P01_INDEPENDENT_SAFETY_FUNCTION=false
P01_FORMULA=P01_CONTRIBUTION=0_BY_EXPLICIT_DOES_NOT_APPLY
P01_AUTHORIZED_INPUTS=NONE_STANDING_POLICY_NOT_VENUE_DERIVED
P01_LEGACY_RECONSTRUCTION_PERFORMED=false
P01_RUNTIME_INSTANCE_PRESENT=false
GET_ENDPOINT_U01=/api/v5/account/config
GET_ENDPOINT_BALANCE=/api/v5/account/balance
AUTHORIZED_GET_COUNT=2
POST_COUNT=0
U04_SUBTRACTED=false
STEP_29P_RISK_ADMISSIBLE=false
FIRST_DEFINITIVE_BLOCK=LIVE_ACCOUNT_BOUND_NOT_TRUSTED_AND_STEP_29P_INSTRUMENT_SCOPE_MISSING
ATLAS_AUTHORITY=NONE
```
