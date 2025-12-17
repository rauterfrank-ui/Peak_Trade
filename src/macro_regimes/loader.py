"""
Macro Regime Loader – Peak_Trade.

Lädt und verwaltet die aktuelle Makro-Regime-Konfiguration aus
config/macro_regimes/current.toml.

Verwendung:
    from src.macro_regimes import load_current_macro_regime_config

    cfg = load_current_macro_regime_config()
    print(cfg.get("regime.primary"))      # z.B. "fed_pause"
    print(cfg.get("sizing.max_allocation"))  # z.B. 0.7
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover  # Fallback für ältere Python-Versionen
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_MACRO_REGIME_PATH = Path("config") / "macro_regimes" / "current.toml"


@dataclass(frozen=True)
class MacroRegimeConfig:
    """
    Repräsentiert den Inhalt von config/macro_regimes/current.toml.

    Wir halten das Schema zunächst bewusst flexibel:
    - `raw`: vollständiger TOML-Content als verschachteltes Dict
    - später können wir gezielte Properties hinzufügen (z.B. meta.date, regime.primary)
    """

    path: Path
    raw: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any | None = None) -> Any:
        """
        Convenience-Getter für verschachtelte Keys im Stil 'meta.date' oder 'regime.primary'.

        Beispiel:
            cfg.get("meta.date")
            cfg.get("regime.primary")
            cfg.get("sizing.max_allocation", default=1.0)
        """
        parts = key.split(".")
        current: Any = self.raw
        for part in parts:
            if not isinstance(current, (Mapping, dict)):
                return default
            if part not in current:
                return default
            current = current[part]
        return current


def _load_toml(path: Path) -> Mapping[str, Any]:
    """
    Kapselt das eigentliche TOML-Laden, damit wir es später leichter
    in Tests oder für andere Loader wiederverwenden können.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Macro-regime-Config '{path}' wurde nicht gefunden. "
            "Erwarte eine Datei config/macro_regimes/current.toml."
        )

    # Explizit UTF-8, um Probleme auf verschiedenen Systemen zu vermeiden.
    content = path.read_bytes()
    return tomllib.loads(content.decode("utf-8"))


def load_current_macro_regime_config(
    base_dir: Path | str | None = None,
    *,
    filename: str = "current.toml",
) -> MacroRegimeConfig:
    """
    Lädt die aktuelle Macro-Regime-Briefing-Datei.

    Standardpfad:
        config/macro_regimes/current.toml  (relativ zum Projekt-Root)

    Parameter:
        base_dir:
            - None: verwende das aktuelle Arbeitsverzeichnis ('.')
            - str/Path: Root-Verzeichnis des Projekts (z.B. tmpdir im Test)

        filename:
            - standardmäßig 'current.toml', später z.B. für Archive überschreibbar

    Rückgabe:
        MacroRegimeConfig mit Pfad + rohem TOML-Content.
    """
    root = Path(base_dir) if base_dir is not None else Path(".")
    path = root / "config" / "macro_regimes" / filename

    data = _load_toml(path)
    return MacroRegimeConfig(path=path, raw=data)
