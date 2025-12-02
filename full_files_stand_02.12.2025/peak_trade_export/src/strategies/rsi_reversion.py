"""
RSI-Reversion-Strategie: Long bei überverkauft, Short bei überkauft.
"""
from typing import Any, Dict
import pandas as pd
from .base import BaseStrategy
from .registry import register_strategy


@register_strategy
class RsiReversionStrategy(BaseStrategy):
    """
    RSI-basierte Mean-Reversion-Strategie.
    
    Parameter:
        period: RSI-Periode (default: 14)
        upper: Obere RSI-Schwelle (default: 70)
        lower: Untere RSI-Schwelle (default: 30)
    """
    
    name = "rsi_reversion"
    
    def generate_signals(
        self, df: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.Series:
        """
        Generiert Signals basierend auf RSI-Extremen.
        
        Returns:
            pd.Series mit -1 (short), 0 (flat), +1 (long)
        """
        # Parameter
        period = params.get("period", 14)
        upper = params.get("upper", 70.0)
        lower = params.get("lower", 30.0)
        
        # Preise
        close = df["close"].astype(float)
        
        # RSI-Berechnung
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Division-by-zero vermeiden
        avg_loss = avg_loss.replace(0.0, 1e-9)
        
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        # Signals
        sig = pd.Series(0.0, index=df.index)
        sig[rsi < lower] = 1.0
        sig[rsi > upper] = -1.0
        
        # State speichern
        last_rsi = rsi.dropna()
        self._state["last_rsi"] = last_rsi.iloc[-1] if not last_rsi.empty else None
        
        return sig
