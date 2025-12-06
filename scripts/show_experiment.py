#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/show_experiment.py
"""
Peak_Trade – Einzelnes Experiment anzeigen
==========================================
Zeigt Details eines einzelnen Runs aus der Registry.

Usage:
    python scripts/show_experiment.py --run-id <UUID>
    python scripts/show_experiment.py --run-id abc12345-...
"""
from __future__ import annotations

import sys
import argparse
import json
from pathlib import Path
from typing import List, Optional, Any, Dict

# Projekt-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.experiments import (
    get_experiment_by_id,
    get_experiment_stats,
    get_experiment_metadata,
    RUN_TYPE_BACKTEST,
    RUN_TYPE_LIVE_RISK_CHECK,
    RUN_TYPE_PAPER_TRADE,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Einzelnes Experiment anzeigen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/show_experiment.py --run-id abc12345-6789-...
  python scripts/show_experiment.py --run-id abc12345 --json
        """,
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run-ID des Experiments (UUID, kann gekürzt sein).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe als JSON.",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Nur Stats anzeigen.",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Nur Metadata anzeigen.",
    )
    return parser.parse_args(argv)


def format_percent(value) -> str:
    """Formatiert als Prozent oder gibt '-' bei None zurück."""
    if value is None:
        return "-"
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return "-"


def format_float(value, decimals: int = 2) -> str:
    """Formatiert Float oder gibt '-' bei None zurück."""
    if value is None:
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


def print_backtest_stats(stats: Dict[str, Any]) -> None:
    """Gibt Backtest-Stats formatiert aus."""
    print("\n--- KENNZAHLEN ---")
    print(f"  Total Return:    {format_percent(stats.get('total_return'))}")
    print(f"  Max Drawdown:    {format_percent(stats.get('max_drawdown'))}")
    print(f"  CAGR:            {format_percent(stats.get('cagr'))}")
    print(f"  Sharpe Ratio:    {format_float(stats.get('sharpe'))}")

    if stats.get('sortino') is not None:
        print(f"  Sortino Ratio:   {format_float(stats.get('sortino'))}")
    if stats.get('calmar') is not None:
        print(f"  Calmar Ratio:    {format_float(stats.get('calmar'))}")

    print("\n--- TRADE-STATISTIKEN ---")
    print(f"  Total Trades:    {stats.get('total_trades', '-')}")
    print(f"  Win Rate:        {format_percent(stats.get('win_rate'))}")
    print(f"  Profit Factor:   {format_float(stats.get('profit_factor'))}")

    if stats.get('blocked_trades') is not None:
        print(f"  Blocked Trades:  {stats.get('blocked_trades')}")


def print_live_risk_stats(stats: Dict[str, Any], metadata: Dict[str, Any]) -> None:
    """Gibt Live-Risk-Check-Stats formatiert aus."""
    print("\n--- RISK-CHECK ERGEBNIS ---")
    allowed = stats.get("allowed", False)
    print(f"  Status:          {'BESTANDEN' if allowed else 'NICHT BESTANDEN'}")
    print(f"  Violations:      {stats.get('n_violations', 0)}")

    print("\n--- METRIKEN ---")
    print(f"  Anzahl Orders:   {stats.get('n_orders', '-')}")
    print(f"  Anzahl Symbole:  {stats.get('n_symbols', '-')}")
    print(f"  Total Notional:  {format_float(stats.get('total_notional'))}")
    print(f"  Max Order Not.:  {format_float(stats.get('max_order_notional'))}")
    print(f"  Daily PnL Net:   {format_float(stats.get('daily_realized_pnl_net'))}")

    # Violations aus Metadata
    violations = metadata.get("violations", [])
    if violations:
        print("\n--- VIOLATIONS ---")
        for v in violations:
            print(f"  - {v}")


def print_paper_trade_stats(stats: Dict[str, Any]) -> None:
    """Gibt Paper-Trade-Stats formatiert aus."""
    print("\n--- PAPER-TRADE ERGEBNIS ---")
    print(f"  Start Cash:      {format_float(stats.get('starting_cash'))}")
    print(f"  End Cash:        {format_float(stats.get('ending_cash'))}")
    print(f"  Equity:          {format_float(stats.get('equity'))}")
    print(f"  Market Value:    {format_float(stats.get('market_value'))}")

    print("\n--- P&L ---")
    print(f"  Realized PnL:    {format_float(stats.get('realized_pnl_total'))}")
    print(f"  Unrealized PnL:  {format_float(stats.get('unrealized_pnl_total'))}")
    print(f"  Total Fees:      {format_float(stats.get('total_fees'))}")
    print(f"  Net PnL:         {format_float(stats.get('realized_pnl_net'))}")

    print("\n--- ORDERS ---")
    print(f"  Anzahl Orders:   {stats.get('n_orders', '-')}")
    print(f"  Anzahl Positions:{stats.get('n_positions', '-')}")


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    # Experiment laden
    record = get_experiment_by_id(args.run_id)

    if record is None:
        print(f"\nExperiment nicht gefunden: {args.run_id}")
        print("Hinweis: Die Run-ID muss exakt übereinstimmen (vollständige UUID).\n")
        return 1

    # JSON-Ausgabe
    if args.json:
        output = {
            "run_id": record.run_id,
            "run_type": record.run_type,
            "run_name": record.run_name,
            "timestamp": record.timestamp,
            "strategy_key": record.strategy_key,
            "symbol": record.symbol,
            "total_return": record.total_return,
            "max_drawdown": record.max_drawdown,
            "sharpe": record.sharpe,
            "cagr": record.cagr,
        }
        try:
            output["stats"] = json.loads(record.stats_json)
        except (json.JSONDecodeError, TypeError):
            output["stats"] = {}
        try:
            output["metadata"] = json.loads(record.metadata_json)
        except (json.JSONDecodeError, TypeError):
            output["metadata"] = {}

        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    # Stats und Metadata laden
    stats = get_experiment_stats(args.run_id) or {}
    metadata = get_experiment_metadata(args.run_id) or {}

    # Nur Stats
    if args.stats_only:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    # Nur Metadata
    if args.metadata_only:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        return 0

    # Vollständige Ausgabe
    print("\n" + "=" * 70)
    print("  EXPERIMENT DETAILS")
    print("=" * 70)

    print("\n--- ALLGEMEIN ---")
    print(f"  Run-ID:          {record.run_id}")
    print(f"  Run-Type:        {record.run_type}")
    print(f"  Run-Name:        {record.run_name}")
    print(f"  Timestamp:       {record.timestamp}")

    if record.strategy_key:
        print(f"  Strategy:        {record.strategy_key}")
    if record.symbol:
        print(f"  Symbol:          {record.symbol}")

    # Tag aus Metadata
    tag = metadata.get("tag")
    if tag:
        print(f"  Tag:             {tag}")

    # Config-Pfad
    config_path = metadata.get("config_path")
    if config_path:
        print(f"  Config:          {config_path}")

    # Run-Type-spezifische Ausgabe
    if record.run_type == RUN_TYPE_BACKTEST:
        print_backtest_stats(stats)
    elif record.run_type == RUN_TYPE_LIVE_RISK_CHECK:
        print_live_risk_stats(stats, metadata)
    elif record.run_type == RUN_TYPE_PAPER_TRADE:
        print_paper_trade_stats(stats)
    else:
        # Generische Stats-Ausgabe
        if stats:
            print("\n--- STATS ---")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {format_float(value)}")
                else:
                    print(f"  {key}: {value}")

    # Weitere Metadata
    print("\n--- METADATA ---")
    skip_keys = {"tag", "config_path", "violations", "runner"}
    for key, value in metadata.items():
        if key not in skip_keys and value is not None:
            if isinstance(value, (dict, list)):
                print(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                print(f"  {key}: {value}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
