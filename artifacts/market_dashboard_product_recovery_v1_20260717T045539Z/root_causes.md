# ROOT_CAUSES

1. **DATA_BINDING**: Review server starts without Market bundle env → governed snapshot/OHLCV/evidence unavailable on :8000.
2. **VISUAL_LAYOUT**: Empty chart forced to ~450px / `min-h-[20rem]` → dominates 1440×900 viewport (~65%).
3. **VISUAL_LAYOUT**: Giant `.pt-foundation-last-price` renders literal `unavailable` as primary focus.
4. **SEMANTIC_STATUS**: `_MATRIX_DISPLAY_STATUS_ALLOWLIST` maps `display_ready` → green `Active` while global Decision=Blocked / Authority=None.
5. **LOCALE**: German + English mix on operator surface (`Keine OHLCV-Bars`, DE decision sentence, EN headers).
6. **EMPTY_HIERARCHY**: Every card repeats full env-var recovery recipes as primary content.
7. **PROCESS**: Orphan uvicorn identity-ok but no pidfile → `PORT_OCCUPIED_BY_UNKNOWN_PROCESS`.

## Gap counts (pre-recovery)

MAJOR_PRODUCT_GAPS_BEFORE=7
