"""
Peak_Trade Momentum Strategy
==============================
Momentum-basierte Trading-Strategie.

Konzept:
- Long-Entry: Wenn Momentum > entry_threshold
- Exit: Wenn Momentum < exit_threshold
- Momentum = (close / close[lookback]) - 1
"""

import pandas as pd
import numpy as np
from typing import Dict


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert Momentum-basierte Signale.
    
    Args:
        df: OHLCV-DataFrame mit DatetimeIndex
        params: Dict mit 'lookback_period', 'entry_threshold', 'exit_threshold'
        
    Returns:
        Series mit Werten:
        - 1: Long-Signal
        - 0: Kein Signal (Neutral)
        - -1: Exit-Signal
        
    Example:
        >>> params = {
        ...     'lookback_period': 20,
        ...     'entry_threshold': 0.02,
        ...     'exit_threshold': -0.01
        ... }
        >>> signals = generate_signals(df, params)
    """
    # Parameter extrahieren
    lookback = params.get('lookback_period', 20)
    entry_threshold = params.get('entry_threshold', 0.02)
    exit_threshold = params.get('exit_threshold', -0.01)
    
    # Validierung
    if lookback <= 0:
        raise ValueError(f"lookback_period ({lookback}) muss > 0 sein")
    
    if len(df) < lookback:
        raise ValueError(f"DataFrame zu kurz ({len(df)} Bars), brauche min. {lookback}")
    
    # Momentum berechnen: (Close heute / Close vor N Tagen) - 1
    momentum = (df['close'] / df['close'].shift(lookback)) - 1
    
    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)
    
    # Entry-Logik: Momentum überschreitet Entry-Threshold
    # Bedingung: Momentum[t-1] < entry_threshold UND Momentum[t] > entry_threshold
    cross_up = (momentum.shift(1) < entry_threshold) & (momentum > entry_threshold)
    signals[cross_up] = 1
    
    # Exit-Logik: Momentum fällt unter Exit-Threshold
    cross_down = (momentum.shift(1) > exit_threshold) & (momentum < exit_threshold)
    signals[cross_down] = -1
    
    return signals


def add_momentum_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """
    Fügt Momentum-Indikatoren zum DataFrame hinzu (für Visualisierung).
    
    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'lookback_period'
        
    Returns:
        DataFrame mit zusätzlicher Spalte 'momentum'
        
    Example:
        >>> df_with_mom = add_momentum_indicators(df, {'lookback_period': 20})
        >>> print(df_with_mom[['close', 'momentum']].tail())
    """
    df = df.copy()
    
    lookback = params.get('lookback_period', 20)
    
    # Momentum berechnen
    df['momentum'] = (df['close'] / df['close'].shift(lookback)) - 1
    
    # Optional: Glättung mit EMA
    df['momentum_ema'] = df['momentum'].ewm(span=5, adjust=False).mean()
    
    return df


def get_strategy_description(params: Dict) -> str:
    """
    Gibt Strategie-Beschreibung zurück.
    
    Args:
        params: Strategie-Parameter
        
    Returns:
        Beschreibungstext
    """
    return f"""
Momentum-Strategie (1h)
=======================
Lookback-Period:   {params.get('lookback_period', 20)} Bars
Entry-Threshold:   {params.get('entry_threshold', 0.02):.1%}
Exit-Threshold:    {params.get('exit_threshold', -0.01):.1%}
Stop-Loss:         {params.get('stop_pct', 0.025):.1%}

Konzept:
- Long wenn Momentum > {params.get('entry_threshold', 0.02):.1%}
- Exit wenn Momentum < {params.get('exit_threshold', -0.01):.1%}
"""
