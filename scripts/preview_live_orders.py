#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/preview_live_orders.py
"""
Peak_Trade: Forward-Signale → Order-Preview
============================================

Liest eine Signals-CSV ein, lädt aktuelle/letzte Preise pro Symbol,
baut aus jedem Signal (direction ≠ 0) eine LiveOrderRequest und speichert
die Orders als CSV unter reports/live/.

Workflow-Empfehlung:

    1. Forward-Signale generieren:
       python scripts/generate_forward_signals.py --strategy ma_crossover

    2. Vorschau der Orders mit Risk-Check:
       python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv --tag precheck

    3. Bei Bedarf Paper-Trade ausführen:
       python scripts/paper_trade_from_orders.py --orders reports/live/..._orders.csv --enforce-live-risk

Usage:
    python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv
    python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv --notional 500 --tag daily
    python scripts/preview_live_orders.py --signals ... --enforce-live-risk
    python scripts/preview_live_orders.py --signals ... --skip-live-risk
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import uuid

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import numpy as np

from src.core.peak_config import load_config, PeakConfig
from src.forward.signals import load_signals_csv
from src.live.orders import (
    LiveOrderRequest,
    save_orders_to_csv,
    side_from_direction,
)
from src.live.workflows import (
    run_live_risk_check,
    RiskCheckContext,
    validate_risk_flags,
    LiveRiskViolationError,
)
from src.orders import OrderRequest, to_order_requests


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Forward-Signale → Order-Preview.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv
  python scripts/preview_live_orders.py --signals ... --notional 500 --tag daily
  python scripts/preview_live_orders.py --signals ... --enforce-live-risk
        """,
    )
    # Positional argument (optional, für Rückwärtskompatibilität)
    parser.add_argument(
        "signals_csv",
        nargs="?",
        help="Pfad zur Signals-CSV (erzeugt von generate_forward_signals.py).",
    )
    # --signals als Alternative zum positional argument
    parser.add_argument(
        "--signals",
        dest="signals_csv_opt",
        help=(
            "Pfad zur Forward-Signal-CSV (Alternative zu positional 'signals_csv'). "
            "Beispiel: --signals reports/forward/..._signals.csv"
        ),
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
        help="Optionaler Tag für Registry-Logging (z.B. 'daily', 'precheck').",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/live",
        help="Zielverzeichnis für Order-CSV (Default: reports/live).",
    )
    # --fixed-notional als primäres Argument
    parser.add_argument(
        "--fixed-notional",
        type=float,
        default=100.0,
        help="Notional pro Trade (Default: 100.0).",
    )
    # --notional als Alias für --fixed-notional
    parser.add_argument(
        "--notional",
        dest="notional_alias",
        type=float,
        help="Alias für --fixed-notional (Notional pro Trade).",
    )
    parser.add_argument(
        "--preview-name",
        help="Name des Preview-Runs (Default: preview_<timestamp>).",
    )
    parser.add_argument(
        "--enforce-live-risk",
        action="store_true",
        help=(
            "Live-Risk-Limits aus config.toml prüfen und bei Verletzung mit Fehler abbrechen. "
            "Ohne dieses Flag werden Verletzungen nur als Warnung ausgegeben."
        ),
    )
    parser.add_argument(
        "--skip-live-risk",
        action="store_true",
        help="Live-Risk-Limits für diesen Run komplett überspringen, auch wenn live_risk.enabled = true.",
    )

    args = parser.parse_args(argv)

    # signals_csv bestimmen: --signals hat Vorrang vor positional
    if args.signals_csv_opt:
        args.signals_csv = args.signals_csv_opt
    elif not args.signals_csv:
        parser.error("Bitte entweder positional 'signals_csv' oder --signals angeben.")

    # notional bestimmen: --notional hat Vorrang vor --fixed-notional
    if args.notional_alias is not None:
        args.fixed_notional = args.notional_alias

    return args


def get_current_price(symbol: str) -> float:
    """
    Holt den aktuellen/letzten Preis für ein Symbol.

    Aktuell: Dummy-Implementation mit plausiblen Preisen.
    NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Echte Daten-Adapter: preview_live_orders.py")

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")

    Returns:
        Aktueller Preis
    """
    # Seed für Reproduzierbarkeit
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Basispreise nach Symbol
    if "BTC" in symbol:
        base_price = 50000 + np.random.randn() * 1000
    elif "ETH" in symbol:
        base_price = 3000 + np.random.randn() * 100
    elif "LTC" in symbol:
        base_price = 100 + np.random.randn() * 5
    else:
        base_price = 1000 + np.random.randn() * 50

    return round(base_price, 2)


def signals_to_orders(
    df_signals: pd.DataFrame,
    default_notional: float,
    preview_name: str,
) -> List[LiveOrderRequest]:
    """
    Wandelt Signals-DataFrame in eine Liste von LiveOrderRequest um.

    Args:
        df_signals: DataFrame mit Spalten symbol, direction, as_of, strategy_key, run_name
        default_notional: Notional-Betrag pro Order
        preview_name: Name des Preview-Runs

    Returns:
        Liste von LiveOrderRequest (nur für direction != 0)
    """
    orders: List[LiveOrderRequest] = []

    for _, row in df_signals.iterrows():
        direction = float(row["direction"])
        if direction == 0:
            continue

        symbol = str(row["symbol"])
        side = side_from_direction(direction)

        if side is None:
            continue

        # Aktuellen Preis holen
        current_price = get_current_price(symbol)

        # Quantity aus Notional berechnen
        quantity = round(default_notional / current_price, 8)

        order = LiveOrderRequest(
            client_order_id=f"{preview_name}_{symbol.replace('/', '_')}_{uuid.uuid4().hex[:8]}",
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            notional=default_notional,
            time_in_force="GTC",
            strategy_key=str(row["strategy_key"]),
            run_name=str(row["run_name"]),
            signal_as_of=str(row["as_of"]),
            comment=f"Preview generated from signals CSV",
            extra={
                "current_price": current_price,
                "original_direction": direction,
            },
        )
        orders.append(order)

    return orders


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n📋 Peak_Trade Order Preview")
    print("=" * 70)

    cfg = load_config(args.config_path)

    # Signals-CSV laden
    signals_path = Path(args.signals_csv)
    print(f"\n📥 Lade Signals-CSV: {signals_path}")
    df_signals = load_signals_csv(signals_path)
    print(f"   {len(df_signals)} Signale geladen")

    # Notional bestimmen: CLI-Wert > Config-Wert
    # args.fixed_notional ist entweder der Wert von --fixed-notional, --notional, oder der Default (100.0)
    if args.fixed_notional != 100.0 or args.notional_alias is not None:
        # Explizit gesetzt via CLI
        default_notional = args.fixed_notional
    else:
        # Fallback auf Config
        default_notional = cfg.get("live.max_notional_per_order", 1000.0)

    print(f"\n💰 Notional pro Order: {default_notional:.2f} {cfg.get('live.base_currency', 'EUR')}")

    # Preview-Name
    preview_name = args.preview_name or f"preview_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Signals → Orders
    orders = signals_to_orders(df_signals, default_notional, preview_name)

    if not orders:
        print("\n⚠️  Keine Orders generiert (alle Signale haben direction=0).")
        return

    print(f"\n📊 {len(orders)} Orders generiert:")
    print("-" * 70)

    for order in orders:
        current_price = order.extra.get("current_price", "?") if order.extra else "?"
        print(
            f"  {order.side:4s} {order.symbol:10s} "
            f"qty={order.quantity:.6f} @ ~{current_price} "
            f"notional={order.notional:.2f}"
        )

    # Live-Risk-Limits prüfen (über zentralen Helper)
    try:
        validate_risk_flags(args.enforce_live_risk, args.skip_live_risk)
    except ValueError as e:
        print(f"\n❌ FEHLER: {e}")
        return

    ctx = RiskCheckContext(
        config=cfg,
        starting_cash=None,  # Preview braucht kein starting_cash
        enforce=args.enforce_live_risk,
        skip=args.skip_live_risk,
        tag=args.tag,
        config_path=args.config_path,
        log_to_registry=True,
        runner_name="preview_live_orders.py",
    )

    try:
        risk_result = run_live_risk_check(
            orders=orders,
            ctx=ctx,
            orders_csv=str(signals_path),
            extra_metadata={"preview_name": preview_name},
        )
    except LiveRiskViolationError as e:
        print(f"\n❌ ABBRUCH: {e}")
        sys.exit(1)

    # Bei Verletzung ohne Enforcement: Warnung, aber fortfahren
    if risk_result is not None and not risk_result.allowed and not args.enforce_live_risk:
        print("\n⚠️  Warnung: Risk-Verletzung erkannt, aber --enforce-live-risk nicht gesetzt.")

    # Output-Verzeichnis erstellen und Orders speichern
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{preview_name}_orders.csv"

    df_orders = save_orders_to_csv(orders, out_path)
    print(f"\n💾 Orders gespeichert: {out_path}")

    # Zusammenfassung
    print("\n📈 Zusammenfassung:")
    print(f"   Signale gelesen:    {len(df_signals)}")
    print(f"   Orders generiert:   {len(orders)}")
    print(f"   BUY-Orders:         {sum(1 for o in orders if o.side == 'BUY')}")
    print(f"   SELL-Orders:        {sum(1 for o in orders if o.side == 'SELL')}")
    print(f"   Total Notional:     {sum(o.notional or 0 for o in orders):.2f}")

    # Order-Layer Kompatibilität zeigen
    try:
        order_requests = to_order_requests(orders)
        print(f"\n🔧 Order-Layer Kompatibilität:")
        print(f"   {len(order_requests)} OrderRequest-Objekte erstellt")
        print(f"   Bereit für PaperOrderExecutor (--use-order-layer in paper_trade_from_orders.py)")
    except Exception as e:
        print(f"\n⚠️  Order-Layer Konvertierung fehlgeschlagen: {e}")

    print(f"\n✅ Order-Preview abgeschlossen!\n")


if __name__ == "__main__":
    main()
