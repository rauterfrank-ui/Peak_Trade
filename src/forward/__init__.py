# src/forward/__init__.py
"""
Forward-/Paper-Trading-Support für Peak_Trade.

Dieses Paket enthält:
- Standardisierte Datenstrukturen für Forward-Signale
- Helper zum Speichern/Laden von Signal-CSV-Dateien
"""
from .signals import (
    ForwardSignal,
    FORWARD_SIGNALS_COLUMNS,
    signals_to_dataframe,
    save_signals_to_csv,
)

__all__ = [
    "ForwardSignal",
    "FORWARD_SIGNALS_COLUMNS",
    "signals_to_dataframe",
    "save_signals_to_csv",
]
