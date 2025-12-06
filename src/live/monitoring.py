# src/live/monitoring.py
"""
Peak_Trade: Live Run Monitoring (Phase 33)
==========================================

Monitoring-Modul für Shadow-/Paper-Runs.
Bietet Snapshot- und Tail-Funktionen zum Beobachten laufender oder
abgeschlossener Runs.

Features:
- LiveRunSnapshot: Zusammenfassung des aktuellen Run-Status
- LiveRunTailRow: Einzelne Event-Zeile für Tail-Ansicht
- load_run_snapshot(): Lädt Snapshot aus Run-Directory
- load_run_tail(): Lädt letzte N Events

WICHTIG: Dieses Modul ist rein lesend (read-only).
         Es trifft keine Trading-Entscheidungen.

Example:
    >>> from src.live.monitoring import load_run_snapshot, load_run_tail
    >>>
    >>> snapshot = load_run_snapshot(Path("live_runs/my_run"))
    >>> print(f"Run: {snapshot.run_id}, Steps: {snapshot.total_steps}")
    >>>
    >>> tail = load_run_tail(Path("live_runs/my_run"), n=10)
    >>> for row in tail:
    ...     print(f"{row.ts_bar}: equity={row.equity:.2f}")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from .run_logging import (
    LiveRunMetadata,
    load_run_metadata,
    load_run_events,
    list_runs,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Config Dataclass
# =============================================================================


@dataclass
class LiveMonitoringConfig:
    """
    Konfiguration für Live-Monitoring.

    Attributes:
        default_interval_seconds: Refresh-Intervall in Sekunden
        default_tail_rows: Anzahl Tail-Zeilen
        use_colors: ANSI-Farben verwenden
    """
    default_interval_seconds: float = 2.0
    default_tail_rows: int = 15
    use_colors: bool = True


def load_live_monitoring_config(cfg: Any) -> LiveMonitoringConfig:
    """
    Lädt LiveMonitoringConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        LiveMonitoringConfig mit Werten aus Config
    """
    return LiveMonitoringConfig(
        default_interval_seconds=cfg.get("live_monitoring.default_interval_seconds", 2.0),
        default_tail_rows=cfg.get("live_monitoring.default_tail_rows", 15),
        use_colors=cfg.get("live_monitoring.use_colors", True),
    )


# =============================================================================
# Snapshot Dataclass
# =============================================================================


@dataclass
class LiveRunSnapshot:
    """
    Snapshot des aktuellen Run-Status.

    Aggregiert alle relevanten Metriken aus Metadaten und Events
    in einer einfach lesbaren Struktur.

    Attributes:
        run_id: Eindeutige Run-ID
        mode: Environment-Modus (paper, shadow)
        strategy_name: Name der Strategie
        symbol: Trading-Symbol
        timeframe: Candle-Timeframe
        started_at: Startzeit des Runs
        ended_at: Endzeit (falls Run beendet)
        last_bar_time: Zeitstempel der letzten Bar
        last_price: Letzter Close-Preis
        position_size: Aktuelle Positionsgröße
        cash: Verfügbares Cash
        equity: Gesamtwert (Cash + Positionen)
        realized_pnl: Realisierter PnL
        unrealized_pnl: Unrealisierter PnL
        total_steps: Anzahl verarbeiteter Steps
        total_orders: Anzahl generierter Orders
        total_blocked_orders: Anzahl blockierter Orders (Risk)
    """
    run_id: str
    mode: str
    strategy_name: str
    symbol: str
    timeframe: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    last_bar_time: Optional[datetime]
    last_price: Optional[float]
    position_size: Optional[float]
    cash: Optional[float]
    equity: Optional[float]
    realized_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    total_steps: int
    total_orders: int
    total_blocked_orders: int


# =============================================================================
# Tail Row Dataclass
# =============================================================================


@dataclass
class LiveRunTailRow:
    """
    Einzelne Zeile für die Tail-Ansicht.

    Repräsentiert ein Event mit den wichtigsten Metriken
    für die tabellarische Anzeige.

    Attributes:
        ts_bar: Zeitstempel der Bar
        equity: Equity-Wert
        realized_pnl: Realisierter PnL
        unrealized_pnl: Unrealisierter PnL
        position_size: Positionsgröße
        orders_count: Anzahl Orders in diesem Step
        risk_allowed: Ob Risk-Check bestanden
        risk_reasons: Gründe für Risk-Block
    """
    ts_bar: Optional[datetime]
    equity: Optional[float]
    realized_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    position_size: Optional[float]
    orders_count: int
    risk_allowed: bool
    risk_reasons: str


# =============================================================================
# Load Functions
# =============================================================================


def load_run_snapshot(run_dir: Path) -> LiveRunSnapshot:
    """
    Lädt einen Snapshot aus einem Run-Verzeichnis.

    Kombiniert Metadaten und Events zu einem aggregierten Snapshot
    mit allen wichtigen Metriken.

    Args:
        run_dir: Pfad zum Run-Verzeichnis

    Returns:
        LiveRunSnapshot mit aggregierten Metriken

    Raises:
        FileNotFoundError: Wenn Run-Verzeichnis oder Dateien fehlen
    """
    run_dir = Path(run_dir)

    # 1. Metadaten laden
    meta = load_run_metadata(run_dir)

    # 2. Events laden
    try:
        events_df = load_run_events(run_dir)
    except FileNotFoundError:
        # Keine Events vorhanden - leerer Snapshot
        return LiveRunSnapshot(
            run_id=meta.run_id,
            mode=meta.mode,
            strategy_name=meta.strategy_name,
            symbol=meta.symbol,
            timeframe=meta.timeframe,
            started_at=meta.started_at,
            ended_at=meta.ended_at,
            last_bar_time=None,
            last_price=None,
            position_size=None,
            cash=None,
            equity=None,
            realized_pnl=None,
            unrealized_pnl=None,
            total_steps=0,
            total_orders=0,
            total_blocked_orders=0,
        )

    # 3. Aggregationen berechnen
    total_steps = len(events_df)

    # Orders zählen
    orders_col = _find_column(events_df, ["orders_generated", "orders_count"])
    total_orders = int(events_df[orders_col].sum()) if orders_col else 0

    # Blocked Orders zählen
    blocked_col = _find_column(events_df, ["orders_blocked"])
    if blocked_col:
        total_blocked_orders = int(events_df[blocked_col].sum())
    else:
        # Fallback: risk_allowed == False zählen
        risk_col = _find_column(events_df, ["risk_allowed"])
        if risk_col:
            total_blocked_orders = int((events_df[risk_col] == False).sum())  # noqa: E712
        else:
            total_blocked_orders = 0

    # Letzte Zeile für aktuelle Werte
    if len(events_df) > 0:
        last_row = events_df.iloc[-1]

        last_bar_time = _parse_datetime(last_row.get("ts_bar"))
        last_price = _safe_float(last_row.get("close") or last_row.get("price"))
        position_size = _safe_float(last_row.get("position_size"))
        cash = _safe_float(last_row.get("cash"))
        equity = _safe_float(last_row.get("equity"))
        realized_pnl = _safe_float(last_row.get("realized_pnl"))
        unrealized_pnl = _safe_float(last_row.get("unrealized_pnl"))
    else:
        last_bar_time = None
        last_price = None
        position_size = None
        cash = None
        equity = None
        realized_pnl = None
        unrealized_pnl = None

    return LiveRunSnapshot(
        run_id=meta.run_id,
        mode=meta.mode,
        strategy_name=meta.strategy_name,
        symbol=meta.symbol,
        timeframe=meta.timeframe,
        started_at=meta.started_at,
        ended_at=meta.ended_at,
        last_bar_time=last_bar_time,
        last_price=last_price,
        position_size=position_size,
        cash=cash,
        equity=equity,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        total_steps=total_steps,
        total_orders=total_orders,
        total_blocked_orders=total_blocked_orders,
    )


def load_run_tail(run_dir: Path, n: int = 15) -> List[LiveRunTailRow]:
    """
    Lädt die letzten N Events aus einem Run-Verzeichnis.

    Args:
        run_dir: Pfad zum Run-Verzeichnis
        n: Anzahl der Zeilen (default: 15)

    Returns:
        Liste von LiveRunTailRow (chronologisch, älteste zuerst)

    Raises:
        FileNotFoundError: Wenn Events-Datei fehlt
    """
    run_dir = Path(run_dir)

    try:
        events_df = load_run_events(run_dir)
    except FileNotFoundError:
        return []

    # Tail nehmen
    tail_df = events_df.tail(n)

    # Zu TailRows konvertieren
    rows: List[LiveRunTailRow] = []
    for _, row in tail_df.iterrows():
        # Orders zählen
        orders_col = _find_column_in_row(row, ["orders_generated", "orders_count"])
        orders_count = int(row[orders_col]) if orders_col else 0

        # Risk-Info
        risk_col = _find_column_in_row(row, ["risk_allowed"])
        risk_allowed = bool(row[risk_col]) if risk_col else True

        reasons_col = _find_column_in_row(row, ["risk_reasons"])
        risk_reasons = str(row[reasons_col]) if reasons_col else ""

        tail_row = LiveRunTailRow(
            ts_bar=_parse_datetime(row.get("ts_bar")),
            equity=_safe_float(row.get("equity")),
            realized_pnl=_safe_float(row.get("realized_pnl")),
            unrealized_pnl=_safe_float(row.get("unrealized_pnl")),
            position_size=_safe_float(row.get("position_size")),
            orders_count=orders_count,
            risk_allowed=risk_allowed,
            risk_reasons=risk_reasons if risk_reasons and risk_reasons != "nan" else "",
        )
        rows.append(tail_row)

    return rows


def get_latest_run_dir(base_dir: str | Path = "live_runs") -> Optional[Path]:
    """
    Findet das neueste Run-Verzeichnis.

    Args:
        base_dir: Basis-Verzeichnis für Runs

    Returns:
        Pfad zum neuesten Run oder None
    """
    runs = list_runs(base_dir)
    if not runs:
        return None
    # list_runs gibt bereits sortiert zurück (neueste zuerst)
    return Path(base_dir) / runs[0]


# =============================================================================
# Helper Functions
# =============================================================================


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Findet erste passende Spalte aus Kandidaten-Liste."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _find_column_in_row(row: pd.Series, candidates: List[str]) -> Optional[str]:
    """Findet erste passende Spalte in einer Row."""
    for col in candidates:
        if col in row.index:
            return col
    return None


def _safe_float(value: Any) -> Optional[float]:
    """Konvertiert Wert zu float oder None."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parst Datetime aus verschiedenen Formaten."""
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# =============================================================================
# Render Functions (für CLI)
# =============================================================================


# ANSI Color Codes
class Colors:
    """ANSI escape codes für Terminal-Farben."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def render_summary(snapshot: LiveRunSnapshot, use_colors: bool = True) -> str:
    """
    Rendert den Summary-Block als String.

    Args:
        snapshot: LiveRunSnapshot
        use_colors: ANSI-Farben verwenden

    Returns:
        Formatierter String für Terminal-Ausgabe
    """
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()

    # Header
    lines = [
        f"{c.BOLD}{'=' * 60}{c.RESET}",
        f"{c.BOLD}  RUN SUMMARY{c.RESET}",
        f"{c.BOLD}{'=' * 60}{c.RESET}",
        "",
    ]

    # Run-Infos
    lines.extend([
        f"  run_id        : {c.CYAN}{snapshot.run_id}{c.RESET}",
        f"  mode          : {snapshot.mode.upper()}",
        f"  strategy      : {snapshot.strategy_name}",
        f"  symbol        : {snapshot.symbol}",
        f"  timeframe     : {snapshot.timeframe}",
    ])

    # Zeitstempel
    started_str = snapshot.started_at.strftime("%Y-%m-%d %H:%M:%S") if snapshot.started_at else "N/A"
    lines.append(f"  started_at    : {started_str}")

    if snapshot.ended_at:
        ended_str = snapshot.ended_at.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  ended_at      : {ended_str}")

    last_bar_str = snapshot.last_bar_time.strftime("%Y-%m-%d %H:%M:%S") if snapshot.last_bar_time else "N/A"
    lines.append(f"  last_bar_time : {last_bar_str}")

    lines.append("")

    # Portfolio-Status
    price_str = f"{snapshot.last_price:,.2f}" if snapshot.last_price is not None else "N/A"
    pos_str = f"{snapshot.position_size:,.6f}" if snapshot.position_size is not None else "0.00"
    cash_str = f"{snapshot.cash:,.2f}" if snapshot.cash is not None else "N/A"
    equity_str = f"{snapshot.equity:,.2f}" if snapshot.equity is not None else "N/A"

    lines.extend([
        f"  last_price    : {price_str}",
        f"  position_size : {pos_str}",
        f"  cash          : {cash_str}",
        f"  equity        : {equity_str}",
    ])

    # PnL mit Farben
    if snapshot.realized_pnl is not None:
        pnl_color = c.GREEN if snapshot.realized_pnl >= 0 else c.RED
        lines.append(f"  realized_pnl  : {pnl_color}{snapshot.realized_pnl:+,.2f}{c.RESET}")
    else:
        lines.append("  realized_pnl  : N/A")

    if snapshot.unrealized_pnl is not None:
        upnl_color = c.GREEN if snapshot.unrealized_pnl >= 0 else c.RED
        lines.append(f"  unrealized_pnl: {upnl_color}{snapshot.unrealized_pnl:+,.2f}{c.RESET}")
    else:
        lines.append("  unrealized_pnl: N/A")

    lines.append("")

    # Statistiken
    lines.extend([
        f"  steps         : {snapshot.total_steps}",
        f"  orders        : {snapshot.total_orders}",
    ])

    # Blocked Orders mit Warnung
    if snapshot.total_blocked_orders > 0:
        lines.append(f"  blocked       : {c.YELLOW}{snapshot.total_blocked_orders} (Risk-Blocked){c.RESET}")
    else:
        lines.append(f"  blocked       : 0")

    lines.append("")

    return "\n".join(lines)


def render_tail(
    tail_rows: List[LiveRunTailRow],
    use_colors: bool = True,
) -> str:
    """
    Rendert die Tail-Tabelle als String.

    Args:
        tail_rows: Liste von LiveRunTailRow
        use_colors: ANSI-Farben verwenden

    Returns:
        Formatierter String für Terminal-Ausgabe
    """
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()

    lines = [
        f"{c.BOLD}{'=' * 100}{c.RESET}",
        f"{c.BOLD}  LAST {len(tail_rows)} EVENTS{c.RESET}",
        f"{c.BOLD}{'=' * 100}{c.RESET}",
    ]

    # Header
    header = (
        f"  {'ts_bar':<20} {'equity':>12} {'r_pnl':>10} {'u_pnl':>10} "
        f"{'pos':>10} {'ord':>4} {'risk':>6} {'reasons':<20}"
    )
    lines.append(f"{c.GRAY}{header}{c.RESET}")
    lines.append(f"  {'-' * 96}")

    # Rows
    for row in tail_rows:
        ts_str = row.ts_bar.strftime("%Y-%m-%d %H:%M:%S") if row.ts_bar else "N/A"
        equity_str = f"{row.equity:>12,.2f}" if row.equity is not None else f"{'N/A':>12}"
        rpnl_str = f"{row.realized_pnl:>10,.2f}" if row.realized_pnl is not None else f"{'N/A':>10}"
        upnl_str = f"{row.unrealized_pnl:>10,.2f}" if row.unrealized_pnl is not None else f"{'N/A':>10}"
        pos_str = f"{row.position_size:>10,.4f}" if row.position_size is not None else f"{'0':>10}"

        # Risk-Status mit Farbe
        if row.risk_allowed:
            risk_str = f"{c.GREEN}{'OK':>6}{c.RESET}"
        else:
            risk_str = f"{c.RED}{'BLOCK':>6}{c.RESET}"

        reasons_str = row.risk_reasons[:20] if row.risk_reasons else "-"

        line = (
            f"  {ts_str:<20} {equity_str} {rpnl_str} {upnl_str} "
            f"{pos_str} {row.orders_count:>4} {risk_str} {reasons_str:<20}"
        )
        lines.append(line)

    lines.append("")

    return "\n".join(lines)
