---
docs_token: DOCS_TOKEN_FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1
status: active
scope: P1 max evidence campaign; bounded read-only OKX GET; witness consumption; #6665 re-evaluation
capability: FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Full Core P1 Max Evidence Campaign To Next Real Blocker V1

Derived spec. Non-SSOT. Bounded read-only venue observation campaign
consuming #6666 witness foundation and re-evaluating #6665 closeout.
Stops at first real blocker outside this WP authority.

```text
WP_ID=FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1
BASE_CAPABILITY=FULL_CORE_P1_COMPLETENESS_WITNESS_FOUNDATION_V1
CONSUMER=p1_negative_completeness_closeout_contract_v1
MAX_AUTHORIZED_GET_COUNT=1
GET_SURFACE=GET_/api/v5/account/interest-accrued
QUERY=type=2&limit=100
AUTHORITY_EFFECT=NONE
owner=src/ops/governed_productive_account_equity_authority_producer_v1/p1_max_evidence_campaign_to_next_real_blocker_v1.py
```
