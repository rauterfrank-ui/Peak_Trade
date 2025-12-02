"""
Peak_Trade – Strategy Loader
Alle Strategien werden hier registriert.
"""

# Mapping: Strategie-Name → Modulpfad
STRATEGY_REGISTRY = {
    "ma_crossover": "ma_crossover",
    "momentum": "momentum",
    "rsi": "rsi",
    "bollinger": "bollinger",
    "macd": "macd",
    "ecm": "ecm",
}

def load_strategy(strategy_name: str):
    """
    Lädt die Strategie dynamisch.
    Erwartet: Modul hat eine Funktion generate_signals(df, params)
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unbekannte Strategie '{strategy_name}'. Verfügbar: {list(STRATEGY_REGISTRY.keys())}")

    module_name = STRATEGY_REGISTRY[strategy_name]

    # Dynamisch importieren
    module = __import__(f"src.strategies.{module_name}", fromlist=["generate_signals"])

    return module.generate_signals


__all__ = [
    "STRATEGY_REGISTRY",
    "load_strategy",
]
