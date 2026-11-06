#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/paper_trade_from_orders.py
"""
Peak_Trade: Paper-Trade-Simulation aus Orders-CSV
==================================================

Verarbeitet eine Orders-CSV (aus preview_live_orders.py) mit dem PaperBroker,
fuehrt Cash- und Positionsfuehrung durch und speichert Reports.

Workflow-Empfehlung:

    1. Forward-Signale generieren:
       python scripts/generate_forward_signals.py --strategy ma_crossover

    2. Vorschau der Orders erstellen:
       python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv

    3. Paper-Trade mit Risk-Check ausführen:
       python scripts/paper_trade_from_orders.py --orders reports/live/..._orders.csv \\
           --starting-cash 10000 --enforce-live-risk --tag paper-session

Usage:
    python scripts/paper_trade_from_orders.py --orders reports/live/preview_..._orders.csv
    python scripts/paper_trade_from_orders.py --orders ... --starting-cash 5000 --tag daily
    python scripts/paper_trade_from_orders.py --orders ... --enforce-live-risk
    python scripts/paper_trade_from_orders.py --orders ... --skip-live-risk
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List

# Pfad-Setup wie in anderen Scripts
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_paper_trade_run
from src.live.orders import load_orders_csv
from src.live.broker_base import PaperBroker
from src.live.workflows import (
    run_live_risk_check,
    RiskCheckContext,
    validate_risk_flags,
    LiveRiskViolationError,
)
from src.orders import (
    PaperMarketContext,
    PaperOrderExecutor,
    to_order_requests,
    OrderExecutionResult,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Paper-Trade-Simulation aus Orders-CSV (Pseudo-Broker mit Positionsfuehrung).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/paper_trade_from_orders.py --orders reports/live/..._orders.csv
  python scripts/paper_trade_from_orders.py --orders ... --starting-cash 5000 --tag daily
  python scripts/paper_trade_from_orders.py --orders ... --enforce-live-risk
        """,
    )
    # Positional argument (optional, fuer Rueckwaertskompatibilitaet)
    parser.add_argument(
        "orders_csv",
        nargs="?",
        help="Pfad zur Orders-CSV (erzeugt von preview_live_orders.py).",
    )
    # --orders als Alternative zum positional argument
    parser.add_argument(
        "--orders",
        dest="orders_csv_opt",
        help="Alternative zu positional 'orders_csv'. Beispiel: --orders reports/live/..._orders.csv",
    )
    # Kern-Argumente (konsistent mit anderen Scripts)
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--tag",
        help="Optionaler Tag für Registry-Logging (z.B. 'daily', 'paper-session').",
    )
    parser.add_argument(
        "--starting-cash",
        dest="start_cash",
        type=float,
        help="Startkapital fuer Paper-Trade. Falls nicht gesetzt, wird live.starting_cash_default verwendet.",
    )
    parser.add_argument(
        "--run-name",
        help="Name fuer den Paper-Trade-Run (wird in der Registry verwendet).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/paper",
        help="Verzeichnis fuer Positions-/Trade-Reports (Default: reports/paper).",
    )
    parser.add_argument(
        "--no-log-trades",
        action="store_true",
        help="Wenn gesetzt, werden Trades nicht einzeln im Terminal geloggt (nur Summary).",
    )
    parser.add_argument(
        "--no-fees",
        action="store_true",
        help="Wenn gesetzt, werden Fees fuer diesen Run auf 0 gesetzt (unabhaengig von config.toml).",
    )
    parser.add_argument(
        "--no-slippage",
        action="store_true",
        help="Wenn gesetzt, wird Slippage fuer diesen Run auf 0 gesetzt (unabhaengig von config.toml).",
    )
    parser.add_argument(
        "--fee-bps",
        type=float,
        help="Override fuer live.fee_bps (in bp, z.B. 10 = 0.10%%).",
    )
    parser.add_argument(
        "--slippage-bps",
        type=float,
        help="Override fuer live.slippage_bps (in bp).",
    )
    parser.add_argument(
        "--enforce-live-risk",
        action="store_true",
        help=(
            "Live-Risk-Limits für diese Paper-Trade-Batch prüfen und bei Verletzung "
            "mit Fehler abbrechen."
        ),
    )
    parser.add_argument(
        "--skip-live-risk",
        action="store_true",
        help="Live-Risk-Limits für diesen Paper-Run komplett überspringen.",
    )
    parser.add_argument(
        "--use-order-layer",
        action="store_true",
        help=(
            "Nutze den neuen Order-Layer (src/orders) statt des alten PaperBroker. "
            "Der Order-Layer bietet eine abstrahierte Order-Ausfuehrung."
        ),
    )

    args = parser.parse_args(argv)

    # orders_csv bestimmen: --orders hat Vorrang vor positional
    if args.orders_csv_opt:
        args.orders_csv = args.orders_csv_opt
    elif not args.orders_csv:
        parser.error("Bitte entweder positional 'orders_csv' oder --orders angeben.")

    return args


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    orders_path = Path(args.orders_csv)
    if not orders_path.is_file():
        raise SystemExit(f"Orders-CSV nicht gefunden: {orders_path}")

    print("\n📊 Peak_Trade Paper-Trade-Simulation")
    print("=" * 70)

    cfg = load_config(args.config_path)
    base_currency = cfg.get("live.base_currency", "EUR")

    if args.start_cash is not None:
        starting_cash = float(args.start_cash)
    else:
        starting_cash = float(cfg.get("live.starting_cash_default", 10000.0))

    # Fees & Slippage aus Config laden
    fee_bps = float(cfg.get("live.fee_bps", 0.0))
    fee_min_per_order = float(cfg.get("live.fee_min_per_order", 0.0))
    slippage_bps = float(cfg.get("live.slippage_bps", 0.0))

    # CLI-Overrides
    if args.fee_bps is not None:
        fee_bps = float(args.fee_bps)
    if args.slippage_bps is not None:
        slippage_bps = float(args.slippage_bps)
    if args.no_fees:
        fee_bps = 0.0
        fee_min_per_order = 0.0
    if args.no_slippage:
        slippage_bps = 0.0

    print(f"\n📥 Lade Orders-CSV: {orders_path}")
    orders = load_orders_csv(orders_path)
    if not orders:
        print("⚠️  Keine Orders in CSV gefunden – nichts zu simulieren.")
        return

    print(f"   {len(orders)} Orders geladen")

    # Live-Risk-Limits prüfen (über zentralen Helper)
    try:
        validate_risk_flags(args.enforce_live_risk, args.skip_live_risk)
    except ValueError as e:
        print(f"\n❌ FEHLER: {e}")
        return

    ctx = RiskCheckContext(
        config=cfg,
        starting_cash=starting_cash,
        enforce=args.enforce_live_risk,
        skip=args.skip_live_risk,
        tag=args.tag,
        config_path=args.config_path,
        log_to_registry=True,
        runner_name="paper_trade_from_orders.py",
    )

    try:
        risk_result = run_live_risk_check(
            orders=orders,
            ctx=ctx,
            orders_csv=str(orders_path),
        )
    except LiveRiskViolationError as e:
        print(f"\n❌ ABBRUCH: {e}")
        print("   Paper-Trade wird NICHT ausgeführt.")
        sys.exit(1)

    # Bei Verletzung ohne Enforcement: Warnung, aber fortfahren
    if risk_result is not None and not risk_result.allowed and not args.enforce_live_risk:
        print("\n⚠️  Warnung: Risk-Verletzung erkannt, Paper-Trade wird trotzdem fortgesetzt.")

    print(f"\n💰 Start-Cash: {starting_cash:.2f} {base_currency}")

    # Entscheide welchen Executor nutzen
    if args.use_order_layer:
        # Neuer Order-Layer (src/orders)
        print("\n🔧 Verwende neuen Order-Layer (src/orders)")

        # Marktkontext aus Orders bauen (Preise aus extra.current_price)
        prices: dict[str, float] = {}
        for order in orders:
            if order.extra and order.extra.get("current_price"):
                prices[order.symbol] = float(order.extra["current_price"])

        market_ctx = PaperMarketContext(
            prices=prices,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            base_currency=base_currency,
        )

        executor = PaperOrderExecutor(market_ctx)

        # LiveOrderRequest -> OrderRequest konvertieren
        order_requests = to_order_requests(orders)

        if not args.no_log_trades:
            print("\n📤 Fuehre Paper-Trades aus (Order-Layer)...")
            print("-" * 70)

        # Orders ausfuehren
        execution_results = executor.execute_orders(order_requests)

        # Ergebnisse anzeigen
        if not args.no_log_trades:
            for result in execution_results:
                if result.is_filled and result.fill:
                    fill = result.fill
                    print(
                        f"[ORDER-LAYER] {fill.side.upper()} {fill.symbol} "
                        f"qty={fill.quantity:.8f} price={fill.price:.8f} "
                        f"fee={fill.fee or 0:.4f} {base_currency}"
                    )
                elif result.is_rejected:
                    print(f"[ORDER-LAYER] REJECTED {result.request.symbol}: {result.reason}")

        # Summary-Metriken aus ExecutionResults berechnen
        filled_results = [r for r in execution_results if r.is_filled and r.fill]
        total_fees = sum(r.fill.fee or 0 for r in filled_results)
        total_notional = sum(r.metadata.get("notional", 0) for r in filled_results)

        # Einfache Equity-Berechnung (nur fuer Summary)
        # HINWEIS: Der Order-Layer trackt keine Positionen wie der PaperBroker
        ending_cash = starting_cash - total_notional - total_fees
        total_market_value = total_notional  # Vereinfacht
        total_realized_pnl = 0.0  # Order-Layer trackt kein PnL
        total_unrealized_pnl = 0.0
        n_positions = len(set(r.fill.symbol for r in filled_results))

        # Leere DataFrames (Order-Layer hat kein Positions-/Trade-Tracking wie PaperBroker)
        import pandas as pd

        positions_df = pd.DataFrame(
            columns=[
                "symbol",
                "quantity",
                "avg_price",
                "last_price",
                "market_value",
                "unrealized_pnl",
                "realized_pnl",
            ]
        )
        trades_df = pd.DataFrame(
            [
                {
                    "ts": r.fill.timestamp.isoformat() if r.fill else None,
                    "symbol": r.fill.symbol if r.fill else None,
                    "side": r.fill.side if r.fill else None,
                    "quantity": r.fill.quantity if r.fill else None,
                    "price": r.fill.price if r.fill else None,
                    "fee": r.fill.fee if r.fill else None,
                    "client_order_id": r.request.client_id,
                }
                for r in filled_results
            ]
        )

    else:
        # Alter PaperBroker (bestehende Logik)
        broker = PaperBroker(
            starting_cash=starting_cash,
            base_currency=base_currency,
            log_to_console=not args.no_log_trades,
            fee_bps=fee_bps,
            fee_min_per_order=fee_min_per_order,
            slippage_bps=slippage_bps,
        )

        if not args.no_log_trades:
            print("\n📤 Fuehre Paper-Trades aus...")
            print("-" * 70)

        reports = broker.submit_orders(orders)

        positions_df = broker.get_positions_df()
        trades_df = broker.get_trades_df()

        # Summary-Metriken berechnen (wie bisher)
        if not positions_df.empty:
            total_market_value = float(positions_df["market_value"].fillna(0.0).sum())
            total_realized_pnl = float(positions_df["realized_pnl"].fillna(0.0).sum())
            total_unrealized_pnl = float(positions_df["unrealized_pnl"].fillna(0.0).sum())
            n_positions = int(len(positions_df))
        else:
            total_market_value = 0.0
            total_realized_pnl = 0.0
            total_unrealized_pnl = 0.0
            n_positions = 0

        # Fees aus Trade-Log extrahieren
        if not trades_df.empty and "fee" in trades_df.columns:
            total_fees = float(trades_df["fee"].fillna(0.0).sum())
        else:
            total_fees = 0.0

        ending_cash = broker.cash

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    orders_stem = orders_path.stem

    positions_path = out_dir / f"paper_positions_{orders_stem}_{ts_label}.csv"
    trades_path = out_dir / f"paper_trades_{orders_stem}_{ts_label}.csv"

    positions_df.to_csv(positions_path, index=False)
    trades_df.to_csv(trades_path, index=False)

    realized_pnl_after_fees = total_realized_pnl - total_fees
    equity = ending_cash + total_market_value

    print("\n📈 Paper-Trade Summary:")
    print("-" * 70)
    print(f"   Start-Cash:             {starting_cash:12.2f} {base_currency}")
    print(f"   End-Cash:               {ending_cash:12.2f} {base_currency}")
    print(f"   Market Value:           {total_market_value:12.2f} {base_currency}")
    print(f"   Equity:                 {equity:12.2f} {base_currency}")
    print(f"   Realized PnL (Price):   {total_realized_pnl:12.2f} {base_currency}")
    print(f"   Total Fees:             {total_fees:12.2f} {base_currency}")
    print(f"   Realized PnL (Netto):   {realized_pnl_after_fees:12.2f} {base_currency}")
    print(f"   Unrealized PnL:         {total_unrealized_pnl:12.2f} {base_currency}")
    print(f"   Anzahl Orders:          {len(orders):12d}")
    print(f"   Anzahl Positions:       {n_positions:12d}")
    print(
        f"   Fee-Modell:             fee_bps={fee_bps:.3f}, fee_min_per_order={fee_min_per_order:.4f}"
    )
    print(f"   Slippage-Modell:        slippage_bps={slippage_bps:.3f}")

    print(f"\n💾 Reports gespeichert:")
    print(f"   Positions: {positions_path}")
    print(f"   Trades:    {trades_path}")

    # Experiment-Logging
    run_name = args.run_name or f"paper_trade_{orders_stem}_{ts_label}"

    stats = {
        "starting_cash": starting_cash,
        "ending_cash": ending_cash,
        "market_value": total_market_value,
        "equity": equity,
        "realized_pnl_total": total_realized_pnl,
        "unrealized_pnl_total": total_unrealized_pnl,
        "total_fees": total_fees,
        "realized_pnl_net": realized_pnl_after_fees,
        "n_orders": int(len(orders)),
        "n_positions": int(n_positions),
        "fee_bps": fee_bps,
        "fee_min_per_order": fee_min_per_order,
        "slippage_bps": slippage_bps,
    }

    run_id = log_paper_trade_run(
        stats=stats,
        orders_csv=str(orders_path),
        positions_csv=str(positions_path),
        trades_csv=str(trades_path),
        tag=args.tag,
        config_path=args.config_path,
        extra_metadata={
            "base_currency": base_currency,
            "run_name": run_name,
        },
    )

    print(f"\n📝 Paper-Trade in Registry geloggt (run_type='paper_trade')")
    print(f"   Run-ID: {run_id}")
    if args.tag:
        print(f"   Tag: {args.tag}")
    print(f"\n✅ Paper-Trade-Simulation abgeschlossen!\n")


if __name__ == "__main__":
    main()
