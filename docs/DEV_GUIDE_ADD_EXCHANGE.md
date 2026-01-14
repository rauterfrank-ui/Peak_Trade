# Developer Guide: Neuen Exchange-Adapter hinzufügen

## Ziel

Neuen Exchange/Market-Adapter hinzufügen, der Data-Layer und ggf. Live-Layer nutzt.

---

## Relevante Komponenten

- **Data-Layer**: `src/data/*` – Market-Data-Adapter
- **Exchange-/Order-Layer**: `src/orders/exchange.py` – Order-Execution
- **Live-Environment**: `src/core/environment.py`, `src/live/safety.py` – Safety-Layer
- **Config**: `config/config.toml` – Exchange-Settings

---

## Schritte (High-Level)

### 1. Market Data Adapter

**Neue Datei erstellen**, z.B.:
- `src&#47;data&#47;my_exchange.py` (illustrative)

**Schnittstelle an vorhandene Adapter angleichen** (z.B. `src/data/kraken.py`):

```python
"""
My Exchange Data Module
======================
OHLCV-Datenbeschaffung von My Exchange mit Parquet-Caching.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import logging

from ..core.config_registry import get_config

logger = logging.getLogger(__name__)


def get_my_exchange_client():
    """
    Erstellt My Exchange-Client.

    Returns:
        Konfigurierter Exchange-Client
    """
    # Exchange-spezifische Client-Initialisierung
    # z.B. ccxt.my_exchange() oder eigene API-Client
    pass


def fetch_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    since: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Holt OHLCV-Daten von My Exchange.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        timeframe: Timeframe (z.B. "1h", "4h", "1d")
        since: Optional Start-Zeitpunkt
        limit: Optional maximale Anzahl Bars

    Returns:
        DataFrame mit OHLCV-Daten (UTC-DatetimeIndex)
    """
    # Exchange-spezifische Implementierung
    # Wichtig: DatetimeIndex muss UTC sein
    pass


def load_ohlcv_cached(
    symbol: str,
    timeframe: str = "1h",
    since: Optional[datetime] = None,
    limit: Optional[int] = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Lädt OHLCV-Daten mit Caching.

    Args:
        symbol: Trading-Pair
        timeframe: Timeframe
        since: Optional Start-Zeitpunkt
        limit: Optional maximale Anzahl Bars
        use_cache: Ob Cache verwendet werden soll

    Returns:
        DataFrame mit OHLCV-Daten
    """
    # Cache-Logik (ähnlich wie in kraken.py)
    pass
```

**Integration in Data-Loader:**

Öffne `src/data/loader.py` und füge eine Factory-Funktion hinzu:

```python
def load_data_from_exchange(
    exchange: str,
    symbol: str,
    timeframe: str = "1h",
    **kwargs
) -> pd.DataFrame:
    """
    Lädt Daten von einem Exchange.

    Args:
        exchange: Exchange-Name ("kraken", "my_exchange", etc.)
        symbol: Trading-Pair
        timeframe: Timeframe
        **kwargs: Weitere Parameter

    Returns:
        DataFrame mit OHLCV-Daten
    """
    if exchange == "kraken":
        from .kraken import load_ohlcv_cached
        return load_ohlcv_cached(symbol, timeframe, **kwargs)
    elif exchange == "my_exchange":
        from .my_exchange import load_ohlcv_cached
        return load_ohlcv_cached(symbol, timeframe, **kwargs)
    else:
        raise ValueError(f"Unbekannter Exchange: {exchange}")
```

---

### 2. Order-/Exchange-Layer (falls Live-Testnet relevant)

**Anpassung in `src/orders/exchange.py`:**

Falls der Exchange für Live-Trading verwendet werden soll, füge eine neue `ExchangeClient`-Implementierung hinzu:

```python
class MyExchangeClient(BaseExchangeClient):
    """
    My Exchange-Client für Order-Execution.
    """
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = True):
        """
        Initialisiert My Exchange-Client.

        Args:
            api_key: API-Key
            api_secret: API-Secret
            sandbox: Ob Sandbox-Modus verwendet werden soll
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        # Exchange-spezifische Client-Initialisierung

    def place_order(self, order: OrderRequest) -> OrderExecutionResult:
        """
        Platziert eine Order auf My Exchange.

        Args:
            order: OrderRequest

        Returns:
            OrderExecutionResult
        """
        # Exchange-spezifische Implementierung
        pass
```

**Config-Erweiterung:**

Füge Exchange-Settings in `config/config.toml` hinzu:

```toml
[live.exchange]
type = "my_exchange"  # oder "kraken", etc.
sandbox = true  # Testnet-Modus

[live.exchange.my_exchange]
api_key = "${MY_EXCHANGE_API_KEY}"  # Aus Umgebungsvariable
api_secret = "${MY_EXCHANGE_API_SECRET}"  # Aus Umgebungsvariable
base_url = "https://api.myexchange.com"  # Optional
```

**Wichtig:** API-Keys sollten **nicht** in `config.toml` im Klartext stehen, sondern aus Umgebungsvariablen geladen werden.

---

### 3. Environment-/Safety-Anpassung

**Environment-Konfiguration:**

Prüfe `src/core/environment.py` und stelle sicher, dass der neue Exchange in der Environment-Konfiguration unterstützt wird.

**Safety-Layer:**

Stelle sicher, dass der Safety-Layer (`src/live/safety.py`) den neuen Exchange unterstützt:
- Testnet-Modus sollte verfügbar sein (oder klar dokumentiert, wenn nicht)
- Live-Modus sollte nur mit expliziter Freigabe funktionieren

**Siehe auch:** `docs/LIVE_TESTNET_PREPARATION.md`

---

### 4. Tests

**Unit-Tests für Data-Funktionen:**

Erstelle `tests/test_data_my_exchange.py`:

```python
"""
Tests für My Exchange Data-Adapter
"""
from __future__ import annotations

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.data.my_exchange import fetch_ohlcv, load_ohlcv_cached


@patch("src.data.my_exchange.get_my_exchange_client")
def test_fetch_ohlcv_returns_dataframe(mock_client):
    """Testet dass fetch_ohlcv ein DataFrame zurückgibt."""
    # Mock Exchange-Client
    mock_client.return_value.fetch_ohlcv.return_value = [
        [1609459200000, 100.0, 105.0, 95.0, 102.0, 1000.0],  # [timestamp, open, high, low, close, volume]
    ]

    df = fetch_ohlcv("BTC/EUR", "1h")

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "close" in df.columns
    assert df.index.tz == pd.Timestamp.now(tz="UTC").tz  # UTC-Index
```

**Unit-Tests für Exchange-Client:**

Erstelle `tests/test_orders_my_exchange.py`:

```python
"""
Tests für My Exchange Order-Client
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from src.orders.exchange import MyExchangeClient
from src.orders.base import OrderRequest, OrderSide


@patch("src.orders.my_exchange.MyExchangeAPI")
def test_place_order_success(mock_api):
    """Testet erfolgreiche Order-Platzierung."""
    client = MyExchangeClient(api_key="test", api_secret="test", sandbox=True)

    order = OrderRequest(
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=0.1,
    )

    # Mock API-Response
    mock_api.return_value.place_order.return_value = {
        "order_id": "12345",
        "status": "filled",
    }

    result = client.place_order(order)

    assert result.status == "filled"
    assert result.order_id == "12345"
```

**Wichtig:** Keine echten API-Keys im Repo! Verwende Mocks/Stubs für Tests.

---

### 5. Dokumentation

**Kurze Erwähnung in `ARCHITECTURE_OVERVIEW.md`:**

Füge den neuen Exchange in der Data-/Exchange-Sektion hinzu.

**Optional: Neues Doku-File:**

Erstelle `docs/EXCHANGE_MY_EXCHANGE.md` (optional, nur wenn umfangreich):

```markdown
# My Exchange Integration

## Übersicht

Kurze Beschreibung der My Exchange-Integration.

## Konfiguration

[Config-Beispiele]

## API-Limits

[Rate-Limits, etc.]

## Troubleshooting

[Häufige Probleme]
```

---

## Safety Hinweise

### ✅ DO

- **Sandbox/Testnet vs. Live**: Immer klar zwischen Sandbox/Testnet und Live unterscheiden
- **API-Keys über Env**: API-Keys aus Umgebungsvariablen, nicht in config/plain-text
- **Rate-Limiting**: Exchange-spezifische Rate-Limits beachten
- **Error-Handling**: Robuste Fehlerbehandlung für API-Calls

### ❌ DON'T

- **Keine Hardcoded-Keys**: Keine API-Keys im Code
- **Keine Live-Orders in Tests**: Tests sollten nur Sandbox/Testnet verwenden
- **Keine ungetesteten API-Calls**: Alle API-Calls sollten getestet sein (mit Mocks)

---

## Beispiel-Integrationen als Referenz

- **Data-Layer**: `src/data/kraken.py` – Kraken-Data-Adapter
- **Order-Layer**: `src/orders/exchange.py` – Exchange-Order-Execution

---

## Troubleshooting

**Problem:** Daten werden nicht geladen
- **Lösung:** Prüfe API-Credentials, Rate-Limits, Symbol-Format

**Problem:** Orders werden nicht ausgeführt
- **Lösung:** Prüfe Sandbox/Live-Modus, API-Permissions, Order-Format

**Problem:** Timezone-Probleme
- **Lösung:** Stelle sicher, dass alle Timestamps UTC sind

---

## Siehe auch

- `ARCHITECTURE_OVERVIEW.md` – Architektur-Übersicht
- `src/data/kraken.py` – Kraken-Data-Adapter als Referenz
- `src/orders/exchange.py` – Exchange-Order-Execution
- `docs/LIVE_TESTNET_PREPARATION.md` – Live-/Testnet-Vorbereitung
