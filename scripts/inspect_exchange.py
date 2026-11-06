#!/usr/bin/env python3
"""
Peak_Trade – Exchange Inspector (Read-Only)
============================================
CLI-Tool zum Inspizieren von Exchange-Daten.

Dieses Tool ist **read-only** und macht keine Trades oder Order-Änderungen!

Verfügbare Modi:
- ticker:   Aktuellen Preis für ein Symbol anzeigen
- ohlcv:    OHLCV-Candlestick-Daten abrufen
- balance:  Kontostände anzeigen (erfordert API-Key)
- orders:   Offene Orders anzeigen (erfordert API-Key)
- markets:  Verfügbare Märkte/Symbole auflisten
- status:   Exchange-Status und Konfiguration anzeigen

Usage:
    # Ticker abrufen
    python scripts/inspect_exchange.py --mode ticker --symbol BTC/EUR

    # OHLCV-Daten (letzte 10 Candles)
    python scripts/inspect_exchange.py --mode ohlcv --symbol BTC/EUR --limit 10

    # Balance anzeigen (erfordert API-Keys in Config)
    python scripts/inspect_exchange.py --mode balance

    # Verfügbare Märkte auflisten
    python scripts/inspect_exchange.py --mode markets

    # Exchange-Status
    python scripts/inspect_exchange.py --mode status
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config
from src.exchange import build_exchange_client_from_config


def parse_args() -> argparse.Namespace:
    """CLI-Argumente parsen."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Exchange Inspector (Read-Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Ticker für BTC/EUR
  python scripts/inspect_exchange.py --mode ticker --symbol BTC/EUR

  # OHLCV-Daten mit 1h Timeframe
  python scripts/inspect_exchange.py --mode ohlcv --symbol BTC/EUR --timeframe 1h --limit 20

  # Kontostände (benötigt API-Keys)
  python scripts/inspect_exchange.py --mode balance

  # Status und Config anzeigen
  python scripts/inspect_exchange.py --mode status
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur TOML-Config-Datei (default: config.toml)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["ticker", "ohlcv", "balance", "orders", "markets", "status"],
        default="status",
        help="Modus: ticker, ohlcv, balance, orders, markets, status (default: status)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Paar (z.B. BTC/EUR, ETH/USDT). Default: BTC/EUR",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe für OHLCV (z.B. 1m, 5m, 1h, 1d). Default: 1h",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Anzahl OHLCV-Candles oder Märkte. Default: 20",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    return parser.parse_args()


def print_header(title: str) -> None:
    """Druckt einen formatierten Header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_ticker(ticker, symbol: str) -> None:
    """Druckt Ticker-Informationen."""
    print_header(f"Ticker: {symbol}")
    print(f"\n  Symbol:    {ticker.symbol}")
    print(f"  Last:      {ticker.last:,.8f}" if ticker.last else "  Last:      N/A")
    print(f"  Bid:       {ticker.bid:,.8f}" if ticker.bid else "  Bid:       N/A")
    print(f"  Ask:       {ticker.ask:,.8f}" if ticker.ask else "  Ask:       N/A")

    spread = ticker.spread_bps()
    if spread is not None:
        print(f"  Spread:    {spread:.2f} bp")

    if ticker.timestamp:
        from datetime import datetime

        ts = datetime.utcfromtimestamp(ticker.timestamp / 1000)
        print(f"  Timestamp: {ts.isoformat()}Z")

    print()


def print_ohlcv(df, symbol: str, timeframe: str) -> None:
    """Druckt OHLCV-Daten."""
    print_header(f"OHLCV: {symbol} ({timeframe})")

    if df.empty:
        print("\n  Keine Daten verfügbar.\n")
        return

    print(f"\n  Zeitraum: {df.index[0]} - {df.index[-1]}")
    print(f"  Candles:  {len(df)}")
    print()

    # Tabelle formatieren
    print("  " + "-" * 66)
    print(f"  {'Timestamp':<22} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12}")
    print("  " + "-" * 66)

    for idx, row in df.tail(10).iterrows():
        ts_str = str(idx)[:19]
        print(
            f"  {ts_str:<22} "
            f"{row['open']:>12,.2f} "
            f"{row['high']:>12,.2f} "
            f"{row['low']:>12,.2f} "
            f"{row['close']:>12,.2f}"
        )

    print("  " + "-" * 66)
    print()


def print_balance(balance) -> None:
    """Druckt Balance-Informationen."""
    print_header("Account Balance")

    assets = balance.non_zero_assets()
    if not assets:
        print("\n  Keine Assets mit Guthaben > 0 gefunden.")
        print("  (Möglicherweise fehlen API-Credentials oder Account ist leer)")
        print()
        return

    print()
    print(f"  {'Asset':<10} {'Free':>15} {'Used':>15} {'Total':>15}")
    print("  " + "-" * 58)

    for asset in sorted(assets):
        info = balance.get_asset(asset)
        print(
            f"  {asset:<10} {info['free']:>15,.8f} {info['used']:>15,.8f} {info['total']:>15,.8f}"
        )

    print("  " + "-" * 58)
    print()


def print_orders(orders, symbol: Optional[str]) -> None:
    """Druckt offene Orders."""
    title = f"Open Orders: {symbol}" if symbol else "Open Orders: alle"
    print_header(title)

    if not orders:
        print("\n  Keine offenen Orders.\n")
        return

    print(f"\n  Anzahl: {len(orders)}")
    print()

    for i, order in enumerate(orders[:10], 1):
        print(f"  [{i}] {order.get('symbol', 'N/A')} - {order.get('side', 'N/A')}")
        print(f"      Amount: {order.get('amount', 'N/A')}")
        print(f"      Price:  {order.get('price', 'N/A')}")
        print(f"      Status: {order.get('status', 'N/A')}")
        print()

    if len(orders) > 10:
        print(f"  ... und {len(orders) - 10} weitere Orders\n")


def print_markets(markets, limit: int) -> None:
    """Druckt verfügbare Märkte."""
    print_header("Verfügbare Märkte")

    if not markets:
        print("\n  Keine Märkte gefunden.\n")
        return

    # Nach Symbol sortieren
    markets = sorted(markets, key=lambda m: m.get("symbol", ""))

    print(f"\n  Gesamt: {len(markets)} Märkte")
    print(f"  (Zeige erste {min(limit, len(markets))})")
    print()

    print(f"  {'Symbol':<15} {'Base':<8} {'Quote':<8} {'Active':>8}")
    print("  " + "-" * 44)

    for market in markets[:limit]:
        symbol = market.get("symbol", "N/A")
        base = market.get("base", "N/A")
        quote = market.get("quote", "N/A")
        active = "Yes" if market.get("active", False) else "No"

        print(f"  {symbol:<15} {base:<8} {quote:<8} {active:>8}")

    print("  " + "-" * 44)
    print()


def print_status(client, cfg) -> None:
    """Druckt Exchange-Status und Konfiguration."""
    print_header("Exchange Status")

    print(f"\n  Exchange:      {client.get_name()}")
    print(f"  Sandbox:       {cfg.get('exchange.sandbox', 'N/A')}")
    print(f"  Rate-Limit:    {cfg.get('exchange.enable_rate_limit', 'N/A')}")

    has_key = bool(cfg.get("exchange.credentials.api_key"))
    print(f"  API-Key:       {'Konfiguriert' if has_key else 'Nicht konfiguriert'}")

    # Timeframes
    timeframes = client.get_available_timeframes()
    if timeframes:
        print(f"  Timeframes:    {', '.join(timeframes[:10])}...")

    print()
    print("  [Read-Only Mode - Keine Trades möglich]")
    print()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    # Config laden
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"\nFEHLER: Config nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as e:
        print(f"\nFEHLER beim Laden der Config: {e}")
        return 1

    # Exchange-Client erstellen
    try:
        client = build_exchange_client_from_config(cfg)
        if args.verbose:
            print(f"\nExchange-Client erstellt: {client}")
    except Exception as e:
        print(f"\nFEHLER beim Erstellen des Exchange-Clients: {e}")
        return 1

    # Modus ausführen
    try:
        if args.mode == "ticker":
            ticker = client.fetch_ticker(args.symbol)
            print_ticker(ticker, args.symbol)

        elif args.mode == "ohlcv":
            df = client.fetch_ohlcv(
                args.symbol,
                timeframe=args.timeframe,
                limit=args.limit,
            )
            print_ohlcv(df, args.symbol, args.timeframe)

        elif args.mode == "balance":
            balance = client.fetch_balance()
            print_balance(balance)

        elif args.mode == "orders":
            orders = client.fetch_open_orders(symbol=args.symbol if args.symbol else None)
            print_orders(orders, args.symbol)

        elif args.mode == "markets":
            markets = client.fetch_markets()
            print_markets(markets, args.limit)

        elif args.mode == "status":
            print_status(client, cfg)

    except Exception as e:
        print(f"\nFEHLER beim Abrufen der Daten: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
