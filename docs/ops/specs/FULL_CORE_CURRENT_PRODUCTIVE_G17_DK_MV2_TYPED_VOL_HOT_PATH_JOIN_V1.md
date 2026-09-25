# Full-Core CURRENT_PRODUCTIVE G17 DK/MV2 Typed-Vol Hot-Path Join v1

---
docs_token: DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_G17_DK_MV2_TYPED_VOL_HOT_PATH_JOIN_V1
STATUS: CAPABILITY_AVAILABLE
scope: DK slice JOIN-1 mark extract + JOIN-2 checkpoint handoff into Master-V2
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
CORE_LOGIC_CHANGE: false
---

## Machine summary

```
CAPABILITY_ID=FULL_CORE_CURRENT_PRODUCTIVE_G17_DK_MV2_TYPED_VOL_HOT_PATH_JOIN_V1
FC_02_BLOCKER=TYPED_VOLATILITY_ESTIMATE_MISSING
JOIN_OWNER=current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1
JOIN_1=current_productive_g17_pt1m_mark_sample_adapter_v1
JOIN_2=current_productive_g17_typed_vol_mark_history_checkpoint_v1
CMC_BIND=current_productive_master_v2_runtime_cycle_v1 (unchanged owner)
PRESENCE_GATE=double_play_runtime_typed_volatility_presence_gate_v1 (unchanged)
NO_NEW_VOLATILITY_FORMULA=true
NO_SILENT_DEFAULT=true
POST_AUTHORIZED=false
```

## Closed edge

```
Authorized GET history-mark-price-candles (PT1M confirm=1)
  → extract_full_core_g17_pt1m_mark_ingest_fields_v1
  → apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1
  → g17_typed_vol_producer passed to run_current_productive_master_v2_runtime_cycle_v1
  → apply_current_productive_g17_typed_vol_cmc_bind_v1
  → typed presence gate (no TYPED_VOLATILITY_ESTIMATE_MISSING when estimate PRODUCED)
```
