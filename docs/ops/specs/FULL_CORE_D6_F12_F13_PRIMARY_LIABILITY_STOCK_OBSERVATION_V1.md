---
docs_token: DOCS_TOKEN_FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1
status: active
scope: Full-Core D6 F12/F13 primary liability-stock observation; one authorized READ-ONLY GET /api/v5/account/balance; raw sealed; F12/F13 remain UNKNOWN after empty/zero/absent tokens; F16-F18 not observed; no POST; no MS2; no D7; RAW_EQ_SOURCE_AUTHORITY=false; no LiveExecutionPort construction
capability: FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 F12 F13 Primary Liability Stock Observation V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.BH.

```text
OWNER_GO=OWNER_GO_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1
OWNER_GO_STATUS=CONSUMED
WORKPACKAGE=D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1
OBSERVATION_AUTHORITY_VALIDATED=true
AUTHORIZED_GET_SURFACES=GET_/api/v5/account/balance
GET_COUNT=1
POST_COUNT=0
ACCOUNT_MUTATION_PERFORMED=false
NONZERO_LIABILITY_OBSERVED=false
RAW_EVIDENCE_SEALED=true
F12_DECISION=REMAIN_UNKNOWN
F13_DECISION=REMAIN_UNKNOWN
F16_DECISION=REMAIN_UNKNOWN
F17_DECISION=REMAIN_UNKNOWN
F18_DECISION=REMAIN_UNKNOWN
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY=F12_F13_AUTHORIZED_FRESH_BALANCE_GET_EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE
EARLIEST_REMAINING_D6_BLOCKER=F12_F13_REMAIN_UNKNOWN_AFTER_AUTHORIZED_FRESH_BALANCE_GET_EMPTY_OR_ZERO_DOES_NOT_PROVE_ABSENCE
RATIFIED_SOURCE_KINDS=NONE
KIND_SET=EMPTY_FAIL_CLOSED
KIND_SET_RESOLVED=false
RAW_EQ_SOURCE_AUTHORITY=false
U05_KIND_DECISION=REMAIN_UNKNOWN
U06_KIND_DECISION=REMAIN_UNKNOWN
RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN
RETENTION_COVERAGE_STATUS=FAIL_CLOSED_NOT_PROVEN
ORDERING_COMPLETENESS_STATUS=FAIL_CLOSED_NOT_PROVEN
COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
ATLAS_AUTHORITY=NONE
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
AUTHORITY_EFFECT=NONE
```

This persist consumes one Owner-GO-scoped READ-ONLY GET of the already
selected PACKAGE_1 surface `GET &#47;api&#47;v5&#47;account&#47;balance`. Raw response
bytes are sealed before forensic token extraction. USDC liability tokens
are the empty string; EUR liability tokens are the exact string `0`;
account-level `liab`/`crossLiab`/`isoLiab` are absent. Empty, zero,
blank, missing, and null are not normalized and do not prove kind
absence. F12 and F13 remain `REMAIN_UNKNOWN`. No EQUITY_STOCK source
kind is ratified. Venue `eq` remains a reconciliation target only.
F16–F18 were not observed. Repeat GET hoping for a non-zero liability
is forbidden. Mini-Slice 2, D6 closeout, and D7 remain unauthorized.
