# Volatility decay breakout v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO `STRATEGY_IMPLEMENTATION_ONLY`.

## Binding

- Strategy identity: `VOLATILITY_DECAY_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Implementation binding: `config&#47;research&#47;volatility_decay_breakout_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `d56ee1f11f697d6734c505c436be325060d956023573ef5cfd64aa010d00fa3f`
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Vol state: `src&#47;research&#47;volatility_decay_breakout_v1_vol_state_v1.py`
- Strategy: `src&#47;research&#47;volatility_decay_breakout_v1_strategy_v1.py`
- Baseline: `src&#47;research&#47;unconditional_20_bar_price_channel_breakout_v1.py`
- Productive PnL evaluator: referenced only
  (`src&#47;research&#47;volatility_compression_breakout_v1_development_evaluation_v1&#47;productive_exit_pnl_evaluator_v1.py`)
- Source definition base SHA: `38f124c88dd9caf29034d1eb70656b68baeb01b0` (PR &#35;5447)

## Semantics

- ATR(14)&#47;close via SMA of True Range over 14 valid bars; incomplete or non-positive close → invalid
- Percentile rank 120 with current value included; tie method `WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF`
- Decay confirmation on completed bar t:
  - percentile(t-1) >= 0.70
  - percentile(t) < 0.40
  - normalized_atr(t) < normalized_atr(t-1)
- No entry on confirmation bar t; decay window offsets inclusive `1..8`
- Single-use event; rearm requires at least one completed bar with percentile >= 0.70
- No compression-regime prerequisite (material difference vs VCB-V1)
- No expansion-persistence requirement (material difference vs VEP-V1)
- Shared 20-bar prior high&#47;low channel core for strategy and baseline
- Entry-event carrier: `ENTRY_EVENT` + `LONG`&#47;`SHORT`&#47;`NONE`; Double-Play remains sole transition authority
- Exit parameters declarative only; no exit&#47;PnL producer and no second PnL truth in this slice

## Explicit non-actions

No evaluation, runner, dataset load, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, risk&#47;sizing mutation, execution-kernel mutation,
preregistration mutation, VCB-V1 retry, VEP-V1 retry, or second PnL truth.

## Next step

`REVIEW_AND_MERGE_IMPLEMENTATION_ONLY_PR_THEN_SEPARATE_OPERATOR_GO_FOR_DEVELOPMENT_EVALUATION_AUTHORIZATION`

---
docs_token: DOCS_TOKEN_VOLATILITY_DECAY_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
