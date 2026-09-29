# OD U01 Eligibility + P01 Directive → 29P Sizing-Mint — Canonical Adjudication v1

**Status:** BINDING scoped Owner-GO adjudication (docs + static contract only)  
**Baseline:** `origin&#47;main @ 6268fab255353ceed84384051de1c045232f3a4c`  
**Machine contract:** [`config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json`](../../config/governance/od_u01_p01_29p_sizing_mint_canonical_adjudication_v1.json)

```text
OWNER_GO=OWNER_GO_OD_U01_P01_29P_SIZING_MINT_BOUNDED_WP_V1
OWNER_GO_STATUS=CONSUMED
DECISION_CASE=D
DEPENDENCY_GATE=PASS
REAL_GET_EXECUTED=false
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Scope

Closes the **semantic and join-contract** chain from U01 account-mode eligibility and
P01 governed reduction directive through the three-input mint into typed 29P risk-capital,
without re-opening PR #6960 transform semantics or PR #6961 numeric venue bind.

Does **not** close `OD_SEALED_VENUE_29P_NORMATIVE` (common epoch sealed identity,
venue number pack). Join-level `decision_epoch` alignment is proven; sealed normative
epoch remains `UNKNOWN_CURRENT`.

## U01 (eligibility, not numeric)

Raw venue field `acctLv` on `GET &#47;api&#47;v5&#47;account&#47;config` is adapted by
`CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_ADAPTER_V1`. Productive eligibility requires raw
`2` → semantic `FUTURES_MODE`. Missing, unknown, unmapped, or `OPEN` fail closed.
No eligibility fact ⇒ no sizing mint.

## P01 (standing policy directive)

`CURRENT_PRODUCTIVE_P01_POLICY_DOES_NOT_APPLY_V1` is mandatory at produce bind time
(architectural redundancy). Applicability `UNKNOWN_FAIL_CLOSED` blocks mint. P01 is
not optional skip: `DOES_NOT_APPLY` with zero contribution is the ratified directive.
Venue GETs do not decide P01 applicability.

Transform at numeric layer remains
`DETAILS_USDC_AVAILEQ_MINUS_CONDITIONAL_P01_USDC_V1` (#6960); under standing policy,
P01 contribution is zero with exactly one policy evaluation at mint join.

## Three-input mint join

Treasury single-source handoff →
`bind_current_productive_u04_p01_eligibility_inputs_and_produce_v1` wires U01, P01, U04,
and numeric base, then `produce_current_productive_29p_risk_capital_v1` mints typed
29P output. All inputs must share account, venue, tdMode, and `decision_epoch`.

`TECHNICALLY_PRESENT != SEMANTICALLY_JOINABLE` — enforced by producer reason codes.

## Explicit non-claims

- No productive GET, credential load, POST, or live enable.
- No new P01 policy, default P01=0 without directive, or new epoch definition.
- No Master V2 / Double Play mutation.
- Does not authorize `OD_EXTERNAL_EFFECT`.

## Remaining owner boundary

`OD_SEALED_VENUE_29P_NORMATIVE`: sealed common-epoch semantics and full 29P normative
pack identity beyond join `decision_epoch` equality.
