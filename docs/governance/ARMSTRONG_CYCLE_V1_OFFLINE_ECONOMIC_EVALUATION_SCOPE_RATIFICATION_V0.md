# Armstrong Cycle v1 — Offline Economic Evaluation Scope Ratification v0

---
docs_token: DOCS_TOKEN_ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Ratifiziert ausschließlich die versionierte offline-only STEP29M-Bindings für `armstrong_cycle&#47;v1` nach post-el_karoui-Distinct-Scope-Definition. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `BINDINGS_MATERIALIZED_NOT_EVALUATED` |
| `SCOPE_ID` | `ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0` |
| `STRATEGY_ID` | `armstrong_cycle` |
| `STRATEGY_VERSION` | `v1` |
| `HYPOTHESIS_ID` | `ARMSTRONG_ECM_MACRO_CALENDAR_CYCLE_PHASE_NON_BITCOIN_FUTURES_V1` |
| `SIGNAL_FAMILY` | `MACRO_CALENDAR_ECM_CYCLE_PHASE` |
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
| Strategy owner | `src/strategies/armstrong/armstrong_cycle_strategy.py` (unchanged) |
| Cycle model owner | `src/strategies/armstrong/cycle_model.py` (unchanged) |
| External parameter schema + warmup | `src/backtest/strategy_signal_binding_v1.py` |
| STEP29M admissibility contract | `src/backtest/step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1.py` |
| Ops evaluation config | `config/ops/step29m_okx_inst_eth_usdt_perp_armstrong_cycle_v1_economic_evaluation_v1.json` |
| Material-difference contract | `config/research/armstrong_cycle_v1_material_difference_and_non_claim_contract_v0.json` |
| Versioned research binding | `config/research/armstrong_cycle_v1_versioned_research_binding_v0.json` |
| Scope ratification config | `config/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.json` |

## C. Ratified Parameter Binding

| Parameter | Class | Bound Value | Notes |
|---|---|---|---|
| `cycle_length_days` | C | `3141` | ECM calendar cycle length |
| `event_window_days` | C | `90` | turning-point event window |
| `reference_date` | C | `2015-10-01` | ECM reference peak date |
| `phase_position_map` | C | `default` | ECM phase → position mapping |
| `use_risk_scaling` | D | excluded | fixed false in signal semantics binding |
| `underlying` | D | excluded | not bound in minimal baseline slice |

## D. Calendar Binding

| Dimension | Binding |
|---|---|
| Timezone | `UTC` |
| Calendar origin | `2015-10-01` |
| Epoch rules | `ECM_REFERENCE_PEAK_DATE_CALENDAR_DAY_COUNT_MOD_CYCLE_LENGTH_UTC_MIDNIGHT` |
| Phase state machine | `ECM_PHASE_STATE_MACHINE_V1` |
| Phases | `CRISIS`, `EXPANSION`, `CONTRACTION`, `PRE_CRISIS`, `POST_CRISIS` |
| Warmup rows | `0` (calendar domain) |
| Signal semantics | `LONG_FLAT_0_1` with ECM phase mapping |

## E. Dataset, Instrument, Cost, Period

| Dimension | Binding |
|---|---|
| Instrument | `inst-eth-usdt-perp` / `ETH-USDT-SWAP` / `OKX` |
| Dataset | `inst-eth-usdt-perp_v1` admissible futures parquet |
| Roundtrip cost | `40 bps` (`10 fee + 5 slippage + 5 half-spread` per side) |
| Training | `2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00` |
| Validation | `2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00` |
| OOS | `2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00` |

## F. Material Difference and Prior Evidence Exclusion

Material difference confirmed against:

- `ehlers_cycle_filter&#47;v1` (terminal inconclusive — DSP cycle bandpass)
- `el_karoui_vol_model&#47;v1` (terminal inconclusive — stochastic vol regime)
- `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0`
- `vol_breakout&#47;v1`
- STEP29M final research fleet v0
- Cross-sectional funding-rate research fleet COMPLETE_NO_PASS surfaces

Source evidence:

`/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_post_el_karoui_inconclusive_read_only_v0_20260710T151847Z`

## G. Canonical Operator Invocation (Baseline Evaluation)

Separate operator GO required. Do not call bare `python` on PATH; use the repo-local adapter:

```bash
export GO_TOKEN="<ALLOWED_CONFIRM_GO_TOKEN>"
scripts/ops/invoke_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0.sh
```

Equivalent explicit form:

```bash
export GO_TOKEN="<ALLOWED_CONFIRM_GO_TOKEN>"
/Users/frnkhrz/Peak_Trade/.venv/bin/python \
  scripts/ops/invoke_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0.py
```

The adapter resolves `${REPO}&#47;.venv&#47;bin&#47;python`, fail-closes when the interpreter or `GO_TOKEN` is missing, and forwards `--confirm-go-token "$GO_TOKEN"` exactly once to `scripts&#47;ops&#47;run_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0.py`.

## H. Next Step

`ARMSTRONG_CYCLE_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0` — separate operator GO required:

`GO_ARMSTRONG_CYCLE_V1_BOUNDED_OFFLINE_ECONOMIC_BASELINE_EVALUATION_NO_RUNTIME_AUTHORITY_V0`

Not authorized in this slice.
