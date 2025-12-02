"""
Peak_Trade MACD Strategy
=========================
MACD (Moving Average Convergence Divergence) Trend-Following.

Konzept:
- MACD Line = EMA(12) - EMA(26)
- Signal Line = EMA(9) von MACD Line
- Histogram = MACD Line - Signal Line
- Entry: MACD kreuzt Signal von unten
- Exit: MACD kreuzt Signal von oben
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet MACD-Indikatoren.
    
    Args:
        prices: Close-Preise
        fast_period: Schnelle EMA
        slow_period: Langsame EMA
        signal_period: Signal-Linie EMA
        
    Returns:
        (macd_line, signal_line, histogram)
    """
    # EMAs berechnen
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    
    # MACD Line = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow
    
    # Signal Line = EMA der MACD Line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # Histogram = Differenz
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert MACD-basierte Signale.
    
    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'fast_ema', 'slow_ema', 'signal_ema'
        
    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)
    """
    # Parameter
    fast = params.get('fast_ema', 12)
    slow = params.get('slow_ema', 26)
    signal = params.get('signal_ema', 9)
    
    # MACD berechnen
    macd_line, signal_line, histogram = calculate_macd(
        df['close'],
        fast_period=fast,
        slow_period=slow,
        signal_period=signal
    )
    
    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)
    
    # Bullish Crossover: MACD kreuzt Signal von unten
    cross_up = (macd_line.shift(1) < signal_line.shift(1)) & (macd_line > signal_line)
    signals[cross_up] = 1
    
    # Bearish Crossover: MACD kreuzt Signal von oben
    cross_down = (macd_line.shift(1) > signal_line.shift(1)) & (macd_line < signal_line)
    signals[cross_down] = -1
    
    return signals


def add_macd_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """Fügt MACD-Indikatoren zum DataFrame hinzu."""
    df = df.copy()
    
    fast = params.get('fast_ema', 12)
    slow = params.get('slow_ema', 26)
    signal = params.get('signal_ema', 9)
    
    macd_line, signal_line, histogram = calculate_macd(
        df['close'],
        fast_period=fast,
        slow_period=slow,
        signal_period=signal
    )
    
    df['macd'] = macd_line
    df['macd_signal'] = signal_line
    df['macd_histogram'] = histogram
    
    return df


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
MACD Trend-Following
=====================
Fast EMA:          {params.get('fast_ema', 12)}
Slow EMA:          {params.get('slow_ema', 26)}
Signal EMA:        {params.get('signal_ema', 9)}
Stop-Loss:         {params.get('stop_pct', 0.025):.1%}

Konzept:
- Entry: MACD kreuzt Signal-Linie von unten (Bullish)
- Exit: MACD kreuzt Signal-Linie von oben (Bearish)
"""
