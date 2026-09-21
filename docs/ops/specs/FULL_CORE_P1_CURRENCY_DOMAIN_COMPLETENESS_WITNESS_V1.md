---
docs_token: DOCS_TOKEN_FULL_CORE_P1_CURRENCY_DOMAIN_COMPLETENESS_WITNESS_V1
status: active
scope: P1 currency-domain completeness witness; bounded interest-limits GET; closed-world enumeration; sealed interest-accrued composition; AUTHORITY_EFFECT=NONE
capability: FULL_CORE_P1_CURRENCY_DOMAIN_COMPLETENESS_WITNESS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Full Core P1 Currency Domain Completeness Witness V1

Derived spec. Non-SSOT. Closes `CURRENCY_DOMAIN_COMPLETE` via closed-world
enumeration from `GET /api/v5/account/interest-limits?type=2` composed with
sealed zero-row interest-accrued packs. Settlement USDC, optional `ccy=USDC`
filter, and zero rows alone do not mint completeness.

```text
WP_ID=FULL_CORE_P1_CURRENCY_DOMAIN_BLOCKER_MAX_IMPLEMENTATION_TO_NEXT_REAL_BLOCKER_V1
MAX_AUTHORIZED_GET_COUNT=1
GET_SURFACE=GET_/api/v5/account/interest-limits
QUERY=type=2
CONSUMER=p1_completeness_witness_foundation_v1
EVIDENCE_CLASS=P1_CURRENCY_DOMAIN_COMPLETENESS_WITNESS_V1
AUTHORITY_EFFECT=NONE
owner=src/ops/governed_productive_account_equity_authority_producer_v1/p1_currency_domain_completeness_witness_v1.py
```
