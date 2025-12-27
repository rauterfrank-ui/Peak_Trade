# src/experiments/live_session_registry.py
"""
Peak_Trade: Live Session Registry (Phase 81)
=============================================

JSON-basiertes Registry-System für Live-/Paper-/Shadow-/Testnet-Sessions,
analog zum bestehenden Experiment-System.

Dieses Modul erfasst jeden Session-Run (Shadow, Testnet, Paper, Live)
und speichert Config, Metriken und Metadaten in einem einheitlichen JSON-Format.

Features:
- LiveSessionRecord: Datenstruktur für Session-Runs (analog zu SweepResultRow)
- register_live_session_run(): Helper zum Registrieren einer Session
- list_session_records(): Query-Funktion zum Auflisten von Sessions
- get_session_summary(): Aggregierte Summary über Sessions
- Markdown/HTML Report Renderer
- Safety-Design: Registry-Fehler brechen Sessions nicht

Speicherort: reports/experiments/live_sessions/*.json (ein File pro Session)

Run-Types:
- live_session_shadow: Shadow-Mode (Simulation ohne API-Calls)
- live_session_testnet: Testnet-Mode (Testnet mit validate_only)
- live_session_paper: Paper-Trading-Mode
- live_session_live: Live-Trading-Mode (nicht empfohlen für Phase 81)

Usage:
    >>> from src.experiments.live_session_registry import (
    ...     LiveSessionRecord,
    ...     register_live_session_run,
    ...     list_session_records,
    ...     render_session_markdown,
    ... )
    >>>
    >>> # Session-Record erstellen und registrieren
    >>> record = LiveSessionRecord(
    ...     session_id="session_20251208_001",
    ...     run_type="live_session_shadow",
    ...     mode="shadow",
    ...     env_name="kraken_futures_testnet",
    ...     symbol="BTC/USDT",
    ...     status="completed",
    ...     started_at=datetime.utcnow(),
    ...     config={"strategy_name": "ma_crossover"},
    ...     metrics={"realized_pnl": 150.0, "max_drawdown": 0.05},
    ... )
    >>> path = register_live_session_run(record)
    >>> print(f"Session saved: {path}")

See also:
    - src/execution/live_session.py (LiveSessionRunner, LiveSessionConfig)
    - src/experiments/base.py (SweepResultRow, ExperimentResult pattern)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, List, Optional, Sequence
import json
from collections import Counter
import textwrap
import html


# =============================================================================
# Constants
# =============================================================================

DEFAULT_LIVE_SESSION_DIR = Path("reports/experiments/live_sessions")

# Run-Type Konstanten
RUN_TYPE_LIVE_SESSION = "live_session"
RUN_TYPE_LIVE_SESSION_SHADOW = "live_session_shadow"
RUN_TYPE_LIVE_SESSION_TESTNET = "live_session_testnet"
RUN_TYPE_LIVE_SESSION_PAPER = "live_session_paper"
RUN_TYPE_LIVE_SESSION_LIVE = "live_session_live"

# Status-Konstanten
STATUS_STARTED = "started"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_ABORTED = "aborted"


# =============================================================================
# LiveSessionRecord Dataclass
# =============================================================================


@dataclass
class LiveSessionRecord:
    """
    Repräsentiert einen registrierten Live-Session-Run.

    Analog zu SweepResultRow, aber spezialisiert für Live-/Paper-/Shadow-/Testnet-Sessions.

    Attributes:
        session_id: Interne ID für die Session (z.B. "session_20251208_001")
        run_id: Optional: Experiment/Run-ID, falls im Experiment-Kontext
        run_type: z.B. "live_session_shadow", "live_session_testnet"
        mode: Generischer Mode ("shadow", "testnet", "live", "paper")
        env_name: Environment-Name (z.B. "kraken_futures_testnet")
        symbol: Trading-Symbol (z.B. "BTC/USDT")
        status: "started" | "completed" | "failed" | "aborted"
        started_at: Session-Startzeit
        finished_at: Session-Endzeit (kann bei harten Abbrüchen None sein)
        config: Session-/Strategie-Konfiguration
        metrics: Ergebnisgrößen (realized_pnl, max_drawdown, num_orders, etc.)
        cli_args: Vollständiger CLI-Call als Liste (z.B. sys.argv)
        error: Fehlermeldung/Kurzbeschreibung bei failed/aborted
        created_at: Zeitstempel der Record-Erstellung
        strategy_tier: Strategy-Tier (core, aux, legacy, r_and_d, unclassified)

    Example:
        >>> record = LiveSessionRecord(
        ...     session_id="session_20251208_001",
        ...     run_type="live_session_shadow",
        ...     mode="shadow",
        ...     env_name="kraken_futures_testnet",
        ...     symbol="BTC/USDT",
        ...     status="completed",
        ...     started_at=datetime.utcnow(),
        ...     config={"strategy_name": "ma_crossover", "timeframe": "1m"},
        ...     metrics={"realized_pnl": 150.0, "max_drawdown": 0.05},
        ...     strategy_tier="core",
        ... )
    """

    session_id: str
    run_id: Optional[str]
    run_type: str  # z.B. "live_session_shadow", "live_session_testnet"
    mode: str  # z.B. "shadow", "testnet", "live", "paper"
    env_name: str
    symbol: str

    status: str  # "started", "completed", "failed", "aborted"

    started_at: datetime
    finished_at: Optional[datetime] = None

    config: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, float] = field(default_factory=dict)
    cli_args: List[str] = field(default_factory=list)
    error: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    strategy_tier: Optional[str] = None  # core, aux, legacy, r_and_d, unclassified

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert den Record in ein JSON-serialisierbares Dict."""
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "run_type": self.run_type,
            "mode": self.mode,
            "env_name": self.env_name,
            "symbol": self.symbol,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "config": dict(self.config),
            "metrics": dict(self.metrics),
            "cli_args": list(self.cli_args),
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "strategy_tier": self.strategy_tier,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LiveSessionRecord":
        """Erzeugt einen LiveSessionRecord aus einem JSON-Dict."""

        def parse_dt(value: Optional[str]) -> Optional[datetime]:
            if value is None:
                return None
            return datetime.fromisoformat(value)

        return cls(
            session_id=data["session_id"],
            run_id=data.get("run_id"),
            run_type=data["run_type"],
            mode=data.get("mode", ""),
            env_name=data.get("env_name", ""),
            symbol=data.get("symbol", ""),
            status=data.get("status", ""),
            started_at=parse_dt(data["started_at"]),
            finished_at=parse_dt(data.get("finished_at")),
            config=data.get("config", {}) or {},
            metrics=data.get("metrics", {}) or {},
            cli_args=data.get("cli_args", []) or [],
            error=data.get("error"),
            created_at=parse_dt(data.get("created_at")) or datetime.utcnow(),
            strategy_tier=data.get("strategy_tier"),
        )


# =============================================================================
# Helper für Dateinamen & Verzeichnis
# =============================================================================


def _ensure_dir(base_dir: Path) -> None:
    """Stellt sicher, dass das Verzeichnis existiert."""
    base_dir.mkdir(parents=True, exist_ok=True)


def _build_session_filename(record: LiveSessionRecord) -> str:
    """Erzeugt einen stabilen Dateinamen für eine Session-JSON-Datei."""
    ts = record.started_at.strftime("%Y%m%dT%H%M%S")
    safe_session_id = record.session_id.replace("/", "_").replace(":", "_").replace(" ", "_")
    safe_run_type = record.run_type.replace("/", "_").replace(":", "_").replace(" ", "_")
    return f"{ts}_{safe_run_type}_{safe_session_id}.json"


# =============================================================================
# register_live_session_run()
# =============================================================================


def register_live_session_run(
    record: LiveSessionRecord,
    base_dir: Path | str | None = None,
) -> Path:
    """
    Persistiert eine Live-Session als JSON-File.

    Speicherort:
      reports/experiments/live_sessions/<timestamp>_<run_type>_<session_id>.json

    Args:
        record: Der zu speichernde LiveSessionRecord
        base_dir: Optionales Basis-Verzeichnis (default: DEFAULT_LIVE_SESSION_DIR)

    Returns:
        Path zur gespeicherten JSON-Datei

    Raises:
        OSError: Bei IO-Fehlern

    Note:
        Diese Funktion darf Exceptions werfen (z.B. IO-Fehler).
        Die Aufrufstelle in run_execution_session.py muss dafür sorgen,
        dass solche Fehler die Session NICHT abbrechen (separater try/except).

    Example:
        >>> record = LiveSessionRecord(
        ...     session_id="session_001",
        ...     run_type="live_session_shadow",
        ...     mode="shadow",
        ...     env_name="kraken_testnet",
        ...     symbol="BTC/USDT",
        ...     status="completed",
        ...     started_at=datetime.utcnow(),
        ... )
        >>> path = register_live_session_run(record)
        >>> print(f"Saved to: {path}")
    """
    base = Path(base_dir) if base_dir is not None else DEFAULT_LIVE_SESSION_DIR
    _ensure_dir(base)

    filename = _build_session_filename(record)
    path = base / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

    return path


# =============================================================================
# Query-Funktion: list_session_records()
# =============================================================================


def list_session_records(
    base_dir: Path | str | None = None,
    run_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[LiveSessionRecord]:
    """
    Lädt LiveSessionRecord-JSONs aus reports/experiments/live_sessions.

    Args:
        base_dir: Optionales Basis-Verzeichnis
        run_type: Filter nach run_type (z.B. "live_session_shadow")
        status: Filter nach status (z.B. "completed")
        limit: Maximale Anzahl zurückgegebener Records (neueste zuerst)

    Returns:
        Liste von LiveSessionRecord (neueste zuerst)

    Note:
        Beschädigte JSON-Dateien werden still übersprungen.

    Example:
        >>> records = list_session_records(run_type="live_session_shadow", limit=10)
        >>> for r in records:
        ...     print(f"{r.session_id}: {r.status}")
    """
    base = Path(base_dir) if base_dir is not None else DEFAULT_LIVE_SESSION_DIR
    if not base.exists():
        return []

    records: List[LiveSessionRecord] = []

    # Dateinamen sind mit Timestamp-Präfix, daher sortiert = chronologische Reihenfolge
    for path in sorted(base.glob("*.json"), reverse=True):
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            rec = LiveSessionRecord.from_dict(raw)
        except Exception:
            # Beschädigte Datei, falsches Format etc. -> überspringen
            continue

        if run_type is not None and rec.run_type != run_type:
            continue
        if status is not None and rec.status != status:
            continue

        records.append(rec)
        if limit is not None and len(records) >= limit:
            break

    return records


# =============================================================================
# Query-Funktion: get_session_summary()
# =============================================================================


def get_session_summary(
    base_dir: Path | str | None = None,
    run_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Liefert eine einfache Aggregations-Summary über alle passenden Sessions.

    Args:
        base_dir: Optionales Basis-Verzeichnis
        run_type: Optional: Filter nach run_type

    Returns:
        Dict mit:
        - num_sessions: Anzahl Sessions
        - by_status: Dict mit Status-Verteilung
        - by_tier: Dict mit Tier-Verteilung (core, aux, legacy, r_and_d, etc.)
        - total_realized_pnl: Summe realized_pnl
        - avg_max_drawdown: Durchschnittlicher max_drawdown
        - first_started_at / last_started_at: ISO-Strings
        - r_and_d_summary: Summary für R&D-Sessions (nur wenn vorhanden)

    Example:
        >>> summary = get_session_summary(run_type="live_session_shadow")
        >>> print(f"Total: {summary['num_sessions']}, PnL: {summary['total_realized_pnl']}")
    """
    records = list_session_records(base_dir=base_dir, run_type=run_type)
    num_sessions = len(records)

    if not records:
        return {
            "num_sessions": 0,
            "by_status": {},
            "by_tier": {},
            "total_realized_pnl": 0.0,
            "avg_max_drawdown": 0.0,
        }

    status_counter = Counter(r.status for r in records)
    tier_counter = Counter(r.strategy_tier or "unclassified" for r in records)

    total_realized_pnl = sum(float(r.metrics.get("realized_pnl", 0.0)) for r in records)
    dd_values = [
        float(r.metrics.get("max_drawdown", 0.0)) for r in records if "max_drawdown" in r.metrics
    ]
    avg_max_drawdown = sum(dd_values) / len(dd_values) if dd_values else 0.0

    result: Dict[str, Any] = {
        "num_sessions": num_sessions,
        "by_status": dict(status_counter),
        "by_tier": dict(tier_counter),
        "total_realized_pnl": total_realized_pnl,
        "avg_max_drawdown": avg_max_drawdown,
        "first_started_at": min(r.started_at for r in records).isoformat(),
        "last_started_at": max(r.started_at for r in records).isoformat(),
    }

    # R&D-Summary wenn R&D-Sessions vorhanden
    r_and_d_records = [r for r in records if r.strategy_tier == "r_and_d"]
    if r_and_d_records:
        r_and_d_pnl = sum(float(r.metrics.get("realized_pnl", 0.0)) for r in r_and_d_records)
        r_and_d_strategies = list(
            set(r.config.get("strategy_name", "unknown") for r in r_and_d_records)
        )
        result["r_and_d_summary"] = {
            "num_sessions": len(r_and_d_records),
            "total_realized_pnl": r_and_d_pnl,
            "strategies": r_and_d_strategies,
            "notice": "R&D-Strategien: Nur für Research/Backtests, nicht live-freigegeben",
        }

    return result


# =============================================================================
# Session-Reports: Markdown
# =============================================================================


def render_session_markdown(record: LiveSessionRecord) -> str:
    """Gibt einen Markdown-Report für eine einzelne Session zurück."""
    import json as _json

    # Tier-Label Mapping
    tier_labels = {
        "core": "Core",
        "aux": "Auxiliary",
        "legacy": "Legacy",
        "r_and_d": "R&D / Research",
        "unclassified": "Unclassified",
    }

    header = f"# Live-Session {record.session_id}\n\n"

    # Tier-Info wenn vorhanden
    tier_line = ""
    if record.strategy_tier:
        tier_label = tier_labels.get(record.strategy_tier, record.strategy_tier)
        tier_line = f"**Strategy Tier:** `{tier_label}`  \n"
        # R&D-Warnung
        if record.strategy_tier == "r_and_d":
            tier_line += "⚠️ *R&D-Strategie: Nur für Research/Backtests, nicht für Live-Trading freigegeben*  \n"

    meta = (
        textwrap.dedent(
            f"""
        **Run-Type:** `{record.run_type}`
        **Mode:** `{record.mode}`
        **Status:** `{record.status}`
        **Symbol:** `{record.symbol}`
        **Environment:** `{record.env_name}`
        **Started:** `{record.started_at.isoformat() if record.started_at else "-"}`
        **Finished:** `{record.finished_at.isoformat() if record.finished_at else "-"}`
        """
        ).strip()
        + "\n"
        + tier_line
        + "\n"
    )

    error_block = ""
    if record.error:
        error_block = f"**Error:** `{record.error}`\n\n"

    config_block = (
        "## Config\n\n```json\n"
        + _json.dumps(record.config, indent=2, ensure_ascii=False)
        + "\n```\n\n"
    )

    metrics_block = (
        "## Metrics\n\n```json\n"
        + _json.dumps(record.metrics, indent=2, ensure_ascii=False)
        + "\n```\n\n"
    )

    cli_block = ""
    if record.cli_args:
        cmd = " ".join(record.cli_args)
        cli_block = f"## CLI-Aufruf\n\n```bash\n{cmd}\n```\n\n"

    return header + meta + error_block + config_block + metrics_block + cli_block


def render_sessions_markdown(records: Sequence[LiveSessionRecord]) -> str:
    """Gibt einen Markdown-Report für mehrere Sessions zurück."""
    if not records:
        return "# Live-Sessions\n\nKeine Sessions gefunden.\n"

    parts: List[str] = ["# Live-Sessions\n"]
    for rec in records:
        parts.append(render_session_markdown(rec))
        parts.append("\n---\n")

    return "\n".join(parts)


# =============================================================================
# Session-Reports: HTML
# =============================================================================


def render_session_html(record: LiveSessionRecord) -> str:
    """Gibt einen einfachen HTML-Report für eine einzelne Session zurück."""
    import json as _json

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    config_json = esc(_json.dumps(record.config, indent=2, ensure_ascii=False))
    metrics_json = esc(_json.dumps(record.metrics, indent=2, ensure_ascii=False))
    cli_cmd = " ".join(record.cli_args)

    error_html = ""
    if record.error:
        error_html = f"<p><strong>Error:</strong> {esc(record.error)}</p>"

    cli_html = ""
    if record.cli_args:
        cli_html = f"<h2>CLI-Aufruf</h2><pre>{esc(cli_cmd)}</pre>"

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Live-Session {esc(record.session_id)}</title>
  </head>
  <body>
    <h1>Live-Session {esc(record.session_id)}</h1>
    <ul>
      <li><strong>Run-Type:</strong> {esc(record.run_type)}</li>
      <li><strong>Mode:</strong> {esc(record.mode)}</li>
      <li><strong>Status:</strong> {esc(record.status)}</li>
      <li><strong>Symbol:</strong> {esc(record.symbol)}</li>
      <li><strong>Environment:</strong> {esc(record.env_name)}</li>
      <li><strong>Started:</strong> {esc(record.started_at.isoformat() if record.started_at else "-")}</li>
      <li><strong>Finished:</strong> {esc(record.finished_at.isoformat() if record.finished_at else "-")}</li>
    </ul>
    {error_html}
    <h2>Config</h2>
    <pre>{config_json}</pre>
    <h2>Metrics</h2>
    <pre>{metrics_json}</pre>
    {cli_html}
  </body>
</html>
"""


def render_sessions_html(records: Sequence[LiveSessionRecord]) -> str:
    """Gibt einen einfachen HTML-Report für mehrere Sessions zurück."""
    if not records:
        return """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Live-Sessions</title>
  </head>
  <body>
    <h1>Live-Sessions</h1>
    <p>Keine Sessions gefunden.</p>
  </body>
</html>
"""

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    rows: List[str] = []
    for rec in records:
        rows.append(
            f"""<tr>
      <td>{esc(rec.session_id)}</td>
      <td>{esc(rec.run_type)}</td>
      <td>{esc(rec.mode)}</td>
      <td>{esc(rec.status)}</td>
      <td>{esc(rec.symbol)}</td>
      <td>{esc(rec.started_at.isoformat() if rec.started_at else "-")}</td>
    </tr>"""
        )

    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Live-Sessions</title>
    <style>
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background-color: #4CAF50; color: white; }}
      tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
  </head>
  <body>
    <h1>Live-Sessions ({len(records)} Sessions)</h1>
    <table>
      <tr>
        <th>Session-ID</th>
        <th>Run-Type</th>
        <th>Mode</th>
        <th>Status</th>
        <th>Symbol</th>
        <th>Started</th>
      </tr>
      {"".join(rows)}
    </table>
  </body>
</html>
"""


# =============================================================================
# Legacy Compatibility: generate_session_run_id, load_session_record
# =============================================================================


def generate_session_run_id(
    mode: str = "shadow",
    prefix: str = "session",
) -> str:
    """
    Generiert eine eindeutige Session-ID.

    Args:
        mode: Session-Mode (shadow, testnet, paper, live)
        prefix: Prefix für die ID

    Returns:
        Eindeutige Session-ID (z.B. "session_20251208_143022_shadow")

    Example:
        >>> session_id = generate_session_run_id("shadow")
        >>> print(session_id)
        session_20251208_143022_shadow
    """
    import uuid

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{mode}_{short_uuid}"


def load_session_record(filepath: Path | str) -> LiveSessionRecord:
    """
    Lädt einen einzelnen LiveSessionRecord aus einer JSON-Datei.

    Args:
        filepath: Pfad zur JSON-Datei

    Returns:
        LiveSessionRecord

    Raises:
        FileNotFoundError: Wenn Datei nicht existiert
        json.JSONDecodeError: Bei ungültigem JSON
    """
    filepath = Path(filepath)

    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return LiveSessionRecord.from_dict(data)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Constants
    "DEFAULT_LIVE_SESSION_DIR",
    "RUN_TYPE_LIVE_SESSION",
    "RUN_TYPE_LIVE_SESSION_SHADOW",
    "RUN_TYPE_LIVE_SESSION_TESTNET",
    "RUN_TYPE_LIVE_SESSION_PAPER",
    "RUN_TYPE_LIVE_SESSION_LIVE",
    "STATUS_STARTED",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_ABORTED",
    # Record class
    "LiveSessionRecord",
    # Functions
    "register_live_session_run",
    "list_session_records",
    "get_session_summary",
    "load_session_record",
    "generate_session_run_id",
    # Report Renderers
    "render_session_markdown",
    "render_sessions_markdown",
    "render_session_html",
    "render_sessions_html",
]
