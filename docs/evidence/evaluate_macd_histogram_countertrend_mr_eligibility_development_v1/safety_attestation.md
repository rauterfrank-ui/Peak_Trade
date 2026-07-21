# Safety attestation — evaluate MACD histogram-countertrend MR eligibility development v1

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
  measurement contract. The MACD(12,26,9) histogram-sign countertrend eligibility
  filter formula was frozen before the single run and not retuned after seeing
  metrics. The gate is research-local (post-map on MV2 position signals,
  side-aware: long admitted iff `histogram < 0`, short admitted iff
  `histogram > 0`); no holdout access.
- Exactly one DEVELOPMENT evaluation run was executed (baseline + treatment arms
  in this single run); no second run occurred regardless of result.
