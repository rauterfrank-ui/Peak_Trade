"""
Strategy-Registry: Zentrale Verwaltung aller Strategien.
"""
from typing import Dict, Type
from .base import BaseStrategy

_REGISTRY: Dict[str, Type[BaseStrategy]] = {}


def register_strategy(cls: Type[BaseStrategy]) -> Type[BaseStrategy]:
    """
    Dekorator zum Registrieren einer Strategie.
    
    Args:
        cls: Strategy-Klasse mit Attribut 'name'
        
    Returns:
        Unveränderte Klasse (Dekorator-Pattern)
        
    Raises:
        ValueError: Wenn 'name' fehlt oder bereits registriert
    """
    if not hasattr(cls, "name"):
        raise ValueError("Strategy-Klasse braucht Attribut 'name'.")
    
    name = getattr(cls, "name")
    
    if not isinstance(name, str) or not name:
        raise ValueError("Strategy-Name muss nicht-leerer String sein.")
    
    if name in _REGISTRY:
        raise ValueError(f"Strategy-Name bereits registriert: {name}")
    
    _REGISTRY[name] = cls
    return cls


def get_strategy(name: str) -> Type[BaseStrategy]:
    """
    Holt Strategy-Klasse aus Registry.
    
    Args:
        name: Name der Strategie
        
    Returns:
        Strategy-Klasse
        
    Raises:
        ValueError: Wenn Name unbekannt
    """
    try:
        return _REGISTRY[name]
    except KeyError as e:
        available = list(_REGISTRY.keys())
        raise ValueError(
            f"Unbekannte Strategie: '{name}'. Verfügbar: {available}"
        ) from e
