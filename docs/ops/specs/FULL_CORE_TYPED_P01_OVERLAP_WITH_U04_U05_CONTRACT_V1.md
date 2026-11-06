---
docs_token: DOCS_TOKEN_FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT_V1
status: active
scope: Full-Core typed P01 overlap/equivalence adjudication versus U04 and U05; both remain independently unresolved fail-closed; no productive reconstruction; no source selection; no mapping; no producer implementation; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
---

# Full Core Typed P01 Overlap With U04 U05 Contract V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AG.

```text
P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT=true
P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT=false
P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT=NONE
P01_U04_OVERLAP_RESOLVED=false
P01_U04_OVERLAP_STATE=UNRESOLVED
P01_U04_OVERLAP_ADJUDICATION=UNKNOWN_RELATIONSHIP_FAIL_CLOSED
P01_U05_OVERLAP_RESOLVED=false
P01_U05_OVERLAP_STATE=UNRESOLVED
P01_U05_OVERLAP_ADJUDICATION=UNKNOWN_RELATIONSHIP_FAIL_CLOSED
P01_OVERLAP_STATE=U06_ACCRUED_FEES_DISTINCT_P01_U04_OVERLAP_UNRESOLVED_P01_U05_OVERLAP_UNRESOLVED_UNKNOWN_OVERLAP_FAIL_CLOSED
P01_EMBEDDED_STATE_RESOLVED=false
P01_EMBEDDED_STATE=UNRESOLVED
P01_EQUITY_BASE_INCLUSION_RESOLVED=false
P01_EQUITY_BASE_INCLUSION_STATUS=UNRESOLVED
P01_APPLICABILITY_RESOLVED=false
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
evidence does not prove whether P01 is economically equivalent, partially
overlapping, fully overlapping, disjoint, nested, member-dependent, or
applicability-dependent with U04 pending-order reservation semantics or U05
liability semantics. The two counterparts remain independently unresolved.
Semantic equivalence, economic overlap, representational nesting, shared
provenance, shared numeric value, shared unit, simultaneous applicability,
and arithmetic interaction remain distinct and unresolved. Unknown remains
fail-closed and is not `DISJOINT`, `EQUIVALENT`, `NON_OVERLAPPING`,
`SAFE_TO_SUM`, `SAFE_TO_NET`, `SAFE_TO_SUBTRACT`, `SAFE_TO_OMIT`, or
`SAFE_TO_DEDUPLICATE`. Zero, absence, missing, and malformed inputs do not
prove disjointness. Equal values, shared source, and shared unit do not
prove equivalence. Unresolved term-set, applicability, or embedding does
not decide overlap. U04/U05 labels do not decide overlap. U06 accrued-fee
distinctness remains pinned and is not a P01↔U06 disjoint, equivalent, or
embedding rule. Unknown overlap cannot authorize summation, omission,
netting, subtraction, or deduplication. Schema presence is not P01 semantic
resolution. Algebra completeness remains false. C01–C21 remain rejected.
