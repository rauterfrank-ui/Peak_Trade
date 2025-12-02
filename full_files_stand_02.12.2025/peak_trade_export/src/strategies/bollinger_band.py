"""
Bollinger-Band-Strategie: Long bei Unterband, Short bei Oberband.
"""
from typing import Any, Dict
import pandas as pd
from .base import BaseStrategy
from .registry import register_strategy


@register_strategy
class BollingerBandStrategy(BaseStrategy):
    """
    Bollinger-Bands Mean-Reversion.
    
    Parameter:
        window: Fenster für MA/Std (default: 20)
        num_std: Anzahl Standardabweichungen (default: 2.0)
    """
    
    name = "bollinger_band"
    
    def generate_signals(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.Series:
        """
        Generiert Signals basierend auf Bollinger-Bands.
        
        Returns:
            pd.Series mit -1 (short), 0 (flat), +1 (long)
        """
        # Parameter
        window = params.get("window", 20)
        num_std = params.get("num_std", 2.0)
        
        # Preise
        close = df["close"].astype(float)
        
        # Bollinger Bands
        ma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        upper = ma + num_std * std
        lower = ma - num_std * std
        
        # Signals
        sig = pd.Series(0.0, index=df.index)
        sig[close < lower] = 1.0
        sig[close > upper] = -1.0
        
        # State speichern
        last_ma = ma.dropna()
        self._state["last_ma"] = last_ma.iloc[-1] if not last_ma.empty else None
        
        return sig
