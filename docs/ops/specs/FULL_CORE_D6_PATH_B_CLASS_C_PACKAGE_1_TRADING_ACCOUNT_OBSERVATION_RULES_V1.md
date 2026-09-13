---
docs_token: DOCS_TOKEN_FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1
status: active
scope: Full-Core D6 PATH_B CLASS_C PACKAGE_1 trading-account observation rules persist; selected observation surfaces and fail-closed semantic laws only; GET unauthorized; observation not executed; U05/U06/Residual remain REMAIN_UNKNOWN; kind-set remains unresolved; Mini-Slice 2 not released; D7 not authorized; C01 not rehabilitated; Atlas authority remains NONE; no venue GET; no reconstruction engine; no C17; no mapping; no producer; no runtime binding; no POST; no wire; no LiveExecutionPort construction
capability: FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 PATH_B CLASS_C PACKAGE_1 Trading Account Observation Rules V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.AZ.

```text
OWNER_SELECTION=OWNER_SELECT_D6_PATH_B_CLASS_C_PACKAGE_1_TRADING_ACCOUNT_OBSERVATION_RULES_V1
OWNER_SELECTION_STATUS=CONSUMED
WORKPACKAGE=D6_PATH_B_CLASS_C_PACKAGE_1_CANONICAL_PERSIST_V1
SELECTED_OPTION=OPTION_D
PACKAGE_1_PERSISTED=true
PATH_B_PREAUTHORIZATION_READY=true
EXECUTION_READY=false
OBSERVATION_EXECUTED=false
OBSERVATION_EXECUTION_AUTHORIZED=false
OBSERVATION_NETWORK_GET_AUTHORIZED=false
SELECTED_OBSERVATION_SURFACES=GET_/api/v5/account/config,GET_/api/v5/account/balance,GET_/api/v5/account/bills,GET_/api/v5/account/bills-archive,GET_/api/v5/account/subtypes
D4_RULE_PERSISTED=true
D4_OBSERVED_FIELDS_ARE_RUNTIME_EVIDENCE_ONLY=true
D4_OBSERVATION_MUST_NOT_MINT_IDENTITY=true
BALANCE_RULE_PERSISTED=true
BALANCE_OBSERVATION_DOES_NOT_REHABILITATE_C01=true
RAW_EQ_SOURCE_AUTHORITY=false
EQ_ROLE=RECONCILIATION_OR_EMBEDDING_TARGET_ONLY
OBSERVED_COMPONENT_FIELDS_HAVE_AUTHORITY_EFFECT=NONE
EMPTY_COVERAGE_RULE_PERSISTED=true
EMPTY_ROWS_MEAN_ONLY_NO_ROWS_OBSERVED_WITHIN_EXECUTED_QUERY=true
EMPTY_ROWS_PROVE_ZERO_EVENTS=false
EMPTY_ROWS_PROVE_KIND_ABSENCE=false
PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED=true
PAGINATION_EXHAUSTION_PROVES_COMPLETENESS=false
RETENTION_GAP_FAIL_CLOSED=true
ORDERING_OR_TIE_AMBIGUITY_FAIL_CLOSED=true
EMBEDDING_RULE_PERSISTED=true
EMBEDDING_OPTION=E_OPTION_A_FAIL_CLOSED_UNKNOWN_ALLOWED
UNKNOWN_EMBEDDING_FACTS=F12_LIABILITY_AFFECTS_EQUITY_STOCK,F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ,F16_FEE_ALREADY_EMBEDDED_IN_EQ,F17_FEE_SEPARATE_ACCOUNT_DELTA,F18_FEE_RECONCILIATION_ONLY
U05_KIND_DECISION=REMAIN_UNKNOWN
U06_KIND_DECISION=REMAIN_UNKNOWN
RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN
KIND_SET_RESOLVED=false
RATIFIED_CLASSIFIED_EVENT_KIND_SET=EMPTY_FAIL_CLOSED
MS1_KIND_SET_FULLY_CLOSED=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
PATH_A=REJECT
PATH_B=SELECTED_BUT_BLOCKED_ON_NEW_AUTHORIZATION
PATH_C=REJECT
CANDIDATE_SURFACE_SELECTION=NONE_SELECTED
ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL=true
ATLAS_AUTHORITY=NONE
C01_REHABILITATION_FORBIDDEN=true
AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT=false
EVENT_KIND_SOURCE_SEAM_SELECTED=false
SOURCE_SELECTED=false
MAPPING_PROVEN=false
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
NETWORK_GET_PERFORMED=false
NETWORK_POST_PERFORMED=false
LIVE_ENABLED=false
LIVE_ARMED=false
WIRE_SEND_PERMITTED=false
D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT
EARLIEST_D6_KIND_SET_DEPENDENCY=NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET
EARLIEST_D6_COMPLETENESS_DEPENDENCY=RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM
AUTHORITY_EFFECT=NONE
```

This persist selects CLASS_C PACKAGE_1 observation surfaces and records
the fail-closed D4, balance, empty-coverage, and embedding laws. It does
not execute observation. It does not authorize GET. Surface selection is
not Atlas uplift, Mini-Slice 2 source-seam authorization, kind
ratification, C01 rehabilitation, D7 authorization, or Live/Canary
authorization. `PATH_B_PREAUTHORIZATION_READY` is true only because these
CLASS_C semantics are selected and persisted. `EXECUTION_READY` remains
false.

D4 rule: observed `uid` / `mainUid` / `settleCcy` / `account-mode` are
runtime evidence only. A later GET may corroborate an already-existing
typed D4 runtime binding. It must not mint D4 identity. Credential, env,
and default identity authority remain forbidden. Mismatch must fail
closed.

Balance rule: allowed observation-only fields may include `eq`,
`cashBal`, `liab`, `crossLiab`, `isoLiab`, `interest`, `upl`, `uplLiab`,
and `uTime`. They must not become EQUITY_STOCK source authority, P01
authority or input, sizing authority, D5 claimed-equity authority, or
kind-ratification evidence by themselves.

Empty-coverage rule: empty rows mean only that no rows were observed
within the executed query. Empty rows do not prove zero events or kind
absence. Pagination exhaustion proves query traversal completed, not
completeness. Retention gap and ordering or tie ambiguity fail closed.

Embedding rule: option A remains fail-closed unknown allowed. F12, F13,
F16, F17, and F18 remain UNKNOWN unless separately proven. No algebraic
inference. No INCLUDE or EXCLUDE from UNKNOWN.
