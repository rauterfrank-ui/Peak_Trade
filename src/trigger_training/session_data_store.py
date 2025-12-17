"""
Peak_Trade: Trigger Training Session Data Store
================================================

Speichert und lädt vollständige Session-Rohdaten für Trigger-Training-Drills.

Im Gegensatz zu session_store.py (speichert nur aggregierte Events),
speichert dieser Store die kompletten Rohdaten einer Offline-Session:
  - Prices (OHLCV-Daten)
  - Signals (Strategy-Outputs)
  - Actions (User-Reaktionen)
  - Trades (ausgeführte Trades mit PnL)

Storage-Format:
    Ein Verzeichnis pro Session mit separaten Parquet-Files:
    live_runs/sessions/<session_id>/
        - prices.parquet
        - signals.parquet
        - actions.parquet
        - trades.parquet
        - meta.json (Session-Metadaten)

Verwendung:
    # Speichern nach Offline-Session
    save_session_data(
        session_id="DRILL_2025_01_15",
        prices_df=prices,
        signals_df=signals,
        actions_df=actions,
        trades_df=trades,
        start_ts=start,
        end_ts=end,
        symbol="BTCEUR",
        timeframe="1m",
    )

    # Laden für Trigger-Training-Drill
    data = load_session_data("DRILL_2025_01_15")
    trades_df = data["trades"]
    signals_df = data["signals"]
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class SessionMetadata:
    """Metadaten für eine gespeicherte Session."""
    session_id: str
    symbol: str
    timeframe: str
    start_ts: str  # ISO-Format
    end_ts: str    # ISO-Format
    environment: str = "offline_paper_trade"
    strategy: str | None = None
    n_signals: int = 0
    n_trades: int = 0
    total_pnl: float = 0.0
    extra: dict | None = None


DEFAULT_SESSIONS_BASE_DIR = Path("live_runs/sessions")


def _get_session_dir(session_id: str, base_dir: Path = DEFAULT_SESSIONS_BASE_DIR) -> Path:
    """Gibt das Session-Verzeichnis zurück."""
    return base_dir / session_id


def save_session_data(
    session_id: str,
    prices_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    actions_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    *,
    symbol: str = "UNKNOWN",
    timeframe: str = "1m",
    environment: str = "offline_paper_trade",
    strategy: str | None = None,
    extra_meta: dict | None = None,
    base_dir: Path = DEFAULT_SESSIONS_BASE_DIR,
) -> Path:
    """
    Speichert vollständige Session-Rohdaten für spätere Verwendung.

    Parameters
    ----------
    session_id:
        Eindeutige Session-ID (z.B. "DRILL_2025_01_15_MORNING")
    prices_df:
        Preis-Zeitreihe mit Spalten: timestamp, close, (optional: open, high, low, volume, symbol)
    signals_df:
        Signale mit Spalten: signal_id, timestamp, symbol, signal_state, recommended_action
    actions_df:
        User-Actions mit Spalten: signal_id, timestamp, user_action, note
    trades_df:
        Trades mit Spalten: timestamp, price, qty, pnl, fees
    start_ts:
        Start-Zeitpunkt der Session
    end_ts:
        End-Zeitpunkt der Session
    symbol:
        Trading-Symbol (z.B. "BTCEUR")
    timeframe:
        Zeitrahmen (z.B. "1m", "5m")
    environment:
        Environment-Label (z.B. "offline_paper_trade")
    strategy:
        Optional: Strategy-Name
    extra_meta:
        Optional: Zusätzliche Metadaten
    base_dir:
        Basis-Verzeichnis für Sessions

    Returns
    -------
    Path
        Pfad zum Session-Verzeichnis

    Example
    -------
    >>> save_session_data(
    ...     session_id="DRILL_TEST_001",
    ...     prices_df=prices,
    ...     signals_df=signals,
    ...     actions_df=actions,
    ...     trades_df=trades,
    ...     start_ts=pd.Timestamp("2025-01-01"),
    ...     end_ts=pd.Timestamp("2025-01-01 01:00:00"),
    ...     symbol="BTCEUR",
    ... )
    """
    session_dir = _get_session_dir(session_id, base_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    # DataFrames als Parquet speichern (effizient & typsicher)
    prices_df.to_parquet(session_dir / "prices.parquet", index=False)
    signals_df.to_parquet(session_dir / "signals.parquet", index=False)
    actions_df.to_parquet(session_dir / "actions.parquet", index=False)
    trades_df.to_parquet(session_dir / "trades.parquet", index=False)

    # Metadaten berechnen und speichern
    meta = SessionMetadata(
        session_id=session_id,
        symbol=symbol,
        timeframe=timeframe,
        start_ts=start_ts.isoformat(),
        end_ts=end_ts.isoformat(),
        environment=environment,
        strategy=strategy,
        n_signals=len(signals_df),
        n_trades=len(trades_df),
        total_pnl=float(trades_df["pnl"].sum()) if len(trades_df) > 0 else 0.0,
        extra=extra_meta,
    )

    with (session_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta.__dict__, f, indent=2, ensure_ascii=False)

    return session_dir


def load_session_data(
    session_id: str,
    base_dir: Path = DEFAULT_SESSIONS_BASE_DIR,
) -> dict[str, pd.DataFrame | SessionMetadata]:
    """
    Lädt vollständige Session-Rohdaten aus dem Store.

    Parameters
    ----------
    session_id:
        Session-ID zum Laden
    base_dir:
        Basis-Verzeichnis für Sessions

    Returns
    -------
    Dict[str, pd.DataFrame | SessionMetadata]
        Dictionary mit Schlüsseln:
          - "prices": Preis-DataFrame
          - "signals": Signals-DataFrame
          - "actions": Actions-DataFrame
          - "trades": Trades-DataFrame
          - "meta": SessionMetadata-Objekt

    Raises
    ------
    FileNotFoundError:
        Wenn Session-ID nicht gefunden wurde

    Example
    -------
    >>> data = load_session_data("DRILL_TEST_001")
    >>> trades_df = data["trades"]
    >>> meta = data["meta"]
    >>> print(f"Session: {meta.session_id}, PnL: {meta.total_pnl}")
    """
    session_dir = _get_session_dir(session_id, base_dir)

    if not session_dir.exists():
        raise FileNotFoundError(
            f"Session '{session_id}' nicht gefunden in {base_dir}. "
            f"Verfügbare Sessions: {list_session_ids(base_dir)}"
        )

    # DataFrames laden
    prices_df = pd.read_parquet(session_dir / "prices.parquet")
    signals_df = pd.read_parquet(session_dir / "signals.parquet")
    actions_df = pd.read_parquet(session_dir / "actions.parquet")
    trades_df = pd.read_parquet(session_dir / "trades.parquet")

    # Metadaten laden
    with (session_dir / "meta.json").open("r", encoding="utf-8") as f:
        meta_dict = json.load(f)

    meta = SessionMetadata(**meta_dict)

    return {
        "prices": prices_df,
        "signals": signals_df,
        "actions": actions_df,
        "trades": trades_df,
        "meta": meta,
    }


def list_session_ids(base_dir: Path = DEFAULT_SESSIONS_BASE_DIR) -> list[str]:
    """
    Listet alle verfügbaren Session-IDs auf.

    Parameters
    ----------
    base_dir:
        Basis-Verzeichnis für Sessions

    Returns
    -------
    list[str]
        Liste von Session-IDs (alphabetisch sortiert)

    Example
    -------
    >>> sessions = list_session_ids()
    >>> print(f"Verfügbare Sessions: {sessions}")
    """
    if not base_dir.exists():
        return []

    return sorted([d.name for d in base_dir.iterdir() if d.is_dir()])


def session_exists(session_id: str, base_dir: Path = DEFAULT_SESSIONS_BASE_DIR) -> bool:
    """
    Prüft, ob eine Session existiert.

    Parameters
    ----------
    session_id:
        Session-ID zum Prüfen
    base_dir:
        Basis-Verzeichnis für Sessions

    Returns
    -------
    bool
        True wenn Session existiert, sonst False
    """
    session_dir = _get_session_dir(session_id, base_dir)
    return session_dir.exists() and (session_dir / "meta.json").exists()
