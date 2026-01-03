from __future__ import annotations

# src/core/peak_config.py
"""
Peak_Trade Config Loading (Phase 36 refactored)
================================================

Leichtgewichtiger TOML-basierter Config-Loader.

Verwendung:
    from src.core.peak_config import load_config, load_config_default

    # Expliziter Pfad
    cfg = load_config("config/config.toml")

    # Oder mit ENV-Variable / Default
    cfg = load_config_default()

Environment Variables:
    PEAK_TRADE_CONFIG_PATH: Pfad zu alternativer config.toml

Config-Pfad-Prioritaet:
    1. Explizit uebergebener path-Parameter
    2. Environment Variable PEAK_TRADE_CONFIG_PATH
    3. Default: config/config.toml relativ zum Projekt-Root
"""

import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

try:
    # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    # Fuer Python 3.9/3.10: pip install tomli
    import tomli as tomllib  # type: ignore[assignment]


# Environment Variable fuer Config-Pfad (Phase 36: vereinheitlicht)
PEAK_TRADE_CONFIG_ENV_VAR = "PEAK_TRADE_CONFIG_PATH"

# Projekt-Root ermitteln (relativ zu dieser Datei)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default Config-Pfad
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "config.toml"


@dataclass
class PeakConfig:
    """
    Dünne Hülle um einen verschachtelten Dict aus TOML.

    Zugriff per Punkt-Notation:
    cfg.get("strategy.ma_crossover.fast_window", 20)
    """

    raw: dict

    def get(self, path: str, default: Any = None) -> Any:
        node: Any = self.raw
        for part in path.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def get_nested(self, path: str, default: Any = None) -> Any:
        """Alias für get() für Kompatibilität."""
        return self.get(path, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Gibt eine tiefe Kopie der internen Config-Struktur als Dict zurück.

        Returns:
            Dict mit allen Config-Werten (tiefe Kopie)
        """
        return deepcopy(self.raw)

    def with_overrides(self, updates: Dict[str, Any]) -> PeakConfig:
        """
        Erzeugt eine neue PeakConfig mit überschriebenen Werten.

        Überschreibt einzelne Pfade (dot-notation) in einer Kopie der Config.
        Das Original-Objekt bleibt unverändert.

        Args:
            updates: Dict von "a.b.c" -> Wert

        Returns:
            Neue PeakConfig-Instanz mit überschriebenen Werten

        Example:
            >>> cfg = load_config("config.toml")
            >>> new_cfg = cfg.with_overrides({
            ...     "strategy.ma_crossover.fast_window": 10,
            ...     "strategy.ma_crossover.slow_window": 50
            ... })
            >>> # Original cfg ist unverändert, new_cfg hat die neuen Werte
        """
        # Tiefe Kopie der raw-Daten erstellen
        data = self.to_dict()

        # Jeden Override-Pfad anwenden
        for path, value in updates.items():
            parts = str(path).split(".")
            node = data

            # Navigiere zum vorletzten Teil und erstelle fehlende Knoten
            for key in parts[:-1]:
                if key not in node or not isinstance(node[key], dict):
                    node[key] = {}
                node = node[key]

            # Setze den finalen Wert
            node[parts[-1]] = value

        # Neue PeakConfig-Instanz mit modifizierten Daten erstellen
        return PeakConfig(raw=data)


def resolve_config_path(path: Optional[str | Path] = None) -> Path:
    """
    Bestimmt den Config-Pfad mit folgender Prioritaet:

    1. Explizit uebergebener path-Parameter
    2. Environment Variable PEAK_TRADE_CONFIG_PATH
    3. Default: config/config.toml im Projekt-Root

    Args:
        path: Optional expliziter Pfad

    Returns:
        Aufgeloester Config-Pfad
    """
    # 1. Explizit uebergeben
    if path is not None:
        return Path(path)

    # 2. Environment Variable
    env_path = os.environ.get(PEAK_TRADE_CONFIG_ENV_VAR)
    if env_path:
        return Path(env_path)

    # 3. Default
    return _DEFAULT_CONFIG_PATH


def load_config(path: Optional[str | Path] = None) -> PeakConfig:
    """
    Laedt eine Config-Datei.

    Args:
        path: Pfad zur TOML-Config-Datei (optional)
              Wenn None: nutzt resolve_config_path() (ENV-Variable oder Default)

    Returns:
        PeakConfig-Instanz

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert
        ValueError: Wenn TOML ungueltig

    Example:
        >>> # Mit explizitem Pfad
        >>> cfg = load_config("config/config.toml")

        >>> # Mit ENV-Variable oder Default
        >>> cfg = load_config()
    """
    p = resolve_config_path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {p}")

    with p.open("rb") as f:
        data = tomllib.load(f)

    if not isinstance(data, dict):
        raise ValueError("Erwartet ein TOML-Top-Level-Table (dict).")

    return PeakConfig(raw=data)


def load_config_default() -> PeakConfig:
    """
    Laedt die Standard-Config basierend auf ENV-Variable oder Default-Pfad.

    Prioritaet:
        1. PEAK_TRADE_CONFIG_PATH Environment Variable
        2. config/config.toml im Projekt-Root

    Returns:
        PeakConfig-Instanz

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert

    Example:
        >>> # Mit Environment Variable
        >>> os.environ['PEAK_TRADE_CONFIG_PATH'] = '/custom/config.toml'
        >>> cfg = load_config_default()

        >>> # Ohne ENV-Variable -> nutzt config/config.toml
        >>> cfg = load_config_default()
    """
    config_path = resolve_config_path()
    return load_config(config_path)


def get_project_root() -> Path:
    """
    Gibt das Projekt-Root-Verzeichnis zurueck.

    Returns:
        Path zum Projekt-Root
    """
    return _PROJECT_ROOT
