# El Karoui Vol Model v1 — Offline Economic Evaluation Scope Ratification v0

---
docs_token: DOCS_TOKEN_EL_KAROUI_VOL_MODEL_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only STEP29M-Bindings für `el_karoui_vol_model/v1` nach PR-#5087-Distinct-Scope-Definition. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `SCOPE_ID` | `EL_KAROUI_VOL_MODEL_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0` |
| `STRATEGY_ID` | `el_karoui_vol_model` |
| `STRATEGY_VERSION` | `v1` |
| `HYPOTHESIS_ID` | `EL_KAROUI_STOCHASTIC_VOL_REGIME_NON_BITCOIN_FUTURES_V1` |
| `SIGNAL_FAMILY` | `STOCHASTIC_VOL_REGIME` |
| `FUTURES_ONLY` | `true` |
| `BITCOIN_PRESENT` | `false` |
| `BITCOIN_DIRECTION_ALLOWED` | `false` |
| `TRADING_LOGIC_MUTATED` | `false` |
| `PARAMETER_SEARCH_ALLOWED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `RUNTIME_EFFECT` | `NONE` |

## B. Materialized Bindings

| Surface | Owner / Path |
|---|---|
| Strategy owner | `src/strategies/el_karoui/el_karoui_vol_model_strategy.py` (unchanged) |
| External parameter schema + warmup | `src/backtest/strategy_signal_binding_v1.py` |
| STEP29M admissibility contract | `src/backtest/step29m_el_karoui_vol_model_v1_economic_evaluation_admissibility_contract_v1.py` |
| Ops evaluation config | `config/ops/step29m_okx_inst_eth_usdt_perp_el_karoui_vol_model_v1_economic_evaluation_v1.json` |
| Material-difference contract | `config/research/el_karoui_vol_model_v1_material_difference_and_non_claim_contract_v0.json` |
| Versioned research binding | `config/research/el_karoui_vol_model_v1_versioned_research_binding_v0.json` |
| Scope ratification config | `config/research/el_karoui_vol_model_v1_offline_economic_evaluation_scope_ratification_v0.json` |

## C. Ratified Parameter Binding

| Parameter | Class | Bound Value | Notes |
|---|---|---|---|
| `vol_window` | C | `20` | consumed for realized-vol estimation |
| `lookback_window` | C | `252` | consumed for percentile regime classification |
| `low_threshold` | C | `0.30` | LOW-regime percentile bound |
| `high_threshold` | C | `0.70` | HIGH-regime percentile bound |
| `vol_target` | D | excluded | not bound in minimal baseline slice |
| `use_ewm` | D | excluded | fixed true in signal semantics binding |
| `use_vol_scaling` | D | excluded | fixed false in baseline slice |
| `annualization_factor` | D | excluded | declared but not bound |
| `regime_position_map` | D | excluded | fixed `default` in signal semantics binding |

## D. Dataset, Instrument, Cost, Period

| Dimension | Binding |
|---|---|
| Instrument | `inst-eth-usdt-perp` / `ETH-USDT-SWAP` / `OKX` |
| Dataset | `inst-eth-usdt-perp_v1` admissible futures parquet |
| Roundtrip cost | `40 bps` (`10 fee + 5 slippage + 5 half-spread` per side) |
| Training | `2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00` |
| Validation | `2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00` |
| OOS | `2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00` |
| Warmup rows | `252` |
| Signal semantics | `LONG_FLAT_0_1` |

## E. Material Difference and Prior Evidence Exclusion

Material difference confirmed against:

- `ehlers_cycle_filter/v1` (terminal inconclusive source scope)
- `cross_sectional_ma_crossover_panel_rank_rotation/v0`
- `vol_breakout/v1`
- STEP29M final research fleet v0
- Cross-sectional funding-rate research fleet COMPLETE_NO_PASS surfaces

Source evidence:

- PR #5087 closeout bundle (MANIFEST_VERIFY_RC=0)
- Ehlers terminal inconclusive distinct-scope definition bundle (MANIFEST_VERIFY_RC=0)

## F. Next Step

`EL_KAROUI_VOL_MODEL_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0` — separate operator GO required:

`GO_EL_KAROUI_VOL_MODEL_V1_BOUNDED_OFFLINE_ECONOMIC_BASELINE_EVALUATION_NO_RUNTIME_AUTHORITY_V0`

Not authorized in this slice.
