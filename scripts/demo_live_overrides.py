#!/usr/bin/env python3
"""
Demo: Live-Overrides Config Integration

Zeigt, wie config/live_overrides/auto.toml automatisch in die Config
integriert wird, wenn wir in einem Live-Environment sind.

Usage:
    # Demo mit Paper-Environment (keine Overrides)
    python scripts/demo_live_overrides.py

    # Demo mit Live-Environment (mit Overrides)
    PEAK_ENV=live python scripts/demo_live_overrides.py

    # Force-Apply in jedem Environment
    python scripts/demo_live_overrides.py --force
"""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.peak_config import (
    load_config,
    load_config_with_live_overrides,
    _is_live_like_environment,
    _load_live_auto_overrides,
    AUTO_LIVE_OVERRIDES_PATH,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Demo der Live-Overrides Config Integration"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force-apply overrides auch in Paper-Environment",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Pfad zu custom config.toml (optional)",
    )
    return parser.parse_args()


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def main() -> None:
    """Main demo function."""
    args = parse_args()

    print_section("Live-Overrides Config Integration Demo")

    # 1. Prüfe auto.toml
    print("1. Prüfe auto.toml...")
    overrides = _load_live_auto_overrides(AUTO_LIVE_OVERRIDES_PATH)
    print(f"   Pfad: {AUTO_LIVE_OVERRIDES_PATH}")
    print(f"   Gefunden: {len(overrides)} Override(s)")
    if overrides:
        for key, value in overrides.items():
            print(f"     - {key} = {value}")
    else:
        print("     (keine aktiven Overrides)")

    # 2. Lade Basis-Config
    print_section("2. Lade Basis-Config (ohne Overrides)")
    base_cfg = load_config(args.config)
    env_mode = base_cfg.get("environment.mode", "paper")
    print(f"   Environment Mode: {env_mode}")
    print(f"   Is Live-like: {_is_live_like_environment(base_cfg)}")

    # Beispiel-Werte aus Basis-Config
    example_keys = [
        "portfolio.leverage",
        "strategy.trigger_delay",
        "macro.regime_weight",
        "risk.max_position",
    ]

    print("\n   Basis-Werte:")
    for key in example_keys:
        value = base_cfg.get(key, "N/A")
        print(f"     - {key}: {value}")

    # 3. Lade Config mit Overrides
    print_section("3. Lade Config mit Live-Overrides")
    live_cfg = load_config_with_live_overrides(
        args.config, force_apply_overrides=args.force
    )

    print("   Werte nach Override-Anwendung:")
    for key in example_keys:
        base_val = base_cfg.get(key, "N/A")
        live_val = live_cfg.get(key, "N/A")
        changed = "✓ CHANGED" if base_val != live_val else ""
        print(f"     - {key}: {live_val} {changed}")

    # 4. Zusammenfassung
    print_section("Zusammenfassung")

    will_apply = args.force or _is_live_like_environment(base_cfg)
    has_overrides = len(overrides) > 0

    if will_apply and has_overrides:
        print("   ✅ Overrides werden angewendet")
        print(f"   ✅ {len(overrides)} Parameter überschrieben")
        if args.force:
            print("   ⚠️  Force-Apply aktiviert (auch in Paper)")
        else:
            print(f"   ✓  Live-Environment erkannt: {env_mode}")
    elif will_apply and not has_overrides:
        print("   ℹ️  Keine Overrides in auto.toml gefunden")
        print("   ℹ️  Config wird ohne Overrides geladen")
    else:
        print("   ℹ️  Paper-Environment: Overrides werden NICHT angewendet")
        print("   ℹ️  Nutze --force um Overrides zu erzwingen")

    # 5. Empfehlungen
    print_section("Empfehlungen für Production Code")
    print("""
   ✅ Verwende: load_config_with_live_overrides()
      -> Automatische Integration von auto.toml in Live-Environments

   ✅ Auto.toml wird gepflegt von: Promotion Loop v0
      -> Bounded auto-apply schreibt validierte Parameter

   ✅ Environment-basiertes Gating:
      -> Paper-Backtests bleiben unverändert
      -> Live/Testnet bekommen automatisch Overrides

   ⚠️  Force-Apply nur in Tests:
      -> Nutze force_apply_overrides=True nur in Testcode
    """)

    print("\n✓ Demo abgeschlossen.\n")


if __name__ == "__main__":
    main()
