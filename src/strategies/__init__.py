"""
Peak_Trade – Strategy Loader
Alle Strategien werden hier registriert.
"""

# Mapping: Strategie-Name → Modulpfad
# WICHTIG: Namen müssen mit [strategy.*] in config.toml übereinstimmen
STRATEGY_REGISTRY = {
    "ma_crossover": "ma_crossover",
    "momentum_1h": "momentum",  # Strategie-Name != Modul-Name
    "rsi_strategy": "rsi",  # Strategie-Name != Modul-Name
    "bollinger_bands": "bollinger",  # Strategie-Name != Modul-Name
    "macd": "macd",
    "ecm_cycle": "ecm",  # Strategie-Name != Modul-Name
    # Phase 18: Research Playground Baselines
    "trend_following": "trend_following",
    "mean_reversion": "mean_reversion",
    "my_strategy": "my_strategy",
    # Phase 27: Strategy Research Track
    "vol_breakout": "vol_breakout",
    "mean_reversion_channel": "mean_reversion_channel",
    "rsi_reversion": "rsi_reversion",
    # Phase 40: Strategy Library & Portfolio-Track v1
    "breakout": "breakout",
    "breakout_donchian": "breakout_donchian",
    "vol_regime_filter": "vol_regime_filter",
    "composite": "composite",
    "regime_aware_portfolio": "regime_aware_portfolio",
    # Research-Track: R&D-Only Strategien
    "armstrong_cycle": "armstrong.armstrong_cycle_strategy",
    "el_karoui_vol_model": "el_karoui.el_karoui_vol_model_strategy",
    "ehlers_cycle_filter": "ehlers.ehlers_cycle_filter_strategy",
    "meta_labeling": "lopez_de_prado.meta_labeling_strategy",
    # R&D-Skeleton Strategien (Platzhalter)
    "bouchaud_microstructure": "bouchaud.bouchaud_microstructure_strategy",
    "vol_regime_overlay": "gatheral_cont.vol_regime_overlay_strategy",
}


def load_strategy(strategy_name: str):
    """
    Lädt die Strategie dynamisch.
    Erwartet: Modul hat eine Funktion generate_signals(df, params)
    oder eine OOP-Strategie in der Registry (Fallback).
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unbekannte Strategie '{strategy_name}'. Verfügbar: {list(STRATEGY_REGISTRY.keys())}"
        )

    module_name = STRATEGY_REGISTRY[strategy_name]

    # Dynamisch importieren
    module = __import__(f"src.strategies.{module_name}", fromlist=["generate_signals"])

    if hasattr(module, "generate_signals") and callable(module.generate_signals):
        return module.generate_signals

    try:
        from src.strategies.registry import get_strategy_spec

        spec = get_strategy_spec(strategy_name)
    except KeyError as exc:
        raise ValueError(
            f"Strategie '{strategy_name}' hat keine generate_signals-Funktion "
            f"und ist nicht in der OOP-Registry registriert."
        ) from exc

    strategy_cls = spec.cls

    def generate_signals(df, params):
        strategy = strategy_cls(config=dict(params))
        return strategy.generate_signals(df)

    return generate_signals


__all__ = [
    "STRATEGY_REGISTRY",
    "load_strategy",
]
