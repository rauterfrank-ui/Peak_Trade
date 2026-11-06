"""
Peak_Trade – Strategy Loader

Canonical strategy resolution is owned by src.strategies.registry.
STRATEGY_REGISTRY is a deprecated compatibility view of loader module refs.
"""

from __future__ import annotations

from src.strategies.registry import (
    StrategyRegistryError,
    get_loader_module_map,
    resolve_strategy_id,
)

# Deprecated compatibility surface — derived from canonical registry snapshot owner.
STRATEGY_REGISTRY = get_loader_module_map()


def load_strategy(strategy_name: str):
    """
    Load strategy signal callable via canonical registry resolution (fail-closed).
    """
    try:
        resolution = resolve_strategy_id(strategy_name)
    except StrategyRegistryError as exc:
        raise ValueError(
            f"Unbekannte Strategie '{strategy_name}'. Verfügbar: {list(STRATEGY_REGISTRY.keys())}"
        ) from exc
    module_name = get_loader_module_map()[resolution.canonical_strategy_id]

    module = __import__(f"src.strategies.{module_name}", fromlist=["generate_signals"])

    if hasattr(module, "generate_signals") and callable(module.generate_signals):
        return module.generate_signals

    from src.strategies.registry import get_strategy_spec

    try:
        spec = get_strategy_spec(resolution.canonical_strategy_id)
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
    "StrategyRegistryError",
    "load_strategy",
    "resolve_strategy_id",
]
