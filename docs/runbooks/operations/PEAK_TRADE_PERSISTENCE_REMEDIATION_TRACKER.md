# Peak_Trade — Persistence Remediation Tracker

```text
AUTHORITY=NONE
DOCUMENT_ROLE=TRACKED_NONAUTHORITATIVE_REMEDIATION_TRACKER
LIFECYCLE=DELETE_FROM_HEAD_AFTER_ALL_ITEMS_CLOSED_AND_CANONICAL_CLOSEOUT_PERSISTED
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
BASELINE_ORIGIN_MAIN_SHA=2caad4a2e68b89c788bb5a5b654a4f32fdba38c5
CREATED_FOR=SECTION_11_13_5_POST_K_PERSISTENCE_REMEDIATION
OWNER_GO=BOUNDED_PERSISTENCE_REMEDIATION_PREPARATION_TRACKER_AND_POST_K_CANONICAL_BIND_NO_FUNDING_NO_EXECUTE
LIVE_AUTHORIZED=false
GENERAL_LIVE_UNLOCKED=false
FUNDING_EXECUTED=false
CANARY_EXECUTED=false
TRADING_POSTS=0
```

This tracker has **no** semantic authority. Canonical truth remains
[`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../canonical/PEAK_TRADE_MASTER_RUNBOOK.md).
Temporary &#47; forensic &#47; chat artefacts remain `AUTHORITY=NONE`.

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
```

## Items

| ID | Domain | Proven fact to persist | Status on this branch | Canonical target |
|---|---|---|---|---|
| GAP-01 | LEVERAGE_POLICY | GET `SET_ACCOUNT_LEVERAGE=3` for `BTC-USD_UM_XPERP-310404` `mgnMode=cross` `posSide=net` | `CLOSED_IN_BRANCH_PENDING_OWNER_MERGE_GO` | Master §11.13.5.L + derived GET pack |
| GAP-02 | CANARY_CAPITAL_FUNDING | Snapshot theoretical IM `2.101456666666666666666666667` USDC at `markPx=63043.7` | `CLOSED_IN_BRANCH_PENDING_OWNER_MERGE_GO` | same pack as **snapshot floor only** |
| GAP-03 | CROSS_MARGIN_BINDINGS | GET-proven cross leverage **setting**; live POST remains unproven | `CLOSED_IN_BRANCH_PENDING_OWNER_MERGE_GO` | economic-baseline contract + §L |
| GAP-04 | GOVERNANCE | PR `#5905` merge consumed at `2caad4a2e68b89c788bb5a5b654a4f32fdba38c5`; remaining product chain is separate funding GO then separate execute GO | `CLOSED_IN_BRANCH_PENDING_OWNER_MERGE_GO` | §K historical pointer superseded by §L |
| GAP-05 | CANARY_INSTRUMENT_BINDING | Sealed post-K GET identity refresh (live, USDC account settle, `minSz=1`, `totalEq=0`, orders=0) | `CLOSED_IN_BRANCH_PENDING_OWNER_MERGE_GO` | `evidence&#47;ops&#47;section_11_13_5_post_k_cross_imr_leverage_get_bind_v1&#47;20260816T033800Z&#47;` |

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

## Closeout rule

Delete this tracker from HEAD only after every item is closed **and**
the canonical §11.13.5.L closeout is persisted on `origin&#47;main`. Until
then this file remains tracked, non-authoritative hygiene.

```text
CANONICAL_NEXT_STEP=OWNER_MERGE_GO_FOR_POST_K_PERSISTENCE_REMEDIATION_PR
EARLIEST_UNRESOLVED_DEPENDENCY=OWNER_MERGE_GO_THEN_SEPARATE_NEW_FUNDING_GO_THEN_SEPARATE_NEW_EXECUTE_GO
HARD_STOP_BEFORE_MERGE=true
HARD_STOP_BEFORE_FUNDING=true
HARD_STOP_BEFORE_EXECUTE=true
```
