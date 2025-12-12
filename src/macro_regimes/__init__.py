"""
Macro Regimes – Loader & Utilities.

Dieses Package kümmert sich um das Laden und Verwalten der
aktuellen Makro-Einschätzung (current.toml) und später Archiv-Files.
"""

from .loader import MacroRegimeConfig, load_current_macro_regime_config

__all__ = [
    "MacroRegimeConfig",
    "load_current_macro_regime_config",
]
