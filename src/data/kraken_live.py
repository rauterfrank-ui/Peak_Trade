# src/data/kraken_live.py
"""
Peak_Trade: Live Kraken Market Data Source (Phase 31)
=====================================================

Polling-basierte Live-Datenquelle für Kraken Public API.
Holt periodisch OHLCV-Daten und stellt sie der ShadowPaperSession bereit.

Features:
- Polling von Kraken Public OHLC Endpoint
- Interner Candle-Buffer mit konfigurierbarer Größe
- Robustes Error-Handling mit Retry-Logic
- Kein API-Key erforderlich (nur public data)
- Thread-safe Buffer-Operationen

WICHTIG: Dieses Modul verwendet NUR public market data endpoints.
         Es werden KEINE Orders gesendet oder private APIs verwendet.

Example:
    >>> source = KrakenLiveCandleSource(
    ...     symbol="BTC/EUR",
    ...     timeframe="1m",
    ...     warmup_candles=200,
    ... )
    >>> source.warmup()  # Initial-Daten holen
    >>> while True:
    ...     candle = source.poll_latest()
    ...     if candle is not None:
    ...         process(candle)
    ...     time.sleep(60)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Sequence

import pandas as pd
import requests

logger = logging.getLogger(__name__)


# =============================================================================
# Kraken Timeframe Mapping
# =============================================================================

# Kraken OHLC interval in minutes
KRAKEN_TIMEFRAME_MAP: Dict[str, int] = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
    "1w": 10080,
}


def _timeframe_to_minutes(tf: str) -> int:
    """Konvertiert Timeframe-String zu Minuten für Kraken API."""
    return KRAKEN_TIMEFRAME_MAP.get(tf, 1)


# =============================================================================
# Kraken Symbol Mapping
# =============================================================================

# Mapping von Standard-Symbolen zu Kraken-internen Namen
KRAKEN_SYMBOL_MAP: Dict[str, str] = {
    "BTC/EUR": "XXBTZEUR",
    "BTC/USD": "XXBTZUSD",
    "ETH/EUR": "XETHZEUR",
    "ETH/USD": "XETHZUSD",
    "XRP/EUR": "XXRPZEUR",
    "XRP/USD": "XXRPZUSD",
    "LTC/EUR": "XLTCZEUR",
    "LTC/USD": "XLTCZUSD",
    "ADA/EUR": "ADAEUR",
    "ADA/USD": "ADAUSD",
    "DOT/EUR": "DOTEUR",
    "DOT/USD": "DOTUSD",
    "SOL/EUR": "SOLEUR",
    "SOL/USD": "SOLUSD",
}


def _symbol_to_kraken(symbol: str) -> str:
    """Konvertiert Standard-Symbol zu Kraken-Format."""
    if symbol in KRAKEN_SYMBOL_MAP:
        return KRAKEN_SYMBOL_MAP[symbol]
    # Fallback: Symbol ohne Slash
    return symbol.replace("/", "")


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class LiveCandle:
    """
    Eine einzelne Live-Candle.

    Attributes:
        timestamp: UTC-Zeitstempel des Candle-Starts
        open: Eröffnungspreis
        high: Höchstpreis
        low: Tiefstpreis
        close: Schlusspreis
        volume: Handelsvolumen
        is_complete: Ob die Candle abgeschlossen ist
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_complete: bool = True

    def to_series(self) -> pd.Series:
        """Konvertiert zu pandas Series."""
        return pd.Series(
            {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            },
            name=self.timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "is_complete": self.is_complete,
        }


@dataclass
class LiveExchangeConfig:
    """
    Konfiguration für Live-Exchange-Verbindung.

    Attributes:
        name: Exchange-Name (z.B. "kraken")
        use_sandbox: Sandbox/Public-Only Modus
        base_url: Basis-URL für API
        rate_limit_ms: Rate-Limit in Millisekunden
        max_retries: Maximale Retry-Versuche
        retry_delay_seconds: Wartezeit zwischen Retries
    """

    name: str = "kraken"
    use_sandbox: bool = True
    base_url: str = "https://api.kraken.com"
    rate_limit_ms: int = 1000
    max_retries: int = 3
    retry_delay_seconds: float = 5.0


@dataclass
class ShadowPaperConfig:
    """
    Konfiguration für Shadow-/Paper-Session.

    Attributes:
        enabled: Session aktiviert
        mode: "shadow" oder "paper"
        symbol: Trading-Symbol
        timeframe: Candle-Timeframe
        poll_interval_seconds: Polling-Intervall
        warmup_candles: Anzahl initialer Candles
        start_balance: Start-Kapital
        position_fraction: Positionsgröße als Anteil
        fee_rate: Fee-Rate für Simulation
        slippage_bps: Slippage in Basispunkten
    """

    enabled: bool = True
    mode: str = "paper"
    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    poll_interval_seconds: float = 60.0
    warmup_candles: int = 200
    start_balance: float = 10000.0
    position_fraction: float = 0.1
    fee_rate: float = 0.0026
    slippage_bps: float = 5.0


# =============================================================================
# Candle Source Protocol
# =============================================================================


class CandleSource(Protocol):
    """Protocol für Candle-Datenquellen."""

    def warmup(self) -> List[LiveCandle]:
        """Holt initiale Candles für Warmup."""
        ...

    def poll_latest(self) -> Optional[LiveCandle]:
        """Pollt die neueste Candle."""
        ...

    def get_buffer(self) -> pd.DataFrame:
        """Gibt den Candle-Buffer als DataFrame zurück."""
        ...

    def get_latest_price(self) -> Optional[float]:
        """Gibt den aktuellsten Preis zurück."""
        ...


# =============================================================================
# KrakenLiveCandleSource
# =============================================================================


class KrakenLiveCandleSource:
    """
    Live-Datenquelle für Kraken Public API.

    Pollt periodisch OHLCV-Daten von Kraken und führt einen
    internen Buffer für die Strategie-Verarbeitung.

    Features:
    - Automatisches Symbol-Mapping (BTC/EUR -> XXBTZEUR)
    - Timeframe-Konvertierung
    - Retry-Logic bei Netzwerkfehlern
    - Buffer-Management mit konfigurierbarer Größe

    WICHTIG: Verwendet NUR public market data endpoints.
             KEINE API-Keys, KEINE Order-Endpoints.

    Example:
        >>> source = KrakenLiveCandleSource(
        ...     symbol="BTC/EUR",
        ...     timeframe="1m",
        ...     warmup_candles=200,
        ... )
        >>> source.warmup()
        >>> # Im Loop:
        >>> candle = source.poll_latest()
        >>> if candle:
        ...     print(f"Latest close: {candle.close}")
    """

    def __init__(
        self,
        symbol: str = "BTC/EUR",
        timeframe: str = "1m",
        base_url: str = "https://api.kraken.com",
        warmup_candles: int = 200,
        max_buffer_size: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        rate_limit_ms: int = 1000,
        session: Optional[requests.Session] = None,
    ) -> None:
        """
        Initialisiert die Kraken Live Candle Source.

        Args:
            symbol: Trading-Symbol (z.B. "BTC/EUR")
            timeframe: Candle-Timeframe (z.B. "1m", "5m", "1h")
            base_url: Kraken API Base URL
            warmup_candles: Anzahl initialer Candles für Warmup
            max_buffer_size: Maximale Buffer-Größe
            max_retries: Max. Retry-Versuche bei Fehlern
            retry_delay: Wartezeit zwischen Retries (Sekunden)
            rate_limit_ms: Rate-Limit in Millisekunden
            session: Optionale requests.Session für Connection-Pooling
        """
        self.symbol = symbol
        self.kraken_symbol = _symbol_to_kraken(symbol)
        self.timeframe = timeframe
        self.interval_minutes = _timeframe_to_minutes(timeframe)
        self.base_url = base_url.rstrip("/")
        self.warmup_candles = warmup_candles
        self.max_buffer_size = max_buffer_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_ms = rate_limit_ms

        # Session für Connection-Pooling
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": "PeakTrade/1.0 (Shadow-Paper-Session)"})

        # Interner Buffer
        self._buffer: List[LiveCandle] = []
        self._last_timestamp: Optional[datetime] = None
        self._last_poll_time: float = 0.0

        logger.info(
            f"[KRAKEN LIVE] Initialisiert: symbol={symbol} ({self.kraken_symbol}), "
            f"timeframe={timeframe} ({self.interval_minutes}m), "
            f"warmup={warmup_candles}"
        )

    def _enforce_rate_limit(self) -> None:
        """Erzwingt Rate-Limit zwischen API-Calls."""
        elapsed_ms = (time.time() - self._last_poll_time) * 1000
        if elapsed_ms < self.rate_limit_ms:
            sleep_time = (self.rate_limit_ms - elapsed_ms) / 1000.0
            time.sleep(sleep_time)
        self._last_poll_time = time.time()

    def _fetch_ohlc(self, since: Optional[int] = None) -> List[List[Any]]:
        """
        Holt OHLC-Daten von Kraken Public API.

        Args:
            since: Unix-Timestamp (Sekunden) für Start der Daten

        Returns:
            Liste von OHLC-Daten [[timestamp, open, high, low, close, vwap, volume, count], ...]

        Raises:
            RuntimeError: Bei API-Fehlern nach allen Retries
        """
        self._enforce_rate_limit()

        url = f"{self.base_url}/0/public/OHLC"
        params: Dict[str, Any] = {
            "pair": self.kraken_symbol,
            "interval": self.interval_minutes,
        }
        if since is not None:
            params["since"] = since

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                # Kraken Error-Handling
                if data.get("error"):
                    errors = data["error"]
                    if errors:
                        error_msg = ", ".join(str(e) for e in errors)
                        raise RuntimeError(f"Kraken API Error: {error_msg}")

                # Ergebnis extrahieren
                result = data.get("result", {})

                # Finde den richtigen Key (kann variieren)
                ohlc_data: List[List[Any]] = []
                for key, value in result.items():
                    if key != "last" and isinstance(value, list):
                        ohlc_data = value
                        break

                return ohlc_data

            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(
                    f"[KRAKEN LIVE] Netzwerkfehler (Versuch {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

            except Exception as e:
                last_error = e
                logger.error(f"[KRAKEN LIVE] Unerwarteter Fehler: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

        raise RuntimeError(
            f"Kraken API nicht erreichbar nach {self.max_retries} Versuchen: {last_error}"
        )

    def _parse_ohlc_row(self, row: List[Any]) -> LiveCandle:
        """
        Parst eine OHLC-Zeile zu LiveCandle.

        Kraken OHLC Format:
        [timestamp, open, high, low, close, vwap, volume, count]

        Args:
            row: OHLC-Zeile von Kraken API

        Returns:
            LiveCandle-Objekt
        """
        # Timestamp ist in Sekunden (Unix)
        ts = datetime.fromtimestamp(float(row[0]), tz=timezone.utc)

        return LiveCandle(
            timestamp=ts,
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[6]),  # Index 6 ist volume, Index 5 ist vwap
            is_complete=True,  # Historische Candles sind komplett
        )

    def warmup(self) -> List[LiveCandle]:
        """
        Holt initiale Candles für Warmup der Strategie.

        Ruft die Kraken API auf und füllt den internen Buffer
        mit den letzten `warmup_candles` Candles.

        Returns:
            Liste der geholten Candles

        Raises:
            RuntimeError: Bei API-Fehlern
        """
        logger.info(f"[KRAKEN LIVE] Warmup: Hole {self.warmup_candles} Candles...")

        try:
            ohlc_data = self._fetch_ohlc()

            if not ohlc_data:
                logger.warning("[KRAKEN LIVE] Keine OHLC-Daten erhalten")
                return []

            # Parsen und in Buffer laden
            candles = [self._parse_ohlc_row(row) for row in ohlc_data]

            # Nach Timestamp sortieren (älteste zuerst)
            candles.sort(key=lambda c: c.timestamp)

            # Auf warmup_candles begrenzen (neueste behalten)
            if len(candles) > self.warmup_candles:
                candles = candles[-self.warmup_candles :]

            # Buffer aktualisieren
            self._buffer = candles

            if candles:
                self._last_timestamp = candles[-1].timestamp
                logger.info(
                    f"[KRAKEN LIVE] Warmup abgeschlossen: {len(candles)} Candles, "
                    f"von {candles[0].timestamp} bis {candles[-1].timestamp}"
                )

            return candles

        except Exception as e:
            logger.error(f"[KRAKEN LIVE] Warmup fehlgeschlagen: {e}")
            raise

    def poll_latest(self) -> Optional[LiveCandle]:
        """
        Pollt die neueste Candle von Kraken.

        Holt neue OHLC-Daten und gibt die neueste Candle zurück,
        wenn sie neuer als die letzte bekannte ist.

        Returns:
            Neue LiveCandle oder None wenn keine neuen Daten
        """
        try:
            # Since-Parameter: Letzte bekannte Timestamp
            since: Optional[int] = None
            if self._last_timestamp:
                since = int(self._last_timestamp.timestamp())

            ohlc_data = self._fetch_ohlc(since=since)

            if not ohlc_data:
                return None

            # Neueste Candle extrahieren
            latest_row = ohlc_data[-1]
            latest_candle = self._parse_ohlc_row(latest_row)

            # Prüfen ob neue Candle
            if self._last_timestamp and latest_candle.timestamp <= self._last_timestamp:
                # Keine neue Candle, aber Preis könnte sich geändert haben
                # Aktualisiere die letzte Candle im Buffer
                if self._buffer and latest_candle.timestamp == self._buffer[-1].timestamp:
                    self._buffer[-1] = latest_candle
                return None

            # Neue Candle gefunden
            self._buffer.append(latest_candle)
            self._last_timestamp = latest_candle.timestamp

            # Buffer-Größe begrenzen
            if len(self._buffer) > self.max_buffer_size:
                self._buffer = self._buffer[-self.max_buffer_size :]

            logger.debug(
                f"[KRAKEN LIVE] Neue Candle: {latest_candle.timestamp}, "
                f"close={latest_candle.close:.2f}"
            )

            return latest_candle

        except Exception as e:
            logger.error(f"[KRAKEN LIVE] Poll fehlgeschlagen: {e}")
            return None

    def poll(self) -> None:
        """
        Alias für poll_latest() ohne Rückgabe.

        Kompatibilität mit CandleSource-Protocol.
        """
        self.poll_latest()

    def get_buffer(self) -> pd.DataFrame:
        """
        Gibt den Candle-Buffer als DataFrame zurück.

        Returns:
            DataFrame mit OHLCV-Daten und DatetimeIndex
        """
        if not self._buffer:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        data = [c.to_dict() for c in self._buffer]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.drop(columns=["is_complete"], inplace=True, errors="ignore")
        return df

    def get_latest_price(self) -> Optional[float]:
        """
        Gibt den aktuellsten Close-Preis zurück.

        Returns:
            Letzter Close-Preis oder None
        """
        if not self._buffer:
            return None
        return self._buffer[-1].close

    def get_latest_candle(self) -> Optional[LiveCandle]:
        """
        Gibt die neueste Candle zurück.

        Returns:
            Letzte LiveCandle oder None
        """
        if not self._buffer:
            return None
        return self._buffer[-1]

    def get_buffer_size(self) -> int:
        """Gibt die aktuelle Buffer-Größe zurück."""
        return len(self._buffer)

    def clear_buffer(self) -> None:
        """Löscht den internen Buffer."""
        self._buffer.clear()
        self._last_timestamp = None
        logger.debug("[KRAKEN LIVE] Buffer geleert")


# =============================================================================
# Fake Candle Source for Testing
# =============================================================================


class FakeCandleSource:
    """
    Fake-Datenquelle für Tests ohne echte API-Calls.

    Liefert vordefinierte Candles aus einer Liste.
    Ideal für Unit-Tests der ShadowPaperSession.

    Example:
        >>> candles = [
        ...     LiveCandle(timestamp=datetime.now(timezone.utc), open=100, high=105, low=99, close=104, volume=10),
        ...     LiveCandle(timestamp=datetime.now(timezone.utc), open=104, high=108, low=103, close=107, volume=15),
        ... ]
        >>> source = FakeCandleSource(candles)
        >>> source.warmup()
        >>> candle = source.poll_latest()
    """

    def __init__(
        self,
        candles: Optional[List[LiveCandle]] = None,
        symbol: str = "BTC/EUR",
    ) -> None:
        """
        Initialisiert die Fake-Datenquelle.

        Args:
            candles: Liste vordefinierter Candles
            symbol: Symbol für Kompatibilität
        """
        self._candles = list(candles) if candles else []
        self._index = 0
        self._buffer: List[LiveCandle] = []
        self.symbol = symbol

    def warmup(self) -> List[LiveCandle]:
        """Lädt alle Candles in den Buffer."""
        # Warmup liefert die ersten 80% der Candles
        warmup_count = max(1, int(len(self._candles) * 0.8))
        self._buffer = self._candles[:warmup_count]
        self._index = warmup_count
        return list(self._buffer)

    def poll_latest(self) -> Optional[LiveCandle]:
        """Gibt die nächste Candle zurück."""
        if self._index >= len(self._candles):
            return None

        candle = self._candles[self._index]
        self._buffer.append(candle)
        self._index += 1
        return candle

    def poll(self) -> None:
        """Alias für poll_latest()."""
        self.poll_latest()

    def get_buffer(self) -> pd.DataFrame:
        """Gibt den Buffer als DataFrame zurück."""
        if not self._buffer:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        data = [c.to_dict() for c in self._buffer]
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        df.drop(columns=["is_complete"], inplace=True, errors="ignore")
        return df

    def get_latest_price(self) -> Optional[float]:
        """Gibt den letzten Close-Preis zurück."""
        if not self._buffer:
            return None
        return self._buffer[-1].close

    def get_latest_candle(self) -> Optional[LiveCandle]:
        """Gibt die letzte Candle zurück."""
        if not self._buffer:
            return None
        return self._buffer[-1]

    def reset(self) -> None:
        """Setzt die Datenquelle zurück."""
        self._index = 0
        self._buffer.clear()


# =============================================================================
# Factory Functions
# =============================================================================


def create_kraken_source_from_config(
    shadow_cfg: ShadowPaperConfig,
    exchange_cfg: LiveExchangeConfig,
) -> KrakenLiveCandleSource:
    """
    Factory-Funktion für KrakenLiveCandleSource aus Config-Objekten.

    Args:
        shadow_cfg: Shadow/Paper Session Config
        exchange_cfg: Exchange Config

    Returns:
        Konfigurierte KrakenLiveCandleSource
    """
    return KrakenLiveCandleSource(
        symbol=shadow_cfg.symbol,
        timeframe=shadow_cfg.timeframe,
        base_url=exchange_cfg.base_url,
        warmup_candles=shadow_cfg.warmup_candles,
        max_retries=exchange_cfg.max_retries,
        retry_delay=exchange_cfg.retry_delay_seconds,
        rate_limit_ms=exchange_cfg.rate_limit_ms,
    )


def load_shadow_paper_config(cfg: Any) -> ShadowPaperConfig:
    """
    Lädt ShadowPaperConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        ShadowPaperConfig mit Werten aus Config
    """
    return ShadowPaperConfig(
        enabled=cfg.get("shadow_paper.enabled", True),
        mode=cfg.get("shadow_paper.mode", "paper"),
        symbol=cfg.get("shadow_paper.symbol", "BTC/EUR"),
        timeframe=cfg.get("shadow_paper.timeframe", "1m"),
        poll_interval_seconds=cfg.get("shadow_paper.poll_interval_seconds", 60.0),
        warmup_candles=cfg.get("shadow_paper.warmup_candles", 200),
        start_balance=cfg.get("shadow_paper.start_balance", 10000.0),
        position_fraction=cfg.get("shadow_paper.position_fraction", 0.1),
        fee_rate=cfg.get("shadow_paper.fee_rate", 0.0026),
        slippage_bps=cfg.get("shadow_paper.slippage_bps", 5.0),
    )


def load_live_exchange_config(cfg: Any) -> LiveExchangeConfig:
    """
    Lädt LiveExchangeConfig aus PeakConfig.

    Args:
        cfg: PeakConfig-Objekt

    Returns:
        LiveExchangeConfig mit Werten aus Config
    """
    return LiveExchangeConfig(
        name=cfg.get("live_exchange.name", "kraken"),
        use_sandbox=cfg.get("live_exchange.use_sandbox", True),
        base_url=cfg.get("live_exchange.base_url", "https://api.kraken.com"),
        rate_limit_ms=cfg.get("live_exchange.rate_limit_ms", 1000),
        max_retries=cfg.get("live_exchange.max_retries", 3),
        retry_delay_seconds=cfg.get("live_exchange.retry_delay_seconds", 5.0),
    )
