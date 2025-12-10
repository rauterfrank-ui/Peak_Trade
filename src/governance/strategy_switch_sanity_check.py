"""
Strategy-Switch Sanity Check für Peak_Trade.

Governance-Prüfung für die [live_profile.strategy_switch] Konfiguration.
Prüft:
  1. active_strategy_id ist in der allowed-Liste
  2. Keine R&D-Strategien (tier=r_and_d / is_live_ready=False) in allowed
  3. Keine unbekannten Strategy-IDs in allowed (gegen Registry validiert)

KEINE Änderungen an der Config – nur Validierung und Status-Reporting.

Stand: Dezember 2024
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional

# Python 3.11+: tomllib ist built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError(
            "Python <3.11 benötigt 'tomli' package: pip install tomli"
        )


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class StrategySwitchSanityResult:
    """
    Ergebnis des Strategy-Switch Sanity Checks.

    Attributes:
        status: "OK" | "WARN" | "FAIL"
        active_strategy_id: Aktuell konfigurierte aktive Strategie
        allowed: Liste der erlaubten Strategien
        invalid_strategies: Strategy-IDs die nicht in der Registry existieren
        r_and_d_strategies: R&D-Strategien die fälschlicherweise in allowed sind
        messages: Liste von Meldungen (Fehler, Warnungen, Infos)
        config_path: Verwendeter Config-Pfad
    """

    status: Literal["OK", "WARN", "FAIL"]
    active_strategy_id: str
    allowed: List[str]
    invalid_strategies: List[str]
    r_and_d_strategies: List[str]
    messages: List[str]
    config_path: str = ""

    @property
    def ok(self) -> bool:
        """True wenn status == 'OK'."""
        return self.status == "OK"

    @property
    def has_failures(self) -> bool:
        """True wenn status == 'FAIL'."""
        return self.status == "FAIL"

    @property
    def has_warnings(self) -> bool:
        """True wenn status == 'WARN'."""
        return self.status == "WARN"


@dataclass
class StrategyMeta:
    """
    Metadaten einer Strategie für Governance-Prüfung.

    Attributes:
        key: Strategie-Key (z.B. "ma_crossover")
        tier: Strategie-Tier ("core", "r_and_d", "experimental", etc.)
        is_live_ready: Ob die Strategie für Live-Trading freigegeben ist
        allowed_environments: Liste erlaubter Umgebungen
    """

    key: str
    tier: str = "core"
    is_live_ready: bool = True
    allowed_environments: List[str] = field(default_factory=lambda: ["live", "testnet", "paper"])


# ============================================================================
# Registry Integration
# ============================================================================


def _get_registry_strategy_keys() -> List[str]:
    """
    Holt alle verfügbaren Strategy-Keys aus der Registry.

    Returns:
        Liste aller registrierten Strategy-Keys
    """
    try:
        from src.strategies.registry import get_available_strategy_keys
        return get_available_strategy_keys()
    except ImportError:
        # Fallback wenn Registry nicht verfügbar
        return []


def _build_strategy_meta_from_config(
    config: Dict[str, Any],
    registry_keys: List[str],
    r_and_d_keys: List[str],
) -> Dict[str, StrategyMeta]:
    """
    Baut ein Strategy-Meta-Mapping aus Config und Registry.

    Nutzt:
      - Registry für bekannte Strategy-Keys
      - Config-Blöcke [strategy.<key>] für tier/is_live_ready
      - Fallback-Liste für bekannte R&D-Strategien

    Args:
        config: Geladene TOML-Config
        registry_keys: Liste der Registry-Keys
        r_and_d_keys: Bekannte R&D-Strategy-Keys

    Returns:
        Mapping {strategy_key: StrategyMeta}
    """
    meta_map: Dict[str, StrategyMeta] = {}

    for key in registry_keys:
        # Versuche Config-Block zu laden
        strategy_cfg = config.get("strategy", {}).get(key, {})

        tier = strategy_cfg.get("tier", "core")
        is_live_ready = strategy_cfg.get("is_live_ready", True)
        allowed_envs = strategy_cfg.get(
            "allowed_environments",
            ["live", "testnet", "paper", "offline_backtest"]
        )

        # Override für bekannte R&D-Strategien
        if key in r_and_d_keys:
            tier = "r_and_d"
            is_live_ready = False

        meta_map[key] = StrategyMeta(
            key=key,
            tier=tier,
            is_live_ready=is_live_ready,
            allowed_environments=allowed_envs,
        )

    return meta_map


# ============================================================================
# Main Function
# ============================================================================


def run_strategy_switch_sanity_check(
    config_path: str = "config/config.toml",
    section_path: str = "live_profile.strategy_switch",
    r_and_d_strategy_keys: Optional[List[str]] = None,
    max_allowed_strategies_warn: int = 5,
) -> StrategySwitchSanityResult:
    """
    Führt den Strategy-Switch Sanity Check durch.

    Prüft die [live_profile.strategy_switch]-Sektion:
      1. active_strategy_id ist in allowed
      2. Keine R&D-Strategien in allowed (tier=r_and_d oder is_live_ready=False)
      3. Keine unbekannten Strategy-IDs in allowed (nicht in Registry)

    Args:
        config_path: Pfad zur Haupt-Config (default: config/config.toml)
        section_path: TOML-Pfad zur strategy_switch Sektion
        r_and_d_strategy_keys: Liste bekannter R&D-Strategie-Keys
        max_allowed_strategies_warn: Bei mehr als N Strategien in allowed → WARN

    Returns:
        StrategySwitchSanityResult mit status, messages, Details

    Example:
        >>> result = run_strategy_switch_sanity_check()
        >>> print(result.status)
        'OK'
        >>> print(result.messages)
        ['Strategy-Switch-Konfiguration sieht gesund aus.']
    """
    messages: List[str] = []

    # Default R&D-Keys
    if r_and_d_strategy_keys is None:
        r_and_d_strategy_keys = [
            "armstrong_cycle",
            "el_karoui_vol_model",
            "ehlers_cycle_filter",
            "meta_labeling",
            "bouchaud_microstructure",
            "vol_regime_overlay",
        ]

    # 1) Config laden
    path = Path(config_path)
    if not path.exists():
        return StrategySwitchSanityResult(
            status="FAIL",
            active_strategy_id="",
            allowed=[],
            invalid_strategies=[],
            r_and_d_strategies=[],
            messages=[f"Config-Datei nicht gefunden: {config_path}"],
            config_path=config_path,
        )

    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
    except Exception as e:
        return StrategySwitchSanityResult(
            status="FAIL",
            active_strategy_id="",
            allowed=[],
            invalid_strategies=[],
            r_and_d_strategies=[],
            messages=[f"Config-Parse-Fehler: {e}"],
            config_path=config_path,
        )

    # 2) Navigiere zum section_path
    parts = section_path.split(".")
    current: Any = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return StrategySwitchSanityResult(
                status="FAIL",
                active_strategy_id="",
                allowed=[],
                invalid_strategies=[],
                r_and_d_strategies=[],
                messages=[f"Sektion '{section_path}' nicht in Config gefunden"],
                config_path=config_path,
            )

    if not isinstance(current, dict):
        return StrategySwitchSanityResult(
            status="FAIL",
            active_strategy_id="",
            allowed=[],
            invalid_strategies=[],
            r_and_d_strategies=[],
            messages=[f"Sektion '{section_path}' ist keine TOML-Table"],
            config_path=config_path,
        )

    # 3) Werte extrahieren
    active_strategy_id = current.get("active_strategy_id", "")
    allowed = list(current.get("allowed", []))

    # 4) Registry und Meta laden
    registry_keys = _get_registry_strategy_keys()
    strategy_meta = _build_strategy_meta_from_config(
        config=config,
        registry_keys=registry_keys,
        r_and_d_keys=r_and_d_strategy_keys,
    )

    invalid_strategies: List[str] = []
    r_and_d_strategies: List[str] = []
    hard_fail = False

    # 5) Basis-Checks

    # Check: allowed darf nicht leer sein
    if not allowed:
        messages.append("allowed-Liste ist leer – kein Strategy-Switch möglich.")
        hard_fail = True

    # Check: active_strategy_id muss in allowed sein
    if active_strategy_id and active_strategy_id not in allowed:
        messages.append(
            f"active_strategy_id '{active_strategy_id}' ist NICHT in der allowed-Liste."
        )
        hard_fail = True

    # 6) allowed-Liste gegen Registry prüfen
    for sid in allowed:
        # Check: Existiert die Strategie in der Registry?
        if registry_keys and sid not in registry_keys:
            invalid_strategies.append(sid)
            continue

        # Check: Ist die Strategie R&D / nicht live-ready?
        meta = strategy_meta.get(sid)
        if meta is not None:
            is_r_and_d = meta.tier == "r_and_d"
            is_not_live_ready = not meta.is_live_ready

            if is_r_and_d or is_not_live_ready:
                r_and_d_strategies.append(sid)

    # 7) Violation-Messages
    if invalid_strategies:
        messages.append(
            f"Unbekannte Strategy-IDs in allowed (nicht in Registry): "
            f"{', '.join(invalid_strategies)}"
        )
        hard_fail = True

    if r_and_d_strategies:
        messages.append(
            f"R&D- oder nicht-live-ready-Strategien in allowed: "
            f"{', '.join(r_and_d_strategies)}"
        )
        hard_fail = True

    # 8) Status bestimmen
    status: Literal["OK", "WARN", "FAIL"]

    if hard_fail:
        status = "FAIL"
    elif len(allowed) == 0:
        # Sollte oben schon als FAIL markiert sein, aber für Klarheit
        status = "WARN"
    elif len(allowed) > max_allowed_strategies_warn:
        status = "WARN"
        messages.append(
            f"allowed-Liste enthält {len(allowed)} Strategien – "
            f"bitte bewusst überprüfen (Threshold: {max_allowed_strategies_warn})."
        )
    else:
        status = "OK"
        if not messages:
            messages.append("Strategy-Switch-Konfiguration sieht gesund aus.")

    return StrategySwitchSanityResult(
        status=status,
        active_strategy_id=active_strategy_id,
        allowed=allowed,
        invalid_strategies=invalid_strategies,
        r_and_d_strategies=r_and_d_strategies,
        messages=messages,
        config_path=config_path,
    )


# ============================================================================
# CLI Helper
# ============================================================================


def print_result(result: StrategySwitchSanityResult) -> None:
    """
    Gibt das Ergebnis formatiert auf der Konsole aus.

    Args:
        result: Das Sanity-Check-Ergebnis
    """
    status_icons = {"OK": "✅", "WARN": "⚠️", "FAIL": "❌"}
    icon = status_icons.get(result.status, "❓")

    print(f"\n{icon} Strategy-Switch Sanity Check: {result.status}")
    print("=" * 50)
    print(f"Config:             {result.config_path}")
    print(f"active_strategy_id: {result.active_strategy_id or '(nicht gesetzt)'}")
    print(f"allowed:            {result.allowed or '(leer)'}")

    if result.invalid_strategies:
        print(f"\n❌ Unbekannte Strategien: {result.invalid_strategies}")

    if result.r_and_d_strategies:
        print(f"\n❌ R&D-Strategien in allowed: {result.r_and_d_strategies}")

    if result.messages:
        print("\nMeldungen:")
        for msg in result.messages:
            print(f"  • {msg}")

    print()
