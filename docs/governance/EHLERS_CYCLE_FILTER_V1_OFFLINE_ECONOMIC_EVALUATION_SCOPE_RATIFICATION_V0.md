# Ehlers Cycle Filter v1 — Offline Economic Evaluation Scope Ratification v0

---
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only STEP29M-Bindings für `ehlers_cycle_filter&#47;v1` nach rank-1-Discovery-Ratifikation. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `SCOPE_ID` | `EHLERS_CYCLE_FILTER_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0` |
| `STRATEGY_ID` | `ehlers_cycle_filter` |
| `STRATEGY_VERSION` | `v1` |
| `HYPOTHESIS_ID` | `EHLERS_DSP_CYCLE_BANDPASS_NON_BITCOIN_FUTURES_V1` |
| `SIGNAL_FAMILY` | `DSP_CYCLE_BANDPASS` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `TRADING_LOGIC_MUTATED` | `false` |
| `PARAMETER_SEARCH_ALLOWED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `RUNTIME_EFFECT` | `NONE` |

## B. Materialized Bindings

| Surface | Owner / Path |
|---|---|
| Strategy owner | `src/strategies/ehlers/ehlers_cycle_filter_strategy.py` (unchanged) |
| External parameter schema + warmup | `src/backtest/strategy_signal_binding_v1.py` |
| STEP29M admissibility contract | `src/backtest/step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1.py` |
| Ops evaluation config | `config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json` |
| Material-difference contract | `config/research/ehlers_cycle_filter_v1_material_difference_and_non_claim_contract_v0.json` |
| Versioned research binding | `config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json` |
| Scope ratification config | `config/research/ehlers_cycle_filter_v1_offline_economic_evaluation_scope_ratification_v0.json` |

## C. Ratified Parameter Binding

| Parameter | Class | Bound Value | Notes |
|---|---|---|---|
| `min_cycle_length` | C | `6` | consumed as Super-Smoother period |
| `lookback` | C | `100` | consumed as minimum history gate and warmup |
| `smoother_type` | D | excluded | declared but not bound in minimal slice |
| `max_cycle_length` | D | excluded | declared but not consumed |
| `cycle_threshold` | D | excluded | declared but not consumed |
| `bandpass_bandwidth` | D | excluded | declared but not consumed |
| `use_hilbert_transform` | D | excluded | declared but not consumed |

## D. Dataset, Instrument, Cost, Period

| Dimension | Binding |
|---|---|
| Instrument | `inst-eth-usdt-perp` / `ETH-USDT-SWAP` / `OKX` |
| Dataset | `inst-eth-usdt-perp_v1` admissible futures parquet |
| Roundtrip cost | `40 bps` (`10 fee + 5 slippage + 5 half-spread` per side) |
| Training | `2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00` |
| Validation | `2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00` |
| OOS | `2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00` |
| Warmup rows | `100` |
| Signal semantics | `LONG_FLAT_0_1` |

## E. Material Difference and Prior Evidence Exclusion

Material difference confirmed against:

- `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0`
- `vol_breakout&#47;v1`
- STEP29M final research fleet v0
- Cross-sectional funding-rate research fleet COMPLETE_NO_PASS surfaces

Source discovery evidence:

`/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_read_only_v0_20260710T104236Z`

## F. Next Step

`EHLERS_CYCLE_FILTER_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0` — separate operator GO required; not authorized in this slice.
