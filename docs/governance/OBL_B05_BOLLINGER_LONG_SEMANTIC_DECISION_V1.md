# OBL_B05 Bollinger Long-Semantic Decision + Quantitative Baseline v1

---
docs_token: DOCS_TOKEN_OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_V1
STATUS: BOLLINGER_LONG_SEMANTIC_DECISION_COMPLETE
scope: decision + quantitative event baseline; non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
BOLLINGER_LONG_SEMANTIC_DECISION_COMPLETE: true
BOLLINGER_DECISION: CONTRACT_REMAINS_AMBIGUOUS
BOLLINGER_QUANTITATIVE_BASELINE_COMPLETE: true
BOLLINGER_SIDE_ACTIVATED: false
BOLLINGER_SHORT_EMISSION: false
OTHER_PRODUCER_SIDE_EMISSION_CHANGED: false
PRODUCTIVE_SEMANTICS_CHANGED: false
---

> Decision&#47;Evidence-Slice only. No productive `entry_side` activation.
> Bollinger `-1` remains EXIT (never SHORT). MACD and other producers unchanged.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_AND_QUANTITATIVE_BASELINE_V1` |
| `BASE_SHA` | `8ed59484959504e7d477dc9e8d4adedd2ec022b0` |
| `PR_5319_MERGE_SHA` | `8ed59484959504e7d477dc9e8d4adedd2ec022b0` |
| `BOLLINGER_DECISION` | `CONTRACT_REMAINS_AMBIGUOUS` |
| `BOLLINGER_SIDE_ACTIVATED` | `false` |
| `BOLLINGER_SHORT_EMISSION` | `false` |
| `PRODUCTIVE_SEMANTICS_CHANGED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `SSOT_JSON` | `config&#47;governance&#47;obl_b05_bollinger_long_semantic_decision_v1.json` |

## B. Decision (Variant C)

Chosen exclusively: **C — `CONTRACT_REMAINS_AMBIGUOUS`**.

| Variant | Result | Why |
|---|---|---|
| A `LONG_ONLY_ENTRY_EXIT` | rejected | Class doc `1 (long)` vs method `1=entry`; Decision D ENTRY≠LONG; adapter keeps `entry_side=NONE`; parent SSOT `BLOCKED_AMBIGUITY` |
| B `SIDE_NEUTRAL_ENTRY_EXIT` | rejected | Consumer path is event-neutral, but producer package is not ratified as `EVENT_ONLY_NO_SIDE_AUTHORITY` (class remains `AMBIGUOUS_OR_CONTRADICTORY`) |
| C `CONTRACT_REMAINS_AMBIGUOUS` | **selected** | Matches parent audit; contradictions unresolved |

Unresolved contradictions (must stay explicit):

1. `CP02` — class doc `1 (long)` vs method return `1=entry`
2. `CP01` — `BaseStrategy` ±1 long&#47;short position vocab vs ENTRY&#47;EXIT encoding
3. `CP03` — registry `supported_sides=(long,short)` vs long-only geometry
4. Decision D — `+1` is ENTRY, never LONG authority
5. Adapter — Bollinger `entry_side` forced `NONE`
6. Parent SSOT — `bollinger_entry_side_decision=BLOCKED_AMBIGUITY`

`-1` is productive EXIT (middle-band cross), never SHORT.

## C. Quantitative baseline (canonical panel)

Identical durable archive + bollinger binding as TF impact diagnostic &#47; full-canonical economic panel:

- archive: full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z
- binding: `config&#47;research&#47;bollinger_bands_v2_full_canonical_system_economic_binding_v1.json`
- panel members: 118
- total bars: 348454

### Bollinger events

| Metric | Panel | Eval (1INCH) |
|---|---:|---:|
| total bars | 348454 | 2953 |
| ENTRY (`+1`) | 185 | 1 |
| EXIT (`-1`) | 20754 | 168 |
| neutral (`0`) | 327515 | 2784 |
| `entry_side` LONG | 0 | 0 |
| `entry_side` SHORT | 0 | 0 |
| `entry_side` NONE | 185 | 1 |
| agreement | unresolved×185 | unresolved×1 |
| first_failed_stage | directional_agreement×185 | directional_agreement×1 |
| ENTER&#47;HOLD&#47;EXIT outcomes | 0 | 0 |

### SHORT reference (`rsi_reversion`, POSITIONAL_LS)

Same bars&#47;panel; documented strategy overlay (not Bollinger).

| Metric | Panel |
|---|---:|
| SHORT entries (`-1` positional) | 53870 |
| LONG entries (`+1` positional) | 64110 |

Contrast rule: Bollinger `-1` = EXIT event; RSI `-1` = SHORT entry. Methodologically comparable only as same-scope event counts under explicit encoding difference.

## D. Comparison (SHORT vs Bollinger&#47;LONG-candidate)

| Field | Bollinger ENTRY_EXIT | RSI POSITIONAL_LS SHORT ref |
|---|---|---|
| Scope | identical panel bars | identical panel bars |
| Entry count | 185 (`+1` ENTRY) | 53870 (`-1` SHORT) |
| Side resolved | 0 (all NONE) | cycle carrier (±1) |
| Agreement | blocked×185 | LONG path reaches later stages on `+1` |
| Composition | not reached for Bollinger ENTRY | observe&#47;selected on RSI `+1` |
| ENTER&#47;HOLD | 0 &#47; 0 | present on RSI `+1` MV2 path |

## E. Next steps (no repair in this slice)

- No productive Bollinger side emission
- Next dominant blocker for Bollinger ENTRY: `directional_agreement` (entry_side=NONE)
- Future activation only after doc-alignment GO:
  `OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1`

## F. Owners &#47; navigation

| Surface | Owner |
|---|---|
| SSOT JSON | `config&#47;governance&#47;obl_b05_bollinger_long_semantic_decision_v1.json` |
| Governance narrative | this document |
| Baseline runner | `scripts&#47;ops&#47;run_obl_b05_bollinger_long_semantic_decision_baseline_v1.py` |
| Tests | `tests&#47;backtest&#47;test_obl_b05_bollinger_long_semantic_decision_v1.py` |
| Parent authority audit | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md` |
| TF impact diagnostic | `docs&#47;governance&#47;OBL_B05_TREND_FOLLOWING_SIDE_IMPACT_DIAGNOSTIC_V1.md` |
| Evidence pointer | `docs&#47;product&#47;evidence&#47;obl_b05_bollinger_long_semantic_decision_v1_20260717T231700Z&#47;` |
