# src/forward/__init__.py
"""
Forward-/Paper-Trading-Support für Peak_Trade.

Dieses Paket enthält:
- Standardisierte Datenstrukturen für Forward-Signale
- Helper zum Speichern/Laden von Signal-CSV-Dateien
"""
from .signals import (
    FORWARD_SIGNALS_COLUMNS,
    ForwardSignal,
    save_signals_to_csv,
    signals_to_dataframe,
)

__all__ = [
    "FORWARD_SIGNALS_COLUMNS",
    "ForwardSignal",
    "save_signals_to_csv",
    "signals_to_dataframe",
]
