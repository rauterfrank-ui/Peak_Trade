# scripts/select_live_candidates.py
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_generic_experiment
from src.analytics.risk_monitor import (
    RiskPolicy,
    load_experiments_df,
    filter_by_lookback,
    annotate_runs_with_risk,
    aggregate_strategy_risk,
)
from src.analytics.filter_flow import SelectionPolicy, build_strategy_selection


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Auswahl von Live-Kandidaten (Filter-Flow) basierend auf Risk & Forward Eval.",
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
            "z.B. 'single_backtest,sweep,portfolio,forward_eval'."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="reports/selection",
        help="Zielverzeichnis für Selection-Outputs. Default: reports/selection",
    )
    parser.add_argument(
        "--print-approved",
        action="store_true",
        help="Wenn gesetzt, werden die APPROVED-Strategien im Terminal ausgegeben.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    cfg = load_config(args.config_path)
    risk_policy = RiskPolicy.from_config(cfg)
    sel_policy = SelectionPolicy.from_config(cfg)

    df = load_experiments_df()
    df = filter_by_lookback(df, risk_policy)

    if args.run_type:
        allowed = {rt.strip() for rt in args.run_type.split(",") if rt.strip()}
        df = df[df["run_type"].isin(allowed)]

    if df.empty:
        print("Keine Experimente im gewählten Zeitraum / Filter – nichts zu analysieren.")
        return

    df_runs = annotate_runs_with_risk(df, risk_policy)
    df_strat_risk = aggregate_strategy_risk(df_runs, risk_policy)

    df_sel = build_strategy_selection(df_runs, df_strat_risk, sel_policy)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"live_candidates_{ts_label}.csv"
    json_path = out_dir / f"live_candidates_{ts_label}.json"

    df_sel.to_csv(csv_path, index=False)

    approved = df_sel[df_sel["selection_status"] == "APPROVED"]["strategy_key"].dropna().tolist()
    watch = df_sel[df_sel["selection_status"] == "WATCH"]["strategy_key"].dropna().tolist()
    blocked = df_sel[df_sel["selection_status"] == "BLOCKED"]["strategy_key"].dropna().tolist()
    unknown = df_sel[df_sel["selection_status"] == "UNKNOWN"]["strategy_key"].dropna().tolist()

    summary = {
        "approved": approved,
        "watch": watch,
        "blocked": blocked,
        "unknown": unknown,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "config": {
            "filter_flow": sel_policy.__dict__,
            "risk_monitor_lookback_days": risk_policy.lookback_days,
        },
    }

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Selection-CSV:   {csv_path}")
    print(f"Selection-JSON:  {json_path}")
    print(f"APPROVED: {approved}")
    print(f"WATCH:    {watch}")
    print(f"BLOCKED:  {blocked}")
    print(f"UNKNOWN:  {unknown}")

    stats = {
        "n_strategies_total": int(len(df_sel)),
        "n_approved": int(len(approved)),
        "n_watch": int(len(watch)),
        "n_blocked": int(len(blocked)),
        "n_unknown": int(len(unknown)),
    }

    log_generic_experiment(
        run_type="selection_analysis",
        run_name=f"selection_analysis_{ts_label}",
        stats=stats,
        report_dir=out_dir,
        report_prefix=f"selection_{ts_label}",
        extra_metadata={
            "runner": "select_live_candidates.py",
            "selection_csv": str(csv_path),
            "selection_json": str(json_path),
            "filter_flow_policy": sel_policy.__dict__,
        },
    )
    print("Selection-Analyse in Registry geloggt (run_type='selection_analysis').")


if __name__ == "__main__":
    main()
