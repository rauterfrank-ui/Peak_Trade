"""
Data Providers
==============

Provider-Implementierungen (z.B. Kraken über ccxt), die optionalen Dependencies
unterliegen können. Diese Module dürfen im Import-Pfad von `src.data` NICHT
hart geladen werden (lazy/optional imports).
"""

__all__ = [
    "KrakenCcxtBackend",
]

from .kraken_ccxt_backend import KrakenCcxtBackend
