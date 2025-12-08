# src/experiments/r_and_d_presets.py
"""
Peak_Trade R&D Preset Loader (Phase 75 – Wave v2)
=================================================

Lädt R&D-Presets aus config/r_and_d_presets.toml für Offline-Experimente.

Verwendung:
    from src.experiments.r_and_d_presets import (
        load_r_and_d_preset,
        list_r_and_d_presets,
        RnDPresetConfig,
    )

    # Preset laden
    preset = load_r_and_d_preset("armstrong_ecm_btc_longterm_v1")

    # Alle Presets auflisten
    presets = list_r_and_d_presets()
"""
from __future__ import annotations

# Python 3.11+ hat tomllib, davor brauchen wir tomli oder toml
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        import toml as tomllib  # type: ignore

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Standard-Pfad zur R&D-Presets-Datei
DEFAULT_R_AND_D_PRESETS_PATH = Path(__file__).parent.parent.parent / "config" / "r_and_d_presets.toml"


@dataclass
class RnDPresetConfig:
    """
    Konfiguration für ein R&D-Experiment-Preset.

    Attributes:
        preset_id: Eindeutige ID des Presets (z.B. "armstrong_ecm_btc_longterm_v1")
        description: Kurzbeschreibung
        strategy: Strategy-ID aus der Registry (z.B. "armstrong_cycle")
        tier: Tier-Level (immer "r_and_d" für R&D-Presets)
        enabled: Ob das Preset aktiviert ist
        experimental: Experimentell-Flag
        allow_live: Ob Live-Trading erlaubt ist (immer False für R&D)
        markets: Liste von Märkten (z.B. ["BTC/USDT"])
        timeframes: Liste von Timeframes (z.B. ["1h", "4h"])
        hypothesis: Forschungshypothese
        focus_metrics: Liste relevanter Metriken
        parameters: Strategy-spezifische Parameter
        default_from: Default-Startdatum
        default_to: Default-Enddatum
    """
    preset_id: str
    description: str = ""
    strategy: str = ""
    tier: str = "r_and_d"
    enabled: bool = False
    experimental: bool = True
    allow_live: bool = False
    markets: List[str] = field(default_factory=lambda: ["BTC/USDT"])
    timeframes: List[str] = field(default_factory=lambda: ["1h"])
    hypothesis: str = ""
    focus_metrics: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    default_from: Optional[str] = None
    default_to: Optional[str] = None

    @property
    def default_symbol(self) -> str:
        """Gibt das erste Market als Default-Symbol zurück."""
        return self.markets[0] if self.markets else "BTC/USDT"

    @property
    def default_timeframe(self) -> str:
        """Gibt den ersten Timeframe als Default zurück."""
        return self.timeframes[0] if self.timeframes else "1h"

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "preset_id": self.preset_id,
            "description": self.description,
            "strategy": self.strategy,
            "tier": self.tier,
            "enabled": self.enabled,
            "experimental": self.experimental,
            "allow_live": self.allow_live,
            "markets": self.markets,
            "timeframes": self.timeframes,
            "hypothesis": self.hypothesis,
            "focus_metrics": self.focus_metrics,
            "parameters": self.parameters,
            "default_from": self.default_from,
            "default_to": self.default_to,
        }


def _load_presets_toml(path: Optional[Path] = None) -> Dict[str, Any]:
    """Lädt die R&D-Presets-TOML-Datei."""
    preset_path = path or DEFAULT_R_AND_D_PRESETS_PATH
    if not preset_path.exists():
        raise FileNotFoundError(f"R&D-Presets-Datei nicht gefunden: {preset_path}")
    
    # tomllib (Python 3.11+) und tomli brauchen binary mode
    # toml (legacy) braucht text mode
    try:
        with open(preset_path, "rb") as f:
            return tomllib.load(f)
    except TypeError:
        # Fallback für toml (text mode)
        with open(preset_path, "r") as f:
            return tomllib.load(f)  # type: ignore


def load_r_and_d_preset(
    preset_id: str,
    path: Optional[Path] = None,
) -> RnDPresetConfig:
    """
    Lädt ein einzelnes R&D-Preset anhand der ID.

    Args:
        preset_id: ID des Presets (z.B. "armstrong_ecm_btc_longterm_v1")
        path: Optionaler Pfad zur TOML-Datei

    Returns:
        RnDPresetConfig mit allen Preset-Daten

    Raises:
        KeyError: Wenn das Preset nicht existiert
        FileNotFoundError: Wenn die TOML-Datei nicht gefunden wird
    """
    data = _load_presets_toml(path)

    if "preset" not in data:
        raise KeyError("Keine [preset.*] Sektionen in der TOML-Datei gefunden")

    presets = data["preset"]
    if preset_id not in presets:
        available = ", ".join(sorted(presets.keys()))
        raise KeyError(f"Preset '{preset_id}' nicht gefunden. Verfügbar: {available}")

    preset_data = presets[preset_id]

    # Parameter extrahieren (falls als Untersektion)
    parameters = preset_data.get("parameters", {})

    return RnDPresetConfig(
        preset_id=preset_id,
        description=preset_data.get("description", ""),
        strategy=preset_data.get("strategy", ""),
        tier=preset_data.get("tier", "r_and_d"),
        enabled=preset_data.get("enabled", False),
        experimental=preset_data.get("experimental", True),
        allow_live=preset_data.get("allow_live", False),
        markets=preset_data.get("markets", ["BTC/USDT"]),
        timeframes=preset_data.get("timeframes", ["1h"]),
        hypothesis=preset_data.get("hypothesis", ""),
        focus_metrics=preset_data.get("focus_metrics", []),
        parameters=parameters,
        default_from=preset_data.get("default_from"),
        default_to=preset_data.get("default_to"),
    )


def list_r_and_d_presets(path: Optional[Path] = None) -> List[RnDPresetConfig]:
    """
    Listet alle verfügbaren R&D-Presets auf.

    Args:
        path: Optionaler Pfad zur TOML-Datei

    Returns:
        Liste aller RnDPresetConfig-Objekte
    """
    data = _load_presets_toml(path)

    if "preset" not in data:
        return []

    presets = []
    for preset_id, preset_data in data["preset"].items():
        try:
            preset = load_r_and_d_preset(preset_id, path)
            presets.append(preset)
        except Exception:
            continue

    return presets


def get_preset_ids(path: Optional[Path] = None) -> List[str]:
    """
    Gibt alle Preset-IDs zurück.

    Args:
        path: Optionaler Pfad zur TOML-Datei

    Returns:
        Liste aller Preset-IDs
    """
    data = _load_presets_toml(path)
    if "preset" not in data:
        return []
    return sorted(data["preset"].keys())


def print_preset_catalog(path: Optional[Path] = None) -> None:
    """Gibt einen formatierten Katalog aller R&D-Presets aus."""
    presets = list_r_and_d_presets(path)

    print("\n" + "=" * 70)
    print("R&D Strategy Presets (Wave v2)")
    print("=" * 70)

    # Gruppiere nach Strategy
    by_strategy: Dict[str, List[RnDPresetConfig]] = {}
    for preset in presets:
        strategy = preset.strategy or "unknown"
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(preset)

    for strategy in sorted(by_strategy.keys()):
        print(f"\n### {strategy}")
        print("-" * 40)
        for preset in by_strategy[strategy]:
            markets = ", ".join(preset.markets[:2])
            timeframes = ", ".join(preset.timeframes[:2])
            print(f"  {preset.preset_id}")
            print(f"    → {preset.description}")
            print(f"    → Markets: {markets} | TF: {timeframes}")
            if preset.hypothesis:
                print(f"    → Hypothese: {preset.hypothesis[:60]}...")

    print("\n" + "=" * 70)
    print(f"Gesamt: {len(presets)} R&D-Presets")
    print("=" * 70 + "\n")
