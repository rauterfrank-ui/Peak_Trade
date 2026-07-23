# Momentum V2 — volatility-scaled own-instrument continuation — preregistered hypothesis and measurement v1

Status: `DEFINITION_ONLY_PREREGISTERED` — hypothesis and measurement contract
preregistered; no evaluation; no strategy implementation.

## Identity

- Scope: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_DEFINITION_ONLY_PREREGISTRATION_V1`
- Workstream: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1`
- Hypothesis: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1`
- Strategy identity: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1`
- Program: `MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1`

## Economic / scientific hypothesis

Volatility-normalizing own-instrument lookback returns before applying frozen
cross thresholds isolates continuation strength from local volatility and
improves net profit factor and net return after canonical costs versus the
identical frozen raw-return `momentum_1h` ENTRY&#47;EXIT baseline on the
DEVELOPMENT_ONLY non-BTC OKX perpetual panel.

## Baseline (unchanged)

- `FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1`
- `lookback_period=20`, `entry_threshold=0.02`, `exit_threshold=-0.01`
- Output contract `ENTRY_EXIT_EVENT_V1` (`+1` long entry, `-1` exit, `0` none)
- `entry_side=NONE`; no short entry
- Registry `MomentumStrategy` semantics not mutated

## Treatment variable

- `vol_scaled_momentum = (close / close.shift(N) - 1) / std(one_bar_simple_returns, N)`
- PIT-safe; completed bars only; `signal_lag_bars=1`
- Long ENTRY on upward cross of `vol_scaled_entry_z=1.0`
- EXIT on downward cross of `vol_scaled_exit_z=0.0`
- Zero &#47; non-finite realized vol → no signal (fail-closed)
- Same output contract as baseline; sole difference is volatility scaling

## Dataset binding

- `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1`
- BTC excluded; spot excluded; holdout unbound &#47; untouched

## Primary / guardrail metrics

- Primary decision metric: `NET_PROFIT_FACTOR`
- Guardrails: gross PF&#47;PnL, net return vs baseline, net expectancy, MaxDD vs
  baseline and absolute MaxDD ≤ 0.25, cost-stress PF@1.5x ≥ 1.0, trade sample
  ≥ 50, per-segment trades ≥ 10, concentration ≤ 0.35, time-segment robustness
  pass ratio ≥ 0.5, deterministic repro digest match

## PASS / FAIL

PASS only if all preregistered gates pass jointly, including treatment net PF
and net return strictly greater than baseline. Otherwise
`DEVELOPMENT_FAIL` &#47; `FAIL_CLOSED_NO_RETRY`.

## Limits

- Development run limit: 1
- Holdout run limit: 0
- `EVALUATION_AUTHORIZED=false`
- `IMPLEMENTATION_AUTHORIZED=false`
- `DEVELOPMENT_RUN_COUNT=0` &#47; `RUN_SLOT_CONSUMED=false`
- No parameter grid; no raw-threshold retune; no second development run

## Evidence

- Contract: `config&#47;research&#47;momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_economic_hypothesis_measurement_contract_v1.json`
- Preregistration evidence: `docs&#47;evidence&#47;preregister_momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_v1&#47;`

---
docs_token: DOCS_TOKEN_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1
STATUS: DEFINITION_ONLY_PREREGISTERED
scope: research, offline-only, non-authorizing, definition-governance
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
