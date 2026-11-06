# Safety attestation — sealed long-panel offline economic reevaluation v1

- `LIVE_AUTHORIZED=false`
- `ORDERS=false`
- No shadow / paper / testnet / live start
- No scheduler / daemon / exchange writes
- No capital binding
- `ECONOMIC_GATE_OPENED=false` (unchanged)
- `ECONOMIC_VALIDITY_OFFLINE_GATE_CHANGED=false`
- `PROMOTION_ELIGIBLE=false`
- Bollinger `entry_side=NONE` unchanged
- No parameter tuning on the test panel
- Futures-only, BTC excluded, spot excluded
- Public/read-only sealed OHLCV only; raw archives remain external
