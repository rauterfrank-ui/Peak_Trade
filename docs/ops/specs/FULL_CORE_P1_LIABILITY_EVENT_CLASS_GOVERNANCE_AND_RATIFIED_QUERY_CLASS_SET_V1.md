---
docs_token: DOCS_TOKEN_FULL_CORE_P1_LIABILITY_EVENT_CLASS_GOVERNANCE_AND_RATIFIED_QUERY_CLASS_SET_V1
status: active
scope: P1 liability event-class governance; P1-scoped ratified query-class set; no global EQUITY_STOCK kind-set uplift; offline sealed composition; AUTHORITY_EFFECT=NONE
capability: FULL_CORE_P1_LIABILITY_EVENT_CLASS_GOVERNANCE_AND_RATIFIED_QUERY_CLASS_SET_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Full Core P1 Liability Event Class Governance And Ratified Query Class Set V1

Derived spec. Non-SSOT. Closes `LIABILITY_EVENT_CLASS_COMPLETE` via P1-scoped
ratification of the sealed interest-accrued Market-loan query class (`type=2`).
Does not mutate global D6 `RATIFIED_CLASSIFIED_KIND_SET` or `KIND_SET_RESOLVED`.

```text
WP_ID=FULL_CORE_P1_LIABILITY_GOVERNANCE_AND_MAX_CLOSEOUT_TO_NEXT_REAL_BLOCKER_V1
CONSUMER=p1_completeness_witness_foundation_v1
EVIDENCE_CLASS=P1_LIABILITY_EVENT_CLASS_GOVERNANCE_WITNESS_V1
RATIFIED_P1_QUERY_CLASS=GET_/api/v5/account/interest-accrued
GLOBAL_KIND_SET_UPLIFT=false
AUTHORITY_EFFECT=NONE
owner=src/ops/governed_productive_account_equity_authority_producer_v1/p1_liability_event_class_governance_and_ratified_query_class_set_v1.py
```
