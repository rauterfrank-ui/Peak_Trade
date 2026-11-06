"""Longer chronological PIT acquisition scaffold v1.

NON-AUTHORITATIVE. Research acquisition planning only.
AUDIT_AUTHORITY_EFFECT=NONE
AUDIT_RUNTIME_EFFECT=NONE

Defaults: dry-run, no network, no write, no credentials.
External archive root required for any write path via PEAK_TRADE_DATA_ARCHIVE_ROOT.
"""

from __future__ import annotations

PACKAGE_MARKER = "LONGER_CHRONOLOGICAL_PIT_ACQUISITION_V1=true"
MANIFEST_SCHEMA_VERSION = "longer_chronological_pit_acquisition_manifest.v1"
STATE_SCHEMA_VERSION = "longer_chronological_pit_acquisition_state.v1"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1"
VENUE = "okx"
MARKET_TYPE = "linear_usdt_perpetual"
FREQUENCY = "PT1H"
OKX_BAR_PARAM = "1H"
TARGET_PERIOD_START = "2021-09-01T00:00:00Z"
TARGET_PERIOD_END = "2024-09-01T00:00:00Z"
ENV_ARCHIVE_ROOT = "PEAK_TRADE_DATA_ARCHIVE_ROOT"
SOURCE_ID_HISTORY_CANDLES = "okx_public_market_history_candles_v1"
SOURCE_ID_FUNDING = "okx_public_funding_rate_history_v1"
SOURCE_ID_CDN_FUNDING_ARCHIVE = "okx_cdn_swaprate_monthly_archive_v0"

__all__ = [
    "PACKAGE_MARKER",
    "MANIFEST_SCHEMA_VERSION",
    "STATE_SCHEMA_VERSION",
    "DATASET_ID",
    "VENUE",
    "MARKET_TYPE",
    "FREQUENCY",
    "ENV_ARCHIVE_ROOT",
]
