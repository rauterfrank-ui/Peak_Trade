# Ehlers Safety Closeout

Owner: `src/strategies/ehlers/ehlers_cycle_filter_strategy.py::EhlersCycleFilterStrategy.generate_signals`

| Check | Result |
|---|---|
| Super Smoother formula | Unchanged for finite valid inputs |
| Warm-up | `len < lookback` → Flat (pre-existing) |
| NaN/Inf close | Flat (`invalid_input`) — no entry |
| Constant series | Deterministic |
| Look-ahead | None (causal recursion + prefix test) |
| Long/Flat only | Enforced; no Short |
| Metadata | AUTH Non-Authority docstring; `IS_LIVE_READY=False`; registry description Non-Authority |
| Valid golden parity | Exact match seed=42 / n=150 / lookback=100 |

Registry: description updated; `allowed_environments` kept including `backtest` (tooling default-env gate).
