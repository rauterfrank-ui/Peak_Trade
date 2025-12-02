"""
Peak_Trade Bollinger Bands Strategy
====================================
Bollinger Bands-basierte Mean-Reversion-Strategie.

Konzept:
- Long-Entry: Preis berührt untere Band (überverkauft)
- Exit: Preis erreicht Mittel-Band
- Bollinger Bands = MA ± (Std * N)
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet Bollinger Bands.
    
    Args:
        prices: Close-Preise
        period: MA-Periode
        num_std: Anzahl Standard-Abweichungen
        
    Returns:
        (upper_band, middle_band, lower_band)
    """
    # Middle Band = Simple Moving Average
    middle = prices.rolling(window=period).mean()
    
    # Standard-Abweichung
    std = prices.rolling(window=period).std()
    
    # Upper/Lower Bands
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return upper, middle, lower


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert Bollinger Bands-Signale.
    
    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'bb_period', 'bb_std', 'entry_threshold', 'exit_threshold'
        
    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)
        
    Strategy:
        - Entry: Preis <= lower_band * entry_threshold (z.B. 95% der unteren Band)
        - Exit: Preis >= middle_band
    """
    # Parameter
    bb_period = params.get('bb_period', 20)
    bb_std = params.get('bb_std', 2.0)
    entry_threshold = params.get('entry_threshold', 0.95)
    exit_threshold = params.get('exit_threshold', 0.50)
    
    # Bollinger Bands berechnen
    upper, middle, lower = calculate_bollinger_bands(
        df['close'],
        period=bb_period,
        num_std=bb_std
    )
    
    # Entry-Level: 95% der unteren Band (konservativer)
    entry_level = lower * entry_threshold
    
    # Exit-Level: Mittel-Band
    exit_level = middle
    
    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)
    
    # Entry: Preis kreuzt entry_level von oben nach unten
    cross_entry = (df['close'].shift(1) > entry_level.shift(1)) & (df['close'] <= entry_level)
    signals[cross_entry] = 1
    
    # Exit: Preis kreuzt exit_level von unten nach oben
    cross_exit = (df['close'].shift(1) < exit_level.shift(1)) & (df['close'] >= exit_level)
    signals[cross_exit] = -1
    
    return signals


def add_bollinger_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """Fügt Bollinger Bands zum DataFrame hinzu."""
    df = df.copy()
    
    bb_period = params.get('bb_period', 20)
    bb_std = params.get('bb_std', 2.0)
    
    upper, middle, lower = calculate_bollinger_bands(
        df['close'],
        period=bb_period,
        num_std=bb_std
    )
    
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    
    # Bandwidth (Volatilitäts-Indikator)
    df['bb_width'] = (upper - lower) / middle
    
    # %B (Position innerhalb der Bands)
    df['bb_percent'] = (df['close'] - lower) / (upper - lower)
    
    return df


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Bollinger Bands Mean-Reversion
================================
BB-Periode:        {params.get('bb_period', 20)} Bars
Standard-Abw.:     {params.get('bb_std', 2.0)} σ
Entry-Threshold:   {params.get('entry_threshold', 0.95):.0%} untere Band
Exit-Threshold:    Mittel-Band
Stop-Loss:         {params.get('stop_pct', 0.03):.1%}

Konzept:
- Entry wenn Preis überverkauft (untere Band)
- Exit bei Mean-Reversion (Mittel-Band)
"""
