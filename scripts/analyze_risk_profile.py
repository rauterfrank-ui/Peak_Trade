# scripts/analyze_risk_profile.py
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.peak_config import load_config
from src.core.experiments import log_generic_experiment
from src.analytics.risk_monitor import (
    RiskPolicy,
    load_experiments_df,
    filter_by_lookback,
    annotate_runs_with_risk,
    aggregate_strategy_risk,
    aggregate_portfolio_risk,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Risk & Monitoring Analyse basierend auf der Experiment-Registry.",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--run-type",
        help=(
            "Optional: nur bestimmte run_type(s) betrachten (Komma-separiert), "
            "z.B. 'single_backtest,sweep,portfolio'."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="reports/risk",
        help="Zielverzeichnis für Risk-Reports (CSV + HTML). Default: reports/risk",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Wenn gesetzt, wird kein HTML-Dashboard erzeugt.",
    )
    return parser.parse_args(argv)


def _df_to_html_table(df: pd.DataFrame, table_class: str = "risk-table") -> str:
    if df.empty:
        return "<p><em>Keine Daten.</em></p>"

    return df.to_html(
        index=False,
        border=0,
        classes=table_class,
        float_format=lambda x: f"{x:.6g}",
    )


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    cfg = load_config(args.config_path)
    policy = RiskPolicy.from_config(cfg)

    df = load_experiments_df()
    df = filter_by_lookback(df, policy)

    if args.run_type:
        allowed = {rt.strip() for rt in args.run_type.split(",") if rt.strip()}
        df = df[df["run_type"].isin(allowed)]

    if df.empty:
        print("Keine Experimente im gewählten Zeitraum / Filter – nichts zu analysieren.")
        return

    df_runs = annotate_runs_with_risk(df, policy)
    df_strat = aggregate_strategy_risk(df_runs, policy)
    df_port = aggregate_portfolio_risk(df_runs, policy)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    runs_csv = out_dir / f"risk_runs_{ts_label}.csv"
    strat_csv = out_dir / f"risk_strategies_{ts_label}.csv"
    port_csv = out_dir / f"risk_portfolios_{ts_label}.csv"

    df_runs.to_csv(runs_csv, index=False)
    df_strat.to_csv(strat_csv, index=False)
    df_port.to_csv(port_csv, index=False)

    print(f"Risk-Runs CSV:        {runs_csv}")
    print(f"Risk-Strategien CSV:  {strat_csv}")
    print(f"Risk-Portfolios CSV:  {port_csv}")

    print("\n=== Strategie-Risiko (Top nach n_runs) ===")
    if not df_strat.empty:
        print(df_strat.sort_values(by="n_runs", ascending=False).head(20).to_string(index=False))
    else:
        print("Keine Strategie-Aggregationen.")

    print("\n=== Portfolio-Risiko (Top nach n_runs) ===")
    if not df_port.empty:
        print(df_port.sort_values(by="n_runs", ascending=False).head(20).to_string(index=False))
    else:
        print("Keine Portfolio-Aggregationen.")

    html_path = None
    if not args.no_html:
        html_path = out_dir / f"risk_dashboard_{ts_label}.html"

        html_runs = _df_to_html_table(df_runs, "risk-table risk-table-runs")
        html_strat = _df_to_html_table(df_strat, "risk-table risk-table-strategies")
        html_port = _df_to_html_table(df_port, "risk-table risk-table-portfolios")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Peak_Trade Risk Dashboard</title>
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
        table.risk-table {{
            border-collapse: collapse;
            width: 100%;
            max-width: 1200px;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        table.risk-table th, table.risk-table td {{
            border: 1px solid #444;
            padding: 0.35rem 0.5rem;
        }}
        table.risk-table th {{
            background-color: #222;
        }}
        .section {{
            margin-bottom: 2.5rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.1rem 0.4rem;
            border-radius: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-ok {{
            background-color: #164b1f;
            color: #8df7a0;
        }}
        .badge-watch {{
            background-color: #4b3f16;
            color: #f5e58a;
        }}
        .badge-blocked {{
            background-color: #4b1616;
            color: #ff8a8a;
        }}
        .badge-unknown {{
            background-color: #333;
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
    <h1>Peak_Trade – Risk Dashboard</h1>

    <div class="meta">
        <p><strong>Lookback (Tage):</strong> {policy.lookback_days}</p>
        <p><strong>Gefilterte run_types:</strong> {args.run_type or "ALLE"}</p>
        <p><strong>Runs in Analyse:</strong> {len(df_runs)}</p>
        <p><strong>Strategien in Analyse:</strong> {len(df_strat)}</p>
        <p><strong>Portfolios in Analyse:</strong> {len(df_port)}</p>
    </div>

    <div class="section">
        <h2>1. Strategien – Risk Overview</h2>
        <p>Aggregierte Risiko-Sicht pro Strategy-Key (Status: OK / WATCH / BLOCKED / UNKNOWN).</p>
        {html_strat}
    </div>

    <div class="section">
        <h2>2. Portfolios – Risk Overview</h2>
        <p>Aggregierte Risiko-Sicht pro Portfolio (nur runs mit run_type='portfolio').</p>
        {html_port}
    </div>

    <div class="section">
        <h2>3. Einzel-Runs – Detailansicht</h2>
        <p>Alle Runs im Lookback-Zeitraum inkl. risk_status_run und risk_reasons_run.</p>
        {html_runs}
    </div>
</body>
</html>
"""
        html_path.write_text(html, encoding="utf-8")
        print(f"\nRisk-Dashboard HTML: {html_path}")

    stats = {
        "n_runs_analyzed": int(len(df_runs)),
        "n_strategies_analyzed": int(len(df_strat)),
        "n_portfolios_analyzed": int(len(df_port)),
        "n_blocked_strategies": (
            int((df_strat["risk_status_group"] == "BLOCKED").sum()) if not df_strat.empty else 0
        ),
        "n_watch_strategies": (
            int((df_strat["risk_status_group"] == "WATCH").sum()) if not df_strat.empty else 0
        ),
    }

    log_generic_experiment(
        run_type="risk_analysis",
        run_name=f"risk_analysis_{ts_label}",
        stats=stats,
        report_dir=out_dir,
        report_prefix=f"risk_{ts_label}",
        extra_metadata={
            "runner": "analyze_risk_profile.py",
            "runs_csv": str(runs_csv),
            "strategies_csv": str(strat_csv),
            "portfolios_csv": str(port_csv),
            "html_path": str(html_path) if html_path is not None else None,
            "risk_policy": policy.__dict__,
            "filter_run_type": args.run_type,
        },
    )
    print("Risk-Analyse in Registry geloggt (run_type='risk_analysis').")


if __name__ == "__main__":
    main()
