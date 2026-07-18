# Bouchaud Safety Closeout

Owner path: `src&#47;strategies&#47;bouchaud&#47;bouchaud_microstructure_strategy.py`  
Owner symbol: `BouchaudMicrostructureStrategy.generate_signals`

| Check | Result |
|---|---|
| OHLC pressure formula (valid) | Unchanged for clean `len >= lookback_ticks` |
| Zero-range candle | Safe (replace 0 + epsilon + fillna) |
| NaN/Inf | Flat |
| Negative / non-finite volume (if column present) | Flat |
| Short history | Flat when `len < lookback_ticks` |
| Look-ahead | None (rolling + prefix test) |
| Proxy claim | Docstring + `attrs.proxy_data_risk=HIGH` |
| Long/Flat only | Enforced |
| Metadata | AUTH Non-Authority docstring; `IS_LIVE_READY=False` |

**PROXY_DATA_RISK=HIGH** unchanged (OHLCV proxy, not tick/L2).
