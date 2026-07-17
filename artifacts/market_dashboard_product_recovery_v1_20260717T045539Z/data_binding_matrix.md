# DATA_BINDING_MATRIX

| Surface | Env gate | Bundle | Missing behavior |
|---|---|---|---|
| Top-20 / Ranking | `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED` + `_BUNDLE_ROOT` | `ranking_funnel.json` | empty / disabled |
| OHLCV chart | `PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED` + `_BUNDLE_ROOT` | `futures_ohlcv.json` | empty SSR chart |
| Visual operator / Funnel / Economic | `PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT` | economic JSON set | NOT_AVAILABLE |
| Linear diagnostics | `PEAK_TRADE_MARKET_LINEAR_DIAGNOSTICS_BUNDLE_ROOT` | factor/drift/ortho JSON | NOT_AVAILABLE |
| F5 compact | `PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED` + `_BUNDLE_ROOT` | F5 dashboard bundle | unavailable |
| Double Play | none (static display) | n/a | always CONFIGURED after remap |
| Safety | process LIVE/ORDERS + F5 | n/a | Blocked / not authorized |

## Review binding (proposed)

`PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES=1` on review_server start/open:
- bind ranking + OHLCV fixture roots under `tests/fixtures/.../complete_minimal`
- keep `LIVE_AUTHORIZED=false` `ORDERS_ALLOWED=false`
- `/market` without flag remains canonical fail-closed empty
