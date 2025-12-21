# src/market_sentinel/v0_daily_outlook.py
"""
MarketSentinel v0 – Daily Market Outlook
=========================================

Automatische tägliche Marktprognose mit Feature-Berechnung und LLM-Integration.

Komponenten:
- MarketConfig: Konfiguration für einen einzelnen Markt
- MarketFeatureSnapshot: Berechnete Features für einen Markt
- DailyMarketOutlookConfig: Gesamtkonfiguration für Daily Outlook
- DailyMarketOutlookResult: Ergebnis eines Outlook-Runs
- load_daily_outlook_config: Lädt Config aus YAML
- load_ohlcv_for_market: Lädt OHLCV-Daten (CSV oder Dummy)
- compute_feature_snapshot: Berechnet Features aus OHLCV
- build_llm_messages: Baut System- und User-Prompt
- call_llm: Ruft LLM-API auf
- write_markdown_report: Schreibt Markdown-Report
- run_daily_market_outlook: Orchestrator-Funktion

Stand: Dezember 2024
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

logger = logging.getLogger(__name__)


# ============================================================================
# DATACLASSES
# ============================================================================


@dataclass
class MarketConfig:
    """
    Konfiguration für einen einzelnen Markt.

    Attributes:
        id: Interner Identifier (z.B. "BTCUSDT", "SPX")
        symbol: Symbol-Name für Daten-Loading
        display_name: Anzeigename (z.B. "BTC / USDT", "S&P 500")
        timeframe: Zeitrahmen (z.B. "1d")
        lookback_days: Wie viele Tage historische Daten

    Example:
        >>> config = MarketConfig(
        ...     id="BTCUSDT",
        ...     symbol="btcusdt",
        ...     display_name="BTC / USDT",
        ...     timeframe="1d",
        ...     lookback_days=60
        ... )
    """

    id: str
    symbol: str
    display_name: str
    timeframe: str = "1d"
    lookback_days: int = 60

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if not self.id:
            raise ValueError("MarketConfig.id darf nicht leer sein")
        if not self.symbol:
            raise ValueError("MarketConfig.symbol darf nicht leer sein")

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "display_name": self.display_name,
            "timeframe": self.timeframe,
            "lookback_days": self.lookback_days,
        }


@dataclass
class MarketFeatureSnapshot:
    """
    Berechnete Features für einen Markt zu einem Zeitpunkt.

    Attributes:
        market: MarketConfig des Marktes
        last_price: Letzter Schlusskurs
        change_1d: Veränderung 1 Tag (in %)
        change_5d: Veränderung 5 Tage (in %)
        change_20d: Veränderung 20 Tage (in %)
        realized_vol_20d: Realisierte Volatilität 20 Tage (annualisiert, in %)
        price_vs_ma50: Prozent-Abstand zum 50-Tage-MA
        price_vs_ma200: Prozent-Abstand zum 200-Tage-MA
        data_source: Quelle der Daten ("csv", "dummy", etc.)
        timestamp: Zeitstempel der Feature-Berechnung

    Example:
        >>> snapshot = MarketFeatureSnapshot(
        ...     market=btc_config,
        ...     last_price=42000.0,
        ...     change_1d=2.5,
        ...     change_5d=8.3,
        ...     change_20d=-5.2,
        ...     realized_vol_20d=45.0,
        ...     price_vs_ma50=3.2,
        ...     price_vs_ma200=15.4,
        ... )
    """

    market: MarketConfig
    last_price: float | None = None
    change_1d: float | None = None
    change_5d: float | None = None
    change_20d: float | None = None
    realized_vol_20d: float | None = None
    price_vs_ma50: float | None = None
    price_vs_ma200: float | None = None
    data_source: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "market_id": self.market.id,
            "display_name": self.market.display_name,
            "last_price": self.last_price,
            "change_1d": self.change_1d,
            "change_5d": self.change_5d,
            "change_20d": self.change_20d,
            "realized_vol_20d": self.realized_vol_20d,
            "price_vs_ma50": self.price_vs_ma50,
            "price_vs_ma200": self.price_vs_ma200,
            "data_source": self.data_source,
            "timestamp": self.timestamp,
        }

    def format_for_llm(self) -> str:
        """Formatiert Snapshot für LLM-Prompt als Markdown-Zeile."""

        def fmt(val: float | None, suffix: str = "%") -> str:
            if val is None:
                return "n/a"
            if suffix == "%":
                return f"{val:+.2f}%"
            return f"{val:.2f}"

        return (
            f"| {self.market.display_name} | "
            f"{fmt(self.last_price, '')} | "
            f"{fmt(self.change_1d)} | "
            f"{fmt(self.change_5d)} | "
            f"{fmt(self.change_20d)} | "
            f"{fmt(self.realized_vol_20d)} | "
            f"{fmt(self.price_vs_ma50)} | "
            f"{fmt(self.price_vs_ma200)} |"
        )


@dataclass
class DailyMarketOutlookConfig:
    """
    Gesamtkonfiguration für den Daily Market Outlook.

    Attributes:
        report_id: Eindeutige Report-ID (z.B. "MARKET_SENTINEL_DAILY_V0")
        output_subdir: Unterverzeichnis für Reports (z.B. "daily")
        horizons: Liste der Zeithorizonte (z.B. ["short_term", "tactical"])
        markets: Liste der MarketConfig-Objekte
        llm_config: Optionale LLM-Konfiguration

    Example:
        >>> config = DailyMarketOutlookConfig(
        ...     report_id="MARKET_SENTINEL_DAILY_V0",
        ...     output_subdir="daily",
        ...     horizons=["short_term", "tactical"],
        ...     markets=[btc_config, spx_config],
        ... )
    """

    report_id: str
    output_subdir: str
    horizons: list[str]
    markets: list[MarketConfig]
    llm_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validierung nach Initialisierung."""
        if not self.report_id:
            raise ValueError("DailyMarketOutlookConfig.report_id darf nicht leer sein")
        if not self.horizons:
            raise ValueError(
                "DailyMarketOutlookConfig.horizons muss mindestens einen Horizont enthalten"
            )
        if not self.markets:
            raise ValueError(
                "DailyMarketOutlookConfig.markets muss mindestens einen Markt enthalten"
            )

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "report_id": self.report_id,
            "output_subdir": self.output_subdir,
            "horizons": self.horizons,
            "markets": [m.to_dict() for m in self.markets],
            "llm_config": self.llm_config,
        }


@dataclass
class DailyMarketOutlookResult:
    """
    Ergebnis eines Daily Market Outlook Runs.

    Attributes:
        config: Die verwendete Konfiguration
        snapshots: Liste der MarketFeatureSnapshots
        created_at: Erstellungszeitpunkt
        report_path: Pfad zum generierten Report
        llm_output: Rohtext der LLM-Ausgabe
        success: Ob der Run erfolgreich war
        error_message: Fehlermeldung falls nicht erfolgreich

    Example:
        >>> result = run_daily_market_outlook(config_path, output_dir)
        >>> print(result.report_path)
    """

    config: DailyMarketOutlookConfig
    snapshots: list[MarketFeatureSnapshot]
    created_at: datetime = field(default_factory=datetime.now)
    report_path: Path | None = None
    llm_output: str | None = None
    success: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "config": self.config.to_dict(),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "created_at": self.created_at.isoformat(),
            "report_path": str(self.report_path) if self.report_path else None,
            "success": self.success,
            "error_message": self.error_message,
        }


# ============================================================================
# CONFIG LOADER
# ============================================================================


def load_daily_outlook_config(path: Path) -> DailyMarketOutlookConfig:
    """
    Lädt die Daily Outlook Konfiguration aus einer YAML-Datei.

    Args:
        path: Pfad zur YAML-Config-Datei

    Returns:
        DailyMarketOutlookConfig-Objekt

    Raises:
        FileNotFoundError: Wenn die Config-Datei nicht existiert
        ValueError: Bei ungültiger Config-Struktur

    Example:
        >>> config = load_daily_outlook_config(Path("config/market_outlook/daily_market_outlook.yaml"))
        >>> print(config.report_id)
        "MARKET_SENTINEL_DAILY_V0"
    """
    if not path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw:
        raise ValueError(f"Config-Datei ist leer oder ungültig: {path}")

    # Pflichtfelder prüfen
    required_fields = ["report_id", "horizons", "markets"]
    for field_name in required_fields:
        if field_name not in raw:
            raise ValueError(f"Pflichtfeld '{field_name}' fehlt in Config: {path}")

    # Markets parsen
    markets = []
    for m in raw["markets"]:
        market_config = MarketConfig(
            id=m.get("id", ""),
            symbol=m.get("symbol", ""),
            display_name=m.get("display_name", m.get("id", "")),
            timeframe=m.get("timeframe", "1d"),
            lookback_days=m.get("lookback_days", 60),
        )
        markets.append(market_config)

    # LLM-Config extrahieren (optional)
    llm_config = raw.get("llm", {})

    return DailyMarketOutlookConfig(
        report_id=raw["report_id"],
        output_subdir=raw.get("output_subdir", "daily"),
        horizons=raw["horizons"],
        markets=markets,
        llm_config=llm_config,
    )


# ============================================================================
# DATA LOADING
# ============================================================================


def _generate_dummy_ohlcv(days: int = 60, start_price: float = 100.0) -> pd.DataFrame:
    """
    Generiert synthetische Dummy-OHLCV-Daten (Random Walk).

    Args:
        days: Anzahl der Tage
        start_price: Startpreis

    Returns:
        DataFrame mit datetime-Index und OHLCV-Spalten

    Note:
        Diese Daten sind rein synthetisch und dienen nur zu Testzwecken.
        Sie sollten nicht für echte Analyse verwendet werden.
    """
    np.random.seed(42)  # Reproduzierbar für Tests

    # Random Walk
    returns = np.random.normal(0, 0.02, days)  # ~2% tägliche Volatilität
    prices = start_price * np.cumprod(1 + returns)

    # Generiere OHLCV
    dates = pd.date_range(end=datetime.now().date(), periods=days, freq="D")

    df = pd.DataFrame(
        {
            "datetime": dates,
            "open": prices * (1 + np.random.uniform(-0.005, 0.005, days)),
            "high": prices * (1 + np.random.uniform(0, 0.02, days)),
            "low": prices * (1 - np.random.uniform(0, 0.02, days)),
            "close": prices,
            "volume": np.random.uniform(1e6, 1e8, days),
        }
    )

    df = df.set_index("datetime")
    return df


def load_ohlcv_for_market(
    market: MarketConfig,
    data_dir: Path | None = None,
) -> tuple[pd.DataFrame, str]:
    """
    Lädt OHLCV-Daten für einen Markt.

    v0-Implementierung:
    - Versucht CSV zu laden aus data/ohlcv/{market.id.lower()}_1d.csv
    - Falls nicht vorhanden: Generiert Dummy-Daten

    Args:
        market: MarketConfig des Marktes
        data_dir: Optionales Datenverzeichnis (Default: data/ohlcv/)

    Returns:
        Tuple aus (DataFrame, data_source)
        - DataFrame: OHLCV-Daten mit datetime-Index
        - data_source: "csv" oder "dummy"

    Example:
        >>> df, source = load_ohlcv_for_market(btc_config)
        >>> print(source)
        "csv" oder "dummy"
    """
    if data_dir is None:
        data_dir = Path("data/ohlcv")

    # Versuche CSV zu laden
    csv_filename = f"{market.id.lower()}_{market.timeframe}.csv"
    csv_path = data_dir / csv_filename

    if csv_path.exists():
        logger.info(f"Lade CSV für {market.id}: {csv_path}")
        try:
            df = pd.read_csv(csv_path, parse_dates=["datetime"])
            if "datetime" in df.columns:
                df = df.set_index("datetime")
            elif df.index.name != "datetime":
                # Versuche ersten Spalte als Datetime
                df.index = pd.to_datetime(df.index)

            # Validiere Mindestanforderungen
            if "close" not in df.columns:
                raise ValueError(f"CSV muss 'close'-Spalte enthalten: {csv_path}")

            # Begrenze auf lookback_days
            if len(df) > market.lookback_days:
                df = df.tail(market.lookback_days)

            return df, "csv"

        except Exception as e:
            logger.warning(f"Fehler beim Laden von {csv_path}: {e}")
            logger.info(f"Verwende Dummy-Daten für {market.id}")

    # Fallback: Dummy-Daten
    logger.info(
        f"Keine CSV gefunden für {market.id}, generiere Dummy-Daten "
        f"(Hinweis: Dies sind synthetische Testdaten!)"
    )

    # Setze sinnvollen Startpreis je nach Markt
    start_prices = {
        "BTCUSDT": 42000.0,
        "ETHUSDT": 2200.0,
        "SPX": 4800.0,
        "NDX": 16500.0,
        "DAX": 17000.0,
        "US10Y": 4.2,
        "EURUSD": 1.08,
        "GOLD": 2000.0,
        "OIL": 75.0,
    }
    start_price = start_prices.get(market.id.upper(), 100.0)

    df = _generate_dummy_ohlcv(days=market.lookback_days, start_price=start_price)
    return df, "dummy"


# ============================================================================
# FEATURE COMPUTATION
# ============================================================================


def compute_feature_snapshot(
    df: pd.DataFrame,
    market: MarketConfig,
    data_source: str = "unknown",
) -> MarketFeatureSnapshot:
    """
    Berechnet Features aus OHLCV-Daten für einen Markt.

    Berechnete Features:
    - last_price: Letzter Close
    - change_1d: (Last / Close[-1] - 1) * 100
    - change_5d: (Last / Close[-5] - 1) * 100
    - change_20d: (Last / Close[-20] - 1) * 100
    - realized_vol_20d: Std(Returns[-20:]) * sqrt(252) * 100
    - price_vs_ma50: (Last / MA50 - 1) * 100
    - price_vs_ma200: (Last / MA200 - 1) * 100

    Args:
        df: DataFrame mit datetime-Index und 'close'-Spalte
        market: MarketConfig des Marktes
        data_source: Quelle der Daten ("csv", "dummy", etc.)

    Returns:
        MarketFeatureSnapshot mit berechneten Features

    Note:
        Bei zu wenig Daten werden entsprechende Felder auf None gesetzt.

    Example:
        >>> snapshot = compute_feature_snapshot(df, btc_config, "csv")
        >>> print(f"BTC: {snapshot.change_1d:+.2f}%")
    """
    if df.empty or "close" not in df.columns:
        logger.warning(f"Keine gültigen Daten für {market.id}")
        return MarketFeatureSnapshot(market=market, data_source=data_source)

    # Sortiere nach Datum (sicherheitshalber)
    df = df.sort_index()
    closes = df["close"].dropna()

    if len(closes) < 2:
        logger.warning(f"Zu wenig Daten für {market.id}: {len(closes)} Datenpunkte")
        return MarketFeatureSnapshot(market=market, data_source=data_source)

    # Letzter Preis
    last_price = float(closes.iloc[-1])

    # Performance-Metriken
    def safe_change(n: int) -> float | None:
        if len(closes) > n:
            prev = closes.iloc[-n - 1]
            if prev != 0:
                return ((last_price / prev) - 1) * 100
        return None

    change_1d = safe_change(1)
    change_5d = safe_change(5)
    change_20d = safe_change(20)

    # Realisierte Volatilität (20 Tage, annualisiert)
    realized_vol_20d = None
    if len(closes) >= 21:
        returns = closes.pct_change().dropna().tail(20)
        if len(returns) >= 10:
            vol_daily = returns.std()
            realized_vol_20d = float(vol_daily * np.sqrt(252) * 100)

    # MA-Abstände
    price_vs_ma50 = None
    price_vs_ma200 = None

    if len(closes) >= 50:
        ma50 = closes.tail(50).mean()
        if ma50 > 0:
            price_vs_ma50 = float((last_price / ma50 - 1) * 100)

    if len(closes) >= 200:
        ma200 = closes.tail(200).mean()
        if ma200 > 0:
            price_vs_ma200 = float((last_price / ma200 - 1) * 100)

    return MarketFeatureSnapshot(
        market=market,
        last_price=last_price,
        change_1d=change_1d,
        change_5d=change_5d,
        change_20d=change_20d,
        realized_vol_20d=realized_vol_20d,
        price_vs_ma50=price_vs_ma50,
        price_vs_ma200=price_vs_ma200,
        data_source=data_source,
    )


# ============================================================================
# LLM PROMPT BUILDING
# ============================================================================

# System-Prompt für den Marktprognose-Spezialisten
SYSTEM_PROMPT = """Du bist der **Globale Marktprognose- und Makro-Spezialist** für das Peak_Trade-Projekt.

## Dein Scope

**Asset-Klassen:**
- Aktien (global, Indizes: S&P 500, Nasdaq, DAX, etc.)
- Anleihen & Zinsen (US 10Y, Bunds)
- FX (EUR/USD, etc.)
- Rohstoffe (Gold, Öl)
- Krypto (BTC, ETH, etc.)

**Zeithorizonte:**
- short_term: Tage bis ca. 1–4 Wochen
- tactical: 1–3 Monate

## Deine Aufgaben

Bei jeder Analyse:

1. **Regime-Beschreibung:**
   - Wachstum vs. Rezessionsrisiko
   - Inflationstrend
   - Zinsregime / Zentralbankmodus
   - Liquidität & Risikoappetit (Risk-On vs. Risk-Off)
   - Volatilitätslage

2. **Szenario-Setups (Bear / Base / Bull):**
   Pro Szenario:
   - Richtung & ungefähre Größenordnung (Range)
   - Wichtigste Treiber & Trigger-Events
   - Zentrale Risiken
   - Cross-Asset-Reaktionen

3. **Peak_Trade-Testideen:**
   Übersetze Szenarien in modellierbare Parameter:
   - Volatilitätslevel, Trendstärke, Mean-Reversion
   - Crash-/Gap-Häufigkeit, Drawdown-Clustering
   - Testprofile (z.B. "HIGH_VOL_CRASH_CLUSTER", "MILD_RALLY_LOW_VOL")

## Safety & Grenzen

- **Keine persönliche Anlageberatung**
- **Keine "kauf/verkauf jetzt Asset X"-Aussagen**
- Betone immer Unsicherheit: Szenarien sind Denkwerkzeuge, keine Versprechen
- Lieber Cluster von Möglichkeiten als Pseudo-Exaktheit

## Stil

- Klar strukturiert (Überschriften, Aufzählungen)
- Sachlich-verständlich
- Ehrlich mit Unsicherheit
- Antworte auf Deutsch
"""


def build_llm_messages(
    config: DailyMarketOutlookConfig,
    snapshots: list[MarketFeatureSnapshot],
) -> list[dict[str, str]]:
    """
    Baut die LLM-Messages (System + User) für den Daily Outlook.

    Args:
        config: Die Outlook-Konfiguration
        snapshots: Liste der berechneten MarketFeatureSnapshots

    Returns:
        Liste von Message-Dicts für LLM-API

    Example:
        >>> messages = build_llm_messages(config, snapshots)
        >>> # messages[0] = System-Message
        >>> # messages[1] = User-Message mit Daten und Aufgabenstellung
    """
    # Baue Feature-Tabelle
    table_header = (
        "| Markt | Letzter Preis | 1d Δ | 5d Δ | 20d Δ | Vol 20d | vs MA50 | vs MA200 |\n"
        "|-------|---------------|------|------|-------|---------|---------|----------|\n"
    )

    table_rows = "\n".join([s.format_for_llm() for s in snapshots])
    feature_table = table_header + table_rows

    # Ermittle Datenquellen
    sources = set(s.data_source for s in snapshots)
    source_note = ""
    if "dummy" in sources:
        source_note = (
            "\n\n**⚠️ Hinweis:** Einige Märkte verwenden synthetische Testdaten (dummy). "
            "Die Analyse basiert teilweise auf simulierten Werten."
        )

    # Horizonte formatieren
    horizons_str = ", ".join(config.horizons)

    user_message = f"""# Daily Market Outlook – {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Marktdaten (Feature-Snapshots)

{feature_table}
{source_note}

## Zeithorizonte für diese Analyse

- **{horizons_str}**

---

## Aufgabenstellung

Bitte analysiere die obigen Marktdaten und erstelle:

1. **Regime-Beschreibung (global)**
   - Aktuelles Makro-Regime
   - Dominante Treiber

2. **Szenario-Analyse**
   Für jeden Zeithorizont ({horizons_str}):
   - **Bear-Szenario:** Richtung, Treiber, Risiken
   - **Base-Szenario:** Richtung, Treiber, Risiken
   - **Bull-Szenario:** Richtung, Treiber, Risiken

3. **Cross-Asset-Zusammenhänge**
   - Risk-On vs. Risk-Off Muster
   - Korrelationsregime

4. **Peak_Trade-Testempfehlungen**
   - 2-3 konkrete Testprofile/Regime-Setups für Backtests
   - Welche Metriken besonders beachten (DD, Vol, Regime-Heatmaps)

Antworte strukturiert mit klaren Überschriften und Aufzählungen.
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


# ============================================================================
# LLM CALL
# ============================================================================


def call_llm(
    messages: list[dict[str, str]],
    model: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.7,
) -> str:
    """
    Ruft die LLM-API auf und gibt die Antwort zurück.

    Verwendet OpenAI-API (oder kompatible Alternative).
    API-Key wird aus Umgebungsvariable OPENAI_API_KEY gelesen.
    Modell kann via OPENAI_MODEL überschrieben werden.

    Args:
        messages: Liste von Message-Dicts
        model: Modell-Name (Default: aus ENV oder "gpt-4o")
        max_tokens: Maximale Tokens für Antwort
        temperature: Temperatur für Sampling

    Returns:
        LLM-Antwort als String

    Raises:
        ValueError: Wenn kein API-Key gesetzt ist
        RuntimeError: Bei API-Fehlern

    Example:
        >>> output = call_llm(messages)
        >>> print(output)
    """
    # API-Key aus Umgebung
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY nicht gesetzt. "
            "Bitte setze die Umgebungsvariable: export OPENAI_API_KEY='sk-...'"
        )

    # Modell aus Umgebung oder Parameter oder Default
    if model is None:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    logger.info(f"Rufe LLM auf: model={model}, max_tokens={max_tokens}")

    try:
        # Versuche OpenAI-Import
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai-Paket nicht installiert. Bitte installiere mit: pip install openai"
            )

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if not response.choices:
            raise RuntimeError("LLM-Antwort enthält keine Choices")

        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM-Antwort enthält keinen Content")

        logger.info(f"LLM-Antwort erhalten: {len(content)} Zeichen")
        return content

    except Exception as e:
        logger.error(f"LLM-Aufruf fehlgeschlagen: {e}")
        raise RuntimeError(f"LLM-Aufruf fehlgeschlagen: {e}") from e


# ============================================================================
# REPORT WRITING
# ============================================================================


def write_markdown_report(
    result: DailyMarketOutlookResult,
    llm_output: str,
    base_output_dir: Path,
) -> Path:
    """
    Schreibt den Markdown-Report für den Daily Market Outlook.

    Args:
        result: DailyMarketOutlookResult mit Config und Snapshots
        llm_output: Rohe LLM-Ausgabe
        base_output_dir: Basis-Verzeichnis für Reports

    Returns:
        Pfad zur geschriebenen Report-Datei

    Example:
        >>> report_path = write_markdown_report(result, llm_output, Path("reports/market_outlook"))
        >>> print(report_path)
        reports/market_outlook/daily/20241210_0800_daily_market_outlook.md
    """
    # Zielverzeichnis erstellen
    output_dir = base_output_dir / result.config.output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Dateiname mit Timestamp
    timestamp = result.created_at.strftime("%Y%m%d_%H%M")
    filename = f"{timestamp}_daily_market_outlook.md"
    report_path = output_dir / filename

    # Report-Inhalt aufbauen
    horizons_str = ", ".join(result.config.horizons)
    markets_str = ", ".join([m.display_name for m in result.config.markets])

    # Feature-Tabelle
    table_header = (
        "| Markt | Letzter Preis | 1d Δ | 5d Δ | 20d Δ | Vol 20d | vs MA50 | vs MA200 | Quelle |\n"
        "|-------|---------------|------|------|-------|---------|---------|----------|--------|\n"
    )
    table_rows = []
    for s in result.snapshots:
        row = s.format_for_llm()
        # Füge Quelle hinzu
        row = row.rstrip("|") + f" {s.data_source} |"
        table_rows.append(row)

    feature_table = table_header + "\n".join(table_rows)

    # Markdown-Report
    report_content = f"""# Daily Market Outlook – MarketSentinel v0

> **Report-ID:** {result.config.report_id}
> **Erstellt:** {result.created_at.strftime("%Y-%m-%d %H:%M:%S")}
> **Horizonte:** {horizons_str}
> **Märkte:** {markets_str}

---

## Feature-Snapshots

{feature_table}

---

## LLM-Auswertung & Szenarien

{llm_output}

---

## Technische Hinweise

- **Generator:** MarketSentinel v0 (Peak_Trade)
- **Datenquellen:** {", ".join(set(s.data_source for s in result.snapshots))}
- **Disclaimer:** Dies ist keine Anlageberatung. Szenarien sind analytische Denkwerkzeuge, keine Prognosen oder Empfehlungen.

---

*Automatisch generiert von MarketSentinel v0*
"""

    # Schreibe Datei
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info(f"Report geschrieben: {report_path}")
    return report_path


# ============================================================================
# ORCHESTRATOR
# ============================================================================


def run_daily_market_outlook(
    config_path: Path,
    base_output_dir: Path,
    skip_llm: bool = False,
    data_dir: Path | None = None,
) -> DailyMarketOutlookResult:
    """
    Orchestrator-Funktion: Führt den kompletten Daily Market Outlook durch.

    Schritte:
    1. Config laden
    2. Für alle Märkte: Daten laden → Features berechnen
    3. LLM-Messages bauen → LLM aufrufen (oder überspringen)
    4. Report schreiben
    5. Result zurückgeben

    Args:
        config_path: Pfad zur YAML-Config
        base_output_dir: Basis-Verzeichnis für Reports
        skip_llm: Wenn True, LLM-Aufruf überspringen (für Tests)
        data_dir: Optionales Datenverzeichnis

    Returns:
        DailyMarketOutlookResult mit Report-Pfad und Snapshots

    Example:
        >>> result = run_daily_market_outlook(
        ...     config_path=Path("config/market_outlook/daily_market_outlook.yaml"),
        ...     base_output_dir=Path("reports/market_outlook"),
        ... )
        >>> print(f"Report erstellt: {result.report_path}")

    Note:
        Bei skip_llm=True wird ein Platzhalter-Text verwendet.
    """
    logger.info(f"Starte Daily Market Outlook: config={config_path}")
    created_at = datetime.now()

    try:
        # 1. Config laden
        config = load_daily_outlook_config(config_path)
        logger.info(f"Config geladen: {len(config.markets)} Märkte, Horizonte: {config.horizons}")

        # 2. Für alle Märkte: Daten laden & Features berechnen
        snapshots: list[MarketFeatureSnapshot] = []
        for market in config.markets:
            logger.info(f"Verarbeite {market.display_name}...")
            df, source = load_ohlcv_for_market(market, data_dir)
            snapshot = compute_feature_snapshot(df, market, source)
            snapshots.append(snapshot)
            logger.debug(f"  -> {market.id}: last_price={snapshot.last_price}")

        # 3. LLM-Messages bauen & aufrufen
        messages = build_llm_messages(config, snapshots)

        if skip_llm:
            logger.info("LLM-Aufruf übersprungen (skip_llm=True)")
            llm_output = (
                "*LLM-Aufruf wurde übersprungen (skip_llm=True).*\n\n"
                "Dies ist ein Platzhalter für den eigentlichen LLM-Output. "
                "Setze skip_llm=False und konfiguriere OPENAI_API_KEY für echte Analyse."
            )
        else:
            # LLM-Config aus Config-Datei
            model = config.llm_config.get("model")
            max_tokens = config.llm_config.get("max_tokens", 4000)
            temperature = config.llm_config.get("temperature", 0.7)

            llm_output = call_llm(
                messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # 4. Result-Objekt erstellen
        result = DailyMarketOutlookResult(
            config=config,
            snapshots=snapshots,
            created_at=created_at,
            llm_output=llm_output,
            success=True,
        )

        # 5. Report schreiben
        report_path = write_markdown_report(result, llm_output, base_output_dir)
        result.report_path = report_path

        logger.info(f"Daily Market Outlook abgeschlossen: {report_path}")
        return result

    except Exception as e:
        logger.error(f"Daily Market Outlook fehlgeschlagen: {e}")
        # Erstelle Fehler-Result
        return DailyMarketOutlookResult(
            config=DailyMarketOutlookConfig(
                report_id="ERROR",
                output_subdir="daily",
                horizons=["short_term"],
                markets=[MarketConfig(id="ERROR", symbol="error", display_name="Error")],
            ),
            snapshots=[],
            created_at=created_at,
            success=False,
            error_message=str(e),
        )
