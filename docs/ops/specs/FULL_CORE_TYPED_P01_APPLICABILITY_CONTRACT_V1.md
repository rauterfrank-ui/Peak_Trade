---
docs_token: DOCS_TOKEN_FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT_V1
status: active
scope: Full-Core typed P01 applicability adjudication contract; applicability remains unspecified fail-closed; no productive reconstruction; no source selection; no mapping; no producer implementation; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
---

# Full Core Typed P01 Applicability Contract V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AD.

```text
P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT=true
P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT=false
P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT=NONE
P01_APPLICABILITY_RESOLVED=false
P01_APPLICABILITY_STATUS=UNSPECIFIED_FAIL_CLOSED
P01_APPLICABILITY_RULE=UNSPECIFIED_FAIL_CLOSED
P01_TERM_SET_RESOLVED=false
P01_VALUE_UNIT_CLASS_RESOLVED=false
P01_TERM_SEMANTICS_RESOLVED=false
P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false
P01_REMAINING_UNRESOLVED_SEMANTICS=P01_TERM_SET_UNSPECIFIED,P01_VALUE_UNIT_CLASS_UNSPECIFIED,P01_APPLICABILITY_UNSPECIFIED,P01_EQUITY_BASE_INCLUSION_UNRESOLVED,P01_EMBEDDING_UNRESOLVED,P01_OVERLAP_WITH_U04_U05_UNRESOLVED,P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED
RECONSTRUCTION_ALGEBRA_SCHEMA_PRESENT=true
RECONSTRUCTION_ALGEBRA_COMPLETE=false
RECONSTRUCTION_ALGEBRA_AUTHORITY_EFFECT=NONE
CANONICAL_FORMULA_PROVEN=false
SOURCE_SELECTED=false
MAPPING_PROVEN=false
GOVERNED_PRODUCER_CREATED=false
LIVE_ACCOUNT_BOUND_JOIN_PRESENT=false
STEP_29P_RISK_ADMISSIBLE=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1
EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING
EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED
```

This persist types the forensic adjudication that canonical repository
evidence does not prove when P01 applies, does not apply, or is
conditionally applicable. `P01_STATUS=DECIDED` is existence of a possible
term, not an applicability rule. Unknown remains fail-closed and is not
`NOT_APPLICABLE`. Zero, absence, missing, and malformed inputs are not
`NOT_APPLICABLE`. Unresolved term-set or unit class does not decide
applicability. U04/U05/U06 and venue-raw fields do not decide applicability.
Schema presence is not P01 semantic resolution. Algebra completeness remains
false. C01–C21 remain rejected.
