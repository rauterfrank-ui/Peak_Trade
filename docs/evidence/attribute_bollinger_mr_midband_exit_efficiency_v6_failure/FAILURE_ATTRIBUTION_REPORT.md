---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_V6_FAILURE_ATTRIBUTION
STATUS: EVIDENCE_ONLY_FAILURE_ATTRIBUTION_COMPLETE
scope: research, offline-only, non-authorizing, read-only attribution
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

# Bollinger&#47;MR midband exit-efficiency V6 — failure attribution (evidence-only)

> **Non-authorizing.** Read-only attribution from committed V6 artifacts only.
> No new evaluation. No raw development panel access. No holdout access.
> V6 remains terminal `FAIL` with run count `1`. Attribution does **not** authorize
> promotion, runtime, or V7 execution&#47;preregistration.

## Binding

- Source hypothesis: `BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6`
- Origin&#47;main: `98aede46fcecc7dffb5b515f4bd87b06fd2eecb7`
- Source preregistration digest: `9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5`
- Source result digest (evaluate summary sha256): `608b1ff80333ffdb3f79566b419e57f3aeb2ac51b4edb98071b571e834bf4330`
- Source evidence: `docs&#47;evidence&#47;evaluate_bollinger_mr_midband_exit_efficiency_development_v6&#47;`
- Attribution evidence: `docs&#47;evidence&#47;attribute_bollinger_mr_midband_exit_efficiency_v6_failure&#47;`

## Safety attestations

| Flag | Value |
|---|---|
| `EVALUATION_RUNNER_EXECUTED` | `false` |
| `BACKTEST_OR_REPLAY_EXECUTED` | `false` |
| `RAW_DEVELOPMENT_PANEL_ACCESSED` | `false` |
| `HOLDOUT_DATA_ACCESSED` | `false` |
| `SOURCE_ARTIFACTS_MUTATED` | `false` |
| `V6_TERMINAL_CLASSIFICATION` | `FAIL` |
| `SOURCE_RUN_COUNT` | `1` |
| `V7_PREREGISTRATION_CREATED` | `false` |

## Totals reconciliation

| Quantity | Value |
|---|---:|
| Baseline trades | 109 |
| Treatment trades | 566 |
| Forced exits | 326 |
| Midband exit count | 318 |
| Max-hold exit count | 10 |
| Dual-trigger overlap (`midband_and_max_holding`) | 2 |
| Treatment ledger `signal` exits | 320 |
| Forced-vs-signal gap | 6 |

Precedence: composite policy is first-of midband-cross OR max-holding. When both fire on the same bar, subtype counters both increment while `exits_forced_by_gate` increments once (`318 + 10 - 326 = 2`).

Ledger mapping: forced gate overrides appear primarily as `exit_reason=signal`. Exact bar-invocation vs trade-close equality is **INCONCLUSIVE** (gap `6`).

## Why trade count rose 109 → 566

**Label:** `EARLIER_EXIT_FOLLOWED_BY_REENTRY_CHURN` (**SUPPORTED**).

- Shared entry keys: 108 &#47; baseline 109
- Earlier treatment exits among shared entries: 66
- Treatment-only entries: 458 (all short)
- Long trade count unchanged (21→21); short 88→545 (+457)

Not explained as purely new independent entry signals. Baseline-only missing entry keys: 1.

## Degradation decomposition (treatment − baseline)

| Channel | Delta |
|---|---:|
| Gross PnL | 1506.091230 |
| Fees | 1851.128130 |
| Slippage | 925.564065 |
| Cost drag | 2776.692196 |
| Net PnL | -1270.600965 |
| Net return | -0.002049119160 |
| Net profit factor | -0.103473955702 |
| Long net PnL | 620.285736 |
| Short net PnL | -1890.886701 |

**Primary degradation channel:** cost drag from short-side re-entry churn after forced midband exits (**PROVEN** cost dominance; **SUPPORTED** churn linkage).

### Separated loss channels

1. **Direct midband&#47;signal truncation of baseline winners (PROVEN on shared path):** 11 `end_of_data→signal` pairs, net delta `-4754.4240`.
2. **Offsetting midband rescues before stop (PROVEN):** 55 `stop_loss→signal` pairs, net delta `4822.0936`.
3. **Downstream re-entry churn (SUPPORTED):** T-only net `-1369.4192`, T-only cost `2773.5392`.
4. **Max-hold effects (SUPPORTED not material as loss):** proxy n=10, net `1457.4271` (positive).
5. **Cost drag (PROVEN):** cost delta `2776.6922` exceeds gross gain `1506.0912`.
6. **Signal-quality&#47;regime buckets:** **NOT_OBSERVABLE** in committed artifacts.

### Expectancy &#47; holding

- Baseline expectancy net `1.362854`, win rate `0.1009`, avg winner `506.1706`, avg loser `-55.2992`
- Treatment expectancy net `-1.982420`, win rate `0.4099`, avg winner `58.7483`, avg loser `-44.1667`
- Mean hold hours: 230.606 → 11.733

## Concentration

Top loss-contributing instruments (net PnL delta):

| Instrument | Net delta | Trade-count delta |
|---|---:|---:|
| APE | -1294.3602 | 52 |
| ENS | -785.0565 | 38 |
| MANA | -622.1046 | 32 |
| LUNA | -543.3363 | 41 |
| EGLD | -456.3878 | 17 |

- Instruments worse&#47;better&#47;unchanged: 11 &#47; 19 &#47; 3
- Worst-5 sum &#47; total net delta: -3701.2455 &#47; -1270.6010
- Pattern: **MIXED** — broad short-side churn plus concentrated instrument losses (not single-name only).

## Earliest causal boundary

Supported boundary: **forced exit eligibility → forced midband&#47;max-hold exit → re-entry → ledger&#47;costs → portfolio aggregation**.

Upstream signal&#47;entry formula unchanged between arms by V6 contract; effective divergence begins at the composite exit gate.

## Candidate explanation tests

| Explanation | Strength |
|---|---|
| Midband cuts winners prematurely | SUPPORTED |
| Midband realizes losses before MR completes | INCONCLUSIVE |
| Forced exits create re-entry churn | SUPPORTED |
| Cost drag dominates gross-edge change | PROVEN |
| Short-side dominates degradation | PROVEN |
| Small instrument subset dominates | SUPPORTED |
| Max-hold interaction material | NOT_SUPPORTED (evidence strength SUPPORTED for non-materiality) |

## Claims strength counts

- PROVEN: 6
- SUPPORTED: 5
- INCONCLUSIVE: 1
- NOT_OBSERVABLE: 2

## Bounded V7 candidates (not preregistered)

Ranked by causal support, falsifiability, semantic distinctness, implementation risk, expected churn&#47;cost reduction:

1. **`BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7_CANDIDATE`** — `REENTRY_COOLDOWN_AFTER_FORCED_MIDBAND_EXIT`
2. `BOLLINGER_MR_OPEN_PNL_CONDITIONED_MIDBAND_EXIT_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7_CANDIDATE` — `PROFITABLE_OR_OPEN_PNL_CONDITIONED_MIDBAND_EXIT`
3. `BOLLINGER_MR_MIDBAND_EXIT_AS_ELIGIBILITY_NOT_FORCED_FLAT_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7_CANDIDATE` — `MIDBAND_EXIT_AS_ELIGIBILITY_RATHER_THAN_UNCONDITIONAL_FORCED_EXIT`

See `v7_candidate_ranking.json` for full falsifiable criteria. No candidate is selected for execution in this slice.

## Explicit non-actions

No V6 rerun. No V7 preregistration&#47;auto-create. No holdout. No retuning-as-V6. No economic&#47;promotion gate open. No runtime&#47;orders. No Master-V2 &#47; Double-Play &#47; risk &#47; sizing &#47; execution mutation. No source V6 artifact mutation.
