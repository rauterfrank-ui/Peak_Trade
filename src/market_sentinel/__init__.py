"""
MarketSentinel – Daily Market Outlook & Prognose-System
========================================================

Automatische Marktanalyse mit LLM-Integration für Peak_Trade.

Module:
- v0_daily_outlook: Täglicher Marktausblick mit Feature-Berechnung und LLM-Analyse

Stand: Dezember 2024
"""

from src.market_sentinel.v0_daily_outlook import (
    MarketConfig,
    MarketFeatureSnapshot,
    DailyMarketOutlookConfig,
    DailyMarketOutlookResult,
    load_daily_outlook_config,
    load_ohlcv_for_market,
    compute_feature_snapshot,
    build_llm_messages,
    call_llm,
    write_markdown_report,
    run_daily_market_outlook,
)

__all__ = [
    "MarketConfig",
    "MarketFeatureSnapshot",
    "DailyMarketOutlookConfig",
    "DailyMarketOutlookResult",
    "load_daily_outlook_config",
    "load_ohlcv_for_market",
    "compute_feature_snapshot",
    "build_llm_messages",
    "call_llm",
    "write_markdown_report",
    "run_daily_market_outlook",
]

__version__ = "0.1.0"
