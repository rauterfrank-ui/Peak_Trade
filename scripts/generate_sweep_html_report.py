#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peak_Trade: HTML-Übersicht für Sweep-Ergebnisse
================================================
Erzeugt eine HTML-Übersicht aus einer Sweep-CSV.

Usage:
    python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_xxx.csv
    python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_xxx.csv --sort-by sharpe --max-rows 50
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: HTML-Übersicht für einen Sweep auf Basis der CSV-Ergebnisse.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Einfachste Form
  python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_demo.csv

  # Mit Sortierung nach Sharpe
  python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_demo.csv --sort-by sharpe

  # Nur Top 50 Zeilen anzeigen
  python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_demo.csv --max-rows 50

  # Kombination
  python scripts/generate_sweep_html_report.py reports/sweeps/sweep_ma_crossover_demo.csv --sort-by total_return --max-rows 20
        """
    )
    parser.add_argument(
        "csv_path",
        help="Pfad zur Sweep-CSV (z.B. reports/sweeps/sweep_ma_crossover_xxx.csv).",
    )
    parser.add_argument(
        "--sort-by",
        help=(
            "Spalte, nach der sortiert werden soll (z.B. total_return, cagr, sharpe). "
            "Standard: unverändert / wie in CSV."
        ),
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (Standard: absteigend, wenn sort-by gesetzt ist).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Optional: maximale Anzahl angezeigter Zeilen in der HTML-Tabelle.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📊 Peak_Trade – Sweep HTML Report Generator")
    print("="*70)

    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV-Datei nicht gefunden: {csv_path}")

    print(f"\n📁 Lade CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)} Zeilen geladen")

    sort_by = args.sort_by
    ascending = args.ascending

    if sort_by is not None and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
        print(f"🔄 Sortiert nach: {sort_by} ({'aufsteigend' if ascending else 'absteigend'})")
    elif sort_by is not None:
        print(f"⚠️  Warnung: Spalte '{sort_by}' nicht gefunden, keine Sortierung angewendet")

    if args.max_rows is not None and args.max_rows > 0:
        df_display = df.head(args.max_rows)
        print(f"📋 Zeige Top {args.max_rows} Zeilen")
    else:
        df_display = df
        print(f"📋 Zeige alle {len(df)} Zeilen")

    # Einige Meta-Infos heuristisch extrahieren
    strategy = df.get("strategy_key", pd.Series(["n/a"])).iloc[0] if len(df) > 0 else "n/a"
    symbol = df.get("symbol", pd.Series(["n/a"])).iloc[0] if len(df) > 0 else "n/a"
    n_runs = len(df)

    # HTML-Tabelle generieren
    html_table = df_display.to_html(
        index=False,
        border=0,
        classes="sweep-table",
        float_format=lambda x: f"{x:.6g}",
    )

    out_dir = csv_path.parent
    out_name = csv_path.stem + "_summary.html"
    out_path = out_dir / out_name

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade Sweep Summary – {csv_path.name}</title>
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
        table.sweep-table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 1400px;
            font-size: 0.85rem;
        }}
        table.sweep-table th, table.sweep-table td {{
            border: 1px solid #444;
            padding: 0.35rem 0.5rem;
        }}
        table.sweep-table th {{
            background-color: #222;
            position: sticky;
            top: 0;
        }}
        table.sweep-table tbody tr:hover {{
            background-color: #1a1a1a;
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
    <h1>Peak_Trade – Sweep Summary</h1>
    <div class="meta">
        <p><strong>CSV:</strong> <code>{csv_path.name}</code></p>
        <p><strong>Strategie:</strong> {strategy}</p>
        <p><strong>Symbol (erste Zeile):</strong> {symbol}</p>
        <p><strong>Anzahl getesteter Konfigurationen:</strong> {n_runs}</p>
        <p><strong>Angezeigte Zeilen:</strong> {len(df_display)}</p>
        <p><strong>Sortierung:</strong> {sort_by or "keine"}{" (aufsteigend)" if ascending and sort_by else " (absteigend)" if sort_by else ""}</p>
    </div>

    <div class="table-wrapper">
        {html_table}
    </div>

    <div class="note">
        <p>
            Hinweis: Alle Werte stammen direkt aus der Sweep-CSV.
            Zusätzliche Reports (Equity/Drawdown/Plots) für Top-Konfigurationen
            liegen ggf. im gleichen Ordner (<code>reports/sweeps/</code>).
        </p>
    </div>
</body>
</html>
"""

    out_path.write_text(html, encoding="utf-8")
    print(f"\n✅ HTML-Übersicht gespeichert: {out_path}")
    print()


if __name__ == "__main__":
    main()
