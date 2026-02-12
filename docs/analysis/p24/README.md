# P24 — Backtest Execution Realism v2 (Partial fills + Volume cap)

See P23 for v1 baseline. This phase adds:
- partial fills across multiple OHLCV bars
- per-bar volume participation cap
- deterministic allocator (no RNG)

Implementation: `src/execution/p24/`
Tests: `tests/p24/`
