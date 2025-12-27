#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/live_ops.py
"""
Peak_Trade: Live Operations CLI (Phase 51)
==========================================

Zentrales Operator-Cockpit für Live-/Testnet-Operationen.

Subcommands:
- orders: Preview live orders and run live risk checks
- portfolio: Preview live portfolio snapshot and risk evaluation
- health: Run basic Live/Testnet health checks

Usage:
    python scripts/live_ops.py orders --signals reports/forward/..._signals.csv
    python scripts/live_ops.py portfolio --config config/config.toml
    python scripts/live_ops.py health --config config/config.toml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import PeakConfig, load_config
from src.live.alerts import LiveAlertsConfig, build_alert_sink_from_config
from src.live.broker_base import BaseBrokerClient, PaperBroker
from src.live.portfolio_monitor import LivePortfolioMonitor, LivePortfolioSnapshot
from src.live.risk_limits import LiveRiskLimits
from src.live.workflows import (
    run_live_risk_check,
    RiskCheckContext,
    validate_risk_flags,
    LiveRiskViolationError,
)
from src.forward.signals import load_signals_csv
from src.live.orders import (
    LiveOrderRequest,
    side_from_direction,
)

# noqa: E402 - imports after sys.path modification
import pandas as pd
import numpy as np
import uuid
from datetime import datetime


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser für Live-Ops CLI."""
    parser = argparse.ArgumentParser(
        prog="live_ops",
        description="Peak_Trade Live-/Testnet Operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/live_ops.py orders --signals reports/forward/..._signals.csv
  python scripts/live_ops.py portfolio --config config/config.toml
  python scripts/live_ops.py health --config config/config.toml --json
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Live-Ops Subcommand",
    )

    # orders
    orders_parser = subparsers.add_parser(
        "orders",
        help="Preview live orders and run live risk checks",
    )
    add_orders_subcommand_args(orders_parser)

    # portfolio
    portfolio_parser = subparsers.add_parser(
        "portfolio",
        help="Preview live portfolio snapshot and risk evaluation",
    )
    add_portfolio_subcommand_args(portfolio_parser)

    # health
    health_parser = subparsers.add_parser(
        "health",
        help="Run basic Live/Testnet health checks",
    )
    add_health_subcommand_args(health_parser)

    return parser


def add_orders_subcommand_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für 'orders' Subcommand hinzu."""
    parser.add_argument(
        "--signals",
        required=True,
        help="Pfad zur Forward-Signal-CSV (erzeugt von generate_forward_signals.py).",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/config.toml",
        help="Pfad zur TOML-Config (Default: config/config.toml).",
    )
    parser.add_argument(
        "--tag",
        help="Optionaler Tag für Registry-Logging (z.B. 'daily', 'precheck').",
    )
    parser.add_argument(
        "--notional",
        type=float,
        help="Notional pro Trade (Default: aus config).",
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
        help="Live-Risk-Limits für diesen Run komplett überspringen.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output orders and risk evaluation as JSON",
    )


def add_portfolio_subcommand_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für 'portfolio' Subcommand hinzu."""
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/config.toml",
        help="Pfad zur TOML-Config (Default: config/config.toml).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output portfolio snapshot and risk evaluation as JSON",
    )
    parser.add_argument(
        "--no-risk",
        action="store_true",
        help="Do not run live risk evaluation on the portfolio snapshot",
    )
    parser.add_argument(
        "--starting-cash",
        type=float,
        default=None,
        help="Starting Cash für prozentuale Daily-Loss-Limits (Default: aus config).",
    )


def add_health_subcommand_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für 'health' Subcommand hinzu."""
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/config.toml",
        help="Pfad zur TOML-Config (Default: config/config.toml).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output health check result as JSON",
    )


def get_current_price(symbol: str) -> float:
    """
    Holt den aktuellen/letzten Preis für ein Symbol.

    Aktuell: Dummy-Implementation mit plausiblen Preisen.
    NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Echte Daten-Adapter: live_ops.py")

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
) -> list[LiveOrderRequest]:
    """
    Wandelt Signals-DataFrame in eine Liste von LiveOrderRequest um.

    Args:
        df_signals: DataFrame mit Spalten symbol, direction, as_of, strategy_key, run_name
        default_notional: Notional-Betrag pro Order
        preview_name: Name des Preview-Runs

    Returns:
        Liste von LiveOrderRequest (nur für direction != 0)
    """
    orders: list[LiveOrderRequest] = []

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
            comment="Preview generated from signals CSV",
            extra={
                "current_price": current_price,
                "original_direction": direction,
            },
        )
        orders.append(order)

    return orders


def run_orders_command(args: argparse.Namespace) -> int:
    """
    Führt 'orders' Subcommand aus.

    Args:
        args: Parsed arguments

    Returns:
        Exit-Code (0 = Erfolg, >0 = Fehler)
    """
    try:
        json_mode = getattr(args, "json", False)

        if not json_mode:
            print("\n📋 Peak_Trade Order Preview (via live_ops)")
            print("=" * 70)

        cfg = load_config(args.config_path)

        # Signals-CSV laden
        signals_path = Path(args.signals)
        if not json_mode:
            print(f"\n📥 Lade Signals-CSV: {signals_path}")
        df_signals = load_signals_csv(signals_path)
        if not json_mode:
            print(f"   {len(df_signals)} Signale geladen")

        # Notional bestimmen
        if args.notional is not None:
            default_notional = args.notional
        else:
            default_notional = cfg.get("live.max_notional_per_order", 1000.0)

        if not json_mode:
            print(
                f"\n💰 Notional pro Order: {default_notional:.2f} {cfg.get('general.base_currency', 'EUR')}"
            )

        # Preview-Name
        preview_name = f"preview_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Signals → Orders
        orders = signals_to_orders(df_signals, default_notional, preview_name)

        if not orders:
            if json_mode:
                print(
                    json.dumps(
                        {
                            "error": "No orders generated",
                            "num_signals": len(df_signals),
                            "num_orders": 0,
                        },
                        indent=2,
                    )
                )
            else:
                print("\n⚠️  Keine Orders generiert (alle Signale haben direction=0).")
            return 0

        if not json_mode:
            print(f"\n📊 {len(orders)} Orders generiert:")

        # Live-Risk-Limits prüfen
        try:
            validate_risk_flags(args.enforce_live_risk, args.skip_live_risk)
        except ValueError as e:
            if json_mode:
                print(json.dumps({"error": str(e)}, indent=2))
            else:
                print(f"\n❌ FEHLER: {e}")
            return 1

        # Alert-Sink laden
        alert_sink = None
        if not args.skip_live_risk:
            live_alerts_raw = cfg.get("live_alerts", {})
            if isinstance(live_alerts_raw, dict):
                alerts_cfg = LiveAlertsConfig.from_dict(live_alerts_raw)
                alert_sink = build_alert_sink_from_config(alerts_cfg)

        ctx = RiskCheckContext(
            config=cfg,
            starting_cash=None,
            enforce=args.enforce_live_risk,
            skip=args.skip_live_risk,
            tag=args.tag,
            config_path=args.config_path,
            log_to_registry=True,
            runner_name="live_ops.py orders",
            notifier=alert_sink,
        )

        try:
            risk_result = run_live_risk_check(
                orders=orders,
                ctx=ctx,
                orders_csv=str(signals_path),
                extra_metadata={"preview_name": preview_name},
            )
        except LiveRiskViolationError as e:
            if json_mode:
                print(json.dumps({"error": str(e)}, indent=2))
            else:
                print(f"\n❌ ABBRUCH: {e}")
            return 1

        # JSON-Output
        if args.json:
            data = {
                "preview_name": preview_name,
                "num_signals": len(df_signals),
                "num_orders": len(orders),
                "orders": [
                    {
                        "client_order_id": o.client_order_id,
                        "symbol": o.symbol,
                        "side": o.side,
                        "quantity": o.quantity,
                        "notional": o.notional,
                    }
                    for o in orders
                ],
            }
            if risk_result:
                data["risk"] = {
                    "allowed": risk_result.allowed,
                    "reasons": risk_result.reasons,
                    "metrics": risk_result.metrics,
                }
            print(json.dumps(data, indent=2, default=str))
        else:
            # Text-Output
            print("-" * 70)
            for order in orders:
                current_price = order.extra.get("current_price", "?") if order.extra else "?"
                print(
                    f"  {order.side:4s} {order.symbol:10s} "
                    f"qty={order.quantity:.6f} @ ~{current_price} "
                    f"notional={order.notional:.2f}"
                )

            if risk_result is not None:
                print("\n📈 Risk-Check:")
                print(f"   Allowed: {risk_result.allowed}")
                if risk_result.reasons:
                    print(f"   Reasons: {risk_result.reasons}")
                else:
                    print("   Reasons: [] (alle Limits OK)")

        return 0

    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def create_exchange_client(cfg: PeakConfig) -> BaseBrokerClient:
    """
    Erstellt einen Exchange-Client basierend auf Config.

    Args:
        cfg: PeakConfig

    Returns:
        BaseBrokerClient
    """
    starting_cash = cfg.get("general.starting_capital", 10000.0)
    base_currency = cfg.get("general.base_currency", "EUR")

    return PaperBroker(
        starting_cash=float(starting_cash),
        base_currency=str(base_currency),
        log_to_console=False,
    )


def format_portfolio_snapshot(snapshot: LivePortfolioSnapshot) -> str:
    """Formatiert Portfolio-Snapshot als Text-Tabelle."""
    lines = []
    lines.append("=" * 70)
    lines.append(
        f"=== Live Portfolio Snapshot ({snapshot.as_of.strftime('%Y-%m-%d %H:%M:%S')} UTC) ==="
    )
    lines.append("=" * 70)
    lines.append("")

    if snapshot.positions:
        lines.append("Positions:")
        lines.append("-" * 70)
        lines.append(
            f"{'symbol':<12} {'side':<6} {'size':>10} {'entry':>12} {'mark':>12} {'notional':>12} {'unreal_pnl':>12}"
        )
        lines.append("-" * 70)

        for pos in snapshot.positions:
            if pos.side != "flat":
                entry_str = f"{pos.entry_price:.2f}" if pos.entry_price else "N/A"
                mark_str = f"{pos.mark_price:.2f}" if pos.mark_price else "N/A"
                pnl_str = f"{pos.unrealized_pnl:.2f}" if pos.unrealized_pnl is not None else "N/A"
                lines.append(
                    f"{pos.symbol:<12} {pos.side:<6} {pos.size:>10.4f} "
                    f"{entry_str:>12} {mark_str:>12} {pos.notional:>12.2f} {pnl_str:>12}"
                )
        lines.append("")
    else:
        lines.append("Positions: (keine offenen Positionen)")
        lines.append("")

    lines.append("Totals:")
    lines.append("-" * 70)
    lines.append(f"  - num_open_positions   : {snapshot.num_open_positions}")
    lines.append(f"  - total_notional       : {snapshot.total_notional:.2f}")
    lines.append(f"  - total_unrealized_pnl : {snapshot.total_unrealized_pnl:.2f}")
    lines.append(f"  - total_realized_pnl   : {snapshot.total_realized_pnl:.2f}")
    lines.append("")

    if snapshot.symbol_notional:
        lines.append("Symbol exposure:")
        lines.append("-" * 70)
        for symbol, notional in sorted(snapshot.symbol_notional.items()):
            lines.append(f"  - {symbol:<12} : {notional:>12.2f}")
        lines.append("")

    return "\n".join(lines)


def format_risk_result(result: Any, snapshot: LivePortfolioSnapshot) -> str:
    """Formatiert Risk-Check-Result als Text."""
    lines = []
    lines.append("Risk status:")
    lines.append("-" * 70)
    lines.append(f"  - allowed : {result.allowed}")

    if result.reasons:
        lines.append(f"  - reasons : {result.reasons}")
    else:
        lines.append("  - reasons : [] (alle Limits OK)")

    lines.append("  - metrics :")
    for key, value in result.metrics.items():
        if isinstance(value, dict):
            lines.append(f"    {key} = {value}")
        elif isinstance(value, (int, float)):
            lines.append(f"    {key} = {value:.2f}")
        else:
            lines.append(f"    {key} = {value}")

    return "\n".join(lines)


def format_json_output(snapshot: LivePortfolioSnapshot, risk_result: Any | None = None) -> str:
    """Formatiert Portfolio-Snapshot + Risk-Result als JSON."""
    data: dict[str, Any] = {
        "as_of": snapshot.as_of.isoformat(),
        "positions": [
            {
                "symbol": pos.symbol,
                "side": pos.side,
                "size": pos.size,
                "entry_price": pos.entry_price,
                "mark_price": pos.mark_price,
                "notional": pos.notional,
                "unrealized_pnl": pos.unrealized_pnl,
                "realized_pnl": pos.realized_pnl,
            }
            for pos in snapshot.positions
        ],
        "totals": {
            "num_open_positions": snapshot.num_open_positions,
            "total_notional": snapshot.total_notional,
            "total_unrealized_pnl": snapshot.total_unrealized_pnl,
            "total_realized_pnl": snapshot.total_realized_pnl,
        },
        "symbol_notional": snapshot.symbol_notional,
    }

    if risk_result:
        data["risk"] = {
            "allowed": risk_result.allowed,
            "reasons": risk_result.reasons,
            "metrics": risk_result.metrics,
        }

    return json.dumps(data, indent=2, default=str)


def run_portfolio_command(args: argparse.Namespace) -> int:
    """
    Führt 'portfolio' Subcommand aus.

    Args:
        args: Parsed arguments

    Returns:
        Exit-Code (0 = Erfolg, >0 = Fehler)
    """
    try:
        config_path = Path(args.config_path)
        if not config_path.exists():
            print(f"❌ Config-Datei nicht gefunden: {config_path}", file=sys.stderr)
            return 1

        cfg = load_config(config_path)

        # Exchange-Client erstellen
        exchange_client = create_exchange_client(cfg)

        # Alert-Sink laden (falls nicht --no-risk)
        alert_sink = None
        if not args.no_risk:
            live_alerts_raw = cfg.get("live_alerts", {})
            if isinstance(live_alerts_raw, dict):
                alerts_cfg = LiveAlertsConfig.from_dict(live_alerts_raw)
                alert_sink = build_alert_sink_from_config(alerts_cfg)

        # Risk-Limits laden (falls nicht --no-risk)
        risk_limits = None
        if not args.no_risk:
            starting_cash = args.starting_cash
            if starting_cash is None:
                starting_cash = cfg.get("general.starting_capital", None)
                if starting_cash is not None:
                    starting_cash = float(starting_cash)

            risk_limits = LiveRiskLimits.from_config(
                cfg,
                starting_cash=starting_cash,
                alert_sink=alert_sink,
            )

        # Portfolio-Monitor erstellen
        monitor = LivePortfolioMonitor(exchange_client, risk_limits=risk_limits)

        # Snapshot erstellen
        snapshot = monitor.snapshot()

        # Risk-Check (falls nicht --no-risk)
        risk_result = None
        if risk_limits is not None:
            risk_result = risk_limits.evaluate_portfolio(snapshot)

        # Ausgabe
        if args.json:
            output = format_json_output(snapshot, risk_result)
            print(output)
        else:
            output = format_portfolio_snapshot(snapshot)
            print(output)

            if risk_result is not None:
                risk_output = format_risk_result(risk_result, snapshot)
                print(risk_output)

        return 0

    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def run_health_command(args: argparse.Namespace) -> int:
    """
    Führt 'health' Subcommand aus.

    Args:
        args: Parsed arguments

    Returns:
        Exit-Code (0 = Erfolg, >0 = Fehler)
    """
    health_result: dict[str, Any] = {
        "config_ok": False,
        "config_errors": [],
        "exchange_ok": False,
        "exchange_errors": [],
        "alerts_enabled": False,
        "alert_sinks_configured": [],
        "alert_config_warnings": [],
        "live_risk_ok": False,
        "live_risk_warnings": [],
        "overall_status": "FAIL",
    }

    try:
        # 1. Config-Ladung & Basiskonsistenz
        try:
            config_path = Path(args.config_path)
            if not config_path.exists():
                health_result["config_errors"].append(f"Config-Datei nicht gefunden: {config_path}")
            else:
                cfg = load_config(config_path)

                # Prüfe zentrale Blöcke
                required_blocks = ["environment", "live_risk", "live_alerts"]
                for block in required_blocks:
                    if not cfg.get(block):
                        health_result["config_errors"].append(f"Block '[{block}]' fehlt in Config")

                if not health_result["config_errors"]:
                    health_result["config_ok"] = True

        except Exception as e:
            health_result["config_errors"].append(f"Fehler beim Laden der Config: {e}")

        # 2. Exchange-Client/Market Access – Smoke-Test
        if health_result["config_ok"]:
            try:
                cfg = load_config(args.config_path)
                # Leichtgewichtiger Test: Client-Initialisierung (Ergebnis wird nicht benötigt)
                create_exchange_client(cfg)
                health_result["exchange_ok"] = True
            except Exception as e:
                health_result["exchange_errors"].append(
                    f"Exchange-Client-Initialisierung fehlgeschlagen: {e}"
                )

        # 3. Alert-System-Konfiguration
        if health_result["config_ok"]:
            try:
                cfg = load_config(args.config_path)
                live_alerts_raw = cfg.get("live_alerts", {})
                if isinstance(live_alerts_raw, dict):
                    alerts_cfg = LiveAlertsConfig.from_dict(live_alerts_raw)
                    health_result["alerts_enabled"] = alerts_cfg.enabled

                    if alerts_cfg.enabled:
                        alert_sink = build_alert_sink_from_config(alerts_cfg)
                        if alert_sink is not None:
                            # Sink-Typen ableiten (vereinfacht)
                            health_result["alert_sinks_configured"] = alerts_cfg.sinks

                            # Warnungen prüfen
                            if "webhook" in alerts_cfg.sinks and not alerts_cfg.webhook_urls:
                                health_result["alert_config_warnings"].append(
                                    "sinks enthält 'webhook', aber keine webhook_urls konfiguriert"
                                )
                            if (
                                "slack_webhook" in alerts_cfg.sinks
                                and not alerts_cfg.slack_webhook_urls
                            ):
                                health_result["alert_config_warnings"].append(
                                    "sinks enthält 'slack_webhook', aber keine slack_webhook_urls konfiguriert"
                                )
            except Exception as e:
                health_result["alert_config_warnings"].append(
                    f"Fehler beim Laden der Alert-Config: {e}"
                )

        # 4. Live-Risk-Limits – Konsistenzcheck
        if health_result["config_ok"]:
            try:
                cfg = load_config(args.config_path)
                # Erstelle LiveRiskLimits, um Config zu validieren
                risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=None)
                risk_cfg = risk_limits.config

                warnings = []
                if risk_cfg.max_total_exposure_notional is not None:
                    if risk_cfg.max_total_exposure_notional <= 0:
                        warnings.append("max_total_exposure_notional <= 0")
                    if risk_cfg.max_symbol_exposure_notional is not None:
                        if (
                            risk_cfg.max_symbol_exposure_notional
                            > risk_cfg.max_total_exposure_notional
                        ):
                            warnings.append(
                                "max_symbol_exposure_notional > max_total_exposure_notional"
                            )

                health_result["live_risk_warnings"] = warnings
                health_result["live_risk_ok"] = len(warnings) == 0

            except Exception as e:
                health_result["live_risk_warnings"].append(
                    f"Fehler beim Laden der Risk-Config: {e}"
                )

        # Overall-Status bestimmen
        if not health_result["config_ok"] or not health_result["exchange_ok"]:
            health_result["overall_status"] = "FAIL"
        elif health_result["live_risk_ok"] and not health_result["alert_config_warnings"]:
            health_result["overall_status"] = "OK"
        else:
            health_result["overall_status"] = "DEGRADED"

        # Ausgabe
        if args.json:
            print(json.dumps(health_result, indent=2, default=str))
        else:
            print("\n🏥 Peak_Trade Live/Testnet Health Check")
            print("=" * 70)
            print(f"\nConfig: {'✅ OK' if health_result['config_ok'] else '❌ FAIL'}")
            if health_result["config_errors"]:
                for err in health_result["config_errors"]:
                    print(f"  - {err}")

            print(f"\nExchange: {'✅ OK' if health_result['exchange_ok'] else '❌ FAIL'}")
            if health_result["exchange_errors"]:
                for err in health_result["exchange_errors"]:
                    print(f"  - {err}")

            print(f"\nAlerts: {'✅ Enabled' if health_result['alerts_enabled'] else '⚠️  Disabled'}")
            if health_result["alert_sinks_configured"]:
                print(f"  Sinks: {', '.join(health_result['alert_sinks_configured'])}")
            if health_result["alert_config_warnings"]:
                for warn in health_result["alert_config_warnings"]:
                    print(f"  ⚠️  {warn}")

            print(f"\nLive Risk: {'✅ OK' if health_result['live_risk_ok'] else '⚠️  WARNINGS'}")
            if health_result["live_risk_warnings"]:
                for warn in health_result["live_risk_warnings"]:
                    print(f"  ⚠️  {warn}")

            print(f"\n{'=' * 70}")
            status_emoji = {
                "OK": "✅",
                "DEGRADED": "⚠️",
                "FAIL": "❌",
            }
            print(
                f"Overall Status: {status_emoji.get(health_result['overall_status'], '?')} {health_result['overall_status']}"
            )
            print()

        # Exit-Code basierend auf Overall-Status
        if health_result["overall_status"] == "FAIL":
            return 1
        elif health_result["overall_status"] == "DEGRADED":
            return 0  # Degraded ist OK für Health-Check
        else:
            return 0

    except Exception as e:
        print(f"❌ Fehler beim Health-Check: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """
    Hauptfunktion für Live-Ops CLI.

    Args:
        argv: Command-Line-Argumente (None = sys.argv)

    Returns:
        Exit-Code (0 = Erfolg, >0 = Fehler)
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "orders":
        return run_orders_command(args)
    elif args.command == "portfolio":
        return run_portfolio_command(args)
    elif args.command == "health":
        return run_health_command(args)
    else:
        parser.error(f"Unknown command {args.command!r}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
