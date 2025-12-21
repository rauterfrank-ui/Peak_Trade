# Phase 38: Exchange-Anbindung v0 (Testnet)

**Stand:** Dezember 2024  
**Status:** ✅ Abgeschlossen

---

## 1. Einleitung / Ziel der Phase

Phase 38 implementiert die **erste Version (v0) der Exchange-Anbindung** für Peak_Trade. Der Fokus liegt auf einer **Testnet-orientierten Architektur**, die später für echtes Live-Trading erweitert werden kann.

### Kernziele

1. **`TradingExchangeClient` Protocol** – Abstraktion für Order-fähige Exchange-Clients
2. **`DummyExchangeClient`** – In-Memory-Client für Offline-Tests (deterministisch)
3. **`ExchangeOrderExecutor` erweitert** – Kann jetzt optional einen TradingExchangeClient nutzen
4. **Config-Hook** `[exchange].default_type` – Steuert den verwendeten Client-Typ

### Abgrenzung

- **v0 = Testnet/Dummy-fokussiert** – Kein "scharfes" Live-Trading
- **Echte Exchange-Calls** nur über `KrakenTestnetClient` (validate_only=true)
- **Production-grade Live-Anbindung** kommt in späteren Phasen (40+)

---

## 2. Neue Dateien

| Datei | Beschreibung |
|-------|--------------|
| `src/exchange/dummy_client.py` | In-Memory Exchange-Client für Offline-Tests. Simuliert Orders, Fills, Fees ohne Netzwerk. |
| `tests/test_exchange_trading_client.py` | 33 Tests für `TradingExchangeClient` Protocol und `DummyExchangeClient` |
| `tests/test_config_exchange.py` | 13 Tests für Exchange-Config-Loading und Factory-Funktion |
| `tests/test_exchange_executor_dummy.py` | 16 Tests für `ExchangeOrderExecutor` mit `DummyExchangeClient` |

---

## 3. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `src/exchange/base.py` | + `TradingExchangeClient` Protocol, `ExchangeOrderStatus` Enum, `ExchangeOrderResult` Dataclass |
| `src/exchange/__init__.py` | + Exports für neue Typen, `build_trading_client_from_config()` Factory-Funktion |
| `src/orders/exchange.py` | `ExchangeOrderExecutor` erweitert: `trading_client` Parameter, `from_config()` Factory |
| `src/core/config_pydantic.py` | + `ExchangeConfig`, `ExchangeDummyConfig` Pydantic-Modelle |
| `config/config.toml` | + `[exchange]` Block mit `default_type = "dummy"` |
| `config/config.test.toml` | + `[exchange]` Block mit `default_type = "dummy"` |
| `tests/test_exchange_smoke.py` | Verbesserte Kommentare, Skip-Logik dokumentiert, 3 neue TradingExchangeClient-Tests |

---

## 4. Architektur-Überblick Exchange v0

### 4.1 Schichtenmodell

```
┌─────────────────────────────────────────────────────────────┐
│                      Config Layer                           │
│  [exchange].default_type = "dummy" | "kraken_testnet"       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 build_trading_client_from_config()          │
│            Factory: Erstellt Client basierend auf Config    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  TradingExchangeClient (Protocol)           │
│  ├── get_name() -> str                                      │
│  ├── place_order(...) -> str (Order-ID)                     │
│  ├── cancel_order(id) -> bool                               │
│  └── get_order_status(id) -> ExchangeOrderResult            │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   DummyExchangeClient   │     │   KrakenTestnetClient   │
│   (In-Memory, Offline)  │     │   (API, validate_only)  │
└─────────────────────────┘     └─────────────────────────┘
```

### 4.2 ExchangeOrderExecutor Modi

Der `ExchangeOrderExecutor` unterstützt zwei Modi:

| Modus | Konstruktor | Verhalten |
|-------|-------------|-----------|
| **Dry-Run** | `ExchangeOrderExecutor(safety_guard=...)` | Simulation via `TestnetOrderExecutor` (wie bisher) |
| **Trading-Client** | `ExchangeOrderExecutor(safety_guard=..., trading_client=client)` | Echte Aufrufe via `TradingExchangeClient` |

### 4.3 Status-Mapping

`ExchangeOrderStatus` (Exchange-Layer) wird auf `OrderStatus` (Orders-Layer) gemappt:

| ExchangeOrderStatus | OrderStatus |
|---------------------|-------------|
| FILLED | "filled" |
| PARTIALLY_FILLED | "partially_filled" |
| PENDING / OPEN | "pending" |
| CANCELLED | "cancelled" |
| REJECTED / EXPIRED | "rejected" |
| VALIDATED | "filled" (validate_only) |

---

## 5. Tests & Metriken

### Test-Entwicklung

| Zeitpunkt | Tests passed | Tests skipped |
|-----------|--------------|---------------|
| Vor Phase 38 | 1251 | 4 |
| Nach Schritt 3.1 | 1284 (+33) | 4 |
| Nach Phase 38 | **1316** (+65) | 4 |

### Neue Test-Coverage

- **`TradingExchangeClient` Protocol**: Vollständig abgedeckt
- **`DummyExchangeClient`**: 33 Tests (alle Methoden, Edge-Cases)
- **`ExchangeOrderExecutor`**: 16 Tests (mit Client, Dry-Run, Factory)
- **Config-Loading**: 13 Tests (TOML, Pydantic, Factory)
- **Smoke-Tests**: 3 neue Offline-Tests für TradingExchangeClient

### Geskippte Tests

Die **4 Integration-Tests** in `tests/test_exchange_smoke.py` bleiben bewusst geskippt:

- `test_integration_fetch_ticker`
- `test_integration_fetch_ohlcv`
- `test_integration_fetch_markets`
- `test_integration_from_config`

**Grund:** Diese Tests machen echte HTTP-Requests und erfordern Opt-in via `PEAK_TRADE_EXCHANGE_TESTS=1`.

---

## 6. Verwendung / How-To

### 6.1 Default-Client konfigurieren

In `config/config.toml`:

```toml
[exchange]
default_type = "dummy"  # Optionen: "dummy", "kraken_testnet"

# Einstellungen für DummyExchangeClient
[exchange.dummy]
btc_eur_price = 50000.0
eth_eur_price = 3000.0
fee_bps = 10.0
slippage_bps = 5.0
```

### 6.2 ExchangeOrderExecutor erstellen

**Via Factory (empfohlen):**

```python
from src.core.peak_config import load_config
from src.orders.exchange import ExchangeOrderExecutor

cfg = load_config()
executor = ExchangeOrderExecutor.from_config(cfg)

# Order ausführen
from src.orders.base import OrderRequest

order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01, order_type="market")
result = executor.execute_order(order)

print(f"Status: {result.status}")
print(f"Fill: {result.fill}")
```

**Manuell:**

```python
from src.exchange.dummy_client import DummyExchangeClient
from src.orders.exchange import ExchangeOrderExecutor
from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.live.safety import SafetyGuard

# Client erstellen
client = DummyExchangeClient(simulated_prices={"BTC/EUR": 50000.0})

# Executor erstellen
env_config = EnvironmentConfig(environment=TradingEnvironment.TESTNET)
safety_guard = SafetyGuard(env_config=env_config)
executor = ExchangeOrderExecutor(safety_guard=safety_guard, trading_client=client)
```

### 6.3 Tests ausführen

**Offline-Tests (Standard):**

```bash
# Alle Exchange-bezogenen Tests
pytest tests/test_exchange_*.py -v

# Nur Smoke-Tests
pytest tests/test_exchange_smoke.py -v
```

**Integration-Tests (Opt-in):**

```bash
# Aktivierung via Environment-Variable
export PEAK_TRADE_EXCHANGE_TESTS=1
pytest tests/test_exchange_smoke.py -v

# Oder in einer Zeile
PEAK_TRADE_EXCHANGE_TESTS=1 pytest tests/test_exchange_smoke.py -v
```

⚠️ **Warnung:** Integration-Tests machen echte HTTP-Requests zur Exchange-API!

---

## 7. Abgrenzung & Ausblick

### Was Phase 38 ist

- ✅ Saubere Abstraktion für Order-fähige Exchange-Clients
- ✅ Deterministischer In-Memory-Client für Tests
- ✅ Erweiterter `ExchangeOrderExecutor` mit Client-Support
- ✅ Config-Hook für Client-Typ-Auswahl
- ✅ Umfassende Test-Abdeckung

### Was Phase 38 NICHT ist

- ❌ Production-grade Live-Trading
- ❌ Vollständige Kraken-Live-Integration
- ❌ Automatische Order-Routing-Logik
- ❌ Multi-Exchange-Support

### Geplante Folgeschritte

| Phase | Inhalt |
|-------|--------|
| Phase 39+ | `KrakenTestnetClient` vollständig an `TradingExchangeClient` anbinden |
| Phase 40+ | `KrakenLiveClient` mit echten Orders (mit allen Safety-Guards) |
| Phase 41+ | Integration in Live-/Testnet-Orchestrierung |
| Später | Multi-Exchange-Support (Binance, etc.) |

---

## 8. Referenzen

### Relevante Dokumentation

- `docs/PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md` – Kraken Testnet Client
- `docs/PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md` – Testnet-Orchestrierung
- `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md` – Safety-Layer

### Code-Referenzen

- `src/exchange/base.py` – TradingExchangeClient Protocol
- `src/exchange/dummy_client.py` – DummyExchangeClient
- `src/orders/exchange.py` – ExchangeOrderExecutor
- `tests/test_exchange_*.py` – Exchange-Tests

---

*Phase 38 abgeschlossen – Exchange v0 ist bereit für Testnet-Integration.*
