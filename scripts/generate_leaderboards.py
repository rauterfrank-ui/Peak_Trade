#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/generate_leaderboards.py
from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufuegen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.analytics.leaderboard import build_standard_leaderboards
from src.core.experiments import EXPERIMENTS_CSV


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: HTML-Leaderboards (Best Performer) basierend auf der Experiment-Registry.",
    )
    parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik fuer Ranking (z.B. sharpe, total_return, cagr, max_drawdown). Default: sharpe",
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (fuer Metriken wie max_drawdown). Default: absteigend.",
    )
    parser.add_argument(
        "--global-top-n",
        type=int,
        default=50,
        help="Anzahl globaler Top-Runs.",
    )
    parser.add_argument(
        "--per-symbol-top-n",
        type=int,
        default=5,
        help="Top-N pro Symbol.",
    )
    parser.add_argument(
        "--per-strategy-top-n",
        type=int,
        default=5,
        help="Top-N pro Strategie.",
    )
    parser.add_argument(
        "--per-run-type-top-n",
        type=int,
        default=5,
        help="Top-N pro Run-Typ.",
    )
    parser.add_argument(
        "--min-runs-per-symbol",
        type=int,
        default=1,
        help="Mindestens so viele Runs pro Symbol, um im Leaderboard aufzutauchen.",
    )
    parser.add_argument(
        "--min-runs-per-strategy",
        type=int,
        default=1,
        help="Mindestens so viele Runs pro Strategie, um im Leaderboard aufzutauchen.",
    )
    parser.add_argument(
        "--min-runs-per-run-type",
        type=int,
        default=1,
        help="Mindestens so viele Runs pro Run-Typ, um im Leaderboard aufzutauchen.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/leaderboards",
        help="Zielverzeichnis fuer das HTML-Dashboard. Default: reports/leaderboards",
    )
    parser.add_argument(
        "--max-all-rows",
        type=int,
        help="Optional: maximale Anzahl Zeilen in der vollstaendigen Registry-Tabelle.",
    )
    return parser.parse_args(argv)


def _df_to_html_table(df: pd.DataFrame, table_class: str = "lb-table") -> str:
    if df.empty:
        return "<p><em>Keine Daten fuer dieses Leaderboard.</em></p>"

    return df.to_html(
        index=False,
        border=0,
        classes=table_class,
        float_format=lambda x: f"{x:.6g}",
    )


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📊 Peak_Trade Leaderboard Generator")
    print("="*70)

    metric = args.metric
    ascending = args.ascending

    print(f"\n⚙️  Lade Experiment-Registry und berechne Leaderboards...")
    print(f"  - Metrik: {metric}")
    print(f"  - Sortierung: {'aufsteigend' if ascending else 'absteigend'}")

    lbs = build_standard_leaderboards(
        metric=metric,
        global_top_n=args.global_top_n,
        per_symbol_top_n=args.per_symbol_top_n,
        per_strategy_top_n=args.per_strategy_top_n,
        per_run_type_top_n=args.per_run_type_top_n,
        min_runs_per_symbol=args.min_runs_per_symbol,
        min_runs_per_strategy=args.min_runs_per_strategy,
        min_runs_per_run_type=args.min_runs_per_run_type,
        ascending=ascending,
    )

    print(f"  ✅ {len(lbs.df_all)} Experimente geladen")
    print(f"  ✅ Globales Leaderboard: {len(lbs.df_global_top)} Eintraege")
    print(f"  ✅ Pro-Symbol: {len(lbs.df_per_symbol)} Eintraege")
    print(f"  ✅ Pro-Strategie: {len(lbs.df_per_strategy)} Eintraege")
    print(f"  ✅ Pro-Run-Typ: {len(lbs.df_per_run_type)} Eintraege")

    df_all = lbs.df_all
    if args.max_all_rows is not None and args.max_all_rows > 0:
        df_all_display = df_all.head(args.max_all_rows)
    else:
        df_all_display = df_all

    html_global = _df_to_html_table(lbs.df_global_top, "lb-table")
    html_symbol = _df_to_html_table(lbs.df_per_symbol, "lb-table")
    html_strategy = _df_to_html_table(lbs.df_per_strategy, "lb-table")
    html_run_type = _df_to_html_table(lbs.df_per_run_type, "lb-table")
    html_all = _df_to_html_table(df_all_display, "lb-table lb-table-all")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "leaderboard.html"

    csv_path = EXPERIMENTS_CSV

    sort_label = f"{metric} ({'asc' if ascending else 'desc'})"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade Leaderboards – Best Performer</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 2rem;
            background-color: #111;
            color: #eee;
        }}
        h1, h2, h3 {{
            color: #fff;
        }}
        a {{
            color: #4ea1ff;
        }}
        .meta {{
            margin-bottom: 1.5rem;
        }}
        .meta p {{
            margin: 0.2rem 0;
        }}
        table.lb-table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 1200px;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        table.lb-table th, table.lb-table td {{
            border: 1px solid #444;
            padding: 0.35rem 0.5rem;
        }}
        table.lb-table th {{
            background-color: #222;
        }}
        table.lb-table tbody tr:hover {{
            background-color: #1a1a1a;
        }}
        .section {{
            margin-bottom: 2.5rem;
        }}
        .note {{
            margin-top: 1rem;
            font-size: 0.8rem;
            color: #aaa;
        }}
        code {{
            background-color: #222;
            padding: 0.15rem 0.3rem;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Peak_Trade – Strategy Leaderboards</h1>

    <div class="meta">
        <p><strong>Experiment-Registry:</strong> <code>{csv_path}</code></p>
        <p><strong>Ranking-Metrik:</strong> <code>{sort_label}</code></p>
        <p><strong>Anzahl Experimente gesamt:</strong> {len(df_all)}</p>
    </div>

    <div class="section">
        <h2>1. Globales Leaderboard (Top {args.global_top_n})</h2>
        <p>Alle Runs, sortiert nach <code>{sort_label}</code>.</p>
        {html_global}
    </div>

    <div class="section">
        <h2>2. Top-Runs pro Symbol (Top {args.per_symbol_top_n} je Symbol)</h2>
        <p>Beste Runs pro Symbol, basierend auf <code>{sort_label}</code>.</p>
        {html_symbol}
    </div>

    <div class="section">
        <h2>3. Top-Runs pro Strategie (Top {args.per_strategy_top_n} je Strategie)</h2>
        <p>Beste Runs pro Strategy-Key, basierend auf <code>{sort_label}</code>.</p>
        {html_strategy}
    </div>

    <div class="section">
        <h2>4. Top-Runs pro Run-Typ (Top {args.per_run_type_top_n} je Typ)</h2>
        <p>z.B. <code>single_backtest</code>, <code>sweep</code>, <code>portfolio</code>, <code>market_scan</code>.</p>
        {html_run_type}
    </div>

    <div class="section">
        <h2>5. Vollstaendige Registry (Auszug)</h2>
        <p>Die vollstaendige Experiment-Registry (ggf. gekuerzt auf die ersten Zeilen).</p>
        {html_all}
        <div class="note">
            <p>Hinweis: Die vollstaendige Registry liegt als CSV unter <code>{csv_path}</code> und kann in Pandas, Excel etc. geladen werden.</p>
        </div>
    </div>
</body>
</html>
"""

    out_path.write_text(html, encoding="utf-8")
    print(f"\n💾 Leaderboard-Dashboard gespeichert: {out_path}")
    print(f"✅ Leaderboard-Generation abgeschlossen!\n")


if __name__ == "__main__":
    main()
