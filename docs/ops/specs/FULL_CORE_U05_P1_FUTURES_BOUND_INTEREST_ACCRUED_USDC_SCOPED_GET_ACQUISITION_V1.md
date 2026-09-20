---
docs_token: DOCS_TOKEN_FULL_CORE_U05_P1_FUTURES_BOUND_INTEREST_ACCRUED_USDC_SCOPED_GET_ACQUISITION_V1
status: active
scope: P1-only one GET &#47;api&#47;v5&#47;account&#47;interest-accrued?type=2&#38;limit=100&#38;ccy=USDC for FUTURES_MODE; material scope differs from CD; P4 and U05 primary proof unchanged; max one GET; zero retries; CB offline qualification; P1 adjudication fail-closed
capability: FULL_CORE_U05_P1_FUTURES_BOUND_INTEREST_ACCRUED_USDC_SCOPED_GET_ACQUISITION_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-20
---

# Full Core U05 P1 FUTURES Bound Interest Accrued USDC-Scoped GET Acquisition V1

Derived spec. Non-SSOT. Consumes Owner-GO
`FULL_CORE_U05_P1_FUTURES_EVENT_SURFACE_DISCOVERY_BIND_AND_SINGLE_GET_TO_FIRST_HARD_BLOCKER_V1`.
Executes exactly one USDC-scoped interest-accrued GET distinct from CD
(`type=2&limit=100` without `ccy`). P1 evidence only; does not close U05, P4,
F12, or F13. Empty `data` is not absence proof.

```text
OWNER_GO=FULL_CORE_U05_P1_FUTURES_EVENT_SURFACE_DISCOVERY_BIND_AND_SINGLE_GET_TO_FIRST_HARD_BLOCKER_V1
EXACT_REQUEST=GET https:&#47;&#47;eea.okx.com&#47;api&#47;v5&#47;account&#47;interest-accrued?type=2&#38;limit=100&#38;ccy=USDC
P1_EVENT_SURFACE_ROLE=INDEPENDENT_LIABILITY_EVENT_EVIDENCE_ONLY
AUTHORIZED_GET_COUNT=1
RETRY_COUNT=0
P4_STATUS=UNKNOWN
PRIMARY_PROOF_CREATED=false
owner=src/ops/governed_productive_account_equity_authority_producer_v1/u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1.py
```
