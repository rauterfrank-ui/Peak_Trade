"""
Peak_Trade Strategien
"""

from .base import BaseStrategy
from .registry import register_strategy, get_strategy

# Import strategien um sie zu registrieren
from . import ma_crossover
from . import rsi_reversion
from . import bollinger_band

__all__ = ["BaseStrategy", "register_strategy", "get_strategy"]
