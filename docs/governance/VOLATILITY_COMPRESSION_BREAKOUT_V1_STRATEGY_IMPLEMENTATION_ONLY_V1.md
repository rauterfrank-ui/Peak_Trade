# Volatility compression breakout v1 — strategy implementation only

## Status

`STRATEGY_IMPLEMENTATION_PRESENT` under operator GO `STRATEGY_IMPLEMENTATION_ONLY`.

## Binding

- Strategy identity: `VOLATILITY_COMPRESSION_BREAKOUT_V1`
- Program: `VOLATILITY_REGIME_RESEARCH_PROGRAM_V1`
- Signal family: `VOLATILITY_REGIME`
- Baseline: `UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1`
- Implementation binding: `config&#47;research&#47;volatility_compression_breakout_v1_strategy_implementation_binding_v1.json`
- Frozen measurement contract digest: `e8edbb7d2cbc55fa7ca979b3f1fc882fa56c03bd91cc2e708f0100342fae3785` (unmutated)
- Shared channel core: `src&#47;research&#47;price_channel_breakout_core_v1.py`
- Vol state: `src&#47;research&#47;volatility_compression_breakout_v1_vol_state_v1.py`
- Strategy: `src&#47;research&#47;volatility_compression_breakout_v1_strategy_v1.py`
- Baseline: `src&#47;research&#47;unconditional_20_bar_price_channel_breakout_v1.py`

## Semantics

- ATR(20)/close via SMA of True Range over 20 valid bars; incomplete or non-positive close → invalid
- Percentile rank 120 with current value included; tie method `WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF`
- Compression `<=0.20` for 12 consecutive bars opens one single-use release cycle
- Release offsets inclusive `1..6`; first expansion `>=0.75` consumes the cycle
- Channel miss or successful LONG/SHORT entry resets immediately; window expiry after offset 6
- Shared 20-bar prior high/low channel core for strategy and baseline
- Entry-event carrier: `ENTRY_EVENT` + `LONG`/`SHORT`/`NONE`; Double-Play remains sole transition authority
- Exit parameters declarative only; no exit state machine in this slice

## Explicit non-actions

No evaluation, runner, dataset load, holdout access, promotion, runtime, Master V2 mutation,
Double-Play authority change, risk/sizing mutation, execution-kernel mutation, or preregistration mutation.

## Next step

`MERGE_READINESS_AUDIT_AFTER_REQUIRED_CHECKS_GREEN` then, separately,
separate operator GO for bounded development evaluation.

---
docs_token: DOCS_TOKEN_VOLATILITY_COMPRESSION_BREAKOUT_V1_STRATEGY_IMPLEMENTATION_ONLY_V1
STATUS: STRATEGY_IMPLEMENTATION_PRESENT
scope: research, offline-only, non-authorizing, strategy-implementation
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---
