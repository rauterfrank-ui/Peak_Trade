"""
Peak_Trade – Kraken Cache Loader with Data-QC (Phase 79)
=========================================================

Lokaler Loader fuer Kraken-Cache-Parquet-Dateien mit integrierter
Data-Quality-Control (QC) fuer Real-Market-Smoke-Tests.

Features:
- Konfigurierbare Pfade (Prod vs. Test)
- Data-Health-Checks (Existenz, Min-Bars, Zeitraum)
- Keine Netzwerk-Calls (Offline-only)
- Strukturierte Health-Reports

Usage:
    from src.data.kraken_cache_loader import (
        KrakenDataHealth,
        load_kraken_cache_window,
        get_real_market_smokes_config,
    )

    # Config laden
    cfg = get_real_market_smokes_config()

    # Daten mit Health-Check laden
    df, health = load_kraken_cache_window(
        base_path=Path(cfg["base_path"]),
        market="BTC/EUR",
        timeframe="1h",
        lookback_days=30,
        min_bars=500,
    )

    if health.status == "ok":
        # Daten verwenden
        ...
    else:
        print(f"Data-Problem: {health.status} - {health.notes}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

import pandas as pd

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# Type alias fuer Health-Status
HealthStatus = Literal["ok", "missing_file", "too_few_bars", "empty", "invalid_format", "other"]


@dataclass
class KrakenDataHealth:
    """
    Data-Health-Report fuer Kraken-Cache-Daten.

    Attributes:
        status: Health-Status ("ok", "missing_file", "too_few_bars", "empty", "other")
        num_bars: Anzahl geladener Bars (0 bei Fehler)
        start_ts: Start-Timestamp der Daten (None bei Fehler)
        end_ts: End-Timestamp der Daten (None bei Fehler)
        notes: Optionale Notizen / Fehlerbeschreibung
        file_path: Pfad zur Quelldatei (fuer Debugging)
        lookback_days_actual: Tatsaechlicher Zeitraum in Tagen
    """

    status: HealthStatus
    num_bars: int = 0
    start_ts: Optional[pd.Timestamp] = None
    end_ts: Optional[pd.Timestamp] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None
    lookback_days_actual: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary fuer JSON-Serialisierung."""
        return {
            "status": self.status,
            "num_bars": self.num_bars,
            "start_ts": str(self.start_ts) if self.start_ts else None,
            "end_ts": str(self.end_ts) if self.end_ts else None,
            "notes": self.notes,
            "file_path": self.file_path,
            "lookback_days_actual": self.lookback_days_actual,
        }

    @property
    def is_ok(self) -> bool:
        """Shortcut: Status ist OK."""
        return self.status == "ok"


def get_real_market_smokes_config(
    config_path: str = "config/config.toml",
) -> Dict[str, Any]:
    """
    Laedt die [real_market_smokes]-Konfiguration aus config.toml.

    Args:
        config_path: Pfad zur Config-Datei

    Returns:
        Dict mit Real-Market-Smokes-Config (defaults wenn nicht vorhanden)

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        # Return sane defaults
        return {
            "base_path": "data/cache",
            "test_base_path": "tests/data/kraken_smoke",
            "default_market": "BTC/EUR",
            "default_timeframe": "1h",
            "default_lookback_days": 30,
            "min_bars": 500,
            "markets": ["BTC/EUR"],
            "timeframes": ["1h"],
        }

    with open(cfg_path, "rb") as f:
        config = tomllib.load(f)

    # Section extrahieren mit Defaults
    rms = config.get("real_market_smokes", {})

    return {
        "base_path": rms.get("base_path", "data/cache"),
        "test_base_path": rms.get("test_base_path", "tests/data/kraken_smoke"),
        "default_market": rms.get("default_market", "BTC/EUR"),
        "default_timeframe": rms.get("default_timeframe", "1h"),
        "default_lookback_days": rms.get("default_lookback_days", 30),
        "min_bars": rms.get("min_bars", 500),
        "markets": rms.get("markets", ["BTC/EUR"]),
        "timeframes": rms.get("timeframes", ["1h"]),
    }


def _build_cache_path(base_path: Path, market: str, timeframe: str) -> Path:
    """
    Baut den Pfad zur Cache-Datei.

    Konvention: BTC/EUR -> BTC_EUR_1h.parquet

    Args:
        base_path: Basis-Verzeichnis
        market: Symbol (z.B. "BTC/EUR")
        timeframe: Zeitrahmen (z.B. "1h")

    Returns:
        Path zur Cache-Datei
    """
    safe_symbol = market.replace("/", "_")
    filename = f"{safe_symbol}_{timeframe}.parquet"
    return base_path / filename


def _timeframe_to_hours(timeframe: str) -> float:
    """Konvertiert Timeframe-String zu Stunden."""
    mapping = {
        "1m": 1 / 60,
        "5m": 5 / 60,
        "15m": 0.25,
        "30m": 0.5,
        "1h": 1.0,
        "4h": 4.0,
        "1d": 24.0,
        "1w": 168.0,
    }
    return mapping.get(timeframe, 1.0)


def load_kraken_cache_window(
    base_path: Path,
    market: str,
    timeframe: str,
    lookback_days: int = 30,
    min_bars: int = 500,
    n_bars: Optional[int] = None,
) -> Tuple[pd.DataFrame, KrakenDataHealth]:
    """
    Laedt Daten aus lokalem Kraken-Cache mit Data-QC.

    Fuehrt automatische Quality-Checks durch und gibt strukturierten
    Health-Report zurueck.

    Args:
        base_path: Basis-Pfad zum Cache-Verzeichnis
        market: Symbol (z.B. "BTC/EUR")
        timeframe: Zeitrahmen (z.B. "1h")
        lookback_days: Anzahl Tage (wird nur verwendet wenn n_bars None)
        min_bars: Minimum benoetigte Bars (Data-QC Threshold)
        n_bars: Explizite Anzahl Bars (ueberschreibt lookback_days)

    Returns:
        Tuple von (DataFrame, KrakenDataHealth)
        - DataFrame: OHLCV-Daten (leer bei Fehler)
        - KrakenDataHealth: Strukturierter Health-Report
    """
    # Pfad bauen
    cache_path = _build_cache_path(Path(base_path), market, timeframe)
    file_path_str = str(cache_path)

    # 1. Existenzcheck
    if not cache_path.exists():
        # Versuche alternative Namenskonventionen
        alt_candidates = list(
            Path(base_path).glob(f"{market.replace('/', '_')}_{timeframe}*.parquet")
        )
        if alt_candidates:
            cache_path = alt_candidates[0]
            file_path_str = str(cache_path)
        else:
            available = list(Path(base_path).glob("*.parquet")) if Path(base_path).exists() else []
            available_str = ", ".join([f.name for f in available]) if available else "keine"
            return pd.DataFrame(), KrakenDataHealth(
                status="missing_file",
                num_bars=0,
                notes=f"Cache-Datei nicht gefunden: {cache_path.name}. Verfuegbar: {available_str}",
                file_path=file_path_str,
            )

    # 2. Laden
    try:
        df = pd.read_parquet(cache_path)
    except Exception as e:
        return pd.DataFrame(), KrakenDataHealth(
            status="invalid_format",
            num_bars=0,
            notes=f"Parquet-Ladefehler: {str(e)[:100]}",
            file_path=file_path_str,
        )

    # 3. Leere Datei pruefen
    if len(df) == 0:
        return pd.DataFrame(), KrakenDataHealth(
            status="empty",
            num_bars=0,
            notes="Cache-Datei ist leer",
            file_path=file_path_str,
        )

    # 4. Index-Typ pruefen und konvertieren
    if not isinstance(df.index, pd.DatetimeIndex):
        # Versuche Konvertierung wenn Timestamp-Spalte existiert
        timestamp_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if timestamp_cols:
            try:
                df = df.set_index(timestamp_cols[0])
                df.index = pd.to_datetime(df.index)
            except Exception:
                pass

        if not isinstance(df.index, pd.DatetimeIndex):
            return pd.DataFrame(), KrakenDataHealth(
                status="invalid_format",
                num_bars=0,
                notes=f"Kein DatetimeIndex: {type(df.index).__name__}",
                file_path=file_path_str,
            )

    # 5. UTC sicherstellen
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # 6. Sortierung
    df = df.sort_index()

    # 7. Spalten pruefen
    expected_cols = ["open", "high", "low", "close", "volume"]
    missing_cols = set(expected_cols) - set(df.columns)
    if missing_cols:
        return pd.DataFrame(), KrakenDataHealth(
            status="invalid_format",
            num_bars=len(df),
            start_ts=df.index[0],
            end_ts=df.index[-1],
            notes=f"Fehlende Spalten: {missing_cols}",
            file_path=file_path_str,
        )

    # 8. Anzahl Bars berechnen
    if n_bars is not None:
        required_bars = n_bars
    else:
        hours_per_bar = _timeframe_to_hours(timeframe)
        required_bars = int(lookback_days * 24 / hours_per_bar)

    # Sicherstellen, dass mindestens warmup_bars vorhanden sind
    required_bars = max(required_bars, 200)

    # 9. Lookback-Filter (letzte N Bars)
    if len(df) > required_bars:
        df = df.tail(required_bars)

    # 10. Min-Bars Check
    actual_bars = len(df)
    start_ts = df.index[0]
    end_ts = df.index[-1]

    # Tatsaechlicher Zeitraum
    if start_ts and end_ts:
        lookback_days_actual = (end_ts - start_ts).total_seconds() / 86400
    else:
        lookback_days_actual = 0.0

    if actual_bars < min_bars:
        return df[expected_cols], KrakenDataHealth(
            status="too_few_bars",
            num_bars=actual_bars,
            start_ts=start_ts,
            end_ts=end_ts,
            notes=f"Nur {actual_bars} Bars vorhanden, min_bars={min_bars} benoetigt",
            file_path=file_path_str,
            lookback_days_actual=lookback_days_actual,
        )

    # 11. Alles OK
    return df[expected_cols], KrakenDataHealth(
        status="ok",
        num_bars=actual_bars,
        start_ts=start_ts,
        end_ts=end_ts,
        file_path=file_path_str,
        lookback_days_actual=lookback_days_actual,
    )


def check_data_health_only(
    base_path: Path,
    market: str,
    timeframe: str,
    min_bars: int = 500,
) -> KrakenDataHealth:
    """
    Fuehrt nur Data-QC durch ohne Daten zu laden.

    Leichtgewichtige Variante fuer CLI --check-data-only Modus.

    Args:
        base_path: Basis-Pfad zum Cache-Verzeichnis
        market: Symbol (z.B. "BTC/EUR")
        timeframe: Zeitrahmen (z.B. "1h")
        min_bars: Minimum benoetigte Bars

    Returns:
        KrakenDataHealth mit Status-Info
    """
    _, health = load_kraken_cache_window(
        base_path=base_path,
        market=market,
        timeframe=timeframe,
        min_bars=min_bars,
    )
    return health


def list_available_cache_files(base_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Listet alle verfuegbaren Cache-Dateien mit Basisinfos.

    Args:
        base_path: Basis-Pfad zum Cache-Verzeichnis

    Returns:
        Dict von {filename: {"size_kb": ..., "modified": ...}}
    """
    if not base_path.exists():
        return {}

    result = {}
    for f in base_path.glob("*.parquet"):
        try:
            stat = f.stat()
            result[f.name] = {
                "size_kb": stat.st_size / 1024,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        except Exception:
            result[f.name] = {"size_kb": 0, "modified": None}

    return result
