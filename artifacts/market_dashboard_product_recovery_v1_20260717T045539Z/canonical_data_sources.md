# EXISTING_CANONICAL_DATA_SOURCES

| Source | Path | Safe read-only? |
|---|---|---|
| Ranking funnel fixture | `tests/fixtures/market_ranking_funnel_readmodel_v0/complete_minimal/` | yes |
| Futures OHLCV fixture | `tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal/` | yes |
| Depth fixture (optional) | `tests/fixtures/market_depth_readmodel_v0/` | yes |
| Materializer | `scripts/ops/materialize_market_dashboard_visual_operator_offline_bundles_v1.py` | yes |
| Visual operator start | `scripts/ops/start_market_dashboard_visual_operator_readonly_v1.sh` | yes (archive-dependent) |
| Double Play display | static in-memory display snapshot (code) | display-only; remap labels only |
| Current state snapshot | `src/webui/market_dashboard_current_state_snapshot_v0.py` | yes |

No synthetic candles. No invented rankings. Fixture binding is opt-in for review only.
