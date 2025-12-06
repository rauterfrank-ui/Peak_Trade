# Phase 31: End-to-End Shadow/Paper Flow mit echten Exchange-Marktdaten

## Übersicht

Phase 31 implementiert einen **kontinuierlichen Shadow-/Paper-Trading-Loop** mit echten Exchange-Marktdaten (Kraken Public API), jedoch **ohne echte Order-Execution**.

### Zielsetzung

- **Live-Marktdaten** von Kraken (oder anderer Exchange) in Echtzeit holen
- **Strategie-Signale** auf Live-Daten generieren
- **Paper-Order-Execution** über simulierten Executor
- **Risk-Limit-Prüfung** vor jeder Order
- **Umfangreiches Logging** und Metriken

### Wichtige Leitplanken

> **KEIN echter Live-Handel in dieser Phase!**

- Orders werden **nur über Paper-/Shadow-Executor simuliert**
- **Keine echten Order-Requests** an Exchange-REST-/WebSocket-APIs
- Nur **public market data** (keine API-Keys für Order-Endpoints)

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ShadowPaperSession                          │
│                                                                     │
│  ┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │ KrakenLiveCandle │───►│   Strategy   │───►│ExecutionPipeline│   │
│  │     Source       │    │              │    │                 │   │
│  └─────────────────┘    └──────────────┘    └────────┬────────┘   │
│          │                                            │            │
│          │ poll()                                     │            │
│          ▼                                            ▼            │
│  ┌─────────────────┐                         ┌───────────────┐    │
│  │  Kraken Public  │                         │LiveRiskLimits │    │
│  │      API        │                         │    check()    │    │
│  └─────────────────┘                         └───────┬───────┘    │
│                                                      │            │
│                                              ┌───────▼───────┐    │
│                                              │ShadowOrder    │    │
│                                              │   Executor    │    │
│                                              │  (no real     │    │
│                                              │   orders)     │    │
│                                              └───────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### Komponenten

| Komponente | Datei | Beschreibung |
|------------|-------|--------------|
| `KrakenLiveCandleSource` | `src/data/kraken_live.py` | Pollt OHLC-Daten von Kraken Public API |
| `ShadowPaperSession` | `src/live/shadow_session.py` | Orchestriert den Trading-Loop |
| `ExecutionPipeline` | `src/execution/pipeline.py` | Transformiert Signale zu Orders |
| `ShadowOrderExecutor` | `src/orders/shadow.py` | Simuliert Order-Ausführung |
| `LiveRiskLimits` | `src/live/risk_limits.py` | Prüft Orders gegen Limits |
| `EnvironmentConfig` | `src/core/environment.py` | Safety-Layer für Environment |

---

## Konfiguration

### config/config.toml

```toml
# ============================================================================
# PHASE 31: SHADOW/PAPER LIVE-SESSION CONFIGURATION
# ============================================================================

[shadow_paper]
enabled = true
mode = "paper"                    # "shadow" oder "paper"
symbol = "BTC/EUR"
timeframe = "1m"
poll_interval_seconds = 60.0
warmup_candles = 200
start_balance = 10000.0
position_fraction = 0.1           # 10% pro Trade
fee_rate = 0.0026                 # 26 bps
slippage_bps = 5.0

[live_exchange]
name = "kraken"
use_sandbox = true                # MUSS true sein
base_url = "https://api.kraken.com"
rate_limit_ms = 1000
max_retries = 3
retry_delay_seconds = 5.0

[live_risk]
enabled = true
base_currency = "EUR"
max_order_notional = 1000.0
max_symbol_exposure_notional = 2000.0
max_total_exposure_notional = 5000.0
max_open_positions = 5
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
block_on_violation = true

[environment]
mode = "paper"                    # NUR "paper" für Phase 31!
enable_live_trading = false
require_confirm_token = true
testnet_dry_run = true
log_all_orders = true
```

### Konfigurationsparameter

#### [shadow_paper]

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `enabled` | bool | true | Session aktivieren |
| `mode` | str | "paper" | "shadow" oder "paper" |
| `symbol` | str | "BTC/EUR" | Trading-Symbol |
| `timeframe` | str | "1m" | Candle-Intervall |
| `poll_interval_seconds` | float | 60.0 | Polling-Frequenz |
| `warmup_candles` | int | 200 | Initiale Candles für Indikatoren |
| `start_balance` | float | 10000.0 | Simuliertes Startkapital |
| `position_fraction` | float | 0.1 | Positionsgröße als Anteil |
| `fee_rate` | float | 0.0026 | Simulierte Fee-Rate |
| `slippage_bps` | float | 5.0 | Simulierte Slippage (bps) |

#### [live_exchange]

| Parameter | Typ | Default | Beschreibung |
|-----------|-----|---------|--------------|
| `name` | str | "kraken" | Exchange-Name |
| `use_sandbox` | bool | true | **MUSS true sein!** |
| `base_url` | str | "https://api.kraken.com" | API Base URL |
| `rate_limit_ms` | int | 1000 | Rate-Limit (ms) |
| `max_retries` | int | 3 | Retry-Versuche |
| `retry_delay_seconds` | float | 5.0 | Retry-Wartezeit |

---

## CLI-Nutzung

### Basis-Aufruf

```bash
# Standard-Start mit MA-Crossover
python -m scripts.run_shadow_paper_session

# Mit Config-Datei
python -m scripts.run_shadow_paper_session --config config/config.toml
```

### Parameter

```bash
# Mit anderer Strategie
python -m scripts.run_shadow_paper_session --strategy rsi_strategy

# Mit anderem Symbol
python -m scripts.run_shadow_paper_session --symbol ETH/EUR

# Mit anderem Timeframe
python -m scripts.run_shadow_paper_session --timeframe 5m

# Begrenzte Laufzeit (30 Minuten)
python -m scripts.run_shadow_paper_session --duration 30

# Nur Config validieren
python -m scripts.run_shadow_paper_session --dry-run

# Debug-Logging
python -m scripts.run_shadow_paper_session --log-level DEBUG
```

### Verfügbare Strategien

- `ma_crossover` - Moving Average Crossover (Default)
- `momentum_1h` - Momentum Strategie
- `rsi_strategy` - RSI Mean-Reversion
- `macd` - MACD Trend-Following

### Beenden

- **Ctrl+C** (SIGINT) - Graceful Shutdown
- **SIGTERM** - Graceful Shutdown

---

## Programmatische Nutzung

### Einfaches Beispiel

```python
from src.core.peak_config import load_config
from src.live.shadow_session import create_shadow_paper_session
from src.strategies.ma_crossover import MACrossoverStrategy

# Config laden
cfg = load_config("config/config.toml")

# Strategie erstellen
strategy = MACrossoverStrategy.from_config(cfg, "strategy.ma_crossover")

# Session erstellen
session = create_shadow_paper_session(cfg=cfg, strategy=strategy)

# Warmup und Start
session.warmup()
session.run_forever()  # Ctrl+C zum Stoppen
```

### Mit Fake-Datenquelle (für Tests)

```python
from src.data.kraken_live import FakeCandleSource, LiveCandle
from datetime import datetime, timezone

# Test-Candles erstellen
candles = [
    LiveCandle(timestamp=datetime.now(timezone.utc), open=50000, high=50100, low=49900, close=50050, volume=10),
    # ... mehr Candles
]

# Fake-Source verwenden
fake_source = FakeCandleSource(candles=candles)

session = ShadowPaperSession(
    env_config=env_config,
    shadow_cfg=shadow_cfg,
    exchange_cfg=exchange_cfg,
    data_source=fake_source,  # Fake statt Kraken
    strategy=strategy,
    pipeline=pipeline,
    risk_limits=risk_limits,
)
```

### N Schritte ausführen

```python
session.warmup()

# 100 Schritte ohne Wartezeit
results = session.run_n_steps(100, sleep_between=False)

print(f"Orders: {len(results)}")
print(f"Metriken: {session.metrics.to_dict()}")
```

### Zeitlich begrenzt

```python
session.warmup()

# 30 Minuten laufen lassen
results = session.run_for_duration(30)  # Minuten
```

---

## Safety-Features

### Environment-Beschränkung

Die Session akzeptiert **nur** folgende Environment-Modi:
- `TradingEnvironment.PAPER`

Bei anderen Modi (z.B. `LIVE`) wird eine `EnvironmentNotAllowedError` geworfen.

```python
# In config.toml
[environment]
mode = "paper"  # Einziger erlaubter Modus!
enable_live_trading = false
```

### Risk-Limit-Prüfung

Vor jeder Order wird `LiveRiskLimits.check_orders()` aufgerufen:

```python
risk_result = self._risk_limits.check_orders(live_orders)

if not risk_result.allowed:
    # Order blockiert!
    logger.warning(f"Orders blockiert: {risk_result.reasons}")
    self._metrics.blocked_orders_count += len(orders)
```

### Kein echter API-Zugriff für Orders

- `KrakenLiveCandleSource` nutzt **nur** `/0/public/OHLC`
- **Keine** Order-Endpoints (`/0/private/*`)
- **Keine** API-Keys erforderlich
- `ShadowOrderExecutor` sendet **keine** Netzwerk-Requests

---

## Datenfluss

### 1. Warmup

```
KrakenLiveCandleSource.warmup()
    │
    ├─► GET /0/public/OHLC?pair=XXBTZEUR&interval=1
    │
    ├─► Parse OHLC Response
    │
    └─► Buffer füllen (N warmup_candles)
```

### 2. Polling Loop

```
while running:
    │
    ├─► KrakenLiveCandleSource.poll_latest()
    │       │
    │       └─► GET /0/public/OHLC (neue Candles)
    │
    ├─► Strategy.generate_signals(buffer)
    │       │
    │       └─► Signal: 0, +1, oder -1
    │
    ├─► Bei Signal-Änderung:
    │       │
    │       ├─► ExecutionPipeline.signal_to_orders()
    │       │
    │       ├─► LiveRiskLimits.check_orders()
    │       │       │
    │       │       └─► allowed: true/false
    │       │
    │       └─► ShadowOrderExecutor.execute_orders()
    │               │
    │               └─► Simuliertes OrderExecutionResult
    │
    └─► time.sleep(poll_interval)
```

---

## Tests

### Test-Datei

`tests/test_live_shadow_session.py`

### Tests ausführen

```bash
# Alle Phase-31-Tests
pytest tests/test_live_shadow_session.py -v

# Einzelnen Test
pytest tests/test_live_shadow_session.py::TestShadowPaperSession::test_session_accepts_paper_environment -v

# Mit Coverage
pytest tests/test_live_shadow_session.py --cov=src/live --cov=src/data
```

### Test-Kategorien

| Kategorie | Beschreibung |
|-----------|--------------|
| `TestConfigLoading` | Config-Loading-Funktionen |
| `TestFakeCandleSource` | Fake-Datenquelle für Tests |
| `TestLiveCandle` | LiveCandle-Datenstruktur |
| `TestShadowPaperSession` | Session-Klasse |
| `TestRiskLimitIntegration` | Risk-Limit-Integration |
| `TestSessionMetrics` | Metriken-Tracking |
| `TestSignalToOrderFlow` | Signal→Order-Flow |
| `TestCallbacks` | Callback-Funktionalität |
| `TestEdgeCases` | Edge Cases |

---

## Integration mit bestehenden Komponenten

### Backtest → Shadow/Paper

Der Shadow/Paper-Flow nutzt dieselbe `ExecutionPipeline` wie Backtests:

```python
# Backtest:
pipeline = ExecutionPipeline.for_paper(market_context)

# Shadow/Paper:
pipeline = ExecutionPipeline.for_shadow(market_context)
```

### Reporting (Phase 30)

Session-Metriken können für Reports verwendet werden:

```python
summary = session.get_execution_summary()
# {
#     "session_metrics": {...},
#     "pipeline_summary": {...},
#     "config": {...}
# }
```

### Experiments Registry

Orders werden via `ShadowOrderExecutor` mit `mode="shadow_run"` markiert:

```python
result.metadata = {
    "mode": "shadow_run",
    "shadow": True,
    "note": "SHADOW-EXECUTION - keine echte Order gesendet"
}
```

---

## Troubleshooting

### "Environment nicht erlaubt"

```
EnvironmentNotAllowedError: Environment-Modus 'live' ist nicht erlaubt
```

**Lösung:** Setze `mode = "paper"` in `[environment]` Block.

### "Warmup fehlgeschlagen"

```
RuntimeError: Warmup fehlgeschlagen: Kraken API nicht erreichbar
```

**Lösung:**
- Internet-Verbindung prüfen
- `base_url` in Config prüfen
- `max_retries` erhöhen

### "Keine neuen Candles"

```
DEBUG: Keine neue Candle
```

**Normal** - Candles werden nur bei neuen Daten geliefert. Bei 1m-Timeframe
und 60s Poll-Interval etwa 1 neue Candle pro Minute.

### "Orders blockiert durch Risk-Limits"

```
WARNING: Orders blockiert durch Risk-Limits: ['max_order_notional_exceeded(...)']
```

**Lösung:** Limits in `[live_risk]` erhöhen oder `enabled = false` setzen.

---

## Nächste Schritte (zukünftige Phasen)

1. **Phase 32:** Testnet-Integration (echte Testnet-Orders)
2. **Phase 33:** Live-Vorbereitung (API-Key-Management)
3. **Phase 34:** Live-Trading (mit expliziter Aktivierung)

---

## Referenzen

- [Kraken Public API Docs](https://docs.kraken.com/rest/#tag/Spot-Market-Data)
- `src/core/environment.py` - Environment-Abstraktion
- `src/live/safety.py` - Safety-Layer
- `src/live/risk_limits.py` - Risk-Limit-System
- `docs/PHASE_24_SHADOW_EXECUTION.md` - Shadow-Execution-Konzept
