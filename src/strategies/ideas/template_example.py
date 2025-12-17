"""
Template für Idea-Strategien
=============================
Diese Datei dient als Blaupause für neue Strategien im Sandbox-Bereich.

Workflow:
1. Mit `scripts/new_idea_strategy.py --name my_idea` eine Kopie erstellen
2. Diese Vorlage anpassen (Indikatoren, Logik, Parameter)
3. Mit `scripts/run_idea_strategy.py --module my_idea --symbol BTC/EUR` testen
4. Iterieren bis zufrieden
5. Optional: in die Haupt-Registry übernehmen
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


class IdeaExampleStrategy(BaseStrategy):
    """
    Template für eine neue Idea-Strategie.

    TODO: Beschreibe hier deine Strategie-Logik:
    - Welche Indikatoren nutzt sie?
    - Welche Entry-/Exit-Regeln?
    - Welche Parameter sind wichtig?

    Args:
        param1: Beispiel-Parameter 1 (z.B. Window-Größe)
        param2: Beispiel-Parameter 2 (z.B. Threshold)
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = IdeaExampleStrategy(param1=20, param2=0.02)
        >>> signals = strategy.generate_signals(df)
    """

    def __init__(
        self,
        param1: int = 20,
        param2: float = 0.02,
        price_col: str = "close",
        config: dict[str, Any] | None = None,
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """
        Initialisiert die Idea-Strategie.

        Args:
            param1: TODO: Beschreibe param1
            param2: TODO: Beschreibe param2
            price_col: Preis-Spalte
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "param1": param1,
            "param2": param2,
            "price_col": price_col,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="IdeaExample",
                description="Template für neue Strategien",
                version="0.1.0",
                author="Peak_Trade",
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.param1 = self.config.get("param1", param1)
        self.param2 = self.config.get("param2", param2)
        self.price_col = self.config.get("price_col", price_col)

        # Optional: Parameter validieren
        self._validate_params()

    def _validate_params(self) -> None:
        """
        Validiert Parameter.

        TODO: Füge hier deine Validierungslogik hinzu:
        - Sind Parameter im erlaubten Bereich?
        - Sind Kombinationen gültig?
        """
        if self.param1 < 1:
            raise ValueError(f"param1 muss >= 1 sein, ist {self.param1}")
        if self.param2 <= 0:
            raise ValueError(f"param2 muss > 0 sein, ist {self.param2}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        TODO: Implementiere hier deine Strategie-Logik!

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens self.price_col)

        Returns:
            Series mit Signalen:
            - 1  = long
            - -1 = short (falls du short-Signale unterstützt)
            - 0  = flat
            Index muss identisch zu data.index sein

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = self.param1  # Beispiel: Mindestens param1 Bars benötigt
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mindestens {min_bars} Bars, habe nur {len(data)}"
            )

        # Kopie für Berechnungen
        df = data.copy()

        # ====================================================================
        # TODO: DEINE STRATEGIE-LOGIK HIER
        # ====================================================================

        # Beispiel 1: Indikatoren berechnen
        # df["sma"] = df[self.price_col].rolling(self.param1).mean()
        # df["std"] = df[self.price_col].rolling(self.param1).std()

        # Beispiel 2: Entry-/Exit-Bedingungen definieren
        # long_entry = df["close"] > df["sma"] + self.param2 * df["std"]
        # long_exit = df["close"] < df["sma"]

        # Beispiel 3: Signale aus Events erzeugen
        # events = pd.Series(0, index=df.index, dtype=int)
        # events[long_entry] = 1
        # events[long_exit] = -1

        # Beispiel 4: Event → State (1=long, 0=flat)
        # state = events.replace({-1: 0})
        # state = state.replace(0, pd.NA).ffill().fillna(0)
        # state = state.infer_objects(copy=False).astype(int)

        # ====================================================================
        # PLACEHOLDER: Gib erstmal nur 0 (flat) zurück
        # ====================================================================
        signals = pd.Series(0, index=df.index, dtype=int)

        return signals

    def get_config_dict(self) -> dict[str, Any]:
        """
        Gibt Config als Dict zurück (nützlich für Logging/Experiment-Tracking).

        Returns:
            Dict mit allen relevanten Parametern
        """
        return {
            "param1": self.param1,
            "param2": self.param2,
            "price_col": self.price_col,
        }


# ============================================================================
# HELPER (Optional)
# ============================================================================

def create_strategy_from_params(**kwargs) -> IdeaExampleStrategy:
    """
    Helper-Funktion zum Erstellen einer Strategie aus Keyword-Args.

    Beispiel:
        >>> strat = create_strategy_from_params(param1=10, param2=0.01)
    """
    return IdeaExampleStrategy(**kwargs)
