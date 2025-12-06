# src/live/workflows.py
"""
Peak_Trade: Zentrale Workflow-Helpers für Live-/Paper-Trading
=============================================================

Stellt konsistente Helper-Funktionen bereit für:
- Risk-Check-Durchführung mit einheitlichem Output
- Registry-Logging
- CLI-Argument-Handling

Diese Funktionen werden von allen Live-/Paper-Scripts verwendet.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from src.core.peak_config import PeakConfig
from src.core.experiments import log_live_risk_check, RUN_TYPE_LIVE_RISK_CHECK
from src.live.orders import LiveOrderRequest
from src.live.risk_limits import LiveRiskLimits, LiveRiskCheckResult
from src.notifications.base import Alert, Notifier, AlertLevel


class LiveRiskViolationError(Exception):
    """Exception bei erzwungenem Risk-Check-Fehler (--enforce-live-risk)."""

    def __init__(self, reasons: List[str], metrics: Dict[str, Any]) -> None:
        self.reasons = reasons
        self.metrics = metrics
        msg = f"Live-Risk-Limits verletzt: {', '.join(reasons)}"
        super().__init__(msg)


@dataclass
class RiskCheckContext:
    """
    Kontext für einen Risk-Check-Durchlauf.

    Attributes:
        config: PeakConfig-Objekt
        starting_cash: Startkapital (für max_daily_loss_pct)
        enforce: Wenn True, Exit bei Verletzung
        skip: Wenn True, Risk-Check komplett überspringen
        tag: Optionaler Tag für Registry-Logging
        config_path: Pfad zur Config (für Registry-Logging)
        log_to_registry: Ob in die Registry geloggt werden soll
        runner_name: Name des aufrufenden Scripts
        notifier: Optionaler Notifier für Alert-Versand
    """

    config: PeakConfig
    starting_cash: Optional[float] = None
    enforce: bool = False
    skip: bool = False
    tag: Optional[str] = None
    config_path: Optional[str] = None
    log_to_registry: bool = True
    runner_name: str = "live_workflow"
    notifier: Optional[Notifier] = None


def validate_risk_flags(enforce: bool, skip: bool) -> None:
    """
    Validiert, dass --enforce-live-risk und --skip-live-risk
    nicht gleichzeitig gesetzt sind.

    Args:
        enforce: Wert von --enforce-live-risk
        skip: Wert von --skip-live-risk

    Raises:
        ValueError: Wenn beide Flags gesetzt sind
    """
    if enforce and skip:
        raise ValueError(
            "Konflikt: --enforce-live-risk und --skip-live-risk können nicht "
            "gleichzeitig verwendet werden. Bitte nur eines der Flags setzen."
        )


def run_live_risk_check(
    orders: Sequence[LiveOrderRequest],
    ctx: RiskCheckContext,
    *,
    orders_csv: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[LiveRiskCheckResult]:
    """
    Führt einen Live-Risk-Check für Orders durch.

    Verhalten:
    - Wenn ctx.skip=True: Check wird übersprungen, gibt None zurück
    - Wenn ctx.skip=False: Check wird durchgeführt, Ergebnis wird geloggt
    - Wenn ctx.enforce=True und allowed=False: LiveRiskViolationError wird geworfen

    Args:
        orders: Liste von LiveOrderRequest
        ctx: RiskCheckContext mit Config, Flags, etc.
        orders_csv: Pfad zur Orders-CSV (für Registry-Logging)
        extra_metadata: Zusätzliche Metadaten für Registry

    Returns:
        LiveRiskCheckResult oder None wenn skip=True

    Raises:
        LiveRiskViolationError: Wenn enforce=True und allowed=False
    """
    # Flags validieren
    validate_risk_flags(ctx.enforce, ctx.skip)

    # Skip-Modus
    if ctx.skip:
        print("\n⚠️  Live-Risk-Check übersprungen (--skip-live-risk)")
        return None

    # LiveRiskLimits instanziieren
    live_limits = LiveRiskLimits.from_config(ctx.config, starting_cash=ctx.starting_cash)

    # Check durchführen
    result = live_limits.check_orders(orders)

    # Konsolen-Output
    _print_risk_check_summary(result)

    # Registry-Logging
    if ctx.log_to_registry:
        meta = {
            "runner": ctx.runner_name,
            "starting_cash": ctx.starting_cash,
        }
        if extra_metadata:
            meta.update(extra_metadata)

        log_live_risk_check(
            metrics=result.metrics,
            allowed=result.allowed,
            reasons=result.reasons,
            orders_csv=orders_csv,
            tag=ctx.tag,
            config_path=ctx.config_path,
            extra_metadata=meta,
        )

    # Alert senden (wenn Notifier konfiguriert)
    if ctx.notifier is not None:
        _send_risk_alert(result, ctx.notifier, ctx.tag)

    # Enforcement
    if ctx.enforce and not result.allowed:
        print("\n❌ ABBRUCH: Live-Risk-Limits verletzt und --enforce-live-risk gesetzt.")
        raise LiveRiskViolationError(
            reasons=result.reasons,
            metrics=result.metrics,
        )

    return result


def _print_risk_check_summary(result: LiveRiskCheckResult) -> None:
    """Gibt eine kompakte Zusammenfassung des Risk-Checks aus."""
    base_ccy = result.metrics.get("base_currency", "EUR")
    enabled = result.metrics.get("live_risk_enabled", True)

    print("\n=== Live-Risk-Limits Check ===")

    if not enabled:
        print("   (Live-Risk-Limits sind in Config deaktiviert)")

    print(f"   Anzahl Orders:        {result.metrics.get('n_orders', 0)}")
    print(f"   Anzahl Symbole:       {result.metrics.get('n_symbols', 0)}")
    print(
        f"   Total Notional:       {result.metrics.get('total_notional', 0.0):.2f} {base_ccy}"
    )
    print(
        f"   Max Order Notional:   {result.metrics.get('max_order_notional', 0.0):.2f} {base_ccy}"
    )
    print(
        f"   Max Symbol Exposure:  {result.metrics.get('max_symbol_exposure_notional', 0.0):.2f} {base_ccy}"
    )
    print(
        f"   Daily PnL (Net):      {result.metrics.get('daily_realized_pnl_net', 0.0):.2f} {base_ccy}"
    )

    if result.reasons:
        print(f"\n❌ {len(result.reasons)} Verletzung(en):")
        for reason in result.reasons:
            print(f"   - {reason}")
    else:
        print("\n✅ Keine Live-Risk-Verletzungen festgestellt.")


def exit_on_risk_violation(result: Optional[LiveRiskCheckResult], enforce: bool) -> bool:
    """
    Prüft, ob bei einem Risk-Violation-Ergebnis abgebrochen werden soll.

    Args:
        result: LiveRiskCheckResult oder None (wenn skip=True)
        enforce: Wert von --enforce-live-risk

    Returns:
        True wenn der Workflow fortgesetzt werden darf, False wenn abgebrochen werden soll
    """
    if result is None:
        # Skip-Modus: Fortsetzen erlaubt
        return True

    if result.allowed:
        # Keine Verletzung: Fortsetzen erlaubt
        return True

    if enforce:
        # Verletzung mit Enforcement: Abbrechen
        return False

    # Verletzung ohne Enforcement: Nur Warnung, Fortsetzen erlaubt
    print("\n⚠️  Warnung: Live-Risk-Limits verletzt, aber --enforce-live-risk nicht gesetzt.")
    print("   Workflow wird trotzdem fortgesetzt.")
    return True


def _send_risk_alert(
    result: LiveRiskCheckResult,
    notifier: Notifier,
    tag: Optional[str] = None,
) -> None:
    """
    Sendet einen Alert basierend auf dem Risk-Check-Ergebnis.

    Args:
        result: Ergebnis des Risk-Checks
        notifier: Notifier für Alert-Versand
        tag: Optionaler Tag für Context
    """
    from datetime import datetime

    # Bestimme Alert-Level basierend auf Ergebnis
    if result.allowed:
        level: AlertLevel = "info"
        message = f"Live-Risk-Check bestanden: {result.metrics.get('n_orders', 0)} Orders geprüft"
    else:
        level = "critical"
        reasons_str = ", ".join(result.reasons[:3])  # Erste 3 Gründe
        if len(result.reasons) > 3:
            reasons_str += f" (+{len(result.reasons) - 3} weitere)"
        message = f"Live-Risk-Verletzung: {reasons_str}"

    alert = Alert(
        level=level,
        source="live_risk",
        message=message,
        timestamp=datetime.utcnow(),
        context={
            "allowed": result.allowed,
            "n_orders": result.metrics.get("n_orders", 0),
            "n_violations": len(result.reasons),
            "reasons": result.reasons,
            "total_notional": result.metrics.get("total_notional", 0.0),
            "tag": tag,
        },
    )
    notifier.send(alert)
