#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/live_operator_status.py
"""
Peak_Trade: Live Operator Status CLI (Phase 72)
================================================

Read-Only Status-CLI für Operatoren zur Anzeige des kompletten
Live-/Gating-/Risk-Status.

WICHTIG: Phase 72 - Read-Only
    - Keine Config-Änderungen
    - Keine State-Änderungen
    - Keine echten Orders
    - Nur Status-Anzeige

Usage:
    python scripts/live_operator_status.py
    python scripts/live_operator_status.py --config config/config.toml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
    get_environment_from_config,
)
from src.core.peak_config import PeakConfig, load_config, load_config_default
from src.live.risk_limits import LiveRiskLimits
from src.live.safety import SafetyGuard, is_live_execution_allowed


def generate_live_status_report(
    env_config: EnvironmentConfig,
    safety_guard: SafetyGuard,
    live_risk_limits: LiveRiskLimits | None = None,
) -> str:
    """
    Generiert einen Status-Report als String.

    Args:
        env_config: EnvironmentConfig-Instanz
        safety_guard: SafetyGuard-Instanz
        live_risk_limits: Optional LiveRiskLimits-Instanz

    Returns:
        Formatierter Status-Report als String
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("Peak_Trade - Live Operator Status (Phase 71/72)")
    lines.append("=" * 70)
    lines.append("Phase 71/72 – Live-Execution Design (Dry-Run only, keine echten Orders möglich)")
    lines.append("")

    # Block 1: Environment & Gating
    lines.append("─" * 70)
    lines.append("Environment & Gating Status")
    lines.append("─" * 70)
    lines.append(f"Mode:                    {env_config.environment.value}")
    lines.append(f"Effective Mode:          {safety_guard.get_effective_mode()}")
    lines.append("")
    lines.append("Gating Status:")
    lines.append(f"  enable_live_trading:    {env_config.enable_live_trading}")
    lines.append(f"  live_mode_armed:        {env_config.live_mode_armed} (Gate 2 - Phase 71)")
    lines.append(
        f"  live_dry_run_mode:      {env_config.live_dry_run_mode} (Phase 71: Technisches Gate)"
    )
    lines.append(f"  require_confirm_token:  {env_config.require_confirm_token}")
    if env_config.confirm_token:
        # Token-Präsenz anzeigen, aber nicht den Wert loggen (Security)
        token_valid = env_config.confirm_token == LIVE_CONFIRM_TOKEN
        lines.append(
            f"  confirm_token:          {'SET (valid)' if token_valid else 'SET (invalid)'}"
        )
    else:
        lines.append(f"  confirm_token:          NOT SET")
    lines.append("")

    # Block 2: Live-Execution-Status
    lines.append("─" * 70)
    lines.append("Live-Execution Status (is_live_execution_allowed)")
    lines.append("─" * 70)
    allowed, reason = is_live_execution_allowed(env_config)
    lines.append(f"Allowed:                 {allowed}")
    lines.append(f"Reason:                  {reason}")
    lines.append("")
    if not allowed:
        lines.append("Blocking Gates:")
        if env_config.environment != TradingEnvironment.LIVE:
            lines.append(
                f"  ✗ Environment ist nicht LIVE (aktuell: {env_config.environment.value})"
            )
        if env_config.environment == TradingEnvironment.LIVE:
            if not env_config.enable_live_trading:
                lines.append("  ✗ Gate 1: enable_live_trading = False")
            if not env_config.live_mode_armed:
                lines.append("  ✗ Gate 2: live_mode_armed = False (Phase 71)")
            if env_config.live_dry_run_mode:
                lines.append("  ✗ Technisches Gate: live_dry_run_mode = True (Phase 71)")
            if env_config.require_confirm_token:
                if env_config.confirm_token != LIVE_CONFIRM_TOKEN:
                    lines.append("  ✗ Confirm-Token ungültig oder fehlt")
    else:
        lines.append("  ⚠️  WARNUNG: Alle Kriterien theoretisch erfüllt!")
        lines.append("     (Phase 71/72: live_dry_run_mode blockiert trotzdem echte Orders)")
    lines.append("")

    # Block 3: Risk-Limits (Live)
    lines.append("─" * 70)
    lines.append("Live Risk-Limits")
    lines.append("─" * 70)
    if live_risk_limits:
        cfg = live_risk_limits.config
        lines.append(f"Risk-Limits Enabled:     {cfg.enabled}")
        lines.append(f"Base Currency:           {cfg.base_currency}")
        lines.append("")
        lines.append("Live-Specific Limits (Phase 71: Design):")
        if cfg.max_live_notional_per_order is not None:
            lines.append(
                f"  max_live_notional_per_order: {cfg.max_live_notional_per_order:.2f} {cfg.base_currency}"
            )
        else:
            lines.append(f"  max_live_notional_per_order: NOT SET")
        if cfg.max_live_notional_total is not None:
            lines.append(
                f"  max_live_notional_total:     {cfg.max_live_notional_total:.2f} {cfg.base_currency}"
            )
        else:
            lines.append(f"  max_live_notional_total:     NOT SET")
        if cfg.live_trade_min_size is not None:
            lines.append(f"  live_trade_min_size:         {cfg.live_trade_min_size:.2f}")
        else:
            lines.append(f"  live_trade_min_size:         NOT SET")
        lines.append("")
        # Qualitative Bewertung (nur Info, keine Entscheidung)
        if cfg.max_live_notional_per_order is None or cfg.max_live_notional_total is None:
            lines.append("⚠️  Hinweis: Einige Live-Limits sind nicht gesetzt.")
            lines.append("   Für Produktivbetrieb sollten alle Limits konfiguriert sein.")
        else:
            lines.append("✓  Live-Limits konfiguriert (Design-Status: Phase 71)")
    else:
        lines.append("LiveRiskLimits:          NOT LOADED")
        lines.append("(Konfiguration möglicherweise nicht vorhanden oder fehlerhaft)")
    lines.append("")

    # Block 4: Hinweise / Empfehlungen
    lines.append("─" * 70)
    lines.append("Hinweise & Empfehlungen")
    lines.append("─" * 70)
    lines.append("Phase 71/72 Status:")
    lines.append("  • Live-Execution-Path existiert als Design/Dry-Run")
    lines.append("  • Keine echten Orders werden gesendet (live_dry_run_mode=True)")
    lines.append("  • System ist ein reines Research-/Testnet-System (v1.0)")
    lines.append("")
    if env_config.environment == TradingEnvironment.LIVE:
        lines.append("Live-Modus aktiv (Design):")
        lines.append("  • Alle Operationen laufen im Dry-Run-Modus")
        lines.append("  • Logs sind mit [LIVE-DRY-RUN] gekennzeichnet")
        lines.append("  • Echte Live-Orders erfordern spätere Phase (z.B. Phase 73+)")
    elif env_config.environment == TradingEnvironment.TESTNET:
        lines.append("Testnet-Modus aktiv:")
        lines.append("  • Testnet-Orders laufen im Dry-Run-Modus (Phase 71)")
    else:
        lines.append("Paper-Modus aktiv:")
        lines.append("  • Kein Live-Kontext - Live-Status irrelevant")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="live_operator_status",
        description="Peak_Trade Live Operator Status CLI (Phase 72 - Read-Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Status mit Default-Config
  python scripts/live_operator_status.py

  # Status mit expliziter Config
  python scripts/live_operator_status.py --config config/config.toml

WICHTIG: Phase 72 - Read-Only
  • Keine Config-Änderungen
  • Keine State-Änderungen
  • Keine echten Orders
  • Nur Status-Anzeige
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Pfad zur config.toml (Default: config/config.toml oder PEAK_TRADE_CONFIG_PATH)",
    )

    return parser


def main() -> int:
    """Hauptfunktion."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Config laden
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"ERROR: Config-Datei nicht gefunden: {config_path}", file=sys.stderr)
                return 1
            cfg = load_config(str(config_path))
        else:
            cfg = load_config_default()

        # Environment & SafetyGuard erstellen
        env_config = get_environment_from_config(cfg)
        safety_guard = SafetyGuard(env_config=env_config)

        # LiveRiskLimits laden (optional - kann fehlen)
        live_risk_limits = None
        try:
            live_risk_limits = LiveRiskLimits.from_config(cfg)
        except Exception as e:
            # Nicht kritisch - nur Status-Anzeige
            print(f"WARNING: LiveRiskLimits konnten nicht geladen werden: {e}", file=sys.stderr)

        # Status-Report generieren und ausgeben
        report = generate_live_status_report(env_config, safety_guard, live_risk_limits)
        print(report)

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

