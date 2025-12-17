"""
MarketSentinel – Daily Market Outlook & Prognose-System
========================================================

Automatische Marktanalyse mit LLM-Integration für Peak_Trade.

Module:
- v0_daily_outlook: Täglicher Marktausblick mit Feature-Berechnung und LLM-Analyse

Stand: Dezember 2024
"""

from src.market_sentinel.v0_daily_outlook import (
    DailyMarketOutlookConfig,
    DailyMarketOutlookResult,
    MarketConfig,
    MarketFeatureSnapshot,
    build_llm_messages,
    call_llm,
    compute_feature_snapshot,
    load_daily_outlook_config,
    load_ohlcv_for_market,
    run_daily_market_outlook,
    write_markdown_report,
)

__all__ = [
    "DailyMarketOutlookConfig",
    "DailyMarketOutlookResult",
    "MarketConfig",
    "MarketFeatureSnapshot",
    "build_llm_messages",
    "call_llm",
    "compute_feature_snapshot",
    "load_daily_outlook_config",
    "load_ohlcv_for_market",
    "run_daily_market_outlook",
    "write_markdown_report",
]

__version__ = "0.1.0"
