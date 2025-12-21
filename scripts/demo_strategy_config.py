#!/usr/bin/env python3
"""
Beispiel: Strategy Config-Management
=====================================
Zeigt, wie man mit get_strategy_cfg() arbeitet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_config, get_strategy_cfg, list_strategies


def main():
    """Demonstriert Strategy Config-Funktionen."""

    print("\n" + "=" * 70)
    print("PEAK_TRADE STRATEGY CONFIG DEMO")
    print("=" * 70)

    # 1. Alle verfügbaren Strategien anzeigen
    print("\n📋 Verfügbare Strategien:")
    print("-" * 70)
    strategies = list_strategies()

    if not strategies:
        print("  (keine Strategien in config.toml definiert)")
    else:
        for i, name in enumerate(strategies, 1):
            print(f"  {i}. {name}")

    # 2. Strategie-Config laden
    if strategies:
        print(f"\n⚙️  Lade Config für '{strategies[0]}':")
        print("-" * 70)

        try:
            params = get_strategy_cfg(strategies[0])

            for key, value in sorted(params.items()):
                print(f"  {key:20s} = {value}")

        except KeyError as e:
            print(f"  ❌ Fehler: {e}")

    # 3. Fehlerfall demonstrieren
    print("\n❌ Fehlerfall: Nicht existierende Strategie")
    print("-" * 70)

    try:
        get_strategy_cfg("non_existent_strategy")
    except KeyError as e:
        print(f"  Erwarteter Fehler gefangen:")
        print(f"  {e}")

    # 4. Globale Config zeigen
    print("\n🔧 Globale Config:")
    print("-" * 70)
    cfg = get_config()
    print(f"  Risk per Trade:     {cfg.risk.risk_per_trade:.1%}")
    print(f"  Max Position Size:  {cfg.risk.max_position_size:.0%}")
    print(f"  Initial Cash:       ${cfg.backtest.initial_cash:,.2f}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
