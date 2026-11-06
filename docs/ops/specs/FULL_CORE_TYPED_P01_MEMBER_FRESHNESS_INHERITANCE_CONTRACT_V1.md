---
docs_token: DOCS_TOKEN_FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1
status: active
scope: Full-Core typed P01 member freshness inheritance adjudication; freshness remains unproven fail-closed; U09 is comparison evidence only; no productive reconstruction; no source selection; no mapping; no producer implementation; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-12
---

# Full Core Typed P01 Member Freshness Inheritance Contract V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AI.

```text
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_SCHEMA_PRESENT=true
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT=false
P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT_AUTHORITY_EFFECT=NONE
P01_MEMBER_FRESHNESS_INHERITANCE_RESOLVED=false
P01_MEMBER_FRESHNESS_STATUS=UNPROVEN
P01_MEMBER_FRESHNESS_RULE=UNSPECIFIED
P01_U09_FRESHNESS_RELATION=UNSPECIFIED
P01_NUMERIC_VALUE_PROVENANCE_RESOLVED=false
P01_NUMERIC_VALUE_PROVENANCE_STATUS=UNSPECIFIED
P01_U04_OVERLAP_RESOLVED=false
P01_U05_OVERLAP_RESOLVED=false
P01_EMBEDDED_STATE_RESOLVED=false
P01_EQUITY_BASE_INCLUSION_RESOLVED=false
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
evidence does not prove a P01 freshness dimension, P01 timestamp, P01-level
or member-level freshness metadata, or a member-to-P01 inheritance rule.
U09 remains `FRESH_GET_PER_PRETRADE_DECISION` as a distinct algebra slot and
is comparison evidence only. U09 is not P01 freshness authority. P01
freshness does not inherit U09 and is not equivalent to U09. Unproven,
unknown, and unspecified freshness are not freshness authorization.
Oldest/newest/min/max/composite/source-specific/independent-timestamp
rules remain unproven and are not ratified. Current time is not P01
freshness. Missing freshness is not fresh. Stale P01 is not admissible.
Unproven freshness cannot authorize ignore, fallback, or stale filtering.
Schema presence is not P01 semantic resolution. Algebra completeness remains
false. Cap 11.1 construction remains forbidden.
