# Valid Input Output Parity

## Ehlers

- Fixture: `n=150`, seed `42`, `lookback=100`, `min_cycle_length=6`, UTC hourly index, `close` only.
- Pre-change golden sum = 74; post-change list equality asserted in `test_valid_input_output_parity_exact`.
- `EHLERS_VALID_INPUT_OUTPUT_CHANGED=false`

## Bouchaud

- Fixture: `n=150`, linear close 100→150, bullish OHLC, `volume=1000`, `lookback_ticks=20`, `imbalance_threshold=0.3`.
- Pre-change output: all `1`; post-change equality asserted in `test_valid_ohlc_output_parity_exact`.
- `BOUCHAUD_VALID_INPUT_OUTPUT_CHANGED=false`

Insufficient-history / invalid-input paths intentionally changed to Flat (safety), outside “valid sufficient” parity scope.
