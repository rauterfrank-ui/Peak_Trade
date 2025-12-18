# Circuit Breaker Pattern

## Überblick

Der Circuit Breaker schützt Peak_Trade vor kaskadierenden Fehlern bei externen Abhängigkeiten (Exchange-APIs, Datenquellen). Basiert auf dem klassischen Circuit-Breaker-Pattern mit drei Zuständen.

## Drei Zustände

```
CLOSED (Normal)
    ↓ (Fehler-Threshold erreicht)
OPEN (Blockiert)
    ↓ (Timeout abgelaufen)
HALF_OPEN (Test)
    ↓ (Erfolg)
CLOSED
    ↓ (Fehler)
OPEN
```

### CLOSED (Grün)
- Alle Anfragen werden durchgelassen
- Fehler werden gezählt
- Bei Threshold-Überschreitung → OPEN

### OPEN (Rot)
- Alle Anfragen werden blockiert
- Nach Timeout → HALF_OPEN
- Schützt System vor Überlastung

### HALF_OPEN (Gelb)
- Limitierte Test-Anfragen erlaubt
- Bei Erfolg → CLOSED
- Bei Fehler → OPEN

## Verwendung

### Als Decorator

```python
from src.infra.resilience import circuit_breaker

@circuit_breaker(
    name="kraken_api",
    failure_threshold=5,
    timeout_seconds=60,
)
async def fetch_kraken_data():
    # API call
    response = await kraken_client.fetch_ohlcv("BTC/USD")
    return response
```

### Direkt

```python
from src.infra.resilience import CircuitBreaker, CircuitBreakerConfig

config = CircuitBreakerConfig(
    name="kraken_api",
    failure_threshold=5,
    timeout_seconds=60,
    half_open_max_calls=3,
)
cb = CircuitBreaker(config)

async def fetch_data():
    result = await cb.call(some_api_function, arg1, arg2)
    return result
```

### Global Registry

```python
from src.infra.resilience import get_circuit_breaker, CircuitBreakerConfig

# Hole oder erstelle Circuit Breaker
cb = get_circuit_breaker(
    "kraken_api",
    CircuitBreakerConfig(name="kraken_api", failure_threshold=5)
)

# Verwende überall im Code
result = await cb.call(fetch_data)
```

## Exchange-Spezifische Konfiguration

### Kraken

```python
@circuit_breaker(
    name="kraken_api",
    failure_threshold=5,
    timeout_seconds=60,
)
async def fetch_kraken_ohlcv(symbol: str):
    import ccxt
    exchange = ccxt.kraken()
    return await exchange.fetch_ohlcv(symbol)
```

### Binance

```python
@circuit_breaker(
    name="binance_api",
    failure_threshold=5,
    timeout_seconds=60,
)
async def fetch_binance_ticker(symbol: str):
    import ccxt
    exchange = ccxt.binance()
    return await exchange.fetch_ticker(symbol)
```

### Coinbase Pro

```python
@circuit_breaker(
    name="coinbasepro_api",
    failure_threshold=5,
    timeout_seconds=60,
)
async def fetch_coinbase_trades(symbol: str):
    import ccxt
    exchange = ccxt.coinbasepro()
    return await exchange.fetch_trades(symbol)
```

## Metriken & Monitoring

```python
from src.infra.resilience import get_circuit_breaker

cb = get_circuit_breaker("kraken_api")

# Hole Status und Metriken
state = cb.get_state()
print(f"State: {state['state']}")
print(f"Success Rate: {state['metrics']['success_rate']:.2%}")
print(f"Failures: {state['failure_count']}/{state['threshold']}")
```

### Metriken

- `total_calls`: Gesamtanzahl Anfragen
- `success_calls`: Erfolgreiche Anfragen
- `failure_calls`: Fehlgeschlagene Anfragen
- `rejected_calls`: Blockierte Anfragen (OPEN State)
- `success_rate`: Erfolgsrate

## Kombination mit Retry & Rate Limiting

```python
from src.infra.resilience import circuit_breaker, retry, rate_limit

@rate_limit(name="kraken", requests_per_second=10)
@circuit_breaker(name="kraken_api", failure_threshold=5)
@retry(max_attempts=3, initial_delay=1.0)
async def fetch_kraken_data_robust(symbol: str):
    # Mit Rate-Limiting, Circuit-Breaker und Retry
    import ccxt
    exchange = ccxt.kraken()
    return await exchange.fetch_ticker(symbol)
```

**Reihenfolge wichtig:**
1. Rate-Limiting (äußerster Decorator)
2. Circuit-Breaker
3. Retry (innerster Decorator)

## Konfiguration

In `config.toml`:

```toml
[resilience]
circuit_breaker_enabled = true
circuit_breaker_threshold = 5
circuit_breaker_timeout = 60

[resilience.circuit_breaker.kraken]
threshold = 5
timeout_seconds = 60
half_open_max_calls = 3

[resilience.circuit_breaker.binance]
threshold = 5
timeout_seconds = 60
half_open_max_calls = 3

[resilience.circuit_breaker.coinbasepro]
threshold = 5
timeout_seconds = 60
half_open_max_calls = 3
```

### Config laden

```python
from src.core import load_config
from src.infra.resilience import CircuitBreakerConfig, get_circuit_breaker

cfg = load_config()

if hasattr(cfg, "resilience") and hasattr(cfg.resilience, "circuit_breaker"):
    kraken_config = CircuitBreakerConfig(
        name="kraken_api",
        failure_threshold=cfg.resilience.circuit_breaker.kraken.threshold,
        timeout_seconds=cfg.resilience.circuit_breaker.kraken.timeout_seconds,
        half_open_max_calls=cfg.resilience.circuit_breaker.kraken.half_open_max_calls,
    )
    cb = get_circuit_breaker("kraken_api", kraken_config)
```

## Fallback-Strategien

Kombiniere Circuit-Breaker mit Fallbacks:

```python
from src.infra.resilience import circuit_breaker, fallback

@fallback(default_value={"status": "unavailable"})
@circuit_breaker(name="kraken_api")
async def fetch_kraken_status():
    # Bei Fehler: Return {"status": "unavailable"}
    import ccxt
    exchange = ccxt.kraken()
    return await exchange.fetch_status()
```

## Best Practices

1. **Spezifische Names**: Verwende eindeutige Namen pro API/Service
2. **Sinnvolle Thresholds**: 3-5 Fehler typisch, zu niedrig = zu sensitiv
3. **Angemessene Timeouts**: 30-60 Sekunden typisch
4. **Monitoring**: Überwache Circuit-Breaker-States
5. **Alerts**: Alert bei OPEN State
6. **Manuelles Reset**: Implementiere für kritische Services

### Manuelles Reset

```python
cb = get_circuit_breaker("kraken_api")
cb.reset()  # Zurück zu CLOSED
```

## Error Handling

```python
from src.infra.resilience import (
    circuit_breaker,
    CircuitBreakerOpenError,
)

@circuit_breaker(name="api")
async def fetch_data():
    # API call
    pass

try:
    result = await fetch_data()
except CircuitBreakerOpenError:
    # Circuit Breaker ist OPEN
    print("Service temporarily unavailable")
    # Verwende Fallback oder zeige Error
except Exception as e:
    # Anderer Fehler
    print(f"Error: {e}")
```

## Troubleshooting

### Circuit Breaker öffnet zu häufig

- Erhöhe `failure_threshold`
- Erhöhe `timeout_seconds`
- Prüfe ob API-Probleme vorliegen

### Circuit Breaker öffnet nie

- Verringere `failure_threshold`
- Prüfe ob Exception korrekt propagiert wird
- Validiere `expected_exception` Type

### Recovery zu langsam

- Verringere `timeout_seconds`
- Erhöhe `half_open_max_calls`

## Siehe auch

- [Health Checks](HEALTH_CHECKS.md)
- [Rate Limiting](RATE_LIMITING.md)
- [Retry Logic](RETRY_LOGIC.md)
- [Monitoring](MONITORING.md)
