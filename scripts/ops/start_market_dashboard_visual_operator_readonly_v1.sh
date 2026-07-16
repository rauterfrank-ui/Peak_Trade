#!/usr/bin/env bash
# Start the READ-ONLY market visual operator surface v1 locally against offline bundles.
#
# This script materializes offline read-only bundles from the real historical futures panel
# and PR5242 economic evidence, exports the fail-closed display gates, and launches uvicorn.
# It grants NO runtime, order, live, promotion or execution authority.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

ARCHIVE_ROOT="/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
PANEL_PATH="${ARCHIVE_ROOT}/datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/panel/normalized_panel_bars.json"
ECONOMIC_EVIDENCE_DIR="${ARCHIVE_ROOT}/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
LINEAR_DIAGNOSTICS_DIR="${ARCHIVE_ROOT}/research/bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0_20260715T004424Z"

# Prefer a durable path under the archive research dir; fall back to /tmp.
DURABLE_BUNDLE_ROOT="${ARCHIVE_ROOT}/research/_market_visual_operator_offline_bundles_v1"
TMP_BUNDLE_ROOT="/tmp/peak_trade_market_visual_operator_bundles_v1"
BUNDLE_ROOT="${MARKET_VISUAL_OPERATOR_BUNDLE_ROOT:-${DURABLE_BUNDLE_ROOT}}"
if ! mkdir -p "${BUNDLE_ROOT}" 2>/dev/null; then
  BUNDLE_ROOT="${TMP_BUNDLE_ROOT}"
  mkdir -p "${BUNDLE_ROOT}"
fi

HOST="${MARKET_VISUAL_OPERATOR_HOST:-127.0.0.1}"
PORT="${MARKET_VISUAL_OPERATOR_PORT:-8765}"

echo "[start] materializing offline bundles into: ${BUNDLE_ROOT}"
PEAK_TRADE_MARKET_VISUAL_OPERATOR_PANEL_PATH="${PANEL_PATH}" \
PEAK_TRADE_MARKET_VISUAL_OPERATOR_ECONOMIC_EVIDENCE_DIR="${ECONOMIC_EVIDENCE_DIR}" \
  python3 scripts/ops/materialize_market_dashboard_visual_operator_offline_bundles_v1.py \
    --output-root "${BUNDLE_ROOT}"

# Read-only display gates (fail-closed OFF by default; enabled here for local inspection).
export PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED=1
export PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT="${BUNDLE_ROOT}/futures_ohlcv"
export PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1
export PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT="${BUNDLE_ROOT}/ranking_funnel"
export PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED=1
export PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT="${BUNDLE_ROOT}/f5_dashboard"
export PEAK_TRADE_MARKET_VISUAL_OPERATOR_EVIDENCE_ROOT="${BUNDLE_ROOT}"
export PEAK_TRADE_MARKET_LINEAR_DIAGNOSTICS_BUNDLE_ROOT="${LINEAR_DIAGNOSTICS_DIR}"
export PEAK_TRADE_MARKET_DEPTH_ENABLED=0

echo "[start] READ-ONLY market visual operator surface v1"
echo "[start] no runtime/order/live/promotion/execution authority"
echo "[start] open: http://${HOST}:${PORT}/market?timeframe=1h"

if command -v uv >/dev/null 2>&1; then
  exec uv run uvicorn src.webui.app:app --host "${HOST}" --port "${PORT}" --no-access-log
fi
exec python3 -m uvicorn src.webui.app:app --host "${HOST}" --port "${PORT}" --no-access-log
