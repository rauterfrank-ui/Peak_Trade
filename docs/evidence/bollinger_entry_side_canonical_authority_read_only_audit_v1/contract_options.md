# Contract Options A–D

## OPTION A — Strategy-owned Side

Bollinger emits LONG&#47;SHORT directly.

| Criterion | Assessment |
|-----------|------------|
| Authority risk | **HIGH** — second truth vs Master V2 Bull&#47;Bear |
| Dynamic Scope &#47; DP compatibility | Poor — strategy would invent system direction |
| Fail-closed | Weak unless heavily gated |
| Backtest&#47;Runtime parity | Would align Classic LONG folklore; break OBL_B07 |
| Productive changes | Adapter + producer docs + side activation |
| Test effort | High (LONG&#47;SHORT&#47;conflict&#47;parity) |
| Recommendation | **REJECT** (not authorized; contradicts EVENT_ONLY) |

## OPTION B — Canonical Composition

Bollinger emits Signal&#47;Intent; a Master-V2-&#47;DP-aware composer produces LONG&#47;SHORT&#47;NONE.

| Criterion | Assessment |
|-----------|------------|
| Authority risk | **LOW–MEDIUM** if composer is sole owner and never projects DP→`entry_side` circularly |
| DP compatibility | Best long-term fit (Strategy Intent ∧ DP Agreement) |
| Fail-closed | Strong if missing Intent or conflict → NONE |
| Parity | Requires explicit Classic non-canonical boundary |
| Productive changes | New composer contract + wiring; Intent schema |
| Test effort | High |
| Recommendation | **DEFER** — needs separate Operator-GO + design slice |

## OPTION C — State-only Side

Master V2 &#47; DP fully owns Side; Bollinger is only Entry-Permission&#47;Timing.

| Criterion | Assessment |
|-----------|------------|
| Authority risk | Medium — side without strategy intent can ignore mean-reversion geometry |
| DP compatibility | High for state purity; weak for strategy meaning |
| Fail-closed | Possible |
| Parity | Classic LONG still mismatched |
| Productive changes | Composition consumes permission bit only |
| Test effort | Medium |
| Recommendation | **REJECT for now** — collapses Intent into State |

## OPTION D — Remain NONE

No Side activation until a separate Contract is implemented and ratified.

| Criterion | Assessment |
|-----------|------------|
| Authority risk | **LOWEST** |
| DP compatibility | Preserved |
| Fail-closed | Current law (`ENTRY_SIDE=NONE`, no directional cycle) |
| Parity | Classic LONG remains non-canonical (documented) |
| Productive changes | None |
| Test effort | None (already locked by OBL_B07) |
| Recommendation | **ACCEPT** |

```text
RECOMMENDED_CONTRACT=OPTION_D
```
