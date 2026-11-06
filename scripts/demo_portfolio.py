#!/usr/bin/env python3
"""
Quick Demo: Multi-Strategy Portfolio
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import list_strategies

print("\n" + "=" * 70)
print("PEAK_TRADE MULTI-STRATEGY PORTFOLIO - QUICK DEMO")
print("=" * 70)

print("\n📋 Verfügbare Strategien in config.toml:")
for i, name in enumerate(list_strategies(), 1):
    print(f"  {i}. {name}")

print("\n💡 Portfolio-Features:")
print("  ✅ Mehrere Strategien parallel")
print("  ✅ Automatische Capital-Allocation")
print("  ✅ Portfolio-Level Risk-Management")
print("  ✅ Diversifikations-Analyse")

print("\n🚀 Backtest starten mit:")
print("  python scripts/run_portfolio_backtest.py")

print("\n" + "=" * 70 + "\n")
