# P24 — Backtest Execution Realism v2 (Partial fills + Volume cap)

See P23 for v1 baseline. This phase adds:
- partial fills across multiple OHLCV bars
- per-bar volume participation cap
- deterministic allocator (no RNG)

Implementation: `src/execution/p24/`
Tests: `tests/p24/`

## Partial Fills v2 (P25 implementation)
- Spec: `docs&#47;analysis&#47;p24&#47;PARTIAL_FILLS_V2_SPEC.md`
- Code: `src&#47;execution&#47;p24&#47;execution_model_v2.py` + `src&#47;execution&#47;p24&#47;config.py`
- Tests: `tests&#47;p24&#47;test_execution_model_v2_partial_fills.py`

Notes:
- Deterministic bar-based partial fills (no randomness).
- Quantity conservation and proportional fees.
- Stop-market triggers then executes as market (configurable same-bar behavior).
