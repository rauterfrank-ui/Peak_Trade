#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/preview_live_portfolio.py
"""
Peak_Trade: Live Portfolio Monitoring & Risk Bridge (Phase 48)
===============================================================

Zeigt aktuellen Portfolio-Status und prüft gegen Live-Risk-Limits.

Usage:
    python scripts/preview_live_portfolio.py --config config/config.toml
    python scripts/preview_live_portfolio.py --config config/config.toml --no-risk
    python scripts/preview_live_portfolio.py --config config/config.toml --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parst Command-Line-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Live Portfolio Monitoring & Risk Bridge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/preview_live_portfolio.py --config config/config.toml
  python scripts/preview_live_portfolio.py --config config/config.toml --no-risk
  python scripts/preview_live_portfolio.py --config config/config.toml --json
        """,
    )

    parser.add_argument(
        "--config",
        dest="config_path",
        default="config/config.toml",
        help="Pfad zur TOML-Config (Default: config/config.toml).",
    )
    parser.add_argument(
        "--no-risk",
        action="store_true",
        help="Überspringt Risk-Bewertung (nur Portfolio-Snapshot).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe als JSON statt Text-Tabelle.",
    )
    parser.add_argument(
        "--starting-cash",
        type=float,
        default=None,
        help="Starting Cash für prozentuale Daily-Loss-Limits (Default: aus config).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output.",
    )

    if argv is None:
        return parser.parse_args()
    else:
        return parser.parse_args(argv)


def create_exchange_client(cfg: PeakConfig) -> BaseBrokerClient:
    """
    Erstellt einen Exchange-Client basierend auf Config.

    Falls kein echter Exchange-Client verfügbar ist, wird ein PaperBroker
    oder DryRunBroker zurückgegeben (für Tests/Demos).

    Args:
        cfg: PeakConfig

    Returns:
        BaseBrokerClient
    """
    # NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Echter Exchange-Client: preview_live_portfolio.py")
    # Aktuell: Fallback auf PaperBroker für Demo-Zwecke

    starting_cash = cfg.get("general.starting_capital", 10000.0)
    base_currency = cfg.get("general.base_currency", "EUR")

    # Prüfe ob PaperBroker mit existierenden Positionen verwendet werden soll
    # (z.B. aus vorherigen Paper-Trades)
    return PaperBroker(
        starting_cash=float(starting_cash),
        base_currency=str(base_currency),
        log_to_console=False,
    )


def format_portfolio_snapshot(snapshot: LivePortfolioSnapshot) -> str:
    """
    Formatiert Portfolio-Snapshot als Text-Tabelle.

    Args:
        snapshot: LivePortfolioSnapshot

    Returns:
        Formatierter String
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"=== Live Portfolio Snapshot ({snapshot.as_of.strftime('%Y-%m-%d %H:%M:%S')} UTC) ===")
    lines.append("=" * 70)
    lines.append("")

    # Positions-Tabelle
    if snapshot.positions:
        lines.append("Positions:")
        lines.append("-" * 70)
        lines.append(f"{'symbol':<12} {'side':<6} {'size':>10} {'entry':>12} {'mark':>12} {'notional':>12} {'unreal_pnl':>12}")
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

    # Totals
    lines.append("Totals:")
    lines.append("-" * 70)
    lines.append(f"  - num_open_positions   : {snapshot.num_open_positions}")
    lines.append(f"  - total_notional       : {snapshot.total_notional:.2f}")
    lines.append(f"  - total_unrealized_pnl : {snapshot.total_unrealized_pnl:.2f}")
    lines.append(f"  - total_realized_pnl   : {snapshot.total_realized_pnl:.2f}")
    lines.append("")

    # Symbol Exposure
    if snapshot.symbol_notional:
        lines.append("Symbol exposure:")
        lines.append("-" * 70)
        for symbol, notional in sorted(snapshot.symbol_notional.items()):
            lines.append(f"  - {symbol:<12} : {notional:>12.2f}")
        lines.append("")

    # Account-Daten (falls verfügbar)
    if snapshot.equity is not None or snapshot.cash is not None:
        lines.append("Account:")
        lines.append("-" * 70)
        if snapshot.equity is not None:
            lines.append(f"  - equity              : {snapshot.equity:.2f}")
        if snapshot.cash is not None:
            lines.append(f"  - cash                : {snapshot.cash:.2f}")
        if snapshot.margin_used is not None:
            lines.append(f"  - margin_used         : {snapshot.margin_used:.2f}")
        lines.append("")

    return "\n".join(lines)


def format_risk_result(result: Any, snapshot: LivePortfolioSnapshot) -> str:
    """
    Formatiert Risk-Check-Result als Text.

    Args:
        result: LiveRiskCheckResult
        snapshot: LivePortfolioSnapshot

    Returns:
        Formatierter String
    """
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
    """
    Formatiert Portfolio-Snapshot + Risk-Result als JSON.

    Args:
        snapshot: LivePortfolioSnapshot
        risk_result: Optional LiveRiskCheckResult

    Returns:
        JSON-String
    """
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
                "leverage": pos.leverage,
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

    if snapshot.equity is not None:
        data["account"] = {}
        if snapshot.equity is not None:
            data["account"]["equity"] = snapshot.equity
        if snapshot.cash is not None:
            data["account"]["cash"] = snapshot.cash
        if snapshot.margin_used is not None:
            data["account"]["margin_used"] = snapshot.margin_used

    if risk_result:
        data["risk"] = {
            "allowed": risk_result.allowed,
            "reasons": risk_result.reasons,
            "metrics": risk_result.metrics,
        }

    return json.dumps(data, indent=2, default=str)


def main(argv: list[str] | None = None) -> int:
    """Hauptfunktion."""
    args = parse_args(argv)

    try:
        # 1. Config laden
        config_path = Path(args.config_path)
        if not config_path.exists():
            print(f"❌ Config-Datei nicht gefunden: {config_path}", file=sys.stderr)
            return 1

        cfg = load_config(config_path)

        # 2. Exchange-Client erstellen
        exchange_client = create_exchange_client(cfg)

        # 3. Alert-Sink laden (falls nicht --no-risk)
        alert_sink = None
        if not args.no_risk:
            live_alerts_raw = cfg.get("live_alerts", {})
            if isinstance(live_alerts_raw, dict):
                alerts_cfg = LiveAlertsConfig.from_dict(live_alerts_raw)
                alert_sink = build_alert_sink_from_config(alerts_cfg)

        # 4. Risk-Limits laden (falls nicht --no-risk)
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

        # 5. Portfolio-Monitor erstellen
        monitor = LivePortfolioMonitor(exchange_client, risk_limits=risk_limits)

        # 6. Snapshot erstellen
        snapshot = monitor.snapshot()

        # 7. Risk-Check (falls nicht --no-risk)
        # Alerts werden automatisch via alert_sink erzeugt, wenn Violations auftreten
        risk_result = None
        if risk_limits is not None:
            risk_result = risk_limits.evaluate_portfolio(snapshot)

        # 8. Ausgabe
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
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

