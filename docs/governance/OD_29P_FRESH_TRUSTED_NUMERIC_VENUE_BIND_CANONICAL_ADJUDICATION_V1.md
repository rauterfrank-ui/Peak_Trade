# OD 29P Fresh-Trusted Numeric Venue Bind — Canonical Adjudication v1

**Status:** BINDING scoped Owner-GO adjudication (docs + static contract only)  
**Baseline:** `origin&#47;main @ 5fbc61636b14e912f7148ef6bb91e4752db71a6a`  
**Machine contract:** [`config/governance/od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1.json`](../../config/governance/od_29p_fresh_trusted_numeric_venue_bind_canonical_adjudication_v1.json)

```text
OWNER_GO=OWNER_GO_OD_29P_FRESH_TRUSTED_NUMERIC_VENUE_BIND_BOUNDED_WP_V1
OWNER_GO_STATUS=CONSUMED
DECISION_CASE=D
INDEPENDENCE_GATE=PASS
NUMERIC_VENUE_BIND_RESOLVED=true
FRESH_TRUSTED_GET_CONTRACT_STATUS=BOUND
REAL_GET_EXECUTED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Scope (does not re-open #6960)

Source semantic `RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING` and transform
`DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1` remain as adjudicated in
PR #6960. This document binds **how a concrete venue numeric observation**
becomes the typed 29P risk-capital surface value under contract.

## Numeric chain (contractual)

`GET /api/v5/account/balance` (authorized read-only, evidence-only in tests) →
exactly one `details[ccy=USDC]` row → parse `availEq` (Decimal) → freshness/trust
gates → conditional P01 → dimension `RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING`.

Raw `availEq` is **not** final `available_for_sizing`. Producer wrap and P01
algebra from #6960 apply.

## Explicit non-claims

- No productive network GET executed by this adjudication.
- No credential load or secret resolution.
- Does not close `unk_sealed_venue_number_29p` (29P normative pack identity).
- Does not authorize `OD_EXTERNAL_EFFECT` / live credential GET execution.
- U01 eligibility and P01 directive mint preconditions remain separate blockers.
- Evidence packs may persist forensic GET artifacts; `VALUE_EPHEMERAL_NOT_DURABLE_ACROSS_RESTART=true` — replay must not mint fresh CURRENT sizing authority alone.

## F-02 / Treasury alignment

`WHOLE_CORE_COMPLETION_EGRESS_Q0_AUTHORITY_V1` closes F-02 for the enter-live
Treasury single-source path at governance truth level; this adjudication aligns
Law Map / CSIA navigation with that contract without activating runtime GET.
