# Phase 3 Chart Contract Report

```text
DEFAULT_VISIBLE_BARS=120
SUPPORTED_CHART_WINDOWS=50,120,250,ALL
WINDOW_CONTROL_MECHANISM=existing_/market?limit=
ALL_WINDOW_LIMIT=720
CANDLE_CHART_REAL_DATA=true
VOLUME_REAL_DATA=true
CHART_SELECTED_INSTRUMENT_SYNC=true
SOURCE_VISIBLE=true
FRESHNESS_VISIBLE=true
TIMEFRAME_VISIBLE=true
BAR_COUNT_VISIBLE=true
TIMEZONE_VISIBLE=true
PRICE_PRECISION_SOURCE_BOUND=false
PRICE_PRECISION_NOTE=range_heuristic_display_only
GAP_RENDERING_POLICY=EXPLICIT
NO_VISUAL_INTERPOLATION_OF_MISSING_BARS=true
STALE_DATA_OVERLAY_REQUIRED=true
MISSING_INTERVALS_MARKED=true
NO_EMPTY_CHART_WHEN_DATA_EXISTS=true
NO_REQUEST_TIME_NETWORK_ACCESS=true
NETWORK_ALLOWLIST=SELF_ONLY
RENDER_MODE=SSR_SVG
CHART_LIBRARY=SSR_SVG
```

## Window support note

All four windows are linked through the existing architecture (`limit` query). The fixture may return fewer bars than requested; UI does not invent bars to fill a window.

## Stale / missing / gap

| State | Behavior | Evidence |
|---|---|---|
| Stale | Fail-closed empty bars + overlay badge | unit + `chart_stale_state.png` |
| Missing/incomplete | Explicit empty chart copy | `timeframe=1h` vs fixture `1d` + screenshot |
| Gap | Explicit dashed marker at post-gap index; no interpolation | adapter unit test; fixture contiguous → no gap screenshot |

## Geometry

From `docs/product/evidence/phase_3_20260716T191523Z/browser/browser_evidence_report.json`:

- Chart top ≈406.7px @ 1440×900
- Chart height ≈480.5px
- Material visibility ≥120px: true
- Horizontal overflow: false
