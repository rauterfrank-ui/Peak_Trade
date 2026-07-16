# Phase 3 Focused Test Report

```text
RESULT=PASS
COMMAND=.venv/bin/python -m pytest -q tests/webui/test_market_dashboard_phase_3_chart_polish_v1.py tests/webui/test_market_dashboard_phase_2_operator_overview_v1.py tests/webui/test_market_dashboard_phase_1a_layout_header_v1.py tests/webui/test_market_dashboard_browser_policy_chrome_primary_v1.py
COUNTS=29 passed
LOG=docs/product/evidence/phase_3_20260716T191523Z/test_output/focused_tests.txt
```

## Phase 3 contract coverage (tests/webui/test_market_dashboard_phase_3_chart_polish_v1.py)

1. Canonical real OHLCV candles + volume markers in HTML
2. No spot / synthetic candle / bitcoin-direction fallback text
3. Selected instrument + chart meta sync markers
4. Timeframe + bar count sync (`1d` fixture)
5. Freshness / source / timezone / bars meta visible
6. Stale overlay without invented candles
7. Missing/incomplete (`timeframe=1h` vs fixture `1d`) explicit empty chart
8. Gap detection unit contract (timestamp holes → indices; no interpolation flag)
9. Window controls 50/120/250/ALL via `limit`
10. Consumer-only adapter (no kraken/fetch/credentials)
11. No external CDN strings
12. No mutating submit controls
13. Above-fold order preserved (header → hero → chart)

## Regression

- Phase 1A layout/header contracts preserved
- Phase 2 operator overview contracts preserved
- Chrome-primary browser policy contracts preserved
