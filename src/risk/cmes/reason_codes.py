"""
CMES reason code registries: stable, uppercase-snake identifiers.

Tests enforce uppercase_snake patterns and that only these stable ids are used.
"""

# Risk reason codes (stable)
RISK_REASON_CODES = frozenset(
    {
        "LIMIT_NEAR",
        "LIMIT_BREACH",
        "VOLATILITY_HIGH",
        "DRAWDOWN_ELEVATED",
        "LIQUIDITY_LOW",
        "CORRELATION_SPIKE",
        "POSITION_CONCENTRATION",
        "NO_DATA",
        "KILL_SWITCH",
    }
)

# Strategy reason codes (stable)
STRATEGY_REASON_CODES = frozenset(
    {
        "PAUSED_BY_OPERATOR",
        "DEGRADED_DATA",
        "BACKTEST_ONLY",
        "LIVE_DISABLED",
        "REGIME_FILTER",
        "SIGNAL_OFF",
    }
)

# Data quality flags (stable)
DATA_QUALITY_FLAGS = frozenset(
    {
        "MISSING_OHLCV",
        "STALE_QUOTE",
        "GAP_DETECTED",
        "LOW_VOLUME",
        "SPREAD_WIDE",
        "NO_RECENT_TICK",
    }
)

# No-trade trigger ids (stable)
NO_TRADE_TRIGGER_IDS = frozenset(
    {
        "RISK_BLOCK",
        "STRATEGY_DISABLED",
        "NO_LIQUIDITY",
        "CIRCUIT_BREAKER",
        "MAINTENANCE",
        "KILL_SWITCH",
    }
)
