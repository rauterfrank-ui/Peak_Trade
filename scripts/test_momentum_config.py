#!/usr/bin/env python3
"""
Quick Test: Momentum Strategy Config
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import get_strategy_cfg, list_strategies

print("\n" + "=" * 70)
print("TEST: Momentum Strategy Config")
print("=" * 70)

# 1. Liste aller Strategien
print("\n📋 Verfügbare Strategien:")
for name in list_strategies():
    print(f"  - {name}")

# 2. Momentum-Config laden
print("\n⚙️  Momentum-Config:")
try:
    strat_cfg = get_strategy_cfg("momentum_1h")
    for key, value in sorted(strat_cfg.items()):
        print(f"  {key:20s} = {value}")
    print("\n✅ Config erfolgreich geladen!")
except KeyError as e:
    print(f"\n❌ FEHLER: {e}")

print("\n" + "=" * 70 + "\n")
