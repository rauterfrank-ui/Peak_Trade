# Phase 3 Operator Runtime Data Binding Repair

```text
GO_TOKEN=GO_VISUAL_OPERATOR_DASHBOARD_PR5248_OPERATOR_RUNTIME_DATA_BINDING_REPAIR_V1
PR=5248
PREVIOUS_EVIDENCE_OPERATOR_PATH_PARITY=false
REPAIR_EVIDENCE_OPERATOR_PATH_PARITY=true
```

## Root cause

Previous Phase-3 Chrome evidence (`docs/product/evidence/phase_3_20260716T191523Z/`) was produced against a **fixture-injected** uvicorn process:

- `PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT=tests&#47;fixtures&#47;...&#47;complete_minimal`
- Default evidence path used `timeframe=1d` (fixture only contains `1d` bars)
- `PEAK_TRADE_FIXED_GENERATED_AT_UTC=2030-01-15...` pinned display freshness

The operator review URL `http://127.0.0.1:8766/market?timeframe=1h` started with bare uvicorn (or leaked fixture env) therefore showed:

- `Source=fixture:complete_minimal` and/or timeframe mismatch → **Bars=0**
- Future freshness timestamp 2030
- Empty chart / stale fail-closed presentation

`CANDLE_CHART_REAL_DATA=true` was therefore proven only against the fixture harness path, **not** the normal operator server path.

```text
EVIDENCE_SERVER_COMMAND=.venv/bin/python -m uvicorn ... WITH fixture env + timeframe=1d
OPERATOR_SERVER_COMMAND=.venv/bin/python -m uvicorn ... WITHOUT canonical bind (before repair)
EVIDENCE_DATA_SOURCE=fixture:complete_minimal
OPERATOR_DATA_SOURCE_BEFORE=fixture:complete_minimal (or disabled/stale empty for 1h)
EVIDENCE_BAR_COUNT=>0 at timeframe=1d only
OPERATOR_BAR_COUNT=0 at timeframe=1h
DATA_PATH_PARITY=FAIL
ROOT_CAUSE=phase3_evidence_used_test_fixture_1d_harness_not_canonical_operator_1h_bind
```

## Repair

- Added `src/webui/market_visual_operator_surface_v1/local_offline_binding_v1.py`
- `create_app()` applies durable offline bundle binding when:
  - not under pytest
  - OHLCV env not already explicit
  - canonical materialized bundle present (same root as start script)
- Never binds `fixture:*` / `complete_minimal`
- Never sets `PEAK_TRADE_FIXED_GENERATED_AT_UTC`
- Chart adapter truthful flags: `CANDLE_CHART_REAL_DATA` / `VOLUME_REAL_DATA` only for `CANONICAL_LOCAL_READ_ONLY_BUNDLE` with bars>0 and non-future freshness

## Canonical bundle

```text
CANONICAL_OHLCV_BUNDLE_PRESENT=true
CANONICAL_OHLCV_BUNDLE_PATH=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/_market_visual_operator_offline_bundles_v1/futures_ohlcv
CANONICAL_SYMBOL=ETHUSDT (and ranking primary NOTUSDT)
CANONICAL_TIMEFRAME=1h
CANONICAL_BAR_COUNT=120
CANONICAL_DATA_START=2024-05-27T02:00:00Z
CANONICAL_DATA_END=2024-06-01T01:00:00Z
CANONICAL_FRESHNESS_STATE=OK (generated_at 2026-07-16T18:05:26Z)
CANONICAL_MANIFEST_VERIFIED=true
SOURCE=historical_panel_offline:214a3f1940d54030
```

## Operator verification (same server port 8766)

```text
OPERATOR_HTTP_STATUS=200
OPERATOR_SOURCE=historical_panel_offline:214a3f1940d54030
OPERATOR_BAR_COUNT=120
OPERATOR_CANDLE_DOM_COUNT=216
OPERATOR_VOLUME_BAR_COUNT=120
FUTURE_TIMESTAMP_PRESENT=false
REAL_CHROME_VERIFIED=true
CONSOLE_ERRORS=0
PAGE_ERRORS=0
FAILED_ASSETS=0
EXTERNAL_REQUESTS=0
CHART_MATERIALLY_VISIBLE_1440X900=true
```

Screenshots:

- `docs/product/evidence/phase_3_operator_binding_repair_20260716T193000Z/screenshots/operator_1440x900_overview_candles.png`
- `docs/product/evidence/phase_3_operator_binding_repair_20260716T193000Z/screenshots/operator_chart_closeup_candles_volume.png`
- `docs/product/evidence/phase_3_operator_binding_repair_20260716T193000Z/screenshots/operator_chart_meta_row.png`
- `docs/product/evidence/phase_3_operator_binding_repair_20260716T193000Z/screenshots/operator_full_page.png`

Machine report:

- `docs/product/evidence/phase_3_operator_binding_repair_20260716T193000Z/browser/operator_chrome_report.json`

## Semantics

```text
TRADING_SEMANTICS_EFFECT=NONE
DATA_PRODUCER_EFFECT=NONE
RUNTIME_EFFECT=LOCAL_READ_ONLY_WEB_SERVER_ONLY
AUTHORITY_EFFECT=NONE
LIVE_AUTHORIZED=false
ORDERS_ALLOWED=false
STOP_BEFORE_MERGE=true
```
