# Peak_Trade — Persistence Remediation Tracker

```text
AUTHORITY=NONE
DOCUMENT_ROLE=TRACKED_NONAUTHORITATIVE_REMEDIATION_TRACKER
LIFECYCLE=RETIRED_CLOSED_NONAUTHORITATIVE_RETAINED_FOR_AUDIT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
BASELINE_ORIGIN_MAIN_SHA=bc59e1e331588ab7e727c6909baa69e8a00d93da
CREATED_FOR=SECTION_11_13_5_POST_K_PERSISTENCE_REMEDIATION
OWNER_GO=OWNER_GO_FOR_PERSISTENCE_CLOSEOUT_AND_TRACKER_RETIREMENT_PREPARATION_NO_FUNDING_NO_EXECUTE
LIVE_AUTHORIZED=false
GENERAL_LIVE_UNLOCKED=false
FUNDING_EXECUTED=false
CANARY_EXECUTED=false
TRADING_POSTS=0
PERSISTENCE_REMEDIATION_PR_MERGED=true
PERSISTENCE_REMEDIATION_STATUS=MERGED_CLOSED
TRACKER_RETIREMENT_ALLOWED=true
TRACKER_DELETED_FROM_HEAD=false
TRACKER_RETIREMENT_DECISION=RETAIN_RETIRED_CLOSED_NONAUTHORITATIVE
```

This tracker has **no** semantic authority. Canonical truth remains
[`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../canonical/PEAK_TRADE_MASTER_RUNBOOK.md)
§11.13.5.M. Temporary &#47; forensic &#47; chat artefacts remain
`AUTHORITY=NONE`.

PR `#5906` squash-merged the post-K GET bind onto `origin&#47;main` at
`bc59e1e331588ab7e727c6909baa69e8a00d93da` (parent
`2caad4a2e68b89c788bb5a5b654a4f32fdba38c5`; frozen feature-head
`cb0779ab77cd1784edba848436891af0a6ccada8`; frozen diff
`73f3845fcc9816df8aa8d017e8a9baf82807a629be1f83800d99b2cda44ac0bc`).
The L-era pointer `OWNER_MERGE_GO_FOR_POST_K_PERSISTENCE_REMEDIATION_PR`
is `CONSUMED_CLOSED`. This closeout does **not** authorize funding or
execute.

## Semantic split (never merge)

| Lane | Meaning | Canonical status |
|---|---|---|
| A `FUTURES_FUNDING_ECONOMICS` (I44 &#47; Master G16) | Funding-rate &#47; payment &#47; accounting claims | `INSUFFICIENT_EVIDENCE` — not in this GO |
| B `CANARY_CAPITAL_FUNDING` | Later separately authorized USDC capital for 1-contract canary | required, **not executed**, **amount unproven** |

Do **not** persist the unproven working claim
`FUNDING_AMOUNT_PROVEN=true` or any operational &#47; recommended funding
amount derived from snapshot theoretical initial margin.

```text
MINIMUM_THEORETICAL_INITIAL_MARGIN_PROVEN=true
SNAPSHOT_THEORETICAL_FUNDING_FLOOR_PROVEN=true
CANARY_OPERATIONAL_MINIMUM_PROVEN=false
RECOMMENDED_BOUNDED_CANARY_FUNDING_AMOUNT_PROVEN=false
FUNDING_AMOUNT_PROVEN=false
NEW_FUNDING_GO_REQUIRED=true
NEW_EXECUTE_GO_REQUIRED=true
FUNDING_GO_AND_EXECUTE_GO_COLLAPSED=false
FUNDING_AUTHORIZED_BY_THIS_CLOSEOUT=false
EXECUTE_AUTHORIZED_BY_THIS_CLOSEOUT=false
```

## Items

| ID | Domain | Proven fact persisted | Status | Canonical target |
|---|---|---|---|---|
| GAP-01 | LEVERAGE_POLICY | GET `SET_ACCOUNT_LEVERAGE=3` for `BTC-USD_UM_XPERP-310404` `mgnMode=cross` `posSide=net` | `CLOSED_CANONICALLY_PERSISTED` | Master §11.13.5.L + derived GET pack |
| GAP-02 | CANARY_CAPITAL_FUNDING | Snapshot theoretical IM `2.101456666666666666666666667` USDC at `markPx=63043.7` | `CLOSED_CANONICALLY_PERSISTED` | same pack as **snapshot floor only** |
| GAP-03 | CROSS_MARGIN_BINDINGS | GET-proven cross leverage **setting**; live POST remains unproven | `CLOSED_CANONICALLY_PERSISTED` | economic-baseline contract + §L |
| GAP-04 | GOVERNANCE | PR `#5905` merge consumed at `2caad4a2e68b89c788bb5a5b654a4f32fdba38c5`; remaining product chain is separate funding GO then separate execute GO | `CLOSED_CANONICALLY_PERSISTED` | §K historical pointer superseded by §L; L merge GO consumed by `#5906` |
| GAP-05 | CANARY_INSTRUMENT_BINDING | Sealed post-K GET identity refresh (live, USDC account settle, `minSz=1`, `totalEq=0`, orders=0) | `CLOSED_CANONICALLY_PERSISTED` | `evidence&#47;ops&#47;section_11_13_5_post_k_cross_imr_leverage_get_bind_v1&#47;20260816T033800Z&#47;` |

No tracker item exists for an operational canary funding minimum: that
quantity is **unproven**, not an undocumented proven fact.

## Classification notes (non-authoritative)

- Public instruments `lever=50` remains `MAX_ALLOWED` &#47; instrument &#47; tier
  limit, **not** set account leverage.
- Account&#47;instruments `lever=10` remains `UNKNOWN` and
  `NOT_ON_SUBMIT_PATH`.
- Public `settleCcy=USD` vs account `settleCcy=USDC`: account truth stays
  USDC.
- Fee GET `takerUSDC=-0.0005` &#47; `makerUSDC=-0.0002` is OKX rebate
  convention and is **not** added as a positive reserve policy.
- Demo Map binding `CANONICAL_ACTIVE_INSTRUMENT=BTC-USD_UM_XPERP-310328`
  is **not** retargeted.

## Retirement

All GAP items are `CLOSED_CANONICALLY_PERSISTED` by squash-merge
`#5906`. This file is `RETIRED_CLOSED_NONAUTHORITATIVE` and is
**retained** on HEAD for audit. It is **not** deleted: the original
delete-after-closeout-on-`origin&#47;main` rule is not satisfied at
closeout authoring time, and historical pointer chains still name this
path. Canonical authority remains SSOT §11.13.5.W. The V-era pointer
`OWNER_GO_REQUIRED_FOR_BOUNDED_GET_ONLY_FRESH_XPERP_TRADE_FEE_EVIDENCE_USING_RATIFIED_QUERY_GRAMMAR`
is consumed as GET-only and superseded by the persisted fresh XPerp
trade-fee GET evidence. Raw numeric reserve terms remain unauthorized
as a funding amount. Fresh theoretical IM is not an operational
funding amount.

```text
CANONICAL_NEXT_STEP=OWNER_GO_REQUIRED_TO_RATIFY_INSTRUMENT_RELEVANT_XPERP_DELIVERY_FEE_ALGEBRA
EARLIEST_UNRESOLVED_DEPENDENCY=CANARY_OPERATIONAL_MINIMUM_UNPROVEN_THEN_SEPARATE_NEW_EXECUTE_GO
PERSISTENCE_REMEDIATION_PR_MERGED=true
TRACKER_RETIREMENT_ALLOWED=true
TRACKER_DELETED_FROM_HEAD=false
HARD_STOP_BEFORE_MERGE=CONSUMED_PR_5906_SQUASH_MERGED
HARD_STOP_BEFORE_FUNDING=true
HARD_STOP_BEFORE_EXECUTE=true
FUNDING_AMOUNT_PROVEN=false
CANARY_OPERATIONAL_MINIMUM_PROVEN=false
RECOMMENDED_BOUNDED_CANARY_FUNDING_AMOUNT_PROVEN=false
```
