#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/new_idea_strategy.py
"""
Peak_Trade: Generator für neue Idea-Strategien
===============================================

Erstellt eine neue Strategie-Datei im `src/strategies/ideas/` Verzeichnis
basierend auf dem Template.

Usage:
    python scripts/new_idea_strategy.py --name rsi_keltner
    python scripts/new_idea_strategy.py --name rsi_keltner --title "RSI + Keltner Reversion"
"""

from __future__ import annotations

import sys
import argparse
import keyword
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Erstellt neue Idea-Strategie aus Template.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Strategie-Name in snake_case (z.B. 'rsi_keltner'). Wird zu Dateinamen und Klassennamen.",
    )
    parser.add_argument(
        "--title",
        help="Optional: Human-readable Titel für Metadata (z.B. 'RSI + Keltner Reversion').",
    )
    return parser.parse_args(argv)


def snake_to_camel(snake_str: str) -> str:
    """
    Konvertiert snake_case zu CamelCase.

    Args:
        snake_str: String in snake_case (z.B. "rsi_keltner")

    Returns:
        String in CamelCase (z.B. "RsiKeltner")

    Example:
        >>> snake_to_camel("rsi_keltner")
        'RsiKeltner'
        >>> snake_to_camel("ma_crossover")
        'MaCrossover'
    """
    components = snake_str.split("_")
    return "".join(c.capitalize() for c in components)


def sanitize_name(name: str) -> str:
    """
    Bereinigt und validiert den Strategie-Namen.

    Args:
        name: Roher Strategie-Name

    Returns:
        Bereinigter snake_case Name

    Raises:
        ValueError: Wenn Name ungültig ist
    """
    # Whitespace entfernen
    name = name.strip()

    # Nur alphanumerisch und Underscores erlauben
    if not all(c.isalnum() or c == "_" for c in name):
        raise ValueError(f"Name darf nur Buchstaben, Zahlen und Underscores enthalten: {name!r}")

    # Darf nicht mit Ziffer beginnen
    if name and name[0].isdigit():
        raise ValueError(f"Name darf nicht mit Ziffer beginnen: {name!r}")

    # Darf kein Python-Keyword sein
    if keyword.iskeyword(name):
        raise ValueError(f"Name darf kein Python-Keyword sein: {name!r}")

    # In lowercase konvertieren
    name = name.lower()

    return name


def build_template(module_name: str, class_name: str, title: str) -> str:
    """
    Baut Python-Code für neue Strategie-Datei.

    Args:
        module_name: Dateiname ohne .py (snake_case)
        class_name: Klassenname (CamelCase)
        title: Human-readable Titel

    Returns:
        Vollständiger Python-Code als String
    """
    template = f'''"""
{title}
{"=" * len(title)}

TODO: Beschreibe hier deine Strategie-Idee:
- Welches Konzept verfolgst du?
- Welche Indikatoren/Signale nutzt du?
- Welche Parameter sind wichtig?
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from ..base import BaseStrategy, StrategyMetadata


class {class_name}Strategy(BaseStrategy):
    """
    {title} Strategy.

    TODO: Füge hier eine detaillierte Beschreibung hinzu:
    - Entry-Regeln
    - Exit-Regeln
    - Parameter-Beschreibung

    Args:
        param1: TODO: Beschreibe param1 (z.B. Window-Größe)
        param2: TODO: Beschreibe param2 (z.B. Threshold)
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = {class_name}Strategy(param1=20, param2=0.02)
        >>> signals = strategy.generate_signals(df)
    """

    def __init__(
        self,
        param1: int = 20,
        param2: float = 0.02,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert {title} Strategy.

        Args:
            param1: TODO: Beschreibe param1
            param2: TODO: Beschreibe param2
            price_col: Preis-Spalte
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {{
            "param1": param1,
            "param2": param2,
            "price_col": price_col,
        }}

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="{title}",
                description="{title} Strategy",
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
            raise ValueError(f"param1 muss >= 1 sein, ist {{self.param1}}")
        if self.param2 <= 0:
            raise ValueError(f"param2 muss > 0 sein, ist {{self.param2}}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        TODO: Implementiere hier deine Strategie-Logik!

        Schritte:
        1. Indikatoren berechnen (z.B. RSI, Bollinger Bands, Keltner Channels)
        2. Entry-/Exit-Bedingungen definieren
        3. Signale aus Events erzeugen
        4. Event → State konvertieren (1=long, 0=flat, -1=short)

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
                f"Spalte '{{self.price_col}}' nicht in DataFrame. "
                f"Verfügbar: {{list(data.columns)}}"
            )

        min_bars = self.param1  # Beispiel: Mindestens param1 Bars benötigt
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mindestens {{min_bars}} Bars, habe nur {{len(data)}}"
            )

        # Kopie für Berechnungen
        df = data.copy()

        # ====================================================================
        # TODO: DEINE STRATEGIE-LOGIK HIER
        # ====================================================================

        # Beispiel: Indikatoren berechnen
        # df["rsi"] = compute_rsi(df[self.price_col], window=14)
        # df["upper_band"], df["lower_band"] = compute_keltner_channels(df, atr_mult=2.0)

        # Beispiel: Entry-/Exit-Bedingungen
        # long_entry = (df["rsi"] < 30) & (df["close"] < df["lower_band"])
        # long_exit = df["rsi"] > 70

        # Beispiel: Signale aus Events erzeugen
        # events = pd.Series(0, index=df.index, dtype=int)
        # events[long_entry] = 1
        # events[long_exit] = -1

        # Beispiel: Event → State (1=long, 0=flat)
        # state = events.replace({{-1: 0}})
        # state = state.replace(0, pd.NA).ffill().fillna(0)
        # state = state.infer_objects(copy=False).astype(int)

        # ====================================================================
        # PLACEHOLDER: Gib erstmal nur 0 (flat) zurück
        # ====================================================================
        signals = pd.Series(0, index=df.index, dtype=int)

        return signals

    def get_config_dict(self) -> Dict[str, Any]:
        """
        Gibt Config als Dict zurück (nützlich für Logging/Experiment-Tracking).

        Returns:
            Dict mit allen relevanten Parametern
        """
        return {{
            "param1": self.param1,
            "param2": self.param2,
            "price_col": self.price_col,
        }}


# ============================================================================
# HELPER (Optional)
# ============================================================================

def create_strategy_from_params(**kwargs) -> {class_name}Strategy:
    """
    Helper-Funktion zum Erstellen einer Strategie aus Keyword-Args.

    Beispiel:
        >>> strat = create_strategy_from_params(param1=10, param2=0.01)
    """
    return {class_name}Strategy(**kwargs)
'''
    return template


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n🚀 Peak_Trade Idea Strategy Generator")
    print("=" * 70)

    # Name bereinigen
    try:
        module_name = sanitize_name(args.name)
    except ValueError as e:
        print(f"\n❌ Fehler: {e}")
        sys.exit(1)

    class_name = snake_to_camel(module_name)
    title = args.title or f"{class_name} Strategy"

    print(f"\n📝 Erstelle neue Strategie:")
    print(f"  - Modul-Name (Datei): {module_name}.py")
    print(f"  - Klassen-Name: {class_name}Strategy")
    print(f"  - Titel: {title}")

    # Zieldatei
    ideas_dir = Path(__file__).parent.parent / "src" / "strategies" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)

    out_file = ideas_dir / f"{module_name}.py"

    # Prüfen ob Datei bereits existiert
    if out_file.exists():
        print(f"\n❌ Fehler: Datei existiert bereits: {out_file}")
        print("  Tipp: Wähle einen anderen Namen oder lösche die alte Datei.")
        sys.exit(1)

    # Template generieren
    code = build_template(module_name, class_name, title)

    # Datei schreiben
    out_file.write_text(code, encoding="utf-8")

    print(f"\n✅ Strategie-Datei erstellt: {out_file}")
    print(f"\n📚 Nächste Schritte:")
    print(f"  1. Öffne {out_file}")
    print(f"  2. Implementiere generate_signals() (suche nach TODO-Kommentaren)")
    print(f"  3. Teste mit: python scripts/run_idea_strategy.py \\")
    print(f"       --module {module_name} \\")
    print(f"       --symbol BTC/EUR \\")
    print(f"       --run-name idea_{module_name}_test")
    print(f"\n🎉 Viel Erfolg mit deiner Strategie!\n")


if __name__ == "__main__":
    main()
