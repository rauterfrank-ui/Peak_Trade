# src/live/alerts.py
"""
Peak_Trade: Alert System (Phase 34)
===================================

Alert-Engine für Shadow-/Paper-Runs.
Überwacht LiveRunSnapshots und generiert Alerts bei Regelverletzungen.

Features:
- Konfigurierbare Alert-Regeln
- Severity-Levels: info, warning, critical
- Debouncing (Anti-Spam)
- Alert-Logging in JSONL-Format

WICHTIG: Dieses Modul ist rein passiv (read-only + logging).
         Es trifft keine Trading-Entscheidungen.

Example:
    >>> from src.live.alerts import AlertEngine, create_alert_engine_from_config
    >>>
    >>> engine = create_alert_engine_from_config(config)
    >>> alerts = engine.evaluate_snapshot(snapshot)
    >>> for alert in alerts:
    ...     print(f"[{alert.severity}] {alert.message}")
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from .monitoring import LiveRunSnapshot

logger = logging.getLogger(__name__)


# =============================================================================
# Severity Levels
# =============================================================================


class Severity:
    """Alert Severity Levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    _RANKING = {
        "info": 0,
        "warning": 1,
        "critical": 2,
    }

    @classmethod
    def rank(cls, severity: str) -> int:
        """Returns numeric rank for severity comparison."""
        return cls._RANKING.get(severity.lower(), 0)

    @classmethod
    def is_at_least(cls, severity: str, min_severity: str) -> bool:
        """Returns True if severity >= min_severity."""
        return cls.rank(severity) >= cls.rank(min_severity)


# =============================================================================
# Config Dataclass
# =============================================================================


@dataclass
class AlertsConfig:
    """
    Konfiguration für das Alert-System.

    Attributes:
        enabled: Alerts aktiviert
        min_severity: Minimale Severity für Alerts
        debounce_seconds: Sekunden zwischen gleichen Alerts
        enable_risk_blocked: Risk-Blocked-Regel aktiviert
        enable_large_loss_abs: Absolute Loss-Regel aktiviert
        large_loss_abs_threshold: Schwelle für absolute Verluste
        enable_large_loss_pct: Prozentuale Loss-Regel aktiviert
        large_loss_pct_threshold: Schwelle für prozentuale Verluste (negativ)
        enable_drawdown: Drawdown-Regel aktiviert
        drawdown_threshold: Schwelle für Drawdown
    """
    enabled: bool = True
    min_severity: str = "warning"
    debounce_seconds: int = 60
    enable_risk_blocked: bool = True
    enable_large_loss_abs: bool = True
    large_loss_abs_threshold: float = -500.0
    enable_large_loss_pct: bool = True
    large_loss_pct_threshold: float = -10.0
    enable_drawdown: bool = False
    drawdown_threshold: float = -15.0


def load_alerts_config(cfg: Any) -> AlertsConfig:
    """
    Lädt AlertsConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        AlertsConfig mit Werten aus Config
    """
    return AlertsConfig(
        enabled=cfg.get("alerts.enabled", True),
        min_severity=cfg.get("alerts.min_severity", "warning"),
        debounce_seconds=cfg.get("alerts.debounce_seconds", 60),
        enable_risk_blocked=cfg.get("alerts.rules.enable_risk_blocked", True),
        enable_large_loss_abs=cfg.get("alerts.rules.enable_large_loss_abs", True),
        large_loss_abs_threshold=cfg.get("alerts.rules.large_loss_abs_threshold", -500.0),
        enable_large_loss_pct=cfg.get("alerts.rules.enable_large_loss_pct", True),
        large_loss_pct_threshold=cfg.get("alerts.rules.large_loss_pct_threshold", -10.0),
        enable_drawdown=cfg.get("alerts.rules.enable_drawdown", False),
        drawdown_threshold=cfg.get("alerts.rules.drawdown_threshold", -15.0),
    )


# =============================================================================
# Alert Rule & Event Dataclasses
# =============================================================================


@dataclass
class AlertRule:
    """
    Definition einer Alert-Regel.

    Attributes:
        id: Eindeutige Regel-ID
        description: Beschreibung der Regel
        severity: Severity-Level
        enabled: Regel aktiviert
        check_fn: Funktion die Snapshot prüft und Optional[str] Message zurückgibt
    """
    id: str
    description: str
    severity: str
    enabled: bool = True
    check_fn: Optional[Callable[[LiveRunSnapshot], Optional[str]]] = None

    def check(self, snapshot: LiveRunSnapshot) -> Optional[str]:
        """
        Prüft die Regel gegen einen Snapshot.

        Returns:
            Alert-Message oder None wenn Regel nicht triggert
        """
        if not self.enabled or self.check_fn is None:
            return None
        return self.check_fn(snapshot)


@dataclass
class AlertEvent:
    """
    Ein ausgelöstes Alert-Event.

    Attributes:
        rule_id: ID der auslösenden Regel
        severity: Severity-Level
        message: Alert-Nachricht
        run_id: Run-ID
        timestamp: Zeitpunkt des Alerts
    """
    rule_id: str
    severity: str
    message: str
    run_id: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu JSON-serialisierbarem Dict."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertEvent":
        """Erstellt AlertEvent aus Dict."""
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            rule_id=data["rule_id"],
            severity=data["severity"],
            message=data["message"],
            run_id=data["run_id"],
            timestamp=timestamp,
        )


# =============================================================================
# Built-in Rule Factories
# =============================================================================


def create_risk_blocked_rule(enabled: bool = True) -> AlertRule:
    """
    Erstellt eine Regel für Risk-Blocked-Events.

    Args:
        enabled: Regel aktiviert

    Returns:
        AlertRule für risk_blocked
    """
    def check(snapshot: LiveRunSnapshot) -> Optional[str]:
        if snapshot.total_blocked_orders > 0:
            return (
                f"Run {snapshot.run_id} has {snapshot.total_blocked_orders} "
                f"risk-blocked orders"
            )
        return None

    return AlertRule(
        id="risk_blocked",
        description="Triggered when orders are blocked by risk limits",
        severity=Severity.CRITICAL,
        enabled=enabled,
        check_fn=check,
    )


def create_large_loss_abs_rule(
    threshold: float = -500.0,
    enabled: bool = True,
) -> AlertRule:
    """
    Erstellt eine Regel für absolute Verluste.

    Args:
        threshold: Verlust-Schwelle (negativ, z.B. -500)
        enabled: Regel aktiviert

    Returns:
        AlertRule für large_loss_abs
    """
    def check(snapshot: LiveRunSnapshot) -> Optional[str]:
        if snapshot.realized_pnl is not None and snapshot.realized_pnl < threshold:
            return (
                f"Run {snapshot.run_id}: Large absolute loss detected. "
                f"Realized PnL: {snapshot.realized_pnl:,.2f} (threshold: {threshold:,.2f})"
            )
        return None

    return AlertRule(
        id="large_loss_abs",
        description=f"Triggered when realized PnL < {threshold}",
        severity=Severity.WARNING,
        enabled=enabled,
        check_fn=check,
    )


def create_large_loss_pct_rule(
    threshold: float = -10.0,
    enabled: bool = True,
) -> AlertRule:
    """
    Erstellt eine Regel für prozentuale Verluste.

    Args:
        threshold: Verlust-Schwelle in Prozent (negativ, z.B. -10.0)
        enabled: Regel aktiviert

    Returns:
        AlertRule für large_loss_pct
    """
    def check(snapshot: LiveRunSnapshot) -> Optional[str]:
        # Berechne PnL-Prozentsatz basierend auf Cash + Position
        if snapshot.equity is None or snapshot.cash is None:
            return None
        if snapshot.realized_pnl is None:
            return None

        # Initiales Kapital schätzen (Equity - Realized PnL)
        initial_equity = snapshot.equity - snapshot.realized_pnl
        if initial_equity <= 0:
            return None

        pnl_pct = (snapshot.realized_pnl / initial_equity) * 100

        if pnl_pct < threshold:
            return (
                f"Run {snapshot.run_id}: Large percentage loss detected. "
                f"PnL: {pnl_pct:.2f}% (threshold: {threshold:.2f}%)"
            )
        return None

    return AlertRule(
        id="large_loss_pct",
        description=f"Triggered when PnL percentage < {threshold}%",
        severity=Severity.WARNING,
        enabled=enabled,
        check_fn=check,
    )


def create_drawdown_rule(
    threshold: float = -15.0,
    enabled: bool = False,
) -> AlertRule:
    """
    Erstellt eine Regel für Drawdown.

    Args:
        threshold: Drawdown-Schwelle in Prozent (negativ)
        enabled: Regel aktiviert

    Returns:
        AlertRule für drawdown
    """
    # Hinweis: Da LiveRunSnapshot aktuell keinen direkten Drawdown enthält,
    # ist diese Regel standardmäßig deaktiviert
    def check(snapshot: LiveRunSnapshot) -> Optional[str]:
        # TODO: Implementiere wenn Drawdown in Snapshot verfügbar
        return None

    return AlertRule(
        id="drawdown",
        description=f"Triggered when drawdown exceeds {threshold}%",
        severity=Severity.CRITICAL,
        enabled=enabled,
        check_fn=check,
    )


def create_no_events_rule(
    max_minutes: int = 10,
    enabled: bool = True,
) -> AlertRule:
    """
    Erstellt eine Regel für fehlende Events.

    Args:
        max_minutes: Maximale Minuten ohne neue Events
        enabled: Regel aktiviert

    Returns:
        AlertRule für no_events
    """
    def check(snapshot: LiveRunSnapshot) -> Optional[str]:
        if snapshot.last_bar_time is None:
            return None

        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes
        last_bar = snapshot.last_bar_time
        if last_bar.tzinfo is None:
            last_bar = last_bar.replace(tzinfo=timezone.utc)

        delta = now - last_bar
        minutes_since = delta.total_seconds() / 60

        if minutes_since > max_minutes:
            return (
                f"Run {snapshot.run_id}: No new events for {minutes_since:.1f} minutes "
                f"(threshold: {max_minutes} minutes)"
            )
        return None

    return AlertRule(
        id="no_events",
        description=f"Triggered when no events for {max_minutes} minutes",
        severity=Severity.INFO,
        enabled=enabled,
        check_fn=check,
    )


# =============================================================================
# Alert Engine
# =============================================================================


class AlertEngine:
    """
    Engine zur Auswertung von Alert-Regeln.

    Evaluiert LiveRunSnapshots gegen konfigurierte Regeln und
    generiert AlertEvents. Unterstützt Debouncing um Spam zu vermeiden.

    Example:
        >>> engine = AlertEngine(rules=[...], min_severity="warning")
        >>> alerts = engine.evaluate_snapshot(snapshot)
    """

    def __init__(
        self,
        rules: Sequence[AlertRule],
        min_severity: str = "warning",
        debounce_seconds: int = 60,
    ) -> None:
        """
        Initialisiert die AlertEngine.

        Args:
            rules: Liste von AlertRules
            min_severity: Minimale Severity für Alerts
            debounce_seconds: Sekunden zwischen gleichen Alerts
        """
        self._rules = list(rules)
        self._min_severity = min_severity
        self._debounce_seconds = debounce_seconds

        # Debounce State: (run_id, rule_id) -> last_trigger_timestamp
        self._last_triggered: Dict[tuple, datetime] = {}

        logger.info(
            f"[ALERT ENGINE] Initialized with {len(rules)} rules, "
            f"min_severity={min_severity}, debounce={debounce_seconds}s"
        )

    @property
    def rules(self) -> List[AlertRule]:
        """Liste der konfigurierten Regeln."""
        return self._rules

    def evaluate_snapshot(self, snapshot: LiveRunSnapshot) -> List[AlertEvent]:
        """
        Evaluiert alle Regeln gegen einen Snapshot.

        Args:
            snapshot: LiveRunSnapshot zu prüfen

        Returns:
            Liste von neuen AlertEvents
        """
        alerts: List[AlertEvent] = []
        now = datetime.now(timezone.utc)

        for rule in self._rules:
            if not rule.enabled:
                continue

            # Severity-Filter
            if not Severity.is_at_least(rule.severity, self._min_severity):
                continue

            # Regel prüfen
            message = rule.check(snapshot)
            if message is None:
                continue

            # Debouncing prüfen
            key = (snapshot.run_id, rule.id)
            last_trigger = self._last_triggered.get(key)

            if last_trigger is not None:
                elapsed = (now - last_trigger).total_seconds()
                if elapsed < self._debounce_seconds:
                    logger.debug(
                        f"[ALERT ENGINE] Debounced alert {rule.id} for {snapshot.run_id} "
                        f"(elapsed: {elapsed:.1f}s < {self._debounce_seconds}s)"
                    )
                    continue

            # Alert erstellen
            alert = AlertEvent(
                rule_id=rule.id,
                severity=rule.severity,
                message=message,
                run_id=snapshot.run_id,
                timestamp=now,
            )
            alerts.append(alert)

            # Debounce-State aktualisieren
            self._last_triggered[key] = now

            logger.info(
                f"[ALERT ENGINE] Alert triggered: [{rule.severity.upper()}] "
                f"{rule.id}: {message}"
            )

        return alerts

    def reset_debounce(self, run_id: Optional[str] = None) -> None:
        """
        Setzt Debounce-State zurück.

        Args:
            run_id: Nur für diesen Run zurücksetzen (None = alle)
        """
        if run_id is None:
            self._last_triggered.clear()
        else:
            keys_to_remove = [k for k in self._last_triggered if k[0] == run_id]
            for key in keys_to_remove:
                del self._last_triggered[key]


# =============================================================================
# Alert Logging
# =============================================================================


def append_alerts_to_file(
    run_dir: Path,
    alerts: Sequence[AlertEvent],
    filename: str = "alerts.jsonl",
) -> None:
    """
    Schreibt Alerts in eine JSONL-Datei im Run-Directory.

    Args:
        run_dir: Pfad zum Run-Verzeichnis
        alerts: Liste von AlertEvents
        filename: Name der Alert-Datei
    """
    if not alerts:
        return

    run_dir = Path(run_dir)
    if not run_dir.exists():
        logger.warning(f"[ALERTS] Run directory does not exist: {run_dir}")
        return

    alerts_path = run_dir / filename

    try:
        with open(alerts_path, "a", encoding="utf-8") as f:
            for alert in alerts:
                line = json.dumps(alert.to_dict(), ensure_ascii=False)
                f.write(line + "\n")

        logger.debug(f"[ALERTS] Appended {len(alerts)} alerts to {alerts_path}")

    except Exception as e:
        logger.error(f"[ALERTS] Failed to write alerts: {e}")


def load_alerts_from_file(
    run_dir: Path,
    filename: str = "alerts.jsonl",
    limit: Optional[int] = None,
) -> List[AlertEvent]:
    """
    Lädt Alerts aus einer JSONL-Datei.

    Args:
        run_dir: Pfad zum Run-Verzeichnis
        filename: Name der Alert-Datei
        limit: Maximale Anzahl (letzte N Alerts)

    Returns:
        Liste von AlertEvents
    """
    run_dir = Path(run_dir)
    alerts_path = run_dir / filename

    if not alerts_path.exists():
        return []

    alerts: List[AlertEvent] = []

    try:
        with open(alerts_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    alert = AlertEvent.from_dict(data)
                    alerts.append(alert)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"[ALERTS] Failed to parse alert line: {e}")

    except Exception as e:
        logger.error(f"[ALERTS] Failed to read alerts: {e}")
        return []

    # Limit anwenden (letzte N)
    if limit is not None and len(alerts) > limit:
        alerts = alerts[-limit:]

    return alerts


# =============================================================================
# Factory from Config
# =============================================================================


def create_alert_engine_from_config(cfg: Any) -> Optional[AlertEngine]:
    """
    Erstellt eine AlertEngine aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        AlertEngine oder None wenn Alerts deaktiviert
    """
    alerts_cfg = load_alerts_config(cfg)

    if not alerts_cfg.enabled:
        logger.info("[ALERTS] Alert engine disabled in config")
        return None

    # Regeln erstellen
    rules: List[AlertRule] = [
        create_risk_blocked_rule(enabled=alerts_cfg.enable_risk_blocked),
        create_large_loss_abs_rule(
            threshold=alerts_cfg.large_loss_abs_threshold,
            enabled=alerts_cfg.enable_large_loss_abs,
        ),
        create_large_loss_pct_rule(
            threshold=alerts_cfg.large_loss_pct_threshold,
            enabled=alerts_cfg.enable_large_loss_pct,
        ),
        create_drawdown_rule(
            threshold=alerts_cfg.drawdown_threshold,
            enabled=alerts_cfg.enable_drawdown,
        ),
        create_no_events_rule(enabled=True),
    ]

    return AlertEngine(
        rules=rules,
        min_severity=alerts_cfg.min_severity,
        debounce_seconds=alerts_cfg.debounce_seconds,
    )


# =============================================================================
# CLI Rendering
# =============================================================================


def render_alerts(
    alerts: Sequence[AlertEvent],
    use_colors: bool = True,
) -> str:
    """
    Rendert Alerts als Terminal-String.

    Args:
        alerts: Liste von AlertEvents
        use_colors: ANSI-Farben verwenden

    Returns:
        Formatierter String
    """
    from .monitoring import Colors

    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()

    if not alerts:
        return ""

    lines = [
        f"{c.BOLD}{c.YELLOW}{'=' * 60}{c.RESET}",
        f"{c.BOLD}{c.YELLOW}  ALERTS ({len(alerts)}){c.RESET}",
        f"{c.BOLD}{c.YELLOW}{'=' * 60}{c.RESET}",
    ]

    for alert in alerts:
        # Farbe je nach Severity
        if alert.severity == Severity.CRITICAL:
            sev_color = c.RED
        elif alert.severity == Severity.WARNING:
            sev_color = c.YELLOW
        else:
            sev_color = c.CYAN

        ts_str = alert.timestamp.strftime("%H:%M:%S")
        lines.append(
            f"  {c.GRAY}{ts_str}{c.RESET} "
            f"[{sev_color}{alert.severity.upper():>8}{c.RESET}] "
            f"{alert.rule_id}: {alert.message}"
        )

    lines.append("")

    return "\n".join(lines)
