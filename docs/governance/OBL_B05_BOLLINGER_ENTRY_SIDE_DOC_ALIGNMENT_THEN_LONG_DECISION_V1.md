# OBL_B05 Bollinger Entry-Side Doc Alignment Then Long Decision v1

---
docs_token: DOCS_TOKEN_OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1
STATUS: BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_COMPLETE
scope: governance/docs alignment + open decision brief; non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_COMPLETE: true
BOLLINGER_SIDE_ACTIVATED: false
SIDE_ACTIVATED: false
ENTRY_SIDE_CURRENT: NONE
CONTRACT_STATE: CONTRACT_REMAINS_AMBIGUOUS
LONG_DECISION_MADE_IN_THIS_SLICE: false
PRODUCTIVE_SRC_CHANGED: false
ACTIVE_SSOT_ALIGNED: true
---

> Non-authorizing. Aligns **active** governance SSOTs to the current fail-closed
> law for Bollinger ENTRY. Does **not** activate `entry_side`, does **not**
> mutate productive `src/`, and does **not** choose LONG unilaterally.
> Historical evidence packages are preserved unchanged.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1` |
| `BASE_SHA` | `236a3ed9d39b0346e00662929e911bb44b2095fc` |
| `ENTRY_SIDE_CURRENT` | `NONE` |
| `CONTRACT_STATE` | `CONTRACT_REMAINS_AMBIGUOUS` |
| `BOLLINGER_SIDE_ACTIVATED` | `false` |
| `LONG_DECISION_MADE_IN_THIS_SLICE` | `false` |
| `PRODUCTIVE_SRC_CHANGED` | `false` |
| `OPEN_DECISION` | `BOLLINGER_ENTRY_SIDE_AUTHORITY_PENDING_SEPARATE_OPERATOR_GO` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `SSOT_JSON` | `config&#47;governance&#47;obl_b05_bollinger_entry_side_doc_alignment_then_long_decision_v1.json` |

## B. Current law (aligned)

1. Bollinger ENTRY has **no authorized side**.
2. `entry_side=NONE` is intentional fail-closed.
3. `cycle_signal_value=+1` alone does **not** authorize LONG.
4. Later LONG (or alternate contract) requires a **separate** explicit Operator-GO.
5. `-1` remains EXIT, never SHORT.

## C. Before &#47; after (contract statement)

| Aspect | Before this slice | After this slice |
|---|---|---|
| Authorized Bollinger ENTRY side | NONE | NONE (unchanged) |
| `+1` ⇒ LONG? | false | false (restated) |
| Active docs next-step wording | pointed at this slice as pending | this slice complete; open authority GO pending |
| Productive `src/` | CP02 present | CP02 still present (untouched) |
| Historical evidence | frozen | preserved, not reinterpreted |

## D. Findings matrix (summary)

Full machine-readable matrix: SSOT JSON `findings_matrix[]`.

| Layer | Action |
|---|---|
| ACTIVE_SSOT | Updated&#47;verified aligned to fail-closed NONE |
| HISTORICAL_EVIDENCE | Preserved; not rewritten |
| PRODUCTIVE_SOURCE | Out of scope; contradictions documented only |
| GENERAL_DEV_GUIDE | Out of scope (generic templates ≠ Bollinger authority) |

## E. Open decision (not decided here)

`OPEN_DECISION=BOLLINGER_ENTRY_SIDE_AUTHORITY_PENDING_SEPARATE_OPERATOR_GO`

| Option | Title | Trade-off (short) |
|---|---|---|
| A | Authorize LONG on ENTRY | Unblocks DA; needs src doc alignment + adapter ratification |
| B | Keep ambiguous &#47; fail-closed NONE | Safest; no ENTER progress |
| C | Extend contract differently | May ratify event-only or alternate side owner; architecture risk |

Operator recommendation recorded in SSOT: do **not** auto-select; prefer B until a dedicated GO chooses A or C.

Candidate follow-on GOs:

- `OBL_B05_BOLLINGER_ENTRY_SIDE_LONG_ACTIVATION_V1`
- `OBL_B05_BOLLINGER_KEEP_FAIL_CLOSED_NONE_RATIFICATION_V1`
- `OBL_B05_BOLLINGER_EVENT_ONLY_NO_SIDE_AUTHORITY_RATIFICATION_V1`

## F. Owners &#47; navigation

| Surface | Owner |
|---|---|
| This slice SSOT | `config&#47;governance&#47;obl_b05_bollinger_entry_side_doc_alignment_then_long_decision_v1.json` |
| This narrative | this document |
| Parent authority | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md` |
| Parent semantic decision | `docs&#47;governance&#47;OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_V1.md` |
| Carrier contract | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1.md` |
| Static tests | `tests&#47;backtest&#47;test_obl_b05_bollinger_entry_side_doc_alignment_v1.py` |
| Evidence pointer | `docs&#47;product&#47;evidence&#47;obl_b05_bollinger_entry_side_doc_alignment_v1_20260717T234000Z&#47;` |
