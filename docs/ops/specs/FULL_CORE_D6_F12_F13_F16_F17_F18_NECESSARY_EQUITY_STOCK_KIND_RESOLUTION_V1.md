---
docs_token: DOCS_TOKEN_FULL_CORE_D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION_V1
status: active
scope: Full-Core D6 typed F12/F13/F16/F17/F18 adjudication against sealed S1-S6 plus #6452 mapping plus #6453 acquisition; all five remain UNKNOWN for missing primary evidence; GET unauthorized; no POST; no MS2; no D7; RAW_EQ_SOURCE_AUTHORITY=false; no LiveExecutionPort construction
capability: FULL_CORE_D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-13
---

# Full Core D6 F12 F13 F16 F17 F18 Necessary Equity Stock Kind Resolution V1

Derived spec. Non-SSOT. Canonical persist is Master Runbook §11.2.1.BG.

```text
OWNER_GO=OWNER_GO_D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION_V1
OWNER_GO_STATUS=CONSUMED
WORKPACKAGE=D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION_V1
SEALED_INPUT_ONLY=true
NEW_NETWORK_GET_COUNT=0
F12_DECISION=REMAIN_UNKNOWN
F13_DECISION=REMAIN_UNKNOWN
F16_DECISION=REMAIN_UNKNOWN
F17_DECISION=REMAIN_UNKNOWN
F18_DECISION=REMAIN_UNKNOWN
F12_F13_F16_F17_F18_STATUS=UNKNOWN
KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY=F12_F13_MISSING_NONZERO_LIABILITY_STOCK_PRIMARY_EVIDENCE_OR_RATIFIED_EQ_IDENTITY
EARLIEST_REMAINING_D6_BLOCKER=F12_F13_RESOLUTION_REQUIRES_NONZERO_LIABILITY_STOCK_PRIMARY_EVIDENCE_OR_RATIFIED_EQ_IDENTITY
RATIFIED_SOURCE_KINDS=NONE
KIND_SET=EMPTY_FAIL_CLOSED
KIND_SET_RESOLVED=false
MAPPING_PERSISTED=true
RAW_EQ_SOURCE_AUTHORITY=false
U05_KIND_DECISION=REMAIN_UNKNOWN
U06_KIND_DECISION=REMAIN_UNKNOWN
RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN
RETENTION_COVERAGE_STATUS=FAIL_CLOSED_NOT_PROVEN
ORDERING_COMPLETENESS_STATUS=FAIL_CLOSED_NOT_PROVEN
AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM=false
COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN=false
MS2_AUTHORIZED=false
D6_FULLY_CLOSED=false
D7_AUTHORIZED=false
ATLAS_AUTHORITY=NONE
C17_CREATED=false
RECONSTRUCTION_ENGINE_CREATED=false
AUTHORITY_EFFECT=NONE
```

This persist adjudicates F12, F13, F16, F17, and F18 individually against
already-sealed PACKAGE_1 Observation, S6 classification, the #6452
source-role mapping, and the #6453 acquisition pack. Empty, blank, and
zero liability tokens do not decide F12 or F13. Live `fee=0` and unpaired
archive nonzero `fee` do not decide F16, F17, or F18. Algebraic inference
from `eq` versus `cashBal` is forbidden. No classified EQUITY_STOCK source
kind is ratified. The remaining D6 blocker is ranked strictly narrower than
§11.2.1.BF: the earliest remaining blocker is F12/F13 resolution, which
requires a non-zero liability-stock primary observation or a ratified `eq`
identity. F16–F18 remain independently blocked on a paired fee-event and
equity-stock observation or a ratified `eq` identity. New GET is not
authorized. Mini-Slice 2, D6 closeout, and D7 remain unauthorized.
