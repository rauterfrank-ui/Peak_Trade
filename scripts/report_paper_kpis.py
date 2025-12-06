#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/report_paper_kpis.py
"""
Peak_Trade: Strategy-Level Paper KPIs Report.

Aggregiert alle paper_trade-Runs aus der Experiment-Registry
und erzeugt eine Strategy-Leaderboard (HTML + CSV).

Usage:
    python scripts/report_paper_kpis.py
    python scripts/report_paper_kpis.py --top 10 --output-dir reports/paper
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Pfad-Setup wie in anderen Scripts
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import EXPERIMENTS_CSV, log_generic_experiment


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Strategy-Level Paper KPIs Report.",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/paper",
        help="Verzeichnis fuer HTML/CSV-Reports (Default: reports/paper).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Maximale Anzahl Strategien im Leaderboard (Default: 20).",
    )
    parser.add_argument(
        "--sort-by",
        default="realized_pnl_net",
        choices=[
            "realized_pnl_net",
            "realized_pnl_total",
            "n_runs",
            "total_notional",
            "total_fees",
            "avg_slippage_bps",
        ],
        help="Sortier-Spalte im Leaderboard (Default: realized_pnl_net).",
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (Default: absteigend).",
    )
    return parser.parse_args(argv)


def _load_paper_runs() -> pd.DataFrame:
    """
    Laedt alle paper_trade-Runs aus der Experiment-Registry.
    """
    if not EXPERIMENTS_CSV.is_file():
        raise SystemExit(f"Experiment-Registry nicht gefunden: {EXPERIMENTS_CSV}")

    df = pd.read_csv(EXPERIMENTS_CSV)

    if "run_type" not in df.columns:
        raise SystemExit(
            f"Experiment-Registry {EXPERIMENTS_CSV} enthaelt keine Spalte 'run_type'."
        )

    df_paper = df[df["run_type"] == "paper_trade"].copy()

    if df_paper.empty:
        raise SystemExit(
            "Keine paper_trade-Runs in der Experiment-Registry gefunden."
        )

    return df_paper


def _parse_metadata_json(metadata_json_str: Any) -> Dict[str, Any]:
    """
    Parst den metadata_json-String aus der Registry.
    """
    if pd.isna(metadata_json_str):
        return {}
    try:
        return json.loads(str(metadata_json_str))
    except (json.JSONDecodeError, TypeError):
        return {}


def _determine_strategy_key(row: pd.Series) -> str:
    """
    Bestimmt den primaeren strategy_key fuer einen paper_trade-Run.

    Heuristik:
    1. metadata_json.strategy_key (falls vorhanden)
    2. metadata_json.runner (falls vorhanden)
    3. run_name
    """
    meta = _parse_metadata_json(row.get("metadata_json"))

    if "strategy_key" in meta and meta["strategy_key"]:
        return str(meta["strategy_key"])

    if "runner" in meta and meta["runner"]:
        runner = str(meta["runner"])
        # Extract strategy from runner filename
        if runner.endswith(".py"):
            runner = runner[:-3]
        return runner

    run_name = row.get("run_name", "unknown")
    return str(run_name)


def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Konvertiert einen Wert sicher in float.
    """
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def aggregate_by_strategy(df_paper: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregiert paper_trade-Runs nach strategy_key.

    Spalten im Output:
    - strategy_key
    - n_runs
    - n_orders_total
    - total_notional
    - avg_notional_per_run
    - total_fees
    - realized_pnl_total
    - realized_pnl_net
    - avg_slippage_bps
    - first_run_ts
    - last_run_ts
    """
    # Strategy-Key fuer jeden Run bestimmen
    df_paper = df_paper.copy()
    df_paper["strategy_key"] = df_paper.apply(_determine_strategy_key, axis=1)

    # Stats aus Registry-Spalten extrahieren (falls vorhanden)
    # Die paper_trade_from_orders.py logged diese Werte
    stat_cols = [
        "n_orders",
        "total_notional",
        "total_fees",
        "realized_pnl_total",
        "realized_pnl_net",
        "slippage_bps",
    ]
    for col in stat_cols:
        if col not in df_paper.columns:
            df_paper[col] = np.nan

    # Timestamp fuer First/Last Run
    if "timestamp" in df_paper.columns:
        df_paper["ts"] = pd.to_datetime(df_paper["timestamp"], errors="coerce")
    else:
        df_paper["ts"] = pd.NaT

    # Group by strategy_key
    grouped = df_paper.groupby("strategy_key")

    records: List[Dict[str, Any]] = []

    for strategy_key, grp in grouped:
        n_runs = len(grp)

        n_orders_total = int(grp["n_orders"].apply(lambda x: _safe_float(x, 0)).sum())
        total_notional = float(grp["total_notional"].apply(lambda x: _safe_float(x, 0)).sum())
        avg_notional_per_run = total_notional / n_runs if n_runs > 0 else 0.0
        total_fees = float(grp["total_fees"].apply(lambda x: _safe_float(x, 0)).sum())
        realized_pnl_total = float(grp["realized_pnl_total"].apply(lambda x: _safe_float(x, 0)).sum())
        realized_pnl_net = float(grp["realized_pnl_net"].apply(lambda x: _safe_float(x, 0)).sum())

        # Slippage: gewichteter Durchschnitt basierend auf notional
        slippages = grp["slippage_bps"].apply(lambda x: _safe_float(x, float("nan")))
        notionals = grp["total_notional"].apply(lambda x: _safe_float(x, 0))
        valid_mask = ~slippages.isna() & (notionals > 0)

        if valid_mask.any():
            avg_slippage_bps = float(
                (slippages[valid_mask] * notionals[valid_mask]).sum()
                / notionals[valid_mask].sum()
            )
        else:
            avg_slippage_bps = float("nan")

        ts_values = grp["ts"].dropna()
        first_run_ts = ts_values.min() if not ts_values.empty else None
        last_run_ts = ts_values.max() if not ts_values.empty else None

        records.append(
            {
                "strategy_key": strategy_key,
                "n_runs": n_runs,
                "n_orders_total": n_orders_total,
                "total_notional": total_notional,
                "avg_notional_per_run": avg_notional_per_run,
                "total_fees": total_fees,
                "realized_pnl_total": realized_pnl_total,
                "realized_pnl_net": realized_pnl_net,
                "avg_slippage_bps": avg_slippage_bps,
                "first_run_ts": first_run_ts,
                "last_run_ts": last_run_ts,
            }
        )

    return pd.DataFrame(records)


def _df_to_html_table(df: pd.DataFrame, table_class: str = "table") -> str:
    if df.empty:
        return "<p><em>Keine Daten.</em></p>"

    return df.to_html(
        index=False,
        border=0,
        classes=table_class,
        float_format=lambda x: f"{x:.6g}",
    )


def build_html_leaderboard(
    cfg: PeakConfig,
    df_kpis: pd.DataFrame,
    n_paper_runs: int,
    sort_by: str,
    ascending: bool,
) -> str:
    """
    Erzeugt ein HTML-Leaderboard fuer Strategy-Level KPIs.
    """
    base_currency = str(cfg.get("live.base_currency", "EUR"))
    ts_now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Tabelle formatieren
    df_display = df_kpis.copy()

    # Timestamp-Spalten formatieren
    for col in ["first_run_ts", "last_run_ts"]:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M") if pd.notna(x) else "–"
            )

    html_table = _df_to_html_table(df_display, "kpi-table")

    # Summary-Stats
    total_strategies = len(df_kpis)
    total_pnl_net = df_kpis["realized_pnl_net"].sum() if "realized_pnl_net" in df_kpis.columns else 0.0
    total_fees_all = df_kpis["total_fees"].sum() if "total_fees" in df_kpis.columns else 0.0
    total_notional_all = df_kpis["total_notional"].sum() if "total_notional" in df_kpis.columns else 0.0

    pnl_class = "highlight-good" if total_pnl_net >= 0 else "highlight-bad"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade - Strategy KPI Leaderboard</title>
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
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background-color: #1a1a1a;
            border-radius: 0.75rem;
            padding: 1rem 1.2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .card h3 {{
            margin-top: 0;
            margin-bottom: 0.4rem;
        }}
        .card p {{
            margin: 0.2rem 0;
        }}
        .section {{
            margin-bottom: 2.5rem;
        }}
        table.kpi-table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 1400px;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        table.kpi-table th, table.kpi-table td {{
            border: 1px solid #444;
            padding: 0.4rem 0.6rem;
        }}
        table.kpi-table th {{
            background-color: #222;
        }}
        .highlight-good {{
            color: #8df7a0;
        }}
        .highlight-bad {{
            color: #ff8a8a;
        }}
        code {{
            background-color: #222;
            padding: 0.15rem 0.3rem;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Peak_Trade - Strategy KPI Leaderboard</h1>

    <div class="meta">
        <p><strong>Base Currency:</strong> {base_currency}</p>
        <p><strong>Sort By:</strong> {sort_by} ({'ascending' if ascending else 'descending'})</p>
        <p><strong>Generated at (UTC):</strong> {ts_now}</p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Uebersicht</h3>
            <p><strong>Anzahl Strategien:</strong> {total_strategies}</p>
            <p><strong>Anzahl Paper-Runs:</strong> {n_paper_runs}</p>
        </div>
        <div class="card">
            <h3>Aggregierte PnL</h3>
            <p><strong>Total PnL (Netto):</strong> <span class="{pnl_class}">{total_pnl_net:.2f} {base_currency}</span></p>
            <p><strong>Total Fees:</strong> {total_fees_all:.2f} {base_currency}</p>
        </div>
        <div class="card">
            <h3>Volumen</h3>
            <p><strong>Total Notional:</strong> {total_notional_all:.2f} {base_currency}</p>
        </div>
    </div>

    <div class="section">
        <h2>Strategy Leaderboard</h2>
        <p>Aggregierte KPIs pro Strategy, sortiert nach <code>{sort_by}</code>.</p>
        {html_table}
    </div>
</body>
</html>
"""


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📊 Peak_Trade Strategy-Level Paper KPIs")
    print("=" * 70)

    cfg = load_config(args.config_path)
    base_currency = str(cfg.get("live.base_currency", "EUR"))

    df_paper = _load_paper_runs()
    n_paper_runs = len(df_paper)
    print(f"   {n_paper_runs} paper_trade-Runs aus Registry geladen.")

    df_kpis = aggregate_by_strategy(df_paper)
    n_strategies = len(df_kpis)
    print(f"   {n_strategies} eindeutige Strategien identifiziert.")

    # Sortieren
    if args.sort_by in df_kpis.columns:
        df_kpis = df_kpis.sort_values(by=args.sort_by, ascending=args.ascending)
    else:
        print(f"   Warnung: Sortier-Spalte '{args.sort_by}' nicht gefunden, verwende default.")
        df_kpis = df_kpis.sort_values(by="realized_pnl_net", ascending=False)

    # Top N
    df_kpis_top = df_kpis.head(args.top)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # CSV Export
    csv_path = out_dir / f"paper_kpi_leaderboard_{ts_label}.csv"
    df_kpis.to_csv(csv_path, index=False)
    print(f"\n💾 CSV-Export: {csv_path}")

    # HTML Leaderboard
    html = build_html_leaderboard(
        cfg=cfg,
        df_kpis=df_kpis_top,
        n_paper_runs=n_paper_runs,
        sort_by=args.sort_by,
        ascending=args.ascending,
    )

    html_path = out_dir / f"paper_kpi_leaderboard_{ts_label}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"   HTML-Leaderboard: {html_path}")

    # Experiment-Logging
    stats = {
        "n_strategies": n_strategies,
        "n_paper_runs": n_paper_runs,
        "total_pnl_net": float(df_kpis["realized_pnl_net"].sum()),
        "total_fees": float(df_kpis["total_fees"].sum()),
        "total_notional": float(df_kpis["total_notional"].sum()),
        "top_strategy": str(df_kpis.iloc[0]["strategy_key"]) if not df_kpis.empty else "n/a",
        "top_strategy_pnl_net": float(df_kpis.iloc[0]["realized_pnl_net"]) if not df_kpis.empty else 0.0,
    }

    log_generic_experiment(
        run_type="paper_kpi_report",
        run_name=f"paper_kpi_leaderboard_{ts_label}",
        stats=stats,
        report_dir=out_dir,
        report_prefix=f"paper_kpi_leaderboard_{ts_label}",
        extra_metadata={
            "runner": "report_paper_kpis.py",
            "csv_path": str(csv_path),
            "html_path": str(html_path),
            "base_currency": base_currency,
            "sort_by": args.sort_by,
            "ascending": args.ascending,
            "top": args.top,
        },
    )

    print(f"\n📝 Paper-KPI-Report in Registry geloggt (run_type='paper_kpi_report')")
    print(f"\n✅ Strategy-Level Paper KPIs Report abgeschlossen!\n")


if __name__ == "__main__":
    main()
