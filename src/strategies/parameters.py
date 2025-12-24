"""
Peak_Trade Strategy Parameter Schema
=====================================
Definiert Parameter für Strategy-Tuning und Optimization.

**Use Cases**:
- Optuna Parameter-Search
- Dokumentation (welche Parameter hat eine Strategie?)
- Validation (sind Parameter im erlaubten Bereich?)

**Design-Prinzipien**:
- Leichtgewichtig: Nur Dataclasses
- Optional: Strategien MÜSSEN kein Schema definieren
- Type-Safe: Klare Typen (int, float, choice, bool)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Literal, Optional


@dataclass
class Param:
    """
    Parameter-Definition für Strategy-Tuning.

    Attributes:
        name: Parameter-Name (z.B. "fast_window")
        kind: Parameter-Typ ("int", "float", "choice", "bool")
        default: Default-Wert
        low: Untere Grenze (nur für int/float)
        high: Obere Grenze (nur für int/float)
        choices: Erlaubte Werte (nur für choice)
        description: Optionale Beschreibung

    Example (int):
        >>> Param(name="fast_window", kind="int", default=20, low=5, high=50)

    Example (float):
        >>> Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1)

    Example (choice):
        >>> Param(name="mode", kind="choice", default="fast", choices=["fast", "slow"])

    Example (bool):
        >>> Param(name="use_filter", kind="bool", default=True)
    """

    name: str
    kind: Literal["int", "float", "choice", "bool"]
    default: Any
    low: Optional[float] = None
    high: Optional[float] = None
    choices: Optional[List[Any]] = None
    description: str = ""

    def __post_init__(self):
        """Validiert Parameter-Definition."""
        # Numerische Parameter: low/high müssen gesetzt sein
        if self.kind in ["int", "float"]:
            if self.low is None or self.high is None:
                raise ValueError(
                    f"Parameter '{self.name}' (kind={self.kind}): "
                    f"low und high müssen gesetzt sein"
                )
            if self.low >= self.high:
                raise ValueError(
                    f"Parameter '{self.name}': low ({self.low}) muss < high ({self.high}) sein"
                )

        # Choice-Parameter: choices müssen gesetzt sein
        if self.kind == "choice":
            if self.choices is None or len(self.choices) == 0:
                raise ValueError(
                    f"Parameter '{self.name}' (kind=choice): " f"choices müssen gesetzt sein"
                )
            if self.default not in self.choices:
                raise ValueError(
                    f"Parameter '{self.name}': "
                    f"default '{self.default}' nicht in choices {self.choices}"
                )

        # Bool-Parameter: default muss bool sein
        if self.kind == "bool":
            if not isinstance(self.default, bool):
                raise ValueError(
                    f"Parameter '{self.name}' (kind=bool): "
                    f"default muss bool sein, ist aber {type(self.default)}"
                )

    def validate_value(self, value: Any) -> bool:
        """
        Prüft ob Wert im erlaubten Bereich liegt.

        Args:
            value: Zu prüfender Wert

        Returns:
            True wenn gültig, False sonst
        """
        if self.kind == "int":
            return isinstance(value, int) and self.low <= value <= self.high
        elif self.kind == "float":
            return isinstance(value, (int, float)) and self.low <= value <= self.high
        elif self.kind == "choice":
            return value in self.choices
        elif self.kind == "bool":
            return isinstance(value, bool)
        return False

    def to_optuna_suggest(self, trial: Any) -> Any:
        """
        Konvertiert Parameter zu Optuna Trial.suggest_*() Call.

        Args:
            trial: Optuna Trial-Instanz

        Returns:
            Vorgeschlagener Wert

        Raises:
            ImportError: Wenn optuna nicht installiert

        Note:
            Benötigt optuna als Dependency. Nur für Study-Runner relevant.
        """
        if self.kind == "int":
            return trial.suggest_int(self.name, int(self.low), int(self.high))
        elif self.kind == "float":
            return trial.suggest_float(self.name, self.low, self.high)
        elif self.kind == "choice":
            return trial.suggest_categorical(self.name, self.choices)
        elif self.kind == "bool":
            return trial.suggest_categorical(self.name, [False, True])
        else:
            raise ValueError(f"Unknown param kind: {self.kind}")


def validate_schema(params: List[Param]) -> None:
    """
    Validiert Parameter-Schema.

    Args:
        params: Liste von Param-Definitionen

    Raises:
        ValueError: Wenn Schema ungültig ist

    Example:
        >>> schema = [
        ...     Param(name="window", kind="int", default=20, low=5, high=50),
        ... ]
        >>> validate_schema(schema)  # OK
        >>>
        >>> bad_schema = [
        ...     Param(name="window", kind="int", default=20),  # low/high fehlen
        ... ]
        >>> validate_schema(bad_schema)  # ValueError
    """
    if not params:
        return  # Empty schema ist OK

    names = set()
    for param in params:
        # Check: Keine doppelten Namen
        if param.name in names:
            raise ValueError(f"Duplicate parameter name: '{param.name}'")
        names.add(param.name)

        # Param validiert sich selbst via __post_init__
        # Hier nur zusätzliche Schema-Level Checks

    # Success: Schema ist valide


def extract_defaults(params: List[Param]) -> dict:
    """
    Extrahiert Default-Werte aus Parameter-Schema.

    Args:
        params: Parameter-Schema

    Returns:
        Dict {name -> default}

    Example:
        >>> schema = [
        ...     Param(name="window", kind="int", default=20, low=5, high=50),
        ...     Param(name="threshold", kind="float", default=0.02, low=0.01, high=0.1),
        ... ]
        >>> extract_defaults(schema)
        {'window': 20, 'threshold': 0.02}
    """
    return {p.name: p.default for p in params}


__all__ = [
    "Param",
    "validate_schema",
    "extract_defaults",
]
