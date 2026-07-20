# Decision matrix — SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1

Repo SHA: `891044056537a4033e6136ba01652a0a2c6e76b7`  
Reference PR: #5349  
Period: `2024-05-01T00:00:00Z..2024-09-01T00:00:00Z`  
Measurement: valid (`ECONOMIC_MEASUREMENT_VALID=true`)  
Gate: closed (`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`)

## 1. Technisch valide

- Cost application `APPLIED` on MV2 legacy-bar path
- Shared-book portfolio aggregation `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`
- Ledger identity gross − fees − slip = net (residual ≈ 0)
- Baseline reproduction matches sealed post-#5349 reference within float tolerance
- Direction authority remains Master V2 / Double Play (`transition_state`); `entry_side=NONE`

## 2. Wirtschaftlich schwach

- Net return ≈ `0.00232538607176469` on shared capital 10000
- Sharpe ≈ `0.1909766065222959`, PF ≈ `1.1135430312470467`, MaxDD ≈ `-0.020480218347394656`
- Cost drag ≈ half of gross edge
- SHORT book net-negative despite trade-count dominance
- Stop-loss exits concentrate almost all losses; rare end-of-data winners carry the book

## 3. Statistisch nicht entscheidbar

- Walk-forward fold signs unstable across 3 windows inside one 4-month PIT
- Stress uses modelled roundtrip bps drag (not full path re-sim)
- Scope / Composition attribution blocked by export DATA_GAP
- Bootstrap P(ret≤0) ≈ `0.961` (diagnostic; not promotion evidence)

## 4. Fehlende Daten

- Longer chronological PIT beyond 2024-05..2024-09
- Per-bar Dynamic Scope / Switch / CHOP context
- CompositionStatus time series
- MAE / MFE path metrics on trades
- Canonical signal-delay / missed-fill / instrument-outage stress runners

## 5. Belegte Hypothesen

- Exit inefficiency (stop-dominated losses vs end-of-data wins) — **CONFIRMED**
- Direction imbalance economically material (LONG+, SHORT−) — **CONFIRMED**
- Cost drag material vs thin gross edge — **CONFIRMED**
- Insufficient PIT period for promotion-grade robustness — **CONFIRMED**

## 6. Widerlegte / nicht gestützte Hypothesen

- Measurement defect as cause of weak economics after #5349 — **NOT_SUPPORTED**
- Need for a second direction authority — **NOT_SUPPORTED** (contract forbids; not observed)

## 7. Zulässige nächste Research-Schritte (ohne Tuning)

- Acquire longer chronological PIT dataset
- Read-only exit attribution deep dive (MAE/MFE if exportable without semantics change)
- Read-only direction-producer attribution (why SHORT count dominates)
- Read-only cost/turnover research on existing fills

## 8. Unzulässiges Tuning (nicht tun)

- Grid / Bayesian / genetic parameter search on bb_period, thresholds, stops, fees
- Changing entry/exit/stop/risk/sizing/composition/switch semantics to lift Sharpe/PF
- Opening economic gate or setting PROMOTION_ELIGIBLE
- Live / order / testnet / scheduler / capital activation

## Safety

`ECONOMIC_GATE_OPENED=false`  
`PROMOTION_ELIGIBLE=false`  
`LIVE_AUTHORIZED=false`  
`ORDERS=false`

Primary root cause: `G_exit_inefficiency`  
Secondary: C_direction_imbalance, B_cost_drag, I_insufficient_pit_period, K_broad_absence_of_economic_edge, H_low_exposure_capital_inefficiency, J_statistical_low_sample, D_instrument_concentration
