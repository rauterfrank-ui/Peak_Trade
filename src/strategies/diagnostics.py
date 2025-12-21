"""
Peak_Trade – Strategy Diagnostics (Phase 76)
=============================================

Zentrale Diagnose-Funktionen fuer die Strategy-Library v1.1.
Ermoeglicht automatisierte Smoke-Tests aller offiziellen Strategien.

Features:
- Enumeration aller v1.1-offiziellen Strategien aus Config
- Mini-Backtest-Smoke-Tests fuer jede Strategie
- Strukturierte Ergebnisse mit Kennzahlen
- Fehlerbehandlung ohne Abbruch des gesamten Tests

Usage:
    from src.strategies.diagnostics import run_strategy_smoke_tests

    # Alle v1.1-Strategien testen
    results = run_strategy_smoke_tests()

    # Bestimmte Strategien testen
    results = run_strategy_smoke_tests(
        strategy_names=["ma_crossover", "rsi_reversion"],
        lookback_days=30,
    )

    # Ergebnisse auswerten
    for r in results:
        if r.status == "ok":
            print(f"[OK] {r.name}: Return={r.return_pct:.2f}%, Trades={r.num_trades}")
        else:
            print(f"[FAIL] {r.name}: {r.error}")
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

import numpy as np
import pandas as pd

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# Type alias for data source
DataSource = Literal["synthetic", "kraken_cache"]


@dataclass
class StrategySmokeResult:
    """
    Ergebnis eines Strategy-Smoke-Tests.

    Attributes:
        name: Strategie-Name (z.B. "ma_crossover")
        status: "ok" wenn Test erfolgreich, "fail" bei Fehler
        data_source: Datenquelle ("synthetic" oder "kraken_cache")
        symbol: Verwendetes Symbol (z.B. "BTC/EUR")
        timeframe: Verwendetes Timeframe (z.B. "1h")
        num_bars: Anzahl der verwendeten Bars
        start_ts: Start-Timestamp der Daten
        end_ts: End-Timestamp der Daten
        return_pct: Gesamtrendite in Prozent (None bei Fehler)
        sharpe: Sharpe Ratio (None bei Fehler oder zu wenig Daten)
        max_drawdown_pct: Maximaler Drawdown in Prozent (None bei Fehler)
        num_trades: Anzahl der ausgefuehrten Trades (None bei Fehler)
        error: Fehlermeldung (None bei Erfolg)
        duration_ms: Ausfuehrungsdauer in Millisekunden
        metadata: Zusaetzliche Infos (Kategorie, Timeframe, etc.)
        data_health: Data-QC Status ("ok", "missing_file", "too_few_bars", "empty", "other")
        data_notes: Data-QC Freitext (z.B. "only 120 bars < min_bars=500")
    """

    name: str
    status: Literal["ok", "fail"]
    data_source: str = "synthetic"
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    num_bars: Optional[int] = None
    start_ts: Optional[pd.Timestamp] = None
    end_ts: Optional[pd.Timestamp] = None
    return_pct: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    num_trades: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    # Phase 79: Data-QC Fields
    data_health: Optional[str] = None
    data_notes: Optional[str] = None


def get_v11_official_strategies(config_path: str = "config/config.toml") -> List[str]:
    """
    Ermittelt alle v1.1-offiziellen Strategien aus der Config.

    Liest [strategies.*] Bloecke und filtert auf v11_official=true.

    Args:
        config_path: Pfad zur Config-Datei

    Returns:
        Liste von Strategie-Namen die v1.1-offiziell sind

    Raises:
        FileNotFoundError: Wenn Config-Datei nicht existiert
        ValueError: Wenn Config-Format ungueltig
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {config_path}")

    with open(cfg_path, "rb") as f:
        config = tomllib.load(f)

    strategies_section = config.get("strategies", {})
    v11_strategies = []

    # Iteriere ueber alle Strategy-Bloecke
    for key, value in strategies_section.items():
        # Skip non-dict entries (wie "active", "available", "defaults", "metadata")
        if not isinstance(value, dict):
            continue

        # Pruefe auf v11_official Flag
        if value.get("v11_official", False):
            v11_strategies.append(key)

    return sorted(v11_strategies)


def get_strategy_category(
    strategy_name: str, config_path: str = "config/config.toml"
) -> Optional[str]:
    """
    Ermittelt die Kategorie einer Strategie aus der Config.

    Args:
        strategy_name: Name der Strategie
        config_path: Pfad zur Config-Datei

    Returns:
        Kategorie-String oder None
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        return None

    with open(cfg_path, "rb") as f:
        config = tomllib.load(f)

    strategies_section = config.get("strategies", {})
    strategy_cfg = strategies_section.get(strategy_name, {})

    return strategy_cfg.get("category")


def get_strategy_defaults(
    strategy_name: str, config_path: str = "config/config.toml"
) -> Dict[str, Any]:
    """
    Holt die Default-Parameter einer Strategie aus der Config.

    Args:
        strategy_name: Name der Strategie
        config_path: Pfad zur Config-Datei

    Returns:
        Dict mit Default-Parametern
    """
    cfg_path = Path(config_path)
    if not cfg_path.exists():
        return {}

    with open(cfg_path, "rb") as f:
        config = tomllib.load(f)

    strategies_section = config.get("strategies", {})
    strategy_cfg = strategies_section.get(strategy_name, {})

    return strategy_cfg.get("defaults", {})


def create_synthetic_ohlcv(
    n_bars: int = 500,
    start_price: float = 50000.0,
    volatility: float = 0.02,
    trend: float = 0.0001,
    seed: Optional[int] = 42,
) -> pd.DataFrame:
    """
    Erstellt synthetische OHLCV-Daten fuer Smoke-Tests.

    Generiert einen Random-Walk mit optionalem Trend und Volatilitaet.
    Beinhaltet realistische High/Low/Volume-Werte.

    Args:
        n_bars: Anzahl der Bars
        start_price: Startpreis
        volatility: Volatilitaet pro Bar (Standardabweichung)
        trend: Trend pro Bar (Mittelwert der Returns)
        seed: Random Seed fuer Reproduzierbarkeit

    Returns:
        DataFrame mit open, high, low, close, volume
    """
    if seed is not None:
        np.random.seed(seed)

    # Zeitindex (stuendlich, UTC)
    idx = pd.date_range(
        start=datetime.now() - timedelta(hours=n_bars),
        periods=n_bars,
        freq="1h",
        tz="UTC",
    )

    # Random Walk fuer Close
    returns = np.random.normal(trend, volatility, n_bars)

    # Etwas Trend-Variation hinzufuegen (Sin-Wave)
    trend_wave = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * volatility * 0.3
    returns = returns + trend_wave

    close_prices = start_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=idx)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(start_price)

    # High/Low mit realistischer Varianz
    high_bump = np.random.uniform(0, volatility * 0.5, n_bars)
    low_dip = np.random.uniform(0, volatility * 0.5, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    # Volume
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def load_kraken_cache_ohlcv(
    symbol: str = "BTC/EUR",
    timeframe: str = "1h",
    lookback_days: int = 30,
    n_bars: Optional[int] = None,
    config_path: str = "config/config.toml",
) -> pd.DataFrame:
    """
    Laedt OHLCV-Daten aus dem lokalen Kraken-Cache.

    Keine Netzwerk-Aufrufe - nur lokale Parquet-Dateien.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Zeitrahmen ("1h", "4h", "1d")
        lookback_days: Anzahl Tage (wird nur verwendet wenn n_bars None)
        n_bars: Explizite Anzahl Bars (ueberschreibt lookback_days)
        config_path: Pfad zur Config-Datei

    Returns:
        DataFrame mit UTC-DatetimeIndex
        Spalten: [open, high, low, close, volume]

    Raises:
        FileNotFoundError: Wenn Cache-Datei nicht existiert
        ValueError: Wenn nicht genuegend Daten vorhanden sind
    """
    # Config laden fuer data_dir
    cfg_path = Path(config_path)
    if cfg_path.exists():
        with open(cfg_path, "rb") as f:
            config = tomllib.load(f)
        data_dir = config.get("data", {}).get("data_dir", "data")
    else:
        data_dir = "data"

    cache_dir = Path(data_dir) / "cache"

    # Cache-Dateiname: BTC/EUR -> BTC_EUR
    safe_symbol = symbol.replace("/", "_")
    cache_filename = f"{safe_symbol}_{timeframe}.parquet"
    cache_path = cache_dir / cache_filename

    if not cache_path.exists():
        # Versuche alternative Naming-Konventionen
        alt_candidates = list(cache_dir.glob(f"{safe_symbol}_{timeframe}*.parquet"))
        if alt_candidates:
            cache_path = alt_candidates[0]
        else:
            available_files = list(cache_dir.glob("*.parquet"))
            available_str = (
                ", ".join([f.name for f in available_files]) if available_files else "keine"
            )
            raise FileNotFoundError(
                f"Kraken cache nicht gefunden: {cache_filename}\n"
                f"Gesuchter Pfad: {cache_path}\n"
                f"Verfuegbare Cache-Dateien: {available_str}"
            )

    # Cache laden
    df = pd.read_parquet(cache_path)

    # Sicherstellen, dass Index DatetimeIndex ist
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError(f"Cache hat keinen DatetimeIndex: {type(df.index)}")

    # UTC sicherstellen
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # Anzahl Bars berechnen
    if n_bars is not None:
        required_bars = n_bars
    else:
        # lookback_days in Bars umrechnen (je nach timeframe)
        timeframe_hours = {
            "1m": 1 / 60,
            "5m": 5 / 60,
            "15m": 0.25,
            "30m": 0.5,
            "1h": 1,
            "4h": 4,
            "1d": 24,
        }
        hours_per_bar = timeframe_hours.get(timeframe, 1)
        required_bars = int(lookback_days * 24 / hours_per_bar)

    # Mindestens 200 Bars fuer Strategien mit grossen Lookbacks
    required_bars = max(required_bars, 200)

    if len(df) < required_bars:
        raise ValueError(
            f"Nicht genuegend Daten im Cache: {len(df)} Bars vorhanden, {required_bars} benoetigt"
        )

    # Nur die letzten n_bars zurueckgeben
    df = df.tail(required_bars)

    # Spalten normalisieren
    expected_cols = ["open", "high", "low", "close", "volume"]
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Fehlende Spalten im Cache: {missing}")

    return df[expected_cols]


def _load_ohlcv_for_smoke(
    data_source: str,
    market: str,
    timeframe: str,
    lookback_days: int,
    n_bars: Optional[int],
    config_path: str,
    min_bars: int = 200,
) -> Tuple[pd.DataFrame, Optional[Any]]:
    """
    Laedt OHLCV-Daten basierend auf der Datenquelle.

    Args:
        data_source: "synthetic" oder "kraken_cache"
        market: Symbol (z.B. "BTC/EUR")
        timeframe: Zeitrahmen
        lookback_days: Anzahl Tage
        n_bars: Explizite Anzahl Bars
        config_path: Pfad zur Config
        min_bars: Minimum benoetigte Bars fuer Data-QC (Phase 79)

    Returns:
        Tuple von (DataFrame, Optional[KrakenDataHealth])
        - DataFrame: OHLCV-Daten
        - KrakenDataHealth: Health-Report (nur bei kraken_cache, sonst None)

    Raises:
        ValueError: Bei unbekannter Datenquelle oder fehlenden Daten
    """
    if data_source == "synthetic":
        # Bisheriges Verhalten: synthetische Daten
        if n_bars is None:
            n_bars = max(lookback_days * 24, 200)
        return create_synthetic_ohlcv(n_bars=n_bars), None

    elif data_source == "kraken_cache":
        # Phase 79: echte Daten aus Kraken-Cache mit Data-QC
        from src.data.kraken_cache_loader import (
            load_kraken_cache_window,
            get_real_market_smokes_config,
        )

        # Config laden fuer base_path
        rms_cfg = get_real_market_smokes_config(config_path)
        base_path = Path(rms_cfg["base_path"])

        # Falls test_base_path gesetzt und existiert, verwende diesen
        test_base_path = Path(rms_cfg.get("test_base_path", "tests/data/kraken_smoke"))
        if test_base_path.exists() and not base_path.exists():
            base_path = test_base_path

        # QC-Threshold: Parameter hat Prioritaet, dann Config
        # Verwende immer den uebergebenen min_bars Parameter
        qc_min_bars = min_bars

        df, health = load_kraken_cache_window(
            base_path=base_path,
            market=market,
            timeframe=timeframe,
            lookback_days=lookback_days,
            min_bars=qc_min_bars,
            n_bars=n_bars,
        )

        # Bei Data-QC-Fehler: Exception werfen (wird im Aufrufer gefangen)
        if not health.is_ok:
            raise ValueError(f"Data-QC fehlgeschlagen: {health.status}. {health.notes or ''}")

        return df, health

    else:
        raise ValueError(
            f"Unbekannte Datenquelle: '{data_source}'. Erlaubt: 'synthetic', 'kraken_cache'"
        )


def run_single_strategy_smoke(
    strategy_name: str,
    df: pd.DataFrame,
    config_path: str = "config/config.toml",
    data_source: str = "synthetic",
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> StrategySmokeResult:
    """
    Fuehrt einen Smoke-Test fuer eine einzelne Strategie aus.

    Args:
        strategy_name: Name der Strategie
        df: OHLCV-DataFrame fuer den Backtest
        config_path: Pfad zur Config
        data_source: Datenquelle ("synthetic" oder "kraken_cache")
        symbol: Verwendetes Symbol (fuer Metadata)
        timeframe: Verwendetes Timeframe (fuer Metadata)

    Returns:
        StrategySmokeResult mit Kennzahlen oder Fehlermeldung
    """
    import time

    start_time = time.perf_counter()

    try:
        # Imports hier, um Fehler abzufangen
        from src.strategies.registry import get_strategy_spec
        from src.backtest.engine import BacktestEngine
        from src.core.peak_config import load_config
        from src.core.position_sizing import build_position_sizer_from_config
        from src.core.risk import build_risk_manager_from_config

        # Strategie aus Registry holen
        spec = get_strategy_spec(strategy_name)

        # Strategie-Defaults aus Config laden
        defaults = get_strategy_defaults(strategy_name, config_path)
        category = get_strategy_category(strategy_name, config_path)

        # Strategie instanziieren
        # Manche Strategien brauchen spezielle Parameter
        try:
            if defaults:
                strategy = spec.cls(**defaults)
            else:
                strategy = spec.cls()
        except TypeError as e:
            # Wenn das nicht klappt, versuche ohne Parameter
            strategy = spec.cls()

        # Signal-Funktion erstellen
        def strategy_fn(data: pd.DataFrame, params: Dict) -> pd.Series:
            return strategy.generate_signals(data)

        # Config laden (fuer BacktestEngine)
        cfg = load_config()

        # Position Sizer und Risk Manager
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        # BacktestEngine erstellen
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
            use_execution_pipeline=True,
        )

        # Backtest ausfuehren
        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_fn,
            strategy_params=defaults,
            symbol="BTC/EUR",
            fee_bps=10.0,  # Realistische Fees
            slippage_bps=5.0,
        )

        # Kennzahlen extrahieren
        stats = result.stats

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Daten-Metadata extrahieren
        start_ts = df.index[0] if len(df) > 0 else None
        end_ts = df.index[-1] if len(df) > 0 else None

        return StrategySmokeResult(
            name=strategy_name,
            status="ok",
            data_source=data_source,
            symbol=symbol,
            timeframe=timeframe,
            num_bars=len(df),
            start_ts=start_ts,
            end_ts=end_ts,
            return_pct=stats.get("total_return", 0.0) * 100,
            sharpe=stats.get("sharpe"),
            max_drawdown_pct=stats.get("max_drawdown", 0.0) * 100,
            num_trades=stats.get("total_trades", 0),
            duration_ms=duration_ms,
            metadata={
                "category": category,
                "win_rate": stats.get("win_rate"),
                "profit_factor": stats.get("profit_factor"),
            },
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Kurze Fehlermeldung extrahieren
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."

        # Optional: Traceback fuer Debugging
        tb = traceback.format_exc()
        if len(tb) > 500:
            tb = tb[-500:]

        return StrategySmokeResult(
            name=strategy_name,
            status="fail",
            data_source=data_source,
            symbol=symbol,
            timeframe=timeframe,
            error=error_msg,
            duration_ms=duration_ms,
            metadata={"traceback": tb},
        )


def run_strategy_smoke_tests(
    strategy_names: Optional[List[str]] = None,
    config_path: str = "config/config.toml",
    market: str = "BTC/EUR",
    timeframe: str = "1h",
    lookback_days: int = 30,
    n_bars: Optional[int] = None,
    data_source: str = "synthetic",
    min_bars: int = 200,
) -> List[StrategySmokeResult]:
    """
    Fuehrt Smoke-Tests fuer mehrere Strategien aus.

    Dies ist die Haupt-API-Funktion fuer Strategy-Diagnose.

    Args:
        strategy_names: Liste von Strategie-Namen (Default: alle v1.1-offiziellen)
        config_path: Pfad zur Config-Datei
        market: Markt-Symbol (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h")
        lookback_days: Anzahl Tage fuer Backtest (beeinflusst n_bars)
        n_bars: Explizite Anzahl Bars (ueberschreibt lookback_days)
        data_source: Datenquelle ("synthetic" oder "kraken_cache")
        min_bars: Minimum benoetigte Bars fuer Data-QC (Phase 79)

    Returns:
        Liste von StrategySmokeResult fuer jede Strategie

    Notes:
        - data_source="synthetic" (Default): Synthetische OHLCV-Daten
        - data_source="kraken_cache": Echte Daten aus lokalem Kraken-Cache
          (keine Netzwerk-Aufrufe, nur lokale Parquet-Dateien)
        - Bei kraken_cache werden Data-Health-Felder gefuellt (Phase 79)
    """
    # Strategien ermitteln
    if strategy_names is None:
        try:
            strategy_names = get_v11_official_strategies(config_path)
        except Exception as e:
            # Fallback auf bekannte v1.1-Strategien
            strategy_names = [
                "ma_crossover",
                "rsi_reversion",
                "breakout",
                "momentum_1h",
                "bollinger_bands",
                "macd",
                "trend_following",
                "mean_reversion",
                "vol_regime_filter",
            ]

    # Daten laden (je nach data_source)
    data_health = None
    try:
        df, data_health = _load_ohlcv_for_smoke(
            data_source=data_source,
            market=market,
            timeframe=timeframe,
            lookback_days=lookback_days,
            n_bars=n_bars,
            config_path=config_path,
            min_bars=min_bars,
        )
    except (FileNotFoundError, ValueError) as e:
        # Bei Datenlade-Fehler: alle Strategien als fail markieren
        # Extrahiere Data-Health-Status aus Error-Message wenn moeglich
        error_str = str(e)
        health_status = "other"
        if "missing_file" in error_str.lower() or "nicht gefunden" in error_str.lower():
            health_status = "missing_file"
        elif "too_few_bars" in error_str.lower():
            health_status = "too_few_bars"
        elif "empty" in error_str.lower():
            health_status = "empty"

        return [
            StrategySmokeResult(
                name=name,
                status="fail",
                data_source=data_source,
                symbol=market,
                timeframe=timeframe,
                error=error_str,
                data_health=health_status,
                data_notes=error_str[:200] if len(error_str) > 200 else error_str,
            )
            for name in strategy_names
        ]

    # Health-Info extrahieren (fuer kraken_cache)
    health_status_str = None
    health_notes_str = None
    if data_health is not None:
        health_status_str = data_health.status
        health_notes_str = data_health.notes

    # Tests ausfuehren
    results = []
    for name in strategy_names:
        result = run_single_strategy_smoke(
            strategy_name=name,
            df=df,
            config_path=config_path,
            data_source=data_source,
            symbol=market,
            timeframe=timeframe,
        )
        # Data-Health-Felder setzen (Phase 79)
        result.data_health = health_status_str if health_status_str else "ok"
        result.data_notes = health_notes_str
        results.append(result)

    return results


def summarize_smoke_results(results: List[StrategySmokeResult]) -> Dict[str, Any]:
    """
    Erstellt eine Zusammenfassung der Smoke-Test-Ergebnisse.

    Args:
        results: Liste von StrategySmokeResult

    Returns:
        Dict mit Summary-Informationen
    """
    ok_count = sum(1 for r in results if r.status == "ok")
    fail_count = sum(1 for r in results if r.status == "fail")

    failed_strategies = [r.name for r in results if r.status == "fail"]

    total_duration_ms = sum(r.duration_ms or 0 for r in results)

    return {
        "total": len(results),
        "ok": ok_count,
        "fail": fail_count,
        "failed_strategies": failed_strategies,
        "all_passed": fail_count == 0,
        "total_duration_ms": total_duration_ms,
    }


def format_smoke_result_line(result: StrategySmokeResult, show_data_info: bool = True) -> str:
    """
    Formatiert ein einzelnes Smoke-Result fuer CLI-Output.

    Args:
        result: StrategySmokeResult
        show_data_info: Ob Datenquelle-Info angezeigt werden soll

    Returns:
        Formatierter String
    """
    # Datenquelle-Info-String erstellen
    data_info = ""
    if show_data_info and result.data_source:
        data_parts = [f"data={result.data_source}"]
        if result.symbol:
            data_parts.append(f"symbol={result.symbol}")
        if result.timeframe:
            data_parts.append(f"tf={result.timeframe}")
        if result.num_bars:
            data_parts.append(f"bars={result.num_bars}")
        # Phase 79: Data-Health anzeigen wenn nicht "ok"
        if result.data_health and result.data_health != "ok":
            data_parts.append(f"health={result.data_health}")
        data_info = f" ({', '.join(data_parts)})"

    if result.status == "ok":
        return_str = f"{result.return_pct:+.2f}%" if result.return_pct is not None else "N/A"
        sharpe_str = f"{result.sharpe:.2f}" if result.sharpe is not None else "N/A"
        dd_str = f"{result.max_drawdown_pct:.2f}%" if result.max_drawdown_pct is not None else "N/A"
        trades_str = str(result.num_trades) if result.num_trades is not None else "N/A"

        return (
            f"[OK]   {result.name:<20}{data_info} | "
            f"Return: {return_str:>10} | "
            f"Sharpe: {sharpe_str:>6} | "
            f"MaxDD: {dd_str:>8} | "
            f"Trades: {trades_str:>4}"
        )
    else:
        error_short = (
            result.error[:50] + "..." if result.error and len(result.error) > 50 else result.error
        )
        # Phase 79: Data-Health-Info bei FAIL anzeigen
        health_info = ""
        if result.data_health and result.data_health != "ok":
            health_info = f" [Data: {result.data_health}]"
        return f"[FAIL] {result.name:<20}{data_info}{health_info} | Error: {error_short}"
