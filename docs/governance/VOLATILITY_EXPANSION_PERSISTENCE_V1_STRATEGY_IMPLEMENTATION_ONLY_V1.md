# Volatility expansion persistence v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO `STRATEGY_IMPLEMENTATION_ONLY`.

## Binding

- Strategy identity: `VOLATILITY_EXPANSION_PERSISTENCE_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Implementation binding: `config&#47;research&#47;volatility_expansion_persistence_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `92e2117ce7e60fe771c4d6e1d6d1aeb8645af80512e21cb9ff21fc4477c7c70e` (unchanged; run-count remains 0)
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Vol state: `src&#47;research&#47;volatility_expansion_persistence_v1_vol_state_v1.py`
- Strategy: `src&#47;research&#47;volatility_expansion_persistence_v1_strategy_v1.py`
- Baseline: `src&#47;research&#47;unconditional_20_bar_price_channel_breakout_v1.py`
- Productive PnL evaluator: referenced only
  (`src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`)

## Semantics

- ATR(14)&#47;close via SMA of True Range over 14 valid bars; incomplete or non-positive close → invalid
- Percentile rank 120 with current value included; tie method `WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF`
- Expansion confirmation on completed bar t:
  - percentile(t) >= 0.80
  - percentile(t-1) >= 0.80
  - percentile(t-2) < 0.80
  - normalized_atr(t) > normalized_atr(t-1)
- No entry on confirmation bar t; persistence window offsets inclusive `1..6`
- Single-use event; rearm requires at least one completed bar with percentile < 0.80
- No compression-regime prerequisite (material difference vs VCB-V1)
- Shared 20-bar prior high&#47;low channel core for strategy and baseline
- Entry-event carrier: `ENTRY_EVENT` + `LONG`&#47;`SHORT`&#47;`NONE`; Double-Play remains sole transition authority
- Exit parameters declarative only; no exit&#47;PnL producer and no second PnL truth in this slice

## Explicit non-actions

No evaluation, runner, dataset load, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, risk&#47;sizing mutation, execution-kernel mutation,
preregistration mutation, VCB-V1 retry, or second PnL truth.

## Next step

`MERGE_READINESS_AUDIT_AFTER_REQUIRED_CHECKS_GREEN` then, separately,
separate operator GO for bounded development evaluation.

---
docs_token: DOCS_TOKEN_VOLATILITY_EXPANSION_PERSISTENCE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
