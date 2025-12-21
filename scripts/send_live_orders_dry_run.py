#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/send_live_orders_dry_run.py
"""
Peak_Trade: Dry-Run Order Submission
=====================================

Liest eine Order-CSV (z.B. von preview_live_orders.py erzeugt) und
"versendet" die Orders via DryRunBroker (= nur Logging, kein echter Handel).

Usage:
    python scripts/send_live_orders_dry_run.py --orders reports/live/preview_20251204_orders.csv
    python scripts/send_live_orders_dry_run.py --orders reports/live/preview_20251204_orders.csv --output-dir reports/live/executions
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_generic_experiment
from src.live.orders import (
    LiveOrderRequest,
    LiveExecutionReport,
    load_orders_csv,
)
from src.live.broker_base import DryRunBroker


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Dry-Run Order Submission.",
    )
    # Positional argument (optional, für Rückwärtskompatibilität)
    parser.add_argument(
        "orders_csv",
        nargs="?",
        help="Pfad zur Orders-CSV (erzeugt von preview_live_orders.py).",
    )
    # --orders als Alternative zum positional argument
    parser.add_argument(
        "--orders",
        dest="orders_csv_opt",
        help=(
            "Pfad zur Orders-CSV (Alternative zu positional 'orders_csv'). "
            "Beispiel: --orders reports/live/..._orders.csv"
        ),
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/live/executions",
        help="Zielverzeichnis für Execution-Reports (Default: reports/live/executions).",
    )
    parser.add_argument(
        "--run-name",
        help="Name dieses Dry-Run-Laufs (Default: dryrun_<timestamp>).",
    )

    args = parser.parse_args(argv)

    # orders_csv bestimmen: --orders hat Vorrang vor positional
    if args.orders_csv_opt:
        args.orders_csv = args.orders_csv_opt
    elif not args.orders_csv:
        parser.error("Bitte entweder positional 'orders_csv' oder --orders angeben.")

    return args


def save_executions_to_csv(
    reports: List[LiveExecutionReport],
    path: Path,
) -> pd.DataFrame:
    """
    Speichert ExecutionReports als CSV.

    Args:
        reports: Liste von LiveExecutionReport
        path: Zielpfad

    Returns:
        DataFrame der gespeicherten Reports
    """
    import json
    from dataclasses import asdict

    rows = []
    for rep in reports:
        d = asdict(rep)
        extra = d.pop("extra", None)
        d["extra_json"] = json.dumps(extra, ensure_ascii=False) if extra else None
        rows.append(d)

    if not rows:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows)

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n🚀 Peak_Trade Dry-Run Order Submission")
    print("=" * 70)

    cfg = load_config(args.config_path)

    # Mode-Check
    live_mode = cfg.get("live.mode", "dry_run")
    if live_mode != "dry_run":
        print(
            f"\n⚠️  Warnung: [live].mode = '{live_mode}', aber dieses Script ist nur für dry_run gedacht!"
        )
        print("   Fahre trotzdem fort mit DryRunBroker (kein echter Handel).")

    # Orders-CSV laden
    orders_path = Path(args.orders_csv)
    print(f"\n📥 Lade Order-CSV: {orders_path}")

    if not orders_path.is_file():
        raise FileNotFoundError(f"Order-CSV nicht gefunden: {orders_path}")

    # load_orders_csv returns List[LiveOrderRequest] directly
    requests = load_orders_csv(orders_path)
    print(f"   {len(requests)} Orders geladen")

    if not requests:
        print("\n⚠️  Keine Orders in der CSV – nichts zu tun.")
        return

    # Run-Name
    run_name = args.run_name or f"dryrun_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # DryRunBroker instanziieren und Orders absenden
    print(f"\n🔧 Initialisiere DryRunBroker...")
    broker = DryRunBroker()

    print(f"\n📤 Sende {len(requests)} Orders via DryRunBroker...")
    print("-" * 70)

    reports = broker.submit_orders(requests)

    # Ergebnisse ausgeben
    print("\n📋 Execution Reports:")
    print("-" * 70)

    acknowledged_count = 0
    rejected_count = 0

    for rep in reports:
        # DryRunBroker returns "ACKNOWLEDGED" for successful dry-run orders
        is_success = rep.status in ("ACKNOWLEDGED", "FILLED")
        status_icon = "✅" if is_success else "❌"
        print(
            f"  {status_icon} {rep.client_order_id[:30]:30s} "
            f"status={rep.status:12s} "
            f"msg={rep.message or ''}"
        )
        if is_success:
            acknowledged_count += 1
        else:
            rejected_count += 1

    # Execution-Reports speichern
    out_dir = Path(args.output_dir)
    out_path = out_dir / f"{run_name}_executions.csv"

    df_exec = save_executions_to_csv(reports, out_path)
    print(f"\n💾 Execution-Reports gespeichert: {out_path}")

    # Experiment-Registry loggen
    log_generic_experiment(
        run_type="live_dry_run",
        run_name=run_name,
        strategy_key=requests[0].strategy_key if requests else None,
        symbol=None,
        stats=None,
        report_dir=out_dir,
        report_prefix=run_name,
        extra_metadata={
            "runner": "send_live_orders_dry_run.py",
            "orders_csv": str(orders_path),
            "n_orders": len(requests),
            "n_acknowledged": acknowledged_count,
            "n_rejected": rejected_count,
            "execution_csv": str(out_path),
        },
    )

    # Zusammenfassung
    print("\n📈 Zusammenfassung:")
    print(f"   Orders gelesen:     {len(requests)}")
    print(f"   ACKNOWLEDGED:       {acknowledged_count}")
    print(f"   REJECTED/Andere:    {rejected_count}")
    print(f"   Run logged:         {run_name}")
    print(f"\n✅ Dry-Run Order Submission abgeschlossen!\n")


if __name__ == "__main__":
    main()
