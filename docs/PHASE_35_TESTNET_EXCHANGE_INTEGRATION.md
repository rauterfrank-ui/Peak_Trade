# Phase 35: Testnet-/Exchange-Integration v1

## Übersicht

Phase 35 implementiert die erste **Testnet-/Demo-Exchange-Integration** für Peak_Trade.
Auf Basis des bestehenden Live-/Shadow-Stacks (Phasen 31–34) wird eine sichere
Integration mit Exchange-APIs eingeführt – strikt **ohne echten Live-Handel**.

### Kernziele

1. **Exchange-Client für Testnet/Demo**: `KrakenTestnetClient`
   - Orders über die Testnet-API senden (validate_only-Modus)
   - Order-Status und Fills abfragen
   - Symbol-Mapping (BTC/EUR → XXBTZEUR)

2. **Sicherer Order-Executor**: `TestnetExchangeOrderExecutor`
   - Strenge Environment-Prüfung (nur `testnet` erlaubt)
   - Integration mit `LiveRiskLimits`
   - Safety-Guards aus dem bestehenden Stack

3. **Testnet-Session-CLI**: `run_testnet_session.py`
   - Analog zu `run_shadow_paper_session.py`
   - Echte API-Calls (im Demo-Modus)
   - Integration mit Monitoring & Alerts

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Testnet Session CLI                       │
│                  scripts/run_testnet_session.py              │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │    TestnetSession       │
         │  (Session-Orchestrator) │
         └────────────┬────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌──────────────┐   ┌─────────────┐
│Strategy │    │TestnetExchange│   │LiveRiskLimits│
│         │    │OrderExecutor  │   │             │
└─────────┘    └──────┬───────┘   └─────────────┘
                      │
         ┌────────────▼────────────┐
         │   KrakenTestnetClient   │
         │  (Exchange-API-Client)  │
         └────────────┬────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Kraken API   │
              │(validate_only)│
              └───────────────┘
```

---

## Neue Dateien

### Exchange-Client

```
src/exchange/kraken_testnet.py
├── KrakenTestnetConfig       # Konfiguration
├── KrakenTestnetClient       # API-Client
├── KrakenOrderResponse       # Response-Dataclass
├── KrakenOrderStatus         # Status-Dataclass
└── ExchangeAPIError (etc.)   # Exceptions
```

### Order-Executor

```
src/orders/testnet_executor.py
├── TestnetExchangeOrderExecutor    # Executor mit Safety & Risk
├── TestnetExecutionLog             # Log-Eintrag
├── EnvironmentNotTestnetError      # Exception
└── create_testnet_executor_from_config()  # Factory
```

### CLI-Script

```
scripts/run_testnet_session.py
├── TestnetSession           # Session-Orchestrator
├── TestnetSessionConfig     # Session-Konfiguration
├── TestnetSessionMetrics    # Metriken
└── build_testnet_session()  # Builder-Funktion
```

### Tests

```
tests/
├── test_exchange_client.py           # Client-Tests
├── test_exchange_order_executor.py   # Executor-Tests
└── test_run_testnet_session.py       # Session-Smoke-Tests
```

---

## Konfiguration

### config/config.toml

```toml
# ============================================================================
# PHASE 35: TESTNET EXCHANGE INTEGRATION
# ============================================================================

[exchange.kraken_testnet]
# Testnet-Integration aktivieren
enabled = true

# Kraken API Base-URL
base_url = "https://api.kraken.com"

# Environment-Variable für den API-Key (NICHT der Key selbst!)
api_key_env_var = "KRAKEN_TESTNET_API_KEY"

# Environment-Variable für das API-Secret (NICHT das Secret selbst!)
api_secret_env_var = "KRAKEN_TESTNET_API_SECRET"

# WICHTIG: validate_only=true bedeutet:
# - Orders werden an die API geschickt und validiert
# - Orders werden NICHT tatsächlich ausgeführt
validate_only = true

# HTTP-Request Timeout in Sekunden
timeout_seconds = 30.0

# Max. Retries bei Netzwerkfehlern
max_retries = 3

# Rate-Limit: Mindestabstand zwischen Requests in Millisekunden
rate_limit_ms = 1000

# ============================================================================
# TESTNET SESSION CONFIGURATION
# ============================================================================

[testnet_session]
enabled = true
default_exchange = "kraken_testnet"
symbol = "BTC/EUR"
timeframe = "1m"
poll_interval_seconds = 60.0
warmup_candles = 200
start_balance = 10000.0
position_fraction = 0.1
fee_rate = 0.0026
slippage_bps = 5.0
```

### Environment-Variablen

```bash
# API-Credentials (NIEMALS im Code oder config.toml!)
export KRAKEN_TESTNET_API_KEY="your_api_key"
export KRAKEN_TESTNET_API_SECRET="your_api_secret"
```

---

## Safety & Security

### 1. Environment-Guard

Der `TestnetExchangeOrderExecutor` prüft **strikt**, dass:

```python
# Nur TradingEnvironment.TESTNET ist erlaubt
if env_config.environment != TradingEnvironment.TESTNET:
    raise EnvironmentNotTestnetError(...)
```

- **PAPER-Modus**: Nicht erlaubt → Exception
- **LIVE-Modus**: Nicht erlaubt → Exception
- **TESTNET-Modus**: Erlaubt

### 2. validate_only-Modus

Default ist `validate_only=true`:

- Orders werden an Kraken gesendet und **validiert**
- Orders werden **NICHT ausgefuehrt** (keine echten Trades)
- Response enthält Order-Beschreibung, aber keine Transaction-ID
- Ideal für Tests ohne Kapitalrisiko

### 3. Risk-Limits

`LiveRiskLimits` werden **VOR** jedem API-Call geprüft:

```python
risk_result = self._risk_limits.check_orders(orders)
if not risk_result.allowed:
    # Order wird NICHT gesendet
    return OrderExecutionResult(status="rejected", ...)
```

### 4. API-Key-Handling

- Keys werden **NUR** aus Environment-Variablen gelesen
- **NIEMALS** Keys im Code oder Config-Dateien speichern
- Config enthält nur den **Namen** der ENV-Variable

---

## Verwendung

### 1. Environment-Variablen setzen

```bash
export KRAKEN_TESTNET_API_KEY="your_api_key"
export KRAKEN_TESTNET_API_SECRET="your_api_secret"
```

### 2. Config anpassen

Stelle sicher, dass `config/config.toml` enthält:

```toml
[environment]
mode = "testnet"
testnet_dry_run = false  # Für echte Testnet-Orders, true für validate_only
```

### 3. Testnet-Session starten

```bash
# Standard-Start mit MA-Crossover
python3 -m scripts.run_testnet_session

# Mit anderer Strategie
python3 -m scripts.run_testnet_session --strategy rsi_strategy

# Mit anderem Symbol
python3 -m scripts.run_testnet_session --symbol ETH/EUR

# Für begrenzte Dauer (30 Minuten)
python3 -m scripts.run_testnet_session --duration 30

# Nur Config validieren (Dry-Run)
python3 -m scripts.run_testnet_session --dry-run
```

### 4. Monitoring (optional)

```bash
# Letzte Run beobachten
python3 -m scripts.monitor_live_run --latest

# Alerts anzeigen
python3 -m scripts.monitor_live_run --latest --alerts
```

---

## Beispiel-Workflow

```bash
# 1. Terminal 1: Testnet-Session starten
export KRAKEN_TESTNET_API_KEY="..."
export KRAKEN_TESTNET_API_SECRET="..."
python3 -m scripts.run_testnet_session \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --duration 60

# 2. Terminal 2: Session beobachten
python3 -m scripts.monitor_live_run --latest --tail

# 3. Terminal 3: Web-Dashboard (optional)
python3 -m scripts.serve_live_dashboard
# → http://localhost:8000
```

---

## Tests

### Alle Phase-35-Tests ausführen

```bash
# Nur Phase-35-Tests
python3 -m pytest tests/test_exchange_client.py tests/test_exchange_order_executor.py tests/test_run_testnet_session.py -v

# Vollständige Test-Suite
python3 -m pytest -q
```

### Test-Abdeckung

| Test-Datei | Beschreibung |
|------------|-------------|
| `test_exchange_client.py` | KrakenTestnetClient mit Mock-API |
| `test_exchange_order_executor.py` | Executor mit Environment-Guards |
| `test_run_testnet_session.py` | Session-Smoke-Tests |

---

## Nicht-Ziele (Phase 35)

- ❌ Echtes Live-Trading (erst ab Phase 40+)
- ❌ Websocket-Orderbook-Streaming
- ❌ Komplexe Order-Typen (nur Market/Limit)
- ❌ Multi-Exchange-Support (nur Kraken in Phase 35)

---

## Erweiterbarkeit

Die Architektur ist so gestaltet, dass später:

1. **Echtes Live-Trading** durch Änderung von:
   - `validate_only=false` in der Config
   - Neuer `LiveExchangeOrderExecutor` (Phase 40+)

2. **Weitere Exchanges** durch:
   - Neue Client-Klassen (z.B. `BinanceTestnetClient`)
   - Gemeinsames Protocol/Interface für Clients

3. **Erweiterte Order-Typen** durch:
   - Erweiterung von `OrderRequest`
   - Anpassung der Symbol-Mappings

---

## Dateien-Übersicht

```
Peak_Trade/
├── config/
│   └── config.toml               # [exchange.kraken_testnet], [testnet_session]
├── src/
│   ├── exchange/
│   │   └── kraken_testnet.py     # KrakenTestnetClient
│   └── orders/
│       └── testnet_executor.py   # TestnetExchangeOrderExecutor
├── scripts/
│   └── run_testnet_session.py    # Testnet-Session-CLI
├── tests/
│   ├── test_exchange_client.py
│   ├── test_exchange_order_executor.py
│   └── test_run_testnet_session.py
└── docs/
    └── PHASE_35_TESTNET_EXCHANGE_INTEGRATION.md  # Diese Dokumentation
```

---

## Changelog

### v1.0.0 (Phase 35)

- Initial release
- KrakenTestnetClient mit validate_only-Modus
- TestnetExchangeOrderExecutor mit Safety & Risk
- Testnet-Session-CLI
- Vollständige Test-Suite
