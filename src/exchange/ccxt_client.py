# src/exchange/ccxt_client.py
"""
Peak_Trade CCXT Exchange Client
================================
Read-only Exchange-Client basierend auf ccxt.

Dieses Modul implementiert das `ExchangeClient`-Protokoll mit ccxt als Backend.
Alle Methoden sind ausschließlich lesend – keine Order-Platzierung!

Unterstützte Exchanges:
    Alle von ccxt unterstützten Exchanges (140+), z.B.:
    - kraken
    - binance
    - coinbasepro
    - bitstamp

Verwendung:
    >>> client = CcxtExchangeClient("kraken")
    >>> ticker = client.fetch_ticker("BTC/EUR")
    >>> print(f"BTC: {ticker.last}")

    >>> # Mit API-Key für Balance-Abfragen
    >>> client = CcxtExchangeClient(
    ...     "kraken",
    ...     api_key="...",
    ...     secret="...",
    ...     sandbox=True,
    ... )
    >>> balance = client.fetch_balance()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd

from .base import Balance, ExchangeClient, Ticker


class CcxtExchangeClient:
    """
    Read-only ccxt-basierter Exchange-Client.

    Implementiert das `ExchangeClient`-Protokoll für read-only Operationen:
    - Ticker (Preise)
    - OHLCV (Candlestick-Daten)
    - Balance (Kontostände, erfordert API-Key)
    - Open Orders (nur lesen, erfordert API-Key)

    WICHTIG: Keine Order-Platzierung implementiert!

    Args:
        exchange_id: ccxt Exchange-ID (z.B. "kraken", "binance")
        api_key: API-Key für authentifizierte Requests (optional)
        secret: API-Secret für authentifizierte Requests (optional)
        enable_rate_limit: Rate-Limiting aktivieren (empfohlen: True)
        sandbox: Sandbox/Testnet-Modus aktivieren (falls verfügbar)
        extra_config: Zusätzliche ccxt-Konfiguration

    Raises:
        ValueError: Bei unbekannter Exchange-ID

    Example:
        >>> # Ohne Authentifizierung (nur Public-Daten)
        >>> client = CcxtExchangeClient("kraken")
        >>> ticker = client.fetch_ticker("BTC/EUR")

        >>> # Mit Authentifizierung (für Balance/Orders)
        >>> client = CcxtExchangeClient(
        ...     "kraken",
        ...     api_key="your_key",
        ...     secret="your_secret",
        ...     sandbox=True,
        ... )
    """

    def __init__(
        self,
        exchange_id: str,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        *,
        enable_rate_limit: bool = True,
        sandbox: bool = False,
        extra_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        # Prüfe ob Exchange existiert
        if not hasattr(ccxt, exchange_id):
            available = [x for x in dir(ccxt) if not x.startswith("_") and x.islower()]
            raise ValueError(
                f"Unknown ccxt exchange id: {exchange_id!r}. "
                f"Available: {', '.join(available[:10])}... (and {len(available) - 10} more)"
            )

        # Exchange-Klasse holen und instanziieren
        klass = getattr(ccxt, exchange_id)
        config: Dict[str, Any] = {
            "enableRateLimit": enable_rate_limit,
        }

        # Extra-Config übernehmen
        if extra_config:
            config.update(extra_config)

        self._exchange: ccxt.Exchange = klass(config)

        # Credentials setzen (falls vorhanden)
        if api_key:
            self._exchange.apiKey = api_key
        if secret:
            self._exchange.secret = secret

        # Sandbox-Modus aktivieren (falls unterstützt)
        if sandbox:
            try:
                if hasattr(self._exchange, "set_sandbox_mode"):
                    self._exchange.set_sandbox_mode(True)
            except Exception:
                # Manche Exchanges unterstützen keinen Sandbox-Modus
                pass

        # Credential-Check deaktivieren für read-only Nutzung ohne Keys
        self._exchange.checkRequiredCredentials = False

    @property
    def exchange(self) -> ccxt.Exchange:
        """Zugriff auf das rohe ccxt.Exchange-Objekt (für erweiterte Nutzung)."""
        return self._exchange

    def get_name(self) -> str:
        """
        Name/ID des Exchanges.

        Returns:
            Exchange-ID (z.B. "kraken")
        """
        return self._exchange.id

    def fetch_ticker(self, symbol: str) -> Ticker:
        """
        Aktuellen Ticker für ein Symbol holen.

        Args:
            symbol: Trading-Paar (z.B. "BTC/EUR")

        Returns:
            Ticker-Objekt mit Preisinformationen

        Raises:
            ccxt.BadSymbol: Bei ungültigem Symbol
            ccxt.NetworkError: Bei Netzwerkproblemen
        """
        raw = self._exchange.fetch_ticker(symbol)

        return Ticker(
            symbol=raw.get("symbol", symbol),
            last=float(raw["last"]) if raw.get("last") is not None else None,
            bid=float(raw["bid"]) if raw.get("bid") is not None else None,
            ask=float(raw["ask"]) if raw.get("ask") is not None else None,
            timestamp=raw.get("timestamp"),
            raw=raw,
        )

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        OHLCV-Daten als DataFrame abrufen.

        Args:
            symbol: Trading-Paar (z.B. "BTC/EUR")
            timeframe: Zeitintervall (z.B. "1m", "5m", "1h", "1d")
            since: Startzeit als Unix-Timestamp in ms (optional)
            limit: Max. Anzahl Candles (optional, Exchange-abhängig)

        Returns:
            DataFrame mit Spalten: ['open', 'high', 'low', 'close', 'volume']
            Index: pd.DatetimeIndex (UTC)

        Raises:
            ccxt.BadSymbol: Bei ungültigem Symbol
            ccxt.BadRequest: Bei ungültigem Timeframe
            ccxt.NetworkError: Bei Netzwerkproblemen
        """
        # ccxt.fetch_ohlcv gibt Liste von [timestamp, o, h, l, c, v]
        ohlcv = self._exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )

        if not ohlcv:
            # Leerer DataFrame mit korrekten Spalten
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"],
                index=pd.DatetimeIndex([], name="timestamp", tz="UTC"),
            )

        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )

        # Timestamp von ms zu datetime konvertieren
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp")

        return df

    def fetch_balance(self) -> Balance:
        """
        Account-Balances abrufen (read-only).

        WICHTIG: Erfordert API-Key mit Lese-Rechten!
        Ohne gültige Credentials schlägt dieser Aufruf fehl.

        Returns:
            Balance-Objekt mit free/used/total pro Asset

        Raises:
            ccxt.AuthenticationError: Bei fehlenden/ungültigen Credentials
            ccxt.NetworkError: Bei Netzwerkproblemen
        """
        raw = self._exchange.fetch_balance()

        # free/used/total extrahieren und zu floats konvertieren
        def to_float_dict(d: Optional[Dict]) -> Dict[str, float]:
            if not d:
                return {}
            return {k: float(v) for k, v in d.items() if v is not None}

        return Balance(
            free=to_float_dict(raw.get("free")),
            used=to_float_dict(raw.get("used")),
            total=to_float_dict(raw.get("total")),
            raw=raw,
        )

    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Offene Orders abrufen (nur Lesen, keine Änderung!).

        WICHTIG: Erfordert API-Key mit Lese-Rechten!

        Args:
            symbol: Optional - filtert nach Symbol
                    Wenn None: alle offenen Orders

        Returns:
            Liste von Order-Dicts im ccxt-Format

        Raises:
            ccxt.AuthenticationError: Bei fehlenden Credentials
            ccxt.NetworkError: Bei Netzwerkproblemen
        """
        if symbol:
            return self._exchange.fetch_open_orders(symbol)
        return self._exchange.fetch_open_orders()

    def fetch_markets(self) -> List[Dict[str, Any]]:
        """
        Alle verfügbaren Märkte/Symbole abrufen.

        Nützlich um gültige Symbole zu finden.

        Returns:
            Liste von Market-Dicts mit Symbol, Base, Quote, etc.
        """
        return self._exchange.fetch_markets()

    def get_available_timeframes(self) -> List[str]:
        """
        Liste der unterstützten Timeframes für diesen Exchange.

        Returns:
            Liste von Timeframe-Strings (z.B. ["1m", "5m", "1h", "1d"])
        """
        return list(self._exchange.timeframes.keys()) if self._exchange.timeframes else []

    def __repr__(self) -> str:
        has_key = "with API-Key" if self._exchange.apiKey else "no API-Key"
        return f"<CcxtExchangeClient({self._exchange.id}, {has_key})>"
