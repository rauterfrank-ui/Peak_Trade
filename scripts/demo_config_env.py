#!/usr/bin/env python3
"""
Demo: Environment-Variable-basiertes Config-System
====================================================
Zeigt wie man verschiedene Configs für verschiedene Umgebungen nutzt.

Usage:
    # Default config.toml
    python scripts/demo_config_env.py

    # Mit Environment Variable
    export PEAK_TRADE_CONFIG=/path/to/custom_config.toml
    python scripts/demo_config_env.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from src.core import (
    get_config,
    resolve_config_path,
    DEFAULT_CONFIG_ENV_VAR,
    reset_config,
)


def main():
    """Demonstriert Config-Pfad-Auflösung."""

    print("\n" + "=" * 70)
    print("PEAK_TRADE CONFIG ENVIRONMENT DEMO")
    print("=" * 70)

    # Aktueller Config-Pfad
    print(f"\n📋 Config-Pfad-Auflösung:")
    print("-" * 70)

    config_path = resolve_config_path()
    print(f"Verwendeter Config-Pfad: {config_path}")
    print(f"Absoluter Pfad:          {config_path.absolute()}")
    print(f"Existiert:               {'✅ Ja' if config_path.exists() else '❌ Nein'}")

    # Environment Variable Status
    print(f"\n🔧 Environment Variable:")
    print("-" * 70)
    env_value = os.getenv(DEFAULT_CONFIG_ENV_VAR)

    if env_value:
        print(f"{DEFAULT_CONFIG_ENV_VAR} = {env_value}")
        print("✅ Environment Variable ist gesetzt")
    else:
        print(f"{DEFAULT_CONFIG_ENV_VAR} nicht gesetzt")
        print("→ Nutzt Default: config.toml")

    # Config laden
    print(f"\n⚙️  Geladene Config:")
    print("-" * 70)

    try:
        cfg = get_config()

        print(f"Initial Cash:      ${cfg.backtest.initial_cash:,.2f}")
        print(f"Risk per Trade:    {cfg.risk.risk_per_trade:.1%}")
        print(f"Max Position Size: {cfg.risk.max_position_size:.0%}")
        print(f"Default Timeframe: {cfg.data.default_timeframe}")

        # Strategien
        print(f"\n📊 Verfügbare Strategien: {len(cfg.strategy)}")
        for i, name in enumerate(sorted(cfg.strategy.keys()), 1):
            print(f"  {i}. {name}")

        print("\n✅ Config erfolgreich geladen!")

    except FileNotFoundError as e:
        print(f"\n❌ FEHLER: {e}")

    # Usage-Beispiele
    print(f"\n💡 Verwendung:")
    print("-" * 70)
    print("# Default config.toml verwenden:")
    print("python scripts/run_backtest.py")
    print()
    print("# Custom Config verwenden:")
    print(f"export {DEFAULT_CONFIG_ENV_VAR}=/path/to/test_config.toml")
    print("python scripts/run_backtest.py")
    print()
    print("# Verschiedene Umgebungen:")
    print(f"export {DEFAULT_CONFIG_ENV_VAR}=configs/dev.toml    # Development")
    print(f"export {DEFAULT_CONFIG_ENV_VAR}=configs/test.toml   # Testing")
    print(f"export {DEFAULT_CONFIG_ENV_VAR}=configs/prod.toml   # Production")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
