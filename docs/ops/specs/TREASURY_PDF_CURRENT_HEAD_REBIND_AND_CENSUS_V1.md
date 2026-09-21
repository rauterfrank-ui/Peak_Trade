---
docs_token: DOCS_TOKEN_TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1
status: active
scope: Treasury PDF current-head rebind census; offline forensic adjudication; PDF_AUTHORITY=NONE; stops at first real blocker
capability: TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-21
---

# Treasury PDF Current Head Rebind And Census V1

Derived spec. Non-SSOT. Rebinds Owner-supplied Treasury audit PDF (§§1–11
historical audit brief; §§12–26 target design only) against CURRENT
`origin/main` evidence. Does not authorize network, credentials, or mutation.

```text
WP_ID=TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1
PDF_AUTHORITY=NONE
AUTHORITY_EFFECT=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
owner=src/ops/treasury_pdf_current_head_rebind_and_census_v1/census_v1.py
EVIDENCE_CLASS=TREASURY_PDF_CURRENT_HEAD_REBIND_AND_CENSUS_V1
```

## Stop boundary

This WP materializes census + durable evidence only. The first real blocker
after Phase-3 shadow binding is **productive read-only treasury/venue
observation** under scoped Owner-GO (PL_TF_002-class session + credential load).
That step is **not** executed here.

```text
EARLIEST_REAL_TREASURY_BLOCKER=PRODUCTIVE_READ_ONLY_TREASURY_VENUE_OBSERVATION_REQUIRES_OWNER_SCOPED_NETWORK_AND_CREDENTIAL_GO
```
