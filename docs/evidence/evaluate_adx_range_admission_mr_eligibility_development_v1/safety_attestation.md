# Safety attestation — evaluate ADX range-admission MR eligibility development v1

- `LIVE_AUTHORIZED=false`
- `RUNTIME_ACTIVATED=false`
- `SHADOW_ACTIVATED=false`
- `TESTNET_ACTIVATED=false`
- `ORDERS_SENT=false`
- `HOLDOUT_ACCESSED=false`
- `SEALED_HOLDOUT_CONTENT_INSPECTED=false`
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `ECONOMIC_VALIDITY_OFFLINE_GATE_CHANGED=false`
- `PROMOTION_ELIGIBLE=false`
- Evaluation uses only the sealed DEVELOPMENT_ONLY panel and the preregistered
  measurement contract. Eligibility filter formulas were frozen before the single
  run and not retuned after seeing metrics. The gate is research-local
  (post-map on MV2 position signals); no holdout access.
