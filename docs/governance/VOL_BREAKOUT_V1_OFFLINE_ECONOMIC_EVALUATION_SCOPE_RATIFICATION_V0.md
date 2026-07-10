# Vol Breakout v1 — Offline Economic Evaluation Scope Ratification v0

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only STEP29M-Bindings für `vol_breakout&#47;v1` nach rank-1-Research-Ratifikation. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `SCOPE_ID` | `VOL_BREAKOUT_V1_NARROW_NEUTRAL_REWIRE_AND_BINDING_IMPLEMENTATION_V0` |
| `STRATEGY_ID` | `vol_breakout` |
| `STRATEGY_VERSION` | `v1` |
| `HYPOTHESIS_ID` | `VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `TRADING_LOGIC_MUTATED` | `false` |
| `ATR_MULTIPLE_BOUND` | `false` |
| `PARAMETER_SEARCH_ALLOWED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `RUNTIME_EFFECT` | `NONE` |

## B. Materialized Bindings

| Surface | Owner / Path |
|---|---|
| Strategy owner | `src/strategies/vol_breakout.py` (unchanged) |
| External parameter schema + warmup | `src/backtest/strategy_signal_binding_v1.py` |
| STEP29M admissibility contract | `src/backtest/step29m_vol_breakout_v1_economic_evaluation_admissibility_contract_v1.py` |
| Ops evaluation config | `config/ops/step29m_okx_inst_eth_usdt_perp_vol_breakout_v1_economic_evaluation_v1.json` |
| Versioned research binding | `config/research/vol_breakout_v1_versioned_research_binding_v0.json` |
| Scope ratification config | `config/research/vol_breakout_v1_offline_economic_evaluation_scope_ratification_v0.json` |

## C. Ratified Parameter Binding

| Parameter | Class | Bound Value | Notes |
|---|---|---|---|
| `lookback_breakout` | C | `20` | consumed |
| `vol_window` | C | `14` | consumed |
| `vol_percentile` | C | `50.0` | consumed |
| `side` | B | `both` | frozen symmetric futures baseline |
| `atr_multiple` | D | excluded | declared but not consumed |

## D. Dataset, Instrument, Cost, Period

| Dimension | Binding |
|---|---|
| Instrument | `inst-eth-usdt-perp` / `ETH-USDT-SWAP` / `OKX` |
| Dataset | `inst-eth-usdt-perp_v1` admissible futures parquet |
| Roundtrip cost | `40 bps` (`10 fee + 5 slippage + 5 half-spread` per side) |
| Training | `2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00` |
| Validation | `2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00` |
| OOS | `2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00` |
| Warmup rows | `40` |

## E. Source Evidence

- Rank-1 ratification bundle: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/rank1_vol_breakout_binding_and_evaluation_ratification_read_only_v0_20260710T063915Z`
- PR5072 terminal-negative closeout: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5072_merge_closeout_20260710T063107Z`

## F. Next Step

`VOL_BREAKOUT_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0` — separate operator GO required; not authorized in this slice.
